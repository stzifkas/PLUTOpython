"""Tests for friendly parse errors."""
import pytest

from plutopy.parser import PlutoParseError, parse


def test_missing_then_in_if():
    src = """procedure
  main
    if x = 1
      log "hi"
    end if
  end main
end procedure
"""
    with pytest.raises(PlutoParseError) as exc:
        parse(src, filename="demo.pluto")
    msg = str(exc.value)
    assert "demo.pluto" in msg
    assert "then" in msg
    # caret line is present
    assert "|" in msg
    assert "^" in msg


def test_missing_end_procedure_gives_hint():
    src = "procedure\n  main\n    log \"hi\"\n  end main\n"
    with pytest.raises(PlutoParseError) as exc:
        parse(src, filename="demo.pluto")
    msg = str(exc.value)
    assert "end of file" in msg or "end procedure" in msg
    assert "hint:" in msg


def test_error_has_location_attributes():
    src = "procedure\n  main\n    @@\n  end main\nend procedure\n"
    with pytest.raises(PlutoParseError) as exc:
        parse(src, filename="demo.pluto")
    assert exc.value.line == 3
    assert exc.value.filename == "demo.pluto"


def test_valid_input_does_not_raise():
    src = 'procedure main log "ok" end main end procedure'
    parse(src)  # should not raise
