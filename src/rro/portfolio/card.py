"""Coastline §7 user-facing card mapping (handbook §7.3).

In Phase A: ``confidence`` is the literal ``"scheduled"`` (degenerate
distribution, ``Q₀.₈ − E[T_eff] = 0``); ``comfort`` is empty; ``risks`` is empty
except for an experimental-taxi low-confidence warning (§4.2). The last-mile
boarding is **not** counted in ``transfers`` / ``transfer_stations`` (§4.1).
"""

from __future__ import annotations

from typing import Optional

from rro.models import Card
# The §4.1 transfer/station semantics are B1-owned; re-exported here for callers.
from rro.routing.decompose import transfer_stations  # noqa: F401


def hhmm(dep_or_arr: str) -> str:
    """Local ``HH:MM`` from an ISO 8601 datetime or a bare ``HH:MM`` (handbook §2.8)."""
    if "T" in dep_or_arr:
        return dep_or_arr.split("T", 1)[1][:5]
    return dep_or_arr[:5]


def build_card(strategy_label: str, legs, *, price_eur: Optional[float] = None,
               taxi_warning: Optional[str] = None) -> Card:
    """Build a §7 summary card from a strategy's legs (handbook §7.3, §4.1).

    ``taxi_warning`` (Coastline §6) is the sole Phase-A source of a ``risks`` entry.
    """
    stations = transfer_stations(legs)
    return Card(
        strategy_label=strategy_label,
        expected_arrival=hhmm(legs[-1].arr) if legs else "",
        confidence="scheduled",
        transfers=len(stations),
        transfer_stations=stations,
        price_eur=price_eur,
        comfort=[],
        risks=[taxi_warning] if taxi_warning else [],
    )
