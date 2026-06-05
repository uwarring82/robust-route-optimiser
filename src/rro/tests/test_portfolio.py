"""Unit tests for card building and JSON serialisation (handbook §7.2, §7.3, §4.1)."""

from __future__ import annotations

import json

from rro.models import Card, Leg, Portfolio, ReferenceCorridor, Score, Strategy
from rro.portfolio.card import build_card, hhmm, transfer_stations
from rro.portfolio.output import to_json


def _legs_to_innenstadt():
    return [
        Leg("first_mile", "bus", "Haßlinghausen", "Hagen Hbf", "07:15", "07:52", "VER 591", 11),
        Leg("backbone", "rail", "Hagen Hbf", "Köln Hbf", "08:03", "09:01", "ICE 945", 9),
        Leg("backbone", "rail", "Köln Hbf", "Freiburg (Breisgau) Hbf", "09:10", "11:52", "ICE 105", 6),
        Leg("last_mile", "tram", "Freiburg (Breisgau) Hbf", "Freiburg Innenstadt",
            "2026-06-08T11:58:00+02:00", "2026-06-08T12:04:00+02:00", "1", None),
    ]


def test_hhmm_handles_iso_and_plain():
    assert hhmm("2026-06-08T12:04:00+02:00") == "12:04"
    assert hhmm("12:31") == "12:31"


def test_transfer_stations_exclude_last_mile_boarding():
    # Counted boundaries are first-mile + backbone only (handbook §4.1).
    stations = transfer_stations(_legs_to_innenstadt())
    assert stations == ["Hagen Hbf", "Köln Hbf"]


def test_build_card_phase_a_rules():
    card = build_card("Schnellste", _legs_to_innenstadt(), price_eur=84.90)
    assert card.confidence == "scheduled"
    assert card.expected_arrival == "12:04"  # last leg arr, HH:MM
    assert card.transfers == 2
    assert card.transfer_stations == ["Hagen Hbf", "Köln Hbf"]
    assert card.comfort == []
    assert card.risks == []


def test_build_card_taxi_warning_populates_risks():
    legs = [
        Leg("first_mile", "taxi", "Haßlinghausen", "Wuppertal Hbf", "07:10", "07:38", None, 11),
        Leg("backbone", "rail", "Wuppertal Hbf", "Freiburg (Breisgau) Hbf", "07:49", "11:31", "ICE", None),
    ]
    card = build_card("Sicherste", legs, taxi_warning="Taxi-Verfügbarkeit unsicher")
    assert card.risks == ["Taxi-Verfügbarkeit unsicher"]
    assert card.transfers == 1
    assert card.transfer_stations == ["Wuppertal Hbf"]


def test_to_json_uses_from_key_and_round_trips():
    legs = _legs_to_innenstadt()
    score = Score(282.9, 283.0, 283.0, 0.16, 2, 9, 0, 512.4, 430.4)
    card = build_card("Schnellste", legs, price_eur=84.90)
    strat = Strategy("fastest", "Schnellste", score, legs, card)
    portfolio = Portfolio(
        query={"origin": "Haßlinghausen", "destination": "Freiburg Innenstadt"},
        parameters={"alpha_c": 0.7, "mode": "deterministic"},
        reference_corridors=[ReferenceCorridor("hagen-koeln-freiburg", 512.4)],
        strategies=[strat],
    )
    doc = json.loads(to_json(portfolio))
    leg0 = doc["strategies"][0]["legs"][0]
    assert "from" in leg0 and "from_" not in leg0
    assert leg0["from"] == "Haßlinghausen"
    assert doc["strategies"][0]["card"]["confidence"] == "scheduled"
    assert doc["reference_corridors"][0]["backbone_km"] == 512.4
    # expected_arrival equals the last leg's arrival (handbook §7.2).
    assert doc["strategies"][0]["card"]["expected_arrival"] == hhmm(legs[-1].arr)
