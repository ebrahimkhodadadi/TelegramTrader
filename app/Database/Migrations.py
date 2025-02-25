from Database.Repository import *


db_path = "telegramtrader.db"

# tables
# signal
signal_columns = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "telegram_channel_title": "TEXT NOT NULL",
    "telegram_message_id": "INTEGER",
    "telegram_message_chatid": "INTEGER",
    "open_price": "REAL NOT NULL",
    "second_price": "REAL",
    "stop_loss": "REAL NOT NULL",
    "tp_list": "TEXT NOT NULL",
    "symbol": "TEXT NOT NULL",
    "current_time": "TEXT NOT NULL"
}
# position
position_columns = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "signal_id": "INTEGER NOT NULL",
    "position_id": "INTEGER NOT NULL",
    "user_id": "INTEGER NOT NULL",
    "is_first": "Boolean NULL",
    "is_second": "Boolean NULL",
    "FOREIGN KEY(signal_id)": "REFERENCES Signals(id) ON DELETE CASCADE"
}

# Create repositories
signal_repo = SQLiteRepository(db_path, "Signals")
position_repo = SQLiteRepository(db_path, "Positions")

# Create tables


def DoMigrations():
    signal_repo.create_table(signal_columns)
    position_repo.create_table(position_columns)


def get_tp_levels(ticket_id):
    """Read Take Profit values from the database"""
    query = """
        SELECT s.tp_list 
        FROM positions p
        INNER JOIN signals s ON p.signal_id = s.id
        WHERE p.position_id = ?
    """
    signal = signal_repo.execute_query(query, (ticket_id,))
    if signal and len(signal) > 0:
        return [float(x) for x in signal[0][0].split(',')]
    return None


def get_last_signal_positions_by_chatid(chat_id):
    """Read last signal positions from the database"""
    query = """
        SELECT p.position_id 
        FROM positions p
        INNER JOIN signals s ON p.signal_id = s.id
        WHERE s.telegram_message_chatid = ?
        ORDER BY p.id DESC
        LIMIT 2
    """
    positions = position_repo.execute_query(query, (chat_id,)) 
    return [x[0] for x in positions]


def get_last_record(open_price, second_price, stop_loss, symbol):
    query = """
            SELECT *
            FROM signals
            WHERE open_price = ? AND second_price = ? AND stop_loss = ? AND symbol = ?
            ORDER BY id DESC
            LIMIT 1
        """
    results = signal_repo.execute_query(
        query, (open_price, second_price, stop_loss, symbol))
    if results == None or len(results) == 0:
        return None

    result = results[0]

    # Map the result to a dictionary using the signal_columns as keys
    signal_columns = {
        "id": result[0],
        "telegram_channel_title": result[1],
        "telegram_message_id": result[2],
        "telegram_message_chatid": result[3],
        "open_price": result[4],
        "second_price": result[5],
        "stop_loss": result[6],
        "tp_list": result[7],
        "symbol": result[8],
        "current_time": result[9]
    }

    return signal_columns


def get_signal_by_positionId(ticket_id):
    query = """
        SELECT s.* 
        FROM signals s
        INNER JOIN positions p ON p.signal_id = s.id
        WHERE p.position_id = ?
        LIMIT 1
    """
    results = signal_repo.execute_query(query, (ticket_id,))
    if results == None or len(results) == 0:
        return None

    result = results[0]

    # Map the result to a dictionary using the signal_columns as keys
    signal_columns = {
        "id": result[0],
        "telegram_channel_title": result[1],
        "telegram_message_id": result[2],
        "telegram_message_chatid": result[3],
        "open_price": result[4],
        "second_price": result[5],
        "stop_loss": result[6],
        "tp_list": result[7],
        "symbol": result[8],
        "current_time": result[9]
    }
    return signal_columns


def get_signal_positions_by_positionId(ticket_id):
    query = """
        SELECT * 
        FROM positions 
        WHERE signal_id = (SELECT signal_id FROM positions WHERE position_id = ?)
        ORDER BY id DESC
        LIMIT 2;
    """
    results = signal_repo.execute_query(query, (ticket_id,))
    
    if not results:  # More Pythonic way to check for empty results
        return []

    # Map all rows to a list of dictionaries
    position_columns = [
        {
            "id": row[0],
            "signal_id": row[1],
            "position_id": row[2],
            "user_id": row[3],
            "is_first": row[4],
            "is_second": row[5]
        }
        for row in results
    ]

    return position_columns  # Returns a list of dictionaries

def get_position_by_signal_id(signal_id, first=False, second=False):
    query = """
        SELECT * 
        FROM positions 
        WHERE signal_id = ? and (is_first = ? and is_second = ?)
        ORDER BY id DESC
        LIMIT 1;
    """
    results = signal_repo.execute_query(query, (signal_id, first, second,))
    
    if not results:  # More Pythonic way to check for empty results
        return None

    # Map all rows to a list of dictionaries
    position_columns = [
        {
            "id": row[0],
            "signal_id": row[1],
            "position_id": row[2],
            "user_id": row[3],
            "is_first": row[4],
            "is_second": row[5]
        }
        for row in results
    ]

    return position_columns[0]  # Returns a list of dictionaries