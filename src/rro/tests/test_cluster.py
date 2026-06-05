"""Unit tests for B4 clustering and a synthetic golden portfolio (handbook §7.1, §7.2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rro.models import (
    Leg,
    Portfolio,
    ReferenceCorridor,
    Score,
    ScoredCandidate,
)
from rro.portfolio.cluster import UnderfullPortfolioError, cluster
from rro.portfolio.output import portfolio_to_dict, to_json

_GOLDEN = Path(__file__).parent / "golden" / "expected_portfolio.json"
_D = "2026-06-08T"
_TZ = "+02:00"


def _t(hhmm: str) -> str:
    return f"{_D}{hhmm}:00{_TZ}"


def _cand(*, hub, lines, arr, e, creativity, transfers, slack, fragile,
          backbone_km, reference_km, price):
    """Build a consistent ScoredCandidate. ``lines`` lists the backbone legs as
    (from, to, line, slack); the first-mile leg carries the transfer slack."""
    legs = [Leg("first_mile", "bus", "Haßlinghausen", hub, _t("07:10"), _t("07:40"),
                "VER 1", slack)]
    for frm, to, line, lslack, ldep, larr in lines:
        legs.append(Leg("backbone", "rail", frm, to, _t(ldep), _t(larr), line, lslack))
    score = Score(
        J=round(e - 0.7 * creativity, 1), Q08_T_eff_min=e, E_T_eff_min=e,
        creativity=creativity, transfers=transfers, min_transfer_slack_min=slack,
        fragile_legs=fragile, backbone_km=backbone_km, reference_km=reference_km,
    )
    return ScoredCandidate(legs=legs, score=score, price_eur=price)


def _fastest():
    return _cand(hub="Hagen Hbf",
                 lines=[("Hagen Hbf", "Köln Hbf", "ICE 945", 9, "07:51", "08:49"),
                        ("Köln Hbf", "Freiburg (Breisgau) Hbf", "ICE 105", None, "08:58", "12:00")],
                 arr="12:00", e=283.0, creativity=0.16, transfers=2, slack=11, fragile=0,
                 backbone_km=512.4, reference_km=430.4, price=84.90)


def _robust():
    return _cand(hub="Wuppertal Hbf",
                 lines=[("Wuppertal Hbf", "Freiburg (Breisgau) Hbf", "ICE 103", None, "07:58", "12:14")],
                 arr="12:14", e=297.0, creativity=0.21, transfers=1, slack=18, fragile=0,
                 backbone_km=505.7, reference_km=399.5, price=84.90)


def _creative():
    return _cand(hub="Witten Hbf",
                 lines=[("Witten Hbf", "Mannheim Hbf", "IC 2304", 12, "07:50", "10:38"),
                        ("Mannheim Hbf", "Freiburg (Breisgau) Hbf", "ICE 73", None, "10:50", "12:26")],
                 arr="12:26", e=309.0, creativity=0.58, transfers=2, slack=14, fragile=1,
                 backbone_km=547.9, reference_km=230.1, price=72.40)


def test_underfull_one_candidate_raises():
    with pytest.raises(UnderfullPortfolioError):
        cluster([_fastest()])


def test_underfull_same_signature_collapses_and_raises():
    # Two candidates with the identical backbone signature collapse to one route.
    a = _robust()
    b = _robust()
    with pytest.raises(UnderfullPortfolioError):
        cluster([a, b])


def test_two_distinct_give_two_strategies_in_precedence_order():
    strategies = cluster([_robust(), _fastest()])
    assert [s.cluster for s in strategies] == ["fastest", "robust"]


def test_three_routes_yield_fastest_robust_creative():
    # The §7.2 outcome: low_transfer is dropped (the fewest-transfer route is the
    # robust one), creative keeps the off-backbone high-C(r) route.
    strategies = cluster([_fastest(), _robust(), _creative()])
    assert [s.cluster for s in strategies] == ["fastest", "robust", "creative"]
    by = {s.cluster: s for s in strategies}
    assert by["fastest"].legs[0].to == "Hagen Hbf"
    assert by["robust"].legs[0].to == "Wuppertal Hbf"
    assert by["creative"].legs[0].to == "Witten Hbf"
    # Robust is the fewest-transfer route (structural proxy), not the fastest.
    assert by["robust"].score.transfers == 1


def test_precedence_resolves_a_direct_contest():
    # A is best for fastest AND low_transfer; B robust; C creative-ish.
    a = _cand(hub="A-Hub", lines=[("A-Hub", "Freiburg (Breisgau) Hbf", "ICE A", None, "07:51", "11:30")],
              arr="11:30", e=250.0, creativity=0.0, transfers=1, slack=10, fragile=0,
              backbone_km=400.0, reference_km=400.0, price=None)  # fastest + fewest transfers
    b = _cand(hub="B-Hub", lines=[("B-Hub", "X", "R1", 8, "07:51", "08:40"),
                                  ("X", "Freiburg (Breisgau) Hbf", "R2", None, "08:50", "12:00")],
              arr="12:00", e=300.0, creativity=0.1, transfers=2, slack=20, fragile=0,
              backbone_km=420.0, reference_km=380.0, price=None)
    c = _cand(hub="C-Hub", lines=[("C-Hub", "Y", "R3", 9, "07:51", "09:10"),
                                  ("Y", "Freiburg (Breisgau) Hbf", "R4", None, "09:20", "12:30")],
              arr="12:30", e=330.0, creativity=0.7, transfers=2, slack=9, fragile=1,
              backbone_km=500.0, reference_km=150.0, price=None)
    strategies = cluster([a, b, c])
    by = {s.cluster: s.legs[0].to for s in strategies}
    # A contested by fastest & low_transfer → fastest wins (higher precedence).
    assert by["fastest"] == "A-Hub"
    assert by["creative"] == "C-Hub"
    # low_transfer re-nominates; with A taken it has no distinct fewest-transfer
    # route left that isn't already robust/creative, so it is dropped.
    assert "low_transfer" not in by


def test_caps_at_four_strategies():
    cands = [
        _cand(hub=f"H{i}", lines=[(f"H{i}", "Freiburg (Breisgau) Hbf", f"L{i}", None, "07:51", "11:30")],
              arr="11:30", e=250.0 + i, creativity=0.1 * i, transfers=1 + (i % 3), slack=10 + i,
              fragile=0, backbone_km=400.0 + i, reference_km=200.0, price=None)
        for i in range(5)
    ]
    strategies = cluster(cands)
    assert len(strategies) == 4
    assert [s.cluster for s in strategies] == ["fastest", "robust", "low_transfer", "creative"]


# --- synthetic golden portfolio (locks the B4 → Layer C seam) ---------------

def _synthetic_portfolio() -> Portfolio:
    strategies = cluster([_fastest(), _robust(), _creative()])
    return Portfolio(
        query={
            "origin": "Haßlinghausen",
            "destination": "Freiburg (Breisgau) Hbf",
            "departure_time": "2026-06-08T07:30:00+02:00",
            "generated_at": "2026-06-05T00:00:00+02:00",  # fixed for the golden
            "coastline_version": "0.6.0-rc1",
            "engine_version": "0.1.0-a",
        },
        parameters={"alpha_c": 0.7, "quantile": 0.8, "t_first_minutes": 45,
                    "epsilon": 3, "mode": "deterministic"},
        reference_corridors=[
            ReferenceCorridor("hagen-koeln-mainz-freiburg", 512.4),
            ReferenceCorridor("hagen-koeln-frankfurt-freiburg", 505.7),
            ReferenceCorridor("wuppertal-koeln-frankfurt-freiburg", 498.1),
        ],
        strategies=strategies,
    )


def test_golden_portfolio_matches():
    expected = json.loads(_GOLDEN.read_text(encoding="utf-8"))
    assert portfolio_to_dict(_synthetic_portfolio()) == expected


def _wuppertal_variant(mode, price, warning, e=259.0):
    legs = [
        Leg("first_mile", mode, "Haßlinghausen", "Wuppertal Hbf", _t("07:10"), _t("07:40"), None, 10),
        Leg("backbone", "rail", "Wuppertal Hbf", "Freiburg (Breisgau) Hbf", _t("07:51"), _t("11:30"), "ICE 9", None),
    ]
    score = Score(J=e, Q08_T_eff_min=e, E_T_eff_min=e, creativity=0.1, transfers=1,
                  min_transfer_slack_min=10, fragile_legs=0, backbone_km=400.0, reference_km=360.0)
    return ScoredCandidate(legs=legs, score=score, price_eur=price, taxi_warning=warning)


@pytest.mark.parametrize("taxi_first", [False, True])
def test_same_signature_collapse_prefers_non_taxi(taxi_first):
    # Same backbone, same time: the non-taxi feeder must survive regardless of
    # input order (handbook §4.3, byte-stable seam).
    bus = _wuppertal_variant("bus", 10.0, None)
    taxi = _wuppertal_variant("taxi", 30.0, "Taxi-Verfügbarkeit unsicher")
    cands = [taxi, bus, _creative()] if taxi_first else [bus, taxi, _creative()]
    wupp = next(s for s in cluster(cands) if s.legs[0].to == "Wuppertal Hbf")
    assert wupp.legs[0].mode == "bus"
    assert wupp.card.price_eur == 10.0
    assert wupp.card.risks == []


def test_same_signature_keeps_taxi_when_strictly_faster():
    bus = _wuppertal_variant("bus", 10.0, None, e=260.0)
    taxi = _wuppertal_variant("taxi", 30.0, "Taxi-Verfügbarkeit unsicher", e=255.0)
    for order in ([bus, taxi, _creative()], [taxi, bus, _creative()]):
        wupp = next(s for s in cluster(order) if s.legs[0].to == "Wuppertal Hbf")
        assert wupp.legs[0].mode == "taxi"
        assert wupp.card.risks == ["Taxi-Verfügbarkeit unsicher"]


def test_cluster_order_constants_consistent():
    from rro.models import CLUSTER_LABELS, CLUSTERS
    from rro.portfolio.cluster import CLUSTER_PRECEDENCE
    assert set(CLUSTER_PRECEDENCE) == set(CLUSTERS) == set(CLUSTER_LABELS)


def test_golden_card_invariants():
    # The serialised cards obey the Phase A rules end-to-end.
    doc = portfolio_to_dict(_synthetic_portfolio())
    for strat in doc["strategies"]:
        card = strat["card"]
        assert card["confidence"] == "scheduled"
        assert card["comfort"] == [] and card["risks"] == []
        assert len(card["transfer_stations"]) == card["transfers"] == strat["score"]["transfers"]
