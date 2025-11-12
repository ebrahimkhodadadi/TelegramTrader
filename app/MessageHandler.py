"""
Message Handler for TelegramTrader

This module processes different types of Telegram messages and coordinates
trading actions, signal updates, and position management.

Features:
    - Signal processing and trade execution
    - Message editing and deletion handling
    - Risk management commands
    - Trading hour validation
    - Comprehensive error handling and logging
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Any
from datetime import datetime
from loguru import logger
from enum import Enum

from Analayzer import parse_message, extract_price
from Configure import GetSettings
from Database import Migrations
from Helper import is_now_between
from MetaTrader import Trade, RiskFreePositions, Update_last_signal, Update_signal, Close_half_signal, Delete_signal


class PerformanceMonitor:
    """Simple performance monitoring for trading operations"""

    _timings = {}
    _counts = {}

    @staticmethod
    def start_operation(operation_name):
        """Start timing an operation"""
        PerformanceMonitor._timings[operation_name] = time.time()

    @staticmethod
    def end_operation(operation_name):
        """End timing an operation and log if slow"""
        if operation_name in PerformanceMonitor._timings:
            duration = time.time() - PerformanceMonitor._timings[operation_name]
            PerformanceMonitor._counts[operation_name] = PerformanceMonitor._counts.get(operation_name, 0) + 1

            # Log slow operations (>100ms)
            if duration > 0.1:
                logger.warning(".2f")

            del PerformanceMonitor._timings[operation_name]
            return duration
        return 0


class MessageType(Enum):
    """Enumeration of message event types"""
    New = 1
    Edited = 2
    Deleted = 3


class ConcurrentOperationProcessor:
    """Handles concurrent processing of trading operations with thread safety"""

    _global_lock = threading.Lock()  # Global lock for critical operations
    _signal_locks = {}  # Per-signal locks to prevent concurrent operations on same signal
    _signal_locks_lock = threading.Lock()  # Lock for managing signal locks
    _executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="TradingOps")  # Increased workers
    _rate_limiter = threading.Semaphore(3)  # Increased concurrent MT5 operations
    _trade_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="TradeOps")  # Dedicated for trade opening

    @staticmethod
    def _get_signal_lock(signal_id):
        """Get or create a lock for a specific signal"""
        with ConcurrentOperationProcessor._signal_locks_lock:
            if signal_id not in ConcurrentOperationProcessor._signal_locks:
                ConcurrentOperationProcessor._signal_locks[signal_id] = threading.Lock()
            return ConcurrentOperationProcessor._signal_locks[signal_id]

    @staticmethod
    def submit_operation(operation_func, *args, **kwargs):
        """Submit an operation for concurrent execution with proper synchronization"""
        def safe_operation():
            signal_id = None

            # Extract signal_id from args/kwargs for per-signal locking
            if args and len(args) > 0:
                # Try to identify signal_id from common patterns
                if operation_func.__name__ in ['Delete_signal', 'Close_half_signal', 'Update_signal']:
                    signal_id = args[0]  # First arg is usually signal_id
                elif operation_func.__name__ == 'Update_last_signal':
                    # For Update_last_signal, we need to get signal_id from database
                    chat_id = args[0]
                    from Database import Migrations
                    positions = Migrations.get_last_signal_positions_by_chatid(chat_id)
                    if positions:
                        signal = Migrations.get_signal_by_positionId(positions[0])
                        if signal:
                            signal_id = signal['id']

            locks_to_acquire = []
            semaphore_acquired = False

            try:
                # Acquire rate limiter semaphore
                ConcurrentOperationProcessor._rate_limiter.acquire()
                semaphore_acquired = True

                # Acquire signal-specific lock if applicable
                signal_lock = None
                if signal_id is not None:
                    signal_lock = ConcurrentOperationProcessor._get_signal_lock(signal_id)
                    signal_lock.acquire()
                    locks_to_acquire.append(signal_lock)

                # Acquire global lock for database operations
                if operation_func.__name__ in ['Delete_signal', 'Update_signal', 'Update_last_signal']:
                    ConcurrentOperationProcessor._global_lock.acquire()
                    locks_to_acquire.append(ConcurrentOperationProcessor._global_lock)

                # Execute the operation
                return operation_func(*args, **kwargs)

            except Exception as e:
                logger.error(f"Error in concurrent operation {operation_func.__name__}: {e}")
                return None
            finally:
                # Release locks in reverse order
                for lock in reversed(locks_to_acquire):
                    lock.release()

                # Release semaphore
                if semaphore_acquired:
                    ConcurrentOperationProcessor._rate_limiter.release()

        return ConcurrentOperationProcessor._executor.submit(safe_operation)

    @staticmethod
    def shutdown():
        """Shutdown the executors and cleanup locks"""
        ConcurrentOperationProcessor._executor.shutdown(wait=True)
        ConcurrentOperationProcessor._trade_executor.shutdown(wait=True)
        # Clear signal locks
        with ConcurrentOperationProcessor._signal_locks_lock:
            ConcurrentOperationProcessor._signal_locks.clear()


class MessageHandler:
    """Handles processing of different Telegram message types"""

    # Command keywords for different actions
    EDIT_KEYWORDS = ['edit', 'edite', 'update', 'modify']
    DELETE_KEYWORDS = ['حذف', 'delete', 'close', 'not a signal', 'vip']
    RISK_FREE_KEYWORDS = ['فری', 'risk free', 'risk-free']

    @staticmethod
    def handle_message(message_type: MessageType, text: str, comment: str,
                      username: Optional[str], message_id: Optional[int],
                      chat_id: int) -> None:
        """
        Main entry point for handling incoming messages.

        Args:
            message_type: Type of message event
            text: Message content
            comment: Additional comment/context
            username: Channel username
            message_id: Telegram message ID
            chat_id: Telegram chat ID
        """
        try:
            # logger.debug(f"Processing {message_type.name} message from chat {chat_id}")

            # Handle special edit commands in message text
            MessageHandler._handle_last_edit(chat_id, text)

            # Check trading hours
            if not MessageHandler._is_trading_allowed():
                return

            # Process based on message type
            if message_type == MessageType.New:
                MessageHandler._handle_new_signal(text, comment, username, message_id, chat_id)

        except Exception as e:
            logger.error(f"Error handling message: {e}")

    @staticmethod
    def _is_trading_allowed() -> bool:
        """Check if trading is allowed based on configured hours"""
        try:
            cfg = GetSettings()
            timer_config = getattr(cfg, "Timer", None)

            if timer_config is None:
                return True  # No timer restriction

            start_time = getattr(timer_config, 'start', None)
            end_time = getattr(timer_config, 'end', None)

            if not start_time or not end_time:
                return True

            if not is_now_between(start_time, end_time):
                logger.warning(f"Trading not allowed. Current time outside {start_time} - {end_time}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking trading hours: {e}")
            return True  # Allow trading on error

    @staticmethod
    def _handle_new_signal(text: str, comment: str, username: Optional[str],
                          message_id: Optional[int], chat_id: int) -> None:
        """Handle new trading signal messages"""
        try:
            # Parse the signal
            parsed_signal = MessageHandler._parse_signal(text)
            if not parsed_signal:
                return

            action_type, symbol, first_price, second_price, take_profits, stop_loss = parsed_signal

            # Validate required fields
            if not MessageHandler._validate_signal_data(action_type, symbol, first_price, stop_loss):
                return

            # Log the signal
            logger.success(f"New {action_type.name} {symbol} signal detected ({comment})")

            # Execute the trade
            Trade(username, message_id, chat_id, action_type, symbol,
                  first_price, second_price, take_profits, stop_loss, comment)

        except Exception as e:
            logger.error(f"Error processing new signal: {e}")

    @staticmethod
    def _parse_signal(text: str) -> Optional[tuple]:
        """Parse trading signal from message text"""
        try:
            if not text:
                # logger.debug("Cannot parse empty text")
                return None
            return parse_message(text)
        except Exception as e:
            logger.error(f"Error parsing signal text: {e}")
            return None

    @staticmethod
    def _validate_signal_data(action_type, symbol: str, first_price: float, stop_loss: float) -> bool:
        """Validate that signal has all required data"""
        if action_type is None:
            # logger.debug("Signal rejected: no action type")
            return False

        if first_price is None:
            # logger.debug("Signal rejected: no entry price")
            return False

        if stop_loss is None:
            # logger.debug("Signal rejected: no stop loss")
            return False

        if not symbol:
            # logger.debug("Signal rejected: no symbol")
            return False

        return True

    @staticmethod
    def _handle_last_edit(chat_id: int, text: str) -> None:
        """Handle edit commands in message text"""
        try:
            if any(keyword in text.lower() for keyword in MessageHandler.EDIT_KEYWORDS):
                stop_loss = extract_price(text)
                if stop_loss is not None:
                    logger.info(f"Submitting concurrent last signal update for chat {chat_id}")
                    ConcurrentOperationProcessor.submit_operation(Update_last_signal, chat_id, stop_loss)
        except Exception as e:
            logger.error(f"Error handling last edit: {e}")

    @staticmethod
    def handle_parent_edit(chat_id: int, message_id: int, text: str) -> None:
        """Handle edit commands in reply messages"""
        try:
            if not any(keyword in text.lower() for keyword in MessageHandler.EDIT_KEYWORDS):
                return

            stop_loss = extract_price(text)
            if stop_loss is None:
                logger.debug("No stop loss found in edit command")
                return

            signal = Migrations.get_signal_by_chat(chat_id, message_id)
            if signal is None:
                logger.debug(f"No signal found for chat {chat_id}, message {message_id}")
                return

            logger.info(f"Submitting concurrent update operation for signal {signal['id']} with new stop loss: {stop_loss}")
            ConcurrentOperationProcessor.submit_operation(Update_signal, signal["id"], stop_loss)

        except Exception as e:
            logger.error(f"Error handling parent edit: {e}")

    @staticmethod
    def handle_edit(chat_id: int, message_id: int, message: str) -> None:
        """Handle message edits that contain updated signal data"""
        try:
            if not message:
                # logger.debug("Edited message has no content")
                return

            signal = Migrations.get_signal_by_chat(chat_id, message_id)
            if signal is None:
                logger.debug(f"No signal found for edited message {message_id}")
                return

            # Parse the updated message
            parsed_signal = MessageHandler._parse_signal(message)
            if not parsed_signal:
                logger.debug("Could not parse edited message")
                return

            action_type, symbol, first_price, second_price, take_profits, stop_loss = parsed_signal

            logger.info(f"Updating signal {signal['id']} with edited data")
            Update_signal(signal["id"], take_profits, stop_loss)

        except Exception as e:
            logger.error(f"Error handling message edit: {e}")

    @staticmethod
    def handle_parent_delete(chat_id: int, message_id: int, text: str) -> None:
        """Handle delete/close commands in reply messages"""
        try:
            if not any(keyword in text.lower() for keyword in MessageHandler.DELETE_KEYWORDS):
                return

            signal = Migrations.get_signal_by_chat(chat_id, message_id)
            if signal is None:
                logger.debug(f"No signal found for delete command")
                return

            # Submit operation for concurrent processing
            if 'half' in text.lower():
                logger.info(f"Submitting concurrent half-close operation for signal {signal['id']}")
                ConcurrentOperationProcessor.submit_operation(Close_half_signal, signal["id"])
            else:
                logger.info(f"Submitting concurrent delete operation for signal {signal['id']}")
                ConcurrentOperationProcessor.submit_operation(Delete_signal, signal["id"])

        except Exception as e:
            logger.error(f"Error handling parent delete: {e}")

    @staticmethod
    def handle_delete(chat_id: int, message_id: int) -> None:
        """Handle message deletions"""
        try:
            signal = Migrations.get_signal_by_chat(chat_id, message_id)
            if signal is None:
                logger.debug(f"No signal found for deleted message {message_id}")
                return

            logger.info(f"Submitting concurrent delete operation for signal {signal['id']} due to message deletion")
            ConcurrentOperationProcessor.submit_operation(Delete_signal, signal["id"])

        except Exception as e:
            logger.error(f"Error handling message deletion: {e}")

    @staticmethod
    def handle_parent_risk_free(chat_id: int, message_id: int, text: str) -> None:
        """Handle risk-free commands in reply messages"""
        try:
            if not any(keyword in text.lower() for keyword in MessageHandler.RISK_FREE_KEYWORDS):
                return

            logger.info(f"Applying risk-free to positions for chat {chat_id}, message {message_id}")
            RiskFreePositions(chat_id, message_id)

        except Exception as e:
            logger.error(f"Error handling risk-free command: {e}")


# Backward compatibility functions
def Handle(messageType, text, comment, username, message_id, chat_id):
    """Legacy main handler function"""
    MessageHandler.handle_message(messageType, text, comment, username, message_id, chat_id)

def HandleOpenPosition(messageType, text, comment, message_username, message_id, chat_id):
    """Legacy position handler (now handled by handle_message)"""
    pass  # Functionality moved to handle_message

def HandleParentRiskFree(chat_id, message_id, text):
    """Legacy risk-free handler"""
    MessageHandler.handle_parent_risk_free(chat_id, message_id, text)

def HandleLastEdite(chat_id, text):
    """Legacy last edit handler (typo preserved for compatibility)"""
    MessageHandler._handle_last_edit(chat_id, text)

def HandleParentEdit(chat_id, message_id, text):
    """Legacy parent edit handler"""
    MessageHandler.handle_parent_edit(chat_id, message_id, text)

def HandleEdite(chat_id, message_id, message):
    """Legacy edit handler (typo preserved for compatibility)"""
    MessageHandler.handle_edit(chat_id, message_id, message)

def HandleParentDelete(chat_id, message_id, text):
    """Legacy parent delete handler"""
    MessageHandler.handle_parent_delete(chat_id, message_id, text)

def HandleDelete(chat_id, message_id):
    """Legacy delete handler"""
    MessageHandler.handle_delete(chat_id, message_id)
