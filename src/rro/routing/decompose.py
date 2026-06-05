"""B1 three-layer decomposition (handbook §4.1, Coastline §B1).

Translates an OTP itinerary (:class:`rro.graph.otp_client.OTPItinerary`) into the
domain model: each leg tagged with its B1 layer (``first_mile`` / ``backbone`` /
``last_mile``) and emitted as a :class:`rro.models.Leg`.

The default ``role="door_to_door"`` decomposition treats the itinerary as a full
origin→destination route: the **backbone** is the long-distance/regional rail
span (first ``RAIL`` leg to last ``RAIL`` leg), anything before it (access walk,
feeder bus/taxi) is ``first_mile``, anything after (egress tram/bus/walk) is
``last_mile``; ending at the rail hub yields no ``last_mile`` leg (the B1
two-layer relaxation, §4.1), and a route with no rail leg falls back to bounding
the backbone by its transit legs.

This rail-span heuristic is only valid for a **complete** route. A first-mile or
last-mile *segment* (e.g. ``BUS origin→stop, WALK stop→hub``) has no rail and
would be mislabelled, so callers decomposing a segment must pass the explicit
``role`` (``"first_mile"`` / ``"backbone"`` / ``"last_mile"``), which tags every
leg with that single layer.
"""

from __future__ import annotations

from rro.models import Leg

_ROLE_LAYERS = ("first_mile", "backbone", "last_mile")


def _assign_layers(modes: list) -> list:
    """Tag each leg of a **door-to-door** route from its ordered mode sequence (§4.1)."""
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


def decompose(itinerary, *, role="door_to_door", tz=None) -> list:
    """Return the itinerary's legs as layered :class:`Leg`s (handbook §4.1).

    ``role`` is ``"door_to_door"`` (default; the rail-span heuristic) or one of
    ``"first_mile"`` / ``"backbone"`` / ``"last_mile"`` to tag every leg with a
    single layer when decomposing a segment rather than a complete route.
    ``tz`` (a ``tzinfo``) localises the offset-aware OTP times; if omitted they
    are emitted in their original zone (UTC, as parsed from OTP epoch-ms).
    Per-leg ``transfer_slack_min`` is the precise buffer in minutes to the next
    leg's departure (sub-minute preserved), or ``None`` for the terminal leg.
    """
    legs = itinerary.legs
    if role in _ROLE_LAYERS:
        layers = [role] * len(legs)
    elif role == "door_to_door":
        layers = _assign_layers([l.mode for l in legs])
    else:
        raise ValueError(
            f"unknown decompose role {role!r}; expected 'door_to_door' or one of {_ROLE_LAYERS}")
    out = []
    for i, ol in enumerate(legs):
        nxt = legs[i + 1] if i + 1 < len(legs) else None
        slack = None if nxt is None else round((nxt.start - ol.end).total_seconds() / 60, 2)
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


# Layers whose line-changes count as transfers (the appended last mile does not, §4.1).
_COUNTED_LAYERS = ("first_mile", "backbone")


def transfer_stations(legs: list) -> list:
    """Transfer stations over first-mile + backbone boundaries only (handbook §4.1).

    The last-mile boarding is excluded — the station is the arrival point of each
    counted leg that is followed by another counted leg.
    """
    counted = [l for l in legs if l.layer in _COUNTED_LAYERS]
    return [counted[i].to for i in range(len(counted) - 1)]


def count_transfers(legs: list) -> int:
    """Number of counted transfers (first-mile + backbone line changes, §4.1)."""
    return len(transfer_stations(legs))


def min_transfer_slack(legs: list):
    """Smallest connection buffer over counted transfers (§4.1), or ``None``.

    A counted transfer is a boundary between two counted (non-last-mile) legs; its
    buffer is the earlier leg's ``transfer_slack_min``. The buffer *into* an
    appended last-mile leg is excluded.
    """
    buffers = [legs[i].transfer_slack_min for i in range(len(legs) - 1)
               if legs[i].layer in _COUNTED_LAYERS and legs[i + 1].layer in _COUNTED_LAYERS
               and legs[i].transfer_slack_min is not None]
    return min(buffers) if buffers else None
