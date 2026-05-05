import sqlite3

DB_NAME = "users.db"

def get_connection():
    return sqlite3.connect(DB_NAME)


def create_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS auth_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        income REAL,
        credit REAL,
        eligibility TEXT,
        purpose TEXT,
        created_at TEXT
    )
    """)
  

    conn.commit()
    conn.close()