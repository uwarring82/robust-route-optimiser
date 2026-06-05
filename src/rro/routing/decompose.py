"""B1 three-layer decomposition (handbook §4.1, Coastline §B1).

Splits a door-to-door itinerary into ``first_mile`` / ``backbone`` / ``last_mile``
legs. Relaxes to two layers when the dominant candidate enters the backbone
directly (no distinct feeder hub). The last mile is a single appended OTP query,
excluded from the backbone search budget and from the transfer count (§4.1).
"""

from __future__ import annotations


def decompose(itinerary, origin: str, destination: str) -> list:
    """Return the itinerary's legs tagged with their B1 layer (§4.1)."""
    raise NotImplementedError("Phase A scaffold: B1 decomposition pending OTP itineraries")
