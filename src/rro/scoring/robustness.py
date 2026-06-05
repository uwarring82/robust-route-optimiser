"""Structural decision-robustness proxy (handbook §6.4, Coastline §0.1).

Phase-A stand-in for ``Q₀.₉₅(T_eff)``: with the degenerate distribution the
*Fastest* and *Sicherste* clusters collapse, so the robust cluster is ordered by a
lexicographic structural key — (1) fewest transfers, (2) largest minimum transfer
slack, (3) fewest structurally fragile legs. Replaced by the Monte-Carlo quantile
in Phase B.
"""

from __future__ import annotations


def robustness_key(transfers: int, min_transfer_slack_min, fragile_legs: int) -> tuple:
    """Lexicographic robustness key; the **smaller** tuple is more robust (§6.4).

    Slack is negated so that larger slack sorts earlier (more robust).
    """
    return (transfers, -(min_transfer_slack_min or 0.0), fragile_legs)


def is_fragile_leg(recovery_headway_min: float, fragile_headway_min: float = 30.0) -> bool:
    """``True`` if a leg's only same-line recovery headway exceeds the threshold (§6.4).

    The threshold (``fragile_headway_min``, default 30 min) is a calibration
    variable, adjustable in the handbook without coastline amendment (Coastline §6).
    """
    return recovery_headway_min > fragile_headway_min


def count_fragile_legs(route, fragile_headway_min: float = 30.0) -> int:
    """Count structurally fragile legs of a route (§6.4). Stub — needs same-line headways."""
    raise NotImplementedError("Phase A scaffold: fragile-leg counting pending headway data")
