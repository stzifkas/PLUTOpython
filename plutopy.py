"""Compatibility shim: expose pluto_ecss under the legacy 'plutopy' name for docs.
Auto-generated during CI; not committed to main branch here.
"""
from pluto_ecss import *

# Expose package metadata
try:
    from pluto_ecss import __version__ as __version__
except Exception:
    __version__ = '0.0.0'
