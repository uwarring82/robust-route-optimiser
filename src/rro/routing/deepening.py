"""B3 progressive deepening controller (handbook §5, Coastline §B3).

Depth 0 (direct + 1-transfer) → Depth 1 (2-transfer) → Depth 2 (creative ×2.5),
with ε-termination. Routing is schedule-based (no GTFS-RT) on ``G_base``.

The controller is parameterised by an injectable ``plan_fn(params) -> list`` that
returns full-route :class:`OTPItinerary`s for a depth's parameters — so it is
testable against recorded responses and decoupled from OTP coordinate/place
details. It decomposes each itinerary (B1), keys a dedup pool by the backbone
:func:`route_signature`, and halts when a deeper sweep stops contributing
portfolio-relevant routes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rro.config import Epsilon
from rro.routing.decompose import (
    count_transfers,
    decompose,
    min_transfer_slack,
)

# Depth ladder (handbook §5.1). Depth 2 scales budget + window by the creative factor.
CREATIVE_FACTOR = 2.5
BASE_BUDGET = 6
BASE_SEARCH_WINDOW_S = 3600
DEPTH_PARAMS = {
    0: {"max_transfers": 1, "budget_mult": 1.0, "window_mult": 1.0},
    1: {"max_transfers": 2, "budget_mult": 1.0, "window_mult": 1.0},
    2: {"max_transfers": 2, "budget_mult": CREATIVE_FACTOR, "window_mult": CREATIVE_FACTOR},
}


def route_signature(legs) -> tuple:
    """Structural identity of the BACKBONE layer (handbook §5.3).

    Ordered ``(line, board_stop, alight_stop)`` over backbone transit legs. The
    first backbone ``board_stop`` IS the feeder hub, so feeder-hub choice is part
    of the signature; the first-mile leg (its mode/path) and the exact
    minute-level departure are abstracted away. Hence different feeder hubs →
    different signatures → distinct candidates; same hub + different first-mile
    mode → shared signature → merged (§4.3, §5.3).
    """
    return tuple((leg.line, leg.from_, leg.to) for leg in legs if leg.layer == "backbone")


def depth_params(depth: int, base_budget: int = BASE_BUDGET,
                 base_window_s: int = BASE_SEARCH_WINDOW_S) -> dict:
    """OTP query parameters for a depth (handbook §5.1). Depths > 2 clamp to Depth 2."""
    p = DEPTH_PARAMS[min(depth, 2)]
    return {
        "depth": depth,
        "max_transfers": p["max_transfers"],
        "num_itineraries": round(base_budget * p["budget_mult"]),
        "search_window_s": round(base_window_s * p["window_mult"]),
    }


@dataclass
class Candidate:
    """A full-route candidate in the deepening pool (handbook §5.3)."""

    legs: list  # door-to-door decomposed Legs
    signature: tuple
    departure: object  # datetime
    arrival: object  # datetime
    alt_departures: list = field(default_factory=list)

    @classmethod
    def from_itinerary(cls, itinerary, *, tz=None) -> "Candidate":
        legs = decompose(itinerary, tz=tz)
        return cls(legs=legs, signature=route_signature(legs),
                   departure=itinerary.start, arrival=itinerary.end)

    @property
    def total_minutes(self) -> float:
        return (self.arrival - self.departure).total_seconds() / 60

    @property
    def transfers(self) -> int:
        return count_transfers(self.legs)

    @property
    def min_slack(self):
        return min_transfer_slack(self.legs)


def _collapse_pref(candidate: "Candidate") -> tuple:
    """Deterministic preference among **same-arrival** same-signature variants.

    Smaller wins: non-taxi first-mile over taxi (so a taxi feeder survives only
    when strictly faster, handbook §4.3), then a stable leg key. Independent of
    input order, and consistent with B4's collapse rule (``portfolio.cluster``).
    """
    legs = candidate.legs
    taxi = 1 if any(l.layer == "first_mile" and (l.mode or "").lower() == "taxi" for l in legs) else 0
    leg_key = tuple((l.layer, l.mode, l.from_, l.to, l.dep, l.arr, l.line or "") for l in legs)
    return (taxi, leg_key)


class CandidatePool:
    """Dedup pool keyed by backbone signature; monotone-accumulating (handbook §5.3)."""

    def __init__(self):
        self._by_sig = {}

    def add(self, candidate: Candidate) -> bool:
        """Add a candidate. Returns ``True`` if it was **added** (new signature) or
        **improved** an existing one (strictly earlier arrival replaces); ``False``
        for a no-improvement merge.

        The True cases are exactly what ε-termination must see (§5.4) — a deeper
        sweep that makes an existing route 50 min faster *is* a portfolio
        improvement, even though the backbone signature is unchanged.

        The signature ignores first-mile mode (§5.3), so a same-hub bus and taxi
        collapse here. The survivor is chosen deterministically (earlier arrival,
        else :func:`_collapse_pref` — non-taxi over taxi), so the kept variant
        never depends on input order. The other's departure is recorded as an
        additional service, preserving the headway picture.
        """
        cur = self._by_sig.get(candidate.signature)
        if cur is None:
            self._by_sig[candidate.signature] = candidate
            return True
        if candidate.arrival < cur.arrival:
            candidate.alt_departures = [*cur.alt_departures, cur.departure]
            self._by_sig[candidate.signature] = candidate
            return True  # improved: strictly earlier arrival
        # Equal/later arrival is not an ε-improvement; pick the survivor by a
        # deterministic preference so order does not change the emitted card.
        if candidate.arrival == cur.arrival and _collapse_pref(candidate) < _collapse_pref(cur):
            candidate.alt_departures = [*cur.alt_departures, cur.departure]
            self._by_sig[candidate.signature] = candidate
        else:
            cur.alt_departures.append(candidate.departure)
        return False

    def routes(self) -> list:
        return list(self._by_sig.values())

    def metrics(self):
        """Incumbent best per criterion, or ``None`` when the pool is empty (§5.4)."""
        rs = self.routes()
        if not rs:
            return None
        return {
            "best_time": min(r.total_minutes for r in rs),
            "best_slack": max((r.min_slack or 0.0) for r in rs),
            "min_transfers": min(r.transfers for r in rs),
        }


def _improves_any(new: list, incumbent, epsilon: Epsilon, creativity_of=None) -> bool:
    """ε-termination test: does any new route better an active criterion by > ε (§5.4)?

    Active Phase A criteria: E[T_eff] (= schedule time), structural slack, transfers,
    and — when a ``creativity_of`` callable is supplied — C(r).
    """
    if not new:
        return False
    if incumbent is None:  # pool was empty before this depth → any route improves
        return True
    for r in new:
        if incumbent["best_time"] - r.total_minutes > epsilon.time_min:
            return True
        if (r.min_slack or 0.0) - incumbent["best_slack"] > epsilon.time_min:
            return True
        if r.transfers < incumbent["min_transfers"]:
            return True
        if creativity_of is not None:
            if creativity_of(r) - (incumbent.get("best_creativity") or 0.0) > epsilon.creativity:
                return True
    return False


def deepen(plan_fn, *, depths: int = 3, base_budget: int = BASE_BUDGET,
           base_window_s: int = BASE_SEARCH_WINDOW_S, epsilon: Epsilon = None,
           creativity_of=None, tz=None) -> list:
    """Run Depth 0/1/2 progressive deepening into a deduplicated pool (handbook §5).

    ``plan_fn(params)`` returns the full-route itineraries for a depth's params
    (``depth``, ``max_transfers``, ``num_itineraries``, ``search_window_s``). The
    pool accumulates monotonically across depths; deepening halts once a depth's
    newly admitted routes fail to improve any active criterion beyond ε (Depth 0
    always runs, since the pool starts empty). Returns the candidate list.
    """
    epsilon = epsilon or Epsilon()
    pool = CandidatePool()
    for depth in range(depths):
        params = depth_params(depth, base_budget, base_window_s)
        incumbent = pool.metrics()
        if incumbent is not None and creativity_of is not None:
            incumbent["best_creativity"] = max(
                (creativity_of(r) for r in pool.routes()), default=None)
        new = []
        for itinerary in plan_fn(params):
            cand = Candidate.from_itinerary(itinerary, tz=tz)
            if pool.add(cand):
                new.append(cand)
        if not _improves_any(new, incumbent, epsilon, creativity_of):
            break
    return pool.routes()
