"""OTP GraphQL client wrapper (handbook §3.5, §5.2, Coastline §1.2).

A thin client over a locally served OpenTripPlanner 2.x **GTFS GraphQL** endpoint.
The routing layers depend only on this interface (issue a query → list of
itineraries), so the backend (OTP 2.x primary; r5py / pure RAPTOR as a documented
alternative, §3.6) is swappable.

Phase A queries **scheduled timetables only** — no realtime updater is configured,
consistent with ``T_eff = T_schedule``. Itinerary/leg times come back as epoch
milliseconds (OTP ``Long``) and are parsed into offset-aware UTC datetimes.

The HTTP transport is injectable: pass ``transport=callable(query, variables) ->
dict`` to run against recorded responses (tests) instead of a live server.

**Version pin.** Phase A targets **OTP 2.9.0**. We use the top-level GTFS GraphQL
``plan`` query, which is *deprecated since OTP 2.7.0* in favour of
``planConnection`` but **not removed** anywhere in the 2.x line (functional through
2.9.0, with a harmless deprecation warning). ``plan`` is the simplest single-shot
scheduled-itinerary query; ``planConnection`` would impose relay cursor pagination
and an ISO-8601 ``Duration`` search window for no Phase A benefit. Migration to
``planConnection`` — and to the non-deprecated ``OffsetDateTime`` leg-time fields,
replacing the deprecated epoch-ms ``startTime``/``endTime`` used here — is a
forward-hook, kept cheap by isolating the query behind this module.
(Verified against the OTP dev-2.x GTFS GraphQL schema + Changelog.)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional

# OTP release this client's query shape is pinned to (see module docstring).
OTP_PINNED_VERSION = "2.9.0"


class OTPError(RuntimeError):
    """Any OTP transport / GraphQL / response-shape failure (maps to CLI exit 3)."""


# Default first-mile + backbone modes for a plan query (handbook §5.2).
DEFAULT_MODES = [
    {"mode": "RAIL"}, {"mode": "BUS"}, {"mode": "TRAM"},
    {"mode": "SUBWAY"}, {"mode": "WALK"},
]

# GTFS GraphQL plan query (handbook §5.2). Scheduled search: arriveBy=false, no
# realtime updater. startTime/endTime are epoch milliseconds.
PLAN_QUERY = """
query Plan($from: InputCoordinates, $to: InputCoordinates, $fromPlace: String,
           $toPlace: String, $date: String!, $time: String!, $numItineraries: Int!,
           $searchWindow: Long, $maxTransfers: Int, $modes: [TransportMode]) {
  plan(from: $from, to: $to, fromPlace: $fromPlace, toPlace: $toPlace,
       date: $date, time: $time, arriveBy: false,
       numItineraries: $numItineraries, searchWindow: $searchWindow,
       maxTransfers: $maxTransfers, transportModes: $modes) {
    itineraries {
      startTime
      endTime
      legs {
        mode
        startTime
        endTime
        distance
        from { name stop { gtfsId } }
        to { name stop { gtfsId } }
        route { shortName }
        trip { gtfsId }
      }
    }
  }
}
""".strip()


@dataclass
class OTPLeg:
    """One leg of an OTP itinerary, in domain-neutral form (B1 layering is later)."""

    mode: str
    from_name: str
    to_name: str
    start: datetime  # offset-aware (UTC)
    end: datetime
    from_stop_id: Optional[str] = None
    to_stop_id: Optional[str] = None
    route_short_name: Optional[str] = None
    trip_id: Optional[str] = None
    distance: Optional[float] = None  # metres (OTP Leg.distance)


@dataclass
class OTPItinerary:
    """An OTP itinerary: start/end and its ordered legs."""

    start: datetime
    end: datetime
    legs: list  # list[OTPLeg]


# --- parsing ---------------------------------------------------------------

def _to_dt(ms) -> datetime:
    if ms is None:
        raise OTPError("missing time in OTP response")
    try:
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    except (TypeError, ValueError, OSError, OverflowError) as e:
        raise OTPError(f"invalid OTP time {ms!r}: {e}") from e


def _stop_id(place: dict) -> Optional[str]:
    stop = (place or {}).get("stop") or {}
    return stop.get("gtfsId")


def parse_leg(leg: dict) -> OTPLeg:
    if not isinstance(leg, dict):
        raise OTPError(f"OTP leg must be an object, got {type(leg).__name__}")
    mode = leg.get("mode")
    if not mode:
        raise OTPError("OTP leg missing 'mode'")
    frm = leg.get("from") or {}
    to = leg.get("to") or {}
    route = leg.get("route") or {}
    trip = leg.get("trip") or {}
    return OTPLeg(
        mode=mode,
        from_name=frm.get("name", ""),
        to_name=to.get("name", ""),
        start=_to_dt(leg.get("startTime")),
        end=_to_dt(leg.get("endTime")),
        from_stop_id=_stop_id(frm),
        to_stop_id=_stop_id(to),
        route_short_name=route.get("shortName"),
        trip_id=trip.get("gtfsId"),
        distance=leg.get("distance"),
    )


def parse_itinerary(it: dict) -> OTPItinerary:
    if not isinstance(it, dict):
        raise OTPError(f"OTP itinerary must be an object, got {type(it).__name__}")
    legs = it.get("legs", [])
    if not isinstance(legs, list):
        raise OTPError(f"itinerary 'legs' must be a list, got {type(legs).__name__}")
    return OTPItinerary(
        start=_to_dt(it.get("startTime")),
        end=_to_dt(it.get("endTime")),
        legs=[parse_leg(l) for l in legs],
    )


def _coords(place) -> dict:
    if isinstance(place, dict):
        return {"lat": place["lat"], "lon": place["lon"]}
    lat, lon = place  # (lat, lon) tuple
    return {"lat": lat, "lon": lon}


def _set_place(variables: dict, coord_key: str, place_key: str, value) -> None:
    """Route a place into either ``from``/``to`` (coordinates) or ``fromPlace``/
    ``toPlace`` (a string: an OTP stop id ``FeedId:StopId`` or ``"lat,lon"``).

    OTP requires exactly one of the pair, so the other is set to ``None``.
    """
    if isinstance(value, str):
        variables[coord_key] = None
        variables[place_key] = value
    else:
        variables[coord_key] = _coords(value)
        variables[place_key] = None


def _split_iso(depart) -> tuple:
    dt = depart if isinstance(depart, datetime) else datetime.fromisoformat(depart)
    return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S")


# --- transport + client ----------------------------------------------------

def _http_transport(endpoint: str, timeout: float) -> Callable:
    import urllib.error
    import urllib.request

    def transport(query: str, variables: dict) -> dict:
        payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
        req = urllib.request.Request(
            endpoint, data=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise OTPError(f"OTP request to {endpoint} failed: {e}") from e
        except json.JSONDecodeError as e:
            raise OTPError(f"OTP returned non-JSON: {e}") from e

    return transport


class OTPClient:
    """Typed wrapper over a locally served OTP 2.x GTFS GraphQL endpoint."""

    def __init__(self, endpoint: str, *, transport: Optional[Callable] = None,
                 timeout: float = 30.0):
        self.endpoint = endpoint
        self._transport = transport or _http_transport(endpoint, timeout)

    def _execute(self, query: str, variables: dict) -> dict:
        try:
            resp = self._transport(query, variables)
        except OTPError:
            raise
        except Exception as e:  # noqa: BLE001 - normalise any transport failure
            raise OTPError(f"OTP transport error: {e}") from e
        if not isinstance(resp, dict):
            raise OTPError("OTP response was not a JSON object")
        errors = resp.get("errors")
        if errors:
            if isinstance(errors, list):
                msgs = "; ".join(
                    str(e.get("message", e)) if isinstance(e, dict) else str(e)
                    for e in errors
                )
            else:
                msgs = str(errors)
            raise OTPError(f"OTP GraphQL errors: {msgs}")
        data = resp.get("data")
        if data is None:
            raise OTPError("OTP response contained no data")
        return data

    def plan(self, origin, destination, depart, *, num_itineraries: int,
             max_transfers: int, search_window_s: int,
             modes: Optional[list] = None) -> list:
        """Plan itineraries for one origin→destination pair at ``depart`` (§5.2).

        ``origin``/``destination`` are either coordinates — a ``(lat, lon)`` tuple
        or ``{"lat","lon"}`` dict (sent as ``from``/``to``) — or a place **string**:
        an OTP stop id ``"FeedId:StopId"`` or ``"lat,lon"`` (sent as
        ``fromPlace``/``toPlace``). ``depart`` is an ISO 8601 string or
        :class:`datetime`. Returns a list of :class:`OTPItinerary`. Raises
        :class:`OTPError` on any failure.
        """
        date, time = _split_iso(depart)
        variables = {
            "date": date,
            "time": time,
            "numItineraries": num_itineraries,
            "searchWindow": search_window_s,
            "maxTransfers": max_transfers,
            "modes": modes if modes is not None else DEFAULT_MODES,
        }
        _set_place(variables, "from", "fromPlace", origin)
        _set_place(variables, "to", "toPlace", destination)
        data = self._execute(PLAN_QUERY, variables)
        plan = data.get("plan")
        if plan is None:
            raise OTPError("OTP response contained no plan")
        # An empty `itineraries: []` is a valid "no routes" result; a missing or
        # null list is a response-shape failure, not "no routes".
        itineraries = plan.get("itineraries")
        if not isinstance(itineraries, list):
            raise OTPError("OTP response 'plan.itineraries' is missing or not a list")
        try:
            return [parse_itinerary(it) for it in itineraries]
        except OTPError:
            raise
        except (KeyError, TypeError, ValueError, AttributeError) as e:
            raise OTPError(f"malformed OTP response: {e}") from e

    def isochrone(self, origin, max_duration_min: int, modes: list) -> list:
        """One-to-many reachability sweep for first-mile hub discovery (§4.2).

        Uses OTP's isochrone / one-to-many endpoint (distinct from the GTFS
        GraphQL ``plan`` API) — not yet implemented in this scaffold.
        """
        raise NotImplementedError("Phase A scaffold: OTP isochrone query pending")
