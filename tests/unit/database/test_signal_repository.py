"""Unit tests for SignalRepository"""

import unittest
from unittest.mock import patch, MagicMock
from tests.fixtures import TestBase, sample_signal_record
from app.Database.repository.signal_repository import SignalRepository


class TestSignalRepository(TestBase):
    """Test cases for SignalRepository"""

    def setUp(self):
        super().setUp()
        self.mock_conn = self.mock_database_connection()
        self.repo = SignalRepository("test.db")

    @patch('sqlite3.connect')
    def test_insert_signal(self, mock_connect):
        """Test inserting a signal record"""
        mock_connect.return_value = self.mock_conn

        data = {
            "telegram_channel_title": "test_channel",
            "telegram_message_id": 123,
            "telegram_message_chatid": 456,
            "open_price": 1.0850,
            "second_price": None,
            "stop_loss": 1.0800,
            "tp_list": "1.0900,1.0950",
            "symbol": "EURUSD",
            "current_time": "2023-11-11 10:00:00"
        }

        result = self.repo.insert(data)
        self.assertEqual(result, 1)  # lastrowid

    @patch('sqlite3.connect')
    def test_get_signal_by_id(self, mock_connect):
        """Test getting signal by ID"""
        mock_connect.return_value = self.mock_conn
        self.mock_conn.cursor.return_value.fetchone.return_value = (
            1, "test_channel", 123, 456, 1.0850, None, 1.0800,
            "1.0900,1.0950", "EURUSD", "2023-11-11 10:00:00"
        )

        result = self.repo.get_signal_by_id(1)
        self.assertIsNotNone(result)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.symbol, "EURUSD")

    @patch('sqlite3.connect')
    def test_get_signal_by_id_not_found(self, mock_connect):
        """Test getting signal by ID when not found"""
        mock_connect.return_value = self.mock_conn
        self.mock_conn.cursor.return_value.fetchone.return_value = None

        result = self.repo.get_signal_by_id(999)
        self.assertIsNone(result)

    @patch('sqlite3.connect')
    def test_get_signal_by_position_id(self, mock_connect):
        """Test getting signal by position ID"""
        mock_connect.return_value = self.mock_conn
        self.mock_conn.cursor.return_value.fetchone.return_value = (
            1, "test_channel", 123, 456, 1.0850, None, 1.0800,
            "1.0900,1.0950", "EURUSD", "2023-11-11 10:00:00"
        )

        result = self.repo.get_signal_by_position_id(12345)
        self.assertIsNotNone(result)
        self.assertEqual(result.symbol, "EURUSD")

    @patch('sqlite3.connect')
    def test_get_last_record(self, mock_connect):
        """Test getting last matching record"""
        mock_connect.return_value = self.mock_conn
        self.mock_conn.cursor.return_value.fetchone.return_value = (
            1, "test_channel", 123, 456, 1.0850, None, 1.0800,
            "1.0900,1.0950", "EURUSD", "2023-11-11 10:00:00"
        )

        result = self.repo.get_last_record(1.0850, None, 1.0800, "EURUSD")
        self.assertIsNotNone(result)
        self.assertEqual(result["symbol"], "EURUSD")

    @patch('sqlite3.connect')
    def test_update_stop_loss(self, mock_connect):
        """Test updating stop loss"""
        mock_connect.return_value = self.mock_conn

        self.repo.update_stop_loss(1, 1.0820)
        self.mock_conn.cursor.return_value.execute.assert_called_once()

    @patch('sqlite3.connect')
    def test_update_take_profits(self, mock_connect):
        """Test updating take profits"""
        mock_connect.return_value = self.mock_conn

        self.repo.update_take_profits(1, [1.0900, 1.0950])
        self.mock_conn.cursor.return_value.execute.assert_called_once()

    @patch('sqlite3.connect')
    def test_get_signal_by_chat(self, mock_connect):
        """Test getting signal by chat and message ID"""
        mock_connect.return_value = self.mock_conn
        self.mock_conn.cursor.return_value.fetchone.return_value = (
            1, "test_channel", 123, 456, 1.0850, None, 1.0800,
            "1.0900,1.0950", "EURUSD", "2023-11-11 10:00:00"
        )

        result = self.repo.get_signal_by_chat(456, 123)
        self.assertIsNotNone(result)
        self.assertEqual(result["telegram_message_id"], 123)

    def test_signal_to_dict(self):
        """Test Signal model to_dict method"""
        from app.Database.models import Signal

        signal = Signal(
            id=1,
            telegram_channel_title="test",
            telegram_message_id=123,
            telegram_message_chatid=456,
            open_price=1.0850,
            second_price=None,
            stop_loss=1.0800,
            tp_list="1.0900,1.0950",
            symbol="EURUSD",
            current_time="2023-11-11 10:00:00"
        )

        result = signal.to_dict()
        self.assertIsInstance(result, dict)
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["symbol"], "EURUSD")


if __name__ == '__main__':
    unittest.main()