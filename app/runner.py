import asyncio
import Database
from loguru import logger
import Configure
import Helper
from Telegram.Telegram import *
from MetaTrader import *
# import pyfiglet 

async def main():
    try:
        # styled_text=pyfiglet.figlet_format('Telegram Trader',font= 'doom')
        # print(styled_text)
        logger.info("Starting...")

        # Get settings
        cfg = Configure.GetSettings()

        # Check if Telegram can be accessed
        while True:
            if not Helper.can_access_telegram(cfg.Notification.token):
                logger.Error("Can't Access Telegram. Enable your VPN. Try again after 3 seconds...")
                await asyncio.sleep(3)
                continue
            break

        # Configure logger
        Configure.ConfigLogger()

        # Configure notification
        Configure.ConfigNotification(cfg.Notification.token, cfg.Notification.chatId)

        # Perform database migrations
        Database.Migrations.DoMigrations()

        # Start MetaTrader monitoring
        meta_trader_task = asyncio.create_task(MetaTrader.monitor_all_accounts())

        # Start Telegram listener
        telegram_settings = cfg.Telegram
        telegram = Telegram(telegram_settings.api_id, telegram_settings.api_hash)
        telegram_task = asyncio.create_task(telegram.HandleMessages())

        # Wait for both tasks to complete (they won't unless the program is stopped)
        await asyncio.gather(meta_trader_task, telegram_task)

    except KeyboardInterrupt:
        logger.info("Exiting...")
    except Exception as e:
        logger.exception(f"Error while starting bot [app - runner.py]\n{e}")

if __name__ == "__main__":
    asyncio.run(main())
