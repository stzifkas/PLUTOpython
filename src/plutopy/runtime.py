"""Runtime library used by transpiled PLUTO procedures.

Transpiled output imports `Runtime`, `Procedure`, and helper functions
from this module. Keeping the runtime explicit means the emitted Python
is readable and debuggable on its own.
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

log = logging.getLogger("plutopy")


class PlutoRuntimeError(RuntimeError):
    pass


@dataclass
class Event:
    name: str
    description: Optional[str] = None
    raised: bool = False

    def raise_(self) -> None:
        self.raised = True
        log.info("event raised: %s", self.name)


@dataclass
class SystemElement:
    name: str
    kind: str = "part"
    description: str = ""
    children: List["SystemElement"] = field(default_factory=list)
    redundant: List[str] = field(default_factory=list)

    def qualified(self) -> str:
        return self.name


@dataclass
class Activity:
    name: str
    target: str
    handler: Callable[["Activity"], Any]
    criticality: str = "routine"

    def invoke(self) -> Any:
        log.info("activity: %s on %s", self.name, self.target)
        return self.handler(self)


_systems: Dict[str, SystemElement] = {}
_activities: Dict[tuple, Activity] = {}


def register_system(elem: SystemElement) -> SystemElement:
    _systems[elem.name] = elem
    return elem


def register_activity(act: Activity) -> Activity:
    _activities[(act.name, act.target)] = act
    return act


def resolve_system(qualified_name: str) -> SystemElement:
    parts = [p.strip() for p in qualified_name.split(" of ")]
    head = parts[0]
    if head not in _systems:
        raise PlutoRuntimeError(f"unknown system element: {head!r} (from {qualified_name!r})")
    return _systems[head]


def resolve_activity(name: str, target: str) -> Activity:
    key = (name, target)
    if key in _activities:
        return _activities[key]
    head_target = target.split(" of ")[0].strip()
    if (name, head_target) in _activities:
        return _activities[(name, head_target)]
    raise PlutoRuntimeError(f"unknown activity: {name!r} on {target!r}")


def _default_switch_on(activity: Activity) -> str:
    msg = f"[ACTIVITY] Switch on {activity.target}"
    print(msg)
    return msg


def _default_switch_off(activity: Activity) -> str:
    msg = f"[ACTIVITY] Switch off {activity.target}"
    print(msg)
    return msg


def switch_on(target: str) -> Callable[[], Any]:
    def _call():
        try:
            act = resolve_activity("Switch on", target)
        except PlutoRuntimeError:
            act = Activity("Switch on", target, _default_switch_on)
        return act.invoke()
    _call.__pluto_name__ = f"Switch on {target}"
    return _call


def switch_off(target: str) -> Callable[[], Any]:
    def _call():
        try:
            act = resolve_activity("Switch off", target)
        except PlutoRuntimeError:
            act = Activity("Switch off", target, _default_switch_off)
        return act.invoke()
    _call.__pluto_name__ = f"Switch off {target}"
    return _call


def initiate(call: Callable[[], Any]) -> threading.Thread:
    t = threading.Thread(target=call, name=getattr(call, "__pluto_name__", "activity"))
    t.start()
    return t


def initiate_and_confirm(call: Callable[[], Any]) -> Any:
    return call()


@dataclass
class Step:
    name: str
    body: Callable[[], None]
    status: str = "not initiated"

    def run(self) -> None:
        self.status = "executing"
        log.info("step start: %s", self.name)
        try:
            self.body()
            self.status = "completed"
            log.info("step complete: %s", self.name)
        except Exception as e:
            self.status = "failed"
            log.error("step failed: %s: %s", self.name, e)
            raise


def initiate_and_confirm_step(name: str, body: Callable[[], None]) -> Step:
    step = Step(name, body)
    step.run()
    return step


def parallel_until_all(calls: List[Callable[[], Any]]) -> None:
    threads = [threading.Thread(target=c, name=getattr(c, "__pluto_name__", "branch")) for c in calls]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def parallel_until_one(calls: List[Callable[[], Any]]) -> None:
    done = threading.Event()
    results: List[Any] = []
    lock = threading.Lock()

    def wrap(c):
        def runner():
            try:
                r = c()
            except Exception as e:
                r = e
            with lock:
                results.append(r)
            done.set()
        return runner

    threads = [threading.Thread(target=wrap(c), daemon=True) for c in calls]
    for t in threads:
        t.start()
    done.wait()


def wait_for_event(proc: "Procedure", event_name: str, timeout: Optional[float] = None) -> None:
    deadline = None if timeout is None else time.time() + timeout
    while True:
        evt = proc.events.get(event_name)
        if evt and evt.raised:
            return
        if deadline is not None and time.time() >= deadline:
            raise PlutoRuntimeError(f"timeout waiting for event {event_name!r}")
        time.sleep(0.01)


def wait_until(predicate: Callable[[], bool], timeout: Optional[float] = None) -> None:
    deadline = None if timeout is None else time.time() + timeout
    while not predicate():
        if deadline is not None and time.time() >= deadline:
            raise PlutoRuntimeError("timeout in wait until")
        time.sleep(0.01)


def inform_user(*parts: Any) -> None:
    print("[INFORM]", " ".join(str(p) for p in parts))


def pluto_log(*parts: Any) -> None:
    log.info("[LOG] %s", " ".join(str(p) for p in parts))


@dataclass
class Procedure:
    name: str = "procedure"
    execution_status: str = "not initiated"
    confirmation_status: str = "not available"
    events: Dict[str, Event] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)

    def declare_event(self, event: Event) -> Event:
        self.events[event.name] = event
        return event

    def raise_event(self, name: str) -> None:
        if name not in self.events:
            raise PlutoRuntimeError(f"event not declared: {name!r}")
        self.events[name].raise_()

    def start(self) -> None:
        self.execution_status = "executing"
        log.info("procedure start: %s", self.name)

    def finish(self) -> None:
        self.execution_status = "completed"
        self.confirmation_status = "confirmed"
        log.info("procedure complete: %s", self.name)
