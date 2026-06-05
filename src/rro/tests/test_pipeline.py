"""End-to-end pipeline test over hand-built OTP itineraries (handbook §2.3), offline."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from rro.config import parse_config
from rro.graph.otp_client import OTPItinerary, OTPLeg
from rro.pipeline import plan_portfolio
from rro.portfolio.output import portfolio_to_dict, to_json
from rro.routing.decompose import feeder_hub

_GOLDEN = Path(__file__).parent / "golden" / "expected_pipeline_portfolio.json"
_T0 = datetime(2026, 6, 8, 7, 0, tzinfo=timezone.utc)


def _m(mins):
    return _T0 + timedelta(minutes=mins)


def _leg(mode, frm, to, s, e, line=None, km=None):
    return OTPLeg(mode, frm, to, _m(s), _m(e), route_short_name=line,
                  distance=(km * 1000 if km is not None else None))


def _itin(legs):
    return OTPItinerary(start=legs[0].start, end=legs[-1].end, legs=legs)


# First-mile itineraries (origin → hub): both survive dominance (time vs transfers).
_FM_WUPPERTAL = _itin([_leg("BUS", "Haßlinghausen", "Wuppertal Hbf", 10, 45)])           # arr 07:45, 0 transfers
_FM_HAGEN = _itin([_leg("BUS", "Haßlinghausen", "Schwelm", 5, 25),                        # arr 07:40, 1 transfer
                   _leg("BUS", "Schwelm", "Hagen Hbf", 28, 40)])

# Backbone itineraries (hub → Freiburg).
_FR = "Freiburg (Breisgau) Hbf"
_BB = {
    "Wuppertal Hbf": [
        _itin([_leg("RAIL", "Wuppertal Hbf", _FR, 56, 295, "ICE 1", 500)]),               # bb1: direct, 500 km
        _itin([_leg("RAIL", "Wuppertal Hbf", "Köln Hbf", 56, 100, "RE", 60),              # bb2: via Köln, 510 km
               _leg("RAIL", "Köln Hbf", _FR, 110, 285, "ICE 105", 450)]),
    ],
    "Hagen Hbf": [
        _itin([_leg("RAIL", "Hagen Hbf", "Köln Hbf", 51, 95, "RE2", 55),                  # bb3: via Köln, 505 km
               _leg("RAIL", "Köln Hbf", _FR, 110, 300, "ICE 105", 450)]),
        _itin([_leg("RAIL", "Hagen Hbf", "Frankfurt (Main) Hbf", 51, 150, "IC", 220),     # bb4: off-trunk, 460 km
               _leg("RAIL", "Frankfurt (Main) Hbf", _FR, 160, 305, "ICE 73", 240)]),
    ],
}


def _hub_plan_fn(origin, departure, t_first_minutes):
    return [_FM_WUPPERTAL, _FM_HAGEN]


def _backbone_plan_fn(hub_arrival, destination, params):
    return _BB.get(hub_arrival.hub_id, [])


def _config():
    return parse_config({
        "origin": "Haßlinghausen",
        "destination": _FR,
        "departure_time": "2026-06-08T07:00:00+02:00",
        "feeds": [
            {"id": "g", "kind": "gtfs", "url": "u"},
            {"id": "osm", "kind": "osm_pbf", "url": "u"},
        ],
    })


def _portfolio():
    return plan_portfolio(
        _config(), "2026-06-08T07:00:00+02:00",
        hub_plan_fn=_hub_plan_fn, backbone_plan_fn=_backbone_plan_fn,
        generated_at="2026-06-05T00:00:00+02:00",
    )


def test_pipeline_produces_full_portfolio():
    p = _portfolio()
    assert [s.cluster for s in p.strategies] == ["fastest", "robust", "low_transfer", "creative"]
    by = {s.cluster: s for s in p.strategies}
    # Fastest = Wuppertal via Köln (275 min); robust = the 1-transfer Wuppertal direct.
    assert by["fastest"].score.E_T_eff_min == 275
    assert by["robust"].score.transfers == 1
    # Creative = the off-trunk Hagen→Frankfurt route (not in R → C = 1).
    assert by["creative"].score.creativity == 1.0
    assert feeder_hub(by["creative"].legs) == "Hagen Hbf"
    # Reference corridors are the top-3 backbones by km.
    assert len(p.reference_corridors) == 3


def test_pipeline_scoring_invariants():
    p = _portfolio()
    for s in p.strategies:
        sc = s.score
        assert sc.Q08_T_eff_min == sc.E_T_eff_min                        # degenerate
        assert abs((sc.Q08_T_eff_min - 0.7 * sc.creativity) - sc.J) < 0.06
        if sc.backbone_km:
            assert abs((1 - sc.reference_km / sc.backbone_km) - sc.creativity) < 0.005
        assert s.card.confidence == "scheduled"
        assert s.card.transfers == sc.transfers == len(s.card.transfer_stations)


def test_pipeline_golden_matches():
    expected = json.loads(_GOLDEN.read_text(encoding="utf-8"))
    assert portfolio_to_dict(_portfolio()) == expected
