"""
MetaTrader 5 Integration Package

This package provides modular components for MetaTrader 5 integration,
following clean architecture principles with single responsibility.
"""

from .MetaTrader import MetaTrader, get_mt5_time, get_symbols
from .connection import AccountConfig

__all__ = ['MetaTrader', 'get_mt5_time', 'get_symbols', 'AccountConfig']