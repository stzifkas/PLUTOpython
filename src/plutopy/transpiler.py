"""PLUTO parse tree -> Python source code.

Emits a self-contained .py file that imports from `plutopy.runtime` and
defines a `main()` function. The transpiled module is human-readable.
"""
from __future__ import annotations

import pathlib
from typing import List

from lark import Token, Tree

from plutopy.parser import parse as parse_pluto

_RUNTIME_DIR = pathlib.Path(__file__).parent


INDENT = "    "


class TranspileError(Exception):
    pass


VALID_RUNTIMES = ("threaded", "async")
VALID_STYLES = ("functions", "class")


def transpile(
    source: str,
    *,
    module_doc: str | None = None,
    filename: str | None = None,
    runtime: str = "threaded",
    style: str = "functions",
    no_runtime: bool = False,
) -> str:
    """Transpile a PLUTO source string into runnable Python source.

    `runtime`:
      - "threaded" (default): emits against `plutopy.runtime`, threads-based.
      - "async": emits against `plutopy.async_runtime`, asyncio-based.

    `style`:
      - "functions" (default): emits `def main():` (or `async def main():`).
      - "class": emits a `TranspiledProcedure(Procedure)` subclass with
        declarations in `__init__` and main body in `run()`.

    `no_runtime`:
      - False (default): the output `import`s from `plutopy.runtime` (or
        `plutopy.async_runtime`).
      - True: inlines the runtime source so the output is a single
        self-contained .py file with no `plutopy` dependency.
    """
    if runtime not in VALID_RUNTIMES:
        raise TranspileError(f"unknown runtime: {runtime!r}; expected one of {VALID_RUNTIMES}")
    if style not in VALID_STYLES:
        raise TranspileError(f"unknown style: {style!r}; expected one of {VALID_STYLES}")
    tree = parse_pluto(source, filename=filename)
    emitter = _Emitter(runtime=runtime, style=style)
    body = emitter.emit_procedure(tree.children[0])
    header = _module_header(module_doc, runtime=runtime, no_runtime=no_runtime)
    return header + body + _module_footer(runtime=runtime, style=style)


_RUNTIME_PUBLIC_NAMES = (
    "Procedure", "Event",
    "switch_on", "switch_off",
    "initiate", "initiate_and_confirm", "initiate_and_confirm_step",
    "parallel_until_all", "parallel_until_one",
    "wait_for_event", "wait_until",
    "inform_user", "pluto_log",
)


def _module_header(doc: str | None, *, runtime: str, no_runtime: bool = False) -> str:
    doc_str = f'"""{doc}"""\n' if doc else '"""Transpiled from a PLUTO procedure."""\n'
    if no_runtime:
        runtime_file = "async_runtime.py" if runtime == "async" else "runtime.py"
        runtime_src = (_RUNTIME_DIR / runtime_file).read_text()
        return (
            doc_str
            + "# --- inlined plutopy runtime (--no-runtime) ---\n"
            + "# This file is self-contained. Edit at your own risk.\n"
            + runtime_src.rstrip()
            + "\n# --- end inlined runtime ---\n\n\n"
        )
    module = "plutopy.async_runtime" if runtime == "async" else "plutopy.runtime"
    import_list = ",\n    ".join(_RUNTIME_PUBLIC_NAMES)
    return (
        doc_str
        + f"from {module} import (\n    {import_list},\n)\n\n\n"
    )


def _module_footer(*, runtime: str, style: str = "functions") -> str:
    invocation = (
        "TranspiledProcedure().run()" if style == "class" else "main()"
    )
    if runtime == "async":
        return (
            "\n\nif __name__ == \"__main__\":\n"
            + INDENT + "import asyncio\n"
            + INDENT + f"asyncio.run({invocation})\n"
        )
    return "\n\nif __name__ == \"__main__\":\n" + INDENT + f"{invocation}\n"


def _join(lines: List[str], depth: int) -> str:
    pad = INDENT * depth
    return "\n".join(pad + ln if ln else ln for ln in lines)


def _text_of_name(node: Tree) -> str:
    """name node -> single string (words joined with spaces)."""
    return " ".join(str(t) for t in node.children)


def _text_of_qname(node: Tree) -> str:
    """qname node -> 'X of Y of Z' string."""
    return " of ".join(_text_of_name(n) for n in node.children)


def _text_of_description(node: Tree) -> str:
    return " ".join(str(t) for t in node.children)


class _Emitter:
    def __init__(self, *, runtime: str = "threaded", style: str = "functions") -> None:
        self._step_counter = 0
        self._var_counter = 0
        self._runtime = runtime
        self._is_async = runtime == "async"
        self._style = style
        self._is_class = style == "class"
        # `proc` for function style, `self` when the body is a method.
        self._receiver = "self" if self._is_class else "proc"

    # async helpers
    @property
    def _def(self) -> str:
        return "async def" if self._is_async else "def"

    @property
    def _await(self) -> str:
        return "await " if self._is_async else ""

    # ---- top-level ----
    def emit_procedure(self, proc: Tree) -> str:
        sections = proc.children  # already-flattened (rule is ?section)
        # categorize
        declare = main = preconds = watchdog = confirmation = None
        for s in sections:
            tag = s.data
            if tag == "declare_section":
                declare = s
            elif tag == "main_section":
                main = s
            elif tag == "preconditions_section":
                preconds = s
            elif tag == "watchdog_section":
                watchdog = s
            elif tag == "confirmation_section":
                confirmation = s

        if self._is_class:
            return self._emit_class(declare, watchdog, preconds, main, confirmation)
        return self._emit_functions(declare, watchdog, preconds, main, confirmation)

    def _emit_functions(self, declare, watchdog, preconds, main, confirmation) -> str:
        lines: List[str] = []
        lines.append(f"{self._def} main():")
        lines.append(f'{INDENT}proc = Procedure("transpiled")')
        lines.append(f"{INDENT}proc.start()")

        if declare is not None:
            lines.append(f"{INDENT}# --- declarations ---")
            for decl in declare.children:
                lines.append(INDENT + self._emit_event_decl(decl))

        if watchdog is not None:
            lines.append(f"{INDENT}# --- watchdog handlers ---")
            lines.extend(_indent_block(self._emit_watchdogs(watchdog), 1))

        if preconds is not None:
            lines.append(f"{INDENT}# --- preconditions ---")
            for pre in preconds.children:
                lines.extend(_indent_block(self._emit_statement(pre), 1))

        if main is not None:
            lines.append(f"{INDENT}# --- main ---")
            for stmt in main.children:
                lines.extend(_indent_block(self._emit_statement(stmt), 1))

        if confirmation is not None:
            lines.append(f"{INDENT}# --- confirmation ---")
            for stmt in confirmation.children:
                lines.extend(_indent_block(self._emit_statement(stmt), 1))

        lines.append(f"{INDENT}proc.finish()")
        return "\n".join(lines) + "\n"

    def _emit_class(self, declare, watchdog, preconds, main, confirmation) -> str:
        lines: List[str] = []
        lines.append("class TranspiledProcedure(Procedure):")
        lines.append(f"{INDENT}def __init__(self):")
        lines.append(f'{INDENT}{INDENT}super().__init__("transpiled")')

        if declare is not None:
            lines.append(f"{INDENT}{INDENT}# --- declarations ---")
            for decl in declare.children:
                lines.append(f"{INDENT}{INDENT}{self._emit_event_decl(decl)}")

        if watchdog is not None:
            lines.append(f"{INDENT}{INDENT}# --- watchdog handlers ---")
            lines.extend(_indent_block(self._emit_watchdogs(watchdog), 2))

        lines.append("")
        lines.append(f"{INDENT}{self._def} run(self):")
        lines.append(f"{INDENT}{INDENT}self.start()")

        if preconds is not None:
            lines.append(f"{INDENT}{INDENT}# --- preconditions ---")
            for pre in preconds.children:
                lines.extend(_indent_block(self._emit_statement(pre), 2))

        if main is not None:
            lines.append(f"{INDENT}{INDENT}# --- main ---")
            for stmt in main.children:
                lines.extend(_indent_block(self._emit_statement(stmt), 2))

        if confirmation is not None:
            lines.append(f"{INDENT}{INDENT}# --- confirmation ---")
            for stmt in confirmation.children:
                lines.extend(_indent_block(self._emit_statement(stmt), 2))

        lines.append(f"{INDENT}{INDENT}self.finish()")
        return "\n".join(lines) + "\n"

    def _emit_watchdogs(self, watchdog: Tree) -> List[str]:
        """Emit handler definitions and registrations. Returns lines at depth 0."""
        out: List[str] = []
        for handler in watchdog.children:
            ev_name = _text_of_name(handler.children[0])
            self._step_counter += 1
            fn_name = f"_watchdog_{self._step_counter}"
            out.append(f"{self._def} {fn_name}():")
            body = handler.children[1:]
            if not body:
                out.append(f"{INDENT}pass")
            else:
                for s in body:
                    out.extend(_indent_block(self._emit_statement(s), 1))
            out.append(f'{self._receiver}.register_watchdog("{ev_name}", {fn_name})')
        return out

    def _emit_event_decl(self, decl: Tree) -> str:
        name = _text_of_name(decl.children[0])
        if len(decl.children) > 1:
            desc = _text_of_description(decl.children[1])
            return f'{self._receiver}.declare_event(Event("{name}", description={desc!r}))'
        return f'{self._receiver}.declare_event(Event("{name}"))'

    # ---- statements: each returns a list of lines (no leading indent) ----
    def _emit_statement(self, stmt: Tree) -> List[str]:
        method = getattr(self, f"_stmt_{stmt.data}", None)
        if method is None:
            raise TranspileError(f"unsupported statement: {stmt.data}")
        return method(stmt)

    def _stmt_initiate_stmt(self, node: Tree) -> List[str]:
        call = self._emit_activity_call(node.children[0])
        return [f"initiate({self._receiver}, {call})"]

    def _stmt_initiate_confirm_stmt(self, node: Tree) -> List[str]:
        call = self._emit_activity_call(node.children[0])
        return [f"{self._await}initiate_and_confirm({self._receiver}, {call})"]

    def _stmt_initiate_confirm_step(self, node: Tree) -> List[str]:
        step_name = _text_of_name(node.children[0])
        body_stmts = node.children[1:]
        self._step_counter += 1
        fn_name = f"_step_{self._step_counter}"
        lines = [f"{self._def} {fn_name}():"]
        if not body_stmts:
            lines.append(f"{INDENT}pass")
        else:
            for s in body_stmts:
                lines.extend(_indent_block(self._emit_statement(s), 1))
        lines.append(f'{self._await}initiate_and_confirm_step("{step_name}", {fn_name})')
        return lines

    def _stmt_parallel_all_stmt(self, node: Tree) -> List[str]:
        return self._emit_parallel(node, "parallel_until_all")

    def _stmt_parallel_one_stmt(self, node: Tree) -> List[str]:
        return self._emit_parallel(node, "parallel_until_one")

    def _emit_parallel(self, node: Tree, fn: str) -> List[str]:
        lines: List[str] = []
        branch_names: List[str] = []
        for branch in node.children:
            self._step_counter += 1
            branch_fn = f"_branch_{self._step_counter}"
            lines.append(f"{self._def} {branch_fn}():")
            inner = self._emit_statement(branch)
            for ln in _indent_block(inner, 1):
                lines.append(ln)
            branch_names.append(branch_fn)
        lines.append(f"{self._await}{fn}([{', '.join(branch_names)}])")
        return lines

    def _stmt_context_stmt(self, node: Tree) -> List[str]:
        target = _text_of_qname(node.children[0])
        body = node.children[1:]
        # Lightweight: emit comment + body
        lines = [f"# context: {target}"]
        for s in body:
            lines.extend(self._emit_statement(s))
        return lines

    def _stmt_if_stmt(self, node: Tree) -> List[str]:
        expr = self._emit_expression(node.children[0])
        then_node = node.children[1]  # if_then
        else_node = node.children[2] if len(node.children) > 2 else None  # if_else
        lines = [f"if {expr}:"]
        for s in then_node.children:
            lines.extend(_indent_block(self._emit_statement(s), 1))
        if else_node is not None:
            lines.append("else:")
            for s in else_node.children:
                lines.extend(_indent_block(self._emit_statement(s), 1))
        return lines

    def _stmt_case_stmt(self, node: Tree) -> List[str]:
        expr = self._emit_expression(node.children[0])
        var = "_case_expr"
        lines = [f"{var} = {expr}"]
        first = True
        otherwise_node = None
        for child in node.children[1:]:
            if child.data == "case_otherwise":
                otherwise_node = child
                continue
            arm_expr = self._emit_expression(child.children[0])
            stmts = child.children[1:]
            keyword = "if" if first else "elif"
            first = False
            lines.append(f"{keyword} {var} == {arm_expr}:")
            if not stmts:
                lines.append(f"{INDENT}pass")
            for s in stmts:
                lines.extend(_indent_block(self._emit_statement(s), 1))
        if otherwise_node is not None:
            lines.append("else:")
            for s in otherwise_node.children:
                lines.extend(_indent_block(self._emit_statement(s), 1))
        return lines

    def _stmt_while_stmt(self, node: Tree) -> List[str]:
        expr = self._emit_expression(node.children[0])
        timeout = self._extract_timeout(node)
        body = [c for c in node.children[1:] if not (isinstance(c, Tree) and c.data == "timeout_clause")]
        if timeout:
            # convert `while EXPR do BODY with timeout T` into a time-limited while loop
            lines = [
                f"_deadline = __import__('time').time() + {timeout}",
                f"while ({expr}) and __import__('time').time() < _deadline:",
            ]
        else:
            lines = [f"while {expr}:"]
        if not body:
            lines.append(f"{INDENT}pass")
        else:
            for s in body:
                lines.extend(_indent_block(self._emit_statement(s), 1))
        return lines

    def _stmt_for_stmt(self, node: Tree) -> List[str]:
        var_name = _text_of_name(node.children[0]).replace(" ", "_")
        # children: name, expr, expr, (expr by)?, statements...
        rest = node.children[1:]
        start_expr = self._emit_expression(rest[0])
        end_expr = self._emit_expression(rest[1])
        # remaining children: optionally a 'by' expr (Tree), then statements
        idx = 2
        step = "1"
        if idx < len(rest) and _is_expression(rest[idx]):
            step = self._emit_expression(rest[idx])
            idx += 1
        body = rest[idx:]
        py_var = _py_ident(var_name)
        lines = [f"for {py_var} in range(int({start_expr}), int({end_expr}) + 1, int({step})):"]
        if not body:
            lines.append(f"{INDENT}pass")
        else:
            for s in body:
                lines.extend(_indent_block(self._emit_statement(s), 1))
        return lines

    def _stmt_repeat_stmt(self, node: Tree) -> List[str]:
        timeout = self._extract_timeout(node)
        non_timeout = [c for c in node.children if not (isinstance(c, Tree) and c.data == "timeout_clause")]
        body = non_timeout[:-1]
        cond = self._emit_expression(non_timeout[-1])
        lines = []
        if timeout:
            lines.append(f"_deadline = __import__('time').time() + {timeout}")
        lines.append("while True:")
        if not body:
            lines.append(f"{INDENT}pass")
        else:
            for s in body:
                lines.extend(_indent_block(self._emit_statement(s), 1))
        lines.append(f"{INDENT}if {cond}:")
        lines.append(f"{INDENT}{INDENT}break")
        if timeout:
            lines.append(f"{INDENT}if __import__('time').time() >= _deadline:")
            lines.append(f"{INDENT}{INDENT}break")
        return lines

    def _stmt_wait_for_event(self, node: Tree) -> List[str]:
        ev = _text_of_name(node.children[0])
        timeout = self._extract_timeout(node)
        timeout_arg = f", timeout={timeout}" if timeout else ""
        return [f'{self._await}wait_for_event({self._receiver}, "{ev}"{timeout_arg})']

    def _stmt_wait_until_expr(self, node: Tree) -> List[str]:
        expr = self._emit_expression(node.children[0])
        timeout = self._extract_timeout(node)
        timeout_arg = f", timeout={timeout}" if timeout else ""
        return [f"{self._await}wait_until(lambda: {expr}{timeout_arg})"]

    def _extract_timeout(self, node: Tree) -> str | None:
        for child in node.children:
            if isinstance(child, Tree) and child.data == "timeout_clause":
                return self._emit_expression(child.children[0])
        return None

    def _stmt_assign_stmt(self, node: Tree) -> List[str]:
        var = _py_ident(_text_of_name(node.children[0]))
        expr = self._emit_expression(node.children[1])
        return [f"{var} = {expr}", f'{self._receiver}.variables["{var}"] = {var}']

    def _stmt_log_stmt(self, node: Tree) -> List[str]:
        expr = self._emit_expression(node.children[0])
        return [f"pluto_log({expr})"]

    def _stmt_inform_stmt(self, node: Tree) -> List[str]:
        expr = self._emit_expression(node.children[0])
        return [f"inform_user({expr})"]

    def _stmt_raise_stmt(self, node: Tree) -> List[str]:
        ev = _text_of_name(node.children[0])
        return [f'{self._await}{self._receiver}.raise_event("{ev}")']

    # ---- activity calls ----
    def _emit_activity_call(self, node: Tree) -> str:
        if node.data == "switch_on":
            target = _text_of_qname(node.children[0])
            return f'switch_on("{target}")'
        if node.data == "switch_off":
            target = _text_of_qname(node.children[0])
            return f'switch_off("{target}")'
        raise TranspileError(f"unsupported activity: {node.data}")

    # ---- expressions ----
    def _emit_expression(self, node) -> str:
        if isinstance(node, Token):
            return _emit_token(node)
        d = node.data
        if d == "num_lit":
            return str(node.children[0])
        if d == "str_lit":
            return str(node.children[0])
        if d == "prop_req":
            return self._emit_property_request(node.children[0])
        if d == "var_ref":
            qn = _text_of_qname(node.children[0])
            return _ref_to_python(qn, self._receiver)
        if d == "not_op":
            return f"(not {self._emit_expression(node.children[0])})"
        if d == "or_expr":
            return "(" + " or ".join(self._emit_expression(c) for c in node.children) + ")"
        if d == "and_expr":
            return "(" + " and ".join(self._emit_expression(c) for c in node.children) + ")"
        if d == "comparison":
            # children: arith, CMP_OP, arith
            left = self._emit_expression(node.children[0])
            op = _map_cmp_op(str(node.children[1]))
            right = self._emit_expression(node.children[2])
            return f"({left} {op} {right})"
        if d == "arith":
            return _emit_binop_chain(node.children, self._emit_expression)
        if d == "term":
            return _emit_binop_chain(node.children, self._emit_expression)
        if d == "qname":
            qn = _text_of_qname(node)
            return _ref_to_python(qn, self._receiver)
        raise TranspileError(f"unsupported expression: {d}")

    def _emit_property_request(self, node) -> str:
        """Emit code to get an activity property.
        
        Translates: execution_status of Star Tracker1
        To: proc.get_property("Star Tracker1", "execution_status")
        """
        # node.children[0] is property_request tree
        # tree has: property_name, "of", qname
        prop_req = node
        prop_name_node = prop_req.children[0]
        qname_node = prop_req.children[1]
        
        # Extract property name (e.g., "execution_status")
        prop_name = _text_of_qname(prop_name_node)
        
        # Extract activity name (e.g., "Star Tracker1")
        activity_name = _text_of_qname(qname_node)
        
        return f'{self._receiver}.get_property("{activity_name}", "{prop_name}")'


def _emit_binop_chain(children, emit) -> str:
    out = emit(children[0])
    i = 1
    while i < len(children):
        op = str(children[i])
        right = emit(children[i + 1])
        out = f"({out} {op} {right})"
        i += 2
    return out


def _emit_token(tok: Token) -> str:
    if tok.type == "NUMBER":
        return str(tok)
    if tok.type == "ESCAPED_STRING":
        return str(tok)
    if tok.type == "WORD":
        return _py_ident(str(tok))
    return str(tok)


def _map_cmp_op(op: str) -> str:
    return {"=": "==", "<>": "!="}.get(op, op)


def _is_expression(node) -> bool:
    if isinstance(node, Token):
        return False
    return node.data in {
        "or_expr", "and_expr", "not_op", "comparison",
        "arith", "term", "num_lit", "str_lit", "var_ref", "qname", "prop_req",
    }


def _ref_to_python(qn: str, receiver: str) -> str:
    """Resolve a PLUTO qualified reference at runtime via the procedure scope."""
    if " of " not in qn:
        ident = _py_ident(qn)
        return f'{receiver}.variables.get("{ident}", {ident!r})'
    return f'{receiver}.variables.get({qn!r}, {qn!r})'


def _py_ident(name: str) -> str:
    safe = name.replace(" ", "_").replace("-", "_")
    if not safe or not (safe[0].isalpha() or safe[0] == "_"):
        safe = "_" + safe
    return safe


def _indent_block(lines: List[str], depth: int) -> List[str]:
    pad = INDENT * depth
    return [pad + ln for ln in lines]
