import sqlite3


def connect_database():
    return sqlite3.connect("atm.db")


def calculate_denominations(amount):

    connection = connect_database()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT denomination, note_count
        FROM atm_cash
        ORDER BY denomination DESC
    """)

    cash_inventory = cursor.fetchall()

    connection.close()

    result = {}

    for denomination, note_count in cash_inventory:

        count_needed = amount // denomination

        count_to_dispense = min(count_needed, note_count)

        if count_to_dispense > 0:

            result[denomination] = int(count_to_dispense)

            amount = amount - (
                denomination * count_to_dispense
            )

    if amount != 0:
        return None

    return result


    if amount != 0:
        return None

    return result