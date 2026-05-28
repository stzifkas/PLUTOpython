"""Tests for the async runtime + --runtime async transpile mode."""
import pathlib
import subprocess
import sys

import pytest

from pluto_ecss.transpiler import transpile


ROOT = pathlib.Path(__file__).parent.parent
EXAMPLES = ROOT / "examples"


def _run_cli(*args):
    env = {"PYTHONPATH": str(ROOT / "src")}
    return subprocess.run(
        [sys.executable, "-m", "pluto_ecss", *args],
        env=env, capture_output=True, text=True, cwd=str(ROOT), check=False,
    )


def test_async_emits_async_def_main():
    src = (EXAMPLES / "01_original.pluto").read_text()
    out = transpile(src, runtime="async")
    assert "async def main():" in out
    assert "from pluto_ecss.async_runtime import" in out
    assert "asyncio.run(main())" in out
    # awaitable calls have `await`
    assert "await initiate_and_confirm" in out
    assert "await parallel_until_all" in out
    # fire-and-forget initiate is NOT awaited (it's a task scheduler)
    assert "initiate(proc, switch_on" in out


def test_async_emits_async_steps_and_branches():
    src = (EXAMPLES / "01_original.pluto").read_text()
    out = transpile(src, runtime="async")
    assert "async def _branch_" in out
    assert "async def _step_" in out


def test_async_watchdog_uses_async_def():
    src = (EXAMPLES / "08_watchdog.pluto").read_text()
    out = transpile(src, runtime="async")
    assert "async def _watchdog_" in out
    assert "await proc.raise_event" in out


def test_async_wait_for_event_is_awaited():
    src = (EXAMPLES / "09_timeout.pluto").read_text()
    out = transpile(src, runtime="async")
    assert "await wait_for_event" in out


def test_threaded_default_unchanged():
    src = (EXAMPLES / "01_original.pluto").read_text()
    out = transpile(src)  # default
    assert "async def" not in out
    assert "asyncio" not in out
    assert "from pluto_ecss.runtime import" in out


def test_unknown_runtime_raises():
    from pluto_ecss.transpiler import TranspileError
    with pytest.raises(TranspileError):
        transpile("procedure main log \"x\" end main end procedure", runtime="bogus")


def test_cli_run_async_original():
    result = _run_cli("run", "--runtime", "async", str(EXAMPLES / "01_original.pluto"))
    assert result.returncode == 0, result.stderr
    assert "Switch on Star Tracker2" in result.stdout
    assert "Switch on Star Tracker1" in result.stdout
    assert "Switch on Reaction Wheel3 of AOC of Satellite" in result.stdout


def test_cli_run_async_watchdog():
    result = _run_cli("run", "--runtime", "async", str(EXAMPLES / "08_watchdog.pluto"))
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert out.index("Switch on Reaction Wheel3") < out.index("watchdog handling boom")
    assert out.index("watchdog handling boom") < out.index("Switch off Reaction Wheel3")


def test_cli_run_async_loops_and_events():
    result = _run_cli("run", "--runtime", "async", str(EXAMPLES / "09_timeout.pluto"))
    assert result.returncode == 0, result.stderr
    assert "ready arrived in time" in result.stdout
    assert "counter reached 3" in result.stdout


def test_async_examples_all_compile():
    """Every example compiles under both runtimes and produces valid Python."""
    for path in sorted(EXAMPLES.glob("*.pluto")):
        out = transpile(path.read_text(), runtime="async")
        compile(out, str(path), "exec")


def test_async_parallel_uses_asyncio_gather_semantically():
    """parallel_until_all on the async runtime should run branches concurrently."""
    import asyncio
    import time
    from pluto_ecss import async_runtime as ar

    order = []

    async def a():
        await asyncio.sleep(0.05)
        order.append("a")

    async def b():
        await asyncio.sleep(0.05)
        order.append("b")

    async def c():
        await asyncio.sleep(0.05)
        order.append("c")

    async def runner():
        start = time.time()
        await ar.parallel_until_all([a, b, c])
        return time.time() - start

    elapsed = asyncio.run(runner())
    assert set(order) == {"a", "b", "c"}
    assert elapsed < 0.12, f"async didn't run concurrently: {elapsed:.3f}s"
