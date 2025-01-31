import json
from loguru import logger
import unittest
from unittest.mock import patch, mock_open
import json
from app.MetaTrader import *

import unittest

class TestCalculateLotSize(unittest.TestCase):
    
    def test_calculate_lot_size_standard_case(self):
        account_size = 10000  # $10,000
        risk_percentage = 1   # 1%
        stop_loss_pips = 50   # 50 pips
        pip_value = 10        # $10 per pip for a standard lot in USD pairs
        expected_lot_size = 0.2
        
        result = MetaTrader.calculate_lot_size(account_size, risk_percentage, stop_loss_pips, pip_value)
        self.assertAlmostEqual(result, expected_lot_size, places=2)

    def test_calculate_lot_size_zero_risk(self):
        account_size = 10000  # $10,000
        risk_percentage = 0   # 0%
        stop_loss_pips = 50   # 50 pips
        pip_value = 10        # $10 per pip for a standard lot in USD pairs
        expected_lot_size = 0.0
        
        result = MetaTrader.calculate_lot_size(account_size, risk_percentage, stop_loss_pips, pip_value)
        self.assertAlmostEqual(result, expected_lot_size, places=2)
    
    def test_calculate_lot_size_high_risk(self):
        account_size = 10000  # $10,000
        risk_percentage = 10  # 10%
        stop_loss_pips = 50   # 50 pips
        pip_value = 10        # $10 per pip for a standard lot in USD pairs
        expected_lot_size = 2.0
        
        result = MetaTrader.calculate_lot_size(account_size, risk_percentage, stop_loss_pips, pip_value)
        self.assertAlmostEqual(result, expected_lot_size, places=2)

    def test_calculate_lot_size_large_stop_loss(self):
        account_size = 10000  # $10,000
        risk_percentage = 1   # 1%
        stop_loss_pips = 100  # 100 pips
        pip_value = 10        # $10 per pip for a standard lot in USD pairs
        expected_lot_size = 0.1
        
        result = MetaTrader.calculate_lot_size(account_size, risk_percentage, stop_loss_pips, pip_value)
        self.assertAlmostEqual(result, expected_lot_size, places=2)
        
    def test_calculate_lot_size_small_account(self):
        account_size = 1000   # $1,000
        risk_percentage = 1   # 1%
        stop_loss_pips = 50   # 50 pips
        pip_value = 10        # $10 per pip for a standard lot in USD pairs
        expected_lot_size = 0.02
        
        result = MetaTrader.calculate_lot_size(account_size, risk_percentage, stop_loss_pips, pip_value)
        self.assertAlmostEqual(result, expected_lot_size, places=2)

if __name__ == '__main__':
    unittest.main()
