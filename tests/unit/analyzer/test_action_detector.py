"""Unit tests for action detection functionality"""

import unittest
from tests.fixtures import TestBase
from app.Analayzer.detectors.action_detector import ActionDetector, TradeType


class TestActionDetector(TestBase):
    """Test cases for ActionDetector class"""

    def test_detect_buy_action_english(self):
        """Test BUY action detection in English"""
        text = "BUY EURUSD @ 1.0850"
        result = ActionDetector.detect_action_type(text)
        self.assertEqual(result, TradeType.Buy)

    def test_detect_sell_action_english(self):
        """Test SELL action detection in English"""
        text = "SELL XAUUSD @ 1950.50"
        result = ActionDetector.detect_action_type(text)
        self.assertEqual(result, TradeType.Sell)

    def test_detect_buy_action_persian(self):
        """Test BUY action detection in Persian"""
        text = "خرید یورو @ ۱.۰۸۵۰"
        result = ActionDetector.detect_action_type(text)
        self.assertEqual(result, TradeType.Buy)

    def test_detect_sell_action_persian(self):
        """Test SELL action detection in Persian"""
        text = "فروش طلا @ ۱۹۵۰"
        result = ActionDetector.detect_action_type(text)
        self.assertEqual(result, TradeType.Sell)

    def test_detect_buy_action_variations(self):
        """Test BUY action detection with variations"""
        buy_signals = [
            "BUY GBPUSD",
            "بخر EURUSD",
            "خرید XAUUSD",
            "بای NASDAQ"
        ]

        for signal in buy_signals:
            with self.subTest(signal=signal):
                result = ActionDetector.detect_action_type(signal)
                self.assertEqual(result, TradeType.Buy)

    def test_detect_sell_action_variations(self):
        """Test SELL action detection with variations"""
        sell_signals = [
            "SELL GBPUSD",
            "بفروش EURUSD",
            "فروش XAUUSD",
            "selling NASDAQ"
        ]

        for signal in sell_signals:
            with self.subTest(signal=signal):
                result = ActionDetector.detect_action_type(signal)
                self.assertEqual(result, TradeType.Sell)

    def test_detect_no_action(self):
        """Test detection when no action is present"""
        neutral_texts = [
            "Market analysis for EURUSD",
            "Technical indicators",
            "Price movement discussion",
            "Random text without trading signals"
        ]

        for text in neutral_texts:
            with self.subTest(text=text):
                result = ActionDetector.detect_action_type(text)
                self.assertIsNone(result)

    def test_detect_action_case_insensitive(self):
        """Test case insensitive action detection"""
        texts = ["buy eurusd", "BUY EURUSD", "Buy EurUsd"]

        for text in texts:
            with self.subTest(text=text):
                result = ActionDetector.detect_action_type(text)
                self.assertEqual(result, TradeType.Buy)

    def test_detect_action_with_noise(self):
        """Test action detection with surrounding noise"""
        text = "According to analysis, BUY EURUSD @ 1.0850 is recommended"
        result = ActionDetector.detect_action_type(text)
        self.assertEqual(result, TradeType.Buy)

    def test_trade_type_enum_values(self):
        """Test TradeType enum values"""
        self.assertEqual(TradeType.Buy.value, 1)
        self.assertEqual(TradeType.Sell.value, 2)

    def test_trade_type_enum_names(self):
        """Test TradeType enum names"""
        self.assertEqual(TradeType.Buy.name, "Buy")
        self.assertEqual(TradeType.Sell.name, "Sell")


if __name__ == '__main__':
    unittest.main()