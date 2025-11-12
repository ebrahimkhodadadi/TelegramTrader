"""Mock data and fixtures for testing"""

from unittest.mock import MagicMock
from datetime import datetime

# Sample trading signals
sample_signals = [
    "BUY EURUSD @ 1.0850\nSL: 1.0800\nTP: 1.0900, 1.0950",
    "SELL XAUUSD @ 1950.50\nStop Loss: 1945.00\nTake Profit: 1960.00",
    "خرید یورو @ ۱.۰۸۵۰\nحد ضرر: ۱.۰۸۰۰\nتی پی: ۱.۰۹۰۰",
    "BUY GBPUSD\nEntry: 1.2650\nSL: 1.2600\nTP1: 1.2700\nTP2: 1.2750"
]

# Mock MT5 position object
def create_mock_position(ticket=12345, symbol="EURUSD", price_open=1.0850,
                        price_current=1.0870, sl=1.0800, tp=1.0900,
                        volume=0.01, type=0):  # 0 = BUY, 1 = SELL
    """Create a mock MT5 position object"""
    position = MagicMock()
    position.ticket = ticket
    position.symbol = symbol
    position.price_open = price_open
    position.price_current = price_current
    position.sl = sl
    position.tp = tp
    position.volume = volume
    position.type = type
    position.magic = 2025
    return position

# Mock MT5 order object
def create_mock_order(ticket=12346, symbol="EURUSD", price_open=1.0850,
                     sl=1.0800, tp=1.0900, volume=0.01, type=0):
    """Create a mock MT5 order object"""
    order = MagicMock()
    order.ticket = ticket
    order.symbol = symbol
    order.price_open = price_open
    order.sl = sl
    order.tp = tp
    order.volume_current = volume
    order.type = type
    order.magic = 2025
    return order

# Sample positions for testing
sample_positions = [
    create_mock_position(ticket=12345, symbol="EURUSD", price_open=1.0850,
                        price_current=1.0870, sl=1.0800, tp=1.0900, type=0),
    create_mock_position(ticket=12346, symbol="XAUUSD", price_open=1950.50,
                        price_current=1948.00, sl=1945.00, tp=1960.00, type=1),
]

# Mock Telegram message
def create_mock_telegram_message(text="BUY EURUSD @ 1.0850", message_id=123,
                                chat_id=456, username="test_channel"):
    """Create a mock Telegram message object"""
    message = MagicMock()
    message.message = text
    message.id = message_id
    message.chat_id = chat_id

    # Mock chat object
    chat = MagicMock()
    chat.username = username
    chat.id = chat_id
    chat.title = f"Channel {username}"

    message.get_chat = MagicMock(return_value=chat)
    message.is_reply = False

    return message

# Mock database signal record
sample_signal_record = {
    "id": 1,
    "telegram_channel_title": "test_channel",
    "telegram_message_id": 123,
    "telegram_message_chatid": 456,
    "open_price": 1.0850,
    "second_price": None,
    "stop_loss": 1.0800,
    "tp_list": "1.0900,1.0950",
    "symbol": "EURUSD",
    "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

# Mock database position record
sample_position_record = {
    "id": 1,
    "signal_id": 1,
    "position_id": 12345,
    "user_id": 123456,
    "is_first": True,
    "is_second": False
}

# Configuration samples
sample_config = {
    "Telegram": {
        "api_id": 123456,
        "api_hash": "test_hash",
        "channels": {
            "whiteList": ["test_channel"],
            "blackList": []
        }
    },
    "Notification": {
        "token": "123456:test_token",
        "chatId": 789
    },
    "MetaTrader": {
        "server": "TestServer",
        "username": 123456,
        "password": "test_password",
        "path": "C:/test/terminal.exe",
        "lot": "0.01",
        "HighRisk": False,
        "SaveProfits": [25, 25, 25, 25],
        "AccountSize": 10000
    }
}

# Test data for analyzer
analyzer_test_data = [
    {
        "input": "BUY EURUSD @ 1.0850\nSL: 1.0800\nTP: 1.0900, 1.0950",
        "expected": {
            "action": "BUY",
            "symbol": "EURUSD",
            "price": 1.0850,
            "sl": 1.0800,
            "tp": [1.0900, 1.0950]
        }
    },
    {
        "input": "SELL XAUUSD @ 1950.50\nStop Loss: 1945.00",
        "expected": {
            "action": "SELL",
            "symbol": "XAUUSD",
            "price": 1950.50,
            "sl": 1945.00,
            "tp": None
        }
    }
]