import sqlite3

conn = sqlite3.connect("trading.db", check_same_thread=False)
cursor = conn.cursor()

# =============================
# CREATE TABLES
# =============================
cursor.execute("""
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock TEXT,
    entry REAL,
    exit REAL,
    pnl REAL,
    result TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock TEXT,
    score REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

# =============================
# INSERT FUNCTIONS
# =============================
def insert_trade(stock, entry, exit_price, pnl, result):
    cursor.execute(
        "INSERT INTO trades (stock, entry, exit, pnl, result) VALUES (?,?,?,?,?)",
        (stock, entry, exit_price, pnl, result)
    )
    conn.commit()

def insert_signal(stock, score):
    cursor.execute(
        "INSERT INTO signals (stock, score) VALUES (?,?)",
        (stock, score)
    )
    conn.commit()

# =============================
# FETCH
# =============================
def fetch_trades():
    cursor.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 100")
    return cursor.fetchall()