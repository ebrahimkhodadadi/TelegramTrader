from app.Database.Repository import SQLiteRepository


db_path = "trade.db"

## tables
#signal
signal_columns = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "telegram_channel_title": "TEXT NOT NULL",
    "telegram_message_id": "INTEGER NOT NULL",
    "open_price": "REAL NOT NULL",
    "second_price": "REAL NOT NULL",
    "stop_loss": "REAL NOT NULL",
    "tp_list": "TEXT NOT NULL",
    "symbol": "TEXT NOT NULL",
    "current_time": "TEXT NOT NULL"
}
#position
position_columns = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "signal_id": "INTEGER NOT NULL",
    "position_id": "INTEGER NOT NULL",
    "user_id": "INTEGER NOT NULL",
    "FOREIGN KEY(signal_id)": "REFERENCES Signal(id) ON DELETE CASCADE"
}

# Create repositories
signal_repo = SQLiteRepository(db_path, "Signal")
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
        return [float(x) for x in signal[0]['tp_list'].split(',')]
    return None

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
        return [float(x) for x in signal[0]['tp_list'].split(',')]
    return None

def get_last_signal_positions():
    """Read last signal positions from the database"""
    query = """
        SELECT TOP 2 p.position_id 
        FROM positions p
        ORDER BY p.signal_id DESC
    """
    positions = position_repo.execute_query(query)
    return [x['position_id'] for x in positions]

# Insert sample data

# position_repo.insert({"signal_id": signal_id})

# # Fetch and display records
# print("Signals:", signal_repo.get_all())
# print("Positions:", position_repo.get_all())
