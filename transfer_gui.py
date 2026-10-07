import tkinter as tk
from tkinter import messagebox
from transfer import transfer_money


def open_transfer_window(sender_account):

    transfer_window = tk.Toplevel()
    transfer_window.title("Transfer Money")
    transfer_window.geometry("450x450")

    tk.Label(
        transfer_window,
        text="TRANSFER MONEY",
        font=("Arial", 22, "bold")
    ).pack(pady=25)

    tk.Label(
        transfer_window,
        text=f"Your Account: {sender_account}",
        font=("Arial", 13)
    ).pack(pady=10)

    tk.Label(
        transfer_window,
        text="Receiver Account Number",
        font=("Arial", 13)
    ).pack(pady=8)

    receiver_entry = tk.Entry(
        transfer_window,
        font=("Arial", 14),
        width=22
    )
    receiver_entry.pack(pady=5)

    tk.Label(
        transfer_window,
        text="Amount",
        font=("Arial", 13)
    ).pack(pady=12)

    amount_entry = tk.Entry(
        transfer_window,
        font=("Arial", 14),
        width=22
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
                "Invalid Input",
                "Please enter valid numbers."
            )
            return

        if amount <= 0:
            messagebox.showerror(
                "Invalid Amount",
                "Amount must be greater than zero."
            )
            return

        result = transfer_money(
            sender_account,
            receiver_account,
            amount
        )

        if result == "RECEIVER_NOT_FOUND":

            messagebox.showerror(
                "Account Not Found",
                "Receiver account does not exist."
            )

            return

        if result == "SAME_ACCOUNT":

            messagebox.showerror(
                "Invalid Transfer",
                "You cannot transfer money to your own account."
            )

            return

        if result == "INSUFFICIENT_BALANCE":

            messagebox.showerror(
                "Insufficient Balance",
                "You do not have enough balance."
            )

            return

        if result == "INVALID_AMOUNT":

            messagebox.showerror(
                "Invalid Amount",
                "Amount must be greater than zero."
            )

            return

        if result == "SENDER_NOT_FOUND":

            messagebox.showerror(
                "Error",
                "Sender account was not found."
            )

            return

        if isinstance(result, dict):

            messagebox.showinfo(
                "Transfer Successful",
                f"₹{amount:,.2f} transferred successfully!\n\n"
                f"Receiver Account: {receiver_account}\n\n"
                f"Remaining Balance: "
                f"₹{result['sender_balance']:,.2f}"
            )

            transfer_window.destroy()

    tk.Button(
        transfer_window,
        text="TRANSFER",
        font=("Arial", 13, "bold"),
        width=18,
        command=process_transfer
    ).pack(pady=30)

    tk.Button(
        transfer_window,
        text="CANCEL",
        font=("Arial", 12),
        width=15,
        command=transfer_window.destroy
    ).pack()


if __name__ == "__main__":

    root = tk.Tk()
    root.withdraw()

    open_transfer_window(1001)

    root.mainloop()