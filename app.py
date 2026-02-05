from flask import Flask, render_template, request, redirect, session
import sqlite3

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
        username = session["user"]   # ⭐ logged-in user

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO expenses (amount, category, date, note, username) VALUES (?, ?, ?, ?, ?)",
            (amount, category, date, note, username)
        )
        conn.commit()
        conn.close()

        return redirect("/expenses")

    return render_template("add_expense.html")


# __________ VIEW EXPENSES __________

@app.route("/expenses")
def view_expenses():
    if "user" not in session:
        return redirect("/login")

    username = session["user"]

    conn = get_db_connection()
    expenses = conn.execute(
        "SELECT * FROM expenses WHERE username = ? ORDER BY date DESC",
        (username,)
    ).fetchall()
    conn.close()

    total = sum(expense["amount"] for expense in expenses)

    return render_template(
        "view_expenses.html",
        expenses=expenses,
        total=total
    )

# __________ EDIT __________

@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):
    if "user" not in session:
        return redirect("/login")

    conn = get_db_connection()

    # ⭐ Only allow editing if this expense belongs to the logged-in user
    expense = conn.execute(
        "SELECT * FROM expenses WHERE id=? AND username=?", 
        (expense_id, session["user"])
    ).fetchone()
    if not expense:
        conn.close()
        return "Unauthorized", 403  # 🚫 Stop here if user is not owner

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

    # ⭐ Only allow deleting if this expense belongs to the logged-in user
    expense = conn.execute(
        "SELECT * FROM expenses WHERE id=? AND username=?", 
        (expense_id, session["user"])
    ).fetchone()
    if not expense:
        conn.close()
        return "Unauthorized", 403  # 🚫 Stop here if user is not owner

    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()
    return redirect("/expenses")

# __________ RUN __________

if __name__ == "__main__":
    create_table()  
    app.run(debug=True)



