"""Tests for the Pyodide playground bundle."""
import json
import pathlib
import re
import subprocess
import sys


ROOT = pathlib.Path(__file__).parent.parent
PLAYGROUND = ROOT / "docs" / "playground"


def _load_bundle():
    js = (PLAYGROUND / "files.js").read_text()
    # extract the JS object literal (everything between the first '{' and last '}')
    start = js.index("{")
    end = js.rindex("}")
    return json.loads(js[start : end + 1])


def test_bundle_exists():
    assert (PLAYGROUND / "index.html").exists(), "playground index.html missing"
    assert (PLAYGROUND / "files.js").exists(), "playground files.js missing"


def test_bundle_in_sync_with_source():
    """Running build_playground.py should produce identical output."""
    before = (PLAYGROUND / "files.js").read_text()
    r = subprocess.run(
        [sys.executable, "scripts/build_playground.py"],
        cwd=str(ROOT), capture_output=True, text=True, check=False,
    )
    assert r.returncode == 0, r.stderr
    after = (PLAYGROUND / "files.js").read_text()
    assert before == after, "playground bundle is out of date; run scripts/build_playground.py"


def test_bundle_contains_required_modules():
    files = _load_bundle()
    required = {
        "plutopy/__init__.py",
        "plutopy/grammar.lark",
        "plutopy/parser.py",
        "plutopy/transpiler.py",
        "plutopy/runtime.py",
        "plutopy/formatter.py",
    }
    missing = required - set(files.keys())
    assert not missing, f"playground bundle missing files: {missing}"


def test_bundled_modules_match_source():
    files = _load_bundle()
    src = ROOT / "src" / "plutopy"
    for rel, content in files.items():
        # rel looks like "plutopy/parser.py"
        path = src / rel[len("plutopy/"):]
        assert path.read_text() == content, f"playground stale for {rel}"


def test_html_references_files_js_and_pyodide():
    html = (PLAYGROUND / "index.html").read_text()
    assert "files.js" in html, "playground HTML does not load files.js"
    assert "pyodide.js" in html, "playground HTML does not load Pyodide"
    # rough check that the boot Python code is well-formed
    py_block = re.search(r"pyodide\.runPython\(`([\s\S]+?)`\)", html)
    assert py_block, "no inline Python init block found"
    compile(py_block.group(1), "<playground>", "exec")
