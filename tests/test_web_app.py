import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import app as atm
import web_app


class WebAppTests(unittest.TestCase):
    def setUp(self):
        self.database_url = os.environ.pop("DATABASE_URL", None)
        self.postgres_url = os.environ.pop("POSTGRES_URL", None)
        self.vercel = os.environ.pop("VERCEL", None)
        self.temp_dir = tempfile.TemporaryDirectory()
        atm.DATABASE = Path(self.temp_dir.name) / "test-atm.db"
        web_app._database_ready = False
        self.client = web_app.app.test_client()

    def tearDown(self):
        if self.database_url is not None:
            os.environ["DATABASE_URL"] = self.database_url
        if self.postgres_url is not None:
            os.environ["POSTGRES_URL"] = self.postgres_url
        if self.vercel is not None:
            os.environ["VERCEL"] = self.vercel
        self.temp_dir.cleanup()

    def sign_in(self):
        return self.client.post(
            "/api/login", json={"account_no": "1001", "pin": "1234"}
        )

    def test_static_page_is_served(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ATM Simulator", response.data)

    def test_postgres_provider_url_is_supported(self):
        os.environ["POSTGRES_URL"] = "postgresql://example.invalid/test"
        with patch.object(atm.psycopg, "connect") as connect:
            connection = atm.connect_database()

        connect.assert_called_once()
        self.assertEqual(
            connect.call_args.args[0], "postgresql://example.invalid/test"
        )
        self.assertTrue(connection.postgres)
        connection.close()
        connection.connection.close.assert_called_once()

    def test_login_deposit_and_database_backed_logout(self):
        login = self.sign_in()
        self.assertEqual(login.status_code, 200)
        self.assertIn("HttpOnly", login.headers["Set-Cookie"])
        self.assertIn("SameSite=Strict", login.headers["Set-Cookie"])

        deposit = self.client.post("/api/transactions/deposit", json={"amount": 500})
        self.assertEqual(deposit.status_code, 201)
        self.assertEqual(deposit.json["balance"], 50500)

        dashboard = self.client.get("/api/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(dashboard.json["account"]["balance"], 50500)

        logout = self.client.post("/api/logout", json={})
        self.assertEqual(logout.status_code, 200)
        self.assertEqual(self.client.get("/api/dashboard").status_code, 401)

    def test_withdrawal_updates_balance_and_inventory(self):
        self.assertEqual(self.sign_in().status_code, 200)

        withdrawal = self.client.post(
            "/api/transactions/withdraw",
            json={"amount": 500, "confirmed_high_risk": False},
        )

        self.assertEqual(withdrawal.status_code, 201)
        self.assertEqual(withdrawal.json["balance"], 49500)
        self.assertEqual(withdrawal.json["denominations"], {"500": 1})

    def test_transfer_updates_both_accounts(self):
        self.assertEqual(self.sign_in().status_code, 200)

        transfer = self.client.post(
            "/api/transactions/transfer",
            json={"receiver_account": "1002", "amount": 1000},
        )

        self.assertEqual(transfer.status_code, 201)
        self.assertEqual(transfer.json["balance"], 49000)

        logout = self.client.post("/api/logout", json={})
        self.assertEqual(logout.status_code, 200)
        receiver_login = self.client.post(
            "/api/login", json={"account_no": "1002", "pin": "5678"}
        )
        self.assertEqual(receiver_login.status_code, 200)
        dashboard = self.client.get("/api/dashboard")
        self.assertEqual(dashboard.json["account"]["balance"], 26000)


if __name__ == "__main__":
    unittest.main()
