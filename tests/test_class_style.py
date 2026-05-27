"""Tests for --style class transpile mode."""
import pathlib
import subprocess
import sys

import pytest

from plutopy.transpiler import transpile, TranspileError


ROOT = pathlib.Path(__file__).parent.parent
EXAMPLES = ROOT / "examples"


def _run_cli(*args):
    env = {"PYTHONPATH": str(ROOT / "src")}
    return subprocess.run(
        [sys.executable, "-m", "plutopy", *args],
        env=env, capture_output=True, text=True, cwd=str(ROOT), check=False,
    )


def test_class_style_emits_subclass():
    src = (EXAMPLES / "04_events.pluto").read_text()
    out = transpile(src, style="class")
    assert "class TranspiledProcedure(Procedure):" in out
    assert "def __init__(self):" in out
    assert 'super().__init__("transpiled")' in out
    assert "def run(self):" in out
    assert "self.start()" in out
    assert "self.finish()" in out
    assert "self.declare_event(Event(\"ready\"" in out
    assert 'self.raise_event("ready")' in out
    assert 'wait_for_event(self, "ready")' in out


def test_class_style_invocation_in_footer():
    src = "procedure main log \"x\" end main end procedure"
    out = transpile(src, style="class")
    assert "TranspiledProcedure().run()" in out
    assert "main()" not in out.split("if __name__")[1]


def test_class_style_with_watchdog():
    src = (EXAMPLES / "08_watchdog.pluto").read_text()
    out = transpile(src, style="class")
    # Watchdog handlers registered inside __init__
    init_section = out.split("def run(self)")[0]
    assert "self.register_watchdog" in init_section
    assert "def _watchdog_" in init_section


def test_class_async_combo():
    src = (EXAMPLES / "08_watchdog.pluto").read_text()
    out = transpile(src, style="class", runtime="async")
    assert "class TranspiledProcedure(Procedure):" in out
    assert "async def run(self):" in out
    assert "async def _watchdog_" in out
    assert "await self.raise_event" in out
    assert "asyncio.run(TranspiledProcedure().run())" in out


def test_unknown_style_raises():
    with pytest.raises(TranspileError):
        transpile("procedure main log \"x\" end main end procedure", style="bogus")


def test_functions_default_unchanged():
    src = (EXAMPLES / "01_original.pluto").read_text()
    out = transpile(src)
    assert "class " not in out
    assert "def main():" in out


def test_cli_run_class_style():
    result = _run_cli("run", "--style", "class", str(EXAMPLES / "01_original.pluto"))
    assert result.returncode == 0, result.stderr
    assert "Switch on Star Tracker2" in result.stdout


def test_cli_run_class_async_watchdog():
    result = _run_cli("run", "--style", "class", "--runtime", "async",
                      str(EXAMPLES / "08_watchdog.pluto"))
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert out.index("Switch on Reaction Wheel3") < out.index("watchdog handling boom")


def test_all_examples_compile_in_all_combos():
    for path in sorted(EXAMPLES.glob("*.pluto")):
        for runtime in ("threaded", "async"):
            for style in ("functions", "class"):
                out = transpile(path.read_text(), runtime=runtime, style=style)
                compile(out, str(path), "exec")
