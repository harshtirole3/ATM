import random
import sqlite3
from datetime import datetime

from denomination import calculate_denominations


# =========================
# DATABASE CONNECTION
# =========================

def connect_database():
    return sqlite3.connect("atm.db")


# =========================
# GENERATE QR TRANSACTION
# =========================

def generate_qr_transaction():

    transaction_id = "QR" + str(random.randint(100000, 999999))

    return transaction_id


# =========================
# VERIFY QR TRANSACTION
# =========================

def verify_qr_transaction(transaction_id):

    if transaction_id.startswith("QR") and len(transaction_id) == 8:
        return True

    return False


# =========================
# CREATE QR PAYMENT
# =========================

def create_qr_payment(amount):

    transaction_id = generate_qr_transaction()

    return {
        "transaction_id": transaction_id,
        "amount": amount,
        "status": "VERIFIED"
    }


# =========================
# QR TO CASH TRANSACTION
# =========================

def process_qr_cash(account_no, amount):

    payment = create_qr_payment(amount)

    if payment["status"] != "VERIFIED":
        return None

    connection = connect_database()
    cursor = connection.cursor()

    # Check account
    cursor.execute(
        "SELECT balance FROM users WHERE account_no = ?",
        (account_no,)
    )

    user = cursor.fetchone()

    if not user:
        connection.close()
        return None

    balance = user[0]

    # Check balance
    if amount > balance:
        connection.close()
        return None

    # Calculate denominations
    denominations = calculate_denominations(amount)

    if denominations is None:
        connection.close()
        return None

    # Update account balance
    new_balance = balance - amount

    cursor.execute(
        """
        UPDATE users
        SET balance = ?
        WHERE account_no = ?
        """,
        (new_balance, account_no)
    )

    # Update ATM cash inventory
    for note, count in denominations.items():

        cursor.execute(
            """
            UPDATE atm_cash
            SET note_count = note_count - ?
            WHERE denomination = ?
            """,
            (count, note)
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
            "QR TO CASH",
            amount,
            new_balance,
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M:%S")
        )
    )

    connection.commit()
    connection.close()

    return {
        "transaction_id": payment["transaction_id"],
        "amount": amount,
        "denominations": denominations,
        "new_balance": new_balance
    }



    