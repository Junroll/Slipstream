import sqlite3
import os

DB_NAME = 'crypto_bot.db'

def init_db():
    db_exists = os.path.exists(DB_NAME)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Settings table with Telegram control columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            mode TEXT DEFAULT 'waterfall',
            threshold_pct REAL DEFAULT 0.05,
            floor_pct REAL DEFAULT -0.20,
            is_paused INTEGER DEFAULT 0,
            is_muted INTEGER DEFAULT 0,
            message_mode TEXT DEFAULT 'per_transaction'
        )
    ''')
    
    # 2. Transactions table
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
    
    # 3. High-Water Mark Memory
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_state (
            id INTEGER PRIMARY KEY,
            high_water_mark REAL
        )
    ''')

    # 4. Blacklist table for ignoring specific coins
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blacklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coin TEXT UNIQUE
        )
    ''')
    
    if not db_exists:
        cursor.execute('''
            INSERT INTO settings 
            (mode, threshold_pct, floor_pct, is_paused, is_muted, message_mode) 
            VALUES ('waterfall', 0.05, -0.20, 1, 0, 'per_transaction')
        ''')
        
        # Seed default blacklist items (Fiat currencies the bot shouldn't trade)
        cursor.execute("INSERT INTO blacklist (coin) VALUES ('USD')")
        cursor.execute("INSERT INTO blacklist (coin) VALUES ('USDC')")
        
        print("✅ New database created and seeded with expanded Telegram settings.")
        
    cursor.execute("SELECT high_water_mark FROM bot_state WHERE id = 1")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO bot_state (id, high_water_mark) VALUES (1, 0.0)")
        print("High-Water Mark tracking initialized.")
    
    conn.commit()
    conn.close()

# --- SETTINGS & TELEGRAM CONTROL FUNCTIONS ---

def get_settings():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Converts the row into a dictionary automatically!
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM settings WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}

def update_setting(column_name, value):
    """A universal function for the Telegram bot to update any setting."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Safe to use f-string here because column_name is hardcoded in our bot.py
    cursor.execute(f"UPDATE settings SET {column_name} = ? WHERE id = 1", (value,))
    conn.commit()
    conn.close()

# --- BLACKLIST FUNCTIONS ---

def get_blacklist():
    """Returns a list of all blacklisted coins."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT coin FROM blacklist")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def add_to_blacklist(coin):
    """Adds a coin. Returns True if successful, False if already exists."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO blacklist (coin) VALUES (?)", (coin.upper(),))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False 
    conn.close()
    return success

def remove_from_blacklist(coin):
    """Removes a coin. Returns True if deleted, False if it wasn't there."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM blacklist WHERE coin = ?", (coin.upper(),))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# --- TRANSACTION & STATE FUNCTIONS ---

def log_transaction(action, coin, amount_usd, status="SUCCESS"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transactions (action, coin, amount_usd, status) VALUES (?, ?, ?, ?)",
        (action, coin, amount_usd, status)
    )
    conn.commit()
    conn.close()

def get_recent_transactions(limit=10):
    """Fetches the most recent transactions for the /history command."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, action, coin, amount_usd FROM transactions ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_high_water_mark():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT high_water_mark FROM bot_state WHERE id = 1")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0.0

def update_high_water_mark(new_value):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE bot_state SET high_water_mark = ? WHERE id = 1", (new_value,))
    conn.commit()
    conn.close()

# Auto-run the setup when the module is imported
init_db()