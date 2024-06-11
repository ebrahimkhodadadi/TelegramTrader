from loguru import logger
from enum import Enum
from Analayzer import *
import Configure
from MetaTrader import *


def Handle(messageType, text, comment):
    actionType, symbol, firstPrice, secondPrice, takeProfit, stopLoss = parse_message(
        text)
    if actionType is None:
        return

    logger.success(f"-> New {actionType.name} {symbol} Signal ({comment})")

    if firstPrice is None:
        logger.error(
            f"Can't open position because first price is empty ({comment})")
        return
    if stopLoss is None:
        logger.error(
            f"Can't open position because stoploss is empty ({comment})")
        return

    cfg = Configure.GetSettings()

    openPrice = firstPrice
    if secondPrice is not None and len(str(openPrice)) == len(str(secondPrice)):
        openPrice = (firstPrice + secondPrice) / 2
    tp = takeProfit
    if cfg.MetaTrader.TakeProfit is not None and cfg.MetaTrader.TakeProfit != 0:
        tp = openPrice + (cfg.MetaTrader.TakeProfit / 10)

    MetaTrader.Trade(actionType, symbol, openPrice, tp, stopLoss, comment)


class MessageType(Enum):
    New = 1
    Edited = 2
    Deleted = 3
