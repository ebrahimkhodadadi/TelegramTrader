import asyncio
import logging
from loguru import logger
from telethon import TelegramClient, events
from telethon.errors import RPCError, AuthKeyError
from telethon.errors.rpcerrorlist import FloodWaitError, NetworkMigrateError, ServerError
from MessageHandler import *


class Telegram:
    def __init__(self, api_id, api_hash):
        self.api_id = api_id
        self.api_hash = api_hash
        self.client = TelegramClient(
            'TelegramSession', self.api_id, self.api_hash)

    async def HandleMessages(self):
        logger.info('start listening...')

        try:
            await self.client.start()
            logger.info("Client started. Press Ctrl+C to stop.")

            @self.client.on(events.NewMessage)
            async def new_event_handler(event):
                Handle(MessageType.New, event.raw_text)
            @self.client.on(events.MessageEdited)
            async def edit_event_handler(event):
                Handle(MessageType.Edited, event.raw_text)
            @self.client.on(events.MessageDeleted)
            async def delete_event_handler(event):
                Handle(MessageType.Deleted, event.raw_text)

            await self.client.run_until_disconnected()
        except (OSError, AuthKeyError, RPCError, FloodWaitError, NetworkMigrateError, ServerError) as e:
            logging.error(f"Connection error: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
        except KeyboardInterrupt:
            logger.warning("Exiting...")
        finally:
            self.client.disconnect()
            logger.warning("Telegram Client disconnected.")

    async def GetMessageDetail(event):
        try:
            chat = await event.get_chat()
            if hasattr(chat, 'username') and chat.username:
                username = chat.username
                message_id = event.message.id

                # Construct the message link
                message_link = f"https://t.me/{username}/{message_id}"
                return username, message_id, message_link
        except:
            return None, None, None