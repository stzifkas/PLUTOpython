<!--
Draft for the GitHub Finish-Up-A-Thon submission post.
Paste into dev.to and add:
  - Cover image (any small satellite/spacecraft illustration works)
  - Tags: githubFinishUpAThon, python, opensource, parsers
  - Canonical URL: pointing at the GitHub repo if you want
-->

# I finally finished my GSoC 2019 project, seven years later

Back in **2019**, as part of a [Google Summer of Code proposal](https://github.com/stzifkas/pluto-ecss/tree/v0.1-gsoc-2019), I started building an open-source parser for **PLUTO** — the procedure language [standardised by ECSS](https://ecss.nl/standard/ecss-e-st-70-32c-space-engineering-test-and-operations-procedure-language/) (`ECSS-E-ST-70-32C`) for spacecraft operations. PLUTO is the DSL ground operators write to bring up a star tracker, run a parallel safety sequence, or react to a satellite-on-orbit event.

My proposal sample built a parse tree from one hard-coded script and "ran" it by walking the tree. It was a proof-of-concept I never grew past one example file. Then life happened, and it sat dormant for seven years.

When the **GitHub Finish-Up-A-Thon** showed up, this was the obvious candidate. So I picked it up, this time with AI tooling at my side, and turned it into something real.

## Before — the GSoC 2019 snapshot

Branch [`legacy/gsoc-2019`](https://github.com/stzifkas/pluto-ecss/tree/legacy/gsoc-2019), tag [`v0.1-gsoc-2019`](https://github.com/stzifkas/pluto-ecss/releases/tag/v0.1-gsoc-2019). Five files, ~30 lines of grammar, no tests, no CLI, several straight-up bugs:

```python
# pluto_ecss.py (2019) — a few real lines from the original
class WatchdogSymbol(Symbol):
    def __init__(self,name,events,step=None):
        self.name = name
        # `super.__init__(...)` without parens — would crash if reached
        ...

class ProcedureSymbol(Symbol):
    def setExecutionSatus(self,data):   # typo: Satus
        self.executionStatus = data
```

The original grammar covered five PLUTO constructs and a single test script:

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

That ran end-to-end. Anything else was a parse error or a `NameError` because of `types` never being imported.

## After — `main`, May 2026

Same script, same syntax — but now it transpiles to readable Python:

```text
$ pluto-ecss compile examples/01_original.pluto
"""Transpiled from 01_original.pluto"""
from pluto_ecss.runtime import (
    Procedure, Event, PlutoAborted, PlutoTerminated,
    switch_on, switch_off,
    initiate, initiate_and_confirm, initiate_and_confirm_step,
    parallel_until_all, parallel_until_one,
    wait_for_event, wait_until,
    inform_user, pluto_log,
)

def main():
    proc = Procedure("transpiled")
    proc.start()
    proc.declare_event(Event("chaos", description='Total disaster'))
    proc.declare_event(Event("chaos2"))
    initiate(proc, switch_on("Star Tracker2"))
    def _branch_1():
        def _step_2():
            initiate_and_confirm(proc, switch_on("Reaction Wheel3 of AOC of Satellite"))
        initiate_and_confirm_step(proc, "SWITCH ON SECOND STAR TRACKER", _step_2)
    def _branch_3():
        def _step_4():
            initiate_and_confirm(proc, switch_on("Star Tracker1"))
        initiate_and_confirm_step(proc, "SWITCH ON FIRST STAR TRACKER", _step_4)
    parallel_until_all([_branch_1, _branch_3])
    proc.finish()

if __name__ == "__main__":
    main()
```

And it actually executes:

```text
$ pluto-ecss run examples/01_original.pluto
[ACTIVITY] Switch on Star Tracker2
[ACTIVITY] Switch on Reaction Wheel3 of AOC of Satellite
[ACTIVITY] Switch on Star Tracker1
```

## Grammar coverage went from ~5 constructs to most of the ECSS spec

The 2019 grammar handled `procedure / main / initiate / initiate and confirm / parallel until all`. After eleven days of focused work, the implementation covers, with anchors to the ECSS sections:

- **A.1.7** — Full procedure & step structure: `declare / preconditions / watchdog / confirmation / main`, and steps mirror procedures.
- **A.3.9.8** — Object references with property requests: `execution_status of <step>`, `validity_status of <param>`, etc.
- **A.3.9.10** — `in the context of X (of Y) do … end context` — qualifies activity targets, properly nested.
- **A.3.9.5 / A.3.9.25** — `save context refer to Temperature of Battery1 by TempB1, …` — telemetry snapshotting.
- **A.3.9.26 / A.3.9.27** — `refer by <name>` on both fire-and-forget initiate and synchronous initiate-and-confirm.
- **A.3.9.28** — Activity arguments in all three shapes: simple (`Mode := "safe"`), record (`Tx record A := 1, B := 2 end record`), and array (`Vs array 1, 2, 3 end array`).
- **A.3.9.33** — Continuation tests with all seven actions (`resume / abort / continue / terminate / ask user / raise event / restart [max N times | with timeout T]`) and the A.2.5 default actions for arms that aren't explicitly set.

Plus the everyday language stuff: `if/else`, `case/when/otherwise`, `while`, `for`, `repeat`, `wait until` / `wait for event` with optional `with timeout`, expressions with arithmetic / comparison / boolean operators, `:=` assignment, `raise event`, `log`, `inform user`, `in parallel until all complete` and `until one completes`.

## A live TUI demo of the runtime

`pluto-ecss demo SCRIPT` runs a transpiled procedure against a Rich-based dashboard that lights up as activities execute:

```text
╭──────────────────── Procedure: 01_original.pluto ─────────────────────╮
│                              COMPLETED                                │
╰───────────────────────────────────────────────────────────────────────╯
                     🛰  Satellite (AOC subsystem)
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component             ┃        Status         ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ AOC Electronics1      │          OFF          │
│ AOC Electronics2      │          OFF          │
│ Reaction Wheel3       │          ON           │
│ Star Tracker1         │          ON           │
│ Star Tracker2         │          ON           │
└───────────────────────┴───────────────────────┘
╭──────────── 📡 Activity feed ────────────╮
│ ▶ Switch on  Star Tracker2                │
│ ▶ Switch on  Reaction Wheel3 of AOC of …  │
│ ▶ Switch on  Star Tracker1                │
╰───────────────────────────────────────────╯
```

## Compile knobs, because the same PLUTO procedure has many right targets

The transpiler isn't one-size-fits-all. Modern mission-control stacks are asyncio-based; libraries want subclassable procedures; some tools want structured data instead of Python. So:

- `--runtime async` → emits `async def main()` against an asyncio runtime with `asyncio.gather` for parallel sections.
- `--style class` → emits a `class TranspiledProcedure(Procedure)` with declarations in `__init__` and main body as `run()`.
- `--emit json` → skips Python entirely, emits a structured JSON description of the procedure for tooling integration.
- `--no-runtime` → inlines the runtime so the output is a single self-contained `.py` with no `pluto-ecss` dependency.

All four compose. `--style class --runtime async` works.

## Friendly errors

The 2019 version raised raw Lark exceptions. The new version catches them and explains:

```text
$ pluto-ecss parse bad.pluto
pluto-ecss: parse error
at bad.pluto:4:7: cannot start a token with 'l'; expected 'and', 'or', 'then', or one of 2 more

     4 |       log "hi"
       |       ^

hint: an if statement looks like: if EXPR then STATEMENTS end if
```

## What landed in numbers

|             | 2019 | 2026 |
| ---         | ---  | ---  |
| Grammar     | 30 lines | 168 lines |
| Tests       | 0 | 224 passing |
| Examples    | 1 | 17 |
| LOC (package) | ~600 | 3 778 |
| CLI surface | none | `parse / compile / run / demo / fmt / gen` |
| Runtimes    | inline tree walker | threaded + asyncio |
| Output formats | side effects | Python (4 variants) + JSON |
| Docs        | one README | full mkdocs site with Pygments lexer |
| Playground  | none | browser-based via Pyodide |
| ECSS sections covered | a handful | most of A.1 and A.3 |

## AI-assisted, honestly

This revival was AI-assisted. I used an AI coding assistant to accelerate the rebuild — particularly for designing the Lark grammar's keyword-priority resolution (the original grammar had brittle negative-lookahead patterns that broke on common keywords), the transpiler's parse-tree-walker, and the runtime's threading primitives. The architectural decisions, the choice to write a transpiler instead of an interpreter, and the test design were mine; the assistant accelerated the typing and surfaced an Earley lexer-priority bug that would have cost me hours to chase down alone.

The interesting thing about doing this with AI tooling at hand is that it removes the discouragement: the 2019 code had real bugs and missing imports that, in 2019, felt like cliff-edges. In 2026, fixing those and *then* doing the spec work felt like one continuous flow rather than three separate undertakings.

## Try it

- **[Repo](https://github.com/stzifkas/pluto-ecss)** — `main` is the after, `legacy/gsoc-2019` is the before
- **[Docs](https://stzifkas.github.io/pluto-ecss/)** — quickstart, grammar reference, architecture
- **[Playground](https://stzifkas.github.io/pluto-ecss/playground/)** — write PLUTO and run it in the browser; no install
- `pip install -e .` → `pluto-ecss run examples/05_full_bringup.pluto`

The completion arc is real. Seven years of dormancy, eleven days of focused finishing, and what was a "sample for a proposal" is now an installable transpiler with a real test suite, a CLI, an asyncio runtime, a docs site, and a browser playground.

Sometimes you really can come back to the abandoned thing and finally ship it.
