"""B4 clustered portfolio (handbook §7.1, Coastline §B4).

Builds **min 2, max 4** structurally distinct strategies — fastest, robust,
creative, low_transfer. The robust cluster uses the structural decision-robustness
proxy (the *Fastest* and *Sicherste* clusters collapse under the degenerate
distribution, §6.4). If fewer than 2 distinct routes exist the portfolio is
underfull and no valid portfolio can be emitted (CLI exit 4) — *min 2* is a hard
floor, not a target.
"""

from __future__ import annotations

from rro.models import CLUSTER_LABELS

# Fixed, deterministic tie-break precedence for assigning a route to a cluster (§7.1).
CLUSTER_PRECEDENCE = ("fastest", "robust", "low_transfer", "creative")


class UnderfullPortfolioError(ValueError):
    """Fewer than 2 distinct routes → no valid portfolio (handbook §7.1, CLI exit 4)."""


def label_for(cluster: str) -> str:
    """The Coastline §7 German user-facing label for a cluster id (§7.1)."""
    return CLUSTER_LABELS[cluster]


def cluster(scored_candidates: list, config) -> list:
    """Assign candidates to 2–4 distinct strategies (handbook §7.1). Stub.

    Raises :class:`UnderfullPortfolioError` when fewer than 2 distinct routes
    exist.
    """
    raise NotImplementedError("Phase A scaffold: B4 clustering pending scored candidates")
