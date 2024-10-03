from loguru import logger
from enum import Enum
from Analayzer import *
import Configure
from MetaTrader import *
import asyncio

def Handle(messageType, text, comment):
    try:
        actionType, symbol, firstPrice, secondPrice, takeProfit, stopLoss = parse_message(text)
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
    
    # Open Position
    MetaTraderBetween.Trade(actionType, symbol, firstPrice, secondPrice, takeProfit, stopLoss, comment)
    MetaTrader.Trade(actionType, symbol, firstPrice, secondPrice, takeProfit, stopLoss, comment)


class MessageType(Enum):
    New = 1
    Edited = 2
    Deleted = 3
