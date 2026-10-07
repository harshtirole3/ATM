import sqlite3
import pandas as pd
from sklearn.ensemble import IsolationForest


def get_transaction_data():

    connection = sqlite3.connect("atm.db")

    query = """
        SELECT account_no, amount
        FROM transactions
        WHERE transaction_type = 'WITHDRAW'
    """

    df = pd.read_sql_query(query, connection)

    connection.close()

    return df


def train_fraud_model():

    df = get_transaction_data()

    # Need enough transactions to train the model
    if len(df) < 5:
        return None

    df["transaction_frequency"] = (
        df.groupby("account_no")["account_no"]
        .transform("count")
    )

    training_data = df[
        ["amount", "transaction_frequency"]
    ]

    model = IsolationForest(
        contamination=0.2,
        random_state=42
    )

    model.fit(training_data)

    return model


def detect_anomaly(account_no, amount):

    model = train_fraud_model()

    if model is None:
        return False

    connection = sqlite3.connect("atm.db")
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM transactions
        WHERE account_no = ?
        AND transaction_type = 'WITHDRAW'
        """,
        (account_no,)
    )

    transaction_frequency = cursor.fetchone()[0]

    connection.close()

    prediction = model.predict(
        [[amount, transaction_frequency]]
    )

    if prediction[0] == -1:
        return True

    return False
print(detect_anomaly(1001, 5000))