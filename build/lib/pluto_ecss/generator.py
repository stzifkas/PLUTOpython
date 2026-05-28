"""Generate a PLUTO procedure from a YAML / dict specification.

The spec is a thin, declarative mirror of the PLUTO grammar that makes
it ergonomic to scaffold procedures programmatically. After generation
the produced source is parsed once to validate it; a parse failure
means the spec or the generator is buggy.

Example spec (YAML)::

    procedure: BringUp
    declare:
      - event: ready
        description: System online
      - event: boom
    watchdog:
      boom:
        - inform_user: "handling boom"
        - switch_off: Reaction Wheel3
    main:
      - log: "starting up"
      - assign: { var: counter, value: 0 }
      - while:
          condition: "counter < 3"
          body:
            - assign: { var: counter, value: "counter + 1" }
      - parallel:
          mode: all
          branches:
            - step:
                name: BRING UP TRACKER
                body:
                  - initiate_and_confirm:
                      switch_on: Star Tracker1
            - step:
                name: BRING UP WHEEL
                body:
                  - initiate_and_confirm:
                      switch_on: Reaction Wheel3 of AOC of Satellite
      - inform_user: "bring up complete"
"""
from __future__ import annotations

import pathlib
from typing import Any, Dict, List, Union

from pluto_ecss.parser import parse as parse_pluto


INDENT = "  "


class GeneratorError(ValueError):
    pass


def generate_from_spec(spec: Dict[str, Any]) -> str:
    """Turn a dict spec into a PLUTO source string, validated by re-parsing."""
    if not isinstance(spec, dict):
        raise GeneratorError("spec must be a dict / YAML mapping")
    lines: List[str] = ["procedure"]
    if "declare" in spec:
        lines.extend(_emit_declare(spec["declare"], 1))
    if "watchdog" in spec:
        lines.extend(_emit_watchdog(spec["watchdog"], 1))
    if "preconditions" in spec:
        lines.extend(_emit_block("preconditions", "end preconditions", spec["preconditions"], 1))
    if "main" not in spec:
        raise GeneratorError("spec is missing required 'main' section")
    lines.extend(_emit_block("main", "end main", spec["main"], 1))
    if "confirmation" in spec:
        lines.extend(_emit_block("confirmation", "end confirmation", spec["confirmation"], 1))
    lines.append("end procedure")
    out = "\n".join(lines) + "\n"
    # Validate by re-parsing; surfaces generator bugs early.
    parse_pluto(out)
    return out


def generate_from_yaml(yaml_text: str) -> str:
    import yaml  # imported lazily so the runtime dependency is opt-in
    spec = yaml.safe_load(yaml_text)
    return generate_from_spec(spec)


def generate_from_file(path: pathlib.Path) -> str:
    return generate_from_yaml(path.read_text())


# ---- emitters ----
def _emit_declare(items: List[Any], depth: int) -> List[str]:
    pad = INDENT * depth
    inner = INDENT * (depth + 1)
    lines = [f"{pad}declare"]
    decls = [_emit_event_decl(item) for item in items]
    if len(decls) == 1:
        lines.append(f"{inner}{decls[0]}")
    else:
        joined = (",\n" + inner).join(decls)
        lines.append(f"{inner}{joined}")
    lines.append(f"{pad}end declare")
    return lines


def _emit_event_decl(item: Dict[str, Any]) -> str:
    if "event" not in item:
        raise GeneratorError(f"declare entry must have 'event' key: {item}")
    name = item["event"]
    desc = item.get("description")
    if desc:
        return f"event {name} described by {desc}"
    return f"event {name}"


def _emit_watchdog(spec: Dict[str, List[Any]], depth: int) -> List[str]:
    pad = INDENT * depth
    inner = INDENT * (depth + 1)
    lines = [f"{pad}watchdog"]
    if not isinstance(spec, dict):
        raise GeneratorError("'watchdog' must map event-name to a list of statements")
    for event_name, body in spec.items():
        lines.append(f"{inner}on {event_name} do")
        for stmt in body:
            lines.extend(_emit_statement(stmt, depth + 2))
        lines.append(f"{inner}end on")
    lines.append(f"{pad}end watchdog")
    return lines


def _emit_block(opener: str, closer: str, statements: List[Any], depth: int) -> List[str]:
    pad = INDENT * depth
    lines = [f"{pad}{opener}"]
    for s in statements:
        lines.extend(_emit_statement(s, depth + 1))
    lines.append(f"{pad}{closer}")
    return lines


# Map of high-level keys to their emitters.
def _emit_statement(stmt: Any, depth: int) -> List[str]:
    pad = INDENT * depth
    if isinstance(stmt, str):
        # bare strings are interpreted as raw PLUTO statements (escape hatch)
        return [f"{pad}{stmt}"]
    if not isinstance(stmt, dict) or len(stmt) != 1:
        raise GeneratorError(
            f"statement must be a single-key dict (or a raw string); got: {stmt!r}"
        )
    (kind, value), = stmt.items()
    emitter = _STATEMENT_EMITTERS.get(kind)
    if emitter is None:
        raise GeneratorError(f"unknown statement kind: {kind!r}")
    return emitter(value, depth)


def _stmt_log(value: Any, depth: int) -> List[str]:
    pad = INDENT * depth
    return [f'{pad}log "{value}"']


def _stmt_inform(value: Any, depth: int) -> List[str]:
    pad = INDENT * depth
    return [f'{pad}inform user "{value}"']


def _stmt_raise(value: Any, depth: int) -> List[str]:
    pad = INDENT * depth
    return [f"{pad}raise event {value}"]


def _stmt_assign(value: Dict[str, Any], depth: int) -> List[str]:
    pad = INDENT * depth
    var = value["var"]
    expr = value["value"]
    return [f"{pad}{var} := {expr}"]


def _stmt_wait_for(value: Any, depth: int) -> List[str]:
    pad = INDENT * depth
    if isinstance(value, str):
        return [f"{pad}wait for event {value}"]
    ev = value["event"]
    timeout = value.get("timeout")
    suffix = f" with timeout {timeout}" if timeout is not None else ""
    return [f"{pad}wait for event {ev}{suffix}"]


def _stmt_wait_until(value: Any, depth: int) -> List[str]:
    pad = INDENT * depth
    if isinstance(value, str):
        return [f"{pad}wait until {value}"]
    cond = value["condition"]
    timeout = value.get("timeout")
    suffix = f" with timeout {timeout}" if timeout is not None else ""
    return [f"{pad}wait until {cond}{suffix}"]


def _stmt_initiate(value: Dict[str, Any], depth: int) -> List[str]:
    return [f"{INDENT * depth}initiate {_emit_activity_call(value)}"]


def _stmt_initiate_and_confirm(value: Dict[str, Any], depth: int) -> List[str]:
    return [f"{INDENT * depth}initiate and confirm {_emit_activity_call(value)}"]


def _stmt_if(value: Dict[str, Any], depth: int) -> List[str]:
    pad = INDENT * depth
    cond = value["condition"]
    then_body = value.get("then", [])
    else_body = value.get("else")
    lines = [f"{pad}if {cond} then"]
    for s in then_body:
        lines.extend(_emit_statement(s, depth + 1))
    if else_body is not None:
        lines.append(f"{pad}else")
        for s in else_body:
            lines.extend(_emit_statement(s, depth + 1))
    lines.append(f"{pad}end if")
    return lines


def _stmt_case(value: Dict[str, Any], depth: int) -> List[str]:
    pad = INDENT * depth
    inner = INDENT * (depth + 1)
    expr = value["expr"]
    arms = value.get("arms", [])
    otherwise = value.get("otherwise")
    lines = [f"{pad}case {expr} of"]
    for arm in arms:
        lines.append(f"{inner}when {arm['when']} do")
        for s in arm.get("do", []):
            lines.extend(_emit_statement(s, depth + 2))
    if otherwise is not None:
        lines.append(f"{inner}otherwise")
        for s in otherwise:
            lines.extend(_emit_statement(s, depth + 2))
    lines.append(f"{pad}end case")
    return lines


def _stmt_while(value: Dict[str, Any], depth: int) -> List[str]:
    pad = INDENT * depth
    cond = value["condition"]
    body = value.get("body", [])
    timeout = value.get("timeout")
    lines = [f"{pad}while {cond} do"]
    for s in body:
        lines.extend(_emit_statement(s, depth + 1))
    if timeout is not None:
        lines.append(f"{pad}with timeout {timeout}")
    lines.append(f"{pad}end while")
    return lines


def _stmt_for(value: Dict[str, Any], depth: int) -> List[str]:
    pad = INDENT * depth
    var = value["var"]
    start_expr = value["from"]
    end_expr = value["to"]
    by = value.get("by")
    body = value.get("body", [])
    by_part = f" by {by}" if by is not None else ""
    lines = [f"{pad}for {var} := {start_expr} to {end_expr}{by_part} do"]
    for s in body:
        lines.extend(_emit_statement(s, depth + 1))
    lines.append(f"{pad}end for")
    return lines


def _stmt_repeat(value: Dict[str, Any], depth: int) -> List[str]:
    pad = INDENT * depth
    body = value.get("body", [])
    until = value["until"]
    timeout = value.get("timeout")
    lines = [f"{pad}repeat"]
    for s in body:
        lines.extend(_emit_statement(s, depth + 1))
    lines.append(f"{pad}until {until}")
    if timeout is not None:
        lines.append(f"{pad}with timeout {timeout}")
    lines.append(f"{pad}end repeat")
    return lines


def _stmt_parallel(value: Dict[str, Any], depth: int) -> List[str]:
    pad = INDENT * depth
    mode = value.get("mode", "all")
    if mode == "all":
        opener = "in parallel until all complete"
    elif mode == "one":
        opener = "in parallel until one completes"
    else:
        raise GeneratorError(f"parallel.mode must be 'all' or 'one', got {mode!r}")
    branches = value.get("branches", [])
    lines = [f"{pad}{opener}"]
    for branch in branches:
        lines.extend(_emit_statement(branch, depth + 1))
    lines.append(f"{pad}end parallel")
    return lines


def _stmt_step(value: Dict[str, Any], depth: int) -> List[str]:
    pad = INDENT * depth
    inner = INDENT * (depth + 1)
    name = value["name"]
    body = value.get("body", [])
    lines = [f"{pad}initiate and confirm step {name}", f"{inner}main"]
    for s in body:
        lines.extend(_emit_statement(s, depth + 2))
    lines.append(f"{inner}end main")
    lines.append(f"{pad}end step")
    return lines


# Shortcut: top-level `switch_on: Target` / `switch_off: Target` map to a
# fire-and-forget `initiate Switch on Target`. This keeps simple specs short.
def _stmt_switch_on(value: Any, depth: int) -> List[str]:
    return _stmt_initiate({"switch_on": value}, depth)


def _stmt_switch_off(value: Any, depth: int) -> List[str]:
    return _stmt_initiate({"switch_off": value}, depth)


_STATEMENT_EMITTERS = {
    "log": _stmt_log,
    "inform_user": _stmt_inform,
    "raise": _stmt_raise,
    "assign": _stmt_assign,
    "wait_for": _stmt_wait_for,
    "wait_until": _stmt_wait_until,
    "initiate": _stmt_initiate,
    "initiate_and_confirm": _stmt_initiate_and_confirm,
    "if": _stmt_if,
    "case": _stmt_case,
    "while": _stmt_while,
    "for": _stmt_for,
    "repeat": _stmt_repeat,
    "parallel": _stmt_parallel,
    "step": _stmt_step,
    "switch_on": _stmt_switch_on,
    "switch_off": _stmt_switch_off,
}


def _emit_activity_call(value: Union[str, Dict[str, Any]]) -> str:
    """Turn an activity-call spec into a PLUTO call fragment."""
    if isinstance(value, str):
        # raw passthrough, e.g. "Switch on Reaction Wheel3 of AOC of Satellite"
        return value
    if not isinstance(value, dict) or len(value) != 1:
        raise GeneratorError(f"activity call must be a single-key dict; got {value!r}")
    (kind, target), = value.items()
    if kind == "switch_on":
        return f"Switch on {target}"
    if kind == "switch_off":
        return f"Switch off {target}"
    raise GeneratorError(f"unknown activity kind: {kind!r}")
