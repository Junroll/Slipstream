import sqlite3
import os

DB_NAME = 'crypto_bot.db'

def init_db():
    db_exists = os.path.exists(DB_NAME)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            mode TEXT DEFAULT 'waterfall',
            threshold_pct REAL DEFAULT 0.05,
            floor_pct REAL DEFAULT -0.20
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            action TEXT,
            coin TEXT,
            amount_usd REAL,
            status TEXT
        )
    ''')
    
    if not db_exists:
        cursor.execute("INSERT INTO settings (mode, threshold_pct, floor_pct) VALUES ('waterfall', 0.05, -0.20)")
        print("✅ New database created and seeded with default settings.")
    
    conn.commit()
    conn.close()

def log_transaction(action, coin, amount_usd, status="SUCCESS"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transactions (action, coin, amount_usd, status) VALUES (?, ?, ?, ?)",
        (action, coin, amount_usd, status)
    )
    conn.commit()
    conn.close()

def get_settings():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT mode, threshold_pct, floor_pct FROM settings LIMIT 1")
    settings = cursor.fetchone()
    conn.close()
    return {"mode": settings[0], "threshold": settings[1], "floor": settings[2]}

init_db()