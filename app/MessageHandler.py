from loguru import logger
from enum import Enum
from Analayzer import *
def Handle(messageType, text, comment):
    actionType, firstPrice, secondPrice, takeProfit, stopLoss = parse_message(text)
    if actionType is not None:
        print("actionType: ", actionType)

class MessageType(Enum):
    New = 1
    Edited = 2
    Deleted = 3