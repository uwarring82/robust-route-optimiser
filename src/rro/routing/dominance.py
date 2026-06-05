"""B2 static dominance filter (handbook §4.3, Coastline §B2).

A hub-arrival ``a`` is dominated by ``b`` iff ``b`` is no later, no more
expensive, and no more transfers, with at least one strict inequality. Dominance
is over ``(arrival_time, cost_eur, transfers)`` only; ``first_mile_mode`` is NOT a
dominance dimension, so two arrivals equal on all three but differing in mode are
mutually non-dominating and both retained.
"""

from __future__ import annotations

from typing import Iterable

from rro.models import HubArrival


def dominates(b: HubArrival, a: HubArrival) -> bool:
    """``True`` iff ``b ≻ a`` (b dominates a) over the three static dimensions (§4.3)."""
    no_worse = (
        b.arrival_time <= a.arrival_time
        and b.cost_eur <= a.cost_eur
        and b.transfers <= a.transfers
    )
    strictly_better = (
        b.arrival_time < a.arrival_time
        or b.cost_eur < a.cost_eur
        or b.transfers < a.transfers
    )
    return no_worse and strictly_better


def is_dominated(a: HubArrival, frontier: Iterable[HubArrival]) -> bool:
    """``True`` iff some other arrival in ``frontier`` dominates ``a`` (§4.3)."""
    return any(dominates(b, a) for b in frontier if b is not a)


def pareto_frontier(arrivals: list) -> list:
    """Return the non-dominated (Pareto-optimal) hub-arrivals (§4.3).

    Comparison is per-hub-arrival, not per-hub: an arrival at one hub can dominate
    an arrival at a different hub. Duplicates (equal on all three criteria) do not
    dominate each other and are both retained.
    """
    return [a for a in arrivals if not is_dominated(a, arrivals)]
