"""Tests for reporting data + save context (PLUTO spec A.3.9.5 / A.3.9.25)."""
import pathlib
import subprocess
import sys

import pytest

from plutopy.parser import parse
from plutopy.transpiler import transpile


ROOT = pathlib.Path(__file__).parent.parent
EXAMPLES = ROOT / "examples"


def _run_cli(*args):
    env = {"PYTHONPATH": str(ROOT / "src")}
    return subprocess.run(
        [sys.executable, "-m", "plutopy", *args],
        env=env, capture_output=True, text=True, cwd=str(ROOT), check=False,
    )


def test_grammar_parses_save_context():
    src = """
    procedure main
      save context refer to Temperature of Battery1 by TempB1,
                         to Voltage of Battery1 by VoltB1
    end main end procedure
    """
    tree = parse(src)
    sc = tree.children[0].children[0].children[0]
    assert sc.data == "save_context_stmt"
    assert len(sc.children) == 2


def test_transpile_emits_save_context_call():
    src = """
    procedure main
      save context refer to Temperature of Battery1 by TempB1,
                         to Voltage of Battery1 by VoltB1
    end main end procedure
    """
    out = transpile(src)
    assert "proc.save_context(" in out
    assert '"Temperature of Battery1"' in out
    assert '"TempB1"' in out


def test_reporting_data_registry_and_resolve():
    from plutopy.runtime import (
        ReportingData, register_reporting_data, resolve_reporting_data,
        _reporting_data,
    )
    _reporting_data.clear()
    rd = register_reporting_data(ReportingData("Temperature", value=42, validity_status="valid"))
    assert resolve_reporting_data("Temperature") is rd
    # leading-name fallback (`Temperature of Battery1` -> `Temperature`)
    assert resolve_reporting_data("Temperature of Battery1") is rd


def test_save_context_snapshots_value_and_validity():
    from plutopy.runtime import (
        Procedure, ReportingData, register_reporting_data, _reporting_data,
    )
    _reporting_data.clear()
    register_reporting_data(ReportingData("Pressure", value=101.3, validity_status="valid"))
    proc = Procedure()
    proc.save_context([("Pressure", "P0")])
    assert "P0" in proc.reporting_data
    snap = proc.reporting_data["P0"]
    assert snap.value == 101.3
    assert snap.validity_status == "valid"
    # Mutate the live parameter after the snapshot
    from plutopy.runtime import resolve_reporting_data
    live = resolve_reporting_data("Pressure")
    live.value = 999.0
    # Snapshot is unaffected
    assert proc.reporting_data["P0"].value == 101.3


def test_save_context_missing_parameter_is_not_available():
    from plutopy.runtime import Procedure, _reporting_data
    _reporting_data.clear()
    proc = Procedure()
    proc.save_context([("NoSuchParam", "X")])
    assert proc.reporting_data["X"].validity_status == "not available"
    assert proc.reporting_data["X"].value is None


def test_resolve_ref_finds_local_snapshot_before_registry():
    from plutopy.runtime import (
        Procedure, ReportingData, register_reporting_data, _reporting_data,
    )
    _reporting_data.clear()
    register_reporting_data(ReportingData("Temp", value=100, validity_status="valid"))
    proc = Procedure()
    proc.save_context([("Temp", "MySnap")])
    # Mutate the live one
    live = _reporting_data["Temp"]
    live.value = 200
    # Snapshot read returns the saved value, not the live one
    assert proc.resolve_ref("MySnap") == 100


def test_get_property_validity_status_of_snapshot():
    from plutopy.runtime import (
        Procedure, ReportingData, register_reporting_data, _reporting_data,
    )
    _reporting_data.clear()
    register_reporting_data(ReportingData("V", value=12.0, validity_status="valid"))
    proc = Procedure()
    proc.save_context([("V", "V0")])
    assert proc.get_property("V0", "validity_status") == "valid"
    assert proc.get_property("V0", "value") == 12.0


def test_get_property_unknown_ref_raises_for_non_status_prop():
    from plutopy.runtime import Procedure, PlutoRuntimeError, _reporting_data
    _reporting_data.clear()
    proc = Procedure()
    with pytest.raises(PlutoRuntimeError):
        proc.get_property("Unknown", "validity_status")


def test_example_runs_end_to_end_with_registered_params():
    """Run the example via subprocess; register params on the fly."""
    bootstrap = (
        "from plutopy import ReportingData, register_reporting_data;"
        "register_reporting_data(ReportingData('Temperature', value=22.5, validity_status='valid'));"
        "register_reporting_data(ReportingData('Voltage', value=28.1, validity_status='valid'));"
        "from plutopy.transpiler import transpile;"
        "import pathlib;"
        "src = pathlib.Path('examples/15_save_context.pluto').read_text();"
        "ns = {'__name__': '__demo__'};"
        "exec(compile(transpile(src), 'demo', 'exec'), ns);"
        "ns['main']()"
    )
    r = subprocess.run(
        [sys.executable, "-c", bootstrap],
        cwd=str(ROOT),
        env={"PYTHONPATH": str(ROOT / "src")},
        capture_output=True, text=True, check=False,
    )
    assert r.returncode == 0, r.stderr
    assert "battery telemetry is valid" in r.stdout


def test_save_context_round_trips_through_formatter():
    from plutopy.formatter import format_source
    src = (EXAMPLES / "15_save_context.pluto").read_text()
    formatted = format_source(src)
    assert "save context refer to Temperature of Battery1 by TempBatt1" in formatted
    assert "to Voltage of Battery1 by VoltBatt1" in formatted
    assert format_source(formatted) == formatted


def test_save_context_serialises_to_json():
    from plutopy.json_emit import transpile_to_dict
    src = (EXAMPLES / "15_save_context.pluto").read_text()
    d = transpile_to_dict(src)
    sc_stmts = [s for s in d["main"] if s["kind"] == "save_context"]
    assert sc_stmts
    entries = sc_stmts[0]["entries"]
    assert {"ref": "Temperature of Battery1", "local": "TempBatt1"} in entries
    assert {"ref": "Voltage of Battery1", "local": "VoltBatt1"} in entries


def test_async_runtime_has_symmetric_save_context():
    from plutopy import async_runtime as ar
    proc = ar.Procedure()
    ar.register_reporting_data(ar.ReportingData("X", value=7, validity_status="valid"))
    proc.save_context([("X", "X0")])
    assert proc.reporting_data["X0"].value == 7
    assert proc.get_property("X0", "validity_status") == "valid"
