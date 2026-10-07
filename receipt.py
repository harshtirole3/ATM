import os
from datetime import datetime


# =========================
# GENERATE DIGITAL RECEIPT
# =========================

def generate_receipt(
    account_no,
    transaction_type,
    amount,
    balance_after,
    transaction_id=None,
    denominations=None
):

    # Create receipts folder
    if not os.path.exists("receipts"):
        os.makedirs("receipts")

    # Generate transaction ID if not provided
    if transaction_id is None:
        transaction_id = "TXN" + datetime.now().strftime("%Y%m%d%H%M%S")

    now = datetime.now()

    receipt = f"""
========================================
              ATM RECEIPT
========================================

Transaction ID : {transaction_id}
Account Number : {account_no}

Transaction    : {transaction_type}
Amount         : Rs.{amount:,.2f}

Date           : {now.strftime("%Y-%m-%d")}
Time           : {now.strftime("%H:%M:%S")}

Balance After  : Rs.{balance_after:,.2f}
"""

    # Add denomination details for cash withdrawal
    if denominations:

        receipt += """
----------------------------------------
Cash Dispensed
----------------------------------------
"""

        for note, count in denominations.items():
            receipt += f"Rs.{note} x {count}\n"

    receipt += """
========================================
          THANK YOU FOR BANKING
========================================
"""

    # Create unique filename
    filename = (
        f"receipts/"
        f"{transaction_id}.txt"
    )

    with open(filename, "w") as file:
        file.write(receipt)

    return filename