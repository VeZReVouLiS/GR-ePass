"""Data coordinator: fetches account activity and turns it into statistics."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import EpassAuthError, EpassClient, EpassConnectionError, EpassError
from .const import (
    ALL_TRANSPONDERS,
    CARD_STATE_ACTIVE,
    CARD_STATE_EXPIRED,
    CARD_STATE_INACTIVE,
    CARD_TYPES,
    CONF_ACCOUNT_ID,
    CONF_SCAN_INTERVAL_MINUTES,
    CONF_TRANSPONDERS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    EVENT_BALANCE_CHANGED,
    EVENT_PASS,
    EVENT_PASS_MAX_AGE,
    TOLL_LIMITS,
    TXN_PAYMENT,
    TXN_TOLL_CHARGE,
)

_LOGGER = logging.getLogger(__name__)

PERIOD_TODAY = "today"
PERIOD_MONTH = "month"
PERIOD_LAST_30_DAYS = "last_30_days"
PERIOD_PREV_MONTH = "prev_month"

PERIODS = (PERIOD_TODAY, PERIOD_MONTH, PERIOD_LAST_30_DAYS, PERIOD_PREV_MONTH)

# Key used for the whole-account rollup inside the stats mapping.
ACCOUNT_KEY = "__account__"


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def parse_dt(value: Any) -> datetime | None:
    """Parse a backend timestamp into an aware datetime in local time.

    The API returns local (Athens) wall-clock timestamps, usually without a
    timezone offset, so naive values are assumed to be local.
    """
    if not value:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = dt_util.parse_datetime(str(value))
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
    return dt_util.as_local(parsed)


def transponder_key(transponder: dict[str, Any]) -> str:
    """Stable identifier for a transponder record."""
    for name in ("TransponderId", "TransponderID", "TransponderDisplayId"):
        if transponder.get(name) not in (None, ""):
            return str(transponder[name])
    return str(transponder.get("VehicleId", ""))


def transponder_label(transponder: dict[str, Any]) -> str:
    """Human friendly name: alias, else plate, else the transponder number."""
    for name in ("Alias", "TransponderText", "PlateNum", "TransponderDisplayId"):
        value = transponder.get(name)
        if value:
            return str(value)
    return transponder_key(transponder)


@dataclass
class PeriodStats:
    """Aggregated toll usage over one time window."""

    passes: int = 0
    cost: float = 0.0
    cost_attiki: float = 0.0
    cost_other: float = 0.0
    payments: float = 0.0
    start: datetime | None = None

    def add(self, amount: float, external: bool) -> None:
        self.passes += 1
        self.cost += amount
        if external:
            self.cost_other += amount
        else:
            self.cost_attiki += amount


@dataclass
class EpassData:
    """Everything the entities need for one refresh."""

    account: dict[str, Any] = field(default_factory=dict)
    transponders: list[dict[str, Any]] = field(default_factory=list)
    billing_dates: list[dict[str, Any]] = field(default_factory=list)
    stats: dict[str, dict[str, PeriodStats]] = field(default_factory=dict)
    last_pass: dict[str, dict[str, Any]] = field(default_factory=dict)
    cards: list[dict[str, Any]] = field(default_factory=list)
    payment_limits: dict[str, Any] = field(default_factory=dict)
    # Published account limits for the monitored vehicle categories.
    limits: dict[str, float] = field(default_factory=dict)
    toll_categories: list[int] = field(default_factory=list)

    @property
    def payable_cards(self) -> list[dict[str, Any]]:
        """Stored cards that can actually be charged (mirrors the portal).

        The payment page filters out anything past its expiry date and
        preselects the first survivor.
        """
        return [c for c in self.cards if c.get("state") == CARD_STATE_ACTIVE]

    def period(self, key: str, period: str) -> PeriodStats:
        return self.stats.get(key, {}).get(period, PeriodStats())


class EpassCoordinator(DataUpdateCoordinator[EpassData]):
    """Polls my e-PASS and derives per-transponder statistics."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: EpassClient,
    ) -> None:
        minutes = entry.options.get(CONF_SCAN_INTERVAL_MINUTES)
        interval = timedelta(minutes=minutes) if minutes else DEFAULT_SCAN_INTERVAL
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} {entry.data.get(CONF_ACCOUNT_ID)}",
            update_interval=interval,
            config_entry=entry,
        )
        self.client = client
        self.account_id = entry.data[CONF_ACCOUNT_ID]
        self._prev_month_key: tuple[int, int] | None = None
        self._prev_month_txns: list[dict[str, Any]] = []
        # None means "not seeded yet": the first refresh records what already
        # happened without raising events for it.
        self._known_passes: set[tuple[Any, ...]] | None = None
        self._prev_balance: float | None = None
        # Set during setup / by the platforms, so the button never has to guess
        # an entity_id -- users rename entities freely.
        self.payment: Any = None
        self.card_select: Any = None
        self.amount_entity: Any = None

    @property
    def selected_transponders(self) -> list[str]:
        """Transponder ids the user picked, or an empty list meaning all."""
        entry = self.config_entry
        assert entry is not None
        selection = entry.options.get(
            CONF_TRANSPONDERS, entry.data.get(CONF_TRANSPONDERS)
        )
        if not selection or ALL_TRANSPONDERS in selection:
            return []
        return [str(item) for item in selection]

    @staticmethod
    def _categories_of(transponders: list[dict[str, Any]]) -> list[int]:
        """Vehicle categories present among the monitored transponders."""
        categories: set[int] = set()
        for transponder in transponders:
            try:
                categories.add(int(float(transponder.get("TollCategoryId"))))
            except (TypeError, ValueError):
                continue
        return sorted(categories)

    @staticmethod
    def _limits_for(categories: list[int]) -> dict[str, float]:
        known = [TOLL_LIMITS[c] for c in categories if c in TOLL_LIMITS]
        if not known:
            return {}
        return {
            name: max(entry[name] for entry in known)
            for name in ("recharge", "low_balance", "invalid")
        }

    @property
    def toll_categories(self) -> list[int]:
        return self.data.toll_categories if self.data else []

    @property
    def account_limits(self) -> dict[str, float]:
        """Published limits that apply to this subscription.

        The price list states the limits *per e-PASS device*, keyed by vehicle
        category, but a subscription has a single shared balance. With a small
        car and a truck on one account the truck is blocked long before the car
        would be, so the account-level figure that actually matters is the
        **highest** limit among the monitored transponders.
        """
        return self.data.limits if self.data else {}

    async def _async_update_data(self) -> EpassData:
        try:
            account = await self.client.async_get_account(self.account_id)
            transponders = await self.client.async_get_transponders(self.account_id)
            billing_dates = await self.client.async_get_billing_dates(self.account_id)

            now = dt_util.now()
            today = now.date()
            month_start = today.replace(day=1)
            window_start = min(month_start, today - timedelta(days=29))

            # One extra day on each side keeps us immune to how the backend
            # interprets the range boundaries; bucketing happens locally.
            begin = self._local_midnight(window_start - timedelta(days=1))
            end = self._local_midnight(today + timedelta(days=2))
            txns = await self.client.async_get_activities(self.account_id, begin, end)

            txns += await self._async_prev_month(today)
        except EpassAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except (EpassConnectionError, EpassError) as err:
            raise UpdateFailed(str(err)) from err

        # Payment metadata is a nice-to-have: a subscriber with no stored card,
        # or a gateway hiccup, must not take the whole integration down.
        cards = await self._async_stored_cards()
        payment_limits = await self._async_payment_limits()

        selection = self.selected_transponders
        if selection:
            transponders = [
                t for t in transponders if transponder_key(t) in selection
            ]

        data = EpassData(
            account=account,
            transponders=transponders,
            billing_dates=billing_dates,
            cards=cards,
            payment_limits=payment_limits,
        )
        data.toll_categories = self._categories_of(transponders)
        data.limits = self._limits_for(data.toll_categories)
        passes = self._build_stats(data, txns, today)
        self._fire_pass_events(passes)
        self._fire_balance_event(data)
        return data

    async def _async_stored_cards(self) -> list[dict[str, Any]]:
        """Tokenised cards, annotated with a usable state."""
        try:
            records = await self.client.async_get_stored_cards()
        except EpassAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except EpassError as err:
            _LOGGER.debug("Could not read stored cards: %s", err)
            return []

        now = dt_util.now()
        cards: list[dict[str, Any]] = []
        for record in records:
            expiry = parse_dt(record.get("ExpiryDate"))
            # Same precedence as getEffectiveState() in the portal: expiry wins
            # over the active flag.
            if expiry is not None and expiry < now:
                state = CARD_STATE_EXPIRED
            elif record.get("Active") is False:
                state = CARD_STATE_INACTIVE
            else:
                state = CARD_STATE_ACTIVE
            last_four = str(record.get("CardNumber") or "").strip()
            cards.append(
                {
                    "id": record.get("Id"),
                    "alias": record.get("Alias") or None,
                    "last_four": last_four or None,
                    "brand": CARD_TYPES.get(
                        int(_as_float(record.get("CardTypeId"))), "other"
                    ),
                    "token": record.get("Token"),
                    "expiry": expiry,
                    "state": state,
                }
            )
        return cards

    async def _async_payment_limits(self) -> dict[str, Any]:
        """Gateway MinAmount / MaxAmount for a top-up."""
        try:
            info = await self.client.async_get_payment_provider_info()
        except EpassAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except EpassError as err:
            _LOGGER.debug("Could not read payment provider info: %s", err)
            return {}
        return {
            "min_amount": _as_float(info.get("MinAmount")) or None,
            "max_amount": _as_float(info.get("MaxAmount")) or None,
        }

    def _fire_pass_events(self, passes: list[dict[str, Any]]) -> None:
        """Raise one event per newly seen toll pass.

        Seeded silently on the first refresh, and limited to recent passes, so
        neither a restart nor the previous-month backfill can replay history.
        """
        fingerprints = {item["fingerprint"] for item in passes}
        if self._known_passes is None:
            self._known_passes = fingerprints
            return

        cutoff = dt_util.now() - EVENT_PASS_MAX_AGE
        for item in passes:
            if item["fingerprint"] in self._known_passes:
                continue
            if item["timestamp"] < cutoff:
                continue
            payload = {k: v for k, v in item.items() if k != "fingerprint"}
            payload["account_id"] = self.account_id
            payload["timestamp"] = item["timestamp"].isoformat()
            self.hass.bus.async_fire(EVENT_PASS, payload)

        self._known_passes = fingerprints

    def _fire_balance_event(self, data: EpassData) -> None:
        """Raise an event whenever the balance moves, in either direction."""
        raw = data.account.get("AccountBalance")
        if raw is None:
            return
        # Same sign flip the balance sensor applies: positive means credit.
        balance = round(-_as_float(raw), 2)
        previous = self._prev_balance
        self._prev_balance = balance
        if previous is None or previous == balance:
            return
        self.hass.bus.async_fire(
            EVENT_BALANCE_CHANGED,
            {
                "account_id": self.account_id,
                "balance": balance,
                "previous_balance": previous,
                "delta": round(balance - previous, 2),
                "direction": "up" if balance > previous else "down",
            },
        )

    def _local_midnight(self, day: date) -> datetime:
        return datetime.combine(day, datetime.min.time()).replace(
            tzinfo=dt_util.DEFAULT_TIME_ZONE
        )

    async def _async_prev_month(self, today: date) -> list[dict[str, Any]]:
        """Previous calendar month, fetched once and then cached."""
        month_start = today.replace(day=1)
        prev_end = month_start - timedelta(days=1)
        prev_start = prev_end.replace(day=1)
        key = (prev_start.year, prev_start.month)
        if self._prev_month_key == key:
            return self._prev_month_txns

        txns = await self.client.async_get_activities(
            self.account_id,
            self._local_midnight(prev_start - timedelta(days=1)),
            self._local_midnight(prev_end + timedelta(days=2)),
        )
        # Trim to the real month so the cached list cannot leak into other
        # windows when it gets merged with the rolling fetch.
        trimmed = [
            txn
            for txn in txns
            if (moment := parse_dt(txn.get("TransactionLDateTime")))
            and prev_start <= moment.date() <= prev_end
        ]
        self._prev_month_key = key
        self._prev_month_txns = trimmed
        return trimmed

    def _build_stats(
        self,
        data: EpassData,
        txns: list[dict[str, Any]],
        today: date,
    ) -> list[dict[str, Any]]:
        """Bucket transactions into the period stats.

        Returns every toll pass it saw, each with the dedup fingerprint, so the
        caller can work out which ones are new and raise events for them.
        """
        month_start = today.replace(day=1)
        prev_month_end = month_start - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)
        last30_start = today - timedelta(days=29)

        keys = [ACCOUNT_KEY] + [transponder_key(t) for t in data.transponders]
        selection = {transponder_key(t) for t in data.transponders}

        starts = {
            PERIOD_TODAY: self._local_midnight(today),
            PERIOD_MONTH: self._local_midnight(month_start),
            PERIOD_LAST_30_DAYS: self._local_midnight(last30_start),
            PERIOD_PREV_MONTH: self._local_midnight(prev_month_start),
        }
        data.stats = {
            key: {
                period: PeriodStats(start=starts[period]) for period in PERIODS
            }
            for key in keys
        }
        seen: set[tuple[Any, ...]] = set()
        passes: list[dict[str, Any]] = []

        for txn in txns:
            moment = parse_dt(txn.get("TransactionLDateTime"))
            if moment is None:
                continue
            day = moment.date()
            txn_type = str(txn.get("TransactionType") or "")
            amount = abs(_as_float(txn.get("TransactionAmount")))
            tid = str(txn.get("TransponderId") or "")

            # The rolling fetch and the cached previous month can overlap. The
            # activity records carry no id of their own, so identity is the
            # timestamp pair plus where and how much.
            fingerprint = (
                txn.get("TransactionLDateTime"),
                txn.get("SysPostLDateTime"),
                tid,
                txn_type,
                txn.get("TransactionAmount"),
                txn.get("PlazaId"),
                txn.get("NodeId"),
                txn.get("LaneText"),
            )
            if fingerprint in seen:
                continue
            seen.add(fingerprint)

            buckets: list[str] = []
            if day == today:
                buckets.append(PERIOD_TODAY)
            if month_start <= day <= today:
                buckets.append(PERIOD_MONTH)
            if last30_start <= day <= today:
                buckets.append(PERIOD_LAST_30_DAYS)
            if prev_month_start <= day <= prev_month_end:
                buckets.append(PERIOD_PREV_MONTH)
            if not buckets:
                continue

            targets = [ACCOUNT_KEY]
            if tid and tid in selection:
                targets.append(tid)
            elif tid and selection and tid not in selection:
                # Transponder filtered out by the user: keep it out of the
                # account rollup too, so the numbers match the visible devices.
                continue

            if txn_type == TXN_PAYMENT:
                if str(txn.get("BankAuthorizationStatusDB") or "") == "D":
                    continue
                for period in buckets:
                    data.stats[ACCOUNT_KEY][period].payments += amount
                continue

            if txn_type != TXN_TOLL_CHARGE:
                continue

            external = str(txn.get("PlazaExternal") or "").upper() == "Y"
            for key in targets:
                for period in buckets:
                    data.stats[key][period].add(amount, external)

            self._track_last_pass(data, ACCOUNT_KEY, txn, moment)
            if tid in selection:
                self._track_last_pass(data, tid, txn, moment)

            passes.append(
                {
                    "fingerprint": fingerprint,
                    "timestamp": moment,
                    "amount": amount,
                    "plaza": txn.get("PlazaText"),
                    "lane": txn.get("LaneText"),
                    "transponder_id": txn.get("TransponderId"),
                    "toll_category": txn.get("TollCategoryName"),
                    "external_network": external,
                }
            )

        return passes

    @staticmethod
    def _track_last_pass(
        data: EpassData,
        key: str,
        txn: dict[str, Any],
        moment: datetime,
    ) -> None:
        current = data.last_pass.get(key)
        if current and current["timestamp"] >= moment:
            return
        data.last_pass[key] = {
            "timestamp": moment,
            "amount": abs(_as_float(txn.get("TransactionAmount"))),
            "plaza": txn.get("PlazaText"),
            "lane": txn.get("LaneText"),
            "transponder_id": txn.get("TransponderId"),
            "toll_category": txn.get("TollCategoryName"),
            "external_network": str(txn.get("PlazaExternal") or "").upper() == "Y",
        }
