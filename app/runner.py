import Telegram
import MetaTrader
from config import config_from_json
import os
from dotenv import load_dotenv
from pathlib import Path
from loguru import logger
from notifiers import get_notifier
from notifiers.logging import NotificationHandler
from jdatetime import datetime as jdatetime


@logger.catch
def GetSettings():
    # Load ENV
    load_dotenv()

    # Load settings
    if (os.getenv("ENV") == "development"):
        cfg = config_from_json(
            "..\config\development.json", read_from_file=True)
    else:
        cfg = config_from_json(
            "..\config\production.json", read_from_file=True)

    return cfg


def ConfigLogger():
    # config logger
    logger.add("../Logs/{time:YYYY-MM-DD}.log")


def ConfigNotification(token, chatId):
    params = {
        "token": token,
        "chat_id": chatId
    }
    telegram = get_notifier('telegram')
    telegram.notify(message='Bot Started! ', **params)
    handler = NotificationHandler("telegram", defaults=params)
    logger.add(handler, level="ERROR")


try:
    logger.info("Starting...")

    # get settings
    cfg = GetSettings()
    # config logger
    ConfigLogger()
    #Notification
    ConfigNotification(cfg.Notification.token, cfg.Notification.chatId)

    # start telegram listener
    telegramSettings = cfg.Telegram
    # telegram = Telegram(telegramSettings.api_id, telegramSettings.api_hash)
except:
    logger.exception("Error while starting bot [app - runner.py]")
