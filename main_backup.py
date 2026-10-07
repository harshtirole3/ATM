import tkinter as tk
from tkinter import messagebox
import sqlite3
from datetime import datetime


# =========================
# DATABASE CONNECTION
# =========================

def connect_database():
    return sqlite3.connect("atm.db")


# =========================
# CHECK BALANCE
# =========================

def check_balance(account_no):

    connection = connect_database()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT balance FROM users WHERE account_no = ?",
        (account_no,)
    )

    result = cursor.fetchone()

    connection.close()

    if result:
        balance = result[0]

        messagebox.showinfo(
            "Account Balance",
            f"Your Current Balance is:\n\n₹{balance:,.2f}"
        )


# =========================
# WITHDRAW CASH
# =========================

def withdraw_cash(account_no):

    withdraw_window = tk.Toplevel()
    withdraw_window.title("Withdraw Cash")
    withdraw_window.geometry("400x300")

    tk.Label(
        withdraw_window,
        text="WITHDRAW CASH",
        font=("Arial", 20, "bold")
    ).pack(pady=20)

    tk.Label(
        withdraw_window,
        text="Enter Amount:",
        font=("Arial", 13)
    ).pack(pady=10)

    amount_entry = tk.Entry(
        withdraw_window,
        font=("Arial", 14),
        width=20
    )
    amount_entry.pack(pady=5)

    def process_withdrawal():

        amount_text = amount_entry.get()

        if not amount_text:
            messagebox.showerror(
                "Error",
                "Please enter an amount."
            )
            return

        try:
            amount = float(amount_text)

        except ValueError:
            messagebox.showerror(
                "Error",
                "Please enter a valid number."
            )
            return

        if amount <= 0:
            messagebox.showerror(
                "Error",
                "Amount must be greater than zero."
            )
            return

        if amount % 50 != 0:
            messagebox.showerror(
                "Invalid Amount",
                "Amount must be a multiple of ₹50."
            )
            return

        connection = connect_database()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT balance FROM users WHERE account_no = ?",
            (account_no,)
        )

        result = cursor.fetchone()

        if not result:
            connection.close()

            messagebox.showerror(
                "Error",
                "Account not found."
            )
            return

        balance = result[0]

        if amount > balance:
            connection.close()

            messagebox.showerror(
                "Insufficient Balance",
                f"Your balance is ₹{balance:,.2f}"
            )
            return

        new_balance = balance - amount

        # Update balance
        cursor.execute(
            "UPDATE users SET balance = ? WHERE account_no = ?",
            (new_balance, account_no)
        )

        # Record transaction
        now = datetime.now()

        cursor.execute(
            """
            INSERT INTO transactions
            (account_no, transaction_type, amount, balance_after, date, time)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                account_no,
                "WITHDRAW",
                amount,
                new_balance,
                now.strftime("%Y-%m-%d"),
                now.strftime("%H:%M:%S")
            )
        )

        connection.commit()
        connection.close()

        messagebox.showinfo(
            "Withdrawal Successful",
            f"₹{amount:,.2f} withdrawn successfully!\n\n"
            f"Remaining Balance: ₹{new_balance:,.2f}"
        )

        withdraw_window.destroy()

    tk.Button(
        withdraw_window,
        text="WITHDRAW",
        font=("Arial", 13, "bold"),
        width=15,
        command=process_withdrawal
    ).pack(pady=20)


# =========================
# DEPOSIT CASH
# =========================

def deposit_cash(account_no):

    deposit_window = tk.Toplevel()
    deposit_window.title("Deposit Cash")
    deposit_window.geometry("400x300")

    tk.Label(
        deposit_window,
        text="DEPOSIT CASH",
        font=("Arial", 20, "bold")
    ).pack(pady=20)

    tk.Label(
        deposit_window,
        text="Enter Amount:",
        font=("Arial", 13)
    ).pack(pady=10)

    amount_entry = tk.Entry(
        deposit_window,
        font=("Arial", 14),
        width=20
    )
    amount_entry.pack(pady=5)

    def process_deposit():

        amount_text = amount_entry.get()

        if not amount_text:
            messagebox.showerror(
                "Error",
                "Please enter an amount."
            )
            return

        try:
            amount = float(amount_text)

        except ValueError:
            messagebox.showerror(
                "Error",
                "Please enter a valid number."
            )
            return

        if amount <= 0:
            messagebox.showerror(
                "Invalid Amount",
                "Amount must be greater than zero."
            )
            return

        connection = connect_database()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT balance FROM users WHERE account_no = ?",
            (account_no,)
        )

        result = cursor.fetchone()

        if not result:
            connection.close()

            messagebox.showerror(
                "Error",
                "Account not found."
            )
            return

        balance = result[0]

        new_balance = balance + amount

        # Update balance
        cursor.execute(
            "UPDATE users SET balance = ? WHERE account_no = ?",
            (new_balance, account_no)
        )

        # Record transaction
        now = datetime.now()

        cursor.execute(
            """
            INSERT INTO transactions
            (account_no, transaction_type, amount, balance_after, date, time)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                account_no,
                "DEPOSIT",
                amount,
                new_balance,
                now.strftime("%Y-%m-%d"),
                now.strftime("%H:%M:%S")
            )
        )

        connection.commit()
        connection.close()

        messagebox.showinfo(
            "Deposit Successful",
            f"₹{amount:,.2f} deposited successfully!\n\n"
            f"New Balance: ₹{new_balance:,.2f}"
        )

        deposit_window.destroy()

    tk.Button(
        deposit_window,
        text="DEPOSIT",
        font=("Arial", 13, "bold"),
        width=15,
        command=process_deposit
    ).pack(pady=20)


# =========================
# MINI STATEMENT
# =========================

def mini_statement(account_no):

    statement_window = tk.Toplevel()
    statement_window.title("Mini Statement")
    statement_window.geometry("750x500")

    tk.Label(
        statement_window,
        text="MINI STATEMENT",
        font=("Arial", 20, "bold")
    ).pack(pady=20)

    connection = connect_database()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT transaction_type,
               amount,
               balance_after,
               date,
               time
        FROM transactions
        WHERE account_no = ?
        ORDER BY transaction_id DESC
        LIMIT 10
        """,
        (account_no,)
    )

    transactions = cursor.fetchall()

    connection.close()

    if not transactions:

        tk.Label(
            statement_window,
            text="No transactions found.",
            font=("Arial", 14)
        ).pack(pady=30)

        return

    # Headings
    headings = tk.Frame(statement_window)
    headings.pack(fill="x", padx=20, pady=10)

    tk.Label(
        headings,
        text="TYPE",
        font=("Arial", 11, "bold"),
        width=14
    ).pack(side="left")

    tk.Label(
        headings,
        text="AMOUNT",
        font=("Arial", 11, "bold"),
        width=14
    ).pack(side="left")

    tk.Label(
        headings,
        text="BALANCE",
        font=("Arial", 11, "bold"),
        width=14
    ).pack(side="left")

    tk.Label(
        headings,
        text="DATE",
        font=("Arial", 11, "bold"),
        width=14
    ).pack(side="left")

    tk.Label(
        headings,
        text="TIME",
        font=("Arial", 11, "bold"),
        width=10
    ).pack(side="left")

    # Transaction rows
    for transaction in transactions:

        transaction_type, amount, balance, date, time = transaction

        row = tk.Frame(statement_window)
        row.pack(fill="x", padx=20, pady=5)

        tk.Label(
            row,
            text=transaction_type,
            width=14
        ).pack(side="left")

        tk.Label(
            row,
            text=f"₹{amount:,.2f}",
            width=14
        ).pack(side="left")

        tk.Label(
            row,
            text=f"₹{balance:,.2f}",
            width=14
        ).pack(side="left")

        tk.Label(
            row,
            text=date,
            width=14
        ).pack(side="left")

        tk.Label(
            row,
            text=time,
            width=10
        ).pack(side="left")


# =========================
# LOGIN
# =========================

def login():

    account_no = account_entry.get()
    pin = pin_entry.get()

    if not account_no or not pin:

        messagebox.showerror(
            "Login Error",
            "Please enter account number and PIN."
        )
        return

    try:
        account_no = int(account_no)

    except ValueError:

        messagebox.showerror(
            "Login Error",
            "Account number must contain numbers only."
        )
        return

    connection = connect_database()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT name, pin, account_locked
        FROM users
        WHERE account_no = ?
        """,
        (account_no,)
    )

    user = cursor.fetchone()

    connection.close()

    if not user:

        messagebox.showerror(
            "Login Failed",
            "Account not found."
        )
        return

    name, correct_pin, account_locked = user

    if account_locked == 1:

        messagebox.showerror(
            "Account Locked",
            "This account is locked."
        )
        return

    if pin != correct_pin:

        messagebox.showerror(
            "Login Failed",
            "Incorrect PIN."
        )
        return

    login_window.destroy()

    open_main_menu(
        name,
        account_no
    )


# =========================
# MAIN MENU
# =========================

def open_main_menu(name, account_no):

    menu_window = tk.Tk()

    menu_window.title("ATM Main Menu")
    menu_window.geometry("500x600")

    tk.Label(
        menu_window,
        text="ATM SIMULATOR",
        font=("Arial", 25, "bold")
    ).pack(pady=20)

    tk.Label(
        menu_window,
        text=f"Welcome, {name}",
        font=("Arial", 16)
    ).pack(pady=10)

    tk.Button(
        menu_window,
        text="CHECK BALANCE",
        font=("Arial", 14),
        width=20,
        command=lambda: check_balance(account_no)
    ).pack(pady=10)

    tk.Button(
        menu_window,
        text="WITHDRAW CASH",
        font=("Arial", 14),
        width=20,
        command=lambda: withdraw_cash(account_no)
    ).pack(pady=10)

    tk.Button(
        menu_window,
        text="DEPOSIT CASH",
        font=("Arial", 14),
        width=20,
        command=lambda: deposit_cash(account_no)
    ).pack(pady=10)

    tk.Button(
        menu_window,
        text="MINI STATEMENT",
        font=("Arial", 14),
        width=20,
        command=lambda: mini_statement(account_no)
    ).pack(pady=10)

    tk.Button(
        menu_window,
        text="LOGOUT",
        font=("Arial", 14),
        width=20,
        command=menu_window.destroy
    ).pack(pady=20)

    menu_window.mainloop()


# =========================
# LOGIN WINDOW
# =========================

login_window = tk.Tk()

login_window.title("ATM Login")
login_window.geometry("450x400")


tk.Label(
    login_window,
    text="ATM SIMULATOR",
    font=("Arial", 25, "bold")
).pack(pady=30)


tk.Label(
    login_window,
    text="Account Number",
    font=("Arial", 13)
).pack(pady=5)


account_entry = tk.Entry(
    login_window,
    font=("Arial", 14),
    width=20
)
account_entry.pack(pady=5)


tk.Label(
    login_window,
    text="PIN",
    font=("Arial", 13)
).pack(pady=5)


pin_entry = tk.Entry(
    login_window,
    font=("Arial", 14),
    width=20,
    show="*"
)
pin_entry.pack(pady=5)


tk.Button(
    login_window,
    text="LOGIN",
    font=("Arial", 14, "bold"),
    width=15,
    command=login
).pack(pady=25)


login_window.mainloop()