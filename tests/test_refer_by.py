"""Tests for `refer by` clause (PLUTO spec A.3.9.27)."""
import pathlib
import subprocess
import sys

from pluto_ecss.parser import parse
from pluto_ecss.transpiler import transpile


ROOT = pathlib.Path(__file__).parent.parent
EXAMPLES = ROOT / "examples"


def _run_cli(*args):
    env = {"PYTHONPATH": str(ROOT / "src")}
    return subprocess.run(
        [sys.executable, "-m", "pluto_ecss", *args],
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
    from pluto_ecss.formatter import format_source
    src = (EXAMPLES / "11_refer_by.pluto").read_text()
    formatted = format_source(src)
    assert "refer by TRACKER1_BOOT" in formatted
    # idempotent
    assert format_source(formatted) == formatted


def test_refer_by_serialises_to_json():
    from pluto_ecss.json_emit import transpile_to_dict
    src = (EXAMPLES / "11_refer_by.pluto").read_text()
    d = transpile_to_dict(src)
    initiate_stmts = [s for s in d["main"] if s["kind"] == "initiate"]
    assert initiate_stmts
    assert initiate_stmts[0]["refer_by"] == "TRACKER1_BOOT"


def test_refer_by_on_initiate_and_confirm_grammar():
    """A.3.9.26: `initiate and confirm <call> [refer by NAME] [continuation_test]`"""
    src = """
    procedure main
      initiate and confirm Switch on X refer by RUN1
    end main end procedure
    """
    tree = parse(src)
    ic = tree.children[0].children[0].children[0]
    assert ic.data == "initiate_confirm_stmt"
    refers = [c for c in ic.children if hasattr(c, "data") and c.data == "refer_by"]
    assert len(refers) == 1


def test_refer_by_on_initiate_and_confirm_emits_kwarg():
    src = "procedure main initiate and confirm Switch on X refer by RUN1 end main end procedure"
    out = transpile(src)
    assert 'instance_name="RUN1"' in out
    assert "initiate_and_confirm(proc," in out


def test_refer_by_on_confirm_composes_with_continuation_test():
    src = """
    procedure main
      initiate and confirm Switch on X refer by RUN1
        in case not confirmed: restart max 2 times; end case
    end main end procedure
    """
    out = transpile(src)
    assert 'instance_name="RUN1"' in out
    assert "_restarts_" in out


def test_refer_by_on_confirm_queryable_at_runtime():
    src = """
    procedure main
      initiate and confirm Switch on X refer by RUN1
      wait until execution_status of RUN1 = "success"
      inform user "ok"
    end main end procedure
    """
    py = transpile(src)
    ns = {"__name__": "__test__"}
    exec(compile(py, "<test>", "exec"), ns)
    ns["main"]()  # should not raise


def test_refer_by_on_confirm_formatter_round_trip():
    from pluto_ecss.formatter import format_source
    src = """
    procedure main
      initiate and confirm Switch on X refer by RUN1
    end main end procedure
    """
    formatted = format_source(src)
    assert "refer by RUN1" in formatted
    assert format_source(formatted) == formatted


def test_refer_by_on_confirm_json_serialisation():
    from pluto_ecss.json_emit import transpile_to_dict
    src = "procedure main initiate and confirm Switch on X refer by RUN1 end main end procedure"
    d = transpile_to_dict(src)
    ic = d["main"][0]
    assert ic["kind"] == "initiate_and_confirm"
    assert ic["refer_by"] == "RUN1"
