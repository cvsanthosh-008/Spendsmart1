import os
import csv
import io
import sqlite3
from functools import wraps
from datetime import date, datetime

from flask import (
    Flask, request, redirect, url_for,
    session, flash, render_template_string,
    Response
)

from werkzeug.security import generate_password_hash, check_password_hash


# -----------------------------------
# FLASK CONFIGURATION
# -----------------------------------

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "spendsmart-change-this-secret-key"
)

DATABASE = os.environ.get("DATABASE_PATH", "spendsmart.db")


# -----------------------------------
# DATABASE CONNECTION
# -----------------------------------

def get_db():

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    return conn


# -----------------------------------
# CREATE DATABASE TABLES
# -----------------------------------

def init_db():

    with get_db() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL,
                is_recurring INTEGER DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                month_key TEXT NOT NULL,
                amount REAL NOT NULL,
                UNIQUE(user_id, month_key)
            )
        """)


init_db()


# -----------------------------------
# LOGIN PROTECTION
# -----------------------------------

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


# -----------------------------------
# COMMON PAGE DESIGN
# -----------------------------------

BASE = """
<!DOCTYPE html>
<html>
<head>
    <title>SpendSmart</title>

    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f4f6fa;
            color: #263238;
        }

        header {
            background: #172554;
            color: white;
            padding: 20px 7%;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }

        header h2 {
            margin: 0;
        }

        nav a {
            color: white;
            text-decoration: none;
            margin: 8px;
        }

        .container {
            max-width: 1100px;
            margin: 30px auto;
            padding: 15px;
        }

        .card {
            background: white;
            padding: 22px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 3px 12px rgba(0,0,0,0.06);
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }

        .stat {
            background: white;
            padding: 22px;
            border-radius: 12px;
            box-shadow: 0 3px 12px rgba(0,0,0,0.06);
        }

        .stat h3 {
            color: #64748b;
            font-size: 15px;
        }

        .stat p {
            font-size: 25px;
            font-weight: bold;
            color: #2563eb;
        }

        input, select, textarea {
            width: 100%;
            padding: 12px;
            margin: 8px 0 15px;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
        }

        button, .btn {
            display: inline-block;
            background: #2563eb;
            color: white;
            padding: 11px 18px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            text-decoration: none;
        }

        .danger {
            background: #dc2626;
        }

        .green {
            background: #16a34a;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }

        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }

        th {
            background: #eff6ff;
        }

        .message {
            padding: 12px;
            background: #dbeafe;
            margin-bottom: 15px;
            border-radius: 6px;
        }

        .auth {
            max-width: 420px;
            margin: 70px auto;
            padding: 30px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 3px 15px rgba(0,0,0,0.1);
        }

        .auth h1, .auth h2 {
            text-align: center;
        }

        .auth button {
            width: 100%;
        }

        a {
            color: #2563eb;
        }

        @media(max-width: 600px) {
            table {
                font-size: 12px;
            }

            th, td {
                padding: 7px;
            }
        }
    </style>
</head>

<body>

<header>
    <h2>SpendSmart 💰</h2>

    {% if session.get('user_id') %}
    <nav>
        <a href="{{ url_for('home') }}">Dashboard</a>
        <a href="{{ url_for('reports') }}">Reports</a>
        <a href="{{ url_for('logout') }}">Logout</a>
    </nav>
    {% endif %}
</header>

<div class="container">

{% with messages = get_flashed_messages() %}
    {% for message in messages %}
        <div class="message">{{ message }}</div>
    {% endfor %}
{% endwith %}

{{ content|safe }}

</div>

</body>
</html>
"""


def render_page(content, **kwargs):

    return render_template_string(
        BASE,
        content=render_template_string(content, **kwargs)
    )


# -----------------------------------
# REGISTRATION
# -----------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if session.get("user_id"):
        return redirect(url_for("home"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Please fill in all fields.")

        elif len(password) < 8:
            flash("Password must have at least 8 characters.")

        else:

            try:

                with get_db() as conn:

                    conn.execute("""
                        INSERT INTO users (name, email, password_hash)
                        VALUES (?, ?, ?)
                    """, (
                        name,
                        email,
                        generate_password_hash(password)
                    ))

                    user = conn.execute(
                        "SELECT id FROM users WHERE email = ?",
                        (email,)
                    ).fetchone()

                session.clear()
                session["user_id"] = user["id"]
                session["user_name"] = name

                return redirect(url_for("home"))

            except sqlite3.IntegrityError:

                flash("Email already registered. Please login.")

    content = """
    <div class="auth">

        <h1>SpendSmart 💰</h1>
        <h2>Create Account</h2>

        <form method="POST">

            <label>Full Name</label>
            <input type="text" name="name" required>

            <label>Email</label>
            <input type="email" name="email" required>

            <label>Password</label>
            <input type="password" name="password"
                   minlength="8" required>

            <button type="submit">Register</button>

        </form>

        <p style="text-align:center">
            Already have an account?
            <a href="{{ url_for('login') }}">Login</a>
        </p>

    </div>
    """

    return render_page(content)


# -----------------------------------
# LOGIN
# -----------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if session.get("user_id"):
        return redirect(url_for("home"))

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        with get_db() as conn:

            user = conn.execute("""
                SELECT * FROM users WHERE email = ?
            """, (email,)).fetchone()

        if user and check_password_hash(
            user["password_hash"], password
        ):

            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect(url_for("home"))

        flash("Invalid email or password.")

    content = """
    <div class="auth">

        <h1>SpendSmart 💰</h1>
        <h2>Welcome Back!</h2>

        <form method="POST">

            <label>Email</label>
            <input type="email" name="email" required>

            <label>Password</label>
            <input type="password" name="password" required>

            <button type="submit">Login</button>

        </form>

        <p style="text-align:center">
            New user?
            <a href="{{ url_for('register') }}">Create Account</a>
        </p>

    </div>
    """

    return render_page(content)


# -----------------------------------
# LOGOUT
# -----------------------------------

@app.route("/logout")
def logout():

    session.clear()

    flash("You have logged out successfully.")

    return redirect(url_for("login"))


# -----------------------------------
# DASHBOARD
# -----------------------------------

@app.route("/", methods=["GET", "POST"])
@login_required
def home():

    user_id = session["user_id"]

    if request.method == "POST":

        if "budget_amount" in request.form:

            month_key = request.form.get("month_key")
            amount = request.form.get("budget_amount")

            try:

                amount = float(amount)

                if amount <= 0:
                    raise ValueError

                with get_db() as conn:

                    conn.execute("""
                        INSERT INTO budgets (user_id, month_key, amount)
                        VALUES (?, ?, ?)
                        ON CONFLICT(user_id, month_key)
                        DO UPDATE SET amount = excluded.amount
                    """, (user_id, month_key, amount))

                flash("Budget updated successfully.")

            except (ValueError, TypeError):
                flash("Please enter a valid budget.")

            return redirect(url_for("home"))

        expense_date = request.form.get("date")
        category = request.form.get("category")
        description = request.form.get("description")
        amount = request.form.get("amount")

        recurring = 1 if request.form.get("is_recurring") else 0

        try:

            amount = float(amount)

            if amount <= 0 or not expense_date or not category:
                raise ValueError

            with get_db() as conn:

                conn.execute("""
                    INSERT INTO expenses
                    (user_id, date, category, description, amount, is_recurring)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    expense_date,
                    category,
                    description,
                    amount,
                    recurring
                ))

            flash("Expense added successfully.")

        except (ValueError, TypeError):
            flash("Please enter valid expense details.")

        return redirect(url_for("home"))

    # FILTERS

    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    category_filter = request.args.get("category", "")
    search = request.args.get("search", "")

    query = "SELECT * FROM expenses WHERE user_id = ?"
    params = [user_id]

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    if category_filter and category_filter != "All Categories":
        query += " AND category = ?"
        params.append(category_filter)

    if search:
        query += " AND (description LIKE ? OR category LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY date DESC, id DESC"

    with get_db() as conn:

        expenses = conn.execute(
            query, params
        ).fetchall()

        total = conn.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses WHERE user_id = ?
        """, (user_id,)).fetchone()[0]

        today_total = conn.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE user_id = ? AND date = ?
        """, (user_id, date.today().isoformat())).fetchone()[0]

        month_key = date.today().strftime("%Y-%m")

        month_total = conn.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE user_id = ? AND substr(date, 1, 7) = ?
        """, (user_id, month_key)).fetchone()[0]

        budget = conn.execute("""
            SELECT amount FROM budgets
            WHERE user_id = ? AND month_key = ?
        """, (user_id, month_key)).fetchone()

        budget_amount = budget["amount"] if budget else 0

    categories = [
        "Food", "Travel", "Shopping", "Bills",
        "Education", "Health", "Entertainment", "Other"
    ]

    content = """
    <h1>Welcome, {{ session.get('user_name') }}! 👋</h1>
    <p>Manage your money wisely with SpendSmart.</p>

    <div class="grid">

        <div class="stat">
            <h3>Total Expenses</h3>
            <p>₹{{ "%.2f"|format(total) }}</p>
        </div>

        <div class="stat">
            <h3>Today's Expenses</h3>
            <p>₹{{ "%.2f"|format(today_total) }}</p>
        </div>

        <div class="stat">
            <h3>This Month</h3>
            <p>₹{{ "%.2f"|format(month_total) }}</p>
        </div>

        <div class="stat">
            <h3>Monthly Budget</h3>
            <p>₹{{ "%.2f"|format(budget_amount) }}</p>
        </div>

    </div>

    <div class="card">
        <h2>Set Monthly Budget</h2>

        <form method="POST">

            <label>Month</label>
            <input type="month" name="month_key"
                   value="{{ month_key }}" required>

            <label>Budget Amount</label>
            <input type="number" name="budget_amount"
                   min="0.01" step="0.01" required>

            <button type="submit">Save Budget</button>

        </form>
    </div>

    <div class="card">

        <h2>Add New Expense</h2>

        <form method="POST">

            <label>Date</label>
            <input type="date" name="date"
                   value="{{ today }}" required>

            <label>Category</label>
            <select name="category" required>
                {% for c in categories %}
                    <option value="{{ c }}">{{ c }}</option>
                {% endfor %}
            </select>

            <label>Description</label>
            <input type="text" name="description"
                   placeholder="Enter description">

            <label>Amount (₹)</label>
            <input type="number" name="amount"
                   min="0.01" step="0.01" required>

            <label>
                <input type="checkbox" name="is_recurring"
                       style="width:auto">
                Recurring Expense
            </label>

            <br><br>

            <button type="submit">Add Expense</button>

        </form>

    </div>

    <div class="card">

        <h2>Filter Expenses</h2>

        <form method="GET">

            <label>From Date</label>
            <input type="date" name="start_date"
                   value="{{ start_date }}">

            <label>To Date</label>
            <input type="date" name="end_date"
                   value="{{ end_date }}">

            <label>Category</label>
            <select name="category">
                <option>All Categories</option>
                {% for c in categories %}
                    <option value="{{ c }}"
                    {% if category_filter == c %}selected{% endif %}>
                        {{ c }}
                    </option>
                {% endfor %}
            </select>

            <label>Search</label>
            <input type="text" name="search"
                   value="{{ search }}"
                   placeholder="Search expenses">

            <button type="submit">Apply Filter</button>

            <a class="btn" href="{{ url_for('home') }}">Reset</a>

        </form>

    </div>

    <div class="card">

        <h2>Recent Expenses</h2>

        <div style="overflow-x:auto">

        <table>

            <tr>
                <th>Date</th>
                <th>Category</th>
                <th>Description</th>
                <th>Amount</th>
                <th>Action</th>
            </tr>

            {% for e in expenses %}

            <tr>

                <td>{{ e.date }}</td>
                <td>{{ e.category }}</td>
                <td>{{ e.description }}</td>
                <td>₹{{ "%.2f"|format(e.amount) }}</td>

                <td>
                    <a href="{{ url_for('edit', expense_id=e.id) }}">
                        Edit
                    </a>

                    <form method="POST"
                          action="{{ url_for('delete', expense_id=e.id) }}"
                          style="display:inline">

                        <button class="danger" type="submit"
                                onclick="return confirm('Delete this expense?')">
                            Delete
                        </button>

                    </form>
                </td>

            </tr>

            {% else %}

            <tr>
                <td colspan="5">No expenses found.</td>
            </tr>

            {% endfor %}

        </table>

        </div>

        <br>

        <a class="btn green" href="{{ url_for('export_csv') }}">
            Download CSV
        </a>

        <a class="btn" href="{{ url_for('reports') }}">
            View Reports
        </a>

    </div>
    """

    return render_page(
        content,
        expenses=expenses,
        total=total,
        today_total=today_total,
        month_total=month_total,
        budget_amount=budget_amount,
        month_key=month_key,
        today=date.today().isoformat(),
        categories=categories,
        start_date=start_date,
        end_date=end_date,
        category_filter=category_filter,
        search=search
    )


# -----------------------------------
# EDIT EXPENSE
# -----------------------------------

@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
@login_required
def edit(expense_id):

    user_id = session["user_id"]

    with get_db() as conn:

        expense = conn.execute("""
            SELECT * FROM expenses
            WHERE id = ? AND user_id = ?
        """, (expense_id, user_id)).fetchone()

    if expense is None:
        return "Expense not found", 404

    if request.method == "POST":

        try:

            amount = float(request.form.get("amount"))

            if amount <= 0:
                raise ValueError

            with get_db() as conn:

                conn.execute("""
                    UPDATE expenses
                    SET date = ?, category = ?,
                        description = ?, amount = ?,
                        is_recurring = ?
                    WHERE id = ? AND user_id = ?
                """, (
                    request.form.get("date"),
                    request.form.get("category"),
                    request.form.get("description"),
                    amount,
                    1 if request.form.get("is_recurring") else 0,
                    expense_id,
                    user_id
                ))

            flash("Expense updated successfully.")

            return redirect(url_for("home"))

        except (ValueError, TypeError):
            flash("Please enter a valid amount.")

    content = """
    <div class="card">

        <h2>Edit Expense</h2>

        <form method="POST">

            <label>Date</label>
            <input type="date" name="date"
                   value="{{ expense.date }}" required>

            <label>Category</label>
            <input type="text" name="category"
                   value="{{ expense.category }}" required>

            <label>Description</label>
            <input type="text" name="description"
                   value="{{ expense.description or '' }}">

            <label>Amount</label>
            <input type="number" name="amount"
                   value="{{ expense.amount }}"
                   min="0.01" step="0.01" required>

            <label>
                <input type="checkbox" name="is_recurring"
                       style="width:auto"
                       {% if expense.is_recurring %}checked{% endif %}>
                Recurring
            </label>

            <br><br>

            <button type="submit">Update Expense</button>

            <a class="btn" href="{{ url_for('home') }}">Cancel</a>

        </form>

    </div>
    """

    return render_page(content, expense=expense)


# -----------------------------------
# DELETE EXPENSE
# -----------------------------------

@app.route("/delete/<int:expense_id>", methods=["POST"])
@login_required
def delete(expense_id):

    with get_db() as conn:

        conn.execute("""
            DELETE FROM expenses
            WHERE id = ? AND user_id = ?
        """, (expense_id, session["user_id"]))

    flash("Expense deleted.")

    return redirect(url_for("home"))


# -----------------------------------
# REPORTS
# -----------------------------------

@app.route("/reports")
@login_required
def reports():

    user_id = session["user_id"]

    with get_db() as conn:

        expenses = conn.execute("""
            SELECT * FROM expenses
            WHERE user_id = ?
            ORDER BY date DESC
        """, (user_id,)).fetchall()

        category_data = conn.execute("""
            SELECT category, SUM(amount) AS total
            FROM expenses
            WHERE user_id = ?
            GROUP BY category
            ORDER BY total DESC
        """, (user_id,)).fetchall()

        total = conn.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses WHERE user_id = ?
        """, (user_id,)).fetchone()[0]

    content = """
    <div class="card">

        <h2>Expense Reports 📊</h2>

        <h3>Total Spending: ₹{{ "%.2f"|format(total) }}</h3>

        <h3>Category-wise Expenses</h3>

        <table>
            <tr>
                <th>Category</th>
                <th>Total Amount</th>
            </tr>

            {% for c in category_data %}
            <tr>
                <td>{{ c.category }}</td>
                <td>₹{{ "%.2f"|format(c.total) }}</td>
            </tr>
            {% else %}
            <tr>
                <td colspan="2">No reports available.</td>
            </tr>
            {% endfor %}
        </table>

        <br>

        <a class="btn" href="{{ url_for('home') }}">
            Back to Dashboard
        </a>

    </div>
    """

    return render_page(
        content,
        total=total,
        category_data=category_data,
        expenses=expenses
    )


# -----------------------------------
# EXPORT CSV
# -----------------------------------

@app.route("/export")
@login_required
def export_csv():

    with get_db() as conn:

        expenses = conn.execute("""
            SELECT * FROM expenses
            WHERE user_id = ?
            ORDER BY date DESC
        """, (session["user_id"],)).fetchall()

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "ID", "Date", "Category",
        "Description", "Amount", "Recurring"
    ])

    for e in expenses:

        writer.writerow([
            e["id"],
            e["date"],
            e["category"],
            e["description"],
            e["amount"],
            "Yes" if e["is_recurring"] else "No"
        ])

    response = Response(
        output.getvalue(),
        mimetype="text/csv"
    )

    response.headers.set(
        "Content-Disposition",
        "attachment",
        filename="spendsmart_report.csv"
    )

    return response


# -----------------------------------
# RUN APPLICATION
# -----------------------------------

if __name__ == "__main__":

    app.run(debug=True)
