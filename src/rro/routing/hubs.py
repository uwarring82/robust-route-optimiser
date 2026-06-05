"""B2 first-mile hub discovery (handbook §4.2, Coastline §B2).

Turns first-mile OTP itineraries (origin → feeder hub) into :class:`HubArrival`
candidates for the static dominance filter (``routing/dominance.py``). Static
evaluation only in Phase A — no temporal decoupling, no live traffic (§4.2). The
exhaustive isochrone sweep (``enumerate_hubs``) uses OTP's one-to-many API and is
deferred; the parsing of reachable arrivals into :class:`HubArrival`s is here and
testable against recorded responses.
"""

from __future__ import annotations

from rro.models import HubArrival


def _minutes(itinerary) -> float:
    return (itinerary.end - itinerary.start).total_seconds() / 60


def hub_arrival(itinerary, t_first_minutes: int, *, cost_eur: float = 0.0) -> HubArrival:
    """Build a :class:`HubArrival` from a first-mile itinerary (origin → hub, §4.2).

    ``t_first_minutes`` is the first-mile window; an itinerary longer than it is
    **not** a first-mile segment (e.g. a full door-to-door route) and raises
    :class:`ValueError` rather than silently emitting the destination as a hub.

    The hub is the itinerary's final stop; ``transfers`` counts first-mile vehicle
    changes (transit legs − 1); ``first_mile_mode`` is the mode of the leg arriving
    at the hub. ``arrival_time`` is the itinerary's (offset-aware) arrival.
    """
    legs = itinerary.legs
    if not legs:
        raise ValueError("cannot derive a hub arrival from an empty itinerary")
    minutes = _minutes(itinerary)
    if minutes > t_first_minutes:
        raise ValueError(
            f"itinerary is not a first-mile segment: {minutes:.0f} min exceeds "
            f"T_first = {t_first_minutes} min (a full route, not origin→hub)")
    transit = [l for l in legs if (l.mode or "").upper() != "WALK"]
    last = legs[-1]
    return HubArrival(
        hub_id=last.to_stop_id or last.to_name,
        arrival_time=itinerary.end.isoformat(),
        cost_eur=cost_eur,
        transfers=max(len(transit) - 1, 0),
        first_mile_mode=(transit[-1].mode if transit else "WALK").lower(),
    )


def hub_arrivals(itineraries, t_first_minutes: int, *, costs: dict = None) -> list:
    """Hub arrivals for itineraries reachable within ``T_first`` (§4.2).

    ``costs`` optionally maps itinerary index → first-mile fare (EUR). Itineraries
    longer than ``T_first`` are skipped (not first-mile segments). The result is
    the over-generated set; the static dominance filter prunes it (§4.3).
    """
    costs = costs or {}
    out = []
    for i, it in enumerate(itineraries):
        if _minutes(it) <= t_first_minutes:
            out.append(hub_arrival(it, t_first_minutes, cost_eur=costs.get(i, 0.0)))
    return out


def enumerate_hubs(origin: str, t_first_minutes: int, client, *,
                   include_taxi: bool = False) -> list:
    """Exhaustively enumerate feeder hubs within ``T_first`` via OTP isochrone (§4.2).

    Phase A scaffold: this drives OTP's one-to-many / isochrone API
    (``otp_client.isochrone``, still a stub) and feeds :func:`hub_arrivals`.
    """
    raise NotImplementedError("Phase A scaffold: OTP isochrone-based hub enumeration pending")
