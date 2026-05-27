# Publishing plutopy to PyPI

This file documents the exact steps to cut a release. Tests must be
green, the version in `pyproject.toml` and `src/plutopy/__init__.py`
must match, and the wheel must pass `twine check`.

## Prerequisites

```bash
pip install build twine
```

You need a PyPI account and an API token (Settings → Account → API
tokens). Save it to `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-<your-token>

[testpypi]
username = __token__
password = pypi-<test-pypi-token>
```

## Pre-flight checklist

```bash
# 1. Make sure the working tree is clean
git status

# 2. Bump version in both places (they must match)
$EDITOR pyproject.toml          # version = "X.Y.Z"
$EDITOR src/plutopy/__init__.py # __version__ = "X.Y.Z"

# 3. Run the full test suite
pytest

# 4. Rebuild the playground bundle if any package source changed
python scripts/build_playground.py
pytest tests/test_playground.py

# 5. Build the artifacts
rm -rf dist/ build/ src/plutopy.egg-info/
python -m build --wheel --sdist

# 6. Sanity-check the artifacts
twine check dist/*

# 7. Verify the wheel actually installs and the CLI works
pip install --force-reinstall dist/plutopy-X.Y.Z-py3-none-any.whl
plutopy --version
plutopy run examples/01_original.pluto
```

## Test on TestPyPI first

```bash
twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            --force-reinstall plutopy
plutopy --version
plutopy run examples/01_original.pluto
```

## Publish to PyPI

```bash
twine upload dist/*
```

Then verify on https://pypi.org/project/plutopy/ that:

- The README renders without errors
- The "Project links" sidebar has Homepage / Docs / Playground / Issues / Changelog
- Classifiers include the Python version matrix and the spec topic
- The console script entry point `plutopy` is listed

## After publishing

1. Tag the release:
   ```bash
   git tag -a vX.Y.Z -m "Release X.Y.Z"
   git push origin vX.Y.Z
   ```
2. Create a GitHub release at https://github.com/stzifkas/PLUTOpython/releases/new from the new tag; attach the wheel and sdist from `dist/`.
3. Update the playground to install from PyPI instead of bundling source:
   - In `docs/playground/index.html`, replace the MEMFS write-loop with `await micropip.install("plutopy")`.
   - Remove `docs/playground/files.js` and `scripts/build_playground.py` from the docs CI workflow.
   - Drop `tests/test_playground.py` (or rewrite it to check the HTML alone).

## Rollback

If a release goes out broken:

```bash
twine upload dist/plutopy-X.Y.Z+post1*    # bump to a post-release first
```

PyPI does not allow re-uploading the same version; you must bump and
re-upload. Worst case, mark the bad release as yanked on PyPI:
Project page → Manage → Releases → Options → Yank.
