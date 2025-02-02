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
                    await self.HandleEvent(MessageType.New, event)

                @self.client.on(events.MessageEdited)
                async def edit_event_handler(event):
                    # username, message_id, message_link = await Telegram.GetMessageDetail(event)
                    # logger.warning(f"message Edited here is the link: {message_link}")
                    pass

                @self.client.on(events.MessageDeleted)
                async def delete_event_handler(event):
                    pass

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
            if (username is None or username.lower() not in {u.lower() for u in whiteList}) and (str(chat_id) not in whiteList and chat_id not in whiteList):
                return
        blackList = cfg.Telegram.channels.blackList
        if blackList is not None and blackList:
            if (username is None or username.lower() in {u.lower() for u in blackList}) or (str(chat_id) in blackList or chat_id in blackList):
                return

        text = event.raw_text.encode('utf-8', errors='ignore').decode('utf-8')
        # send signal to a channel
        # try:
        #     # Bug: fix already exist position telegram
        #     await self.SendMessage(text)
        # except:
        #     pass

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

    async def SendMessage(self, text):
        try:
            try:
                actionType, symbol, firstPrice, secondPrice, takeProfit, stopLoss = parse_message(
                    text)
                if actionType is None or firstPrice is None or stopLoss is None or symbol is None or takeProfit is None:
                    return
            except:
                return

            if actionType.value == 1:  # buy
                actionType = "Buy"
            elif actionType.value == 2:  # sell
                actionType = "Sell"

            if await self.check_duplicate_signal(symbol, firstPrice, stopLoss, takeProfit):
                return

            # Send signal to channel
            cfg = Configure.GetSettings()

            if secondPrice is not None:
                firstPrice = str(firstPrice) + " - " + str(secondPrice)

            message_template = {
                "message": "🚀 **Forex Signal Alert!** 🚀\n\n"
                "**Pair:** {pair}\n"
                "**Action:** {action}\n"
                "**Entry Price:** {entry_price}\n"
                "**Stop Loss:** {stop_loss}\n"
                "**Take Profit:** {take_profit}\n\n"
                "Join our channel for more signals and updates!\n\n"
                "{channel_link}"
            }

            formatted_message = message_template["message"].format(
                pair=symbol,
                action=actionType,
                entry_price=firstPrice,
                stop_loss=stopLoss,
                take_profit=takeProfit,
                channel_link='@'+cfg.Telegram.SignalChannel
            )

            await self.client.send_message(entity=cfg.Telegram.SignalChannel, message=formatted_message)
        except Exception as e:
            logger.exception(f"Error while SendMessage\n{e}")

    async def check_duplicate_signal(self, symbol, entry_price, stop_loss, take_profit):
        try:
            cfg = Configure.GetSettings()

            # Get channel entity
            channel_entity = await self.client.get_input_entity(cfg.Telegram.SignalChannel)

            # Calculate time boundaries for the last 2 hour
            now = datetime.now()
            last_hour = now - timedelta(hours=2)

            # Get messages from the last hour
            messages = await self.client(GetHistoryRequest(
                peer=channel_entity,
                offset_id=0,
                offset_date=last_hour,
                add_offset=0,
                limit=100,
                max_id=0,
                min_id=0,
                hash=0
            ))

            # Check if there are any messages matching the signal parameters
            for message in messages.messages:
                if message is None or message.message is None:
                    continue
                if (str(symbol) in message.message and
                    str(entry_price) in message.message and
                    str(stop_loss) in message.message and
                        str(take_profit) in message.message):
                    return True

            return False
        except Exception as e:
            logger.exception("Error while checking duplicate signal\n"+str(e))
