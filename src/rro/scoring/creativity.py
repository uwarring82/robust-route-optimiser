"""B-creativity C(r) and the two-pass reference set R (handbook §6.3, Coastline §0.3).

``C(r) = 1 − (km on R / total backbone km)``, backbone-only. Two-pass: a
calibration pass at ``α_C = 0`` freezes the top-3 backbone corridors by km as R;
the scoring pass computes C(r) for each candidate.
"""

from __future__ import annotations

from rro.models import ReferenceCorridor, ReferenceSet


def creativity_from_km(backbone_km: float, reference_km: float) -> float:
    """``C(r) = 1 − reference_km / backbone_km``, in ``[0, 1]``, two-decimal (§6.3).

    By definition ``reference_km`` (km of *r* on R) is a subset of the total
    backbone km, so ``0 ≤ reference_km ≤ backbone_km``. Negative inputs or
    ``reference_km > backbone_km`` are programming errors and raise
    :class:`ValueError`; a tiny floating-point overshoot is tolerated and clamped.
    Returns ``0.0`` for a route with no backbone (relaxed two-layer route,
    Coastline §B1).
    """
    if backbone_km < 0 or reference_km < 0:
        raise ValueError("backbone_km and reference_km must be non-negative")
    if backbone_km == 0:
        return 0.0
    if reference_km > backbone_km + 1e-6:
        raise ValueError("reference_km cannot exceed backbone_km (km on R ⊆ total backbone km)")
    return round(1.0 - min(reference_km, backbone_km) / backbone_km, 2)


def calibrate_reference(candidates: list, top_n: int = 3, version: int = 1) -> ReferenceSet:
    """Pass 1 (α_C = 0): freeze the top-N backbone corridors by km as R (§6.3).

    Phase A scaffold: requires backbone-corridor enumeration from the candidate
    pool. R-blending on structural GTFS change (Coastline §0.3) is a forward-hook.
    """
    raise NotImplementedError("Phase A scaffold: reference-set calibration pending")


def backbone_km_on(route, corridors: list) -> float:
    """Backbone km of ``route`` overlapping any frozen R corridor (§6.3). Stub."""
    raise NotImplementedError("Phase A scaffold: R-overlap geometry pending")
