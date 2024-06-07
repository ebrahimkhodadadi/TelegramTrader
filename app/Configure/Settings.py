from loguru import logger
from config import config_from_json
from dotenv import load_dotenv
import os

@logger.catch
def GetSettings():
    # Load ENV
    load_dotenv()

    # Load settings
    if (os.getenv("ENV") == "development"):
        cfg = config_from_json(
            "config\development.json", read_from_file=True)
    else:
        cfg = config_from_json(
            "config\production.json", read_from_file=True)

    return cfg