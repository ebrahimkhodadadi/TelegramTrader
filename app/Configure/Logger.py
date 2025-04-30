from loguru import logger
import sys
import os
from datetime import datetime
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

    # Ensure the log folder exists
    log_folder = "log"
    os.makedirs(log_folder, exist_ok=True)

    # Create filename based on current date
    log_filename = datetime.now().strftime("%Y-%m-%d") + ".log"
    log_path = os.path.join(log_folder, log_filename)

    # Log to stdout
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <cyan>{extra[mt5_time]}</cyan> | {level} | {message}",
        filter=add_mt5_time,
        enqueue=True
    )

    # Log to file
    logger.add(
        log_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {extra[mt5_time]} | {level} | {message}",
        filter=add_mt5_time,
        rotation="00:00",  # Optional: rotates daily
        retention="7 days",  # Optional: keep logs for 7 days
        compression="zip",  # Optional: compress old logs
        enqueue=True
    )
