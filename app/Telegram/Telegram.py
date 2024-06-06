import asyncio
import logging
from loguru import logger
from telethon import TelegramClient, events
from telethon.errors import RPCError, AuthKeyError
from telethon.errors.rpcerrorlist import FloodWaitError, NetworkMigrateError, ServerError

logging.basicConfig(level=logging.INFO)


class Telegram:
    def __init__(self, api_id, api_hash):
        self.api_id = api_id
        self.api_hash = api_hash
        self.client = TelegramClient('anon', self.api_id, self.api_hash)

    async def HandleMessages(self):
        #logger.info('start listening...')
    
        try:
            await self.client.start()
            me = await self.client.get_me()
            print(me.stringify())
            await self.client.run_until_disconnected()
        except (OSError, AuthKeyError, RPCError, FloodWaitError, NetworkMigrateError, ServerError) as e:
            logging.error(f"Connection error: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
