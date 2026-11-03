from database import get_db_connection

def add_expense(date, category, description, amount, is_recurring=0):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO expenses (date, category, description, amount, is_recurring) VALUES (?, ?, ?, ?, ?)",
        (date, category, description, amount, is_recurring)
    )
    conn.commit()
    conn.close()

def get_all_expenses(limit=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if limit:
        cursor.execute("SELECT * FROM expenses ORDER BY date DESC LIMIT ?", (limit,))
    else:
        cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
    expenses = cursor.fetchall()
    conn.close()
    return expenses

def get_expense_by_id(expense_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
    expense = cursor.fetchone()
    conn.close()
    return expense

def update_expense(expense_id, date, category, description, amount, is_recurring=0):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE expenses SET date = ?, category = ?, description = ?, amount = ?, is_recurring = ? WHERE id = ?",
        (date, category, description, amount, is_recurring, expense_id)
    )
    conn.commit()
    conn.close()

def delete_expense(expense_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()

def get_filtered_expenses(start_date=None, end_date=None, category=None, search=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM expenses WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
        
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
        
    if category and category != "All Categories":
        query += " AND category = ?"
        params.append(category)
        
    if search:
        query += " AND (description LIKE ? OR category LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
        
    query += " ORDER BY date DESC"
    
    cursor.execute(query, params)
    expenses = cursor.fetchall()
    conn.close()
    return expenses

def set_budget(month_year, amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO budgets (month_year, amount) VALUES (?, ?)
        ON CONFLICT(month_year) DO UPDATE SET amount = ?
    """, (month_year, amount, amount))
    conn.commit()
    conn.close()

def get_budget(month_year):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT amount FROM budgets WHERE month_year = ?", (month_year,))
    row = cursor.fetchone()
    conn.close()
    return row["amount"] if row else 10000.0