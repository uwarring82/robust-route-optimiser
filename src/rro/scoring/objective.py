"""B-objective J(r) and the deterministic Q₀.₈ (handbook §6.2, Coastline §0.2).

Deterministic mode: ``T_eff = T_schedule``, so every quantile of the (degenerate)
distribution equals the scheduled time — ``Q₀.₈ = Q₀.₉₅ = E[T_eff] = T_schedule``.
``J(r) = Q₀.₈ − α_C · C(r)``, emitted rounded to one decimal (§2.8).
"""

from __future__ import annotations


def quantile_t_eff(t_schedule_min: float, q: float = 0.8) -> float:
    """Degenerate distribution: every quantile equals ``T_schedule`` (§6.1).

    The ``q`` argument is accepted for interface stability across phases but has
    no effect in Phase A.
    """
    return t_schedule_min


def j_objective(q08_min: float, alpha_c: float, creativity: float) -> float:
    """``J(r) = Q₀.₈ − α_C · C(r)``, rounded to one decimal (handbook §2.8, §6.2)."""
    return round(q08_min - alpha_c * creativity, 1)
