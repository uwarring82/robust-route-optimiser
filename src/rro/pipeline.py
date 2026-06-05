"""End-to-end Phase A pipeline (handbook §2.3, §2.4).

Wires the layers into a portfolio:

    hub discovery (B2) → static dominance (B2) → progressive deepening (B3)
        → two-pass C(r) calibration + scoring → B4 clustering → portfolio JSON.

It is parameterised by two injectable plan functions so it runs fully offline in
tests (and against a live OTP server in production, via :func:`otp_plan_fns`):

* ``hub_plan_fn(origin, departure, t_first_minutes) -> list[OTPItinerary]`` —
  first-mile itineraries origin→reachable hubs (OTP isochrone / one-to-many).
* ``backbone_plan_fn(hub_arrival, destination, params) -> list[OTPItinerary]`` —
  hub→destination backbone itineraries for a depth's params (OTP ``plan``).
"""

from __future__ import annotations

from rro import COASTLINE_VERSION, ENGINE_VERSION
from rro.graph.otp_client import OTPItinerary
from rro.portfolio.cluster import UnderfullPortfolioError, cluster
from rro.routing.deepening import deepen
from rro.routing.dominance import pareto_frontier
from rro.routing.hubs import hub_arrival, qualifies_as_first_mile
from rro.scoring.assemble import score_route
from rro.scoring.creativity import calibrate_reference


def _assemble(first_mile: OTPItinerary, backbone: OTPItinerary) -> OTPItinerary:
    """Concatenate a first-mile and a backbone itinerary into one full route."""
    return OTPItinerary(start=first_mile.start, end=backbone.end,
                        legs=[*first_mile.legs, *backbone.legs])


def _taxi_warning(legs):
    if any(l.layer == "first_mile" and (l.mode or "").lower() == "taxi" for l in legs):
        return "Taxi-Verfügbarkeit ist eine Heuristik (experimentell, §6)."
    return None


def plan_portfolio(config, departure, *, hub_plan_fn, backbone_plan_fn,
                   generated_at, tz=None):
    """Produce a :class:`~rro.models.Portfolio` for the corridor (handbook §2.3).

    Raises :class:`UnderfullPortfolioError` when no hub is reachable or fewer than
    two distinct routes survive (CLI exit 4).
    """
    from rro.models import Portfolio  # local import keeps the module import-light

    # B2 — hub discovery + static dominance (§4.2, §4.3).
    pairs = []  # (HubArrival, first_mile_itinerary)
    for it in hub_plan_fn(config.origin, departure, config.t_first_minutes):
        if qualifies_as_first_mile(it, config.t_first_minutes):
            pairs.append((hub_arrival(it, config.t_first_minutes), it))
    if not pairs:
        raise UnderfullPortfolioError("no feeder hubs reachable within T_first")
    survivors = {id(ha) for ha in pareto_frontier([ha for ha, _ in pairs])}
    surviving = [(ha, it) for ha, it in pairs if id(ha) in survivors]

    # B3 — progressive deepening, assembling full routes per surviving hub (§5).
    def plan_fn(params):
        routes = []
        for ha, first_mile in surviving:
            for backbone in backbone_plan_fn(ha, config.destination, params):
                routes.append(_assemble(first_mile, backbone))
        return routes

    candidates = deepen(plan_fn, depths=config.depths, epsilon=config.epsilon, tz=tz)
    if not candidates:
        raise UnderfullPortfolioError("no backbone routes found")

    # Two-pass C(r): freeze R from the enumeration, then score (§6.3).
    reference = calibrate_reference([c.legs for c in candidates])
    scored = [score_route(c.legs, c.total_minutes, reference, config.alpha_c,
                          taxi_warning=_taxi_warning(c.legs))
              for c in candidates]

    # B4 — clustering → Layer C (§7).
    strategies = cluster(scored)

    return Portfolio(
        query={
            "origin": config.origin,
            "destination": config.destination,
            "departure_time": departure,
            "generated_at": generated_at,
            "coastline_version": COASTLINE_VERSION,
            "engine_version": ENGINE_VERSION,
        },
        parameters={
            "alpha_c": config.alpha_c,
            "quantile": config.quantile,
            "t_first_minutes": config.t_first_minutes,
            "epsilon": config.epsilon.time_min,
            "mode": "deterministic",
        },
        reference_corridors=reference.corridors,
        strategies=strategies,
    )


def otp_plan_fns(client, *, base_budget=None):
    """Build OTP-backed (hub, backbone) plan functions from a live client.

    The backbone function calls the GTFS GraphQL ``plan`` query, passing the hub
    and destination as place strings (``OTPClient.plan`` accepts a stop id
    ``FeedId:StopId`` or ``"lat,lon"``). For live use, hub discovery must therefore
    populate ``HubArrival.hub_id`` with a resolvable stop id (not a display name),
    and ``config.destination`` likewise — a Phase-B/live-OTP precondition. Hub
    discovery itself needs OTP's isochrone / one-to-many API (``client.isochrone``),
    which is not yet implemented — the returned ``hub_plan_fn`` surfaces that clearly.
    """
    def hub_plan_fn(origin, departure, t_first_minutes):
        return client.isochrone(origin, t_first_minutes, modes=None)

    def backbone_plan_fn(hub_arrival, destination, params):
        return client.plan(
            hub_arrival.hub_id, destination, hub_arrival.arrival_time,
            num_itineraries=params["num_itineraries"],
            max_transfers=params["max_transfers"],
            search_window_s=params["search_window_s"],
        )

    return hub_plan_fn, backbone_plan_fn
