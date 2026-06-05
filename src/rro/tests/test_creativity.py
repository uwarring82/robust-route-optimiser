"""Tests for the two-pass creativity reference set R and C(r) (handbook §6.3)."""

from __future__ import annotations

from rro.models import Leg
from rro.scoring.creativity import (
    backbone_km_of,
    calibrate_reference,
    creativity_of_route,
    reference_km_of,
)


def _bb(line, frm, to, km):
    return Leg("backbone", "rail", frm, to, "07:00", "08:00", line, None, distance_m=km * 1000)


def _route(*legs):
    return list(legs)


def test_calibrate_reference_top3_by_km():
    routes = [
        _route(_bb("L1", "A", "FR", 500)),
        _route(_bb("L2", "B", "FR", 510)),
        _route(_bb("L3", "C", "FR", 505)),
        _route(_bb("L4", "D", "FR", 460)),   # 4th by km → not in R
    ]
    ref = calibrate_reference(routes)
    assert [round(c.backbone_km) for c in ref.corridors] == [510, 505, 500]
    assert ("L2", "B", "FR") in ref.leg_keys
    assert ("L4", "D", "FR") not in ref.leg_keys


def test_creativity_fully_on_R_is_zero_off_R_is_one():
    r_on = _route(_bb("L2", "B", "FR", 510))
    r_off = _route(_bb("L4", "D", "FR", 460))
    ref = calibrate_reference([
        _route(_bb("L1", "A", "FR", 500)), r_on,
        _route(_bb("L3", "C", "FR", 505)), r_off,
    ])
    assert creativity_of_route(r_on, ref) == 0.0
    assert creativity_of_route(r_off, ref) == 1.0


def test_partial_overlap_gives_fractional_creativity():
    # A route sharing one of its two equal-length backbone legs with R.
    shared = _bb("TRUNK", "X", "FR", 250)
    own = _bb("OFF", "Y", "X", 250)
    ref = calibrate_reference([
        _route(shared, _bb("T2", "Z", "X", 300)),   # in R, contains TRUNK X→FR
        _route(_bb("A1", "P", "FR", 600)),
        _route(_bb("A2", "Q", "FR", 590)),
    ])
    r = _route(own, shared)  # 500 km total, 250 on R → C = 0.5
    assert backbone_km_of(r) == 500.0
    assert reference_km_of(r, ref) == 250.0
    assert creativity_of_route(r, ref) == 0.5


def test_corridor_ids_are_slugged_and_deterministic():
    ref = calibrate_reference([
        _route(_bb("ICE", "Wuppertal Hbf", "Freiburg (Breisgau) Hbf", 500)),
        _route(_bb("ICE", "Hagen Hbf", "Freiburg (Breisgau) Hbf", 510)),
    ])
    ids = [c.corridor_id for c in ref.corridors]
    assert ids == ["hagen-hbf-freiburg-breisgau-hbf", "wuppertal-hbf-freiburg-breisgau-hbf"]
