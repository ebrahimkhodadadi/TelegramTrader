from loguru import logger
from enum import Enum

def Handle(messageType, text):
    pass

class MessageType(Enum):
    New = 1
    Edited = 2
    Deleted = 3