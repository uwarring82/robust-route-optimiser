"""Coastline §7 user-facing card mapping (handbook §7.3).

In Phase A: ``confidence`` is the literal ``"scheduled"`` (degenerate
distribution, ``Q₀.₈ − E[T_eff] = 0``); ``comfort`` is empty; ``risks`` is empty
except for an experimental-taxi low-confidence warning (§4.2). The last-mile
boarding is **not** counted in ``transfers`` / ``transfer_stations`` (§4.1).
"""

from __future__ import annotations

from typing import Optional

from rro.models import Card

# Layers whose line-changes count as transfers (the appended last mile does not, §4.1).
_COUNTED_LAYERS = ("first_mile", "backbone")


def hhmm(dep_or_arr: str) -> str:
    """Local ``HH:MM`` from an ISO 8601 datetime or a bare ``HH:MM`` (handbook §2.8)."""
    if "T" in dep_or_arr:
        return dep_or_arr.split("T", 1)[1][:5]
    return dep_or_arr[:5]


def transfer_stations(legs) -> list:
    """Transfer stations over first-mile + backbone boundaries only (handbook §4.1).

    The last-mile boarding is excluded. The station is the arrival point of each
    counted leg that is followed by another counted leg.
    """
    counted = [l for l in legs if l.layer in _COUNTED_LAYERS]
    return [counted[i].to for i in range(len(counted) - 1)]


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
