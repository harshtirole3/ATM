from email.message import Message
from io import BytesIO
import os
import threading

from flask import Flask, Response, jsonify, request

from app import ATMRequestHandler, DATABASE_ERRORS, initialize_database


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20_000
_database_ready = False
_database_lock = threading.Lock()


class WSGIATMRequestHandler(ATMRequestHandler):
    def __init__(self, path, headers, body, secure):
        self.path = path
        self.headers = headers
        self.rfile = BytesIO(body)
        self.wfile = BytesIO()
        self.response_status = 200
        self.response_headers = {}
        self.secure = secure

    def send_response(self, code, message=None):
        self.response_status = code

    def send_header(self, name, value):
        self.response_headers[name] = value

    def end_headers(self):
        pass


def ensure_database():
    global _database_ready
    if _database_ready:
        return
    with _database_lock:
        if not _database_ready:
            initialize_database()
            _database_ready = True


@app.errorhandler(413)
def request_too_large(_error):
    return jsonify({"error": "Request body is missing or too large."}), 413


@app.route("/", defaults={"path": ""}, methods=["GET", "POST"])
@app.route("/<path:path>", methods=["GET", "POST"])
def dispatch(path):
    del path
    if request.path.startswith("/api/"):
        try:
            ensure_database()
        except RuntimeError as error:
            app.logger.exception("ATM deployment configuration error")
            return jsonify({"error": str(error)}), 503
        except DATABASE_ERRORS:
            app.logger.exception("ATM database initialization failed")
            return jsonify({"error": "Database error. Please try again."}), 500

    headers = Message()
    for name, value in request.headers.items():
        headers[name] = value
    body = request.get_data(cache=False)
    headers["Content-Length"] = str(len(body))
    handler = WSGIATMRequestHandler(
        request.full_path,
        headers,
        body,
        secure=request.is_secure or bool(os.environ.get("VERCEL")),
    )
    if request.method in {"GET", "HEAD"}:
        handler.do_GET()
    else:
        handler.do_POST()

    return Response(
        handler.wfile.getvalue(),
        status=handler.response_status,
        headers=handler.response_headers,
    )
