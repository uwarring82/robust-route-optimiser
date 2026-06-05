"""JSON portfolio serialisation (handbook §2.8, §7.2).

Renders the canonical schema with exact, phase-stable field names. ``Leg.from_``
serialises to ``"from"``. Emitted ``legs[].dep``/``arr`` are ISO 8601; the
abbreviated ``HH:MM`` examples in the handbook are display-only.
"""

from __future__ import annotations

import json
from dataclasses import asdict

from rro.models import Leg, Portfolio, Strategy


def leg_to_dict(leg: Leg) -> dict:
    """Serialise a leg, mapping ``from_`` → ``"from"`` (handbook §2.8)."""
    return {
        "layer": leg.layer,
        "mode": leg.mode,
        "from": leg.from_,
        "to": leg.to,
        "dep": leg.dep,
        "arr": leg.arr,
        "line": leg.line,
        "transfer_slack_min": leg.transfer_slack_min,
    }


def strategy_to_dict(s: Strategy) -> dict:
    return {
        "cluster": s.cluster,
        "label": s.label,
        "score": asdict(s.score),
        "legs": [leg_to_dict(l) for l in s.legs],
        "card": asdict(s.card),
    }


def portfolio_to_dict(p: Portfolio) -> dict:
    return {
        "query": p.query,
        "parameters": p.parameters,
        "reference_corridors": [asdict(c) for c in p.reference_corridors],
        "strategies": [strategy_to_dict(s) for s in p.strategies],
    }


def to_json(p: Portfolio, indent: int = 2) -> str:
    """Serialise a portfolio to canonical JSON (handbook §2.8)."""
    return json.dumps(portfolio_to_dict(p), ensure_ascii=False, indent=indent)
