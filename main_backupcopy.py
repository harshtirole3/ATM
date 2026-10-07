import tkinter as tk
from tkinter import messagebox
import sqlite3
from datetime import datetime
from denomination import calculate_denominations
from qr_payment import process_qr_cash
from receipt import generate_receipt
from fraud_detection import (
    check_large_withdrawal,
    check_repeated_withdrawals,
    check_suspicious_pattern
)
from ml_fraud_detection import detect_anomaly



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
    withdraw_window.geometry("450x400")

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
                "Invalid Amount",
                "Amount must be greater than zero."
            )
            return

        if amount % 50 != 0:
            messagebox.showerror(
                "Invalid Amount",
                "Amount must be a multiple of ₹50."
            )
            return

        # FRAUD RULE 1
        if check_large_withdrawal(amount):

            messagebox.showwarning(
                "Suspicious Transaction",
                f"⚠️ Large withdrawal detected!\n\n"
                f"Amount: ₹{amount:,.2f}\n\n"
                f"This transaction has been flagged as suspicious."
            )

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

        denominations = calculate_denominations(amount)

        if denominations is None:
            connection.close()

            messagebox.showerror(
                "ATM Cash Unavailable",
                "The ATM does not have the required combination of notes."
            )
            return

        new_balance = balance - amount

        cursor.execute(
            """
            UPDATE users
            SET balance = ?
            WHERE account_no = ?
            """,
            (new_balance, account_no)
        )

        for note, count in denominations.items():

            cursor.execute(
                """
                UPDATE atm_cash
                SET note_count = note_count - ?
                WHERE denomination = ?
                """,
                (count, note)
            )

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
        if detect_anomaly(account_no, amount):
        
                    messagebox.showwarning(
                        "ML Anomaly Detected",
                        "🤖 Unusual transaction pattern detected!\n\n"
                        f"Amount: ₹{amount:,.2f}\n\n"
                        "The machine learning model has flagged "
                        "this transaction as potentially anomalous."
                    )

        # FRAUD RULE 2
        if check_repeated_withdrawals(account_no):
                    


            messagebox.showwarning(
                "Suspicious Activity",
                "⚠️ Multiple withdrawals detected!\n\n"
                "This account has made 3 or more withdrawals "
                "within the last 5 minutes.\n\n"
                "The activity has been flagged for review."
            )

        # FRAUD RULE 3
        if check_suspicious_pattern(account_no):

            messagebox.showwarning(
                "Suspicious Pattern",
                "⚠️ Suspicious transaction pattern detected!\n\n"
                "The same withdrawal amount has been used "
                "5 or more times within the last 30 minutes.\n\n"
                "The activity has been flagged for review."
            )

        notes_text = ""

        for note, count in denominations.items():
            notes_text += f"₹{note} × {count}\n"

        transaction_id = (
            "TXN" +
            datetime.now().strftime("%Y%m%d%H%M%S%f")
        )

        receipt_file = generate_receipt(
            account_no,
            "WITHDRAW",
            amount,
            new_balance,
            transaction_id,
            denominations
        )

        messagebox.showinfo(
            "Withdrawal Successful",
            f"₹{amount:,.2f} withdrawn successfully!\n\n"
            f"Transaction ID:\n{transaction_id}\n\n"
            f"Cash Dispensed:\n"
            f"{notes_text}\n"
            f"Remaining Balance: ₹{new_balance:,.2f}\n\n"
            f"Digital Receipt Saved:\n{receipt_file}"
        )

        withdraw_window.destroy()

    tk.Button(
        withdraw_window,
        text="WITHDRAW",
        font=("Arial", 13, "bold"),
        width=15,
        command=process_withdrawal
    ).pack(pady=25)
    # =========================
# DEPOSIT CASH
# =========================

def deposit_cash(account_no):

    deposit_window = tk.Toplevel()
    deposit_window.title("Deposit Cash")
    deposit_window.geometry("400x350")

    tk.Label(
        deposit_window,
        text="DEPOSIT CASH",
        font=("Arial", 22, "bold")
    ).pack(pady=25)

    tk.Label(
        deposit_window,
        text="Enter deposit amount:",
        font=("Arial", 13)
    ).pack(pady=10)

    amount_entry = tk.Entry(
        deposit_window,
        font=("Arial", 14),
        width=20
    )
    amount_entry.pack(pady=10)

    def process_deposit():

        amount_text = amount_entry.get()

        if not amount_text:

            messagebox.showerror(
                "Deposit Error",
                "Please enter an amount."
            )
            return

        try:
            amount = float(amount_text)

        except ValueError:

            messagebox.showerror(
                "Deposit Error",
                "Please enter a valid amount."
            )
            return

        if amount <= 0:

            messagebox.showerror(
                "Deposit Error",
                "Amount must be greater than zero."
            )
            return

        connection = connect_database()
        cursor = connection.cursor()

        # Get current balance
        cursor.execute(
            """
            SELECT balance
            FROM users
            WHERE account_no = ?
            """,
            (account_no,)
        )

        user = cursor.fetchone()

        if not user:

            connection.close()

            messagebox.showerror(
                "Deposit Error",
                "Account not found."
            )
            return

        current_balance = user[0]

        new_balance = current_balance + amount

        # Update balance
        cursor.execute(
            """
            UPDATE users
            SET balance = ?
            WHERE account_no = ?
            """,
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

        # Get transaction ID
        transaction_id = cursor.lastrowid

        connection.close()

        # Generate digital receipt
        generate_receipt(
            account_no,
            "DEPOSIT",
            amount,
            new_balance,
            transaction_id
        )

        messagebox.showinfo(
            "Deposit Successful",
            f"₹{amount:.2f} deposited successfully!\n\n"
            f"New Balance: ₹{new_balance:.2f}"
        )

        deposit_window.destroy()

    tk.Button(
        deposit_window,
        text="DEPOSIT",
        font=("Arial", 14, "bold"),
        width=15,
        command=process_deposit
    ).pack(pady=25)

    tk.Button(
        deposit_window,
        text="CANCEL",
        font=("Arial", 12),
        width=15,
        command=deposit_window.destroy
    ).pack()
# =========================
# ACCOUNT TO ACCOUNT TRANSFER
# =========================

def account_transfer(account_no):

    transfer_window = tk.Toplevel()
    transfer_window.title("Account Transfer")
    transfer_window.geometry("450x400")

    tk.Label(
        transfer_window,
        text="ACCOUNT TO ACCOUNT TRANSFER",
        font=("Arial", 18, "bold")
    ).pack(pady=20)

    tk.Label(
        transfer_window,
        text="Receiver Account Number:",
        font=("Arial", 13)
    ).pack(pady=5)

    receiver_entry = tk.Entry(
        transfer_window,
        font=("Arial", 14),
        width=20
    )
    receiver_entry.pack(pady=5)

    tk.Label(
        transfer_window,
        text="Transfer Amount:",
        font=("Arial", 13)
    ).pack(pady=10)

    amount_entry = tk.Entry(
        transfer_window,
        font=("Arial", 14),
        width=20
    )
    amount_entry.pack(pady=5)

    def process_transfer():

        receiver_text = receiver_entry.get()
        amount_text = amount_entry.get()

        if not receiver_text or not amount_text:
            messagebox.showerror(
                "Error",
                "Please enter receiver account and amount."
            )
            return

        try:
            receiver_account = int(receiver_text)
            amount = float(amount_text)

        except ValueError:
            messagebox.showerror(
                "Error",
                "Please enter valid numbers."
            )
            return

        if receiver_account == account_no:
            messagebox.showerror(
                "Error",
                "You cannot transfer money to your own account."
            )
            return

        if amount <= 0:
            messagebox.showerror(
                "Error",
                "Transfer amount must be greater than zero."
            )
            return

        connection = connect_database()
        cursor = connection.cursor()

        # Check receiver account
        cursor.execute(
            "SELECT name, balance FROM users WHERE account_no = ?",
            (receiver_account,)
        )

        receiver = cursor.fetchone()

        if not receiver:
            connection.close()

            messagebox.showerror(
                "Error",
                "Receiver account not found."
            )
            return

        # Check sender balance
        cursor.execute(
            "SELECT balance FROM users WHERE account_no = ?",
            (account_no,)
        )

        sender = cursor.fetchone()

        if not sender:
            connection.close()

            messagebox.showerror(
                "Error",
                "Sender account not found."
            )
            return

        sender_balance = sender[0]
        receiver_name = receiver[0]
        receiver_balance = receiver[1]

        if amount > sender_balance:
            connection.close()

            messagebox.showerror(
                "Insufficient Balance",
                f"Your balance is ₹{sender_balance:,.2f}"
            )
            return

        new_sender_balance = sender_balance - amount
        new_receiver_balance = receiver_balance + amount

        # Deduct money from sender
        cursor.execute(
            "UPDATE users SET balance = ? WHERE account_no = ?",
            (new_sender_balance, account_no)
        )

        # Add money to receiver
        cursor.execute(
            "UPDATE users SET balance = ? WHERE account_no = ?",
            (new_receiver_balance, receiver_account)
        )

        # Current date and time
        now = datetime.now()

        # Record sender transaction
        cursor.execute(
            """
            INSERT INTO transactions
            (account_no, transaction_type, amount, balance_after, date, time)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                account_no,
                "TRANSFER OUT",
                amount,
                new_sender_balance,
                now.strftime("%Y-%m-%d"),
                now.strftime("%H:%M:%S")
            )
        )

        # Record receiver transaction
        cursor.execute(
            """
            INSERT INTO transactions
            (account_no, transaction_type, amount, balance_after, date, time)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                receiver_account,
                "TRANSFER IN",
                amount,
                new_receiver_balance,
                now.strftime("%Y-%m-%d"),
                now.strftime("%H:%M:%S")
            )
        )

        connection.commit()
        connection.close()

        messagebox.showinfo(
            "Transfer Successful",
            f"₹{amount:,.2f} transferred successfully!\n\n"
            f"To: {receiver_name}\n"
            f"Account: {receiver_account}\n\n"
            f"Remaining Balance: ₹{new_sender_balance:,.2f}"
        )

        transfer_window.destroy()

    tk.Button(
        transfer_window,
        text="TRANSFER",
        font=("Arial", 13, "bold"),
        width=15,
        command=process_transfer
    ).pack(pady=25)

    # =========================
# QR TO CASH
# =========================

def qr_to_cash(account_no):

    qr_window = tk.Toplevel()
    qr_window.title("QR To Cash")
    qr_window.geometry("450x400")

    tk.Label(
        qr_window,
        text="QR → CASH",
        font=("Arial", 22, "bold")
    ).pack(pady=25)

    tk.Label(
        qr_window,
        text="Enter QR Cash Amount:",
        font=("Arial", 13)
    ).pack(pady=10)

    amount_entry = tk.Entry(
        qr_window,
        font=("Arial", 14),
        width=20
    )
    amount_entry.pack(pady=5)

    def process():

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
                "Please enter a valid amount."
            )
            return

        if amount <= 0:

            messagebox.showerror(
                "Invalid Amount",
                "Amount must be greater than zero."
            )
            return

        if amount % 50 != 0:

            messagebox.showerror(
                "Invalid Amount",
                "Amount must be a multiple of Rs.50."
            )
            return

        result = process_qr_cash(
            account_no,
            amount
        )

        if result is None:

            messagebox.showerror(
                "QR Cash Failed",
                "QR cash transaction could not be completed."
            )
            return

        notes_text = ""

        for note, count in result["denominations"].items():

            notes_text += f"Rs.{note} x {count}\n"

        messagebox.showinfo(
            "QR Cash Successful",
            f"QR Transaction Successful!\n\n"
            f"Transaction ID:\n"
            f"{result['transaction_id']}\n\n"
            f"Cash Amount: Rs.{amount:,.2f}\n\n"
            f"Cash Dispensed:\n"
            f"{notes_text}\n"
            f"Remaining Balance: "
            f"Rs.{result['new_balance']:,.2f}"
        )

        qr_window.destroy()

    tk.Button(
        qr_window,
        text="GENERATE CASH",
        font=("Arial", 13, "bold"),
        width=18,
        command=process
    ).pack(pady=30)
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
        SELECT name, pin, account_locked, pin_attempts
        FROM users
        WHERE account_no = ?
        """,
        (account_no,)
    )

    user = cursor.fetchone()

    if not user:

        connection.close()

        messagebox.showerror(
            "Login Failed",
            "Account not found."
        )
        return

    name, correct_pin, account_locked, pin_attempts = user

    # Check if account is already locked
    if account_locked == 1:

        connection.close()

        messagebox.showerror(
            "Account Locked",
            "This account is locked due to multiple incorrect PIN attempts."
        )
        return

    # Check PIN
    if pin != correct_pin:

        pin_attempts += 1

        # Lock account after 3 wrong attempts
        if pin_attempts >= 3:

            cursor.execute(
                """
                UPDATE users
                SET pin_attempts = ?, account_locked = 1
                WHERE account_no = ?
                """,
                (pin_attempts, account_no)
            )

            connection.commit()
            connection.close()

            messagebox.showerror(
                "Account Locked",
                "3 incorrect PIN attempts.\nYour account has been locked."
            )

            return

        # Save failed attempt
        cursor.execute(
            """
            UPDATE users
            SET pin_attempts = ?
            WHERE account_no = ?
            """,
            (pin_attempts, account_no)
        )

        connection.commit()
        connection.close()

        attempts_remaining = 3 - pin_attempts

        messagebox.showerror(
            "Login Failed",
            f"Incorrect PIN.\n"
            f"Attempts remaining: {attempts_remaining}"
        )

        return

    # Correct PIN → reset failed attempts
    cursor.execute(
        """
        UPDATE users
        SET pin_attempts = 0
        WHERE account_no = ?
        """,
        (account_no,)
    )

    connection.commit()
    connection.close()

    login_window.destroy()

    open_main_menu(
        name,
        account_no
    )

# =========================
# MAIN MENU
# =========================

# =========================
# MAIN MENU
# =========================

def open_main_menu(name, account_no):

    menu_window = tk.Tk()

    menu_window.title("ATM Main Menu")
    menu_window.geometry("500x650")

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
    ).pack(pady=8)

    tk.Button(
        menu_window,
        text="WITHDRAW CASH",
        font=("Arial", 14),
        width=20,
        command=lambda: withdraw_cash(account_no)
    ).pack(pady=8)

    tk.Button(
        menu_window,
        text="DEPOSIT CASH",
        font=("Arial", 14),
        width=20,
        command=lambda: deposit_cash(account_no)
    ).pack(pady=8)

    tk.Button(
        menu_window,
        text="QR → CASH",
        font=("Arial", 14),
        width=20,
        command=lambda: qr_to_cash(account_no)
    ).pack(pady=8)

    tk.Button(
        menu_window,
        text="ACCOUNT TRANSFER",
        font=("Arial", 14),
        width=20,
        command=lambda: account_transfer(account_no)
    ).pack(pady=8)

    tk.Button(
        menu_window,
        text="MINI STATEMENT",
        font=("Arial", 14),
        width=20,
        command=lambda: mini_statement(account_no)
    ).pack(pady=8)

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