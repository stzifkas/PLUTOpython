# Quickstart

## Install

```bash
git clone https://github.com/stzifkas/pluto-ecss
cd pluto-ecss
pip install -e .          # adds the `pluto-ecss` console script
pip install -e ".[tui]"   # plus rich, for `pluto-ecss demo`
pip install -e ".[dev]"   # plus pytest + rich + pygments
```

Python 3.9 or newer is required. The only runtime dependency is [`lark`](https://pypi.org/project/lark/).

## The pipeline

```text
script.pluto
    │
    ▼  pluto_ecss.parser  (Lark Earley)
parse tree
    │
    ▼  pluto_ecss.transpiler
Python source
    │
    ▼  exec()
running procedure  ── calls into ──>  pluto_ecss.runtime
```

## Commands

```bash
pluto-ecss parse   examples/03_loops.pluto              # show the parse tree
pluto-ecss compile examples/01_original.pluto           # emit Python (threaded runtime)
pluto-ecss compile --runtime async examples/01_original.pluto   # emit async/await Python
pluto-ecss compile examples/01_original.pluto -o /tmp/demo.py
pluto-ecss run     examples/01_original.pluto           # transpile and execute
pluto-ecss run --runtime async examples/04_events.pluto # run against asyncio runtime
pluto-ecss -v run  examples/04_events.pluto             # with runtime lifecycle logs
pluto-ecss demo    examples/05_full_bringup.pluto       # live TUI dashboard
pluto-ecss fmt     examples/01_original.pluto           # canonicalise the source
pluto-ecss gen     examples/specs/bringup.yaml          # scaffold from a YAML spec
```

## Runtime targets

By default `compile` and `run` target the **threaded** runtime (`pluto_ecss.runtime`). Pass `--runtime async` to emit `async def main()` calling `pluto_ecss.async_runtime`, which uses `asyncio.gather` for parallel sections and `asyncio.Event` for `wait for event`. Useful when integrating into an existing event loop — threads inside `asyncio` are a footgun.

## Your first PLUTO procedure

`hello.pluto`:

```pluto
procedure
    declare
      event ready described by Spacecraft online
    end declare
    main
      log "starting up"
      initiate and confirm Switch on Star Tracker1
      raise event ready
      inform user "we are go for science"
    end main
end procedure
```

Run it:

```bash
$ pluto-ecss -v run hello.pluto
pluto-ecss: procedure start: transpiled
pluto-ecss: [LOG] starting up
pluto-ecss: activity: Switch on on Star Tracker1
pluto-ecss: event raised: ready
pluto-ecss: procedure complete: transpiled
[ACTIVITY] Switch on Star Tracker1
[INFORM] we are go for science
```

The default activity handler just prints. To wire your own behaviour:

```python
from pluto_ecss.runtime import Activity, register_activity, switch_on, initiate_and_confirm

def my_switch_on(act):
    print(f"sending TC to power on {act.target}")
    # … send the real telecommand here …

register_activity(Activity("Switch on", "Star Tracker1", my_switch_on))
initiate_and_confirm(switch_on("Star Tracker1"))
```
