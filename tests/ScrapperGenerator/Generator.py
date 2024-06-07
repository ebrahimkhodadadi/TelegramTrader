import requests
from bs4 import BeautifulSoup
import MetaTrader5 as mt5
from enum import Enum
from loguru import logger
import json
import os

def add_message(new_message, file_path='data.json'):
    # Load existing data
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
    else:
        data = {"messages": []}
    
    # Check if the new message already exists
    if new_message in data["messages"]:
        print("Message already exists.")
        return
    
    # Add new message
    data["messages"].append(new_message)
    
    # Save updated data
    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)
    
    print("Message added successfully.")


def GetPost(url):
    try:
        page = requests.get(url, timeout=5)
        soup = BeautifulSoup(page.content, 'html.parser')
        signalEncoded = soup.find('div', class_='js-message_text')
        if signalEncoded:
            if len(signalEncoded.text) > 0:
                return signalEncoded.get_text(separator="\n")
        else:
            signalEncoded = soup.find('div', class_='js-videosticker')
            if signalEncoded:
                return signalEncoded.text
            signalEncoded = soup.find(
                'div', class_='tgme_widget_message_sticker_wrap media_supported_cont')
            if signalEncoded:
                return signalEncoded.text
            signalEncoded = soup.find(
                'div', class_='tgme_widget_message_video_wrap')
            if signalEncoded:
                return signalEncoded.text
    except KeyboardInterrupt:
        mt5.shutdown()
        logger.warning("exit")
        quit()
    except:
        logger.trace("An exception occurred while GetPost")

    return None

def get_main_word_actiontype(sentence):
    buy_list = ['buy', 'بخر', 'خرید']
    sell_list = ['sell', 'بفروش', 'فروش', 'selling',]

    words = sentence.split()

    for word in words:
        if word.lower() in buy_list:
            return TradeType.Buy
        elif word.lower() in sell_list:
            return TradeType.Sell
    return None


class TradeType(Enum):
    Buy = 1
    Sell = 2


if __name__ == '__main__':
    LastChannelPostId = 21187
    BaseChannelUserName = "Radin_Forex"
    while (True):
        URL = "https://t.me/" + BaseChannelUserName + "/" + str(LastChannelPostId) + "?embed=1&mode=tme"
        logger.info(f"Wait to get signal... ({URL})")

        postText = GetPost(url=URL)
        LastChannelPostId -= 1
        if postText == None:
            continue

        actionType = get_main_word_actiontype(postText)
        if actionType is None:
            continue

        add_message(postText, "tests\\ScrapperGenerator\\data.json")
