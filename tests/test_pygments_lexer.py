"""Smoke test for the Pygments lexer. Skipped if Pygments isn't installed."""
import pytest

pygments = pytest.importorskip("pygments")

from pygments import highlight
from pygments.formatters import RawTokenFormatter
from pygments.token import Keyword, Name

from pluto_ecss.pygments_lexer import PlutoLexer


def test_keywords_are_tokenised_as_keywords():
    src = "procedure\n  main\n    initiate Switch on Star Tracker1\n  end main\nend procedure"
    tokens = list(PlutoLexer().get_tokens(src))
    types_and_text = [(t, v) for t, v in tokens]
    keyword_words = {v.strip() for t, v in types_and_text if t in Keyword or t in Keyword.Reserved or t in Keyword.Pseudo}
    assert "procedure" in keyword_words
    assert "main" in keyword_words
    assert "initiate" in keyword_words
    assert "Switch" in keyword_words


def test_identifiers_kept_as_names():
    src = "procedure main\nx := 1\nend main\nend procedure"
    tokens = list(PlutoLexer().get_tokens(src))
    # 'x' should appear as a Name token
    names = {v.strip() for t, v in tokens if t in Name}
    assert "x" in names


def test_highlight_does_not_crash():
    out = highlight("procedure main log \"hi\" end main end procedure",
                    PlutoLexer(), RawTokenFormatter())
    assert b"Keyword" in out
