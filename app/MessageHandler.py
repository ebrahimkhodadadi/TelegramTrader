from datetime import datetime
from app.database import Migrations
from loguru import logger
from enum import Enum
from Analayzer import *
import Configure
from MetaTrader import *
import asyncio

def Handle(messageType, text, comment, username, message_id):
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
    
    # save in database
    signal_data = {
        "telegram_channel_title": username,
        "telegram_message_id": message_id,
        "open_price": firstPrice,
        "stop_loss": stopLoss,
        "tp_list": takeProfit,
        "symbol": symbol,
        "current_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    signal_id = Migrations.signal_repo.insert(signal_data)

    # Open Position
    MetaTrader.Trade(actionType, symbol, firstPrice, secondPrice, takeProfit, stopLoss, comment, signal_id)


class MessageType(Enum):
    New = 1
    Edited = 2
    Deleted = 3
