from notifiers import get_notifier
from notifiers.logging import NotificationHandler
from loguru import logger

import Helper

def ConfigNotification(token, chatId):
    params = {
        "token": token,
        "chat_id": chatId
    }
    telegram = get_notifier('telegram')
    telegram.notify(message='Bot Started! \n' + Helper.get_jalali_datetime(), **params)
    handler = NotificationHandler("telegram", defaults=params)
    logger.add(handler)