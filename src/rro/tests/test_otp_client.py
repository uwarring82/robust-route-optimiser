"""Tests for the OTP GraphQL client against recorded responses (handbook §3.5, §5.2)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from rro.graph.otp_client import (
    DEFAULT_MODES,
    OTPClient,
    OTPError,
    parse_itinerary,
)

# A recorded OTP 2.x GTFS GraphQL `plan` response: bus feeder + ICE backbone.
# Epoch ms chosen to be readable in UTC.
_DEP_MS = 1_781_503_800_000        # 2026-06-14T22:10:00Z (value is arbitrary but fixed)
_RECORDED = {
    "data": {
        "plan": {
            "itineraries": [
                {
                    "startTime": _DEP_MS,
                    "endTime": _DEP_MS + 13_200_000,  # +3h40m
                    "legs": [
                        {
                            "mode": "BUS",
                            "startTime": _DEP_MS,
                            "endTime": _DEP_MS + 1_800_000,  # +30m
                            "from": {"name": "Haßlinghausen", "stop": {"gtfsId": "de:05954:1"}},
                            "to": {"name": "Wuppertal Hbf", "stop": {"gtfsId": "de:05124:1"}},
                            "route": {"shortName": "CE61"},
                            "trip": {"gtfsId": "de:trip:1"},
                        },
                        {
                            "mode": "RAIL",
                            "startTime": _DEP_MS + 2_400_000,
                            "endTime": _DEP_MS + 13_200_000,
                            "from": {"name": "Wuppertal Hbf", "stop": {"gtfsId": "de:05124:1"}},
                            "to": {"name": "Freiburg (Breisgau) Hbf", "stop": {"gtfsId": "de:08311:1"}},
                            "route": {"shortName": "ICE 105"},
                            "trip": {"gtfsId": "de:trip:2"},
                        },
                    ],
                }
            ]
        }
    }
}


def _client(response, capture=None):
    def transport(query, variables):
        if capture is not None:
            capture["query"] = query
            capture["variables"] = variables
        if isinstance(response, Exception):
            raise response
        return response
    return OTPClient("http://localhost:8080/otp/gtfs/v1", transport=transport)


def test_plan_parses_recorded_response():
    itins = _client(_RECORDED).plan(
        (51.32, 7.27), (47.99, 7.84), "2026-06-08T07:30:00+02:00",
        num_itineraries=6, max_transfers=1, search_window_s=3600,
    )
    assert len(itins) == 1
    legs = itins[0].legs
    assert [l.mode for l in legs] == ["BUS", "RAIL"]
    assert legs[0].route_short_name == "CE61"
    assert legs[1].route_short_name == "ICE 105"
    assert legs[0].from_name == "Haßlinghausen"
    assert legs[1].to_name == "Freiburg (Breisgau) Hbf"
    assert legs[1].to_stop_id == "de:08311:1"
    assert legs[0].trip_id == "de:trip:1"


def test_plan_converts_epoch_ms_to_offset_aware_utc():
    itins = _client(_RECORDED).plan(
        (51.32, 7.27), (47.99, 7.84), "2026-06-08T07:30:00+02:00",
        num_itineraries=6, max_transfers=1, search_window_s=3600,
    )
    leg0 = itins[0].legs[0]
    assert leg0.start == datetime.fromtimestamp(_DEP_MS / 1000, tz=timezone.utc)
    assert leg0.start.tzinfo is not None
    assert (leg0.end - leg0.start).total_seconds() == 1800  # 30 min


def test_plan_builds_query_variables():
    cap = {}
    _client(_RECORDED, capture=cap).plan(
        {"lat": 51.32, "lon": 7.27}, (47.99, 7.84), "2026-06-08T07:30:00+02:00",
        num_itineraries=6, max_transfers=2, search_window_s=5400,
    )
    v = cap["variables"]
    assert v["from"] == {"lat": 51.32, "lon": 7.27}
    assert v["to"] == {"lat": 47.99, "lon": 7.84}
    assert v["date"] == "2026-06-08" and v["time"] == "07:30:00"
    assert v["numItineraries"] == 6
    assert v["maxTransfers"] == 2
    assert v["searchWindow"] == 5400
    assert v["modes"] == DEFAULT_MODES
    assert "plan(" in cap["query"]


def test_empty_itineraries_returns_empty_list():
    resp = {"data": {"plan": {"itineraries": []}}}
    assert _client(resp).plan((0, 0), (1, 1), "2026-06-08T07:30:00+02:00",
                              num_itineraries=6, max_transfers=1, search_window_s=3600) == []


def test_graphql_errors_raise_otp_error():
    resp = {"errors": [{"message": "Unknown argument 'maxTransfers'"}], "data": None}
    with pytest.raises(OTPError, match="maxTransfers"):
        _client(resp).plan((0, 0), (1, 1), "2026-06-08T07:30:00+02:00",
                           num_itineraries=6, max_transfers=1, search_window_s=3600)


def test_null_plan_raises_otp_error():
    resp = {"data": {"plan": None}}
    with pytest.raises(OTPError, match="no plan"):
        _client(resp).plan((0, 0), (1, 1), "2026-06-08T07:30:00+02:00",
                           num_itineraries=6, max_transfers=1, search_window_s=3600)


def test_transport_exception_normalised_to_otp_error():
    with pytest.raises(OTPError, match="transport error"):
        _client(RuntimeError("connection refused")).plan(
            (0, 0), (1, 1), "2026-06-08T07:30:00+02:00",
            num_itineraries=6, max_transfers=1, search_window_s=3600)


def test_non_dict_response_raises():
    with pytest.raises(OTPError, match="not a JSON object"):
        _client("oops").plan((0, 0), (1, 1), "2026-06-08T07:30:00+02:00",
                             num_itineraries=6, max_transfers=1, search_window_s=3600)


def test_parse_itinerary_directly():
    it = parse_itinerary(_RECORDED["data"]["plan"]["itineraries"][0])
    assert len(it.legs) == 2
    assert it.end > it.start


def test_query_schema_types_match_otp_2x():
    from rro.graph.otp_client import PLAN_QUERY
    assert "$searchWindow: Long" in PLAN_QUERY          # seconds, not Int
    assert "$modes: [TransportMode]" in PLAN_QUERY      # nullable list elements
    assert "[TransportMode!]" not in PLAN_QUERY          # not the non-null-element form


def _plan(resp):
    return _client(resp).plan((0, 0), (1, 1), "2026-06-08T07:30:00+02:00",
                              num_itineraries=6, max_transfers=1, search_window_s=3600)


def _wrap_itin(itin):
    return {"data": {"plan": {"itineraries": [itin]}}}


def test_missing_leg_mode_raises_otp_error():
    bad = _wrap_itin({"startTime": _DEP_MS, "endTime": _DEP_MS + 1000,
                      "legs": [{"startTime": _DEP_MS, "endTime": _DEP_MS + 1000,
                                "from": {}, "to": {}}]})
    with pytest.raises(OTPError, match="mode"):
        _plan(bad)


def test_null_legs_raises_otp_error():
    bad = _wrap_itin({"startTime": _DEP_MS, "endTime": _DEP_MS + 1000, "legs": None})
    with pytest.raises(OTPError, match="legs"):
        _plan(bad)


def test_non_numeric_time_raises_otp_error():
    bad = _wrap_itin({"startTime": "not-a-number", "endTime": _DEP_MS, "legs": []})
    with pytest.raises(OTPError, match="time"):
        _plan(bad)


def test_itinerary_not_object_raises_otp_error():
    with pytest.raises(OTPError):
        _plan({"data": {"plan": {"itineraries": ["oops"]}}})
