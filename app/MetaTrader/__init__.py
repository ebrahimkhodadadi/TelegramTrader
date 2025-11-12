"""
MetaTrader 5 Integration Package

This package provides modular components for MetaTrader 5 integration,
following clean architecture principles with single responsibility.
"""

from .MetaTrader import MetaTrader, get_mt5_time, get_symbols
from .connection import AccountConfig

# Backward compatibility exports
Trade = MetaTrader.Trade
RiskFreePositions = MetaTrader.RiskFreePositions
Update_last_signal = MetaTrader.Update_last_signal
Update_signal = MetaTrader.Update_signal
Close_half_signal = MetaTrader.Close_half_signal
Delete_signal = MetaTrader.Delete_signal
monitor_all_accounts = MetaTrader.monitor_all_accounts

__all__ = ['MetaTrader', 'get_mt5_time', 'get_symbols', 'AccountConfig', 'Trade', 'RiskFreePositions', 'Update_last_signal', 'Update_signal', 'Close_half_signal', 'Delete_signal', 'monitor_all_accounts']