"""Shared adapter entrypoints.

This package provides a minimal re-export layer so new code can depend on
`adapters.shared` without immediately moving the existing adapter modules.
"""

from adapters import joinquant, local

__all__ = ["local", "joinquant"]
