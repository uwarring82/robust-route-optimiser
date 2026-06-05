"""Unit tests for rro.config — the strict YAML contract (handbook §2.6, §8.3)."""

from __future__ import annotations

import pytest

from rro.config import ConfigError, parse_config, require_departure_time


def test_defaults_applied(valid_config_dict):
    cfg = parse_config(valid_config_dict)
    assert cfg.t_first_minutes == 45
    assert cfg.depths == 3
    assert cfg.epsilon.time_min == 3.0
    assert cfg.epsilon.creativity == 0.05
    assert cfg.alpha_c == 0.7
    assert cfg.quantile == 0.8
    assert cfg.fragile_headway_min == 30.0
    assert cfg.accessibility_required is False
    assert cfg.bahncard is None


def test_unknown_top_level_key_rejected(valid_config_dict):
    valid_config_dict["surprise"] = 1
    with pytest.raises(ConfigError, match="unknown key"):
        parse_config(valid_config_dict)


def test_unknown_epsilon_key_rejected(valid_config_dict):
    valid_config_dict["epsilon"] = {"time_min": 3, "nope": 1}
    with pytest.raises(ConfigError, match="epsilon"):
        parse_config(valid_config_dict)


@pytest.mark.parametrize("missing", ["origin", "destination", "feeds"])
def test_missing_required_key(valid_config_dict, missing):
    del valid_config_dict[missing]
    with pytest.raises(ConfigError, match="required"):
        parse_config(valid_config_dict)


def test_requires_at_least_one_gtfs(valid_config_dict):
    valid_config_dict["feeds"] = [
        {"id": "osm", "kind": "osm_pbf", "url": "u"},
    ]
    with pytest.raises(ConfigError, match="gtfs"):
        parse_config(valid_config_dict)


def test_requires_exactly_one_osm(valid_config_dict):
    valid_config_dict["feeds"].append(
        {"id": "osm2", "kind": "osm_pbf", "url": "u"}
    )
    with pytest.raises(ConfigError, match="osm_pbf"):
        parse_config(valid_config_dict)


def test_bad_feed_kind_rejected(valid_config_dict):
    valid_config_dict["feeds"][0]["kind"] = "weather"
    with pytest.raises(ConfigError, match="kind"):
        parse_config(valid_config_dict)


def test_epsilon_overrides(valid_config_dict):
    valid_config_dict["epsilon"] = {"time_min": 5, "creativity": 0.1}
    cfg = parse_config(valid_config_dict)
    assert cfg.epsilon.time_min == 5
    assert cfg.epsilon.creativity == 0.1


def test_require_departure_time_override_wins(valid_config_dict):
    cfg = parse_config(valid_config_dict)
    assert require_departure_time(cfg, "2026-01-01T00:00:00+01:00").startswith("2026-01-01")
    assert require_departure_time(cfg).startswith("2026-06-08")  # from config


def test_require_departure_time_missing_errors(valid_config_dict):
    del valid_config_dict["departure_time"]
    cfg = parse_config(valid_config_dict)
    assert cfg.departure_time is None  # optional at load time
    with pytest.raises(ConfigError, match="departure_time required"):
        require_departure_time(cfg)
