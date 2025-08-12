from enum import Enum
import unicodedata
from loguru import logger
import json
import re
import os
from MetaTrader import *


def extract_price(message):
    match = re.search(r'@[\s]*([0-9]+(?:\.[0-9]+)?)', message)
    if match:
        return float(match.group(1))
    return None


def parse_message(message):
    try:
        if message is None or len(message) < 0:
            return None, None, None, None, None, None

        message = clean_text(message.lower())

        actionType = get_main_word_actiontype(message)
        if actionType is None:
            return None, None, None, None, None
        firstPrice = GetFirstPrice(message)
        secondPrice = GetSecondPrice(message)
        takeProfits = GetTakeProfits(message)
        stopLoss = GetStopLoss(message)
        symbol = GetSymbol(message)

        if firstPrice == secondPrice or secondPrice in takeProfits or secondPrice == stopLoss:
            secondPrice = None

        return actionType, symbol, firstPrice, secondPrice, takeProfits, stopLoss
    except Exception as e:
        logger.error("Error while deserilize message: \n" + e)
        return None, None, None, None, None, None


def clean_text(text):
    """Normalize text by removing only special Unicode formatting, keeping Persian and new lines."""
    text = unicodedata.normalize("NFKC", text)  # Normalize bold/italic Unicode
    # Remove excessive spaces but keep new lines
    text = re.sub(r'[^\S\r\n]+', ' ', text)
    text = re.sub(r'[☑️❌]', '', text)  # Remove ☑️ and ❌ symbols
    text = re.sub(r'[^\w\s.,:;!?(){}\[\]/\-+=@#%&*\'\"<>]', '', text)
    superscript_map = str.maketrans("¹²³⁴⁵⁶⁷⁸⁹⁰", "1234567890")
    text = text.translate(superscript_map)
    return text.strip()


def GetFirstPrice(message):
    try:
        message = message.upper().replace("US30", "DJIUSD")
        match = re.findall(r'(\d+(?:\.\d+)?)', message)
        openPrice = None
        if not match:
            match = re.search(r'(\d+\.\d+)', message)
        if not match:
            match = re.findall(r'@ (\d+\.\d+)', message)
        openPrice = float(match[0]) if match else None
        return openPrice
    except Exception as e:
        # logger.error("Can't deserilize message '" +
        #              message + "' for first price: \n" + e)
        return None


def GetSecondPrice(message):
    try:
        match = re.search(r'\b\d+\.?\d*///(\d+\.?\d*)',
                          message)  # <--- New pattern added
        if not match:
            match = re.search(r'@\d+\.?\d*\s*-\s*(\d+\.?\d*)', message)
        if not match:
            match = re.search(
                r'2(?:nd)?\s+limit\s*@\s*(\d+\.?\d*)', message, re.IGNORECASE)
        if not match:
            match = re.search(r'\b\d+\.?\d*__+(\d+\.?\d*)', message)
        if not match:
            match = re.search(r'@\s*\d+\.?\d*\s*-\s*(\d+\.?\d*)', message)
        if not match:
            match = re.search(
                r'@\s*\d+\.?\d*\s*-\s*(\d+\.?\d*)|:\s*\d+\.?\d*\s*-\s*(\d+\.?\d*)', message)
        if not match:
            match = re.search(r'\b\d+\.?\d*\s*-\s*(\d+\.?\d*)', message)
        if not match:
            match = re.search(r'\b\d+\b\s*و\s*(\d+)\s*فروش', message)
        if not match:
            match = re.search(r'\b\d+\b\s*و\s*(\d+)\s*خرید', message)
        if not match:
            match = re.search(r'\b\d+\.?\d*/(\d+\.?\d*)', message)
        if not match:
            match = re.search(r'=\s*(\d+\.?\d*)', message)
        if not match:
            match = re.search(r'(?:\d+\.\d+)[^\d]+(\d+\.\d+)', message)
        if match:
            second_number = float(match.group(1) or match.group(2))
        else:
            second_number = None

        return second_number
    except Exception as e:
        return None


def GetTakeProfits(message):
    try:
        tp_numbers = []
        sentences = re.split(r'\n+', message)
        for sentence in sentences:
            # Extract TP numbers for various formats
            tp_match = re.findall(
                r'tp\s*\d*\s*[@:.\-]?\s*(\d+\.\d+|\d+)', sentence, re.IGNORECASE)
            if tp_match and tp_match[0] == '0':
                tp_match = None
            if not tp_match:
                tp_match = re.findall(
                    r'tp\s*(?:\d*\s*:\s*)?(\d+\.\d+)', sentence, re.IGNORECASE)
            if not tp_match:
                tp_match = re.findall(
                    r'\btp\b\s*[:\-@.]?\s*(\d+(?:\.\d+)?)', sentence, re.IGNORECASE)
            if not tp_match:
                tp_match = re.findall(
                    r'tp\s*:\s*(\d+\.?\d*)', sentence, re.IGNORECASE)
            if not tp_match:
                tp_match = re.findall(
                    r'tp1\s*:\s*(\d+\.?\d*)', sentence, re.IGNORECASE)
            if not tp_match:
                tp_match = re.findall(
                    r'tp1\s*\s*(\d+\.?\d*)', sentence, re.IGNORECASE)
            if not tp_match:
                tp_match = re.findall(
                    r'tp\s*[-:]\s*(\d+\.\d+|\d+)', message, re.IGNORECASE)
            if not tp_match:
                tp_match = re.findall(
                    r'tp\s*1\s*[-:]\s*(\d+\.\d+|\d+)', message, re.IGNORECASE)
            if not tp_match:
                tp_match = re.findall(
                    r'checkpoint\s*1\s*:\s*(\d+\.?\d*|OPEN)', message, re.IGNORECASE)
            if not tp_match:
                tp_match = re.findall(
                    r'takeprofit\s*1\s*=\s*(\d+\.\d+|\d+)', message, re.IGNORECASE)
            if not tp_match:
                tp_match = re.findall(
                    r'take\s*profit\s*1\s*:\s*(\d+\.\d+|\d+)', message, re.IGNORECASE)
            # if not tp_match:
            #     tp_match = re.findall(
            #         r'tp\s*(?:\d*[\s:]+)?(\d+\.\d+|\d+)', sentence, re.IGNORECASE)
            if not tp_match:
                tp_match = re.findall(r'تی پی\s*(\d+)', message)
            if tp_match:
                tp_numbers.extend([float(tp) for tp in tp_match])
            else:
                tp_matches = re.findall(
                    r'tp\s*\d*\s*[@:.\-]?\s*(\d+\.\d+|\d+)', sentence, re.IGNORECASE)
                if tp_matches:
                    tp_numbers.extend([float(tp) for tp in tp_matches])

            tp_match_takeprofit = re.findall(
                r'take\s*profit\s*\d+\s*[-:]\s*(\d+\.\d+|\d+)', sentence, re.IGNORECASE)
            if tp_match_takeprofit:
                tp_numbers.extend([float(tp) for tp in tp_match_takeprofit])

            # Add TP2, TP3, TP4, etc., extraction logic
            tp_match_2 = re.findall(
                r'tp(\d+)\s*[:\-]?\s*(\d+\.\d+|\d+)', sentence, re.IGNORECASE)
            if tp_match_2:
                for tp in tp_match_2:
                    tp_numbers.append(float(tp[1]))

            # Check for comma-separated TP values in Persian
            persian_tp_match = re.findall(r'تی پی\s*([\d\s,،]+)', sentence)
            if persian_tp_match:
                persian_tp_numbers = []
                for match in persian_tp_match:
                    persian_tp_numbers.extend(
                        [float(tp.strip()) for tp in re.split(
                            r'[,\s،]+', match) if tp.strip().isdigit() and '/' not in tp]
                    )
                return persian_tp_numbers

        if len(tp_numbers) == 0 or tp_numbers == 1.0:
            return None
        tp_numbers = set(tp_numbers)
        return {tp for tp in tp_numbers if tp != 1.0}
    except Exception as e:
        # logger.error("Can't deserialize message '" +
        #               message + "' for tp: \n" + e)
        return None


def GetStopLoss(message):
    try:
        message = message.lower()
        sl_numbers = []
        sentences = re.split(r'\n+', message)
        # sentences = message.splitlines()
        for sentence in sentences:
            sl_match = re.search(r'sl\s*:\s*(\d+\.\d+)',
                                 sentence, re.IGNORECASE)
            if not sl_match:
                sl_match = re.search(
                    r'sl\s*:\s*(\d+\.?\d*)', sentence, re.IGNORECASE)
            if not sl_match:
                sl_match = re.search(r'(?i)stop\s*(\d+\.?\d*)', sentence)
            if not sl_match:
                sl_match = re.search(
                    r'حد\s*(\d+\.\d+|\d+)', message, re.IGNORECASE)
            if not sl_match:
                sl_match = re.search(
                    r'STOP LOSS\s*:\s*(\d+\.?\d*)', sentence, re.IGNORECASE)
            if not sl_match:
                sl_match = re.search(
                    r'sl\s*[-:]\s*(\d+\.\d+|\d+)', sentence, re.IGNORECASE)
            if not sl_match:
                sl_match = re.search(
                    r'sl\s*[:\-]\s*(\d+\.?\d*)', sentence, re.IGNORECASE)
            if not sl_match:
                sl_match = re.search(
                    r'stop\s*loss\s*[:\-]\s*(\d+\.?\d*)', message, re.IGNORECASE)
            if not sl_match:
                sl_match = re.search(r'sl\s*(\d+\.?\d*)',
                                     message, re.IGNORECASE)
            if not sl_match:
                sl_match = re.search(
                    r'stop\s*loss\s*[@:]\s*(\d+\.?\d*)', message, re.IGNORECASE)
            if not sl_match:
                sl_match = re.search(
                    r'Stoploss\s*=\s*(\d+\.\d+|\d+)', message, re.IGNORECASE)
            if not sl_match:
                sl_match = re.search(
                    r'SL\s*@\s*(\d+\.\d+|\d+)', message, re.IGNORECASE)
            if not sl_match:
                sl_match = re.search(r'(?i)stop\s*loss\s*(\d+)', message)
            if not sl_match:
                sl_match = re.search(
                    r'استاپ\s*(\d+\.?\d*)', message, re.IGNORECASE)
            if not sl_match:
                sl_match = re.search(
                    r'sl[\s.:]*([\d]+\.?\d*)', sentence, re.IGNORECASE)
            if not sl_match:
                sl_match = re.search(
                    r'stop\s*loss\s*(?:point)?\s*[:\-]?\s*(\d+\.\d+|\d+)', message, re.IGNORECASE)
            if sl_match:
                sl_numbers.append(float(sl_match.group(1)))
            if not sl_numbers:
                words = re.findall(r'\b\d+\b\bsl\b', sentence.lower())
                if 'sl' in words:
                    index = words.index('sl')
                    if index < len(words) - 1:  # Check if there's a number after "sl"
                        try:
                            sl_numbers.append(int(words[index + 1]))
                        except ValueError:
                            pass  # Ignore if the next word after "sl" is not a number

            if sl_numbers:
                return sl_numbers[0]
    except Exception as e:
        # logger.error("Can't deserilize message '" +
        #              message + "' for sl: \n" + e)
        return None


def get_main_word_actiontype(sentence):
    buy_list = ['buy', 'بخر', 'خرید', 'بای']
    sell_list = ['sell', 'selll', 'بفروش', 'فروش', 'selling', "𝐒𝐞𝐥𝐥"]

    words = sentence.split()

    for word in words:
        if word.lower() in buy_list or re.search(r"buy", word, re.IGNORECASE):
            return TradeType.Buy
        elif word.lower() in sell_list or re.search(r"sell", word, re.IGNORECASE):
            return TradeType.Sell

    return None


class TradeType(Enum):
    Buy = 1
    Sell = 2


def read_symbol_list():
    root_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', '..'))
    json_file_path = os.path.join(root_dir, "data", "Symbols.json")
    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)
            return data.get('SymbolList', [])
    except Exception as e:
        logger.exception(
            "An error occurred while reading the symbol list JSON file")
        return []


def find_similar_word(word, symbol_list):
    word_upper = word.upper()
    for symbol in symbol_list:
        if word_upper in symbol:
            return symbol  # Return the first match
    return None  # Return None if no match is found


def GetSymbol(sentence):
    symbol_list = MetaTrader.GetSymbols()
    words = sentence.split()
    for word in words:
        word = word.replace("/", "").replace("-", "")
        if word.upper() in symbol_list:
            return find_similar_word(word, symbol_list)
        
    for word in words:
        # Normalize the word by removing slashes and hyphens
        word_normalized = word.replace("/", "").replace("-", "").upper()    

        # XAUUSD check
        if any(x in word_normalized for x in ['طلا', 'GOLD', 'GLD', '#XAUUSD', 'انس', 'گلد', '𝐗𝐀𝐔𝐔𝐒𝐃', 'XAUUSD', 'اونس']):
            return find_similar_word('XAUUSD', symbol_list) 

        # DJUSD check (US30 / Dow Jones)
        if any(x in word_normalized for x in ['US30', 'داوجونز']):
            return find_similar_word('DJIUSD', symbol_list) 

        # EURUSD check
        if any(x in word_normalized for x in ['یورو', 'EURUSD']):
            return find_similar_word('EURUSD', symbol_list) 

        # NASDAQ check
        if 'NASDAQ' in word_normalized:
            return find_similar_word('NDAQ', symbol_list)   

        # OIL check
        if 'OIL' in word_normalized:
            return find_similar_word('OIL', symbol_list)    



        return find_similar_word('XAUUSD', symbol_list)
