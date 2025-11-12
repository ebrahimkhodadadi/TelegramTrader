"""Unit tests for PositionManager functionality"""

import unittest
from unittest.mock import patch, MagicMock
from tests.fixtures import TestBase, sample_positions
from app.MetaTrader.trading.positions import PositionManager


class TestPositionManager(TestBase):
    """Test cases for PositionManager class"""

    def setUp(self):
        super().setUp()
        self.market_data = self.mock_mt5_connection()
        self.manager = PositionManager(self.market_data, magic_number=2025)

    @patch('app.MetaTrader.trading.positions.mt5.symbol_info_tick')
    @patch('app.MetaTrader.trading.positions.mt5.order_send')
    def test_save_profit_position_zero_percentage(self, mock_order_send, mock_symbol_info):
        """Test that zero profit percentage skips operation"""
        # Setup mocks
        mock_symbol_info.return_value = MagicMock(bid=1.0850, ask=1.0852)
        mock_order_send.return_value = MagicMock(retcode=10009)  # TRADE_RETCODE_DONE

        # Mock position
        position = sample_positions[0]  # EURUSD BUY position
        self.market_data.get_open_positions.return_value = position

        # Test with zero percentage
        save_profits = [0, 25, 25, 25]  # Zero at first level
        result = self.manager.save_profit_position(12345, 0, save_profits)

        # Should return True (success) but not execute any orders
        self.assertTrue(result)
        mock_order_send.assert_not_called()

    @patch('app.MetaTrader.trading.positions.mt5.symbol_info_tick')
    @patch('app.MetaTrader.trading.positions.mt5.order_send')
    def test_save_profit_position_close_disabled(self, mock_order_send, mock_symbol_info):
        """Test that disabled position closing skips operation"""
        # Setup mocks
        mock_symbol_info.return_value = MagicMock(bid=1.0850, ask=1.0852)
        mock_order_send.return_value = MagicMock(retcode=10009)

        # Mock position
        position = sample_positions[0]
        self.market_data.get_open_positions.return_value = position

        # Test with close_positions=False
        save_profits = [25, 25, 25, 25]
        result = self.manager.save_profit_position(12345, 0, save_profits, close_positions=False)

        # Should return True (success) but not execute any orders
        self.assertTrue(result)
        mock_order_send.assert_not_called()

    @patch('app.MetaTrader.trading.positions.mt5.symbol_info_tick')
    @patch('app.MetaTrader.trading.positions.mt5.order_send')
    def test_save_profit_position_normal_percentage(self, mock_order_send, mock_symbol_info):
        """Test normal profit percentage execution"""
        # Setup mocks
        mock_symbol_info.return_value = MagicMock(bid=1.0850, ask=1.0852)
        mock_order_send.return_value = MagicMock(retcode=10009)  # TRADE_RETCODE_DONE

        # Mock position with larger volume to avoid minimum lot issues
        position = sample_positions[0]._replace(volume=0.1)  # 0.1 lot instead of 0.01
        self.market_data.get_open_positions.return_value = position

        # Test with normal percentage
        save_profits = [25, 25, 25, 25]
        result = self.manager.save_profit_position(12345, 0, save_profits)

        # Should execute order
        self.assertTrue(result)
        mock_order_send.assert_called_once()

        # Verify order parameters
        call_args = mock_order_send.call_args[0][0]
        self.assertEqual(call_args['action'], 1)  # TRADE_ACTION_DEAL
        self.assertEqual(call_args['volume'], 0.025)  # 25% of 0.1 lot
        self.assertEqual(call_args['type'], 1)  # ORDER_TYPE_SELL for closing BUY

    @patch('app.MetaTrader.trading.positions.mt5.symbol_info_tick')
    @patch('app.MetaTrader.trading.positions.mt5.order_send')
    def test_save_profit_position_100_percentage(self, mock_order_send, mock_symbol_info):
        """Test 100% profit percentage closes entire position"""
        # Setup mocks
        mock_symbol_info.return_value = MagicMock(bid=1.0850, ask=1.0852)
        mock_order_send.return_value = MagicMock(retcode=10009)

        # Mock position
        position = sample_positions[0]
        self.market_data.get_open_positions.return_value = position

        # Test with 100% percentage
        save_profits = [25, 25, 25, 100]
        result = self.manager.save_profit_position(12345, 3, save_profits)

        # Should call close_position (not partial close)
        self.assertTrue(result)
        # Verify it would close the full position
        call_args = mock_order_send.call_args[0][0]
        self.assertEqual(call_args['volume'], 0.01)  # Full position volume

    def test_save_profit_position_no_position(self):
        """Test handling when position is not found"""
        self.market_data.get_open_positions.return_value = None

        result = self.manager.save_profit_position(99999, 0, [25, 25, 25, 25])
        self.assertFalse(result)

    def test_save_profit_position_invalid_index(self):
        """Test handling of invalid save_profits index"""
        position = sample_positions[0]
        self.market_data.get_open_positions.return_value = position

        result = self.manager.save_profit_position(12345, 10, [25, 25, 25, 25])
        self.assertFalse(result)

    def test_save_profit_position_no_save_profits(self):
        """Test handling when save_profits is None"""
        position = sample_positions[0]
        self.market_data.get_open_positions.return_value = position

        result = self.manager.save_profit_position(12345, 0, None)
        self.assertFalse(result)

    def test_save_profit_position_empty_save_profits(self):
        """Test handling when save_profits is empty"""
        position = sample_positions[0]
        self.market_data.get_open_positions.return_value = position

        result = self.manager.save_profit_position(12345, 0, [])
        self.assertFalse(result)

    @patch('app.MetaTrader.trading.positions.mt5.symbol_info_tick')
    @patch('app.MetaTrader.trading.positions.mt5.order_send')
    def test_save_profit_position_minimum_volume_closes_entire(self, mock_order_send, mock_symbol_info):
        """Test that minimum volume below 0.01 closes entire position"""
        # Setup mocks
        mock_symbol_info.return_value = MagicMock(bid=1.0850, ask=1.0852)
        mock_order_send.return_value = MagicMock(retcode=10009)

        # Mock position with very small volume
        position = sample_positions[0]._replace(volume=0.005)  # Very small position
        self.market_data.get_open_positions.return_value = position

        # Test with percentage that results in volume < 0.01
        save_profits = [50, 25, 25, 25]  # 50% of 0.005 = 0.0025 < 0.01
        result = self.manager.save_profit_position(12345, 0, save_profits)

        # Should close entire position
        self.assertTrue(result)
        mock_order_send.assert_called_once()

        # Verify it closes the full position volume
        call_args = mock_order_send.call_args[0][0]
        self.assertEqual(call_args['volume'], 0.005)  # Full position volume

    @patch('app.MetaTrader.trading.positions.mt5.symbol_info_tick')
    def test_save_profit_position_no_price_data(self, mock_symbol_info):
        """Test handling when price data is unavailable"""
        mock_symbol_info.return_value = None

        position = sample_positions[0]
        self.market_data.get_open_positions.return_value = position

        result = self.manager.save_profit_position(12345, 0, [25, 25, 25, 25])
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()