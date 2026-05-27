"""asyncio-flavoured runtime for transpiled PLUTO procedures.

Symmetric to plutopy.runtime, but:
  - `initiate_and_confirm`, `parallel_until_all/one`, `wait_for_event`,
    `wait_until`, and `Procedure.raise_event` are coroutines.
  - Events wrap `asyncio.Event` so waits are non-busy.
  - Sync activity handlers are dispatched via `asyncio.to_thread` so
    blocking telecommand stacks integrate without poisoning the loop.

Transpiled output with `--runtime async` imports from this module.
"""
from __future__ import annotations

import asyncio
import inspect
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

log = logging.getLogger("plutopy")


class PlutoRuntimeError(RuntimeError):
    pass


class PlutoAborted(Exception):
    """`abort` continuation action — propagates out of the procedure body."""


class PlutoTerminated(Exception):
    """`terminate` continuation action — jumps to the confirmation body."""


CallableOrCoro = Union[Callable[[], Any], Awaitable[Any]]


@dataclass
class Event:
    name: str
    description: Optional[str] = None
    _event: asyncio.Event = field(default_factory=asyncio.Event)

    def raise_(self) -> None:
        self._event.set()
        log.info("event raised: %s", self.name)

    @property
    def raised(self) -> bool:
        return self._event.is_set()


@dataclass
class SystemElement:
    name: str
    kind: str = "part"
    description: str = ""


@dataclass
class Activity:
    name: str
    target: str
    handler: Callable[..., Any]
    criticality: str = "routine"

    async def invoke(self, **arguments: Any) -> Any:
        log.info("activity: %s on %s", self.name, self.target)
        if inspect.iscoroutinefunction(self.handler):
            try:
                return await self.handler(self, **arguments)
            except TypeError:
                return await self.handler(self)
        try:
            return await asyncio.to_thread(self.handler, self, **arguments)
        except TypeError:
            return await asyncio.to_thread(self.handler, self)


@dataclass
class ActivityExecution:
    """Tracks execution state of an activity instance."""
    name: str
    execution_status: str = "pending"  # pending, executing, success, failure
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    confirmation_status: Optional[Any] = None

    def get_property(self, property_name: str) -> Any:
        """Get a property of this activity execution."""
        props = {
            "execution_status": self.execution_status,
            "start_time": self.start_time,
            "completion_time": self.completion_time,
            "confirmation_status": self.confirmation_status,
        }
        if property_name not in props:
            raise PlutoRuntimeError(f"unknown property: {property_name!r}")
        return props[property_name]


_activities: Dict[tuple, Activity] = {}


def register_activity(act: Activity) -> Activity:
    _activities[(act.name, act.target)] = act
    return act


def resolve_activity(name: str, target: str) -> Activity:
    key = (name, target)
    if key in _activities:
        return _activities[key]
    head = target.split(" of ")[0].strip()
    if (name, head) in _activities:
        return _activities[(name, head)]
    raise PlutoRuntimeError(f"unknown activity: {name!r} on {target!r}")


def _format_args(arguments: Optional[Dict[str, Any]]) -> str:
    if not arguments:
        return ""
    parts = ", ".join(f"{k}={v!r}" for k, v in arguments.items())
    return f" with {parts}"


def _default_switch_on(activity: Activity, **arguments: Any) -> str:
    msg = f"[ACTIVITY] Switch on {activity.target}{_format_args(arguments)}"
    print(msg)
    return msg


def _default_switch_off(activity: Activity, **arguments: Any) -> str:
    msg = f"[ACTIVITY] Switch off {activity.target}{_format_args(arguments)}"
    print(msg)
    return msg


def switch_on(target: str, *, arguments: Optional[Dict[str, Any]] = None) -> Callable[[], Awaitable[Any]]:
    args = arguments or {}
    async def _call():
        try:
            act = resolve_activity("Switch on", target)
        except PlutoRuntimeError:
            act = Activity("Switch on", target, _default_switch_on)
        return await act.invoke(**args)
    _call.__pluto_name__ = f"Switch on {target}"
    _call.arguments = args
    return _call


def switch_off(target: str, *, arguments: Optional[Dict[str, Any]] = None) -> Callable[[], Awaitable[Any]]:
    args = arguments or {}
    async def _call():
        try:
            act = resolve_activity("Switch off", target)
        except PlutoRuntimeError:
            act = Activity("Switch off", target, _default_switch_off)
        return await act.invoke(**args)
    _call.__pluto_name__ = f"Switch off {target}"
    _call.arguments = args
    return _call


def initiate(proc: "Procedure", call: Callable[[], Awaitable[Any]],
             instance_name: Optional[str] = None) -> asyncio.Task:
    """Fire-and-forget: schedule the call but do not await it here.

    When `instance_name` is given (PLUTO `refer by`), the activity is
    registered under that name so `<property> of MY_INSTANCE`
    references resolve to its execution state (spec A.3.9.27 / A.3.9.8).
    """
    activity_name = instance_name or getattr(call, "__pluto_name__", "activity")
    act_exec = proc.register_activity(activity_name)

    async def wrapper():
        act_exec.start_time = datetime.now()
        act_exec.execution_status = "executing"
        try:
            coro = call() if inspect.iscoroutinefunction(call) else asyncio.to_thread(call)
            result = await coro
            act_exec.confirmation_status = result
            act_exec.execution_status = "success"
        except Exception as e:
            act_exec.execution_status = "failure"
            act_exec.confirmation_status = str(e)
            raise
        finally:
            act_exec.completion_time = datetime.now()

    return asyncio.create_task(wrapper())


async def initiate_and_confirm(proc: "Procedure", call: CallableOrCoro) -> Any:
    activity_name = getattr(call, "__pluto_name__", "activity") if callable(call) else "activity"
    act_exec = proc.register_activity(activity_name)
    
    act_exec.start_time = datetime.now()
    act_exec.execution_status = "executing"
    try:
        if inspect.iscoroutinefunction(call):
            result = await call()
        elif inspect.iscoroutine(call):
            result = await call
        else:
            result = await asyncio.to_thread(call)
        act_exec.confirmation_status = result
        act_exec.execution_status = "success"
        return result
    except Exception as e:
        act_exec.execution_status = "failure"
        act_exec.confirmation_status = str(e)
        raise
    finally:
        act_exec.completion_time = datetime.now()


@dataclass
class Step:
    name: str
    body: Callable[[], Awaitable[None]]
    status: str = "not initiated"

    async def run(self) -> None:
        self.status = "executing"
        log.info("step start: %s", self.name)
        try:
            await self.body()
            self.status = "completed"
            log.info("step complete: %s", self.name)
        except Exception as e:
            self.status = "failed"
            log.error("step failed: %s: %s", self.name, e)
            raise


async def initiate_and_confirm_step(proc: "Procedure", name: str,
                                    body: Callable[[], Awaitable[None]]) -> Step:
    """Run a named step. The step is registered with the Procedure so its
    execution properties can be queried via PLUTO `<property> of <step_name>`
    references."""
    act_exec = proc.register_activity(name)
    step = Step(name, body)
    act_exec.start_time = datetime.now()
    act_exec.execution_status = "executing"
    try:
        await step.run()
        act_exec.execution_status = "success"
        act_exec.confirmation_status = "success"
    except Exception as e:
        act_exec.execution_status = "failure"
        act_exec.confirmation_status = str(e)
        raise
    finally:
        act_exec.completion_time = datetime.now()
    return step


async def parallel_until_all(calls: List[Callable[[], Awaitable[Any]]]) -> None:
    coros = [c() if inspect.iscoroutinefunction(c) else asyncio.to_thread(c) for c in calls]
    await asyncio.gather(*coros)


async def parallel_until_one(calls: List[Callable[[], Awaitable[Any]]]) -> None:
    coros = [
        asyncio.ensure_future(c() if inspect.iscoroutinefunction(c) else asyncio.to_thread(c))
        for c in calls
    ]
    done, pending = await asyncio.wait(coros, return_when=asyncio.FIRST_COMPLETED)
    for p in pending:
        p.cancel()
    # surface exceptions from the completed ones
    for task in done:
        exc = task.exception()
        if exc is not None:
            raise exc


async def wait_for_event(proc: "Procedure", event_name: str, timeout: Optional[float] = None) -> None:
    evt = proc.events.get(event_name)
    if evt is None:
        raise PlutoRuntimeError(f"event not declared: {event_name!r}")
    if timeout is None:
        await evt._event.wait()
    else:
        try:
            await asyncio.wait_for(evt._event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            raise PlutoRuntimeError(f"timeout waiting for event {event_name!r}") from None


async def wait_until(predicate: Callable[[], bool], timeout: Optional[float] = None) -> None:
    async def _poll():
        while not predicate():
            await asyncio.sleep(0.01)
    if timeout is None:
        await _poll()
    else:
        try:
            await asyncio.wait_for(_poll(), timeout=timeout)
        except asyncio.TimeoutError:
            raise PlutoRuntimeError("timeout in wait until") from None


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
    watchdog_handlers: Dict[str, Callable[[], Awaitable[None]]] = field(default_factory=dict)
    _activities: Dict[str, ActivityExecution] = field(default_factory=dict)

    def declare_event(self, event: Event) -> Event:
        self.events[event.name] = event
        return event

    def register_watchdog(self, event_name: str, handler: Callable[[], Awaitable[None]]) -> None:
        self.watchdog_handlers[event_name] = handler

    async def raise_event(self, name: str) -> None:
        if name not in self.events:
            raise PlutoRuntimeError(f"event not declared: {name!r}")
        self.events[name].raise_()
        handler = self.watchdog_handlers.get(name)
        if handler is not None:
            log.info("watchdog: handling %s", name)
            if inspect.iscoroutinefunction(handler):
                await handler()
            else:
                handler()

    def register_activity(self, activity_name: str) -> ActivityExecution:
        act = ActivityExecution(activity_name)
        self._activities[activity_name] = act
        return act

    def get_property(self, activity_name: str, property_name: str) -> Any:
        """Read a property of a tracked activity / step.

        For `execution_status` specifically, a step that has not yet been
        initiated returns "not_initiated" rather than raising — this matches
        the PLUTO spec's lifecycle: every activity has a defined status
        even before it starts.
        """
        if activity_name not in self._activities:
            if property_name == "execution_status":
                return "not_initiated"
            raise PlutoRuntimeError(f"activity not tracked: {activity_name!r}")
        return self._activities[activity_name].get_property(property_name)

    def start(self) -> None:
        self.execution_status = "executing"
        log.info("procedure start: %s", self.name)

    def finish(self) -> None:
        self.execution_status = "completed"
        self.confirmation_status = "confirmed"
        log.info("procedure complete: %s", self.name)
