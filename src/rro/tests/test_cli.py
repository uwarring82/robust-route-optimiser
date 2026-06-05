"""CLI exit-code contract tests (handbook §8.1).

Exit codes: 0 ok; 1 internal/not-implemented; 2 config/validation; 3 OTP; 4 underfull.
"""

from __future__ import annotations

import pytest

from rro.cli import EXIT_NOTIMPL, EXIT_VALIDATION, main

_VALID_YAML = """
origin: "Haßlinghausen"
destination: "Freiburg (Breisgau) Hbf"
departure_time: "2026-06-08T07:30:00+02:00"
feeds:
  - {id: delfi, kind: gtfs, url: "https://example/g.zip"}
  - {id: osm, kind: osm_pbf, url: "https://example/c.pbf"}
"""


def _write(tmp_path, text, name="corridor.yml"):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_valid_plan_returns_documented_notimpl_not_traceback(tmp_path, capsys):
    rc = main(["plan", "--config", _write(tmp_path, _VALID_YAML)])
    assert rc == EXIT_NOTIMPL  # documented (1), not an uncaught exception
    assert "not yet implemented" in capsys.readouterr().err


def test_missing_config_file_exits_2(capsys):
    assert main(["plan", "--config", "/no/such/file.yml"]) == EXIT_VALIDATION


def test_unknown_key_exits_2(tmp_path, capsys):
    bad = _VALID_YAML + "surprise: 1\n"
    assert main(["plan", "--config", _write(tmp_path, bad)]) == EXIT_VALIDATION


def test_missing_departure_and_no_flag_exits_2(tmp_path, capsys):
    no_dep = _VALID_YAML.replace(
        'departure_time: "2026-06-08T07:30:00+02:00"\n', ""
    )
    rc = main(["plan", "--config", _write(tmp_path, no_dep)])
    assert rc == EXIT_VALIDATION
    assert "departure_time required" in capsys.readouterr().err


def test_depart_flag_supplies_missing_departure(tmp_path, capsys):
    # With --depart provided, departure resolves and we reach the pipeline stub (1).
    no_dep = _VALID_YAML.replace(
        'departure_time: "2026-06-08T07:30:00+02:00"\n', ""
    )
    rc = main(["plan", "--config", _write(tmp_path, no_dep),
               "--depart", "2026-06-08T07:30:00+02:00"])
    assert rc == EXIT_NOTIMPL


@pytest.mark.parametrize(
    "flag,value",
    [
        ("--alpha-c", "-1"), ("--quantile", "2"), ("--epsilon", "-5"),
        ("--alpha-c", "nan"), ("--quantile", "nan"), ("--epsilon", "inf"),
    ],
)
def test_out_of_range_overrides_exit_2(tmp_path, capsys, flag, value):
    # CLI overrides must be re-validated, not passed through to the pipeline.
    rc = main(["plan", "--config", _write(tmp_path, _VALID_YAML), flag, value])
    assert rc == EXIT_VALIDATION
    assert "config error" in capsys.readouterr().err
