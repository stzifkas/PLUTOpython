# The Finish-Up-A-Thon arc

This repo started life in **2019** as a [Google Summer of Code work product](https://github.com/stzifkas/PLUTOpython/tree/v0.1-gsoc-2019): a sample parser for the PLUTO DSL that built a parse tree out of a single hard-coded script and "ran" it by walking the tree. It was a proof of concept that never grew past one example file. It sat dormant for nearly seven years.

For the [GitHub Finish-Up-A-Thon](https://dev.to/github) (May–June 2026), it's been revived as an actual installable PLUTO transpiler.

## Before — the GSoC snapshot

Tag [`v0.1-gsoc-2019`](https://github.com/stzifkas/PLUTOpython/releases/tag/v0.1-gsoc-2019), branch [`legacy/gsoc-2019`](https://github.com/stzifkas/PLUTOpython/tree/legacy/gsoc-2019).

| Aspect | State in 2019 |
| --- | --- |
| Grammar | ~30 lines, covered `initiate`, `initiate and confirm (step)`, `parallel until all`, `switch on`, event declarations |
| Runtime | Tree-walking interpreter inside the parser file. Threaded but missing many features. |
| Codebase | Two `.py` files, mixed concerns, several syntax-level bugs (typos like `setExecutionSatus`, missing `import types`, `super.__init__` with no parens) |
| Tests | None |
| Packaging | None — `python plutopy.py` only |
| CLI | None — entry point hard-coded to `script.pluto` |
| Output | Side effects from a tree walk; no Python emission |
| Docs | README sketched the design but didn't say how to use it |

## After — `main`, May 2026

| Aspect | State in 2026 |
| --- | --- |
| Grammar | `if/else`, `case`, `while`, `for`, `repeat … until`, `wait for event` / `wait until` with `with timeout`, `:=` assignment, `raise event`, `log`, `inform user`, `in parallel until one completes`, full expression grammar (arithmetic / comparison / boolean), watchdog handlers — plus everything from 2019 |
| Pipeline | **Transpiler**: PLUTO → parse tree → Python source. Generated `.py` imports a runtime library and is independently runnable / debuggable / shippable. |
| Runtime | `plutopy.runtime` with `Procedure`, `Event`, `Activity`, `parallel_until_all`, `wait_for_event`, watchdog dispatch, etc. Activities are pluggable. |
| Package | `pip install plutopy`, proper `src/` layout, packaged grammar file |
| CLI | `plutopy parse | compile | run | demo` with `-v` for runtime logging |
| Demo | `plutopy demo` — live Rich-based TUI of a fake satellite reacting to procedure activities in real time |
| Errors | Friendly parse errors with file:line:column, source caret, structural hints |
| Tests | 48 pytest cases covering parser, transpiler output, runtime, end-to-end CLI, and the TUI |
| CI | GitHub Actions matrix on Python 3.9 / 3.11 / 3.13 |
| Highlighter | Pygments lexer for `.pluto` files; powers this docs site |
| Docs | This mkdocs site, deployed from `docs/` via CI |

## AI-assisted revival

This revival was AI-assisted. The architectural decisions (transpiler over interpreter, Rich for the TUI, lowering WORD priority to fix the keyword-vs-identifier ambiguity in the Earley lexer, the runtime API surface) and the test design are mine; the AI assistant accelerated typing, drafted the Lark grammar's first cut, and surfaced the Earley lexer priority bug that would have taken me a couple of hours to chase down.
