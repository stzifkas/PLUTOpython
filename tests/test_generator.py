"""Tests for the YAML / dict -> PLUTO generator."""
import pathlib
import subprocess
import sys

import pytest

from plutopy.generator import (
    GeneratorError,
    generate_from_spec,
    generate_from_yaml,
)
from plutopy.parser import parse


ROOT = pathlib.Path(__file__).parent.parent


def test_minimal_spec_generates_valid_pluto():
    spec = {"main": [{"log": "hello"}]}
    out = generate_from_spec(spec)
    assert "procedure" in out
    assert 'log "hello"' in out
    assert "end procedure" in out
    parse(out)


def test_spec_with_declare_and_main():
    spec = {
        "declare": [{"event": "ready", "description": "Spacecraft ready"}, {"event": "boom"}],
        "main": [{"raise": "ready"}],
    }
    out = generate_from_spec(spec)
    assert "event ready described by Spacecraft ready" in out
    assert "event boom" in out
    assert "raise event ready" in out


def test_spec_with_watchdog():
    spec = {
        "declare": [{"event": "boom"}],
        "watchdog": {
            "boom": [
                {"inform_user": "handling"},
                {"initiate_and_confirm": {"switch_off": "Reaction Wheel3"}},
            ]
        },
        "main": [{"raise": "boom"}],
    }
    out = generate_from_spec(spec)
    assert "watchdog" in out
    assert "on boom do" in out
    assert "Switch off Reaction Wheel3" in out


def test_spec_with_control_flow():
    spec = {
        "main": [
            {"assign": {"var": "x", "value": 0}},
            {
                "while": {
                    "condition": "x < 3",
                    "body": [{"assign": {"var": "x", "value": "x + 1"}}],
                }
            },
            {
                "if": {
                    "condition": "x = 3",
                    "then": [{"inform_user": "done"}],
                    "else": [{"inform_user": "huh"}],
                }
            },
        ]
    }
    out = generate_from_spec(spec)
    assert "while x < 3 do" in out
    assert "x := x + 1" in out
    assert "if x = 3 then" in out
    assert "else" in out


def test_spec_with_parallel_and_step():
    spec = {
        "main": [
            {
                "parallel": {
                    "mode": "all",
                    "branches": [
                        {"step": {"name": "A", "body": [{"initiate_and_confirm": {"switch_on": "Star Tracker1"}}]}},
                        {"step": {"name": "B", "body": [{"initiate_and_confirm": {"switch_on": "Star Tracker2"}}]}},
                    ],
                }
            }
        ]
    }
    out = generate_from_spec(spec)
    assert "in parallel until all complete" in out
    assert "initiate and confirm step A" in out
    assert "initiate and confirm step B" in out
    assert "Switch on Star Tracker1" in out


def test_parallel_one_mode():
    spec = {
        "main": [{
            "parallel": {
                "mode": "one",
                "branches": [
                    {"step": {"name": "A", "body": [{"log": "a"}]}},
                    {"step": {"name": "B", "body": [{"log": "b"}]}},
                ],
            }
        }]
    }
    out = generate_from_spec(spec)
    assert "in parallel until one completes" in out


def test_wait_for_with_timeout():
    spec = {
        "declare": [{"event": "r"}],
        "main": [
            {"raise": "r"},
            {"wait_for": {"event": "r", "timeout": 5}},
        ],
    }
    out = generate_from_spec(spec)
    assert "wait for event r with timeout 5" in out


def test_missing_main_raises():
    with pytest.raises(GeneratorError):
        generate_from_spec({"declare": [{"event": "e"}]})


def test_unknown_statement_raises():
    with pytest.raises(GeneratorError):
        generate_from_spec({"main": [{"jump": "moon"}]})


def test_yaml_round_trip_from_file():
    yaml_text = """
procedure: T
declare:
  - event: ready
main:
  - log: "go"
  - raise: ready
"""
    out = generate_from_yaml(yaml_text)
    assert "event ready" in out
    assert 'log "go"' in out


def test_cli_gen_to_file(tmp_path):
    spec = tmp_path / "spec.yaml"
    spec.write_text("main:\n  - log: \"x\"\n")
    out = tmp_path / "out.pluto"
    env = {"PYTHONPATH": str(ROOT / "src")}
    r = subprocess.run(
        [sys.executable, "-m", "plutopy", "gen", str(spec), "-o", str(out)],
        env=env, capture_output=True, text=True, cwd=str(ROOT), check=False,
    )
    assert r.returncode == 0, r.stderr
    assert "log " in out.read_text()


def test_example_spec_generates_and_runs():
    """The shipped example spec should produce a procedure that runs end-to-end."""
    spec_path = ROOT / "examples" / "specs" / "bringup.yaml"
    out = generate_from_yaml(spec_path.read_text())
    # If we made it here, parsing succeeded; also run the generated code.
    import tempfile
    tmp = pathlib.Path(tempfile.mkstemp(suffix=".pluto")[1])
    try:
        tmp.write_text(out)
        env = {"PYTHONPATH": str(ROOT / "src")}
        r = subprocess.run(
            [sys.executable, "-m", "plutopy", "run", str(tmp)],
            env=env, capture_output=True, text=True, cwd=str(ROOT), check=False,
        )
        assert r.returncode == 0, r.stderr
        assert "bring up complete" in r.stdout
    finally:
        tmp.unlink()
