from loguru import logger
import sys
import os

def ConfigLogger():
    # logger.add(sys.stderr, format="{time:MMMM D, YYYY > HH:mm:ss!UTC} | {level} | {message}")

    # config logger
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    log_file = os.path.join(root_dir, "Logs", "{time:YYYY-MM-DD}.log")
    logger.add(log_file)
