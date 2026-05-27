"""Lark parser wrapper. Loads grammar.lark and exposes parse()."""
from __future__ import annotations

import pathlib
from functools import lru_cache

from lark import Lark, Tree

_GRAMMAR_PATH = pathlib.Path(__file__).parent / "grammar.lark"


@lru_cache(maxsize=1)
def _parser() -> Lark:
    return Lark(_GRAMMAR_PATH.read_text(), start="start", parser="earley", propagate_positions=True)


def parse(source: str) -> Tree:
    return _parser().parse(source)
