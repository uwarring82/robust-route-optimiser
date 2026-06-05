"""B3 progressive deepening controller (handbook §5, Coastline §B3).

Depth 0 (direct + 1-transfer) → Depth 1 (2-transfer) → Depth 2 (creative ×2.5),
with ε-termination. Routing is schedule-based (no GTFS-RT) on ``G_base``.
"""

from __future__ import annotations

# Depth ladder knobs (handbook §5.1). ``creative_factor`` and ε live in config.
CREATIVE_FACTOR = 2.5
DEPTH_PARAMS = {
    0: {"max_transfers": 1, "budget_mult": 1.0, "window_mult": 1.0},
    1: {"max_transfers": 2, "budget_mult": 1.0, "window_mult": 1.0},
    2: {"max_transfers": 2, "budget_mult": CREATIVE_FACTOR, "window_mult": CREATIVE_FACTOR},
}


def route_signature(legs) -> tuple:
    """Structural identity of the BACKBONE layer (handbook §5.3).

    Ordered ``(line, board_stop, alight_stop)`` over backbone transit legs. The
    first backbone ``board_stop`` IS the feeder hub, so feeder-hub choice is part
    of the signature; the first-mile leg (its mode/path) and the exact
    minute-level departure are abstracted away. Hence different feeder hubs →
    different signatures → distinct candidates; same hub + different first-mile
    mode → shared signature → merged (§4.3, §5.3).
    """
    return tuple(
        (leg.line, leg.from_, leg.to)
        for leg in legs
        if leg.layer == "backbone"
    )


def improves_any(new_routes, pool, criteria, eps) -> bool:
    """ε-termination test: does any route in ``new_routes`` better an active
    portfolio criterion beyond its ε threshold (handbook §5.4)? Stub."""
    raise NotImplementedError("Phase A scaffold: ε-termination test pending scored pool")


def deepen(hubs, client, config):
    """Run Depth 0/1/2 deepening into a deduplicated candidate pool (§5). Stub."""
    raise NotImplementedError("Phase A scaffold: deepening controller pending OTP client")
