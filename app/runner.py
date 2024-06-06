from loguru import logger
import Configure
import Helper
from Telegram.Telegram import *
import asyncio


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
    Configure.ConfigNotification(cfg.Notification.token, cfg.Notification.chatId)

    # start telegram listener
    telegramSettings = cfg.Telegram
    telegram = Telegram(telegramSettings.api_id, telegramSettings.api_hash)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(telegram.HandleMessages())
except:
    logger.exception("Error while starting bot [app - runner.py]")
