import sqlite3
from datetime import datetime, timedelta


def check_large_withdrawal(amount):

    if amount > 10000:
        return True

    return False


def check_repeated_withdrawals(account_no):

    connection = sqlite3.connect("atm.db")
    cursor = connection.cursor()

    current_time = datetime.now()
    five_minutes_ago = current_time - timedelta(minutes=5)

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM transactions
        WHERE account_no = ?
        AND transaction_type = 'WITHDRAW'
        AND date || ' ' || time >= ?
        """,
        (
            account_no,
            five_minutes_ago.strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    result = cursor.fetchone()

    connection.close()

    if result[0] >= 3:
        return True

    return False
def check_suspicious_pattern(account_no):

    connection = sqlite3.connect("atm.db")
    cursor = connection.cursor()

    current_time = datetime.now()
    thirty_minutes_ago = current_time - timedelta(minutes=30)

    cursor.execute(
        """
        SELECT amount
        FROM transactions
        WHERE account_no = ?
        AND transaction_type = 'WITHDRAW'
        AND date || ' ' || time >= ?
        """,
        (
            account_no,
            thirty_minutes_ago.strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    transactions = cursor.fetchall()

    connection.close()

    amounts = [transaction[0] for transaction in transactions]

    for amount in set(amounts):

        if amounts.count(amount) >= 5:
            return True

    return False
