"""OTP GraphQL client wrapper (handbook §3.5, Coastline §1.2).

The routing layers depend only on this interface (issue query → list of
itineraries), so the backend (OTP 2.x primary; r5py / pure RAPTOR as a documented
alternative, §3.6) is swappable. Phase A queries scheduled timetables only — no
realtime updater is configured (``T_eff = T_schedule``).
"""

from __future__ import annotations


class OTPClient:
    """Typed wrapper over a locally served OTP 2.x GTFS GraphQL endpoint."""

    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    def plan(self, origin, destination, depart, *, num_itineraries: int,
             max_transfers: int, search_window_s: int) -> list:
        """Plan itineraries for one origin→destination pair at ``depart`` (§5.2)."""
        raise NotImplementedError("Phase A scaffold: OTP GraphQL plan() pending")

    def isochrone(self, origin, max_duration_min: int, modes: list) -> list:
        """One-to-many reachability sweep for first-mile hub discovery (§4.2)."""
        raise NotImplementedError("Phase A scaffold: OTP isochrone query pending")
