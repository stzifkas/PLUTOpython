"""Compatibility shim package exposing pluto_ecss as 'plutopy' for docs build."""
from pluto_ecss import *

try:
    from pluto_ecss import __version__ as __version__
except Exception:
    __version__ = '0.0.0'
