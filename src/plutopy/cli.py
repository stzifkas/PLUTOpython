"""Command-line interface for plutopy.

Usage:
    plutopy parse    SCRIPT          # show parse tree
    plutopy compile  SCRIPT [-o OUT] # emit Python source
    plutopy run      SCRIPT          # transpile and execute
"""
from __future__ import annotations

import argparse
import pathlib
import sys
import tempfile

from plutopy import __version__
from plutopy.parser import parse as parse_pluto, PlutoParseError
from plutopy.transpiler import transpile


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="plutopy", description="PLUTO -> Python transpiler")
    ap.add_argument("--version", action="version", version=f"plutopy {__version__}")
    ap.add_argument("-v", "--verbose", action="store_true", help="emit runtime lifecycle logs")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_parse = sub.add_parser("parse", help="show the parse tree of a PLUTO script")
    p_parse.add_argument("script", type=pathlib.Path)

    p_compile = sub.add_parser("compile", help="transpile to Python")
    p_compile.add_argument("script", type=pathlib.Path)
    p_compile.add_argument("-o", "--output", type=pathlib.Path, help="output .py path (default: stdout)")

    p_run = sub.add_parser("run", help="transpile and execute")
    p_run.add_argument("script", type=pathlib.Path)
    p_run.add_argument("--keep", action="store_true", help="keep transpiled .py file and print its path")

    p_demo = sub.add_parser("demo", help="live TUI dashboard (requires rich)")
    p_demo.add_argument("script", type=pathlib.Path, nargs="?", help="optional .pluto script; defaults to examples/05_full_bringup.pluto")

    p_fmt = sub.add_parser("fmt", help="canonicalise PLUTO source (pretty-print)")
    p_fmt.add_argument("script", type=pathlib.Path)
    p_fmt.add_argument("-i", "--in-place", action="store_true", help="rewrite the file in place")
    p_fmt.add_argument("--check", action="store_true", help="exit non-zero if the file isn't already canonical")

    p_gen = sub.add_parser("gen", help="generate a PLUTO procedure from a YAML spec")
    p_gen.add_argument("spec", type=pathlib.Path, help="YAML spec file")
    p_gen.add_argument("-o", "--output", type=pathlib.Path, help="output .pluto path (default: stdout)")

    args = ap.parse_args(argv)

    if args.verbose:
        import logging
        logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

    if args.cmd == "parse":
        try:
            tree = parse_pluto(args.script.read_text(), filename=str(args.script))
        except PlutoParseError as e:
            print(f"plutopy: parse error\n{e}", file=sys.stderr)
            return 1
        print(tree.pretty())
        return 0

    if args.cmd == "compile":
        try:
            py = transpile(args.script.read_text(), module_doc=f"Transpiled from {args.script.name}")
        except PlutoParseError as e:
            print(f"plutopy: parse error\n{e}", file=sys.stderr)
            return 1
        if args.output:
            args.output.write_text(py)
        else:
            sys.stdout.write(py)
        return 0

    if args.cmd == "demo":
        from plutopy.demo import run_demo
        return run_demo(args.script)

    if args.cmd == "gen":
        from plutopy.generator import generate_from_file, GeneratorError
        try:
            out = generate_from_file(args.spec)
        except (GeneratorError, PlutoParseError) as e:
            print(f"plutopy: gen error\n{e}", file=sys.stderr)
            return 1
        if args.output:
            args.output.write_text(out)
        else:
            sys.stdout.write(out)
        return 0

    if args.cmd == "fmt":
        from plutopy.formatter import format_source
        original = args.script.read_text()
        try:
            formatted = format_source(original, filename=str(args.script))
        except PlutoParseError as e:
            print(f"plutopy: parse error\n{e}", file=sys.stderr)
            return 1
        if args.check:
            return 0 if original == formatted else 1
        if args.in_place:
            args.script.write_text(formatted)
            return 0
        sys.stdout.write(formatted)
        return 0

    if args.cmd == "run":
        try:
            py = transpile(args.script.read_text(), module_doc=f"Transpiled from {args.script.name}")
        except PlutoParseError as e:
            print(f"plutopy: parse error\n{e}", file=sys.stderr)
            return 1
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
            tmp.write(py)
            tmp_path = tmp.name
        if args.keep:
            print(f"[transpiled to {tmp_path}]", file=sys.stderr)
        ns: dict = {"__name__": "__main__", "__file__": tmp_path}
        exec(compile(py, tmp_path, "exec"), ns)
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
