"""Tests for `in the context of X do ... end context` (PLUTO spec A.3.9.10)."""
import pathlib
import subprocess
import sys

from plutopy.transpiler import transpile


ROOT = pathlib.Path(__file__).parent.parent
EXAMPLES = ROOT / "examples"


def _run_cli(*args):
    env = {"PYTHONPATH": str(ROOT / "src")}
    return subprocess.run(
        [sys.executable, "-m", "plutopy", *args],
        env=env, capture_output=True, text=True, cwd=str(ROOT), check=False,
    )


def test_simple_context_appends_to_target():
    src = """
    procedure main
      in the context of Telescope1 do
        initiate and confirm Switch on Power Unit
      end context
    end main end procedure
    """
    out = transpile(src)
    assert 'switch_on("Power Unit of Telescope1")' in out


def test_context_does_not_leak_after_end():
    src = """
    procedure main
      in the context of Telescope1 do
        initiate and confirm Switch on A
      end context
      initiate and confirm Switch on B
    end main end procedure
    """
    out = transpile(src)
    assert 'switch_on("A of Telescope1")' in out
    assert 'switch_on("B")' in out
    assert 'switch_on("B of Telescope1")' not in out


def test_nested_contexts_compose_innermost_first():
    src = """
    procedure main
      in the context of Outer do
        in the context of Inner do
          initiate and confirm Switch on Thing
        end context
        initiate and confirm Switch on AfterInner
      end context
    end main end procedure
    """
    out = transpile(src)
    # nested: Thing -> innermost (Inner) first, then Outer
    assert 'switch_on("Thing of Inner of Outer")' in out
    # after closing Inner, only Outer applies
    assert 'switch_on("AfterInner of Outer")' in out


def test_qualified_context_target_appended():
    src = """
    procedure main
      in the context of Telescope1 of Payload do
        initiate and confirm Switch on Power Unit
      end context
    end main end procedure
    """
    out = transpile(src)
    assert 'switch_on("Power Unit of Telescope1 of Payload")' in out


def test_context_works_inside_steps():
    src = """
    procedure main
      in the context of T1 do
        initiate and confirm step BRINGUP
          main
            initiate and confirm Switch on Box;
          end main
        end step
      end context
    end main end procedure
    """
    out = transpile(src)
    assert 'switch_on("Box of T1")' in out


def test_example_runs_end_to_end():
    result = _run_cli("run", str(EXAMPLES / "13_set_context.pluto"))
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "Switch on Power Unit of Telescope1 of Payload" in out
    assert "Switch off Power Unit of Telescope1 of Payload" in out
    assert "Switch on Power Unit of Telescope2 of Payload" in out
    assert "both telescopes cycled" in out


def test_example_runs_in_async_mode():
    result = _run_cli("run", "--runtime", "async", str(EXAMPLES / "13_set_context.pluto"))
    assert result.returncode == 0, result.stderr
    assert "Telescope1 of Payload" in result.stdout
    assert "Telescope2 of Payload" in result.stdout


def test_context_with_arguments_composes():
    src = """
    procedure main
      in the context of T1 do
        initiate and confirm Switch on Box with Mode := "safe" end with
      end context
    end main end procedure
    """
    out = transpile(src)
    assert 'switch_on("Box of T1", arguments={"Mode": "safe"})' in out
