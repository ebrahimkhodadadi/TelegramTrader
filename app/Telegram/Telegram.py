import logging
from datetime import datetime, timedelta
from telethon.tl.functions.messages import GetHistoryRequest
from loguru import logger
from telethon import TelegramClient, events
from telethon.errors import RPCError, AuthKeyError
from telethon.errors.rpcerrorlist import FloodWaitError, NetworkMigrateError, ServerError
from MessageHandler import *
import Configure
import sys
import asyncio


class Telegram:
    """
Telegram Client Module

This module provides a Telegram client implementation for handling messages and events
from Telegram channels.

Classes:
    Telegram: Main class for handling Telegram client operations

Dependencies:
    - telethon: For Telegram client functionality
    - loguru: For logging
    - Configure: For configuration settings
    - MessageHandler: For message processing

Usage:
    telegram = Telegram(api_id, api_hash)
    await telegram.HandleMessages()
"""

    def __init__(self, api_id, api_hash):
        self.api_id = api_id
        self.api_hash = api_hash
        self.client = TelegramClient(
            'TelegramSession', self.api_id, self.api_hash)

    async def HandleMessages(self):
        sys.stdout.reconfigure(encoding='utf-8')
        logger.info('start listening...')

        while True:
            try:
                await self.client.start()
                logger.info("Client started. Press Ctrl+C to stop.")

                @self.client.on(events.NewMessage)
                async def new_event_handler(event):
                    if event.message.is_reply:
                        replied = await event.message.get_reply_message()
                        if replied:
                            parent_chat_id = clear_chat_id(event.chat_id)
                            parent_msg_id = replied.id
                            message = event.message.message.lower()

                            HandleParentEdit(parent_chat_id, parent_msg_id, message)
                            HandleParentDelete(parent_chat_id, parent_msg_id, message)
                            HandleParentRiskFree(parent_chat_id, parent_msg_id, message)
                    else:
                        await self.HandleEvent(MessageType.New, event)
                    
                @self.client.on(events.MessageEdited)
                async def edit_event_handler(event):
                    chat_id = clear_chat_id(event.chat_id)

                    message_id = event.message.id
                    text = event.message.message.lower()
                    text = text.encode('utf-8', errors='ignore').decode('utf-8')
                    
                    HandleEdite(chat_id, message_id, text)

                @self.client.on(events.MessageDeleted)
                async def delete_event_handler(event):
                    chat_id = clear_chat_id(event.chat_id)

                    for msg_id in event.deleted_ids:
                        HandleDelete(chat_id, msg_id)

                await self.client.run_until_disconnected()

            except (OSError, AuthKeyError, RPCError, FloodWaitError, NetworkMigrateError, ServerError) as e:
                logging.error(f"Connection error: {e}")
                await asyncio.sleep(5)  # Wait before retrying
                logger.info("Retrying connection...")

            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                await asyncio.sleep(5)  # Retry even on unexpected errors

            except KeyboardInterrupt:
                logger.warning("Exiting...")
                break  # Break the loop if manually interrupted

            finally:
                await self.client.disconnect()
                logger.warning("Telegram Client disconnected.")

    async def HandleEvent(self, messageType, event):
        message_link = ""
        username = None
        # get settings
        try:
            username, message_id, message_link, chat_id = await Telegram.GetMessageDetail(event)
        except:
            pass
        # validtor
        cfg = Configure.GetSettings()
        whiteList = cfg.Telegram.channels.whiteList
        if whiteList is not None and whiteList:
            if (username is None or username.lower() not in {str(u).lower() for u in whiteList}) and (str(chat_id) not in whiteList and chat_id not in whiteList):
                return
        blackList = cfg.Telegram.channels.blackList
        if blackList is not None and blackList:
            if (username is None or username.lower() in {str(u).lower() for u in blackList}) or (str(chat_id) in blackList or chat_id in blackList):
                return

        text = event.raw_text.encode('utf-8', errors='ignore').decode('utf-8')

        # open postion
        Handle(messageType, text, message_link, username, message_id, chat_id)

    async def GetMessageDetail(event):
        try:
            chat = await event.get_chat()
            chat_id = chat.id

            if hasattr(chat, 'username') and chat.username:
                username = chat.username
                message_id = event.message.id

                # Construct the message link
                message_link = f"https://t.me/{username}/{message_id}"
            elif hasattr(chat, 'title') and chat.title:
                username = chat.title
                message_id = event.message.id

                # Construct the message link
                message_link = f"{username}/{message_id}"

            return username, message_id, message_link, chat_id
        except:
            return None, None, None

def clear_chat_id(chat_id):
    if chat_id is None:
        return chat_id
    
    # Strip -100 prefix if present
    if str(chat_id).startswith("-100"):
        raw_id = int(str(chat_id)[4:])
    else:
        raw_id = chat_id
        
    return abs(raw_id)