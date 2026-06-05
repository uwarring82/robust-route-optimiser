"""Tests for the B3 progressive-deepening controller (handbook §5)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from rro.config import Epsilon
from rro.graph.otp_client import OTPItinerary, OTPLeg
from rro.routing.deepening import (
    Candidate,
    CandidatePool,
    deepen,
    depth_params,
)

_T0 = datetime(2026, 6, 8, 7, 0, tzinfo=timezone.utc)


def _m(mins):
    return _T0 + timedelta(minutes=mins)


def _route(hub, line, dep_min, arr_min):
    """A full route: bus Haßlinghausen→hub, rail hub→Freiburg."""
    hub_arr = dep_min + 30
    bus = OTPLeg("BUS", "Haßlinghausen", hub, _m(dep_min), _m(hub_arr))
    rail = OTPLeg("RAIL", hub, "Freiburg (Breisgau) Hbf", _m(hub_arr + 11), _m(arr_min),
                  route_short_name=line)
    return OTPItinerary(start=bus.start, end=rail.end, legs=[bus, rail])


def _plan_fn(by_depth):
    calls = []

    def plan_fn(params):
        calls.append(params["depth"])
        return by_depth.get(params["depth"], [])

    plan_fn.calls = calls
    return plan_fn


# --- depth ladder ----------------------------------------------------------

def test_depth_params_ladder():
    assert depth_params(0)["max_transfers"] == 1
    assert depth_params(0)["num_itineraries"] == 6
    assert depth_params(1)["max_transfers"] == 2
    assert depth_params(2)["num_itineraries"] == 15    # round(6 * 2.5)
    assert depth_params(2)["search_window_s"] == 9000  # round(3600 * 2.5)


def test_depth_params_clamps_beyond_two():
    p2, p3 = depth_params(2), depth_params(3)
    assert p3["depth"] == 3
    assert {k: p3[k] for k in p3 if k != "depth"} == {k: p2[k] for k in p2 if k != "depth"}


# --- candidate + pool ------------------------------------------------------

def test_candidate_metrics():
    c = Candidate.from_itinerary(_route("Wuppertal Hbf", "ICE 1", 0, 270))
    assert c.signature == (("ICE 1", "Wuppertal Hbf", "Freiburg (Breisgau) Hbf"),)
    assert c.total_minutes == 270
    assert c.transfers == 1                     # first-mile → backbone at Wuppertal
    assert c.min_slack == 11                     # bus arr +11 → rail dep


def test_pool_dedup_keeps_earlier_arrival_and_records_alt():
    pool = CandidatePool()
    early = Candidate.from_itinerary(_route("Wuppertal Hbf", "ICE 1", 0, 270))    # arr 11:30
    late = Candidate.from_itinerary(_route("Wuppertal Hbf", "ICE 1", 60, 360))    # same sig, arr 13:00
    assert pool.add(early) is True
    assert pool.add(late) is False              # merged, not added
    [kept] = pool.routes()
    assert kept.arrival == early.arrival         # earlier kept
    assert late.departure not in [kept.departure]
    assert kept.alt_departures == [late.departure]


def test_pool_merge_replaces_when_earlier_added_second():
    pool = CandidatePool()
    late = Candidate.from_itinerary(_route("Wuppertal Hbf", "ICE 1", 60, 360))
    early = Candidate.from_itinerary(_route("Wuppertal Hbf", "ICE 1", 0, 270))
    pool.add(late)
    pool.add(early)
    [kept] = pool.routes()
    assert kept.arrival == early.arrival
    assert kept.alt_departures == [late.departure]


# --- deepening + ε-termination ---------------------------------------------

def test_deepen_stops_when_a_depth_adds_nothing_new():
    a = _route("Wuppertal Hbf", "ICE 1", 0, 270)
    plan = _plan_fn({0: [a], 1: [a]})           # depth 1 re-returns the same route
    routes = deepen(plan, depths=3, epsilon=Epsilon(3, 0.05))
    assert plan.calls == [0, 1]                  # depth 2 never reached
    assert len(routes) == 1


def test_deepen_continues_while_improving():
    slow = _route("Wuppertal Hbf", "ICE 1", 0, 280)
    fast = _route("Hagen Hbf", "ICE 2", 0, 250)   # distinct sig, faster → improves
    plan = _plan_fn({0: [slow], 1: [fast], 2: []})
    routes = deepen(plan, depths=3, epsilon=Epsilon(3, 0.05))
    assert plan.calls == [0, 1, 2]                # depth 1 improved, so depth 2 ran
    assert len(routes) == 2


def test_deepen_stops_when_improvement_below_epsilon():
    base = _route("Wuppertal Hbf", "ICE 1", 0, 280)
    barely = _route("Hagen Hbf", "ICE 2", 0, 279)  # 1 min faster < ε.time_min(3)
    plan = _plan_fn({0: [base], 1: [barely]})
    routes = deepen(plan, depths=3, epsilon=Epsilon(3, 0.05))
    assert plan.calls == [0, 1]                   # 1-min gain does not justify depth 2
    assert len(routes) == 2                        # but both distinct routes are kept


def test_deepen_runs_deeper_after_same_signature_improvement():
    # A deeper sweep that makes an existing route 50 min faster IS an improvement,
    # even though the backbone signature is unchanged — deepening must continue.
    slow = _route("Wuppertal Hbf", "ICE 1", 0, 280)   # Depth 0
    fast = _route("Wuppertal Hbf", "ICE 1", 0, 230)   # Depth 1: same sig, 50 min faster
    plan = _plan_fn({0: [slow], 1: [fast], 2: []})
    routes = deepen(plan, depths=3, epsilon=Epsilon(3, 0.05))
    assert plan.calls == [0, 1, 2]                     # the improvement kept deepening alive
    assert len(routes) == 1                            # same signature, merged
    assert routes[0].total_minutes == 230              # the faster variant kept


def test_pool_add_signals_improvement():
    pool = CandidatePool()
    slow = Candidate.from_itinerary(_route("Wuppertal Hbf", "ICE 1", 0, 280))
    fast = Candidate.from_itinerary(_route("Wuppertal Hbf", "ICE 1", 0, 230))
    assert pool.add(slow) is True   # added
    assert pool.add(fast) is True   # improved (earlier arrival)
    same = Candidate.from_itinerary(_route("Wuppertal Hbf", "ICE 1", 0, 230))
    assert pool.add(same) is False  # no improvement → merge


def test_deepen_accumulates_monotonically():
    a = _route("Wuppertal Hbf", "ICE 1", 0, 280)
    b = _route("Hagen Hbf", "ICE 2", 0, 250)
    c = _route("Witten Hbf", "ICE 3", 0, 240)
    plan = _plan_fn({0: [a], 1: [b], 2: [c]})
    routes = deepen(plan, depths=3, epsilon=Epsilon(3, 0.05))
    sigs = {r.signature for r in routes}
    assert len(sigs) == 3                          # pool never resets across depths


def test_deepen_empty_first_depth_stops():
    plan = _plan_fn({})                            # nothing anywhere
    routes = deepen(plan, depths=3)
    assert plan.calls == [0]
    assert routes == []
