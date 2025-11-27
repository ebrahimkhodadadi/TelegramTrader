"""Configuration management for TelegramTrader with safe property access"""

import os
from typing import Any, Dict, Optional, List
from loguru import logger
from config import config_from_json
from dotenv import load_dotenv


class SafeConfig:
    """Provides safe access to configuration properties with defaults"""

    def __init__(self, config_data=None):
        self._config = config_data or {}
        self._defaults = self._get_defaults()

    def _get_defaults(self) -> Dict[str, Any]:
        """Define default values for all configuration properties"""
        return {
            # Telegram defaults
            'telegram_api_id': 0,
            'telegram_api_hash': '',
            'telegram_channels_whitelist': [],
            'telegram_channels_blacklist': [],

            # Notification defaults
            'notification_token': '',
            'notification_chat_id': 0,

            # Main config defaults
            'disable_cache': False,

            # MetaTrader defaults
            'mt_server': '',
            'mt_username': 0,
            'mt_password': '',
            'mt_path': os.path.join(os.getcwd(), 'terminal64.exe'),
            'mt_lot': '1%',
            'mt_high_risk': False,
            'mt_save_profits': [25, 25, 25, 25],
            'mt_account_size': None,
            'mt_closer_price': 0.0,
            'mt_expire_pending_orders_minutes': None,
            'mt_close_positions_on_trail': True,
            'mt_symbol_mappings': {},
            'mt_symbols_whitelist': [],
            'mt_symbols_blacklist': [],

            # Timer defaults
            'timer_start': None,
            'timer_end': None,
        }

    def _get_nested_value(self, *keys, default=None):
        """Safely get nested configuration value"""
        current = self._config
        try:
            for key in keys:
                if isinstance(current, dict):
                    current = current.get(key, {})
                elif hasattr(current, key):
                    current = getattr(current, key, {})
                else:
                    return default
            return current if current != {} else default
        except (AttributeError, KeyError, TypeError):
            return default

    # Telegram properties
    @property
    def telegram_api_id(self) -> int:
        return self._get_nested_value('Telegram', 'api_id', self._defaults['telegram_api_id'])

    @property
    def telegram_api_hash(self) -> str:
        return self._get_nested_value('Telegram', 'api_hash', self._defaults['telegram_api_hash'])

    @property
    def telegram_channels_whitelist(self) -> List[str]:
        return self._get_nested_value('Telegram', 'channels', 'whiteList', self._defaults['telegram_channels_whitelist'])

    @property
    def telegram_channels_blacklist(self) -> List[str]:
        return self._get_nested_value('Telegram', 'channels', 'blackList', self._defaults['telegram_channels_blacklist'])

    # Notification properties
    @property
    def notification_token(self) -> str:
        return self._get_nested_value('Notification', 'token', self._defaults['notification_token'])

    @property
    def notification_chat_id(self) -> int:
        return self._get_nested_value('Notification', 'chatId', self._defaults['notification_chat_id'])

    # MetaTrader properties
    @property
    def mt_server(self) -> str:
        return self._get_nested_value('MetaTrader', 'server', self._defaults['mt_server'])

    @property
    def mt_username(self) -> int:
        return self._get_nested_value('MetaTrader', 'username', self._defaults['mt_username'])

    @property
    def mt_password(self) -> str:
        return self._get_nested_value('MetaTrader', 'password', self._defaults['mt_password'])

    @property
    def mt_path(self) -> str:
        path = self._get_nested_value('MetaTrader', 'path', self._defaults['mt_path'])
        if not path or not os.path.exists(path):
            # Try to find terminal64.exe in current directory
            current_dir = os.getcwd()
            default_path = os.path.join(current_dir, 'terminal64.exe')
            if os.path.exists(default_path):
                return default_path
        return path

    @property
    def mt_lot(self) -> str:
        return self._get_nested_value('MetaTrader', 'lot', self._defaults['mt_lot'])

    @property
    def mt_high_risk(self) -> bool:
        return self._get_nested_value('MetaTrader', 'HighRisk', self._defaults['mt_high_risk'])

    @property
    def mt_save_profits(self) -> List[int]:
        return self._get_nested_value('MetaTrader', 'SaveProfits', self._defaults['mt_save_profits'])

    @property
    def mt_account_size(self) -> Optional[float]:
        return self._get_nested_value('MetaTrader', 'AccountSize', self._defaults['mt_account_size'])

    @property
    def mt_closer_price(self) -> float:
        return self._get_nested_value('MetaTrader', 'CloserPrice', self._defaults['mt_closer_price'])

    @property
    def mt_expire_pending_orders_minutes(self) -> Optional[int]:
        return self._get_nested_value('MetaTrader', 'expirePendinOrderInMinutes', self._defaults['mt_expire_pending_orders_minutes'])

    @property
    def mt_close_positions_on_trail(self) -> bool:
        return self._get_nested_value('MetaTrader', 'ClosePositionsOnTrail', self._defaults['mt_close_positions_on_trail'])

    @property
    def mt_symbol_mappings(self) -> Dict[str, str]:
        return self._get_nested_value('MetaTrader', 'SymbolMappings', self._defaults['mt_symbol_mappings'])

    @property
    def mt_symbols_whitelist(self) -> List[str]:
        return self._get_nested_value('MetaTrader', 'symbols', 'whiteList', self._defaults['mt_symbols_whitelist'])

    @property
    def mt_symbols_blacklist(self) -> List[str]:
        return self._get_nested_value('MetaTrader', 'symbols', 'blackList', self._defaults['mt_symbols_blacklist'])

    # Main config properties
    @property
    def disable_cache(self) -> bool:
        return self._get_nested_value('disableCache', self._defaults['disable_cache'])

    # Timer properties
    @property
    def timer_start(self) -> Optional[str]:
        return self._get_nested_value('Timer', 'start', self._defaults['timer_start'])

    @property
    def timer_end(self) -> Optional[str]:
        return self._get_nested_value('Timer', 'end', self._defaults['timer_end'])

    # Legacy compatibility properties (for backward compatibility)
    @property
    def Telegram(self):
        """Legacy Telegram config access"""
        class TelegramConfig:
            def __init__(self, parent):
                self.api_id = parent.telegram_api_id
                self.api_hash = parent.telegram_api_hash
                self.channels = self
            def __getattr__(self, name):
                if name == 'whiteList':
                    return self.__class__.__bases__[0].telegram_channels_whitelist
                elif name == 'blackList':
                    return self.__class__.__bases__[0].telegram_channels_blacklist
                raise AttributeError(f"'TelegramConfig' has no attribute '{name}'")
        return TelegramConfig(self)

    @property
    def Notification(self):
        """Legacy Notification config access"""
        class NotificationConfig:
            def __init__(self, parent):
                self.token = parent.notification_token
                self.chatId = parent.notification_chat_id
        return NotificationConfig(self)

    @property
    def MetaTrader(self):
        """Legacy MetaTrader config access"""
        class MetaTraderConfig:
            def __init__(self, parent):
                self.server = parent.mt_server
                self.username = parent.mt_username
                self.password = parent.mt_password
                self.path = parent.mt_path
                self.lot = parent.mt_lot
                self.HighRisk = parent.mt_high_risk
                self.SaveProfits = parent.mt_save_profits
                self.AccountSize = parent.mt_account_size
                self.CloserPrice = parent.mt_closer_price
                self.expirePendinOrderInMinutes = parent.mt_expire_pending_orders_minutes
                self.ClosePositionsOnTrail = parent.mt_close_positions_on_trail
                self.SymbolMappings = parent.mt_symbol_mappings
                self.symbols = self
            def __getattr__(self, name):
                if name == 'whiteList':
                    return self.__class__.__bases__[0].mt_symbols_whitelist
                elif name == 'blackList':
                    return self.__class__.__bases__[0].mt_symbols_blacklist
                raise AttributeError(f"'MetaTraderConfig' has no attribute '{name}'")
        return MetaTraderConfig(self)

    @property
    def Timer(self):
        """Legacy Timer config access"""
        class TimerConfig:
            def __init__(self, parent):
                self.start = parent.timer_start
                self.end = parent.timer_end
        return TimerConfig(self)


class Settings:
    """Static settings class for global access"""

    _instance = None

    @classmethod
    def get_instance(cls) -> SafeConfig:
        """Get singleton instance of settings"""
        if cls._instance is None:
            try:
                raw_config = cls._load_raw_config()
                cls._instance = SafeConfig(raw_config)
            except Exception as e:
                logger.warning(f"Failed to load configuration, using defaults: {e}")
                cls._instance = SafeConfig()  # Use defaults only
        return cls._instance

    @classmethod
    def _load_raw_config(cls):
        """Load raw configuration from file"""
        # Load environment variables
        load_dotenv()

        # Determine configuration file path
        config_file = cls._get_config_file_path()

        if not os.path.exists(config_file):
            logger.warning(f"Configuration file not found: {config_file}, using defaults")
            return {}

        # Load and parse configuration
        cfg = config_from_json(config_file, read_from_file=True)
        return cfg

    @classmethod
    def _get_config_file_path(cls) -> str:
        """Determine the configuration file path based on environment"""
        env = os.getenv("ENV", "").lower()

        if env == "development":
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            return os.path.join(root_dir, "config", "development.json")
        elif env == "production":
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
            return os.path.join(root_dir, "config", "production.json")
        else:
            # Default to settings.json in current working directory
            current_path = os.getcwd()
            return os.path.join(current_path, "settings.json")

    # Static properties for easy access
    @staticmethod
    def telegram_api_id() -> int:
        return Settings.get_instance().telegram_api_id

    @staticmethod
    def telegram_api_hash() -> str:
        return Settings.get_instance().telegram_api_hash

    @staticmethod
    def telegram_channels_whitelist() -> List[str]:
        return Settings.get_instance().telegram_channels_whitelist

    @staticmethod
    def telegram_channels_blacklist() -> List[str]:
        return Settings.get_instance().telegram_channels_blacklist

    @staticmethod
    def notification_token() -> str:
        return Settings.get_instance().notification_token

    @staticmethod
    def notification_chat_id() -> int:
        return Settings.get_instance().notification_chat_id

    @staticmethod
    def mt_server() -> str:
        return Settings.get_instance().mt_server

    @staticmethod
    def mt_username() -> int:
        return Settings.get_instance().mt_username

    @staticmethod
    def mt_password() -> str:
        return Settings.get_instance().mt_password

    @staticmethod
    def mt_path() -> str:
        return Settings.get_instance().mt_path

    @staticmethod
    def mt_lot() -> str:
        return Settings.get_instance().mt_lot

    @staticmethod
    def mt_high_risk() -> bool:
        return Settings.get_instance().mt_high_risk

    @staticmethod
    def mt_save_profits() -> List[int]:
        return Settings.get_instance().mt_save_profits

    @staticmethod
    def mt_account_size() -> Optional[float]:
        return Settings.get_instance().mt_account_size

    @staticmethod
    def mt_closer_price() -> float:
        return Settings.get_instance().mt_closer_price

    @staticmethod
    def mt_expire_pending_orders_minutes() -> Optional[int]:
        return Settings.get_instance().mt_expire_pending_orders_minutes

    @staticmethod
    def mt_close_positions_on_trail() -> bool:
        return Settings.get_instance().mt_close_positions_on_trail

    @staticmethod
    def mt_symbol_mappings() -> Dict[str, str]:
        return Settings.get_instance().mt_symbol_mappings

    @staticmethod
    def mt_symbols_whitelist() -> List[str]:
        return Settings.get_instance().mt_symbols_whitelist

    @staticmethod
    def mt_symbols_blacklist() -> List[str]:
        return Settings.get_instance().mt_symbols_blacklist

    @staticmethod
    def disable_cache() -> bool:
        return Settings.get_instance().disable_cache

    @staticmethod
    def timer_start() -> Optional[str]:
        return Settings.get_instance().timer_start

    @staticmethod
    def timer_end() -> Optional[str]:
        return Settings.get_instance().timer_end


# Global instance for easy access
settings = Settings.get_instance()

# Backward compatibility aliases
SettingsManager = Settings

# Backward compatibility functions
@logger.catch
def GetSettings():
    """Legacy function for backward compatibility"""
    return Settings.get_instance()