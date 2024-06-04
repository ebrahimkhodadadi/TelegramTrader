from loguru import logger


def ConfigLogger():
    # config logger
    logger.add("../Logs/{time:YYYY-MM-DD}.log")
