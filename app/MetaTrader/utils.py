"""Utility functions and helpers for MetaTrader operations"""


def get_mt5_time():
    """Get current MT5 server time"""
    from connection import ConnectionManager
    return ConnectionManager.get_mt5_time()


def get_symbols():
    """Get all available symbols"""
    from connection import ConnectionManager
    return ConnectionManager.get_symbols()