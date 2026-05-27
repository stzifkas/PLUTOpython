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
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

log = logging.getLogger("plutopy")


class PlutoRuntimeError(RuntimeError):
    pass


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
    handler: Callable[["Activity"], Any]
    criticality: str = "routine"

    async def invoke(self) -> Any:
        log.info("activity: %s on %s", self.name, self.target)
        if inspect.iscoroutinefunction(self.handler):
            return await self.handler(self)
        return await asyncio.to_thread(self.handler, self)


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


def _default_switch_on(activity: Activity) -> str:
    msg = f"[ACTIVITY] Switch on {activity.target}"
    print(msg)
    return msg


def _default_switch_off(activity: Activity) -> str:
    msg = f"[ACTIVITY] Switch off {activity.target}"
    print(msg)
    return msg


def switch_on(target: str) -> Callable[[], Awaitable[Any]]:
    async def _call():
        try:
            act = resolve_activity("Switch on", target)
        except PlutoRuntimeError:
            act = Activity("Switch on", target, _default_switch_on)
        return await act.invoke()
    _call.__pluto_name__ = f"Switch on {target}"
    return _call


def switch_off(target: str) -> Callable[[], Awaitable[Any]]:
    async def _call():
        try:
            act = resolve_activity("Switch off", target)
        except PlutoRuntimeError:
            act = Activity("Switch off", target, _default_switch_off)
        return await act.invoke()
    _call.__pluto_name__ = f"Switch off {target}"
    return _call


def initiate(call: Callable[[], Awaitable[Any]]) -> asyncio.Task:
    """Fire and forget: schedule the call but do not await it here."""
    coro = call() if inspect.iscoroutinefunction(call) else asyncio.to_thread(call)
    return asyncio.create_task(coro)


async def initiate_and_confirm(call: CallableOrCoro) -> Any:
    if inspect.iscoroutinefunction(call):
        return await call()
    if inspect.iscoroutine(call):
        return await call
    return await asyncio.to_thread(call)


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


async def initiate_and_confirm_step(name: str, body: Callable[[], Awaitable[None]]) -> Step:
    step = Step(name, body)
    await step.run()
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

    def start(self) -> None:
        self.execution_status = "executing"
        log.info("procedure start: %s", self.name)

    def finish(self) -> None:
        self.execution_status = "completed"
        self.confirmation_status = "confirmed"
        log.info("procedure complete: %s", self.name)
