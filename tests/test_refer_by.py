"""Tests for `refer by` clause (PLUTO spec A.3.9.27)."""
import pathlib
import subprocess
import sys

from plutopy.parser import parse
from plutopy.transpiler import transpile


ROOT = pathlib.Path(__file__).parent.parent
EXAMPLES = ROOT / "examples"


def _run_cli(*args):
    env = {"PYTHONPATH": str(ROOT / "src")}
    return subprocess.run(
        [sys.executable, "-m", "plutopy", *args],
        env=env, capture_output=True, text=True, cwd=str(ROOT), check=False,
    )


def test_grammar_parses_refer_by():
    src = "procedure main initiate Switch on X refer by INSTANCE_A end main end procedure"
    tree = parse(src)
    init = tree.children[0].children[0].children[0]
    assert init.data == "initiate_stmt"
    refers = [c for c in init.children if hasattr(c, "data") and c.data == "refer_by"]
    assert len(refers) == 1


def test_transpile_emits_instance_name_kwarg():
    src = "procedure main initiate Switch on X refer by INSTANCE_A end main end procedure"
    out = transpile(src)
    assert 'instance_name="INSTANCE_A"' in out


def test_transpile_without_refer_by_unchanged():
    src = "procedure main initiate Switch on X end main end procedure"
    out = transpile(src)
    assert "instance_name" not in out


def test_refer_by_makes_execution_status_queryable():
    result = _run_cli("run", str(EXAMPLES / "11_refer_by.pluto"))
    assert result.returncode == 0, result.stderr
    out = result.stdout
    # both "tracker boot kicked off" and "tracker is up" must appear, in order
    assert out.index("tracker boot kicked off") < out.index("tracker is up")
    assert "Switch on Star Tracker1" in out


def test_refer_by_works_in_async_runtime():
    result = _run_cli("run", "--runtime", "async", str(EXAMPLES / "11_refer_by.pluto"))
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "tracker is up" in out
    assert "Switch on Star Tracker1" in out


def test_refer_by_round_trips_through_formatter():
    from plutopy.formatter import format_source
    src = (EXAMPLES / "11_refer_by.pluto").read_text()
    formatted = format_source(src)
    assert "refer by TRACKER1_BOOT" in formatted
    # idempotent
    assert format_source(formatted) == formatted


def test_refer_by_serialises_to_json():
    from plutopy.json_emit import transpile_to_dict
    src = (EXAMPLES / "11_refer_by.pluto").read_text()
    d = transpile_to_dict(src)
    initiate_stmts = [s for s in d["main"] if s["kind"] == "initiate"]
    assert initiate_stmts
    assert initiate_stmts[0]["refer_by"] == "TRACKER1_BOOT"
