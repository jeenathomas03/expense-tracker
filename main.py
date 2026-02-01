import mysql.connector

# Connecting to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="MySql@123"  
)
cursor = conn.cursor()

# Create database and table 
cursor.execute("CREATE DATABASE IF NOT EXISTS expense_tracker")
cursor.execute("USE expense_tracker")
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100),
    amount DECIMAL(10,2),
    category VARCHAR(50),
    expense_date DATE
)
""")

# To add expense
def add_expense():
    title = input("Enter expense title: ")
    amount = float(input("Enter amount: "))
    category = input("Enter category: ")
    date = input("Enter date (YYYY-MM-DD): ")

    query = "INSERT INTO expenses (title, amount, category, expense_date) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (title, amount, category, date))
    conn.commit()
    print("Expense added successfully!")

# view all expenses
def view_expenses():
    cursor.execute("SELECT * FROM expenses")
    expenses = cursor.fetchall()
    for exp in expenses:
        print(exp)

# Main Menu
while True:
    print("\n--- Expense Tracker ---")
    print("1. Add Expense")
    print("2. View Expenses")
    print("3. Exit")

    choice = input("Choose option: ")

    if choice == "1":
        add_expense()
    elif choice == "2":
        view_expenses()
    elif choice == "3":
        print("Goodbye!")
        break
    else:
        print("Invalid choice")

conn.close()
