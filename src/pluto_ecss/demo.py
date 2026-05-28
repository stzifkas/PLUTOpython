"""Live TUI demo: visualises a fake satellite reacting to a PLUTO procedure.

Run with:
    pluto-ecss demo                   # uses examples/05_full_bringup.pluto
    pluto-ecss demo path/to/script.pluto
"""
from __future__ import annotations

import pathlib
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List

from pluto_ecss import runtime
from pluto_ecss.runtime import Activity, register_activity
from pluto_ecss.transpiler import transpile

try:
    from rich.console import Group
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
except ImportError as e:  # pragma: no cover
    raise SystemExit(
        "The `demo` command requires the 'rich' package.\n"
        "Install it with: pip install pluto-ecss[tui]   (or: pip install rich)"
    ) from e


@dataclass
class DashboardState:
    """Pure state. The renderer reads it; the activity handlers mutate it."""
    components: Dict[str, str] = field(default_factory=dict)
    activity_feed: List[str] = field(default_factory=list)
    event_log: List[str] = field(default_factory=list)
    procedure_status: str = "not initiated"
    lock: threading.Lock = field(default_factory=threading.Lock)

    def set_component(self, name: str, status: str) -> None:
        with self.lock:
            self.components[name] = status

    def push_activity(self, line: str) -> None:
        with self.lock:
            self.activity_feed.append(line)
            self.activity_feed[:] = self.activity_feed[-12:]

    def push_event(self, line: str) -> None:
        with self.lock:
            self.event_log.append(line)
            self.event_log[:] = self.event_log[-8:]


# Default initial satellite configuration
DEFAULT_COMPONENTS = [
    "Star Tracker1",
    "Star Tracker2",
    "Reaction Wheel3",
    "AOC Electronics1",
    "AOC Electronics2",
]


def _render(state: DashboardState, script_name: str) -> Group:
    sat_table = Table(title="🛰  Satellite (AOC subsystem)", show_lines=False, expand=True)
    sat_table.add_column("Component", style="cyan", no_wrap=True)
    sat_table.add_column("Status", justify="center")
    with state.lock:
        components = dict(state.components)
        activity_feed = list(state.activity_feed)
        event_log = list(state.event_log)
        proc_status = state.procedure_status
    for name, status in sorted(components.items()):
        colour = {"ON": "bold green", "OFF": "bold red"}.get(status, "yellow")
        sat_table.add_row(name, Text(status, style=colour))

    proc_colour = {
        "executing": "bold yellow",
        "completed": "bold green",
        "failed": "bold red",
    }.get(proc_status, "white")
    proc_panel = Panel(
        Text(proc_status.upper(), style=proc_colour, justify="center"),
        title=f"Procedure: {script_name}",
        border_style=proc_colour,
    )

    activity_panel = Panel(
        Text("\n".join(activity_feed) or "(idle)", style="white"),
        title="📡 Activity feed",
        border_style="cyan",
    )

    event_panel = Panel(
        Text("\n".join(event_log) or "(no events)", style="magenta"),
        title="⚡ Events",
        border_style="magenta",
    )

    return Group(proc_panel, sat_table, activity_panel, event_panel)


def _wire_activities(state: DashboardState) -> None:
    """Replace default switch_on/off handlers so they update the dashboard."""

    def on_switch_on(act: Activity):
        target = act.target.split(" of ")[0].strip()
        state.set_component(target, "ON")
        state.push_activity(f"▶ Switch on  {act.target}")
        time.sleep(0.4)  # slow down so the user can see things happen

    def on_switch_off(act: Activity):
        target = act.target.split(" of ")[0].strip()
        state.set_component(target, "OFF")
        state.push_activity(f"⏹ Switch off {act.target}")
        time.sleep(0.4)

    for comp in DEFAULT_COMPONENTS:
        register_activity(Activity("Switch on", comp, on_switch_on))
        register_activity(Activity("Switch off", comp, on_switch_off))

    # Also register a couple of qualified targets used in the examples
    for comp in DEFAULT_COMPONENTS:
        register_activity(Activity("Switch on", f"{comp} of AOC of Satellite", on_switch_on))
        register_activity(Activity("Switch off", f"{comp} of AOC of Satellite", on_switch_off))


def _patch_procedure(state: DashboardState) -> None:
    """Monkey-patch Procedure lifecycle methods to broadcast events."""
    orig_start = runtime.Procedure.start
    orig_finish = runtime.Procedure.finish
    orig_raise = runtime.Procedure.raise_event
    orig_declare = runtime.Procedure.declare_event

    def start(self):
        state.procedure_status = "executing"
        orig_start(self)

    def finish(self):
        state.procedure_status = "completed"
        orig_finish(self)

    def raise_event(self, name):
        state.push_event(f"raised: {name}")
        orig_raise(self, name)

    def declare_event(self, event):
        state.push_event(f"declared: {event.name}")
        return orig_declare(self, event)

    runtime.Procedure.start = start
    runtime.Procedure.finish = finish
    runtime.Procedure.raise_event = raise_event
    runtime.Procedure.declare_event = declare_event


def run_demo(script_path: pathlib.Path | None = None) -> int:
    if script_path is None:
        # locate examples/05_full_bringup.pluto relative to this file or cwd
        candidates = [
            pathlib.Path.cwd() / "examples" / "05_full_bringup.pluto",
            pathlib.Path(__file__).resolve().parent.parent.parent / "examples" / "05_full_bringup.pluto",
        ]
        script_path = next((p for p in candidates if p.exists()), None)
        if script_path is None:
            print("No script supplied and examples/05_full_bringup.pluto not found.")
            return 2

    state = DashboardState()
    for c in DEFAULT_COMPONENTS:
        state.set_component(c, "OFF")
    _wire_activities(state)
    _patch_procedure(state)

    py_source = transpile(script_path.read_text(), module_doc=f"demo: {script_path.name}")
    ns: dict = {"__name__": "__demo__"}

    error: dict = {}

    def worker():
        try:
            exec(compile(py_source, str(script_path), "exec"), ns)
            ns["main"]()
        except Exception as e:  # noqa: BLE001
            state.procedure_status = "failed"
            error["e"] = e

    t = threading.Thread(target=worker, daemon=True)
    with Live(_render(state, script_path.name), refresh_per_second=10, screen=False) as live:
        t.start()
        while t.is_alive():
            live.update(_render(state, script_path.name))
            time.sleep(0.1)
        live.update(_render(state, script_path.name))

    if "e" in error:
        print(f"\nprocedure failed: {error['e']}")
        return 1
    return 0
