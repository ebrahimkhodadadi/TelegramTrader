"""Integration tests for analyzer functionality"""

import unittest
import json
from tests.fixtures import TestBase, analyzer_test_data
from app.Analayzer import parse_message, extract_price


class TestAnalyzerIntegration(TestBase):
    """Integration tests for analyzer functionality"""

    def get_messages_from_json(self, file_path):
        """Load messages from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
                return data.get("messages", [])
        except Exception as e:
            self.logger.error("Error reading JSON file: " + str(e))
            return []

    def test_parse_message_with_test_data(self):
        """Test parsing messages using analyzer_test_data"""
        for test_case in analyzer_test_data:
            with self.subTest(input=test_case["input"]):
                result = parse_message(test_case["input"])

                if test_case["expected"]["action"] == "BUY":
                    self.assertEqual(result[0].name, "Buy")
                elif test_case["expected"]["action"] == "SELL":
                    self.assertEqual(result[0].name, "Sell")

                self.assertEqual(result[1], test_case["expected"]["symbol"])
                self.assertEqual(result[2], test_case["expected"]["price"])
                self.assertEqual(result[3], None)  # second_price
                self.assertEqual(result[5], test_case["expected"]["sl"])

                if test_case["expected"]["tp"]:
                    expected_tp = set(test_case["expected"]["tp"])
                    self.assertEqual(result[4], expected_tp)

    def test_extract_price_functionality(self):
        """Test extract_price function"""
        test_cases = [
            ("BUY EURUSD @ 1.0850", 1.0850),
            ("SELL XAUUSD @ 1950.50", 1950.50),
            ("No price here", None),
            ("@ 1.2345 somewhere", 1.2345)
        ]

        for text, expected in test_cases:
            with self.subTest(text=text):
                result = extract_price(text)
                self.assertEqual(result, expected)

    def test_parse_message_error_handling(self):
        """Test parse_message error handling"""
        error_cases = [
            None,
            "",
            "Random text without trading signal",
            "BUY",  # Incomplete signal
            "SELL EURUSD",  # Missing price
        ]

        for case in error_cases:
            with self.subTest(case=case):
                result = parse_message(case)
                self.assertEqual(result, (None, None, None, None, None, None))

    def test_parse_message_return_types(self):
        """Test that parse_message returns correct types"""
        result = parse_message("BUY EURUSD @ 1.0850 SL: 1.0800 TP: 1.0900")

        # Check return types
        self.assertIsNotNone(result[0])  # action_type
        self.assertIsInstance(result[1], str)  # symbol
        self.assertIsInstance(result[2], float)  # first_price
        # second_price can be None or float
        # take_profits can be None or set
        self.assertIsInstance(result[5], float)  # stop_loss

    def test_complex_signal_parsing(self):
        """Test parsing of complex real-world signals"""
        complex_signals = [
            "BUY EURUSD @ 1.0850\nSL: 1.0800\nTP1: 1.0900\nTP2: 1.0950\nTP3: 1.1000",
            "SELL XAUUSD @ 1950.50\nStop Loss: 1945.00\nTake Profit: 1960.00, 1970.00, 1980.00",
            "خرید یورو @ ۱.۰۸۵۰\nحد ضرر: ۱.۰۸۰۰\nتی پی: ۱.۰۹۰۰، ۱.۰۹۵۰"
        ]

        for signal in complex_signals:
            with self.subTest(signal=signal[:50] + "..."):
                result = parse_message(signal)
                self.assertIsNotNone(result[0])  # Should detect action
                self.assertIsNotNone(result[1])  # Should detect symbol
                self.assertIsNotNone(result[2])  # Should detect price
                self.assertIsNotNone(result[5])  # Should detect SL


if __name__ == '__main__':
    unittest.main()