"""Configuration management for TelegramTrader"""

import os
from typing import Any, Dict
from loguru import logger
from config import config_from_json
from dotenv import load_dotenv


class SettingsManager:
    """Manages application configuration loading and validation"""

    @staticmethod
    def get_settings() -> Dict[str, Any]:
        """Load and return application settings from configuration file

        Returns:
            Dict containing parsed configuration

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            Exception: If configuration loading fails
        """
        try:
            # Load environment variables
            load_dotenv()

            # Determine configuration file path
            config_file = SettingsManager._get_config_file_path()

            if not os.path.exists(config_file):
                error_msg = f"Configuration file not found: {config_file}"
                logger.critical(error_msg)
                raise FileNotFoundError(error_msg)

            logger.info(f"Loading configuration from: {config_file}")

            # Load and parse configuration
            cfg = config_from_json(config_file, read_from_file=True)

            logger.success("Configuration loaded successfully")
            return cfg

        except Exception as e:
            logger.critical(f"Failed to load configuration: {e}")
            raise

    @staticmethod
    def _get_config_file_path() -> str:
        """Determine the configuration file path based on environment

        Returns:
            Path to the configuration file
        """
        # Check environment variable for config selection
        env = os.getenv("ENV", "").lower()

        if env == "development":
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            return os.path.join(root_dir, "config", "development.json")
        elif env == "production":
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            return os.path.join(root_dir, "config", "production.json")
        else:
            # Default to settings.json in current working directory
            current_path = os.getcwd()
            return os.path.join(current_path, "settings.json")


# Backward compatibility function
@logger.catch
def GetSettings():
    """Legacy function for backward compatibility"""
    return SettingsManager.get_settings()