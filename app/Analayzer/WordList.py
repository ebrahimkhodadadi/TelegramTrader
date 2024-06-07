from enum import Enum
from loguru import logger
import json

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
        logger.exception("An error occurred while reading the symbol list JSON file")
        return []
    
def GetSymbol(sentence):
    symbol_list = read_symbol_list('data\\Symbols.json')
    words = sentence.split()
    for word in words:
        if word.lower() in symbol_list:
            return word
        if (word == 'طلا' or 
            word == 'gold' or
            word == 'انس'):
            return 'XAUUSD'
        
    return None