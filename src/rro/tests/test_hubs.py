"""Tests for B2 hub discovery: first-mile itineraries -> HubArrival (handbook §4.2)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from rro.graph.otp_client import OTPItinerary, OTPLeg
from rro.routing.dominance import pareto_frontier
from rro.routing.hubs import hub_arrival, hub_arrivals

_T0 = datetime(2026, 6, 8, 7, 0, tzinfo=timezone.utc)


def _leg(mode, frm, to, start_min, end_min, *, to_stop=None):
    return OTPLeg(
        mode=mode, from_name=frm, to_name=to,
        start=_T0 + timedelta(minutes=start_min), end=_T0 + timedelta(minutes=end_min),
        to_stop_id=to_stop,
    )


def _itin(legs):
    return OTPItinerary(start=legs[0].start, end=legs[-1].end, legs=legs)


def test_hub_arrival_from_single_bus_leg():
    it = _itin([_leg("BUS", "Haßlinghausen", "Wuppertal Hbf", 0, 30, to_stop="de:05124:1")])
    ha = hub_arrival(it, cost_eur=4.5)
    assert ha.hub_id == "de:05124:1"            # prefers gtfsId
    assert ha.transfers == 0                     # one transit leg
    assert ha.first_mile_mode == "bus"
    assert ha.cost_eur == 4.5
    assert ha.arrival_time.endswith("+00:00")    # offset-aware


def test_hub_arrival_counts_transfers():
    it = _itin([
        _leg("BUS", "Haßlinghausen", "Schwelm", 0, 15),
        _leg("BUS", "Schwelm", "Wuppertal Hbf", 18, 35),
    ])
    assert hub_arrival(it).transfers == 1


def test_hub_arrival_falls_back_to_name_without_stop_id():
    it = _itin([_leg("BUS", "Haßlinghausen", "Gevelsberg", 0, 20)])
    assert hub_arrival(it).hub_id == "Gevelsberg"


def test_empty_itinerary_raises():
    with pytest.raises(ValueError):
        hub_arrival(OTPItinerary(start=_T0, end=_T0, legs=[]))


def test_hub_arrivals_filters_by_t_first():
    within = _itin([_leg("BUS", "Haßlinghausen", "Wuppertal Hbf", 0, 30)])      # 30 min
    over = _itin([_leg("BUS", "Haßlinghausen", "Dortmund Hbf", 0, 55)])          # 55 min
    hubs = hub_arrivals([within, over], t_first_minutes=45)
    assert [h.hub_id for h in hubs] == ["Wuppertal Hbf"]


def test_hub_arrivals_feed_dominance_filter():
    # Two reachable hubs; the strictly-worse one is pruned by static dominance.
    a = _itin([_leg("BUS", "Haßlinghausen", "Wuppertal Hbf", 0, 30)])
    b = _itin([_leg("BUS", "Haßlinghausen", "Hagen Hbf", 0, 40)])  # later, same cost/transfers
    hubs = hub_arrivals([a, b], t_first_minutes=45)
    front = pareto_frontier(hubs)
    assert {h.hub_id for h in front} == {"Wuppertal Hbf"}
