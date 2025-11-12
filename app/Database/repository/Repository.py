import sqlite3
from typing import List, Tuple, Any, Dict, TypeVar, Generic

T = TypeVar('T')

class SQLiteRepository(Generic[T]):
    def __init__(self, db_path: str, table_name: str):
        self.db_path = db_path
        self.table_name = table_name
    
    def _connect(self):
        return sqlite3.connect(self.db_path)
    
    def create_table(self, columns: Dict[str, str]):
        with self._connect() as conn:
            cursor = conn.cursor()
            columns_def = ', '.join(f'{col} {dtype}' for col, dtype in columns.items())
            query = f'CREATE TABLE IF NOT EXISTS {self.table_name} ({columns_def})'
            cursor.execute(query)
            conn.commit()
    
    def insert(self, data: Dict[str, Any]):
        with self._connect() as conn:
            cursor = conn.cursor()
            columns = ', '.join(data.keys())
            placeholders = ', '.join('?' * len(data))
            values = tuple(data.values())
            query = f'INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})'
            cursor.execute(query, values)
            conn.commit()
            return cursor.lastrowid
    
    def get_all(self) -> List[Tuple]:
        with self._connect() as conn:
            cursor = conn.cursor()
            query = f'SELECT * FROM {self.table_name}'
            cursor.execute(query)
            return cursor.fetchall()
    
    def get_by_id(self, record_id: Any) -> Tuple:
        with self._connect() as conn:
            cursor = conn.cursor()
            query = f'SELECT * FROM {self.table_name} WHERE id = ?'
            cursor.execute(query, (record_id,))
            return cursor.fetchone()
    
    def update(self, record_id: Any, data: Dict[str, Any]):
        with self._connect() as conn:
            cursor = conn.cursor()
            set_clause = ', '.join(f'{col} = ?' for col in data.keys())
            values = tuple(data.values()) + (record_id,)
            query = f'UPDATE {self.table_name} SET {set_clause} WHERE id = ?'
            cursor.execute(query, values)
            conn.commit()
    
    def delete(self, record_id: Any):
        with self._connect() as conn:
            cursor = conn.cursor()
            query = f'DELETE FROM {self.table_name} WHERE id = ?'
            cursor.execute(query, (record_id,))
            conn.commit()
    
    def execute_query(self, query: str, params: Tuple = ()) -> List[Tuple]:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
