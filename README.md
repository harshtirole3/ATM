# ATM Simulator

A demo-only ATM web simulator. It supports account sign-in, deposits,
withdrawals, account transfers, QR-to-cash simulation, and transaction history.
It does not connect to a bank or move real money.

## Run locally

Python 3.10+ is recommended.

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:8000>. The local app uses `atm.db`, creating the demo
accounts on first start:

| Account | PIN |
| --- | --- |
| 1001 | 1234 |
| 1002 | 5678 |

Set `ATM_SQLITE_PATH` to use a different local SQLite file.

## Deploy to Vercel

The hosted app requires a persistent PostgreSQL database; Vercel's function
filesystem is not persistent. Create a PostgreSQL database with a provider of
your choice and configure its connection URL as the `DATABASE_URL` environment
variable in the Vercel project settings (including for the Production
environment). Keep the URL private. The app creates its tables and inserts the
two demo accounts and ATM note inventory on its first API request.

1. Import this repository into Vercel. `pyproject.toml` points its Python
   runtime at the Flask app in `web_app.py`; `vercel.json` routes requests to
   that function.
2. Add `DATABASE_URL` using the provider's PostgreSQL connection string. Use a
   connection string with TLS enabled; use the provider's pooled URL if its
   serverless guidance recommends one.
3. Deploy and open the site. Sign in with either demo account above.

Vercel functions can scale out, so sessions are stored as hashed tokens in
PostgreSQL rather than in process memory. The browser cookie is HttpOnly,
SameSite=Strict, and Secure on Vercel. Never use this simulator for real
customer data or financial transactions.

## Tests

```sh
python -m unittest discover -s tests
```
