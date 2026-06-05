"""OTP 2.x graph build (handbook §3.4, Coastline §1.2).

Builds the serialised OTP graph from pinned GTFS + OSM PBF — this graph *is*
``G_base`` for Phase A. The ``G_base → [C] → G″ → [B] → G′`` mutation chain
(Coastline §3.1) is the single load-bearing Phase B insertion point (§8.7); in
Phase A ``G′ ≡ G″ ≡ G_base``.
"""

from __future__ import annotations


def build_graph(staged_inputs: list, out_dir: str) -> str:
    """Invoke OTP 2.x in build mode; return the path to the serialised graph (§3.4)."""
    raise NotImplementedError("Phase A scaffold: OTP graph build pending")
