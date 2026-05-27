import pathlib

import pytest

from plutopy.transpiler import transpile


EXAMPLES = sorted(pathlib.Path(__file__).parent.parent.joinpath("examples").glob("*.pluto"))


@pytest.mark.parametrize("path", EXAMPLES, ids=[p.name for p in EXAMPLES])
def test_examples_compile(path):
    out = transpile(path.read_text())
    assert "def main():" in out
    assert "from plutopy.runtime import" in out
    # the transpiled source must be valid Python
    compile(out, str(path), "exec")


def test_event_declaration_emitted():
    src = """
    procedure
      declare
        event boom described by Big problem
      end declare
      main
        log "ok"
      end main
    end procedure
    """
    out = transpile(src)
    assert 'Event("boom"' in out
    assert "Big problem" in out


def test_assignment_emitted():
    src = """
    procedure
      main
        counter := 1 + 2
      end main
    end procedure
    """
    out = transpile(src)
    assert "counter = " in out
    assert "proc.variables[\"counter\"]" in out


def test_parallel_emits_branches():
    src = """
    procedure
      main
        in parallel until all complete
          initiate and confirm step A
            main
              initiate and confirm Switch on X;
            end main
          end step;
          initiate and confirm step B
            main
              initiate and confirm Switch on Y;
            end main
          end step;
        end parallel
      end main
    end procedure
    """
    out = transpile(src)
    assert "parallel_until_all" in out
    assert out.count("def _step_") >= 2
