from loguru import logger
import sys

def ConfigLogger():
    # logger.add(sys.stderr, format="{time:MMMM D, YYYY > HH:mm:ss!UTC} | {level} | {message}")

    # config logger
    logger.add("../Logs/{time:YYYY-MM-DD}.log")
