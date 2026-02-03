from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# ---------- DATABASE CONNECTION ----------
def get_db_connection():
    conn = sqlite3.connect("expenses.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------- CREATE TABLE ----------
def create_table():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            note TEXT
        )
    """)
    conn.commit()
    conn.close()

create_table()

# ---------- ROUTES ----------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/add", methods=["GET", "POST"])
def add_expense():
    if request.method == "POST":
        amount = request.form["amount"]
        category = request.form["category"]
        date = request.form["date"]
        note = request.form["note"]

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO expenses (amount, category, date, note) VALUES (?, ?, ?, ?)",
            (amount, category, date, note)
        )
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("add_expense.html")

@app.route("/expenses")
def view_expenses():
    conn = get_db_connection()
    expenses = conn.execute(
        "SELECT * FROM expenses ORDER BY date DESC"
    ).fetchall()
    conn.close()

    total = sum(expense["amount"] for expense in expenses)

    return render_template(
        "view_expenses.html",
        expenses=expenses,
        total=total
    )

@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):
    conn = get_db_connection()
    expense = conn.execute(
        "SELECT * FROM expenses WHERE id = ?", (expense_id,)
    ).fetchone()

    if request.method == "POST":
        amount = request.form["amount"]
        category = request.form["category"]
        date = request.form["date"]
        note = request.form["note"]

        conn.execute(
            "UPDATE expenses SET amount = ?, category = ?, date = ?, note = ? WHERE id = ?",
            (amount, category, date, note, expense_id)
        )
        conn.commit()
        conn.close()
        return redirect("/expenses")

    conn.close()
    return render_template("edit_expense.html", expense=expense)

@app.route("/delete/<int:expense_id>")
def delete_expense(expense_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()
    return redirect("/expenses")
# ---------- RUN APP ----------
if __name__ == "__main__":
    app.run(debug=True)

