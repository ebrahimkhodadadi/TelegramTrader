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
        cfg = Configure.GetSettings()
        mtAccount = AccountConfig(cfg["MetaTrader"])
        mt = MetaTrader(
            path=mtAccount.path,
            server=mtAccount.server,
            user=mtAccount.username,
            password=mtAccount.password
        )

        if mt.Login() == False:
            return None

        symbol = mt.validate_symbol("XAUUSD")

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            print(f"symbol_info_tick() failed for {symbol}")
            return None

        server_time = tick.time
        server_time_utc = datetime.utcfromtimestamp(
            server_time).replace(tzinfo=pytz.utc)
        return server_time_utc

    @staticmethod
    def get_symbols():
        """Retrieve all available symbols from MT5"""
        try:
            cfg = Configure.GetSettings()
            account = AccountConfig(cfg["MetaTrader"])
            mt = MetaTrader(
                path=account.path,
                server=account.server,
                user=account.username,
                password=account.password
            )
            if not mt.Login():
                logger.error(f"Failed to login to {mt.server}")
                return None

            symbols = mt5.symbols_get()
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
                return True

            print(f"try to login to {self.server} with {self.user}")
            # establish connection to the MetaTrader 5 terminal
            if not mt5.initialize(path=self.path, login=self.user, server=self.server, password=self.password):
                print("MetaTrader Login failed, error code =",
                      mt5.last_error())
                return False
            print(f"login was successful for {self.user}")
            return True
        except Exception as e:
            print(f"Unexpected error: {e}")
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


# Import here to avoid circular imports
from MetaTrader import MetaTrader