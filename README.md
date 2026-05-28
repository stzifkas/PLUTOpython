# pluto-ecss

> A PLUTO ([ECSS-E-ST-70-32C](https://ecss.nl/standard/ecss-e-st-70-32c-space-engineering-test-and-operations-procedure-language/)) to Python transpiler and runtime.
> Take a spacecraft operations procedure written in PLUTO, get back a runnable Python program.

📚 **[Read the docs](https://stzifkas.github.io/pluto-ecss/)** · 🎮 **[Web playground](https://stzifkas.github.io/pluto-ecss/playground/)** · 🛰 **[TUI demo](#the-tui-demo)** · 🧭 **[Finish-Up-A-Thon arc](#the-finish-up-a-thon-arc)**

PLUTO is the procedure language standardised by ECSS for spacecraft monitoring and command. It's the DSL operators write when they need to bring up a star tracker, run a parallel safety sequence, or react to an on-board event. `pluto-ecss` parses that DSL with [Lark](https://github.com/lark-parser/lark) and emits a readable Python module that calls into a small runtime library.

```pluto
procedure
    declare
      event chaos described by Total disaster, event chaos2
    end declare
    main
      initiate Switch on Star Tracker2
      in parallel until all complete
        initiate and confirm step SWITCH ON SECOND STAR TRACKER
          main
            initiate and confirm Switch on Reaction Wheel3 of AOC of Satellite;
          end main
        end step;
        initiate and confirm step SWITCH ON FIRST STAR TRACKER
          main
            initiate and confirm Switch on Star Tracker1;
          end main
        end step;
      end parallel
    end main
end procedure
```

```bash
$ pluto-ecss run examples/01_original.pluto
[ACTIVITY] Switch on Star Tracker2
[ACTIVITY] Switch on Reaction Wheel3 of AOC of Satellite
[ACTIVITY] Switch on Star Tracker1
```

---

## The Finish-Up-A-Thon arc

This repo started life in **2019** as a Google Summer of Code work product: a sample parser for the PLUTO DSL that built a parse tree out of a single hard-coded script and "ran" it by walking the tree. It was a proof of concept that never grew past one example file. It's been dormant for nearly seven years.

For the [GitHub Finish-Up-A-Thon](https://dev.to/github) (May–June 2026), it's been revived as an actual, installable PLUTO transpiler.

### Before — the GSoC snapshot (tag [`v0.1-gsoc-2019`](../../tree/v0.1-gsoc-2019), branch [`legacy/gsoc-2019`](../../tree/legacy/gsoc-2019))

| Aspect | State in 2019 |
| --- | --- |
| Grammar | ~30 lines, covered `initiate`, `initiate and confirm (step)`, `parallel until all`, `switch on`, event declarations |
| Runtime | Tree-walking interpreter inside the parser file. Threaded but missing many features. |
| Codebase | Two `.py` files, mixed concerns, several syntax-level bugs (typos like `setExecutionSatus`, missing `import types`, `super.__init__` with no parens) |
| Tests | None |
| Packaging | None — `python pluto_ecss.py` only |
| CLI | None — entry point is hard-coded to `script.pluto` |
| Output | Only side effects from a tree walk; no Python emission |
| Docs | README sketched the design but didn't describe how to actually use it |

You can still see all of this — just check out the `legacy/gsoc-2019` branch.

### After — what's in `main` now

| Aspect | State in 2026 |
| --- | --- |
| Grammar | Expanded to cover `if/then`, `while`, `for`, `repeat … until`, `wait for event`, `wait until`, `:=` assignment, `raise event`, `log`, `inform user`, `in parallel until one completes`, expressions with arithmetic / comparison / boolean operators, plus everything from 2019 |
| Pipeline | **Transpiler**: PLUTO → parse tree → Python source. The generated `.py` imports a runtime library and is independently runnable / debuggable / shippable. |
| Runtime | Small standalone module (`pluto_ecss.runtime`) with `Procedure`, `Event`, `Activity`, `parallel_until_all`, `wait_for_event`, etc. Activities are pluggable; the default handler prints a trace. |
| Package | `pip install -e .`, proper `src/` layout, packaged grammar file |
| CLI | `pluto-ecss parse|compile|run` with `-v` for runtime logging |
| Tests | 24 pytest cases covering the parser, transpiler output validity, runtime behaviour, and end-to-end CLI |
| CI | GitHub Actions matrix on Python 3.9 / 3.11 / 3.13 |
| Demo | `pluto-ecss demo` — live Rich-based TUI of a fake satellite reacting to PLUTO activities in real time |
| Error messages | Friendly parse errors with file:line:column, source caret, and structural hints (vs. raw Lark exceptions in 2019) |
| Highlighter | Pygments lexer for `.pluto`, registered as an entry point, picked up automatically by mkdocs / Jupyter / GitHub / Sphinx |
| Docs | mkdocs site at `docs/`, deployed on every push to `main` |
| Formatter | `pluto-ecss fmt` — canonical pretty-printer (idempotent, `--check` mode for CI) |
| Generator | `pluto-ecss gen spec.yaml` — scaffold a PLUTO procedure from a declarative YAML spec |
| Playground | Pyodide-powered browser playground that compiles and runs PLUTO entirely client-side |

> This revival was AI-assisted: I used an AI coding assistant to accelerate the rebuild, particularly for designing the Lark grammar's keyword-priority resolution (the original grammar had brittle negative-lookahead patterns that broke on common keywords), the transpiler's parse-tree-walker, and the runtime's threading primitives. The architectural decisions, the choice to write a transpiler instead of an interpreter, and the test design are mine; the assistant accelerated the typing and surfaced an Earley-lexer-priority bug that would have cost me a couple of hours otherwise.

---

## Install

```bash
git clone https://github.com/stzifkas/pluto-ecss
cd pluto-ecss
pip install -e .          # adds the `pluto-ecss` console script
pip install -e ".[dev]"   # plus pytest
```

Python 3.9+ is required. The only runtime dependency is [`lark`](https://pypi.org/project/lark/).

## Use

```bash
# 1. See the parse tree
pluto-ecss parse examples/03_loops.pluto

# 2. Transpile to Python (writes to stdout, or use -o)
pluto-ecss compile examples/01_original.pluto -o /tmp/demo.py

# 3. Transpile and execute in one shot
pluto-ecss run examples/01_original.pluto
pluto-ecss -v run examples/04_events.pluto    # with runtime lifecycle logs

# 4. Live TUI dashboard (requires `pip install pluto-ecss[tui]`)
pluto-ecss demo examples/05_full_bringup.pluto
```

### Friendly parse errors

```text
$ pluto-ecss parse bad.pluto
pluto-ecss: parse error
at bad.pluto:7:7: cannot start a token with 'l'; expected 'and', 'or', 'then', or one of 2 more

     7 |       log "hi"
       |       ^

hint: an if statement looks like: if EXPR then STATEMENTS end if
```

### The TUI demo

`pluto-ecss demo` watches a fake satellite light up as the procedure runs:

```
╭──────────────────────── Procedure: 05_full_bringup.pluto ────────────────────────╮
│                                  EXECUTING                                       │
╰──────────────────────────────────────────────────────────────────────────────────╯
                              🛰  Satellite (AOC subsystem)
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component             ┃        Status         ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ AOC Electronics1      │          OFF          │
│ Reaction Wheel3       │          ON           │
│ Star Tracker1         │          ON           │
│ Star Tracker2         │          OFF          │
└───────────────────────┴───────────────────────┘
╭────────── 📡 Activity feed ──────────╮      ╭───────── ⚡ Events ─────────╮
│ ▶ Switch on Reaction Wheel3 of AOC … │      │ declared: boom              │
│ ▶ Switch on Star Tracker1            │      ╰─────────────────────────────╯
╰──────────────────────────────────────╯
```

Activities update component state live; events update the event log; the procedure status flips from `EXECUTING` to `COMPLETED` when `main()` returns.

The transpiler output is plain Python — no DSL trickery, no eval-of-source-strings. You can read it, modify it, debug it with `pdb`, or check it into a deployment artifact.

## Example: from PLUTO to readable Python

`examples/01_original.pluto` (the original GSoC demo):

```pluto
procedure
    declare
      event chaos described by Total disaster, event chaos2
    end declare
    main
      initiate Switch on Star Tracker2
      in parallel until all complete
        initiate and confirm step SWITCH ON SECOND STAR TRACKER
          main
            initiate and confirm Switch on Reaction Wheel3 of AOC of Satellite;
          end main
        end step;
        initiate and confirm step SWITCH ON FIRST STAR TRACKER
          main
            initiate and confirm Switch on Star Tracker1;
          end main
        end step;
      end parallel
    end main
end procedure
```

`pluto-ecss compile`s it to:

```python
"""Transpiled from 01_original.pluto"""
from pluto_ecss.runtime import (
    Procedure, Event,
    switch_on, switch_off,
    initiate, initiate_and_confirm, initiate_and_confirm_step,
    parallel_until_all, parallel_until_one,
    wait_for_event, wait_until,
    inform_user, pluto_log,
)


def main():
    proc = Procedure("transpiled")
    proc.start()
    # --- declarations ---
    proc.declare_event(Event("chaos", description='Total disaster'))
    proc.declare_event(Event("chaos2"))
    # --- main ---
    initiate(switch_on("Star Tracker2"))
    def _branch_1():
        def _step_2():
            initiate_and_confirm(switch_on("Reaction Wheel3 of AOC of Satellite"))
        initiate_and_confirm_step("SWITCH ON SECOND STAR TRACKER", _step_2)
    def _branch_3():
        def _step_4():
            initiate_and_confirm(switch_on("Star Tracker1"))
        initiate_and_confirm_step("SWITCH ON FIRST STAR TRACKER", _step_4)
    parallel_until_all([_branch_1, _branch_3])
    proc.finish()


if __name__ == "__main__":
    main()
```

That generated file is self-contained Python. Drop it into any project that depends on `pluto_ecss.runtime` and it'll run.

## Supported PLUTO constructs

| Category | Constructs |
| --- | --- |
| Sections | `procedure / declare / preconditions / main / watchdog / confirmation / end procedure` |
| Events | `event NAME described by DESCRIPTION`, `raise event NAME`, `wait for event NAME` |
| Activities | `initiate [refer by NAME]`, `initiate and confirm [refer by NAME]`, `Switch on/off TARGET (of TARGET)*`, simple+record+array `with` arguments (A.3.9.26, A.3.9.27, A.3.9.28) |
| Steps | `initiate and confirm step NAME … end step` with full A.1.7 sub-bodies: `declare / preconditions / watchdog / confirmation / main` |
| Continuation tests | `in case confirmed: continue; not confirmed: restart [max N times \| with timeout T]; aborted: abort; raise event E; ask user; terminate; end case` — defaults per A.2.5 (A.3.9.33) |
| Activity properties | `<property> of <step or named-instance>` — `execution_status`, `start_time`, `completion_time`, `confirmation_status` (A.3.9.8) |
| Reporting data | External `ReportingData` registry, `save context refer to <ref> by <local>` snapshots, `value / engineering_value / validity_status / sampling_time` queryable (A.3.9.5, A.3.9.25) |
| Context | `in the context of X (of Y…) do … end context` — qualifies activity targets, nesting supported (A.3.9.10) |
| Control flow | `if … then … else … end if`, `case E of when V do … otherwise … end case`, `while … do … [with timeout E] end while`, `for X := A to B [by C] do … end for`, `repeat … until E [with timeout E] end repeat`, `wait for event E [with timeout T]`, `wait until E [with timeout T]` |
| Watchdog | `watchdog on EVENT do … end on end watchdog` — handlers fire synchronously when the event is raised |
| Concurrency | `in parallel until all complete … end parallel`, `in parallel until one completes … end parallel` |
| Assignment | `var := expr` |
| Expressions | numbers, strings, qualified names, property requests, `+ - * /`, `> < >= <= = <>`, `and / or / not` |
| Output | `log expr`, `inform user expr` |

## Architecture

```
       script.pluto
           │
           ▼
  ┌────────────────────┐
  │ pluto_ecss.parser     │  Lark Earley parser, grammar.lark
  └────────────────────┘
           │ Tree
           ▼
  ┌────────────────────┐
  │ pluto_ecss.transpiler │  Tree walker; emits readable Python source
  └────────────────────┘
           │ Python source string
           ▼
  ┌────────────────────┐
  │ pluto_ecss.runtime    │  Procedure, Event, parallel_*, switch_on/off, …
  └────────────────────┘
```

- **`src/pluto_ecss/grammar.lark`** — the grammar. Uses Earley because PLUTO's multi-word identifiers (`Star Tracker2`, `Reaction Wheel3 of AOC of Satellite`) require token-stream ambiguity. WORD has priority `-10` so keyword literals always win.
- **`src/pluto_ecss/parser.py`** — Lark wrapper, caches the compiled parser.
- **`src/pluto_ecss/transpiler.py`** — `_Emitter` class with a `_stmt_*` method per statement kind.
- **`src/pluto_ecss/runtime.py`** — concrete runtime: `Procedure`, `Event`, `Activity`, `parallel_until_all`, etc. Activities are registered via `register_activity(...)`; if none is registered, a default handler prints a trace.
- **`src/pluto_ecss/cli.py`** — the `pluto-ecss` command.

## Plugging in your own activities

The default handler for `Switch on X` just prints a line. To wire up real behaviour, register an `Activity` before running the transpiled module:

```python
from pluto_ecss.runtime import Activity, register_activity, switch_on, initiate_and_confirm

def my_switch_on(act):
    print(f"sending TC to power on {act.target}")
    # … send the real telecommand here …

register_activity(Activity("Switch on", "Star Tracker1", my_switch_on))

initiate_and_confirm(switch_on("Star Tracker1"))
```

## Running the tests

```bash
pip install -e ".[dev]"
pytest
```

## Repo layout

```
pluto-ecss/
├── README.md
├── LICENSE                       # MIT
├── pyproject.toml
├── .github/workflows/ci.yml
├── examples/                     # PLUTO scripts (01 = the original GSoC demo)
│   ├── 01_original.pluto
│   ├── 02_assignment_and_log.pluto
│   ├── 03_loops.pluto
│   ├── 04_events.pluto
│   └── 05_full_bringup.pluto
├── src/pluto_ecss/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── grammar.lark
│   ├── parser.py
│   ├── runtime.py
│   └── transpiler.py
└── tests/
    ├── conftest.py
    ├── test_parser.py
    ├── test_transpiler.py
    ├── test_runtime.py
    └── test_end_to_end.py
```

## What's missing (deliberate scope cuts)

To stay shippable for the Finish-Up-A-Thon deadline:

- **Generic object operations** beyond `Switch on/off` — adding more verbs is a one-line grammar change per verb plus a runtime helper.
- **Engineering units** on parameters (A.3 p–s) — units aren't tracked or auto-converted; values are plain Python.
- **`with value set` and `with directives` clauses** on activity calls (A.3.9.28). Simple, record, and array arguments are supported.
- **Monitoring statuses** (limit-check, delta-check, expected-status, status-consistency — A.3.9.8) — not implemented on reporting data.
- **"ask user"** in preconditions / confirmation (A.1.3, A.1.6) — only the continuation-action variant is interactive; precondition/confirmation `ask user` is not.
- **Full ECSS Space System Model** — the 2019 prototype carried a sprawling SSM class hierarchy; the current runtime keeps `SystemElement`, `Activity`, `Event`, `ReportingData`. The full model can be re-introduced incrementally on top of the runtime registry.

## Credits

- Original GSoC 2019 proposal & prototype: Sokratis Tzifkas
- 2026 revival for the Finish-Up-A-Thon: Sokratis Tzifkas, with AI assistance
- Built on [Lark](https://github.com/lark-parser/lark)
- PLUTO language defined by the ECSS-E-ST-70-32C standard (European Cooperation for Space Standardization)
