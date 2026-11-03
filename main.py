import csv
import io
from flask import Flask, render_template, request, redirect, url_for, Response
from database import init_db
from expense_manager import (
    add_expense, get_all_expenses, get_expense_by_id, 
    update_expense, delete_expense, get_filtered_expenses, set_budget
)
from reports import get_dashboard_summary

app = Flask(__name__)

init_db()

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        if "budget_amount" in request.form:
            month_key = request.form.get("month_key")
            amount = request.form.get("budget_amount")
            if month_key and amount:
                set_budget(month_key, float(amount))
            return redirect(url_for("home"))
            
        date = request.form.get("date")
        category = request.form.get("category")
        description = request.form.get("description")
        amount = request.form.get("amount")
        is_recurring = 1 if request.form.get("is_recurring") else 0
        
        if date and category and amount:
            add_expense(date, category, description, float(amount), is_recurring)
        return redirect(url_for("home"))
        
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    filter_category = request.args.get("category")
    search_query = request.args.get("search")
    
    summary = get_dashboard_summary()
    
    if start_date or end_date or search_query or (filter_category and filter_category != "All Categories"):
        expenses = get_filtered_expenses(start_date, end_date, filter_category, search_query)
    else:
        expenses = get_all_expenses(limit=5)
        
    return render_template(
        "home.html", 
        summary=summary, 
        expenses=expenses, 
        selected_start=start_date or "", 
        selected_end=end_date or "",
        selected_category=filter_category or "All Categories",
        selected_search=search_query or ""
    )

@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
def edit(expense_id):
    expense = get_expense_by_id(expense_id)
    if request.method == "POST":
        date = request.form.get("date")
        category = request.form.get("category")
        description = request.form.get("description")
        amount = request.form.get("amount")
        is_recurring = 1 if request.form.get("is_recurring") else 0
        
        update_expense(expense_id, date, category, description, float(amount), is_recurring)
        return redirect(url_for("home"))
        
    return render_template("edit.html", expense=expense)

@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete(expense_id):
    delete_expense(expense_id)
    return redirect(url_for("home"))

@app.route("/reports")
def reports():
    summary = get_dashboard_summary()
    all_expenses = get_all_expenses()
    return render_template("reports.html", summary=summary, expenses=all_expenses)

@app.route("/export")
def export_csv():
    all_expenses = get_all_expenses()
    
    def generate():
        data = io.StringIO()
        writer = csv.writer(data)
        writer.writerow(["ID", "Date", "Category", "Description", "Amount", "Is Recurring"])
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)
        
        for exp in all_expenses:
            writer.writerow([exp["id"], exp["date"], exp["category"], exp["description"], exp["amount"], "Yes" if exp["is_recurring"] else "No"])
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    response = Response(generate(), mimetype="text/csv")
    response.headers.set("Content-Disposition", "attachment", filename="expense_report.csv")
    return response

if __name__ == "__main__":
    app.run(debug=True)