"""B1 three-layer decomposition (handbook §4.1, Coastline §B1).

Translates an OTP itinerary (:class:`rro.graph.otp_client.OTPItinerary`) into the
domain model: each leg tagged with its B1 layer (``first_mile`` / ``backbone`` /
``last_mile``) and emitted as a :class:`rro.models.Leg`.

The **backbone** is the long-distance/regional rail span: the run from the first
``RAIL`` leg to the last ``RAIL`` leg. Anything before it (access walk, feeder
bus/taxi) is ``first_mile``; anything after (egress tram/bus/walk to the
destination) is ``last_mile``. When the route ends at the rail destination hub
there is simply no ``last_mile`` leg (the B1 two-layer relaxation, §4.1). A route
with no rail leg falls back to bounding the backbone by its transit legs.
"""

from __future__ import annotations

from rro.models import Leg


def _assign_layers(modes: list) -> list:
    """Tag each leg with its B1 layer from the ordered mode sequence (§4.1)."""
    up = [(m or "").upper() for m in modes]
    n = len(up)
    rail = [i for i, m in enumerate(up) if m == "RAIL"]
    span = rail or [i for i, m in enumerate(up) if m != "WALK"]
    if not span:
        return ["first_mile"] * n  # all-walk degenerate route
    first, last = span[0], span[-1]
    return ["first_mile" if i < first else "last_mile" if i > last else "backbone"
            for i in range(n)]


def _iso(dt, tz):
    return (dt.astimezone(tz) if tz is not None else dt).isoformat()


def decompose(itinerary, *, tz=None) -> list:
    """Return the itinerary's legs as layered :class:`Leg`s (handbook §4.1).

    ``tz`` (a ``tzinfo``) localises the offset-aware OTP times; if omitted they
    are emitted in their original zone (UTC, as parsed from OTP epoch-ms).
    Per-leg ``transfer_slack_min`` is the raw buffer to the next leg's departure,
    or ``None`` for the terminal leg.
    """
    legs = itinerary.legs
    layers = _assign_layers([l.mode for l in legs])
    out = []
    for i, ol in enumerate(legs):
        nxt = legs[i + 1] if i + 1 < len(legs) else None
        slack = None if nxt is None else round((nxt.start - ol.end).total_seconds() / 60)
        out.append(Leg(
            layer=layers[i],
            mode=(ol.mode or "").lower(),
            from_=ol.from_name,
            to=ol.to_name,
            dep=_iso(ol.start, tz),
            arr=_iso(ol.end, tz),
            line=ol.route_short_name,
            transfer_slack_min=slack,
        ))
    return out


def feeder_hub(legs: list):
    """The feeder hub: the first backbone leg's board stop (§4.1, §5.3).

    ``None`` for a relaxed route with no backbone leg.
    """
    for leg in legs:
        if leg.layer == "backbone":
            return leg.from_
    return None
