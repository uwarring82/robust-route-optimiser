"""Tests for B1 decomposition: OTP itinerary -> layered domain legs (handbook §4.1)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from rro.graph.otp_client import OTPItinerary, OTPLeg
from rro.routing.decompose import decompose, feeder_hub

_T0 = datetime(2026, 6, 8, 7, 0, tzinfo=timezone.utc)


def _leg(mode, frm, to, start_min, end_min, line=None):
    return OTPLeg(
        mode=mode, from_name=frm, to_name=to,
        start=_T0 + timedelta(minutes=start_min), end=_T0 + timedelta(minutes=end_min),
        route_short_name=line,
    )


def _leg_s(mode, frm, to, start_s, end_s):
    return OTPLeg(
        mode=mode, from_name=frm, to_name=to,
        start=_T0 + timedelta(seconds=start_s), end=_T0 + timedelta(seconds=end_s),
    )


def _itin(legs):
    return OTPItinerary(start=legs[0].start, end=legs[-1].end, legs=legs)


def test_first_mile_plus_backbone():
    it = _itin([
        _leg("BUS", "Haßlinghausen", "Wuppertal Hbf", 0, 30, "CE61"),
        _leg("RAIL", "Wuppertal Hbf", "Freiburg (Breisgau) Hbf", 41, 270, "ICE 105"),
    ])
    legs = decompose(it)
    assert [l.layer for l in legs] == ["first_mile", "backbone"]
    assert [l.mode for l in legs] == ["bus", "rail"]
    assert feeder_hub(legs) == "Wuppertal Hbf"
    assert legs[0].transfer_slack_min == 11   # 41 - 30
    assert legs[-1].transfer_slack_min is None  # terminal


def test_first_backbone_backbone_lastmile():
    it = _itin([
        _leg("BUS", "Haßlinghausen", "Hagen Hbf", 0, 30, "VER 591"),
        _leg("RAIL", "Hagen Hbf", "Köln Hbf", 41, 100, "ICE 945"),
        _leg("RAIL", "Köln Hbf", "Freiburg (Breisgau) Hbf", 110, 280, "ICE 105"),
        _leg("TRAM", "Freiburg (Breisgau) Hbf", "Freiburg Innenstadt", 286, 292, "1"),
    ])
    legs = decompose(it)
    assert [l.layer for l in legs] == ["first_mile", "backbone", "backbone", "last_mile"]
    assert feeder_hub(legs) == "Hagen Hbf"


def test_ends_at_rail_hub_has_no_last_mile():
    it = _itin([
        _leg("BUS", "Haßlinghausen", "Wuppertal Hbf", 0, 30, "CE61"),
        _leg("RAIL", "Wuppertal Hbf", "Freiburg (Breisgau) Hbf", 41, 270, "ICE 105"),
    ])
    assert all(l.layer != "last_mile" for l in decompose(it))


def test_tz_localisation():
    from zoneinfo import ZoneInfo
    it = _itin([_leg("RAIL", "A", "B", 0, 60, "ICE")])
    leg = decompose(it, tz=ZoneInfo("Europe/Berlin"))[0]
    assert leg.dep.endswith("+02:00")  # 2026-06-08 is CEST


def test_no_rail_falls_back_to_transit_span():
    it = _itin([
        _leg("WALK", "Origin", "Bus Stop", 0, 5),
        _leg("BUS", "Bus Stop", "Town", 6, 26, "100"),
        _leg("WALK", "Town", "Dest", 27, 32),
    ])
    legs = decompose(it)
    assert [l.layer for l in legs] == ["first_mile", "backbone", "last_mile"]


def test_first_mile_segment_with_trailing_walk_needs_role():
    # BUS origin->stop, WALK stop->hub: with the default door_to_door heuristic
    # there is no rail, so this would be mislabelled. role="first_mile" tags all.
    it = _itin([
        _leg("BUS", "Haßlinghausen", "Bus Stop", 0, 20, "100"),
        _leg("WALK", "Bus Stop", "Wuppertal Hbf", 21, 26),
    ])
    legs = decompose(it, role="first_mile")
    assert [l.layer for l in legs] == ["first_mile", "first_mile"]
    assert feeder_hub(legs) is None  # a segment has no backbone leg


def test_unknown_role_raises():
    it = _itin([_leg("RAIL", "A", "B", 0, 60)])
    with pytest.raises(ValueError, match="role"):
        decompose(it, role="middle")


def test_slack_preserves_sub_minute():
    # 30-second buffer must not collapse to 0 (precise float).
    it = _itin([_leg_s("RAIL", "A", "B", 0, 600), _leg_s("RAIL", "B", "C", 630, 1200)])
    assert decompose(it)[0].transfer_slack_min == 0.5


def test_decompose_via_real_parser():
    # Full path: a recorded OTP response -> parse_itinerary -> decompose.
    from rro.graph.otp_client import parse_itinerary
    ms = 1_781_503_800_000
    raw = {
        "startTime": ms, "endTime": ms + 13_200_000,
        "legs": [
            {"mode": "BUS", "startTime": ms, "endTime": ms + 1_800_000,
             "from": {"name": "Haßlinghausen"}, "to": {"name": "Wuppertal Hbf"},
             "route": {"shortName": "CE61"}, "trip": {"gtfsId": "t1"}},
            {"mode": "RAIL", "startTime": ms + 2_400_000, "endTime": ms + 13_200_000,
             "from": {"name": "Wuppertal Hbf"}, "to": {"name": "Freiburg (Breisgau) Hbf"},
             "route": {"shortName": "ICE 105"}, "trip": {"gtfsId": "t2"}},
        ],
    }
    legs = decompose(parse_itinerary(raw))
    assert [l.layer for l in legs] == ["first_mile", "backbone"]
    assert legs[1].line == "ICE 105"
