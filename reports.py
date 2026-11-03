from database import get_db_connection
from datetime import datetime
from collections import defaultdict
from expense_manager import get_budget

def get_dashboard_summary():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total Expenses
    cursor.execute("SELECT SUM(amount) FROM expenses")
    total_expenses = cursor.fetchone()[0] or 0.0
    
    # Total Transactions Count
    cursor.execute("SELECT COUNT(*) FROM expenses")
    total_transactions = cursor.fetchone()[0] or 0
    
    # Category Breakdown for Pie Chart
    cursor.execute("""
        SELECT category, SUM(amount) as total 
        FROM expenses 
        GROUP BY category
        ORDER BY total DESC
    """)
    category_rows = cursor.fetchall()
    category_data = [{"category": row["category"], "total": row["total"]} for row in category_rows]
    
    # Fetch all records for monthly breakdown
    cursor.execute("SELECT date, amount FROM expenses")
    all_rows = cursor.fetchall()
    conn.close()
    
    monthly_totals = defaultdict(float)
    current_month_key = datetime.now().strftime("%Y-%m")
    current_month_spent = 0.0
    
    for row in all_rows:
        try:
            dt = datetime.strptime(row["date"], "%Y-%m-%d")
            month_str = dt.strftime("%b")
            monthly_totals[month_str] += row["amount"]
            
            if dt.strftime("%Y-%m") == current_month_key:
                current_month_spent += row["amount"]
        except ValueError:
            pass

    # Budget tracking for current month
    monthly_budget = get_budget(current_month_key)
    budget_percentage = min(round((current_month_spent / monthly_budget) * 100, 1), 100) if monthly_budget > 0 else 0

    # Generate Smart Insights
    insights = []
    if category_data:
        top_cat = category_data[0]
        insights.append(f"🔥 Your highest spending category is <b>{top_cat['category']}</b> with ₹{top_cat['total']}.")
    
    if budget_percentage >= 90:
        insights.append("⚠️ Warning: You have used over 90% of your monthly budget!")
    elif budget_percentage > 0:
        insights.append(f"✅ You are currently within budget ({budget_percentage}% of monthly limit used).")
    else:
        insights.append("💡 Tip: Start logging your daily transactions to see deeper financial trends.")

    return {
        "total_expenses": total_expenses,
        "total_transactions": total_transactions,
        "monthly_average": round(total_expenses / max(len(monthly_totals), 1), 2),
        "category_data": category_data,
        "monthly_totals": dict(monthly_totals),
        "current_month_spent": current_month_spent,
        "monthly_budget": monthly_budget,
        "budget_percentage": budget_percentage,
        "current_month_key": current_month_key,
        "insights": insights
    }