"""B4 clustered portfolio (handbook §7.1, Coastline §B4).

Builds **min 2, max 4** structurally distinct strategies — fastest, robust,
creative, low_transfer. The robust cluster uses the structural decision-robustness
proxy (the *Fastest* and *Sicherste* clusters collapse under the degenerate
distribution, §6.4).

Assignment honours each route's *strongest distinct claim* (§7.1): every cluster
nominates its best not-yet-assigned route by its cluster key; a route nominated
by several clusters goes to the **highest-precedence** nominator
(``fastest → robust → low_transfer → creative``); the losing clusters re-nominate
their next-best, repeating until each cluster has a distinct route or none
remains for it. A cluster with no distinct route left is dropped; the portfolio
never drops below 2. Fewer than 2 distinct routes → :class:`UnderfullPortfolioError`
(no valid portfolio; CLI exit 4) — *min 2* is a hard floor, not a target.
"""

from __future__ import annotations

from rro.models import CLUSTER_LABELS, ScoredCandidate, Strategy
from rro.portfolio.card import build_card
from rro.routing.deepening import route_signature
from rro.scoring.robustness import robustness_key

# Fixed, deterministic precedence for resolving a contested route (§7.1). The
# output strategies are emitted in this order.
CLUSTER_PRECEDENCE = ("fastest", "robust", "low_transfer", "creative")


class UnderfullPortfolioError(ValueError):
    """Fewer than 2 distinct routes → no valid portfolio (handbook §7.1, CLI exit 4)."""


def label_for(cluster_name: str) -> str:
    """The Coastline §7 German user-facing label for a cluster id (§7.1)."""
    return CLUSTER_LABELS[cluster_name]


def _sig_str(c: ScoredCandidate) -> str:
    return repr(route_signature(c.legs))


def _cluster_sort_key(name: str):
    """Sort key for a cluster — smaller is better, with a deterministic tiebreak.

    The cluster's primary key (§7.1) is paired with the backbone signature string
    so equal-primary candidates order reproducibly regardless of input order.
    """
    def key(c: ScoredCandidate):
        s = c.score
        if name == "fastest":
            primary = (s.E_T_eff_min,)
        elif name == "robust":
            primary = robustness_key(s.transfers, s.min_transfer_slack_min, s.fragile_legs)
        elif name == "creative":
            primary = (-s.creativity,)
        elif name == "low_transfer":
            primary = (s.transfers,)
        else:  # pragma: no cover - guarded by CLUSTER_PRECEDENCE
            raise KeyError(name)
        return (primary, _sig_str(c))

    return key


def _distinct(candidates: list) -> list:
    """Collapse candidates sharing a backbone signature, keeping the fastest (§5.3).

    Preserves first-occurrence order for determinism.
    """
    best = {}
    for c in candidates:
        sig = route_signature(c.legs)
        cur = best.get(sig)
        if cur is None or c.score.E_T_eff_min < cur.score.E_T_eff_min:
            best[sig] = c
    out, seen = [], set()
    for c in candidates:
        sig = route_signature(c.legs)
        if sig not in seen:
            seen.add(sig)
            out.append(best[sig])
    return out


def _best_unassigned(name: str, candidates: list, used: set):
    for c in sorted(candidates, key=_cluster_sort_key(name)):
        if id(c) not in used:
            return c
    return None


def _make_strategy(name: str, cand: ScoredCandidate) -> Strategy:
    label = CLUSTER_LABELS[name]
    card = build_card(label, cand.legs, price_eur=cand.price_eur, taxi_warning=cand.taxi_warning)
    return Strategy(cluster=name, label=label, score=cand.score, legs=cand.legs, card=card)


def cluster(scored_candidates, config=None) -> list:
    """Assign candidates to 2–4 distinct strategies (handbook §7.1, Coastline §B4).

    Returns a list of :class:`~rro.models.Strategy` in ``CLUSTER_PRECEDENCE``
    order. Raises :class:`UnderfullPortfolioError` if fewer than 2 distinct routes
    exist.
    """
    candidates = _distinct(list(scored_candidates))
    if len(candidates) < 2:
        raise UnderfullPortfolioError(
            f"need at least 2 distinct routes for a portfolio, got {len(candidates)}"
        )

    assigned: dict = {}
    used: set = set()
    pending = list(CLUSTER_PRECEDENCE)

    while pending:
        # Each pending cluster nominates its best unassigned route.
        nominations = {}
        for name in pending:  # pending stays in precedence order
            best = _best_unassigned(name, candidates, used)
            if best is not None:
                nominations[name] = best
        if not nominations:
            break

        # A contested route goes to its highest-precedence nominator.
        winners, claimed = {}, set()
        for name in nominations:  # precedence order
            cand = nominations[name]
            if id(cand) not in claimed:
                claimed.add(id(cand))
                winners[name] = cand

        for name, cand in winners.items():
            assigned[name] = cand
            used.add(id(cand))

        # Losers (and clusters that found no candidate) re-nominate next round.
        pending = [n for n in pending if n not in assigned and _best_unassigned(n, candidates, used)]

    return [_make_strategy(n, assigned[n]) for n in CLUSTER_PRECEDENCE if n in assigned]
