"""Exercise the statistics folding without Home Assistant.

The property that matters: the coordinator re-fetches the same thirty days on
every refresh, so folding the same window twice must not change the totals. A
running counter would fail this; day records should not.
"""

import asyncio
import io
import os
import sys
import types
from datetime import date, datetime, timedelta, timezone

ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "custom_components", "gr_epass",
)

# --- stubs ----------------------------------------------------------------
class FakeStore:
    def __init__(self, *args, **kwargs):
        self.saved = None

    async def async_load(self):
        return self.saved

    async def async_save(self, data):
        self.saved = data

    async def async_remove(self):
        self.saved = None


ha = types.ModuleType("homeassistant")
core = types.ModuleType("homeassistant.core")
core.HomeAssistant = object
helpers = types.ModuleType("homeassistant.helpers")
storage = types.ModuleType("homeassistant.helpers.storage")
storage.Store = FakeStore
sys.modules.update({
    "homeassistant": ha,
    "homeassistant.core": core,
    "homeassistant.helpers": helpers,
    "homeassistant.helpers.storage": storage,
})

source = io.open(os.path.join(ROOT, "statistics.py"), encoding="utf-8").read()
source = source.replace("from .const import MAX_RANGE_DAYS, TXN_TOLL_CHARGE",
                        "MAX_RANGE_DAYS = 30\nTXN_TOLL_CHARGE = \"02\"")
module = types.ModuleType("stats_under_test")
sys.modules["stats_under_test"] = module
exec(compile(source, "statistics.py", "exec"), module.__dict__)  # noqa: S102

EpassStatistics = module.EpassStatistics

TODAY = date(2026, 8, 27)


def parse(value):
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc) if value else None


def pass_at(day: date, hour: int, amount: float = 2.55, kind: str = "02") -> dict:
    return {
        "TransactionType": kind,
        "TransactionLDateTime": datetime(day.year, day.month, day.day, hour, 5).isoformat(),
        "TransactionAmount": -amount,
    }


def midnight(day: date) -> datetime:
    return datetime(day.year, day.month, day.day, tzinfo=timezone.utc)


async def main() -> int:
    failures = []

    def check(name, got, want):
        if got != want:
            failures.append("%s: got %r, wanted %r" % (name, got, want))
        else:
            print("  ok   %-46s %r" % (name, got))

    stats = EpassStatistics(None, "test")
    await stats.async_load()

    window_start = TODAY - timedelta(days=3)
    txns = [
        pass_at(TODAY, 8), pass_at(TODAY, 8), pass_at(TODAY, 18),
        pass_at(TODAY - timedelta(days=1), 7),
        # a payment must not count as a pass
        pass_at(TODAY - timedelta(days=1), 12, 10.0, kind="01"),
        # outside the window: must be ignored
        pass_at(TODAY - timedelta(days=40), 9),
    ]

    stats.absorb(txns, window_start, TODAY, parse)
    check("passes after one fold", stats.total_passes, 4)
    check("cost today", round(stats.histograms()["by_month"]["2026-08"]["cost"], 2), 10.2)

    # The property under test.
    stats.absorb(txns, window_start, TODAY, parse)
    stats.absorb(txns, window_start, TODAY, parse)
    check("passes after three folds", stats.total_passes, 4)

    hist = stats.histograms()
    check("hour 8", hist["passes_by_hour"][8], 2)
    check("hour 18", hist["passes_by_hour"][18], 1)
    check("hour 7", hist["passes_by_hour"][7], 1)
    check("busiest hour", hist["busiest_hour"], 8)
    check("weekday total", sum(hist["passes_by_weekday"]), 4)
    check("days recorded", hist["days_recorded"], 2)

    # A pass the operator later removes must disappear, not linger.
    fewer = [t for t in txns if not t["TransactionLDateTime"].startswith("2026-08-27T18")]
    stats.absorb(fewer, window_start, TODAY, parse)
    check("passes after a removal", stats.total_passes, 3)
    check("hour 18 after removal", stats.histograms()["passes_by_hour"][18], 0)

    # Days before the window keep their records.
    stats.absorb([pass_at(TODAY - timedelta(days=10), 6)],
                 TODAY - timedelta(days=10), TODAY - timedelta(days=10), parse)
    check("older day added", stats.total_passes, 4)
    stats.absorb(fewer, window_start, TODAY, parse)
    check("older day survives a window fold", stats.total_passes, 4)

    # Persistence round-trip.
    await stats.async_save()
    again = EpassStatistics(None, "test")
    again._store = stats._store
    await again.async_load()
    check("passes after reload", again.total_passes, 4)
    check("first day after reload", again.histograms()["first_day"],
          (TODAY - timedelta(days=10)).isoformat())

    # The walk backwards: stops after two empty chunks, keeps what it found.
    calls = []

    async def fetch(begin, end):
        calls.append((begin.date(), end.date()))
        if len(calls) == 1:
            return [pass_at(TODAY - timedelta(days=20), 9)]
        return []

    walked = EpassStatistics(None, "walk")
    await walked.async_load()
    walked.absorb([pass_at(TODAY, 8)], TODAY - timedelta(days=2), TODAY, parse)
    changed = await walked.async_backfill(fetch, midnight, parse, TODAY)
    check("backfill reported a change", changed, True)
    check("backfill stopped after empty chunks", len(calls), 3)
    check("backfill kept the old pass", walked.total_passes, 2)

    print()
    if failures:
        for line in failures:
            print("  FAIL", line)
    else:
        print("  all checks passed")
    return 1 if failures else 0


sys.exit(asyncio.run(main()))
