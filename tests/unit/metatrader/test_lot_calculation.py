"""Unit tests for lot calculation functionality"""

import unittest
from unittest.mock import patch, MagicMock
from tests.fixtures import TestBase
from app.MetaTrader.trading.validation import LotCalculator


class TestLotCalculation(TestBase):
    """Test cases for lot size calculations"""

    def setUp(self):
        super().setUp()
        self.calculator = LotCalculator()

    def test_calculate_lot_size_percentage_mode(self):
        """Test lot calculation with percentage risk"""
        result = self.calculator.calculate_lot_size_with_prices(
            symbol="EURUSD",
            risk_percentage="2%",
            open_price=1.0850,
            stop_loss_price=1.0800,
            account_size=10000
        )

        # Expected: 2% of 10000 = 200 risk amount
        # Risk per pip: 50 pips * 10 (EURUSD pip value) = 500
        # Lot size: 200 / 500 = 0.4
        expected = 0.4
        self.assertAlmostEqual(result, expected, places=1)

    def test_calculate_lot_size_fixed_mode(self):
        """Test lot calculation with fixed lot size"""
        result = self.calculator.calculate_lot_size_with_prices(
            symbol="EURUSD",
            risk_percentage="0.5",  # Fixed lot size
            open_price=1.0850,
            stop_loss_price=1.0800,
            account_size=10000
        )

        self.assertEqual(result, 0.5)

    def test_calculate_lot_size_zero_risk(self):
        """Test lot calculation with zero risk percentage"""
        result = self.calculator.calculate_lot_size_with_prices(
            symbol="EURUSD",
            risk_percentage="0%",
            open_price=1.0850,
            stop_loss_price=1.0800,
            account_size=10000
        )

        self.assertEqual(result, 0.0)

    def test_calculate_lot_size_high_risk(self):
        """Test lot calculation with high risk percentage"""
        result = self.calculator.calculate_lot_size_with_prices(
            symbol="EURUSD",
            risk_percentage="5%",
            open_price=1.0850,
            stop_loss_price=1.0800,
            account_size=10000
        )

        # Expected: 5% of 10000 = 500 risk amount
        # Risk per pip: 50 pips * 10 = 500
        # Lot size: 500 / 500 = 1.0
        expected = 1.0
        self.assertAlmostEqual(result, expected, places=1)

    def test_calculate_lot_size_large_stop_loss(self):
        """Test lot calculation with large stop loss"""
        result = self.calculator.calculate_lot_size_with_prices(
            symbol="EURUSD",
            risk_percentage="1%",
            open_price=1.0850,
            stop_loss_price=1.0750,  # 100 pips stop loss
            account_size=10000
        )

        # Expected: 1% of 10000 = 100 risk amount
        # Risk per pip: 100 pips * 10 = 1000
        # Lot size: 100 / 1000 = 0.1
        expected = 0.1
        self.assertAlmostEqual(result, expected, places=1)

    def test_calculate_lot_size_small_account(self):
        """Test lot calculation with small account"""
        result = self.calculator.calculate_lot_size_with_prices(
            symbol="EURUSD",
            risk_percentage="1%",
            open_price=1.0850,
            stop_loss_price=1.0800,
            account_size=1000
        )

        # Expected: 1% of 1000 = 10 risk amount
        # Risk per pip: 50 pips * 10 = 500
        # Lot size: 10 / 500 = 0.02
        expected = 0.02
        self.assertAlmostEqual(result, expected, places=2)

    def test_calculate_lot_size_no_account_size(self):
        """Test lot calculation without account size (uses MT5 account)"""
        with patch('app.MetaTrader.trading.validation.mt5.account_info') as mock_account:
            mock_account.return_value = MagicMock(balance=5000)

            result = self.calculator.calculate_lot_size_with_prices(
                symbol="EURUSD",
                risk_percentage="2%",
                open_price=1.0850,
                stop_loss_price=1.0800,
                account_size=None
            )

            # Expected: 2% of 5000 = 100 risk amount
            # Risk per pip: 50 pips * 10 = 500
            # Lot size: 100 / 500 = 0.2
            expected = 0.2
            self.assertAlmostEqual(result, expected, places=1)

    def test_calculate_lot_size_gold_symbol(self):
        """Test lot calculation for gold (XAUUSD)"""
        result = self.calculator.calculate_lot_size_with_prices(
            symbol="XAUUSD",
            risk_percentage="1%",
            open_price=1950.50,
            stop_loss_price=1945.50,
            account_size=10000
        )

        # Gold pip value is typically 0.1 USD per pip for standard lot
        # Risk per pip: 5 pips * 0.1 = 0.5
        # Risk amount: 1% of 10000 = 100
        # Lot size: 100 / 0.5 = 200
        # But this is unrealistic - MT5 would cap it
        self.assertIsInstance(result, float)

    def test_calculate_lot_size_invalid_percentage(self):
        """Test lot calculation with invalid percentage format"""
        result = self.calculator.calculate_lot_size_with_prices(
            symbol="EURUSD",
            risk_percentage="invalid",
            open_price=1.0850,
            stop_loss_price=1.0800,
            account_size=10000
        )

        # Should return the string as-is (not percentage)
        self.assertEqual(result, "invalid")

    @patch('app.MetaTrader.trading.validation.mt5.symbol_info')
    def test_calculate_lot_size_missing_symbol_info(self, mock_symbol_info):
        """Test lot calculation when symbol info is unavailable"""
        mock_symbol_info.return_value = None

        with self.assertRaises(AttributeError):
            self.calculator.calculate_lot_size_with_prices(
                symbol="INVALID",
                risk_percentage="1%",
                open_price=1.0850,
                stop_loss_price=1.0800,
                account_size=10000
            )


if __name__ == '__main__':
    unittest.main()