"""Core data types for the RRO Phase A engine.

Field names mirror the canonical JSON portfolio schema (handbook §2.8); these are
the in-memory representations. Serialisation lives in :mod:`rro.portfolio.output`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# B1 three-layer decomposition (handbook §4.1).
LAYERS = ("first_mile", "backbone", "last_mile")

# B4 cluster ids in Coastline §B4 *catalogue* order. The tie-break / output
# ordering is rro.portfolio.cluster.CLUSTER_PRECEDENCE (a permutation of these).
CLUSTERS = ("fastest", "robust", "creative", "low_transfer")
CLUSTER_LABELS = {
    "fastest": "Schnellste",
    "robust": "Sicherste",
    "creative": "Überraschung",
    "low_transfer": "Entspannt",
}


@dataclass
class Leg:
    """One itinerary leg. ``from_`` serialises to ``"from"`` (a Python keyword).

    ``dep`` / ``arr`` are ISO 8601 datetimes with offset in emitted JSON
    (handbook §2.8); ``transfer_slack_min`` is the raw buffer to the next leg, or
    ``None`` for the terminal leg (§4.1).
    """

    layer: str  # one of LAYERS
    mode: str
    from_: str
    to: str
    dep: str
    arr: str
    line: Optional[str] = None
    transfer_slack_min: Optional[float] = None
    distance_m: Optional[float] = None  # internal (backbone km / C(r)); not serialised


@dataclass
class Score:
    """Per-strategy score block (handbook §2.8). In Phase A
    ``Q08_T_eff_min == E_T_eff_min == T_schedule`` (degenerate distribution)."""

    J: float
    Q08_T_eff_min: float
    E_T_eff_min: float
    creativity: float
    transfers: int
    min_transfer_slack_min: Optional[float]
    fragile_legs: int
    backbone_km: float
    reference_km: float


@dataclass
class Card:
    """Coastline §7 user-facing summary card (handbook §7.3).

    In Phase A ``confidence`` is the literal ``"scheduled"`` (degenerate
    distribution), ``comfort`` is empty, and ``risks`` is empty except for an
    experimental-taxi low-confidence warning (§4.2).
    """

    strategy_label: str
    expected_arrival: str
    confidence: str = "scheduled"
    transfers: int = 0
    transfer_stations: list = field(default_factory=list)
    price_eur: Optional[float] = None
    comfort: list = field(default_factory=list)
    risks: list = field(default_factory=list)


@dataclass
class Strategy:
    """A clustered portfolio strategy (handbook §7.1)."""

    cluster: str
    label: str
    score: Score
    legs: list  # list[Leg]
    card: Card


@dataclass
class ScoredCandidate:
    """A routed itinerary after scoring, before B4 clustering (handbook §6 → §7).

    Carries the leg structure and the full :class:`Score`; ``price_eur`` and
    ``taxi_warning`` feed the §7 card. B4 selects cluster representatives from a
    list of these.
    """

    legs: list  # list[Leg]
    score: Score
    price_eur: Optional[float] = None
    taxi_warning: Optional[str] = None


@dataclass
class ReferenceCorridor:
    """One frozen reference corridor in the set R (handbook §6.3, Coastline §0.3)."""

    corridor_id: str
    backbone_km: float


@dataclass
class ReferenceSet:
    """The two-pass creativity reference set R, versioned (handbook §6.3).

    ``leg_keys`` is the union of ``(line, from, to)`` backbone legs across the R
    corridors — used to measure a route's km on R for C(r).
    """

    corridors: list  # list[ReferenceCorridor]
    version: int = 1
    leg_keys: set = field(default_factory=set)


@dataclass
class HubArrival:
    """A first-mile hub-arrival candidate (handbook §4.2).

    Dominance (§4.3) is over ``(arrival_time, cost_eur, transfers)`` only;
    ``first_mile_mode`` is carried but is NOT a dominance dimension.
    """

    hub_id: str
    arrival_time: str  # ISO 8601 datetime with offset (handbook §2.8) — absolute, comparable
    cost_eur: float
    transfers: int
    first_mile_mode: str


@dataclass
class Portfolio:
    """The full canonical portfolio (handbook §2.8)."""

    query: dict
    parameters: dict
    reference_corridors: list  # list[ReferenceCorridor]
    strategies: list  # list[Strategy]
