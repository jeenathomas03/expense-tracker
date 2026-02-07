from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime, timedelta


app = Flask(__name__)
app.secret_key = "secret123"   

# __________ DATABASE CONNECTION __________

def get_db_connection():
    conn = sqlite3.connect("expenses.db")
    conn.row_factory = sqlite3.Row
    return conn

# __________ CREATE TABLES __________

def create_table():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            note TEXT
        )
    """)
    conn.commit()
    conn.close()

# __________ LOGIN __________

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect("/")
        else:
            return "Invalid username or password"

    return render_template("login.html")

# __________ SIGN UP __________

@app.route("/signup", methods=["POST"])
def signup():
    username = request.form["username"]
    password = request.form["password"]

    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return "Username already exists"
    finally:
        conn.close()

    return redirect("/login")
 
 # __________ DASHBOARD __________

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    return f"<h1>Welcome {session['user']} 🎉</h1><a href='/logout'>Logout</a>"


# __________ LOGOUT __________

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

# __________ HOME __________

@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    return render_template("index.html")

# __________ ADD EXPENSE __________

@app.route("/add", methods=["GET", "POST"])
def add_expense():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        amount = request.form["amount"]
        category = request.form["category"]
        date = request.form["date"]
        note = request.form["note"]
        username = session["user"]   
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO expenses (amount, category, date, note, username) VALUES (?, ?, ?, ?, ?)",
            (amount, category, date, note, username)
        )
        conn.commit()
        conn.close()

        return redirect("/expenses")

    return render_template("add_expense.html")

# __________VIEW EXPENSES__________

@app.route("/expenses")
def view_expenses():
    if "user" not in session:
        return redirect("/login")

    username = session["user"]

    today = datetime.today()
    first_day = today.replace(day=1)

    if today.month == 12:
        last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

    conn = get_db_connection()

    expenses = conn.execute("""
        SELECT * FROM expenses 
        WHERE username = ? AND date BETWEEN ? AND ?
        ORDER BY date DESC
    """, (
        username,
        first_day.strftime("%Y-%m-%d"),
        last_day.strftime("%Y-%m-%d")
    )).fetchall()

    conn.close()

    total = sum(expense["amount"] for expense in expenses)

    month_name = today.strftime("%B %Y")

    return render_template(
        "view_expenses.html",
        expenses=expenses,
        total=total,
        month=month_name
    )

# __________ EDIT __________

@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):
    if "user" not in session:
        return redirect("/login")

    conn = get_db_connection()

    expense = conn.execute(
        "SELECT * FROM expenses WHERE id=? AND username=?", 
        (expense_id, session["user"])
    ).fetchone()
    if not expense:
        conn.close()
        return "Unauthorized", 403  

    if request.method == "POST":
        amount = request.form["amount"]
        category = request.form["category"]
        date = request.form["date"]
        note = request.form["note"]

        conn.execute(
            "UPDATE expenses SET amount=?, category=?, date=?, note=? WHERE id=?",
            (amount, category, date, note, expense_id)
        )
        conn.commit()
        conn.close()
        return redirect("/expenses")

    conn.close()
    return render_template("edit_expense.html", expense=expense)

# __________ DELETE __________

@app.route("/delete/<int:expense_id>")
def delete_expense(expense_id):
    if "user" not in session:
        return redirect("/login")

    conn = get_db_connection()

    expense = conn.execute(
        "SELECT * FROM expenses WHERE id=? AND username=?", 
        (expense_id, session["user"])
    ).fetchone()
    if not expense:
        conn.close()
        return "Unauthorized", 403 

    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()
    return redirect("/expenses")

# __________PAST MONTH EXPENSES__________

@app.route("/past-month")
def past_month_expenses():
    if "user" not in session:
        return redirect("/login")

    username = session["user"]

    selected_month = request.args.get("month")

    today = datetime.today()

    if selected_month:
        selected_date = datetime.strptime(selected_month, "%Y-%m")
        start_date = selected_date.replace(day=1)

        
        if selected_date.month == 12:
            end_date = selected_date.replace(year=selected_date.year+1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = selected_date.replace(month=selected_date.month+1, day=1) - timedelta(days=1)

   
    else:
        first_day_current_month = today.replace(day=1)
        end_date = first_day_current_month - timedelta(days=1)
        start_date = end_date.replace(day=1)

    conn = get_db_connection()

    expenses = conn.execute("""
        SELECT * FROM expenses 
        WHERE username = ? AND date BETWEEN ? AND ?
        ORDER BY date DESC
    """, (username,
          start_date.strftime("%Y-%m-%d"),
          end_date.strftime("%Y-%m-%d"))).fetchall()

    conn.close()

    total = sum(expense["amount"] for expense in expenses)

    return render_template(
        "past_month.html",
        expenses=expenses,
        total=total,
        month=start_date.strftime("%B %Y")
    )

# __________PAST MONTH EXPENSES__________

@app.route("/monthly-graph")
def monthly_graph():
    if "user" not in session:
        return redirect("/login")

    username = session["user"]

    conn = get_db_connection()

    expenses = conn.execute("""
        SELECT date, amount FROM expenses
        WHERE username = ?
    """, (username,)).fetchall()

    conn.close()

    monthly_data = {}

    for exp in expenses:
        month = datetime.strptime(exp["date"], "%Y-%m-%d").strftime("%B %Y")

        if month not in monthly_data:
            monthly_data[month] = 0

        monthly_data[month] += exp["amount"]

    months = list(monthly_data.keys())
    totals = list(monthly_data.values())

    return render_template(
        "monthly_graph.html",
        months=months,
        totals=totals
    )

# __________ RUN __________

if __name__ == "__main__":
    create_table()  
    app.run(debug=True)
