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
from admin_dashboard import open_dashboard


# =========================================================
# DATABASE CONNECTION
# =========================================================

def connect_database():
    return sqlite3.connect("atm.db")


# =========================================================
# CHECK BALANCE
# =========================================================

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
        return result[0]

    return None


# =========================================================
# WITHDRAW CASH
# =========================================================

def withdraw_cash(account_no, amount):

    if amount <= 0:
        messagebox.showerror(
            "Invalid Amount",
            "Please enter a valid amount."
        )
        return

    # -----------------------------------------------------
    # FRAUD CHECK 1 - LARGE WITHDRAWAL
    # -----------------------------------------------------

    if check_large_withdrawal(amount):

        response = messagebox.askyesno(
            "Fraud Alert",
            "This transaction is above ₹10,000.\n\n"
            "It has been flagged as a high-risk transaction.\n\n"
            "Do you want to continue?"
        )

        if not response:
            return

    # -----------------------------------------------------
    # FRAUD CHECK 2 - REPEATED WITHDRAWALS
    # -----------------------------------------------------

    if check_repeated_withdrawals(account_no):

        messagebox.showwarning(
            "Fraud Alert",
            "Multiple withdrawals detected within a short period.\n\n"
            "Transaction blocked for security."
        )

        return

    # -----------------------------------------------------
    # FRAUD CHECK 3 - SUSPICIOUS PATTERN
    # -----------------------------------------------------

    if check_suspicious_pattern(account_no):

        messagebox.showwarning(
            "Suspicious Activity",
            "Suspicious transaction pattern detected.\n\n"
            "Transaction blocked for security."
        )

        return

    # -----------------------------------------------------
    # ML FRAUD DETECTION
    # -----------------------------------------------------

    try:

        anomaly_detected = detect_anomaly(
            account_no,
            amount
        )

        if anomaly_detected:

            response = messagebox.askyesno(
                "ML Fraud Alert",
                "Machine Learning detected an unusual transaction.\n\n"
                "Do you want to continue?"
            )

            if not response:
                return

    except Exception:
        # ML module should not stop normal ATM operation
        pass

    # -----------------------------------------------------
    # DATABASE
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # CHECK BALANCE
    # -----------------------------------------------------

    if amount > balance:

        connection.close()

        messagebox.showerror(
            "Insufficient Balance",
            "You do not have enough balance."
        )

        return

    # -----------------------------------------------------
    # SMART DENOMINATION
    # -----------------------------------------------------

    denominations = calculate_denominations(amount)

    if denominations is None:

        connection.close()

        messagebox.showerror(
            "Cash Unavailable",
            "ATM does not have the required denominations."
        )

        return

    new_balance = balance - amount

    # -----------------------------------------------------
    # UPDATE USER BALANCE
    # -----------------------------------------------------

    cursor.execute(
        """
        UPDATE users
        SET balance = ?
        WHERE account_no = ?
        """,
        (new_balance, account_no)
    )

    # -----------------------------------------------------
    # UPDATE ATM CASH INVENTORY
    # -----------------------------------------------------

    for denomination, count in denominations.items():

        cursor.execute(
            """
            UPDATE atm_cash
            SET note_count = note_count - ?
            WHERE denomination = ?
            """,
            (count, denomination)
        )

    # -----------------------------------------------------
    # TRANSACTION DETAILS
    # -----------------------------------------------------

    now = datetime.now()

    cursor.execute(
        """
        INSERT INTO transactions
        (
            account_no,
            transaction_type,
            amount,
            balance_after,
            date,
            time
        )
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

    transaction_id = cursor.lastrowid

    connection.commit()
    connection.close()

    # -----------------------------------------------------
    # RECEIPT
    # -----------------------------------------------------

    try:

        generate_receipt(
            account_no,
            "WITHDRAW",
            amount,
            new_balance,
            transaction_id,
            denominations
        )

    except Exception:
        pass

    # -----------------------------------------------------
    # SHOW RESULT
    # -----------------------------------------------------

    denomination_text = ""

    for denomination, count in denominations.items():

        denomination_text += (
            f"₹{denomination} × {count}\n"
        )

    messagebox.showinfo(
        "Withdrawal Successful",
        f"Transaction ID: {transaction_id}\n\n"
        f"Amount: ₹{amount}\n\n"
        f"Cash Dispensed:\n"
        f"{denomination_text}\n"
        f"Remaining Balance: ₹{new_balance}"
    )


# =========================================================
# DEPOSIT CASH
# =========================================================

def deposit_cash(account_no, amount):

    if amount <= 0:

        messagebox.showerror(
            "Invalid Amount",
            "Please enter a valid amount."
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

    # -----------------------------------------------------
    # UPDATE BALANCE
    # -----------------------------------------------------

    cursor.execute(
        """
        UPDATE users
        SET balance = ?
        WHERE account_no = ?
        """,
        (new_balance, account_no)
    )

    # -----------------------------------------------------
    # TRANSACTION
    # -----------------------------------------------------

    now = datetime.now()

    cursor.execute(
        """
        INSERT INTO transactions
        (
            account_no,
            transaction_type,
            amount,
            balance_after,
            date,
            time
        )
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

    transaction_id = cursor.lastrowid

    connection.commit()
    connection.close()

    # -----------------------------------------------------
    # RECEIPT
    # -----------------------------------------------------

    try:

        generate_receipt(
            account_no,
            "DEPOSIT",
            amount,
            new_balance,
            transaction_id
        )

    except Exception:
        pass

    messagebox.showinfo(
        "Deposit Successful",
        f"Transaction ID: {transaction_id}\n\n"
        f"Deposited Amount: ₹{amount}\n\n"
        f"New Balance: ₹{new_balance}"
    )


# =========================================================
# ACCOUNT TRANSFER
# =========================================================

def account_transfer(sender_account, receiver_account, amount):

    if amount <= 0:

        messagebox.showerror(
            "Invalid Amount",
            "Please enter a valid amount."
        )

        return

    if sender_account == receiver_account:

        messagebox.showerror(
            "Invalid Transfer",
            "Sender and receiver accounts cannot be the same."
        )

        return

    connection = connect_database()
    cursor = connection.cursor()

    # -----------------------------------------------------
    # SENDER
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT balance
        FROM users
        WHERE account_no = ?
        """,
        (sender_account,)
    )

    sender = cursor.fetchone()

    if not sender:

        connection.close()

        messagebox.showerror(
            "Error",
            "Sender account not found."
        )

        return

    # -----------------------------------------------------
    # RECEIVER
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT balance
        FROM users
        WHERE account_no = ?
        """,
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

    sender_balance = sender[0]
    receiver_balance = receiver[0]

    # -----------------------------------------------------
    # CHECK BALANCE
    # -----------------------------------------------------

    if amount > sender_balance:

        connection.close()

        messagebox.showerror(
            "Insufficient Balance",
            "Sender does not have enough balance."
        )

        return

    new_sender_balance = sender_balance - amount
    new_receiver_balance = receiver_balance + amount

    # -----------------------------------------------------
    # UPDATE SENDER
    # -----------------------------------------------------

    cursor.execute(
        """
        UPDATE users
        SET balance = ?
        WHERE account_no = ?
        """,
        (new_sender_balance, sender_account)
    )

    # -----------------------------------------------------
    # UPDATE RECEIVER
    # -----------------------------------------------------

    cursor.execute(
        """
        UPDATE users
        SET balance = ?
        WHERE account_no = ?
        """,
        (new_receiver_balance, receiver_account)
    )

    # -----------------------------------------------------
    # TRANSACTIONS
    # -----------------------------------------------------

    now = datetime.now()

    # Sender transaction
    cursor.execute(
        """
        INSERT INTO transactions
        (
            account_no,
            transaction_type,
            amount,
            balance_after,
            date,
            time
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            sender_account,
            "TRANSFER OUT",
            amount,
            new_sender_balance,
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M:%S")
        )
    )

    # Receiver transaction
    cursor.execute(
        """
        INSERT INTO transactions
        (
            account_no,
            transaction_type,
            amount,
            balance_after,
            date,
            time
        )
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
        f"₹{amount} transferred successfully.\n\n"
        f"Receiver Account: {receiver_account}\n\n"
        f"Remaining Balance: ₹{new_sender_balance}"
    )


# =========================================================
# QR TO CASH
# =========================================================

def qr_to_cash(account_no, amount):

    if amount <= 0:

        messagebox.showerror(
            "Invalid Amount",
            "Please enter a valid amount."
        )

        return

    result = process_qr_cash(
        account_no,
        amount
    )

    if isinstance(result, dict):

        transaction_id = result.get(
            "transaction_id",
            "N/A"
        )

        balance_after = result.get(
            "balance_after",
            check_balance(account_no)
        )

        denominations = result.get(
            "denominations",
            {}
        )

        denomination_text = ""

        if denominations:

            for denomination, count in denominations.items():

                denomination_text += (
                    f"₹{denomination} × {count}\n"
                )

        messagebox.showinfo(
            "QR Cash Successful",
            f"Transaction ID: {transaction_id}\n\n"
            f"Amount: ₹{amount}\n\n"
            f"Cash Dispensed:\n"
            f"{denomination_text}\n"
            f"Remaining Balance: ₹{balance_after}"
        )

    else:

        messagebox.showerror(
            "QR Transaction Failed",
            str(result)
        )


# =========================================================
# MINI STATEMENT
# =========================================================

def mini_statement(account_no):

    connection = connect_database()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            transaction_id,
            transaction_type,
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

        messagebox.showinfo(
            "Mini Statement",
            "No transactions found."
        )

        return

    statement_window = tk.Toplevel()
    statement_window.title("Mini Statement")
    statement_window.geometry("650x500")
    statement_window.configure(
        bg="#0B132B"
    )

    tk.Label(
        statement_window,
        text="MINI STATEMENT",
        font=("Arial", 22, "bold"),
        bg="#0B132B",
        fg="white"
    ).pack(pady=20)

    frame = tk.Frame(
        statement_window,
        bg="white"
    )

    frame.pack(
        padx=20,
        pady=10,
        fill="both",
        expand=True
    )

    headers = [
        "ID",
        "TYPE",
        "AMOUNT",
        "BALANCE",
        "DATE",
        "TIME"
    ]

    for column, header in enumerate(headers):

        tk.Label(
            frame,
            text=header,
            font=("Arial", 9, "bold"),
            bg="#E5E7EB",
            fg="#111827",
            width=13
        ).grid(
            row=0,
            column=column,
            padx=1,
            pady=1
        )

    for row_index, transaction in enumerate(
        transactions,
        start=1
    ):

        for column_index, value in enumerate(
            transaction
        ):

            tk.Label(
                frame,
                text=str(value),
                font=("Arial", 8),
                bg="white",
                fg="#111827",
                width=13
            ).grid(
                row=row_index,
                column=column_index,
                padx=1,
                pady=2
            )


# =========================================================
# LOGIN
# =========================================================

def login():

    account_no_text = account_entry.get().strip()
    pin = pin_entry.get().strip()

    if not account_no_text or not pin:

        messagebox.showerror(
            "Login Error",
            "Please enter account number and PIN."
        )

        return

    try:

        account_no = int(account_no_text)

    except ValueError:

        messagebox.showerror(
            "Login Error",
            "Account number must contain digits only."
        )

        return

    connection = connect_database()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            name,
            pin,
            account_locked,
            pin_attempts
        FROM users
        WHERE account_no = ?
        """,
        (account_no,)
    )

    user = cursor.fetchone()

    # -----------------------------------------------------
    # ACCOUNT NOT FOUND
    # -----------------------------------------------------

    if not user:

        connection.close()

        messagebox.showerror(
            "Login Failed",
            "Account not found."
        )

        return

    name, correct_pin, account_locked, pin_attempts = user

    # -----------------------------------------------------
    # ACCOUNT LOCKED
    # -----------------------------------------------------

    if account_locked == 1:

        connection.close()

        messagebox.showerror(
            "Account Locked",
            "Your account has been locked due to "
            "3 incorrect PIN attempts.\n\n"
            "Please contact the administrator."
        )

        return

    # -----------------------------------------------------
    # CORRECT PIN
    # -----------------------------------------------------

    if pin == correct_pin:

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
            account_no,
            name
        )

    # -----------------------------------------------------
    # WRONG PIN
    # -----------------------------------------------------

    else:

        pin_attempts += 1

        if pin_attempts >= 3:

            cursor.execute(
                """
                UPDATE users
                SET
                    pin_attempts = 3,
                    account_locked = 1
                WHERE account_no = ?
                """,
                (account_no,)
            )

            connection.commit()
            connection.close()

            messagebox.showerror(
                "Account Locked",
                "You entered the wrong PIN 3 times.\n\n"
                "Your account has been locked."
            )

        else:

            cursor.execute(
                """
                UPDATE users
                SET pin_attempts = ?
                WHERE account_no = ?
                """,
                (
                    pin_attempts,
                    account_no
                )
            )

            connection.commit()
            connection.close()

            remaining = 3 - pin_attempts

            messagebox.showwarning(
                "Incorrect PIN",
                f"Incorrect PIN.\n\n"
                f"Attempts remaining: {remaining}"
            )


# =========================================================
# MAIN ATM MENU
# =========================================================

# =========================================================
# MODERN MAIN ATM MENU
# =========================================================

def open_main_menu(account_no, name):

    menu_window = tk.Tk()

    menu_window.title("ATM Simulator - Main Menu")
    menu_window.geometry("850x700")
    menu_window.resizable(False, False)
    menu_window.configure(bg="#0B132B")

    # =====================================================
    # HEADER
    # =====================================================

    header = tk.Frame(
        menu_window,
        bg="#0B132B"
    )

    header.pack(
        fill="x",
        pady=(25, 10)
    )

    tk.Label(
        header,
        text="🏦",
        font=("Arial", 38),
        bg="#0B132B",
        fg="white"
    ).pack()

    tk.Label(
        header,
        text="ATM SIMULATOR",
        font=("Arial", 28, "bold"),
        bg="#0B132B",
        fg="white"
    ).pack()

    tk.Label(
        header,
        text="Smart & Secure Banking System",
        font=("Arial", 11),
        bg="#0B132B",
        fg="#94A3B8"
    ).pack(
        pady=(3, 0)
    )

    # =====================================================
    # USER INFORMATION
    # =====================================================

    user_card = tk.Frame(
        menu_window,
        bg="white",
        width=700,
        height=90
    )

    user_card.pack(
        pady=(10, 20)
    )

    user_card.pack_propagate(False)

    left_user = tk.Frame(
        user_card,
        bg="white"
    )

    left_user.pack(
        side="left",
        padx=25,
        pady=15
    )

    tk.Label(
        left_user,
        text=f"Welcome, {name}",
        font=("Arial", 16, "bold"),
        bg="white",
        fg="#111827"
    ).pack(
        anchor="w"
    )

    tk.Label(
        left_user,
        text=f"Account Number: {account_no}",
        font=("Arial", 10),
        bg="white",
        fg="#6B7280"
    ).pack(
        anchor="w",
        pady=(4, 0)
    )

    # Current balance
    balance = check_balance(account_no)

    balance_frame = tk.Frame(
        user_card,
        bg="#EFF6FF"
    )

    balance_frame.pack(
        side="right",
        padx=20,
        pady=12
    )

    tk.Label(
        balance_frame,
        text="AVAILABLE BALANCE",
        font=("Arial", 8, "bold"),
        bg="#EFF6FF",
        fg="#2563EB"
    ).pack(
        padx=18,
        pady=(8, 0)
    )

    tk.Label(
        balance_frame,
        text=f"₹{balance:,.2f}",
        font=("Arial", 15, "bold"),
        bg="#EFF6FF",
        fg="#1E3A8A"
    ).pack(
        padx=18,
        pady=(2, 8)
    )

    # =====================================================
    # MENU TITLE
    # =====================================================

    tk.Label(
        menu_window,
        text="SELECT TRANSACTION",
        font=("Arial", 12, "bold"),
        bg="#0B132B",
        fg="#CBD5E1"
    ).pack(
        pady=(0, 12)
    )

    # =====================================================
    # BUTTON CONTAINER
    # =====================================================

    button_container = tk.Frame(
        menu_window,
        bg="#0B132B"
    )

    button_container.pack()

    # =====================================================
    # BUTTON FUNCTIONS
    # =====================================================

    def balance_button():

        balance = check_balance(account_no)

        messagebox.showinfo(
            "Account Balance",
            f"Available Balance\n\n"
            f"₹{balance:,.2f}"
        )

    # -----------------------------------------------------

    def withdraw_button():

        amount_window = tk.Toplevel(menu_window)

        amount_window.title("Withdraw Cash")
        amount_window.geometry("420x330")
        amount_window.resizable(False, False)
        amount_window.configure(bg="#0B132B")

        tk.Label(
            amount_window,
            text="💸",
            font=("Arial", 35),
            bg="#0B132B",
            fg="white"
        ).pack(pady=(25, 5))

        tk.Label(
            amount_window,
            text="WITHDRAW CASH",
            font=("Arial", 20, "bold"),
            bg="#0B132B",
            fg="white"
        ).pack()

        tk.Label(
            amount_window,
            text="Enter amount to withdraw",
            font=("Arial", 10),
            bg="#0B132B",
            fg="#CBD5E1"
        ).pack(pady=(5, 15))

        amount_entry = tk.Entry(
            amount_window,
            font=("Arial", 14),
            width=25,
            justify="center"
        )

        amount_entry.pack(
            ipady=7
        )

        def process_withdraw():

            try:
                amount = float(
                    amount_entry.get()
                )

            except ValueError:

                messagebox.showerror(
                    "Invalid Amount",
                    "Please enter a valid numeric amount."
                )

                return

            amount_window.destroy()

            withdraw_cash(
                account_no,
                amount
            )

        tk.Button(
            amount_window,
            text="WITHDRAW",
            font=("Arial", 11, "bold"),
            width=25,
            bg="#2563EB",
            fg="white",
            activebackground="#1D4ED8",
            relief="flat",
            cursor="hand2",
            command=process_withdraw
        ).pack(
            pady=25,
            ipady=7
        )

    # -----------------------------------------------------

    def deposit_button():

        amount_window = tk.Toplevel(menu_window)

        amount_window.title("Deposit Cash")
        amount_window.geometry("420x330")
        amount_window.resizable(False, False)
        amount_window.configure(bg="#0B132B")

        tk.Label(
            amount_window,
            text="💵",
            font=("Arial", 35),
            bg="#0B132B",
            fg="white"
        ).pack(pady=(25, 5))

        tk.Label(
            amount_window,
            text="DEPOSIT CASH",
            font=("Arial", 20, "bold"),
            bg="#0B132B",
            fg="white"
        ).pack()

        tk.Label(
            amount_window,
            text="Enter amount to deposit",
            font=("Arial", 10),
            bg="#0B132B",
            fg="#CBD5E1"
        ).pack(pady=(5, 15))

        amount_entry = tk.Entry(
            amount_window,
            font=("Arial", 14),
            width=25,
            justify="center"
        )

        amount_entry.pack(
            ipady=7
        )

        def process_deposit():

            try:
                amount = float(
                    amount_entry.get()
                )

            except ValueError:

                messagebox.showerror(
                    "Invalid Amount",
                    "Please enter a valid numeric amount."
                )

                return

            amount_window.destroy()

            deposit_cash(
                account_no,
                amount
            )

        tk.Button(
            amount_window,
            text="DEPOSIT",
            font=("Arial", 11, "bold"),
            width=25,
            bg="#2563EB",
            fg="white",
            activebackground="#1D4ED8",
            relief="flat",
            cursor="hand2",
            command=process_deposit
        ).pack(
            pady=25,
            ipady=7
        )

    # -----------------------------------------------------

    def transfer_button():

        transfer_window = tk.Toplevel(menu_window)

        transfer_window.title("Account Transfer")
        transfer_window.geometry("450x450")
        transfer_window.resizable(False, False)
        transfer_window.configure(bg="#0B132B")

        tk.Label(
            transfer_window,
            text="🔄",
            font=("Arial", 35),
            bg="#0B132B",
            fg="white"
        ).pack(pady=(20, 5))

        tk.Label(
            transfer_window,
            text="ACCOUNT TRANSFER",
            font=("Arial", 20, "bold"),
            bg="#0B132B",
            fg="white"
        ).pack()

        tk.Label(
            transfer_window,
            text="Receiver Account Number",
            font=("Arial", 10, "bold"),
            bg="#0B132B",
            fg="white"
        ).pack(pady=(20, 5))

        receiver_entry = tk.Entry(
            transfer_window,
            font=("Arial", 13),
            width=25,
            justify="center"
        )

        receiver_entry.pack(
            ipady=6
        )

        tk.Label(
            transfer_window,
            text="Transfer Amount",
            font=("Arial", 10, "bold"),
            bg="#0B132B",
            fg="white"
        ).pack(pady=(15, 5))

        amount_entry = tk.Entry(
            transfer_window,
            font=("Arial", 13),
            width=25,
            justify="center"
        )

        amount_entry.pack(
            ipady=6
        )

        def process_transfer():

            try:

                receiver = int(
                    receiver_entry.get()
                )

                amount = float(
                    amount_entry.get()
                )

            except ValueError:

                messagebox.showerror(
                    "Invalid Input",
                    "Enter a valid account number and amount."
                )

                return

            transfer_window.destroy()

            account_transfer(
                account_no,
                receiver,
                amount
            )

        tk.Button(
            transfer_window,
            text="TRANSFER MONEY",
            font=("Arial", 11, "bold"),
            width=25,
            bg="#2563EB",
            fg="white",
            activebackground="#1D4ED8",
            relief="flat",
            cursor="hand2",
            command=process_transfer
        ).pack(
            pady=25,
            ipady=7
        )

    # -----------------------------------------------------

    def qr_button():

        qr_window = tk.Toplevel(menu_window)

        qr_window.title("QR To Cash")
        qr_window.geometry("420x350")
        qr_window.resizable(False, False)
        qr_window.configure(bg="#0B132B")

        tk.Label(
            qr_window,
            text="📱",
            font=("Arial", 35),
            bg="#0B132B",
            fg="white"
        ).pack(pady=(25, 5))

        tk.Label(
            qr_window,
            text="QR → CASH",
            font=("Arial", 20, "bold"),
            bg="#0B132B",
            fg="white"
        ).pack()

        tk.Label(
            qr_window,
            text="Enter QR payment amount",
            font=("Arial", 10),
            bg="#0B132B",
            fg="#CBD5E1"
        ).pack(pady=(5, 15))

        amount_entry = tk.Entry(
            qr_window,
            font=("Arial", 14),
            width=25,
            justify="center"
        )

        amount_entry.pack(
            ipady=7
        )

        def process_qr():

            try:

                amount = float(
                    amount_entry.get()
                )

            except ValueError:

                messagebox.showerror(
                    "Invalid Amount",
                    "Please enter a valid amount."
                )

                return

            qr_window.destroy()

            qr_to_cash(
                account_no,
                amount
            )

        tk.Button(
            qr_window,
            text="GENERATE QR & GET CASH",
            font=("Arial", 11, "bold"),
            width=28,
            bg="#2563EB",
            fg="white",
            activebackground="#1D4ED8",
            relief="flat",
            cursor="hand2",
            command=process_qr
        ).pack(
            pady=25,
            ipady=7
        )

    # =====================================================
    # MENU BUTTON CREATOR
    # =====================================================

    def create_menu_button(
        parent,
        text,
        command,
        row,
        column
    ):

        button = tk.Button(
            parent,
            text=text,
            font=("Arial", 11, "bold"),
            width=27,
            height=2,
            bg="white",
            fg="#111827",
            activebackground="#EFF6FF",
            activeforeground="#1D4ED8",
            relief="flat",
            bd=0,
            cursor="hand2",
            command=command
        )

        button.grid(
            row=row,
            column=column,
            padx=10,
            pady=8
        )

        return button

    # =====================================================
    # MENU BUTTONS
    # =====================================================

    create_menu_button(
        button_container,
        "💰   CHECK BALANCE",
        balance_button,
        0,
        0
    )

    create_menu_button(
        button_container,
        "💸   WITHDRAW CASH",
        withdraw_button,
        0,
        1
    )

    create_menu_button(
        button_container,
        "💵   DEPOSIT CASH",
        deposit_button,
        1,
        0
    )

    create_menu_button(
        button_container,
        "🔄   ACCOUNT TRANSFER",
        transfer_button,
        1,
        1
    )

    create_menu_button(
        button_container,
        "📱   QR → CASH",
        qr_button,
        2,
        0
    )

    create_menu_button(
        button_container,
        "📄   MINI STATEMENT",
        lambda: mini_statement(account_no),
        2,
        1
    )

    # =====================================================
    # SECURITY INFO
    # =====================================================

    security_frame = tk.Frame(
        menu_window,
        bg="#111C36"
    )

    security_frame.pack(
        pady=(18, 12)
    )

    tk.Label(
        security_frame,
        text="🔒 Secure Session",
        font=("Arial", 9, "bold"),
        bg="#111C36",
        fg="#60A5FA"
    ).pack(
        side="left",
        padx=(15, 5),
        pady=8
    )

    tk.Label(
        security_frame,
        text="Fraud Detection • ML Monitoring",
        font=("Arial", 9),
        bg="#111C36",
        fg="#94A3B8"
    ).pack(
        side="left",
        padx=(5, 15),
        pady=8
    )

    # =====================================================
    # EXIT BUTTON
    # =====================================================

    tk.Button(
        menu_window,
        text="EXIT",
        font=("Arial", 10, "bold"),
        width=18,
        bg="#DC2626",
        fg="white",
        activebackground="#B91C1C",
        relief="flat",
        cursor="hand2",
        command=menu_window.destroy
    ).pack(
        pady=(0, 15),
        ipady=6
    )

    # =====================================================
    # START MENU
    # =====================================================

    menu_window.mainloop()


# =========================================================
# ADMIN LOGIN
# =========================================================

def admin_login():

    admin_window = tk.Toplevel(
        login_window
    )

    admin_window.title(
        "ATM Simulator - Admin Login"
    )

    admin_window.geometry(
        "420x420"
    )

    admin_window.resizable(
        False,
        False
    )

    admin_window.configure(
        bg="#0B132B"
    )

    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------

    tk.Label(
        admin_window,
        text="🔐",
        font=("Arial", 35),
        bg="#0B132B",
        fg="white"
    ).pack(
        pady=(25, 5)
    )

    tk.Label(
        admin_window,
        text="ADMIN LOGIN",
        font=("Arial", 22, "bold"),
        bg="#0B132B",
        fg="white"
    ).pack()

    # -----------------------------------------------------
    # CARD
    # -----------------------------------------------------

    card = tk.Frame(
        admin_window,
        bg="white",
        width=350,
        height=260
    )

    card.pack(
        pady=20
    )

    card.pack_propagate(
        False
    )

    # -----------------------------------------------------
    # ADMIN ID
    # -----------------------------------------------------

    tk.Label(
        card,
        text="ADMIN ID",
        font=("Arial", 10, "bold"),
        bg="white",
        fg="#374151"
    ).pack(
        anchor="w",
        padx=30,
        pady=(20, 5)
    )

    admin_id_entry = tk.Entry(
        card,
        font=("Arial", 13),
        width=25
    )

    admin_id_entry.pack(
        padx=30,
        ipady=5
    )

    # -----------------------------------------------------
    # PASSWORD
    # -----------------------------------------------------

    tk.Label(
        card,
        text="PASSWORD",
        font=("Arial", 10, "bold"),
        bg="white",
        fg="#374151"
    ).pack(
        anchor="w",
        padx=30,
        pady=(10, 5)
    )

    password_entry = tk.Entry(
        card,
        font=("Arial", 13),
        width=25,
        show="*"
    )

    password_entry.pack(
        padx=30,
        ipady=5
    )

    # -----------------------------------------------------
    # VERIFY ADMIN
    # -----------------------------------------------------

    def verify_admin():

        admin_id = admin_id_entry.get().strip()
        password = password_entry.get().strip()

        if (
            admin_id == "admin"
            and password == "admin123"
        ):

            admin_window.destroy()

            open_dashboard()

        else:

            messagebox.showerror(
                "Access Denied",
                "Invalid Admin ID or Password."
            )

    tk.Button(
        card,
        text="LOGIN AS ADMIN",
        font=("Arial", 10, "bold"),
        width=25,
        bg="#2563EB",
        fg="white",
        activebackground="#1D4ED8",
        relief="flat",
        cursor="hand2",
        command=verify_admin
    ).pack(
        pady=15,
        ipady=5
    )


# =========================================================
# MODERN LOGIN WINDOW
# =========================================================

login_window = tk.Tk()

login_window.title(
    "ATM Simulator - Secure Login"
)

login_window.geometry(
    "500x600"
)

login_window.resizable(
    False,
    False
)

login_window.configure(
    bg="#0B132B"
)


# =========================================================
# LOGIN HEADER
# =========================================================

tk.Label(
    login_window,
    text="🏦",
    font=("Arial", 45),
    bg="#0B132B",
    fg="white"
).pack(
    pady=(30, 5)
)

tk.Label(
    login_window,
    text="ATM SIMULATOR",
    font=("Arial", 27, "bold"),
    bg="#0B132B",
    fg="white"
).pack()

tk.Label(
    login_window,
    text="Secure Banking System",
    font=("Arial", 11),
    bg="#0B132B",
    fg="#CBD5E1"
).pack(
    pady=(5, 20)
)


# =========================================================
# LOGIN CARD
# =========================================================

login_card = tk.Frame(
    login_window,
    bg="white",
    width=400,
    height=400
)

login_card.pack(
    padx=50,
    pady=10
)

login_card.pack_propagate(
    False
)


# =========================================================
# WELCOME
# =========================================================

tk.Label(
    login_card,
    text="Welcome Back",
    font=("Arial", 22, "bold"),
    bg="white",
    fg="#111827"
).pack(
    pady=(25, 5)
)

tk.Label(
    login_card,
    text="Login to access your account",
    font=("Arial", 10),
    bg="white",
    fg="#6B7280"
).pack(
    pady=(0, 20)
)


# =========================================================
# ACCOUNT NUMBER
# =========================================================

tk.Label(
    login_card,
    text="ACCOUNT NUMBER",
    font=("Arial", 10, "bold"),
    bg="white",
    fg="#374151"
).pack(
    anchor="w",
    padx=45,
    pady=(5, 5)
)

account_entry = tk.Entry(
    login_card,
    font=("Arial", 13),
    width=28
)

account_entry.pack(
    padx=45,
    ipady=6
)


# =========================================================
# PIN
# =========================================================

tk.Label(
    login_card,
    text="PIN",
    font=("Arial", 10, "bold"),
    bg="white",
    fg="#374151"
).pack(
    anchor="w",
    padx=45,
    pady=(15, 5)
)


pin_frame = tk.Frame(
    login_card,
    bg="white"
)

pin_frame.pack(
    padx=45
)

pin_entry = tk.Entry(
    pin_frame,
    font=("Arial", 13),
    width=22,
    show="*"
)

pin_entry.pack(
    side="left",
    ipady=6
)


# =========================================================
# SHOW / HIDE PIN
# =========================================================

def toggle_pin():

    if pin_entry.cget("show") == "*":

        pin_entry.config(
            show=""
        )

        show_button.config(
            text="HIDE"
        )

    else:

        pin_entry.config(
            show="*"
        )

        show_button.config(
            text="SHOW"
        )


show_button = tk.Button(
    pin_frame,
    text="SHOW",
    font=("Arial", 8, "bold"),
    bg="#E5E7EB",
    fg="#374151",
    relief="flat",
    cursor="hand2",
    command=toggle_pin
)

show_button.pack(
    side="left",
    padx=(5, 0),
    ipadx=5,
    ipady=5
)


# =========================================================
# USER LOGIN BUTTON
# =========================================================

tk.Button(
    login_card,
    text="LOGIN",
    font=("Arial", 13, "bold"),
    width=27,
    bg="#2563EB",
    fg="white",
    activebackground="#1D4ED8",
    activeforeground="white",
    relief="flat",
    cursor="hand2",
    command=login
).pack(
    pady=(20, 10),
    ipady=7
)


# =========================================================
# ADMIN LOGIN BUTTON
# =========================================================

tk.Button(
    login_card,
    text="ADMIN LOGIN",
    font=("Arial", 10, "bold"),
    width=27,
    bg="#E5E7EB",
    fg="#374151",
    activebackground="#D1D5DB",
    relief="flat",
    cursor="hand2",
    command=admin_login
).pack(
    pady=(0, 10),
    ipady=5
)


# =========================================================
# FOOTER
# =========================================================

tk.Label(
    login_window,
    text="Secure • Smart • Intelligent ATM",
    font=("Arial", 9),
    bg="#0B132B",
    fg="#94A3B8"
).pack(
    pady=8
)

tk.Label(
    login_window,
    text="© 2026 ATM Simulator",
    font=("Arial", 8),
    bg="#0B132B",
    fg="#64748B"
).pack()


# =========================================================
# START APPLICATION
# =========================================================

login_window.mainloop()