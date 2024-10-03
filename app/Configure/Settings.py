from loguru import logger
from config import config_from_json
from dotenv import load_dotenv
import os

@logger.catch
def GetSettings():
    # Load ENV
    load_dotenv()

    # Load settings
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

    # Load settings
    if os.getenv("ENV") == "development":
        config_file = os.path.join(root_dir, "config", "development.json")
    else:
        config_file = os.path.join(root_dir, "config", "production.json")

    # Load the config file
    cfg = config_from_json(config_file, read_from_file=True)

    return cfg