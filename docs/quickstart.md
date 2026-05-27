# Quickstart

## Install

```bash
git clone https://github.com/stzifkas/PLUTOpython
cd PLUTOpython
pip install -e .          # adds the `plutopy` console script
pip install -e ".[tui]"   # plus rich, for `plutopy demo`
pip install -e ".[dev]"   # plus pytest + rich + pygments
```

Python 3.9 or newer is required. The only runtime dependency is [`lark`](https://pypi.org/project/lark/).

## The pipeline

```text
script.pluto
    │
    ▼  plutopy.parser  (Lark Earley)
parse tree
    │
    ▼  plutopy.transpiler
Python source
    │
    ▼  exec()
running procedure  ── calls into ──>  plutopy.runtime
```

## Commands

```bash
plutopy parse   examples/03_loops.pluto      # show the parse tree
plutopy compile examples/01_original.pluto   # emit Python to stdout
plutopy compile  examples/01_original.pluto -o /tmp/demo.py
plutopy run     examples/01_original.pluto   # transpile and execute
plutopy -v run  examples/04_events.pluto     # with runtime lifecycle logs
plutopy demo    examples/05_full_bringup.pluto    # live TUI dashboard
```

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
$ plutopy -v run hello.pluto
plutopy: procedure start: transpiled
plutopy: [LOG] starting up
plutopy: activity: Switch on on Star Tracker1
plutopy: event raised: ready
plutopy: procedure complete: transpiled
[ACTIVITY] Switch on Star Tracker1
[INFORM] we are go for science
```

The default activity handler just prints. To wire your own behaviour:

```python
from plutopy.runtime import Activity, register_activity, switch_on, initiate_and_confirm

def my_switch_on(act):
    print(f"sending TC to power on {act.target}")
    # … send the real telecommand here …

register_activity(Activity("Switch on", "Star Tracker1", my_switch_on))
initiate_and_confirm(switch_on("Star Tracker1"))
```
