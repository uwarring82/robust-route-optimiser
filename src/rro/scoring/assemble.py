"""Assemble a scored candidate from a route's legs (handbook §6, Layer B).

Reduces a full-route leg list + its schedule time into a :class:`ScoredCandidate`
with the canonical :class:`Score` block — the bridge from routing to B4.
"""

from __future__ import annotations

from typing import Optional

from rro.models import Score, ScoredCandidate
from rro.routing.decompose import count_transfers, min_transfer_slack
from rro.scoring.creativity import backbone_km_of, creativity_from_km, reference_km_of
from rro.scoring.objective import j_objective, quantile_t_eff


def score_route(legs, total_minutes, reference_set, alpha_c, *,
                price_eur: Optional[float] = None,
                taxi_warning: Optional[str] = None) -> ScoredCandidate:
    """Score one full route into a :class:`ScoredCandidate` (handbook §6, §2.8).

    Deterministic mode: ``Q₀.₈ = E[T_eff] = T_schedule = total_minutes``.
    ``backbone_km`` / ``reference_km`` are rounded to one decimal and ``creativity``
    is derived from those rounded values, so the §2.8 invariant
    ``creativity == 1 − reference_km / backbone_km`` holds exactly. ``fragile_legs``
    is 0 here — same-line recovery headways are a forward refinement (§6.4).
    """
    q08 = round(quantile_t_eff(total_minutes), 1)
    backbone_km = round(backbone_km_of(legs), 1)
    reference_km = round(reference_km_of(legs, reference_set), 1)
    creativity = creativity_from_km(backbone_km, reference_km)
    score = Score(
        J=j_objective(q08, alpha_c, creativity),
        Q08_T_eff_min=q08,
        E_T_eff_min=q08,
        creativity=creativity,
        transfers=count_transfers(legs),
        min_transfer_slack_min=min_transfer_slack(legs),
        fragile_legs=0,
        backbone_km=backbone_km,
        reference_km=reference_km,
    )
    return ScoredCandidate(legs=legs, score=score, price_eur=price_eur, taxi_warning=taxi_warning)
