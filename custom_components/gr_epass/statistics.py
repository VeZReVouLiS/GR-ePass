"""Long-run toll statistics: when you actually drive.

The account API only answers thirty days at a time and keeps nothing aggregated,
so anything longer than a month has to be built up locally and kept. This holds
one record per day and derives the histograms from it.

Per-day records rather than running counters, because the coordinator re-fetches
the last thirty days on every refresh: counters would double-count, while a day
record can simply be recomputed from the window that was just fetched. The window
is authoritative for the days inside it, so a pass that the operator later
corrects or removes is reflected instead of lingering for ever.

Hours are stored sparsely -- a day has a handful of passes, not twenty-four -- so
a couple of years of history stays small enough to keep in one store.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import MAX_RANGE_DAYS, TXN_TOLL_CHARGE

_LOGGER = logging.getLogger(__name__)

STORE_VERSION = 1
# How far back a first-time backfill will walk. Two years is more history than
# the portal itself shows, and it stops the walk being unbounded on an old
# account.
MAX_BACKFILL_DAYS = 730
# Consecutive empty chunks that end the walk. One empty month is normal -- a
# holiday, a car off the road -- so a single gap must not look like the start of
# the account.
EMPTY_CHUNKS_BEFORE_STOP = 2


@dataclass
class DayRecord:
    """What happened on one calendar day."""

    passes: int = 0
    cost: float = 0.0
    hours: dict[int, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "p": self.passes,
            "c": round(self.cost, 2),
            "h": {str(hour): count for hour, count in sorted(self.hours.items())},
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> DayRecord:
        hours = {}
        for hour, count in (raw.get("h") or {}).items():
            try:
                hours[int(hour)] = int(count)
            except (TypeError, ValueError):
                continue
        return cls(
            passes=int(raw.get("p") or 0),
            cost=float(raw.get("c") or 0.0),
            hours=hours,
        )


class EpassStatistics:
    """Day records for one subscription, persisted across restarts."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store = Store(hass, STORE_VERSION, f"gr_epass_stats_{entry_id}")
        self._days: dict[date, DayRecord] = {}
        self._earliest_fetched: date | None = None
        self._loaded = False

    # ------------------------------------------------------------- persistence

    async def async_load(self) -> None:
        raw = await self._store.async_load() or {}
        for key, value in (raw.get("days") or {}).items():
            try:
                day = date.fromisoformat(key)
            except ValueError:
                continue
            self._days[day] = DayRecord.from_dict(value)
        earliest = raw.get("earliest_fetched")
        if earliest:
            try:
                self._earliest_fetched = date.fromisoformat(earliest)
            except ValueError:
                self._earliest_fetched = None
        self._loaded = True
        _LOGGER.debug("Loaded %s day records", len(self._days))

    async def async_save(self) -> None:
        await self._store.async_save(
            {
                "days": {
                    day.isoformat(): record.as_dict()
                    for day, record in sorted(self._days.items())
                },
                "earliest_fetched": (
                    self._earliest_fetched.isoformat()
                    if self._earliest_fetched
                    else None
                ),
            }
        )

    async def async_remove(self) -> None:
        """Drop the stored history, for when the entry is deleted."""
        await self._store.async_remove()

    # ------------------------------------------------------------------ folding

    def absorb(
        self,
        txns: list[dict[str, Any]],
        window_start: date,
        window_end: date,
        parse: Any,
    ) -> None:
        """Replace the day records inside a fetched window.

        ``parse`` turns a backend timestamp into an aware datetime; it is passed
        in rather than imported to keep this module independent of the
        coordinator.
        """
        if window_end < window_start:
            return

        fresh: dict[date, DayRecord] = {}
        for txn in txns:
            if str(txn.get("TransactionType") or "").strip() != TXN_TOLL_CHARGE:
                continue
            moment: datetime | None = parse(txn.get("TransactionLDateTime"))
            if moment is None:
                continue
            day = moment.date()
            if not window_start <= day <= window_end:
                continue
            record = fresh.setdefault(day, DayRecord())
            record.passes += 1
            record.cost += abs(_as_float(txn.get("TransactionAmount")))
            record.hours[moment.hour] = record.hours.get(moment.hour, 0) + 1

        # Every day in the window is rewritten from what was just fetched, so a
        # day that no longer has passes stops claiming the ones it used to.
        day = window_start
        while day <= window_end:
            if day in fresh:
                self._days[day] = fresh[day]
            else:
                self._days.pop(day, None)
            day += timedelta(days=1)

        if self._earliest_fetched is None or window_start < self._earliest_fetched:
            self._earliest_fetched = window_start

    async def async_backfill(
        self,
        fetch: Any,
        midnight: Any,
        parse: Any,
        today: date,
    ) -> bool:
        """Walk backwards a month at a time, once, to build up history.

        ``fetch(begin, end)`` returns the activities for a window. Returns True
        when something new was stored, so the caller knows to save.
        """
        oldest_allowed = today - timedelta(days=MAX_BACKFILL_DAYS)
        cursor = (self._earliest_fetched or today) - timedelta(days=1)
        empty_run = 0
        stored_anything = False

        while cursor >= oldest_allowed and empty_run < EMPTY_CHUNKS_BEFORE_STOP:
            chunk_start = max(oldest_allowed, cursor - timedelta(days=MAX_RANGE_DAYS - 1))
            try:
                txns = await fetch(
                    midnight(chunk_start - timedelta(days=1)),
                    midnight(cursor + timedelta(days=2)),
                )
            except Exception as err:  # noqa: BLE001 - history is best-effort
                _LOGGER.debug("Backfill stopped at %s: %s", chunk_start, err)
                break

            # Judge by what was actually stored, not by whether the call
            # returned rows: a chunk can come back full of passes that all fall
            # outside its own window, and saving then refreshing for that is
            # work for nothing.
            before = (len(self._days), self.total_passes)
            self.absorb(txns, chunk_start, cursor, parse)
            if (len(self._days), self.total_passes) == before:
                empty_run += 1
            else:
                empty_run = 0
                stored_anything = True

            cursor = chunk_start - timedelta(days=1)

        if stored_anything:
            _LOGGER.debug(
                "Backfill reached %s (%s days)",
                self._earliest_fetched,
                len(self._days),
            )
        return stored_anything

    # ------------------------------------------------------------- derived data

    @property
    def loaded(self) -> bool:
        return self._loaded

    @property
    def total_passes(self) -> int:
        return sum(record.passes for record in self._days.values())

    def histograms(self) -> dict[str, Any]:
        """Hour of day, day of week and month, derived from the day records."""
        by_hour = [0] * 24
        by_weekday = [0] * 7
        by_month: dict[str, dict[str, float]] = {}
        cost_by_hour = [0.0] * 24

        for day, record in self._days.items():
            by_weekday[day.weekday()] += record.passes
            month = by_month.setdefault(
                "%04d-%02d" % (day.year, day.month), {"passes": 0, "cost": 0.0}
            )
            month["passes"] += record.passes
            month["cost"] += record.cost
            for hour, count in record.hours.items():
                if 0 <= hour < 24:
                    by_hour[hour] += count
                    # Cost is only known per day, so it is spread over the
                    # passes of that day rather than invented per hour.
                    if record.passes:
                        cost_by_hour[hour] += record.cost * count / record.passes

        for month in by_month.values():
            month["cost"] = round(month["cost"], 2)

        days = sorted(self._days)
        return {
            "passes_by_hour": by_hour,
            "cost_by_hour": [round(value, 2) for value in cost_by_hour],
            "passes_by_weekday": by_weekday,
            "by_month": dict(sorted(by_month.items())),
            "busiest_hour": _argmax(by_hour),
            "busiest_weekday": _argmax(by_weekday),
            "days_recorded": len(days),
            "first_day": days[0].isoformat() if days else None,
            "last_day": days[-1].isoformat() if days else None,
        }


def _argmax(values: list[int]) -> int | None:
    """Index of the largest value, or None when nothing has been recorded."""
    best = max(values) if values else 0
    return values.index(best) if best else None


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
