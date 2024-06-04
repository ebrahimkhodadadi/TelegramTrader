from loguru import logger
import Configure
import Helper

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
    # telegram = Telegram(telegramSettings.api_id, telegramSettings.api_hash)
except:
    logger.exception("Error while starting bot [app - runner.py]")
