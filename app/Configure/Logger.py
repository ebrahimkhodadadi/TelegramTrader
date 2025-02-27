from loguru import logger
import sys
import os
from MetaTrader import *

def add_mt5_time(record):
    record["extra"]["mt5_time"] = MetaTrader.get_mt5_time() or "N/A"
    return record["extra"]["mt5_time"]

def ConfigLogger():
    logger.remove() 
    
    logger.level("DEBUG", color="<blue>")
    logger.level("INFO", color="<green>")
    logger.level("WARNING", color="<yellow>")
    logger.level("ERROR", color="<red>")
    logger.level("CRITICAL", color="<bold red>")

    logger.add(
        sys.stdout, 
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <cyan>{extra[mt5_time]}</cyan> | {level} | {message}",
        filter=add_mt5_time,
        enqueue=True
    )

    # Bind MT5 time dynamically
    # logger.bind(mt5_time=lambda: MetaTrader.get_mt5_time())
    
