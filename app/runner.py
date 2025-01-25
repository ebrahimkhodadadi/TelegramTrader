import Database
from loguru import logger
import Configure
import Helper
from Telegram.Telegram import *
import asyncio
from MetaTrader import *

try:
    logger.info("Starting...")

    # get settings
    cfg = Configure.GetSettings()
    # check if can access Telegram
    if Helper.can_access_telegram(cfg.Notification.token) == False:
        raise Exception("Can't Access Telegram Enable your VPN.")
    # config logger
    Configure.ConfigLogger()
    # Notification
    Configure.ConfigNotification(
        cfg.Notification.token, cfg.Notification.chatId)

    # migrations
    Database.Migrations.DoMigrations()
    
    # metatrader monitoring 
    #Note: test
    asyncio.run(MetaTrader.Monitor())
    
    # start telegram listener
    telegramSettings = cfg.Telegram
    telegram = Telegram(telegramSettings.api_id, telegramSettings.api_hash)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(telegram.HandleMessages())
except KeyboardInterrupt:
    logger.info("Exiting...")
except Exception as e:
    logger.exception(f"Error while starting bot [app - runner.py]\n{e}")
