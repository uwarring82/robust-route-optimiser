"""B-creativity C(r) and the two-pass reference set R (handbook §6.3, Coastline §0.3).

``C(r) = 1 − (km on R / total backbone km)``, backbone-only. Two-pass: a
calibration pass (α_C = 0, i.e. the deepening enumeration) freezes the top-3
backbone corridors by km as R; the scoring pass computes C(r) for each candidate
as the fraction of its backbone km lying on an R corridor (leg-level overlap).
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


def backbone_km_of(legs: list) -> float:
    """Total backbone km of a route (sum of backbone leg distances, §B1)."""
    return sum((l.distance_m or 0.0) for l in legs if l.layer == "backbone") / 1000.0


def backbone_leg_keys(legs: list) -> set:
    """The ``(line, from, to)`` keys of a route's backbone legs."""
    return {(l.line, l.from_, l.to) for l in legs if l.layer == "backbone"}


def reference_km_of(legs: list, reference_set: ReferenceSet) -> float:
    """Backbone km of a route lying on any R corridor (leg-level overlap, §6.3)."""
    keys = reference_set.leg_keys
    return sum((l.distance_m or 0.0) for l in legs
               if l.layer == "backbone" and (l.line, l.from_, l.to) in keys) / 1000.0


def _backbone_signature(legs: list) -> tuple:
    return tuple((l.line, l.from_, l.to) for l in legs if l.layer == "backbone")


def _slug(s: str) -> str:
    out = []
    for ch in (s or "").lower():
        if ch.isalnum():
            out.append(ch)
        elif out and out[-1] != "-":
            out.append("-")
    return "".join(out).strip("-")


def _corridor_id(signature: tuple) -> str:
    stops = []
    for (_line, frm, to) in signature:
        if not stops:
            stops.append(frm)
        stops.append(to)
    return "-".join(_slug(s) for s in stops) or "corridor"


def calibrate_reference(candidate_legs, top_n: int = 3, version: int = 1) -> ReferenceSet:
    """Pass 1 (α_C = 0): freeze the top-N backbone corridors by km as R (§6.3).

    ``candidate_legs`` is an iterable of full-route leg lists. Corridors are keyed
    by backbone signature (deduplicated, keeping the largest km); ties broken by
    ``corridor_id`` for determinism.
    """
    by_sig = {}
    for legs in candidate_legs:
        sig = _backbone_signature(legs)
        if not sig:
            continue
        km = backbone_km_of(legs)
        if sig not in by_sig or km > by_sig[sig][0]:
            by_sig[sig] = (km, legs)
    ranked = sorted(by_sig.items(), key=lambda kv: (-kv[1][0], _corridor_id(kv[0])))[:top_n]
    corridors = [ReferenceCorridor(corridor_id=_corridor_id(sig), backbone_km=round(km, 1))
                 for sig, (km, _legs) in ranked]
    leg_keys = set()
    for sig, (_km, legs) in ranked:
        leg_keys |= backbone_leg_keys(legs)
    return ReferenceSet(corridors=corridors, version=version, leg_keys=leg_keys)


def creativity_of_route(legs: list, reference_set: ReferenceSet) -> float:
    """C(r) for a route against the frozen R (§6.3) — used for ε-termination."""
    total = backbone_km_of(legs)
    if total <= 0:
        return 0.0
    return creativity_from_km(total, reference_km_of(legs, reference_set))
