import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'bookings.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_id TEXT,
                service_name TEXT,
                price INTEGER,
                date TEXT,
                time TEXT,
                client_name TEXT,
                client_phone TEXT,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

init_db()
