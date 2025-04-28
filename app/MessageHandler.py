from datetime import datetime
from Database import Migrations
from loguru import logger
from enum import Enum
from Analayzer import *
import Configure
import Helper
from MetaTrader import *
import asyncio


def Handle(messageType, text, comment, username, message_id, chat_id):
    cfg = Configure.GetSettings()
    if getattr(cfg, "Timer", None) is not None:
        if(Helper.is_now_between(cfg.Timer.start, cfg.Timer.end) == False):
            logger.warning(f"Trade Time is finished and it't between {cfg.Timer.start} and {cfg.Timer.end}.")
            return
    
    HandleOpenPosition(messageType, text, comment, username, message_id, chat_id)
    HandleRiskFree(chat_id, text)


def HandleOpenPosition(messageType, text, comment, message_username, message_id, chat_id):
    try:
        actionType, symbol, firstPrice, secondPrice, takeProfits, stopLoss = parse_message(text)
    except:
        return

    if actionType is None:
        return

    logger.success(f"-> New {actionType.name} {symbol} Signal ({comment})")

    if firstPrice is None:
        # logger.error(
        #     f"Can't open position because first price is empty ({comment})")
        return
    if stopLoss is None:
        # logger.error(
        #     f"Can't open position because stoploss is empty ({comment})")
        return
    if symbol is None:
        # logger.error(
        #     f"Can't open position because symbol is empty ({comment})")
        return

    MetaTrader.Trade(message_username, message_id, chat_id, actionType, symbol, firstPrice, secondPrice, takeProfits, stopLoss, comment)


def HandleRiskFree(chat_id, text):
    if 'فری' in text or 'risk free' in text:
        MetaTrader.RiskFreePositions(chat_id)


class MessageType(Enum):
    New = 1
    Edited = 2
    Deleted = 3
