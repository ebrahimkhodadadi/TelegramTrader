"""Unit tests for text processing functionality"""

import unittest
from tests.fixtures import TestBase
from app.Analayzer.parsers.text_processor import TextProcessor


class TestTextProcessor(TestBase):
    """Test cases for TextProcessor class"""

    def test_clean_text_basic(self):
        """Test basic text cleaning"""
        input_text = "BUY EURUSD @ 1.0850 📈"
        expected = "BUY EURUSD @ 1.0850"
        result = TextProcessor.clean_text(input_text)
        self.assertEqual(result, expected)

    def test_clean_text_persian(self):
        """Test Persian text cleaning"""
        input_text = "خرید یورو @ ۱.۰۸۵۰ ✅"
        expected = "خرید یورو @ ۱.۰۸۵۰"
        result = TextProcessor.clean_text(input_text)
        self.assertEqual(result, expected)

    def test_clean_text_unicode_normalization(self):
        """Test Unicode normalization"""
        input_text = "BUY EURUSD @ 1.0850"
        # Input has bold formatting (invisible in editor)
        result = TextProcessor.clean_text(input_text)
        self.assertIsInstance(result, str)
        self.assertNotIn('\u200b', result)  # Zero-width space

    def test_clean_text_multiple_spaces(self):
        """Test multiple space normalization"""
        input_text = "BUY   EURUSD    @    1.0850"
        expected = "BUY EURUSD @ 1.0850"
        result = TextProcessor.clean_text(input_text)
        self.assertEqual(result, expected)

    def test_clean_text_newlines(self):
        """Test newline handling"""
        input_text = "BUY EURUSD\n@\n1.0850"
        expected = "BUY EURUSD\n@\n1.0850"
        result = TextProcessor.clean_text(input_text)
        self.assertEqual(result, expected)

    def test_clean_text_superscript(self):
        """Test superscript number conversion"""
        input_text = "TP¹ 1.0900"
        expected = "TP1 1.0900"
        result = TextProcessor.clean_text(input_text)
        self.assertEqual(result, expected)

    def test_clean_text_empty_string(self):
        """Test empty string handling"""
        result = TextProcessor.clean_text("")
        self.assertEqual(result, "")

    def test_clean_text_none_input(self):
        """Test None input handling"""
        with self.assertRaises(AttributeError):
            TextProcessor.clean_text(None)

    def test_clean_text_special_characters(self):
        """Test removal of special characters"""
        input_text = "BUY EURUSD @ 1.0850!#$%&*"
        expected = "BUY EURUSD @ 1.0850"
        result = TextProcessor.clean_text(input_text)
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()