from loguru import logger
import re
from Analayzer.WordList import *


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
        second_match = re.findall(r'@ \d+\.\d+ - (\d+\.\d+)', message)
        second_number = None
        if not second_match:
            second_match = re.findall(r'-(\d+\.\d+)', message)
        if not second_match:
            second_match = re.findall(r'\d+\.\d+ - (\d+\.\d+)', message)
        if not second_match:
            second_match = re.findall(r'(\d+\/\d+)', message)
            try:
                second_number = float(second_match[0].split('/')[1])
            except:
                pass
        if not second_number:
            second_number = float(second_match[0]) if second_match else None
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
                    r'tp\s*[-:]\s*(\d+\.\d+|\d+)', message, re.IGNORECASE)
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
        sl_numbers = []
        sentences = re.split(r'\n+', message)
        for sentence in sentences:
            words = re.findall(r'\b\d+\b\bsl\b', sentence.lower())
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
                    r'sl\s*[-:]\s*(\d+\.\d+|\d+)', message, re.IGNORECASE)
            if sl_match:
                sl_numbers.append(float(sl_match.group(1)))
            if not sl_numbers:
                if 'sl' in words:
                    index = words.index('sl')
                    if index < len(words) - 1:  # Check if there's a number after "sl"
                        try:
                            sl_numbers.append(int(words[index + 1]))
                        except ValueError:
                            pass  # Ignore if the next word after "sl" is not a number
    except Exception as e:
        logger.error("Can't deserilize message '" +
                     message + "' for sl: \n" + e)
        return None
