"""Pytest config: ensure src/ is on sys.path and the legacy plutopy.py doesn't shadow."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")

# Drop cwd and the legacy module path so `import plutopy` resolves to src/plutopy/.
sys.path[:] = [p for p in sys.path if p not in ("", ".", ROOT)]
if SRC not in sys.path:
    sys.path.insert(0, SRC)
