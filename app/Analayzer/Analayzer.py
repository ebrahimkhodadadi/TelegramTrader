from enum import Enum
from loguru import logger
import json
import re


def parse_message(message):
    try:
        if message is None or len(message) < 0:
            return None, None, None, None, None, None

        message = message.lower()

        actionType = get_main_word_actiontype(message)
        if actionType is None:
            return None, None, None, None, None
        firstPrice = GetFirstPrice(message)
        secondPrice = GetSecondPrice(message)
        takeProfit = GetTakeProfit(message)
        stopLoss = GetStopLoss(message)
        symbol = GetSymbol(message)
        return actionType, symbol, firstPrice, secondPrice, takeProfit, stopLoss
    except Exception as e:
        logger.error("Error while deserilize message: \n" + e)
        return None, None, None, None, None, None


def GetFirstPrice(message):
    try:
        match = re.findall(r'(\d+(?:\.\d+)?)', message)
        openPrice = None
        if not match:
            match = re.search(r'(\d+\.\d+)', message)
        if not match:
            match = re.findall(r'@ (\d+\.\d+)', message)
        openPrice = float(match[0]) if match else None
        return openPrice
    except Exception as e:
        logger.error("Can't deserilize message '" +
                     message + "' for first price: \n" + e)
        return None


def GetSecondPrice(message):
    try:
        match = re.search(r'@\d+\.?\d*\s*-\s*(\d+\.?\d*)', message)
        if not match:
            match = re.search(r'@\d+\.?\d*\s*-\s*(\d+\.?\d*)', message)
        if not match:
            match = re.search(r'@\s*\d+\.?\d*\s*-\s*(\d+\.?\d*)', message)
        if not match:
            match = re.search(r'@\s*\d+\.?\d*\s*-\s*(\d+\.?\d*)|:\s*\d+\.?\d*\s*-\s*(\d+\.?\d*)', message)
        if not match:
            match = re.search(r'\b\d+\.?\d*\s*-\s*(\d+\.?\d*)', message)
        if not match:
            match = re.search(r'\b\d+\b\s*و\s*(\d+)\s*فروش', message)
        if not match:
            match = re.search(r'\b\d+\b\s*و\s*(\d+)\s*خرید', message)
        if match:
            second_number = float(match.group(1) or match.group(2))
        else:
            second_number = None

        return second_number
    except Exception as e:
        logger.error("Can't deserilize message '" +
                     message + "' for second price: \n" + e)
        return None


def GetTakeProfit(message):
    try:
        tp_numbers = []
        sentences = re.split(r'\n+', message)
        for sentence in sentences:
            words = re.findall(r'\b\d+\b|\btp\b', sentence.lower())
            # Extract TP numbers
            tp_match = re.search(
                r'tp\s*(?:\d*\s*:\s*)?(\d+\.\d+)', sentence, re.IGNORECASE)
            if not tp_match:
                tp_match = re.search(
                    r'tp\s*:\s*(\d+\.?\d*)', sentence, re.IGNORECASE)
            if not tp_match:
                tp_match = re.search(
                    r'tp1\s*:\s*(\d+\.?\d*)', sentence, re.IGNORECASE)
            if not tp_match:
                tp_match = re.search(
                    r'tp1\s*\s*(\d+\.?\d*)', sentence, re.IGNORECASE)
            if not tp_match:
                tp_match = re.search(
                    r'tp\s*[-:]\s*(\d+\.\d+|\d+)', message, re.IGNORECASE)
            if not tp_match:
                tp_match = re.search(
                    r'tp\s*[:\-]?\s*(\d+\.?\d*)', message, re.IGNORECASE)
            if not tp_match:
                tp_match = re.search(
                    r'checkpoint\s*1\s*:\s*(\d+\.?\d*|OPEN)', message, re.IGNORECASE)
            if tp_match:
                tp_numbers.append(float(tp_match.group(1)))
            if not tp_numbers:
                if 'tp' in words:
                    index = words.index('tp')
                    if index < len(words) - 1:  # Check if there's a number after "tp"
                        try:
                            tp_numbers.append(int(words[index + 1]))
                        except ValueError:
                            pass  # Ignore if the next word after "tp" is not a number
        if len(tp_numbers) == 0:
            return None
        return tp_numbers[0]
    except Exception as e:
        logger.error("Can't deserilize message '" +
                     message + "' for tp: \n" + e)
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
                    r'استاپ\s*(\d+\.?\d*)', message, re.IGNORECASE)
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
        logger.error("Can't deserilize message '" +
                     message + "' for sl: \n" + e)
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


def read_symbol_list(json_file_path):
    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)
            return data.get('SymbolList', [])
    except Exception as e:
        logger.exception(
            "An error occurred while reading the symbol list JSON file")
        return []


def GetSymbol(sentence):
    symbol_list = read_symbol_list('data\\Symbols.json')
    words = sentence.split()
    for word in words:
        if word.upper() in symbol_list:
            return word.upper()
        if (word == 'طلا' or
            word == 'gold' or
            word == '#XAUUSD' or
            word == 'انس' or
            word == 'اونس'):
            return 'XAUUSD'

    return None
