import tkinter as tk
from tkinter import messagebox
import sqlite3


# =========================
# DATABASE CONNECTION
# =========================

def connect_database():
    return sqlite3.connect("atm.db")


# =========================
# REFILL ATM CASH
# =========================

def refill_cash():

    refill_window = tk.Toplevel(inventory_window)
    refill_window.title("Refill ATM Cash")
    refill_window.geometry("400x350")

    tk.Label(
        refill_window,
        text="REFILL ATM CASH",
        font=("Arial", 20, "bold")
    ).pack(pady=20)

    tk.Label(
        refill_window,
        text="Denomination",
        font=("Arial", 13)
    ).pack(pady=5)

    denomination_entry = tk.Entry(
        refill_window,
        font=("Arial", 14),
        width=20
    )
    denomination_entry.pack(pady=5)

    tk.Label(
        refill_window,
        text="Number of Notes",
        font=("Arial", 13)
    ).pack(pady=10)

    notes_entry = tk.Entry(
        refill_window,
        font=("Arial", 14),
        width=20
    )
    notes_entry.pack(pady=5)

    def process_refill():

        denomination_text = denomination_entry.get()
        notes_text = notes_entry.get()

        if not denomination_text or not notes_text:

            messagebox.showerror(
                "Error",
                "Please enter denomination and number of notes."
            )
            return

        try:
            denomination = int(denomination_text)
            notes = int(notes_text)

        except ValueError:

            messagebox.showerror(
                "Error",
                "Please enter numbers only."
            )
            return

        if denomination not in [500, 200, 100, 50]:

            messagebox.showerror(
                "Invalid Denomination",
                "Use only 500, 200, 100 or 50."
            )
            return

        if notes <= 0:

            messagebox.showerror(
                "Invalid Number",
                "Number of notes must be greater than zero."
            )
            return

        connection = connect_database()
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE atm_cash
            SET note_count = note_count + ?
            WHERE denomination = ?
            """,
            (notes, denomination)
        )

        connection.commit()
        connection.close()

        messagebox.showinfo(
            "Refill Successful",
            f"Added {notes} notes of Rs.{denomination}."
        )

        refill_window.destroy()

        # Refresh inventory display
        update_inventory_display()

    tk.Button(
        refill_window,
        text="ADD CASH",
        font=("Arial", 13, "bold"),
        width=15,
        command=process_refill
    ).pack(pady=25)


# =========================
# UPDATE INVENTORY DISPLAY
# =========================

def update_inventory_display():

    # Remove old inventory labels
    for widget in inventory_frame.winfo_children():
        widget.destroy()

    connection = connect_database()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT denomination, note_count
        FROM atm_cash
        ORDER BY denomination DESC
        """
    )

    inventory = cursor.fetchall()

    connection.close()

    total_cash = 0

    for denomination, note_count in inventory:

        total_cash += denomination * note_count

        tk.Label(
            inventory_frame,
            text=f"Rs.{denomination}    →    {note_count} notes",
            font=("Arial", 15)
        ).pack(pady=10)

    tk.Label(
        inventory_frame,
        text="------------------------------",
        font=("Arial", 12)
    ).pack(pady=10)

    tk.Label(
        inventory_frame,
        text=f"Total Cash: Rs.{total_cash:,.2f}",
        font=("Arial", 16, "bold")
    ).pack(pady=10)


# =========================
# INVENTORY WINDOW
# =========================

inventory_window = tk.Tk()

inventory_window.title("ATM Cash Inventory")
inventory_window.geometry("500x550")


tk.Label(
    inventory_window,
    text="ATM CASH INVENTORY",
    font=("Arial", 22, "bold")
).pack(pady=25)


inventory_frame = tk.Frame(inventory_window)
inventory_frame.pack()


update_inventory_display()


tk.Button(
    inventory_window,
    text="REFILL ATM CASH",
    font=("Arial", 13, "bold"),
    width=18,
    command=refill_cash
).pack(pady=15)


tk.Button(
    inventory_window,
    text="CLOSE",
    font=("Arial", 13, "bold"),
    width=15,
    command=inventory_window.destroy
).pack(pady=10)


inventory_window.mainloop()