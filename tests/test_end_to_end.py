import pathlib
import subprocess
import sys

EXAMPLES = pathlib.Path(__file__).parent.parent / "examples"
ROOT = pathlib.Path(__file__).parent.parent


def _run_cli(args):
    env = {"PYTHONPATH": str(ROOT / "src")}
    return subprocess.run(
        [sys.executable, "-m", "pluto_ecss", *args],
        env=env,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        check=False,
    )


def test_cli_run_original_script():
    result = _run_cli(["run", str(EXAMPLES / "01_original.pluto")])
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "Switch on Star Tracker2" in out
    assert "Switch on Reaction Wheel3 of AOC of Satellite" in out
    assert "Switch on Star Tracker1" in out


def test_cli_compile_writes_python():
    result = _run_cli(["compile", str(EXAMPLES / "04_events.pluto")])
    assert result.returncode == 0, result.stderr
    assert "def main():" in result.stdout
    assert 'Event("ready"' in result.stdout
    # output is valid Python
    compile(result.stdout, "<compiled>", "exec")


def test_cli_parse_prints_tree():
    result = _run_cli(["parse", str(EXAMPLES / "03_loops.pluto")])
    assert result.returncode == 0, result.stderr
    assert "while_stmt" in result.stdout
    assert "for_stmt" in result.stdout


def test_loops_example_actually_loops(capsys=None):
    result = _run_cli(["-v", "run", str(EXAMPLES / "03_loops.pluto")])
    assert result.returncode == 0, result.stderr
    # 3 while + 3 for iterations
    assert result.stderr.count("loop iteration") == 3
    assert result.stderr.count("for iteration") == 3
    assert "[INFORM] loops finished" in result.stdout
