"""
TelegramTrader Application Runner

This module serves as the main entry point for the TelegramTrader application.
It orchestrates the startup sequence, initializes all components, and manages
the main event loop for trading operations.

Features:
    - Structured startup sequence with validation
    - Component initialization and health checks
    - Graceful error handling and recovery
    - Concurrent task management
    - Clean shutdown procedures
"""

import asyncio
import signal
import sys
from typing import NoReturn
from loguru import logger

from Configure import GetSettings, ConfigLogger, ConfigNotification
from Database import DoMigrations
from Helper import can_access_telegram
from Telegram.Telegram import TelegramClientManager
from MetaTrader import monitor_all_accounts
from MessageHandler import ConcurrentOperationProcessor


class ApplicationRunner:
    """Main application runner for TelegramTrader"""

    def __init__(self):
        self.settings = None
        self.telegram_client = None
        self.shutdown_event = asyncio.Event()

    async def run(self) -> NoReturn:
        """
        Main application entry point.

        Initializes all components and starts the main event loop.
        Handles graceful shutdown on interruption.
        """
        try:
            # Display startup banner
            self._display_startup_banner()

            # Initialize application
            await self._initialize_application()

            # Start main services
            await self._start_services()

        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            await self._shutdown()
        except Exception as e:
            logger.critical(f"Critical error during application startup: {e}")
            await self._shutdown()
            sys.exit(1)

    def _display_startup_banner(self) -> None:
        """Display application startup banner"""
        banner = """
╔══════════════════════════════════════╗
║           TelegramTrader              ║
║     Automated Trading Bot            ║
╚══════════════════════════════════════╝
        """
        print(banner)
        logger.info("Initializing TelegramTrader...")

    async def _initialize_application(self) -> None:
        """Initialize all application components in proper order"""
        logger.info("Starting application initialization...")

        # Load configuration
        await self._load_configuration()

        # Validate connectivity
        await self._validate_connectivity()

        # Initialize components
        await self._initialize_components()

        # Setup shutdown handlers
        self._setup_signal_handlers()

        logger.success("Application initialization completed")

    async def _load_configuration(self) -> None:
        """Load and validate application configuration"""
        # logger.info("Loading configuration...")
        try:
            self.settings = GetSettings()
            # logger.success("Configuration loaded successfully")
        except Exception as e:
            logger.critical(f"Failed to load configuration: {e}")
            raise

    async def _validate_connectivity(self) -> None:
        """Validate external service connectivity"""
        logger.info("Validating connectivity...")

        # Check Telegram access
        await self._check_telegram_connectivity()

        logger.success("Connectivity validation completed")

    async def _check_telegram_connectivity(self) -> None:
        """Check if Telegram API is accessible"""
        max_retries = 5
        retry_delay = 3

        for attempt in range(max_retries):
            try:
                token = self.settings.Notification.token
                if can_access_telegram(token):
                    logger.success("Telegram API access confirmed")
                    return
                else:
                    logger.warning(f"Telegram API access check failed (attempt {attempt + 1}/{max_retries})")

            except Exception as e:
                logger.warning(f"Error checking Telegram connectivity: {e}")

            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)

        # If we get here, all retries failed
        error_msg = "Unable to access Telegram API after multiple attempts. Please check your internet connection and API credentials."
        logger.critical(error_msg)
        raise ConnectionError(error_msg)

    async def _initialize_components(self) -> None:
        """Initialize all application components"""
        logger.info("Initializing components...")

        # Configure logging
        ConfigLogger()

        # Configure notifications
        ConfigNotification(
            self.settings.Notification.token,
            self.settings.Notification.chatId
        )

        # Initialize database
        DoMigrations()

        logger.success("Component initialization completed")

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            self.shutdown_event.set()

        # Handle common termination signals
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Handle shutdown event in event loop
        asyncio.create_task(self._monitor_shutdown())

    async def _monitor_shutdown(self) -> None:
        """Monitor shutdown event and initiate graceful shutdown"""
        await self.shutdown_event.wait()
        await self._shutdown()

    async def _start_services(self) -> NoReturn:
        """Start main application services"""
        logger.info("Starting main services...")

        # Create service tasks
        tasks = await self._create_service_tasks()

        # Start services concurrently
        logger.success("All services started. TelegramTrader is now active.")
        logger.info("Press Ctrl+C to stop")

        try:
            # Wait for all tasks (they run indefinitely until shutdown)
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Error in service execution: {e}")
        finally:
            await self._shutdown()

    async def _create_service_tasks(self) -> list:
        """Create and return main service tasks"""
        tasks = []

        # MetaTrader monitoring task
        logger.info("Starting MetaTrader monitoring service...")
        mt_task = asyncio.create_task(monitor_all_accounts())
        tasks.append(mt_task)

        # Telegram monitoring task
        logger.info("Starting Telegram monitoring service...")
        telegram_settings = self.settings.Telegram
        self.telegram_client = TelegramClientManager(
            telegram_settings.api_id,
            telegram_settings.api_hash
        )
        telegram_task = asyncio.create_task(self.telegram_client.start_monitoring())
        tasks.append(telegram_task)

        return tasks

    async def _shutdown(self) -> None:
        """Perform graceful application shutdown"""
        logger.info("Initiating graceful shutdown...")

        try:
            # Close Telegram client
            if self.telegram_client:
                logger.info("Closing Telegram client...")
                # Client handles its own disconnection

            # Shutdown concurrent operation processor
            logger.info("Shutting down concurrent operation processor...")
            ConcurrentOperationProcessor.shutdown()

            logger.success("Application shutdown completed")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        finally:
            # Ensure event loop stops
            asyncio.get_event_loop().stop()


async def main() -> NoReturn:
    """Main application entry point"""
    runner = ApplicationRunner()
    await runner.run()


if __name__ == "__main__":
    """Script entry point"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")
        sys.exit(1)
