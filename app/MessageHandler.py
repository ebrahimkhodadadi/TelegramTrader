from datetime import datetime
from Database import Migrations
from loguru import logger
from enum import Enum
from Analayzer import *
import Configure
import Database
import Helper
from MetaTrader import *
import asyncio


def Handle(messageType, text, comment, username, message_id, chat_id):
    HandleRiskFree(chat_id, text)
    HandleLastEdite(chat_id, text)
    
    cfg = Configure.GetSettings()
    if getattr(cfg, "Timer", None) is not None:
        if(Helper.is_now_between(cfg.Timer.start, cfg.Timer.end) == False):
            logger.warning(f"Trade Time is finished and it't between {cfg.Timer.start} and {cfg.Timer.end}.")
            return
    
    HandleOpenPosition(messageType, text, comment, username, message_id, chat_id)


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
        
def HandleLastEdite(chat_id, text):
    if 'edite' in text or 'update' in text:
        stop_loss = extract_price(text)
        if stop_loss is None:
            return
        MetaTrader.Update_last_signal(chat_id, stop_loss)
def HandleParentEdit(chat_id, message_id, text):
    if 'edite' in text or 'update' in text:
        stop_loss = extract_price(text)
        if stop_loss is None:
            return
        signal = Database.Migrations.get_signal_by_chat(chat_id, message_id)
        if signal is None:
            return
        MetaTrader.Update_signal(signal["id"], stop_loss)
def HandleEdite(chat_id, message_id, message):
    signal = Database.Migrations.get_signal_by_chat(chat_id, message_id)
    if signal is None:
        return
    try:
        actionType, symbol, firstPrice, secondPrice, takeProfits, stopLoss = parse_message(message)
    except:
        return
    
    MetaTrader.Update_signal(signal["id"], stopLoss)
    
def HandleParentDelete(chat_id, message_id, text):
    if 'حذف' in text or 'delete' in text or 'close' in text:
        signal = Database.Migrations.get_signal_by_chat(chat_id, message_id)
        if signal is None:
            return
        MetaTrader.delete_signal(signal["id"])
def HandleDelete(chat_id, message_id):
    signal = Database.Migrations.get_signal_by_chat(chat_id, message_id)
    if signal is None:
        return

    MetaTrader.delete_signal(signal["id"])
    
        
class MessageType(Enum):
    New = 1
    Edited = 2
    Deleted = 3
