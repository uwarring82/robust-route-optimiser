"""Unit tests for B2 dominance and the B3 route signature (handbook §4.3, §5.3)."""

from __future__ import annotations

from rro.models import HubArrival, Leg
from rro.routing.dominance import dominates, is_dominated, pareto_frontier
from rro.routing.deepening import route_signature


_DAY = "2026-06-08T"
_TZ = "+02:00"


def _hub(hub_id, hhmm, cost, transfers, mode="bus", tz=_TZ):
    return HubArrival(hub_id, f"{_DAY}{hhmm}:00{tz}", cost, transfers, mode)


def test_strict_dominance():
    b = _hub("Wuppertal", "08:30", 5.0, 0)
    a = _hub("Hagen", "08:45", 6.0, 1)
    assert dominates(b, a) is True
    assert dominates(a, b) is False


def test_equal_arrivals_differ_only_in_mode_are_mutually_nondominating():
    bus = _hub("Wuppertal", "08:30", 5.0, 0, mode="bus")
    taxi = _hub("Wuppertal", "08:30", 5.0, 0, mode="taxi")
    # No strict improvement either way → neither dominates (handbook §4.3).
    assert dominates(bus, taxi) is False
    assert dominates(taxi, bus) is False
    front = pareto_frontier([bus, taxi])
    assert bus in front and taxi in front


def test_pareto_frontier_prunes_dominated():
    best = _hub("Wuppertal", "08:30", 5.0, 0)
    worse = _hub("Hagen", "08:55", 9.0, 2)
    other = _hub("Schwelm", "08:20", 7.0, 1)  # earlier but pricier — non-dominated
    front = pareto_frontier([best, worse, other])
    assert best in front
    assert other in front
    assert worse not in front
    assert is_dominated(worse, [best, worse, other]) is True


def test_dominance_uses_absolute_time_not_string_compare():
    # a arrives 06:00 UTC; b arrives 06:30 UTC — a is earlier in absolute terms,
    # but lexicographically "...08:00...+02:00" > "...07:30...+01:00", so a naive
    # string compare would wrongly conclude a is later. a should dominate b.
    a = HubArrival("Wuppertal", f"{_DAY}08:00:00+02:00", 5.0, 0, "bus")  # 06:00 UTC
    b = HubArrival("Hagen", f"{_DAY}07:30:00+01:00", 6.0, 1, "bus")      # 06:30 UTC
    assert a.arrival_time > b.arrival_time          # lexicographic (the trap)
    assert dominates(a, b) is True                  # absolute time (correct)
    assert dominates(b, a) is False


def test_dominance_across_midnight():
    # 23:50 on day 1 is earlier than 00:10 on day 2 in absolute terms.
    earlier = HubArrival("A", "2026-06-08T23:50:00+02:00", 5.0, 0, "bus")
    later = HubArrival("B", "2026-06-09T00:10:00+02:00", 6.0, 1, "bus")
    assert dominates(earlier, later) is True
    assert dominates(later, earlier) is False


def _leg(layer, frm, to, line, mode="rail"):
    return Leg(layer=layer, mode=mode, from_=frm, to=to, dep="x", arr="y", line=line)


def test_route_signature_is_backbone_only():
    legs = [
        _leg("first_mile", "Haßlinghausen", "Hagen Hbf", "VER 591", mode="bus"),
        _leg("backbone", "Hagen Hbf", "Köln Hbf", "ICE 945"),
        _leg("backbone", "Köln Hbf", "Freiburg (Breisgau) Hbf", "ICE 105"),
        _leg("last_mile", "Freiburg (Breisgau) Hbf", "Freiburg Innenstadt", "1", mode="tram"),
    ]
    sig = route_signature(legs)
    assert sig == (
        ("ICE 945", "Hagen Hbf", "Köln Hbf"),
        ("ICE 105", "Köln Hbf", "Freiburg (Breisgau) Hbf"),
    )


def test_different_feeder_hubs_have_different_signatures():
    # Feeder hub = first backbone board_stop → part of the signature (§5.3).
    via_hagen = [_leg("backbone", "Hagen Hbf", "Freiburg (Breisgau) Hbf", "ICE 105")]
    via_wupp = [_leg("backbone", "Wuppertal Hbf", "Freiburg (Breisgau) Hbf", "ICE 105")]
    assert route_signature(via_hagen) != route_signature(via_wupp)
