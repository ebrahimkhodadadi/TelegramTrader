from app.database.Repository import SQLiteRepository


db_path = "trade.db"

## tables
#signal
signal_columns = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "telegram_channel_title": "TEXT NOT NULL",
    "telegram_message_id": "INTEGER NOT NULL",
    "open_price": "REAL NOT NULL",
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
    "FOREIGN KEY(signal_id)": "REFERENCES Signal(id) ON DELETE CASCADE"
}

# Create repositories
signal_repo = SQLiteRepository(db_path, "Signal")
position_repo = SQLiteRepository(db_path, "Positions")

# Create tables
def DoMigrations():
    signal_repo.create_table(signal_columns)
    position_repo.create_table(position_columns)

# Insert sample data

# position_repo.insert({"signal_id": signal_id})

# # Fetch and display records
# print("Signals:", signal_repo.get_all())
# print("Positions:", position_repo.get_all())
