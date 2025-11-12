import os
import Configure
from loguru import logger
import MetaTrader5 as mt5
import time
from datetime import datetime
import pytz


class ConnectionManager:
    """Handles MetaTrader 5 connection management and symbol validation"""

    @staticmethod
    def get_mt5_time():
        """Get current MT5 server time"""
        try:
            # Check if MT5 is initialized
            if mt5.terminal_info() is None:
                return None

            # Use a common symbol to get time
            symbol = "XAUUSD"
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                # Try EURUSD as fallback
                tick = mt5.symbol_info_tick("EURUSD")
                if tick is None:
                    return None

            server_time = tick.time
            server_time_utc = datetime.utcfromtimestamp(
                server_time).replace(tzinfo=pytz.utc)
            return server_time_utc
        except Exception as e:
            logger.error(f"Error getting MT5 time: {e}")
            return None

    @staticmethod
    def get_symbols():
        """Retrieve all available symbols from MT5"""
        try:
            # Check if MT5 is initialized and logged in
            terminal_info = mt5.terminal_info()
            if terminal_info is None:
                # logger.warning("MT5 terminal not initialized, attempting to initialize...")
                # Try to initialize without login for basic operations
                if not mt5.initialize():
                    logger.error("Failed to initialize MT5 terminal")
                    return None

            # Check if we're logged in (connected to account)
            account_info = mt5.account_info()
            if account_info is None:
                logger.warning("Not logged into MT5 account, symbols may not be available")
                # Still try to get symbols, some basic symbols might be available

            symbols = mt5.symbols_get()
            if symbols is None:
                logger.error("Failed to retrieve symbols from MT5")
                return None

            return {symbol.name for symbol in symbols}
        except Exception as ex:
            logger.error(f"Unexpected error in get symbols: {ex}")
            return None

    def __init__(self, path, server, user, password):
        self.path = path
        self.server = server
        self.user = user
        self.password = password

    def login(self) -> bool:
        """Establish connection to MetaTrader 5 terminal"""
        try:
            if mt5.terminal_info() is not None:
                logger.info(f"MT5 terminal already connected for user {self.user}")
                return True

            logger.info(f"Attempting MT5 login for user {self.user} on server {self.server}")
            # establish connection to the MetaTrader 5 terminal
            if not mt5.initialize(path=self.path, login=self.user, server=self.server, password=self.password):
                error_code = mt5.last_error()
                logger.error(f"MT5 login failed for user {self.user}: error code {error_code}")
                return False

            # Verify connection by getting account info
            account_info = mt5.account_info()
            if account_info:
                logger.success(f"MT5 login successful for user {self.user} - Account: {account_info.login}, Balance: {account_info.balance}")
            else:
                logger.warning(f"MT5 login completed for user {self.user} but account info unavailable")

            return True
        except Exception as e:
            logger.error(f"Unexpected error during MT5 login for user {self.user}: {e}")
            return False

    def validate_symbol(self, symbol):
        """Validate and map symbol to correct MT5 format"""
        symbol_list = ConnectionManager.get_symbols()
        symbol = symbol.upper()
        matches = [symbol_mt for symbol_mt in symbol_list if symbol in symbol_mt]
        if not matches:
            return symbol

        cfg = Configure.GetSettings()
        mappings = cfg.get("MetaTrader", {}).get("SymbolMappings", {})

        if symbol in mappings:
            exact = mappings[symbol]
            if exact in symbol_list:
                return exact

        # If not mapped, choose the one without ! or #
        no_suffix = [s for s in matches if '!' not in s and '#' not in s]
        if no_suffix:
            return no_suffix[0]
        # Else first
        return matches[0]

    def check_symbol(self, symbol):
        """Check if symbol is available and select it in Market Watch"""
        logger.info("Check symbol " + symbol)
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            symbol_info = mt5.symbol_info(symbol.upper())
        if symbol_info is None:
            logger.critical(f"not found {symbol}, can not call order_check()")
            mt5.shutdown()
            return False
        # if the symbol is unavailable in MarketWatch, add it
        if not symbol_info.visible:
            logger.debug(symbol, "is not visible, trying to switch on")
            if not mt5.symbol_select(symbol, True):
                logger.critical("symbol_select({}}) failed, exit", symbol)
                mt5.shutdown()
                return False
        return True


class AccountConfig:
    """Configuration class for MetaTrader account settings"""

    def __init__(self, account_dict):
        self.path = account_dict.get('path')
        if not self.path:  # Check if None or empty
            current_path = os.getcwd()
            self.path = os.path.join(current_path, "terminal64.exe")
        # Check if the file exists
        if not os.path.exists(self.path):
            raise FileNotFoundError(
                f"Error: The file does not exist at path: {self.path}")

        self.TakeProfit = account_dict.get('TakeProfit')
        self.server = account_dict.get('server')
        self.username = account_dict.get('username')
        self.password = account_dict.get('password')
        self.lot = account_dict.get('lot')
        self.HighRisk = account_dict.get('HighRisk')
        self.CloserPrice = account_dict.get('CloserPrice')
        self.SaveProfits = account_dict.get('SaveProfits')
        self.account_size = account_dict.get('AccountSize')
        self.expirePendinOrderInMinutes = account_dict.get(
            'expirePendinOrderInMinutes')

