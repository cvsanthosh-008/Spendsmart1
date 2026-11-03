import sqlite3

DB_NAME = "expense.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            amount REAL NOT NULL,
            is_recurring INTEGER DEFAULT 0
        )
    ''')
    
    # Safety check: Automatically add the column if an old table exists without it
    try:
        cursor.execute("ALTER TABLE expenses ADD COLUMN is_recurring INTEGER DEFAULT 0;")
    except sqlite3.OperationalError:
        pass  # Column already exists, safe to ignore
    
    # Budgets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month_year TEXT UNIQUE,
            amount REAL NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

# Run this once to fix/initialize the database
if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")