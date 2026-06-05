"""Unit tests for the pure scoring functions (handbook §6, §2.8 invariants)."""

from __future__ import annotations

from rro.scoring.creativity import creativity_from_km
from rro.scoring.objective import j_objective, quantile_t_eff
from rro.scoring.robustness import is_fragile_leg, robustness_key


def test_quantile_is_degenerate():
    # Phase A: every quantile equals T_schedule (handbook §6.1).
    assert quantile_t_eff(271.0, 0.8) == 271.0
    assert quantile_t_eff(271.0, 0.95) == 271.0


def test_j_objective_rounding_matches_handbook_example():
    # §7.2 creative strategy: 309.0 − 0.7·0.58 = 308.594 → 308.6.
    assert j_objective(309.0, 0.7, 0.58) == 308.6
    # creativity 0 → J equals Q0.8.
    assert j_objective(271.0, 0.7, 0.0) == 271.0


def test_creativity_from_km():
    # §7.2 creative: 1 − 230.1/547.9 = 0.5800… → 0.58.
    assert creativity_from_km(547.9, 230.1) == 0.58
    # Fully on reference corridors → 0.
    assert creativity_from_km(312.4, 312.4) == 0.0
    # No backbone (relaxed two-layer) → 0.
    assert creativity_from_km(0.0, 0.0) == 0.0


def test_robustness_key_orders_by_structure():
    # Fewer transfers wins first.
    a = robustness_key(1, 18, 0)
    b = robustness_key(2, 30, 0)
    assert a < b
    # Equal transfers: larger min slack wins (negated → smaller tuple).
    assert robustness_key(1, 18, 0) < robustness_key(1, 11, 0)
    # Equal transfers and slack: fewer fragile legs wins.
    assert robustness_key(1, 11, 0) < robustness_key(1, 11, 1)


def test_robustness_key_handles_none_slack():
    assert robustness_key(1, None, 0) == (1, 0.0, 0)


def test_is_fragile_leg_threshold():
    assert is_fragile_leg(45, 30) is True
    assert is_fragile_leg(20, 30) is False
    assert is_fragile_leg(30, 30) is False  # strictly exceeds
