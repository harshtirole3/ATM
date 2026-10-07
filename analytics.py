import sqlite3
import pandas as pd
import matplotlib.pyplot as plt


def get_transactions():

    connection = sqlite3.connect("atm.db")

    query = """
        SELECT
            account_no,
            transaction_type,
            amount,
            balance_after,
            date,
            time
        FROM transactions
        ORDER BY transaction_id
    """

    df = pd.read_sql_query(query, connection)

    connection.close()

    return df


def show_transaction_summary():

    df = get_transactions()

    if df.empty:
        print("No transactions available.")
        return

    print("\n========================================")
    print("       ATM TRANSACTION ANALYTICS")
    print("========================================")

    print(f"\nTotal Transactions : {len(df)}")

    withdrawals = df[
        df["transaction_type"] == "WITHDRAW"
    ]

    deposits = df[
        df["transaction_type"] == "DEPOSIT"
    ]

    print(
        f"Total Withdrawals  : "
        f"₹{withdrawals['amount'].sum():,.2f}"
    )

    print(
        f"Total Deposits     : "
        f"₹{deposits['amount'].sum():,.2f}"
    )

    print(
        f"Withdrawal Count   : "
        f"{len(withdrawals)}"
    )

    print(
        f"Deposit Count      : "
        f"{len(deposits)}"
    )


def show_transaction_chart():

    df = get_transactions()

    if df.empty:
        print("No transaction data available.")
        return

    summary = (
        df.groupby("transaction_type")["amount"]
        .sum()
    )

    summary.plot(
        kind="bar",
        title="ATM Transaction Summary",
        xlabel="Transaction Type",
        ylabel="Amount (₹)"
    )

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":

    show_transaction_summary()

    show_transaction_chart()