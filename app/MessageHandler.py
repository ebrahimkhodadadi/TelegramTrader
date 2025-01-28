from datetime import datetime
from Database import Migrations
from loguru import logger
from enum import Enum
from Analayzer import *
import Configure
from MetaTrader import *
import asyncio


def Handle(messageType, text, comment, username, message_id):
    HandleOpenPosition(messageType, text, comment, username, message_id)
    HandleRiskFree(username, text)


def HandleOpenPosition(messageType, text, comment, message_username, message_id):
    try:
        actionType, symbol, firstPrice, secondPrice, takeProfits, stopLoss = parse_message(
            text)
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

    MetaTrader.Trade(message_username, message_id,actionType, symbol, firstPrice, secondPrice, takeProfits, stopLoss, comment)


def HandleRiskFree(message_username, text):
    if "ریسک فری" not in text or "risk free" not in text:
        return
    MetaTrader.CloseLastSignalPositions(message_username)


class MessageType(Enum):
    New = 1
    Edited = 2
    Deleted = 3
