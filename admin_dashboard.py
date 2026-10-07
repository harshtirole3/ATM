import tkinter as tk
from tkinter import messagebox
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt


# =========================================================
# DATABASE CONNECTION
# =========================================================

def connect_database():
    return sqlite3.connect("atm.db")


# =========================================================
# GET ATM CASH INVENTORY
# =========================================================

def get_atm_cash():

    connection = connect_database()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT denomination, note_count
        FROM atm_cash
        ORDER BY denomination DESC
    """)

    data = cursor.fetchall()

    connection.close()

    return data


# =========================================================
# GET TRANSACTION DATA
# =========================================================

def get_transaction_data():

    connection = connect_database()

    query = """
        SELECT
            transaction_id,
            account_no,
            transaction_type,
            amount,
            balance_after,
            date,
            time
        FROM transactions
        ORDER BY transaction_id DESC
    """

    data = pd.read_sql_query(
        query,
        connection
    )

    connection.close()

    return data


# =========================================================
# DASHBOARD DATA
# =========================================================

def get_dashboard_data():

    connection = connect_database()
    cursor = connection.cursor()

    # Total accounts
    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    total_accounts = cursor.fetchone()[0]

    # Locked accounts
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE account_locked = 1
        """
    )

    locked_accounts = cursor.fetchone()[0]

    # Total ATM cash
    cursor.execute(
        """
        SELECT SUM(
            denomination * note_count
        )
        FROM atm_cash
        """
    )

    total_cash = cursor.fetchone()[0]

    if total_cash is None:
        total_cash = 0

    # Total transactions
    cursor.execute(
        "SELECT COUNT(*) FROM transactions"
    )

    total_transactions = cursor.fetchone()[0]

    connection.close()

    return (
        total_accounts,
        locked_accounts,
        total_cash,
        total_transactions
    )


# =========================================================
# SHOW TRANSACTION ANALYTICS
# =========================================================

def show_chart():

    data = get_transaction_data()

    if data.empty:

        messagebox.showinfo(
            "Transaction Analytics",
            "No transaction data available."
        )

        return

    # -----------------------------------------------------
    # TRANSACTION SUMMARY
    # -----------------------------------------------------

    withdrawal_total = data.loc[
        data["transaction_type"] == "WITHDRAW",
        "amount"
    ].sum()

    deposit_total = data.loc[
        data["transaction_type"] == "DEPOSIT",
        "amount"
    ].sum()

    transfer_out_total = data.loc[
        data["transaction_type"].isin(
            ["TRANSFER OUT", "TRANSFER SENT"]
        ),
        "amount"
    ].sum()

    transfer_in_total = data.loc[
        data["transaction_type"].isin(
            ["TRANSFER IN", "TRANSFER RECEIVED"]
        ),
        "amount"
    ].sum()

    qr_total = data.loc[
        data["transaction_type"] == "QR TO CASH",
        "amount"
    ].sum()

    transaction_counts = (
        data["transaction_type"]
        .value_counts()
    )

    # -----------------------------------------------------
    # SUMMARY WINDOW
    # -----------------------------------------------------

    analytics_window = tk.Toplevel()

    analytics_window.title(
        "Transaction Analytics"
    )

    analytics_window.geometry(
        "800x650"
    )

    analytics_window.resizable(
        False,
        False
    )

    analytics_window.configure(
        bg="#0B132B"
    )

    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------

    tk.Label(
        analytics_window,
        text="📊",
        font=("Arial", 35),
        bg="#0B132B",
        fg="white"
    ).pack(
        pady=(20, 0)
    )

    tk.Label(
        analytics_window,
        text="TRANSACTION ANALYTICS",
        font=("Arial", 22, "bold"),
        bg="#0B132B",
        fg="white"
    ).pack()

    tk.Label(
        analytics_window,
        text="ATM transaction monitoring & analysis",
        font=("Arial", 10),
        bg="#0B132B",
        fg="#94A3B8"
    ).pack(
        pady=(3, 15)
    )

    # -----------------------------------------------------
    # SUMMARY CARD
    # -----------------------------------------------------

    summary_card = tk.Frame(
        analytics_window,
        bg="white"
    )

    summary_card.pack(
        padx=40,
        pady=10,
        fill="x"
    )

    summary_text = (
        f"Total Transactions : {len(data)}\n\n"
        f"Withdrawals        : ₹{withdrawal_total:,.2f}\n"
        f"Deposits           : ₹{deposit_total:,.2f}\n"
        f"Transfers Out      : ₹{transfer_out_total:,.2f}\n"
        f"Transfers In       : ₹{transfer_in_total:,.2f}\n"
        f"QR → Cash          : ₹{qr_total:,.2f}"
    )

    tk.Label(
        summary_card,
        text=summary_text,
        font=("Arial", 11),
        bg="white",
        fg="#111827",
        justify="left"
    ).pack(
        padx=25,
        pady=18,
        anchor="w"
    )

    # -----------------------------------------------------
    # SHOW CHART
    # -----------------------------------------------------

    def display_chart():

        chart_data = (
            data.groupby(
                "transaction_type"
            )["amount"]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        plt.figure(
            figsize=(9, 5)
        )

        chart_data.plot(
            kind="bar"
        )

        plt.title(
            "Transaction Amount by Type"
        )

        plt.xlabel(
            "Transaction Type"
        )

        plt.ylabel(
            "Amount (₹)"
        )

        plt.xticks(
            rotation=30,
            ha="right"
        )

        plt.tight_layout()

        plt.show()

    # -----------------------------------------------------
    # CHART BUTTON
    # -----------------------------------------------------

    tk.Button(
        analytics_window,
        text="📈  VIEW TRANSACTION CHART",
        font=("Arial", 11, "bold"),
        width=30,
        bg="#2563EB",
        fg="white",
        activebackground="#1D4ED8",
        relief="flat",
        cursor="hand2",
        command=display_chart
    ).pack(
        pady=15,
        ipady=7
    )

    # -----------------------------------------------------
    # TRANSACTION COUNTS
    # -----------------------------------------------------

    count_card = tk.Frame(
        analytics_window,
        bg="#111C36"
    )

    count_card.pack(
        padx=40,
        pady=10,
        fill="x"
    )

    counts_text = "Transaction Count:  "

    for transaction_type, count in transaction_counts.items():

        counts_text += (
            f"{transaction_type}: {count}    "
        )

    tk.Label(
        count_card,
        text=counts_text,
        font=("Arial", 9),
        bg="#111C36",
        fg="#CBD5E1",
        wraplength=700
    ).pack(
        padx=15,
        pady=12
    )

    # -----------------------------------------------------
    # CLOSE
    # -----------------------------------------------------

    tk.Button(
        analytics_window,
        text="CLOSE",
        font=("Arial", 10, "bold"),
        width=18,
        bg="#DC2626",
        fg="white",
        activebackground="#B91C1C",
        relief="flat",
        cursor="hand2",
        command=analytics_window.destroy
    ).pack(
        pady=12,
        ipady=5
    )


# =========================================================
# SHOW ATM INVENTORY
# =========================================================

def show_inventory():

    inventory_window = tk.Toplevel()

    inventory_window.title(
        "ATM Cash Inventory"
    )

    inventory_window.geometry(
        "650x550"
    )

    inventory_window.resizable(
        False,
        False
    )

    inventory_window.configure(
        bg="#0B132B"
    )

    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------

    tk.Label(
        inventory_window,
        text="🏧",
        font=("Arial", 35),
        bg="#0B132B",
        fg="white"
    ).pack(
        pady=(25, 0)
    )

    tk.Label(
        inventory_window,
        text="ATM CASH INVENTORY",
        font=("Arial", 22, "bold"),
        bg="#0B132B",
        fg="white"
    ).pack()

    tk.Label(
        inventory_window,
        text="Current denomination availability",
        font=("Arial", 10),
        bg="#0B132B",
        fg="#94A3B8"
    ).pack(
        pady=(3, 20)
    )

    # -----------------------------------------------------
    # INVENTORY CARD
    # -----------------------------------------------------

    card = tk.Frame(
        inventory_window,
        bg="white"
    )

    card.pack(
        padx=50,
        fill="x"
    )

    headers = [
        "DENOMINATION",
        "NOTE COUNT",
        "TOTAL VALUE"
    ]

    for column, header in enumerate(headers):

        tk.Label(
            card,
            text=header,
            font=("Arial", 10, "bold"),
            bg="#E5E7EB",
            fg="#111827",
            width=20
        ).grid(
            row=0,
            column=column,
            padx=1,
            pady=1
        )

    inventory = get_atm_cash()

    total_cash = 0

    for row_index, (
        denomination,
        note_count
    ) in enumerate(
        inventory,
        start=1
    ):

        value = (
            denomination * note_count
        )

        total_cash += value

        tk.Label(
            card,
            text=f"₹{denomination}",
            font=("Arial", 10),
            bg="white",
            fg="#111827",
            width=20
        ).grid(
            row=row_index,
            column=0,
            pady=5
        )

        tk.Label(
            card,
            text=str(note_count),
            font=("Arial", 10),
            bg="white",
            fg="#111827",
            width=20
        ).grid(
            row=row_index,
            column=1,
            pady=5
        )

        tk.Label(
            card,
            text=f"₹{value:,.2f}",
            font=("Arial", 10),
            bg="white",
            fg="#111827",
            width=20
        ).grid(
            row=row_index,
            column=2,
            pady=5
        )

    # -----------------------------------------------------
    # TOTAL CASH
    # -----------------------------------------------------

    tk.Label(
        inventory_window,
        text=f"TOTAL ATM CASH: ₹{total_cash:,.2f}",
        font=("Arial", 16, "bold"),
        bg="#111C36",
        fg="#60A5FA"
    ).pack(
        pady=20,
        ipadx=20,
        ipady=10
    )

    # -----------------------------------------------------
    # CLOSE
    # -----------------------------------------------------

    tk.Button(
        inventory_window,
        text="CLOSE",
        font=("Arial", 10, "bold"),
        width=18,
        bg="#DC2626",
        fg="white",
        activebackground="#B91C1C",
        relief="flat",
        cursor="hand2",
        command=inventory_window.destroy
    ).pack(
        pady=10,
        ipady=5
    )


# =========================================================
# UNLOCK ACCOUNT
# =========================================================

def unlock_account():

    unlock_window = tk.Toplevel()

    unlock_window.title(
        "Unlock Account"
    )

    unlock_window.geometry(
        "450x400"
    )

    unlock_window.resizable(
        False,
        False
    )

    unlock_window.configure(
        bg="#0B132B"
    )

    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------

    tk.Label(
        unlock_window,
        text="🔓",
        font=("Arial", 35),
        bg="#0B132B",
        fg="white"
    ).pack(
        pady=(25, 0)
    )

    tk.Label(
        unlock_window,
        text="UNLOCK ACCOUNT",
        font=("Arial", 22, "bold"),
        bg="#0B132B",
        fg="white"
    ).pack()

    tk.Label(
        unlock_window,
        text="Reset PIN attempt counter",
        font=("Arial", 10),
        bg="#0B132B",
        fg="#94A3B8"
    ).pack(
        pady=(3, 20)
    )

    # -----------------------------------------------------
    # CARD
    # -----------------------------------------------------

    card = tk.Frame(
        unlock_window,
        bg="white",
        width=350,
        height=190
    )

    card.pack()

    card.pack_propagate(False)

    tk.Label(
        card,
        text="ACCOUNT NUMBER",
        font=("Arial", 10, "bold"),
        bg="white",
        fg="#374151"
    ).pack(
        anchor="w",
        padx=30,
        pady=(25, 5)
    )

    account_entry = tk.Entry(
        card,
        font=("Arial", 13),
        width=25,
        justify="center"
    )

    account_entry.pack(
        padx=30,
        ipady=6
    )

    # -----------------------------------------------------
    # PROCESS UNLOCK
    # -----------------------------------------------------

    def process_unlock():

        account_text = (
            account_entry.get().strip()
        )

        try:

            account_no = int(
                account_text
            )

        except ValueError:

            messagebox.showerror(
                "Invalid Account",
                "Enter a valid account number."
            )

            return

        connection = connect_database()
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT account_locked
            FROM users
            WHERE account_no = ?
            """,
            (account_no,)
        )

        result = cursor.fetchone()

        if not result:

            connection.close()

            messagebox.showerror(
                "Account Not Found",
                "No account exists with this number."
            )

            return

        cursor.execute(
            """
            UPDATE users
            SET
                account_locked = 0,
                pin_attempts = 0
            WHERE account_no = ?
            """,
            (account_no,)
        )

        connection.commit()
        connection.close()

        messagebox.showinfo(
            "Account Unlocked",
            f"Account {account_no} has been unlocked successfully."
        )

        unlock_window.destroy()

    # -----------------------------------------------------
    # UNLOCK BUTTON
    # -----------------------------------------------------

    tk.Button(
        card,
        text="🔓  UNLOCK ACCOUNT",
        font=("Arial", 10, "bold"),
        width=25,
        bg="#2563EB",
        fg="white",
        activebackground="#1D4ED8",
        relief="flat",
        cursor="hand2",
        command=process_unlock
    ).pack(
        pady=20,
        ipady=6
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

def open_dashboard():

    dashboard = tk.Tk()

    dashboard.title(
        "ATM Simulator - Admin Dashboard"
    )

    dashboard.geometry(
        "900x700"
    )

    dashboard.resizable(
        False,
        False
    )

    dashboard.configure(
        bg="#0B132B"
    )

    # =====================================================
    # HEADER
    # =====================================================

    header = tk.Frame(
        dashboard,
        bg="#0B132B"
    )

    header.pack(
        pady=(25, 5)
    )

    tk.Label(
        header,
        text="🔐",
        font=("Arial", 35),
        bg="#0B132B",
        fg="white"
    ).pack()

    tk.Label(
        header,
        text="ADMIN DASHBOARD",
        font=("Arial", 27, "bold"),
        bg="#0B132B",
        fg="white"
    ).pack()

    tk.Label(
        header,
        text="ATM Management & Monitoring System",
        font=("Arial", 11),
        bg="#0B132B",
        fg="#94A3B8"
    ).pack(
        pady=(3, 0)
    )

    # =====================================================
    # DASHBOARD STATISTICS
    # =====================================================

    (
        total_accounts,
        locked_accounts,
        total_cash,
        total_transactions
    ) = get_dashboard_data()

    stats_frame = tk.Frame(
        dashboard,
        bg="#0B132B"
    )

    stats_frame.pack(
        pady=20
    )

    def create_stat_card(
        title,
        value,
        row,
        column
    ):

        card = tk.Frame(
            stats_frame,
            bg="white",
            width=190,
            height=100
        )

        card.grid(
            row=row,
            column=column,
            padx=10
        )

        card.grid_propagate(False)

        tk.Label(
            card,
            text=title,
            font=("Arial", 9, "bold"),
            bg="white",
            fg="#6B7280"
        ).pack(
            pady=(18, 3)
        )

        tk.Label(
            card,
            text=value,
            font=("Arial", 18, "bold"),
            bg="white",
            fg="#1D4ED8"
        ).pack()

    create_stat_card(
        "TOTAL ACCOUNTS",
        str(total_accounts),
        0,
        0
    )

    create_stat_card(
        "LOCKED ACCOUNTS",
        str(locked_accounts),
        0,
        1
    )

    create_stat_card(
        "ATM CASH",
        f"₹{total_cash:,.0f}",
        0,
        2
    )

    create_stat_card(
        "TRANSACTIONS",
        str(total_transactions),
        0,
        3
    )

    # =====================================================
    # ACTION TITLE
    # =====================================================

    tk.Label(
        dashboard,
        text="ADMIN CONTROLS",
        font=("Arial", 12, "bold"),
        bg="#0B132B",
        fg="#CBD5E1"
    ).pack(
        pady=(10, 12)
    )

    # =====================================================
    # ACTION BUTTONS
    # =====================================================

    action_frame = tk.Frame(
        dashboard,
        bg="#0B132B"
    )

    action_frame.pack()

    def create_action_button(
        text,
        command,
        row,
        column
    ):

        button = tk.Button(
            action_frame,
            text=text,
            font=("Arial", 11, "bold"),
            width=30,
            height=2,
            bg="white",
            fg="#111827",
            activebackground="#EFF6FF",
            activeforeground="#1D4ED8",
            relief="flat",
            cursor="hand2",
            command=command
        )

        button.grid(
            row=row,
            column=column,
            padx=10,
            pady=8
        )

    create_action_button(
        "🏧  VIEW ATM INVENTORY",
        show_inventory,
        0,
        0
    )

    create_action_button(
        "📊  VIEW TRANSACTION ANALYTICS",
        show_chart,
        0,
        1
    )

    create_action_button(
        "🔓  UNLOCK ACCOUNT",
        unlock_account,
        1,
        0
    )

    # =====================================================
    # SECURITY INFORMATION
    # =====================================================

    security_frame = tk.Frame(
        dashboard,
        bg="#111C36"
    )

    security_frame.pack(
        padx=80,
        pady=25,
        fill="x"
    )

    tk.Label(
        security_frame,
        text="🔒 ADMIN ACCESS",
        font=("Arial", 10, "bold"),
        bg="#111C36",
        fg="#60A5FA"
    ).pack(
        side="left",
        padx=20,
        pady=12
    )

    tk.Label(
        security_frame,
        text="Inventory • Analytics • Account Security",
        font=("Arial", 9),
        bg="#111C36",
        fg="#94A3B8"
    ).pack(
        side="left",
        pady=12
    )

    # =====================================================
    # CLOSE
    # =====================================================

    tk.Button(
        dashboard,
        text="CLOSE DASHBOARD",
        font=("Arial", 10, "bold"),
        width=22,
        bg="#DC2626",
        fg="white",
        activebackground="#B91C1C",
        relief="flat",
        cursor="hand2",
        command=dashboard.destroy
    ).pack(
        pady=5,
        ipady=6
    )

    dashboard.mainloop()


# =========================================================
# TEST / DIRECT RUN
# =========================================================

if __name__ == "__main__":
    open_dashboard()