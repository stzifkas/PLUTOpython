import time

import pytest

from plutopy.runtime import (
    Activity,
    Event,
    PlutoRuntimeError,
    Procedure,
    initiate_and_confirm,
    parallel_until_all,
    register_activity,
    resolve_activity,
    switch_on,
    wait_for_event,
)


def test_event_raise_and_wait():
    proc = Procedure()
    proc.declare_event(Event("ready"))
    proc.raise_event("ready")
    # should return immediately since already raised
    wait_for_event(proc, "ready", timeout=0.5)


def test_wait_for_event_timeout():
    proc = Procedure()
    proc.declare_event(Event("never"))
    with pytest.raises(PlutoRuntimeError):
        wait_for_event(proc, "never", timeout=0.05)


def test_default_switch_on_runs(capsys):
    initiate_and_confirm(switch_on("Star Tracker9"))
    captured = capsys.readouterr().out
    assert "Switch on Star Tracker9" in captured


def test_register_and_resolve_activity():
    called = []

    def handler(act):
        called.append(act.target)

    register_activity(Activity("Switch on", "Custom Target", handler))
    resolved = resolve_activity("Switch on", "Custom Target")
    resolved.invoke()
    assert called == ["Custom Target"]


def test_parallel_until_all_runs_concurrently():
    order = []

    def make(label, delay):
        def fn():
            time.sleep(delay)
            order.append(label)
        return fn

    start = time.time()
    parallel_until_all([make("a", 0.05), make("b", 0.05), make("c", 0.05)])
    elapsed = time.time() - start
    assert set(order) == {"a", "b", "c"}
    # if these ran serially, elapsed would be ~0.15s
    assert elapsed < 0.12, f"expected concurrency, took {elapsed:.3f}s"
