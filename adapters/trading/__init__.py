"""Trading adapter entrypoints.

This package provides a minimal re-export layer so new code can depend on
`adapters.trading` without immediately moving the existing broker modules.
"""

from adapters import broker

__all__ = ["broker"]
