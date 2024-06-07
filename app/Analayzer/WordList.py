from enum import Enum

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