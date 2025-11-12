"""Base test class with common utilities and setup"""

import unittest
import tempfile
import os
import sys
from unittest.mock import MagicMock, patch
from loguru import logger

# Add app directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestBase(unittest.TestCase):
    """Base test class providing common test utilities"""

    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()

        # Disable logging during tests
        logger.remove()
        logger.add(lambda _: None, level="CRITICAL")

    def tearDown(self):
        """Clean up test environment"""
        # Remove temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

        # Restore logging
        logger.remove()
        logger.add(sys.stdout, level="INFO")

    def create_temp_file(self, filename, content=""):
        """Create a temporary file with given content"""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    def mock_mt5_connection(self):
        """Create a mock MT5 connection for testing"""
        mock_mt5 = MagicMock()
        mock_mt5.initialize.return_value = True
        mock_mt5.login.return_value = True
        mock_mt5.terminal_info.return_value = MagicMock(connected=True)
        mock_mt5.symbol_info_tick.return_value = MagicMock(bid=1.0, ask=1.001)
        mock_mt5.symbol_info.return_value = MagicMock(visible=True)
        mock_mt5.symbol_select.return_value = True
        mock_mt5.positions_get.return_value = []
        mock_mt5.orders_get.return_value = []
        return mock_mt5

    def mock_database_connection(self):
        """Create a mock database connection"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        mock_cursor.fetchall.return_value = []
        mock_cursor.lastrowid = 1
        return mock_conn

    def assertIsFloat(self, value, msg=None):
        """Assert that value is a float"""
        self.assertIsInstance(value, float, msg)

    def assertIsString(self, value, msg=None):
        """Assert that value is a string"""
        self.assertIsInstance(value, str, msg)

    def assertIsList(self, value, msg=None):
        """Assert that value is a list"""
        self.assertIsInstance(value, list, msg)

    def assertIsDict(self, value, msg=None):
        """Assert that value is a dict"""
        self.assertIsInstance(value, dict, msg)