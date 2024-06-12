import json
from loguru import logger
import unittest
from unittest.mock import patch, mock_open
import json
from app.Analayzer import *

def get_messages_from_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
            return data.get("messages", [])
    except Exception as e:
        logger.error("Error reading JSON file: " + str(e))
        return []

class TestGetFirstPrice(unittest.TestCase):
    def test_get_first_price(self):
        # Get messages from the mocked JSON file
        messages = get_messages_from_json('data\\messages.json')
        
        for message in messages:
            #print("\n--> message: \n" + message)
            result = GetFirstPrice(message)
            #print(f"-> GetFirstPrice result: {result}")
            # Check if the result is a float or None
            self.assertTrue(isinstance(result, float), f"Failed on message:\n {message}")
            
class TestGetSecondPrice(unittest.TestCase):
    def test_get_second_price(self):
        # Get messages from the mocked JSON file
        messages = get_messages_from_json('data\\messages.json')
        
        for message in messages:
            # print("\n--> message: \n" + message)
            result = GetSecondPrice(message)
            # print(f"-> GetSecondPrice result: {result}")
            # Check if the result is a float or None
            self.assertTrue(isinstance(result, float), f"Failed on message:\n {message}")
            
class TestGetTakeProfit(unittest.TestCase):
    def test_get_takeprofit(self):
        # Get messages from the mocked JSON file
        messages = get_messages_from_json('data\\messages.json')
        
        for message in messages:
            # print("\n--> message: \n" + message)
            result = GetTakeProfit(message)
            # print(f"-> GetTakeProfit result: {result}")
            # Check if the result is a float or None
            self.assertTrue(isinstance(result, float), f"Failed on message:\n {message}")
            
class TestGetStopLoss(unittest.TestCase):
    def test_get_stoploss(self):
        # Get messages from the mocked JSON file
        messages = get_messages_from_json('data\\messages.json')
        
        for message in messages:
            # print("\n--> message: \n" + message)
            result = GetStopLoss(message)
            # print(f"-> GetStopLoss result: {result}")
            # Check if the result is a float or None
            self.assertTrue(isinstance(result, float), f"Failed on message:\n {message}")

if __name__ == "__main__":
    unittest.main()