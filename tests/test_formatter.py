"""Tests for the PLUTO pretty-printer."""
import pathlib
import subprocess
import sys

import pytest

from plutopy.formatter import format_source
from plutopy.parser import parse


ROOT = pathlib.Path(__file__).parent.parent
EXAMPLES = sorted((ROOT / "examples").glob("*.pluto"))


@pytest.mark.parametrize("path", EXAMPLES, ids=[p.name for p in EXAMPLES])
def test_examples_format_and_reparse(path):
    """Every example formats to something the parser accepts back."""
    formatted = format_source(path.read_text(), filename=str(path))
    tree = parse(formatted)
    assert tree.data == "start"


@pytest.mark.parametrize("path", EXAMPLES, ids=[p.name for p in EXAMPLES])
def test_format_is_idempotent(path):
    """format(format(x)) == format(x) — the formatter has reached a fixed point."""
    first = format_source(path.read_text(), filename=str(path))
    second = format_source(first)
    assert first == second, "formatter is not idempotent"


def test_formatter_normalises_indentation():
    src = """procedure
      main
        log "hi"
      end main
end procedure"""
    out = format_source(src)
    assert out.split("\n")[1] == "  main"  # 2-space indent
    assert out.split("\n")[2] == '    log "hi"'


def test_formatter_drops_redundant_semicolons():
    src = """procedure
  main
    initiate and confirm Switch on X;
  end main
end procedure"""
    out = format_source(src)
    assert ";" not in out


def test_formatter_preserves_else_branch():
    src = """procedure main
        if x = 1 then
          inform user "yes"
        else
          inform user "no"
        end if
      end main end procedure"""
    out = format_source(src)
    assert "else" in out
    assert "yes" in out and "no" in out


def test_cli_fmt_check_passes_on_canonical():
    env = {"PYTHONPATH": str(ROOT / "src")}
    # First format in place to a temp copy
    src_path = ROOT / "examples" / "01_original.pluto"
    formatted = format_source(src_path.read_text())

    import tempfile
    tmp = pathlib.Path(tempfile.mkstemp(suffix=".pluto")[1])
    try:
        tmp.write_text(formatted)
        result = subprocess.run(
            [sys.executable, "-m", "plutopy", "fmt", "--check", str(tmp)],
            env=env, capture_output=True, text=True, cwd=str(ROOT), check=False,
        )
        assert result.returncode == 0
    finally:
        tmp.unlink()


def test_cli_fmt_check_fails_on_non_canonical():
    env = {"PYTHONPATH": str(ROOT / "src")}
    src_path = ROOT / "examples" / "01_original.pluto"
    result = subprocess.run(
        [sys.executable, "-m", "plutopy", "fmt", "--check", str(src_path)],
        env=env, capture_output=True, text=True, cwd=str(ROOT), check=False,
    )
    # original uses 4-space indentation; canonical is 2 → should not match
    assert result.returncode == 1
