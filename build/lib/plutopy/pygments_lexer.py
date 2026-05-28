"""Pygments lexer for the PLUTO DSL.

Registered as an entry point in pyproject.toml under
`pygments.lexers` as `plutopy.pygments_lexer:PlutoLexer`, so once the
package is installed you can write::

    pygmentize -l pluto examples/01_original.pluto

and ``mkdocs`` / Jekyll / GitHub-flavored markdown will highlight
fenced code blocks tagged ```pluto.
"""
from __future__ import annotations

from pygments.lexer import RegexLexer, words
from pygments.token import (
    Comment,
    Keyword,
    Name,
    Number,
    Operator,
    Punctuation,
    String,
    Text,
)


_BLOCK_KEYWORDS = (
    "procedure", "declare", "preconditions", "main", "watchdog",
    "confirmation", "step",
)
_CONTROL_KEYWORDS = (
    "if", "then", "else", "case", "of", "when", "otherwise",
    "while", "do", "for", "to", "by", "repeat", "until", "wait",
    "with", "timeout", "in", "the", "context", "parallel", "all",
    "complete", "one", "completes",
)
_ACTION_KEYWORDS = (
    "initiate", "and", "confirm", "raise", "log", "inform", "user",
    "Switch", "on", "off",
)
_DECL_KEYWORDS = (
    "event", "described", "end",
)
_OPERATOR_WORDS = (
    "and", "or", "not", "of",
)


class PlutoLexer(RegexLexer):
    """Pygments lexer for PLUTO procedures."""

    name = "PLUTO"
    aliases = ["pluto", "plutopy"]
    filenames = ["*.pluto"]
    mimetypes = ["text/x-pluto"]

    tokens = {
        "root": [
            (r"//[^\n]*", Comment.Single),
            (r"\s+", Text),
            (r'"[^"\n]*"', String.Double),
            (r"[0-9]+(\.[0-9]+)?", Number),
            (r":=", Operator),
            (r"(>=|<=|<>|=|>|<)", Operator),
            (r"[+\-*/]", Operator),
            (r"[,;:()]", Punctuation),
            (words(_BLOCK_KEYWORDS, prefix=r"\b", suffix=r"\b"), Keyword.Reserved),
            (words(_DECL_KEYWORDS, prefix=r"\b", suffix=r"\b"), Keyword.Declaration),
            (words(_CONTROL_KEYWORDS, prefix=r"\b", suffix=r"\b"), Keyword),
            (words(_OPERATOR_WORDS, prefix=r"\b", suffix=r"\b"), Operator.Word),
            (words(_ACTION_KEYWORDS, prefix=r"\b", suffix=r"\b"), Keyword.Pseudo),
            (r"[A-Za-z_][A-Za-z0-9_]*", Name),
        ],
    }
