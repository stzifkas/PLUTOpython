import pathlib

import pytest

from plutopy.parser import parse


EXAMPLES = sorted(pathlib.Path(__file__).parent.parent.joinpath("examples").glob("*.pluto"))


@pytest.mark.parametrize("path", EXAMPLES, ids=[p.name for p in EXAMPLES])
def test_examples_parse(path):
    tree = parse(path.read_text())
    assert tree.data == "start"


def test_minimal_procedure():
    src = 'procedure main log "hi" end main end procedure'
    tree = parse(src)
    assert tree.data == "start"


def test_multiword_qname():
    src = """
    procedure
      main
        initiate Switch on Reaction Wheel3 of AOC of Satellite
      end main
    end procedure
    """
    tree = parse(src)
    main = tree.children[0].children[0]
    assert main.data == "main_section"
    initiate = main.children[0]
    assert initiate.data == "initiate_stmt"
    switch_on = initiate.children[0]
    qname = switch_on.children[0]
    # qname has three name children: "Reaction Wheel3", "AOC", "Satellite"
    assert len(qname.children) == 3
