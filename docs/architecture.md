# Architecture

```text
       script.pluto
           │
           ▼
  ┌────────────────────┐
  │ plutopy.parser     │  Lark Earley parser, grammar.lark
  └────────────────────┘
           │ Tree
           ▼
  ┌────────────────────┐
  │ plutopy.transpiler │  Tree walker, emits readable Python source
  └────────────────────┘
           │ Python source string
           ▼
  ┌────────────────────┐
  │ plutopy.runtime    │  Procedure, Event, parallel_*, switch_on/off, …
  └────────────────────┘
```

## Modules

### `plutopy.grammar` (`grammar.lark`)

The grammar file is parsed with [Lark](https://github.com/lark-parser/lark)'s Earley algorithm.
Earley handles the PLUTO ambiguity around multi-word identifiers (`Star Tracker2`, `Reaction Wheel3 of AOC of Satellite`). The `WORD` terminal is declared with priority `-10` so string-literal keywords always win the tokenisation race.

### `plutopy.parser`

A thin wrapper around the cached Lark parser. Adds friendly error wrapping: parse failures raise `PlutoParseError` with source line/column, a caret marker, and a structural hint.

### `plutopy.transpiler`

A `_Emitter` class with one `_stmt_<rulename>` method per statement kind. Every method returns a list of Python source lines; the caller indents them as it splices them into the surrounding block. The output is plain Python — no eval-of-strings, no DSL trickery.

### `plutopy.runtime`

The standard library the transpiled output calls into:

- `Procedure`: lifecycle, event registry, watchdog handlers, variable scope.
- `Event`: declared events with `raise_()`.
- `Activity` + `register_activity`: pluggable activity handlers. Default behaviour prints a trace.
- `switch_on(target)` / `switch_off(target)`: helpers that look up a registered activity and invoke it.
- `initiate(call)` / `initiate_and_confirm(call)`: fire-and-forget vs synchronous.
- `parallel_until_all([…])` / `parallel_until_one([…])`: thread-based concurrency.
- `wait_for_event(proc, name, timeout=None)` / `wait_until(predicate, timeout=None)`.
- `inform_user(...)` / `pluto_log(...)`.

### `plutopy.cli`

`argparse` front-end exposing `parse / compile / run / demo` subcommands. `-v` enables Python logging at INFO level so you can watch the procedure lifecycle.

### `plutopy.demo`

Rich-based live dashboard. Registers custom activity handlers that mutate a `DashboardState`, monkey-patches `Procedure.start/finish/raise_event/declare_event` to broadcast lifecycle events, and runs the procedure in a thread while the main thread refreshes a `rich.Live` group.

### `plutopy.pygments_lexer`

A `RegexLexer` registered as a Pygments entry point named `pluto`, so any tool that uses Pygments (mkdocs, GitHub, Jupyter, etc.) can highlight `.pluto` code.
