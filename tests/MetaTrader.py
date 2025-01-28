import unittest
from unittest.mock import patch, MagicMock
import MetaTrader5 as mt5
from loguru import logger

from app.MetaTrader import *


class TestMetaTrader(unittest.TestCase):
    @classmethod
    def setUp(self):
        self.mt = MetaTrader(
            path="C:/Users/Trade/Desktop/1/terminal64.exe",
            server="CapitalxtendLLC-MU",
            user=10187248,
            password="1A(f4@@eSoZ4"
        )
        self.symbol = "XAUUSD"
        if not self.mt.Login():
            logger.error("Failed to connect to MT5 terminal")
            raise unittest.SkipTest("Could not connect to MT5 terminal")

    def test_login(self):
        """Test if login returns boolean and connection is active"""
        self.assertIn(self.mt.Login(), [True, False])
        self.assertTrue(mt5.terminal_info().connected)

    def test_check_symbol(self):
        """Test symbol checking with real market data"""
        result = self.mt.CheckSymbol(self.symbol)
        self.assertIsInstance(result, bool)
        
        if result:
            logger.info(f"{self.symbol} is available for trading")
        else:
            logger.warning(f"{self.symbol} is not available")

    def test_get_current_price(self):
        """Test price retrieval with real market data"""
        price = self.mt.get_current_price(self.symbol)
        self.assertIsNotNone(price)
        self.assertIsInstance(price, float)
        logger.info(f"Current {self.symbol} price: {price}")
    
    def test_get_open_positions(self):
        """Test position retrieval with real account data"""
        positions = self.mt.get_open_positions()
        logger.info(f"Found {len(positions)} open positions")
        logger.info(f"{positions}")
        self.assertIsInstance(positions, list)

        if positions:
            position = positions[0]
            self.assertTrue(hasattr(position, 'ticket'))
            self.assertTrue(hasattr(position, 'symbol'))
            self.assertTrue(hasattr(position, 'volume'))
    
    def test_get_pending_orders(self):
        """Test pending orders retrieval with real account data"""
        orders = self.mt.get_pending_orders()
        logger.info(f"Found {len(orders)} pending orders")
        logger.info(f"{orders}")
        self.assertIsInstance(orders, list)
    
        if orders:
            order = orders[0]
            self.assertTrue(hasattr(order, 'ticket'))
            self.assertTrue(hasattr(order, 'symbol'))
            self.assertTrue(hasattr(order, 'volume_initial'))
    
    def test_get_position_by_ticket_valid(self):
        """
        Test retrieving a position with a valid ticket ID.
        """
        # Get all open positions
        ticketid = 22284487
        
        # positions = self.mt.get_open_positions()
        # if not positions:
        #     self.skipTest("No open positions found. Skipping test.")

        # Use the first position's ticket ID
        position = self.mt.get_position_by_ticket(ticketid)
        logger.info(f"Found position {position}")

        # Validate the returned position
        self.assertIsNotNone(position, "Position should not be None for a valid ticket ID.")
        self.assertEqual(position.ticket, ticketid, "Ticket ID should match the requested position.")
        
    def test_close_half_position(self):
        """Test closing half of a position"""
        # Test with valid lot size
        self.mt.close_half_position(ticket=22258633)
    
    def test_close_position_valid(self):
        """
        Test closing a valid position.
        """
        # Get all open positions
        positions = self.mt.get_open_positions()
        if not positions:
            self.skipTest("No open positions found. Skipping test.")

        # Use the first position's ticket ID
        ticket_id = positions[0].ticket
        result = self.mt.close_position(ticket_id)

        # Validate the result
        self.assertTrue(result, "Failed to close the position.")
        logger.info(f"Successfully closed position with ticket ID: {ticket_id}")
    
    def test_update_stop_loss_valid(self):
        """
        Test updating stop loss for a valid position.
        """
        # result = self.mt.OpenPosition(mt5.ORDER_TYPE_BUY, "0.01", "XAUUSD", 2780, 2740, self.mt.get_current_price("XAUUSD"), None, "comment", None)
        ticket_id = 22270677
        new_stop_loss = 2740

        result = self.mt.update_stop_loss(ticket_id, new_stop_loss)

        # Validate the result
        self.assertTrue(result, "Failed to update stop loss for a valid position.")
        logger.info(f"Successfully updated stop loss for position {ticket_id} to {new_stop_loss}")
        
if __name__ == '__main__':
    unittest.main()