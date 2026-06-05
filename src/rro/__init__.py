"""Robust Route Optimiser (RRO) — Phase A static engine.

Implements the Phase A handbook (``docs/handbook/phase-a-engine.md``), which is
subordinate to Coastline v0.6.0-rc1 (``docs/coastline/rro-coastline-v0.6.0-rc1.md``).

Phase A runs in deterministic mode (``T_eff = T_schedule``) on the static base
graph ``G_base`` only — no real-time, no state-dependent ``G′`` mutation, no
Monte Carlo. See the module map in handbook §2.5.
"""

ENGINE_VERSION = "0.1.0-a"
COASTLINE_VERSION = "0.6.0-rc1"

__all__ = ["ENGINE_VERSION", "COASTLINE_VERSION"]
