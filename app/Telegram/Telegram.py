import logging
from loguru import logger
from telethon import TelegramClient, events
from telethon.errors import RPCError, AuthKeyError
from telethon.errors.rpcerrorlist import FloodWaitError, NetworkMigrateError, ServerError
from MessageHandler import *
import Configure

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
                await Telegram.HandleEvent(MessageType.New, event)
            @self.client.on(events.MessageEdited)
            async def edit_event_handler(event):
                # await Telegram.HandleEvent(MessageType.Edited, event)
                logger.trace('message Edited here is the detail: ' + event)
                pass
            @self.client.on(events.MessageDeleted)
            async def delete_event_handler(event):
                # await Telegram.HandleEvent(MessageType.Deleted, event)
                logger.trace('message Deleted here is the detail: ' + event)
                pass

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

    async def HandleEvent(messageType, event):
        # get settings
        username, message_id, message_link =  await Telegram.GetMessageDetail(event)
        # validtor
        cfg = Configure.GetSettings()
        whiteList = cfg.Telegram.channels.whiteList
        if whiteList is not None and whiteList:
            if username not in whiteList:
                return
        blackList = cfg.Telegram.channels.blackList
        if blackList is not None and blackList:
            if username in blackList:
                return
        
        Handle(messageType, event.raw_text, message_link)
    
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