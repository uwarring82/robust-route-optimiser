"""B2 first-mile hub enumeration (handbook §4.2, Coastline §B2).

Enumerates **all** stops reachable within ``T_first`` (default 45 min) of the
origin across walk/bus/taxi — an exhaustive reachability sweep, not nearest-k.
Static evaluation only in Phase A (no temporal decoupling, no live traffic). The
taxi first-mile is an experimental, replaceable module (handbook §6).
"""

from __future__ import annotations

from rro.models import HubArrival


def enumerate_hubs(origin: str, t_first_minutes: int, client, *,
                   include_taxi: bool = False) -> list:
    """Return candidate :class:`HubArrival`s within the ``T_first`` window (§4.2)."""
    raise NotImplementedError("Phase A scaffold: hub enumeration pending OTP isochrones")
