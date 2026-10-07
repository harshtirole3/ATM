import sqlite3

# Create/connect to ATM database
connection = sqlite3.connect("atm.db")

cursor = connection.cursor()

# ---------------- USERS TABLE ----------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    account_no INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    pin TEXT NOT NULL,
    balance REAL NOT NULL,
    daily_withdrawal REAL DEFAULT 0,
account_locked INTEGER DEFAULT 0,
pin_attempts INTEGER DEFAULT 0)
""")
# Add PIN attempts column if it does not already exist
try:
    cursor.execute("ALTER TABLE users ADD COLUMN pin_attempts INTEGER DEFAULT 0")
except sqlite3.OperationalError:
    pass

# ---------------- TRANSACTIONS TABLE ----------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_no INTEGER,
    transaction_type TEXT,
    amount REAL,
    balance_after REAL,
    date TEXT,
    time TEXT
)
""")

# ---------------- ATM CASH TABLE ----------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS atm_cash (
    denomination INTEGER PRIMARY KEY,
    note_count INTEGER
)
""")

# ---------------- SAMPLE USERS ----------------

cursor.execute("""
INSERT OR IGNORE INTO users
(account_no, name, pin, balance)
VALUES (1001, 'Muskan', '1234', 50000)
""")

cursor.execute("""
INSERT OR IGNORE INTO users
(account_no, name, pin, balance)
VALUES (1002, 'Rahul', '5678', 25000)
""")

# ---------------- ATM CASH ----------------

cash_data = [
    (500, 100),
    (200, 100),
    (100, 100),
    (50, 100)
]

cursor.executemany("""
INSERT OR IGNORE INTO atm_cash
(denomination, note_count)
VALUES (?, ?)
""", cash_data)

# Save changes
connection.commit()

# Close database
connection.close()

print("ATM Database created successfully!")