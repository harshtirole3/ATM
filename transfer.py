import sqlite3
from datetime import datetime


def connect_database():
    return sqlite3.connect("atm.db")


def transfer_money(sender_account, receiver_account, amount):

    connection = connect_database()
    cursor = connection.cursor()

    # Check sender
    cursor.execute(
        "SELECT balance FROM users WHERE account_no = ?",
        (sender_account,)
    )

    sender = cursor.fetchone()

    if not sender:
        connection.close()
        return "SENDER_NOT_FOUND"

    # Check receiver
    cursor.execute(
        "SELECT balance FROM users WHERE account_no = ?",
        (receiver_account,)
    )

    receiver = cursor.fetchone()

    if not receiver:
        connection.close()
        return "RECEIVER_NOT_FOUND"

    # Prevent transferring to same account
    if sender_account == receiver_account:
        connection.close()
        return "SAME_ACCOUNT"

    sender_balance = sender[0]

    # Check balance
    if amount > sender_balance:
        connection.close()
        return "INSUFFICIENT_BALANCE"

    # Check amount
    if amount <= 0:
        connection.close()
        return "INVALID_AMOUNT"

    new_sender_balance = sender_balance - amount
    new_receiver_balance = receiver[0] + amount

    # Update sender
    cursor.execute(
        """
        UPDATE users
        SET balance = ?
        WHERE account_no = ?
        """,
        (new_sender_balance, sender_account)
    )

    # Update receiver
    cursor.execute(
        """
        UPDATE users
        SET balance = ?
        WHERE account_no = ?
        """,
        (new_receiver_balance, receiver_account)
    )

    now = datetime.now()

    # Sender transaction
    cursor.execute(
        """
        INSERT INTO transactions
        (account_no, transaction_type, amount, balance_after, date, time)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            sender_account,
            "TRANSFER SENT",
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
        (account_no, transaction_type, amount, balance_after, date, time)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            receiver_account,
            "TRANSFER RECEIVED",
            amount,
            new_receiver_balance,
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M:%S")
        )
    )

    connection.commit()
    connection.close()

    return {
        "status": "SUCCESS",
        "sender_balance": new_sender_balance,
        "receiver_balance": new_receiver_balance
    }