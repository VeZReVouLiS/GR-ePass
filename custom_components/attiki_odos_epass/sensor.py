"""Sensors for Attiki Odos e-PASS."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import EpassConfigEntry
from .entity import BRAND, account_device_info
from .const import (
    ACCOUNT_STATUS,
    BALANCE_STATUS,
    DOMAIN,
    LIMITS_SOURCE,
    TRANSPONDER_RESTRICTION_OK,
    TRANSPONDER_STATES,
)
from .coordinator import (
    ACCOUNT_KEY,
    PERIOD_LAST_30_DAYS,
    PERIOD_MONTH,
    PERIOD_PREV_MONTH,
    PERIOD_TODAY,
    EpassCoordinator,
    EpassData,
    parse_dt,
    transponder_key,
    transponder_label,
)

EURO = "EUR"


def _num(value: Any) -> float | None:
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def _abs(value: Any) -> float | None:
    number = _num(value)
    return None if number is None else abs(number)


def _credit(value: Any) -> float | None:
    """Flip the portal's credit-negative ledger into a human-facing number.

    The API keeps a signed ledger where a *negative* AccountBalance means money
    sitting in your favour: -13.79 is rendered as "13,79 EUR P" (Pistosi) by the
    portal, and a positive value would be rendered "... X" (Chreosi). Negating it
    gives the intuitive reading: positive = prepaid credit left, negative = owed.
    """
    number = _num(value)
    return None if number is None else -number


def _latest_statement(data: EpassData) -> dict[str, Any]:
    """Newest billing period. The endpoint returns them newest first, but sort
    defensively rather than trusting the order."""
    if not data.billing_dates:
        return {}
    return max(
        data.billing_dates,
        key=lambda item: str(item.get("BillingDateAsDate") or ""),
    )


def _enum(mapping: dict[int, str], value: Any) -> str | None:
    if value in (None, ""):
        return None
    try:
        return mapping.get(int(value))
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True, kw_only=True)
class EpassSensorDescription(SensorEntityDescription):
    """Describes one e-PASS sensor.

    ``value_fn`` receives the refreshed data plus the key of the thing the
    entity belongs to (``ACCOUNT_KEY`` or a transponder id).
    """

    value_fn: Callable[[EpassData, str], StateType | datetime]
    attrs_fn: Callable[[EpassData, str], dict[str, Any] | None] | None = None
    period: str | None = None


def _stat(period: str, attribute: str) -> Callable[[EpassData, str], StateType]:
    def _value(data: EpassData, key: str) -> StateType:
        value = getattr(data.period(key, period), attribute)
        return round(value, 2) if isinstance(value, float) else value

    return _value


def _last_pass(data: EpassData, key: str) -> datetime | None:
    entry = data.last_pass.get(key)
    return entry["timestamp"] if entry else None


def _last_pass_attrs(data: EpassData, key: str) -> dict[str, Any] | None:
    entry = data.last_pass.get(key)
    if not entry:
        return None
    return {
        "amount": entry["amount"],
        "plaza": entry["plaza"],
        "lane": entry["lane"],
        "toll_category": entry["toll_category"],
        "external_network": entry["external_network"],
        "transponder_id": entry["transponder_id"],
    }


def _invalid_limit(data: EpassData, _key: str) -> float | None:
    """Balance below which no subscriber pass is allowed at all.

    Read from the published price list by vehicle category, never
    computed. Worth exposing because it is the number that actually
    bites: under it the barrier stays down and the only way through is a
    staffed lane.
    """
    return data.limits.get("invalid")


def _limit_attrs(data: EpassData, _key: str) -> dict[str, Any]:
    return {
        "toll_categories": data.toll_categories,
        "recharge_limit": data.limits.get("recharge"),
        "low_balance_limit": data.limits.get("low_balance"),
        "limits_source": LIMITS_SOURCE,
    }


def _card_attrs(data: EpassData, _key: str) -> dict[str, Any]:
    """Expose the stored cards for a picker, without any sensitive field.

    Only the brand, the last four digits, the alias and the expiry are shown.
    The bank token is deliberately left out: it is the one value that could
    initiate a charge, and attributes end up in the recorder and in traces.
    """
    return {
        "cards": [
            {
                "id": card["id"],
                "brand": card["brand"],
                "last_four": card["last_four"],
                "alias": card["alias"],
                "expiry": card["expiry"].isoformat() if card["expiry"] else None,
                "state": card["state"],
            }
            for card in data.cards
        ],
        "min_amount": data.payment_limits.get("min_amount"),
        "max_amount": data.payment_limits.get("max_amount"),
    }


def _next_card_expiry(data: EpassData, _key: str) -> datetime | None:
    """Soonest expiry among the usable cards, for an "renew your card" alert."""
    expiries = [
        card["expiry"]
        for card in data.payable_cards
        if card["expiry"] is not None
    ]
    return min(expiries) if expiries else None


def _period_sensors(scope: str) -> list[EpassSensorDescription]:
    """Pass count and cost for each of the four time windows.

    Calendar windows (today, this month, last month) are period totals, so they
    get state_class TOTAL and feed long-term statistics.

    The rolling 30-day window is a snapshot, not a meter: it goes down as old
    days fall out of the window. MEASUREMENT would describe that correctly, but
    Home Assistant rejects MEASUREMENT together with device_class MONETARY, so
    the money one carries no state class at all. History still graphs it; it
    just stays out of long-term statistics, which is the honest outcome for a
    figure that is not a cumulative total.
    """
    windows = (
        (PERIOD_TODAY, "today", SensorStateClass.TOTAL, SensorStateClass.TOTAL),
        (PERIOD_MONTH, "month", SensorStateClass.TOTAL, SensorStateClass.TOTAL),
        (PERIOD_LAST_30_DAYS, "last_30_days", SensorStateClass.MEASUREMENT, None),
        (PERIOD_PREV_MONTH, "prev_month", SensorStateClass.TOTAL, SensorStateClass.TOTAL),
    )
    sensors: list[EpassSensorDescription] = []
    for period, slug, count_class, money_class in windows:
        sensors.append(
            EpassSensorDescription(
                key=f"{scope}_passes_{slug}",
                translation_key=f"passes_{slug}",
                state_class=count_class,
                icon="mdi:boom-gate-arrow-up",
                value_fn=_stat(period, "passes"),
                period=period,
            )
        )
        sensors.append(
            EpassSensorDescription(
                key=f"{scope}_cost_{slug}",
                translation_key=f"cost_{slug}",
                native_unit_of_measurement=EURO,
                device_class=SensorDeviceClass.MONETARY,
                state_class=money_class,
                value_fn=_stat(period, "cost"),
                period=period,
            )
        )
    return sensors


ACCOUNT_SENSORS: tuple[EpassSensorDescription, ...] = (
    EpassSensorDescription(
        key="balance",
        translation_key="balance",
        native_unit_of_measurement=EURO,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:wallet",
        value_fn=lambda data, _key: _credit(data.account.get("AccountBalance")),
    ),
    EpassSensorDescription(
        key="balance_status",
        translation_key="balance_status",
        device_class=SensorDeviceClass.ENUM,
        options=list(BALANCE_STATUS.values()),
        icon="mdi:speedometer",
        value_fn=lambda data, _key: _enum(
            BALANCE_STATUS, data.account.get("BalanceStatus")
        ),
    ),
    EpassSensorDescription(
        key="last_pass",
        translation_key="last_pass",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:road-variant",
        value_fn=_last_pass,
        attrs_fn=_last_pass_attrs,
    ),
    EpassSensorDescription(
        key="cost_month_attiki",
        translation_key="cost_month_attiki",
        native_unit_of_measurement=EURO,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=_stat(PERIOD_MONTH, "cost_attiki"),
        period=PERIOD_MONTH,
    ),
    EpassSensorDescription(
        key="cost_month_other",
        translation_key="cost_month_other",
        native_unit_of_measurement=EURO,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        value_fn=_stat(PERIOD_MONTH, "cost_other"),
        period=PERIOD_MONTH,
    ),
    EpassSensorDescription(
        key="payments_month",
        translation_key="payments_month",
        native_unit_of_measurement=EURO,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:cash-plus",
        value_fn=_stat(PERIOD_MONTH, "payments"),
        period=PERIOD_MONTH,
    ),
    EpassSensorDescription(
        key="last_payment_amount",
        translation_key="last_payment_amount",
        native_unit_of_measurement=EURO,
        device_class=SensorDeviceClass.MONETARY,
        icon="mdi:cash-check",
        # Payments land in the ledger as a credit, i.e. negative. See _credit().
        value_fn=lambda data, _key: _abs(data.account.get("LastPaymentAmount")),
    ),
    EpassSensorDescription(
        key="last_payment_date",
        translation_key="last_payment_date",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:calendar-check",
        value_fn=lambda data, _key: parse_dt(
            data.account.get("LastPaymentDateTime")
        ),
    ),
    EpassSensorDescription(
        key="last_statement_date",
        translation_key="last_statement_date",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:file-document-outline",
        value_fn=lambda data, _key: parse_dt(
            _latest_statement(data).get("BillingDateAsDate")
        ),
        attrs_fn=lambda data, _key: {
            "issue_number": _latest_statement(data).get("IssueNumber"),
            "statements_available": len(data.billing_dates),
        },
    ),
    EpassSensorDescription(
        key="transponder_count",
        translation_key="transponder_count",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:credit-card-multiple-outline",
        value_fn=lambda data, _key: len(data.transponders),
        attrs_fn=lambda data, _key: {
            "distributed_on_account": data.account.get("TranspondersDistributed"),
        },
    ),
    EpassSensorDescription(
        key="account_status",
        translation_key="account_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.ENUM,
        options=list(ACCOUNT_STATUS.values()),
        value_fn=lambda data, _key: _enum(
            ACCOUNT_STATUS, data.account.get("AccountStatus")
        ),
        attrs_fn=lambda data, _key: {
            "account_id": data.account.get("AccountID"),
            "account_alias": data.account.get("AccountAlias"),
            "account_profile": data.account.get("AccountProfile"),
            "account_type": data.account.get("AccountType"),
            "e_invoice_status": data.account.get("EInvoiceStatus"),
        },
    ),
    EpassSensorDescription(
        key="invalid_balance_limit",
        translation_key="invalid_balance_limit",
        entity_category=EntityCategory.DIAGNOSTIC,
        native_unit_of_measurement=EURO,
        device_class=SensorDeviceClass.MONETARY,
        icon="mdi:boom-gate-alert-outline",
        value_fn=_invalid_limit,
        attrs_fn=_limit_attrs,
    ),
    EpassSensorDescription(
        key="payment_cards",
        translation_key="payment_cards",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:credit-card-check-outline",
        value_fn=lambda data, _key: len(data.payable_cards),
        attrs_fn=_card_attrs,
    ),
    EpassSensorDescription(
        key="card_expiry",
        translation_key="card_expiry",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:credit-card-clock-outline",
        value_fn=_next_card_expiry,
    ),
    *_period_sensors("account"),
)

TRANSPONDER_SENSORS: tuple[EpassSensorDescription, ...] = (
    EpassSensorDescription(
        key="last_pass",
        translation_key="last_pass",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:road-variant",
        value_fn=_last_pass,
        attrs_fn=_last_pass_attrs,
    ),
    EpassSensorDescription(
        key="transponder_status",
        translation_key="transponder_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.ENUM,
        options=TRANSPONDER_STATES,
        value_fn=lambda data, key: _restriction_state(_record(data, key)),
        attrs_fn=lambda data, key: _transponder_attrs(_record(data, key)),
    ),
    *_period_sensors("transponder"),
)


def _record(data: EpassData, key: str) -> dict[str, Any]:
    for transponder in data.transponders:
        if transponder_key(transponder) == key:
            return transponder
    return {}


def _restriction_state(record: dict[str, Any]) -> str | None:
    """Mirror the portal: RestrictionStatus == 2 is the green check."""
    value = record.get("RestrictionStatus")
    if value in (None, ""):
        return None
    try:
        return (
            "active" if int(value) == TRANSPONDER_RESTRICTION_OK else "restricted"
        )
    except (TypeError, ValueError):
        return None


def _transponder_attrs(record: dict[str, Any]) -> dict[str, Any]:
    vehicle = " ".join(
        str(record[part])
        for part in ("VehicleMake", "VehicleModel")
        if record.get(part)
    )
    return {
        "transponder_id": record.get("TransponderId"),
        # TransponderDisplayId comes back null; TransponderText holds the
        # number printed on the device.
        "transponder_number": record.get("TransponderText"),
        "plate": record.get("PlateNum"),
        "vehicle": vehicle or None,
        "vehicle_color": record.get("VehicleColor"),
        "toll_category": record.get("TollCategoryId"),
        "distributed_on": record.get("DistributedLDateTime"),
        "restriction_status": record.get("RestrictionStatus"),
        "trip_status": record.get("TripStatus"),
        "trip_count": record.get("TripCount"),
        "alias": record.get("Alias"),
    }


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EpassConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the e-PASS sensors."""
    coordinator = entry.runtime_data
    account_id = str(coordinator.account_id)

    entities: list[SensorEntity] = [
        EpassSensor(coordinator, description, account_id, ACCOUNT_KEY)
        for description in ACCOUNT_SENSORS
    ]
    for transponder in coordinator.data.transponders:
        key = transponder_key(transponder)
        entities.extend(
            EpassSensor(coordinator, description, account_id, key)
            for description in TRANSPONDER_SENSORS
        )
    async_add_entities(entities)


class EpassSensor(CoordinatorEntity[EpassCoordinator], SensorEntity):
    """One e-PASS value, either account wide or for a single transponder."""

    _attr_has_entity_name = True
    entity_description: EpassSensorDescription

    def __init__(
        self,
        coordinator: EpassCoordinator,
        description: EpassSensorDescription,
        account_id: str,
        data_key: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._data_key = data_key

        if data_key == ACCOUNT_KEY:
            self._attr_unique_id = f"{account_id}_{description.key}"
            self._attr_device_info = account_device_info(account_id)
        else:
            record = _record(coordinator.data, data_key)
            self._attr_unique_id = f"{account_id}_{data_key}_{description.key}"
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, f"transponder_{account_id}_{data_key}")},
                via_device=(DOMAIN, f"account_{account_id}"),
                name=transponder_label(record) if record else data_key,
                manufacturer=BRAND,
                model="e-PASS transponder",
                serial_number=str(record.get("TransponderText") or data_key),
            )

    @property
    def native_value(self) -> StateType | datetime:
        return self.entity_description.value_fn(self.coordinator.data, self._data_key)

    @property
    def last_reset(self) -> datetime | None:
        description = self.entity_description
        if (
            description.period is None
            or description.state_class != SensorStateClass.TOTAL
        ):
            return None
        return self.coordinator.data.period(self._data_key, description.period).start

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(
            self.coordinator.data, self._data_key
        )
