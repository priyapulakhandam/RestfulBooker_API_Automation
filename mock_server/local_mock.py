"""Lightweight in-memory mock server mimicking Restful-Booker API."""
import json
import re
import threading
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Optional, Set
from utils.logger import get_logger

logger = get_logger("MockServer")


class MockBookerHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler emulating Restful-Booker endpoints."""

    # In-memory storage shared across requests
    bookings: Dict[int, dict] = {
        1: {
            "firstname": "Eric",
            "lastname": "Jones",
            "totalprice": 279,
            "depositpaid": False,
            "bookingdates": {"checkin": "2026-05-18", "checkout": "2026-05-20"},
            "additionalneeds": "Breakfast",
        }
    }
    valid_tokens: Set[str] = set()
    next_id: int = 100

    def _send_response(self, status: int, body: str, content_type: str = "text/plain; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def _send_json(self, status: int, data: dict):
        body = json.dumps(data)
        self._send_response(status, body, content_type="application/json; charset=utf-8")

    def _read_json_body(self) -> Optional[dict]:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return None
        body_bytes = self.rfile.read(content_length)
        try:
            return json.loads(body_bytes.decode("utf-8"))
        except Exception:
            return None

    def _is_authenticated(self) -> bool:
        # Check Cookie header: token=...
        cookie_header = self.headers.get("Cookie", "")
        for part in cookie_header.split(";"):
            part = part.strip()
            if part.startswith("token="):
                token_val = part.split("token=")[1].strip()
                if token_val in self.valid_tokens:
                    return True
        # Check Authorization header: Basic YWRtaW46cGFzc3dvcmQxMjM=
        auth_header = self.headers.get("Authorization", "")
        if auth_header == "Basic YWRtaW46cGFzc3dvcmQxMjM=":
            return True
        return False

    def do_GET(self):
        # Health check
        if self.path == "/ping":
            self._send_response(201, "Created")
            return

        # List bookings
        if self.path == "/booking" or self.path.startswith("/booking?"):
            results = [{"bookingid": bid} for bid in self.bookings.keys()]
            self._send_json(200, results)
            return

        # Single booking
        match = re.match(r"^/booking/(\d+)$", self.path)
        if match:
            booking_id = int(match.group(1))
            if booking_id in self.bookings:
                self._send_json(200, self.bookings[booking_id])
            else:
                self._send_response(404, "Not Found")
            return

        self._send_response(404, "Not Found")

    def do_POST(self):
        # Auth endpoint
        if self.path == "/auth":
            body = self._read_json_body() or {}
            if body.get("username") == "admin" and body.get("password") == "password123":
                token = uuid.uuid4().hex[:15]
                self.valid_tokens.add(token)
                self._send_json(200, {"token": token})
            else:
                self._send_json(200, {"reason": "Bad credentials"})
            return

        # Create booking
        if self.path == "/booking":
            body = self._read_json_body()
            if not body:
                self._send_response(400, "Bad Request")
                return

            booking_id = MockBookerHandler.next_id
            MockBookerHandler.next_id += 1
            self.bookings[booking_id] = body
            self._send_json(200, {"bookingid": booking_id, "booking": body})
            return

        self._send_response(404, "Not Found")

    def do_PUT(self):
        match = re.match(r"^/booking/(\d+)$", self.path)
        if match:
            if not self._is_authenticated():
                self._send_response(403, "Forbidden")
                return

            booking_id = int(match.group(1))
            if booking_id not in self.bookings:
                self._send_response(404, "Not Found")
                return

            body = self._read_json_body()
            if not body:
                self._send_response(400, "Bad Request")
                return

            self.bookings[booking_id] = body
            self._send_json(200, body)
            return

        self._send_response(404, "Not Found")

    def do_PATCH(self):
        match = re.match(r"^/booking/(\d+)$", self.path)
        if match:
            if not self._is_authenticated():
                self._send_response(403, "Forbidden")
                return

            booking_id = int(match.group(1))
            if booking_id not in self.bookings:
                self._send_response(404, "Not Found")
                return

            body = self._read_json_body()
            if not body:
                self._send_response(400, "Bad Request")
                return

            current = self.bookings[booking_id]
            current.update(body)
            self._send_json(200, current)
            return

        self._send_response(404, "Not Found")

    def do_DELETE(self):
        match = re.match(r"^/booking/(\d+)$", self.path)
        if match:
            if not self._is_authenticated():
                self._send_response(403, "Forbidden")
                return

            booking_id = int(match.group(1))
            if booking_id not in self.bookings:
                self._send_response(405, "Method Not Allowed")
                return

            del self.bookings[booking_id]
            self._send_response(201, "Created")
            return

        self._send_response(404, "Not Found")

    def log_message(self, format, *args):
        # Suppress default noisy std output from BaseHTTPRequestHandler
        pass


class MockBookerServer:
    """Manager for running the MockBookerHandler in background thread."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8001):
        self.host = host
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None

    def start(self):
        self.server = HTTPServer((self.host, self.port), MockBookerHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        logger.info(f"Mock server running at http://{self.host}:{self.port}")

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("Mock server stopped.")


_global_mock_server: Optional[MockBookerServer] = None


def start_mock_server(host: str = "127.0.0.1", port: int = 8001) -> MockBookerServer:
    global _global_mock_server
    if _global_mock_server is None:
        _global_mock_server = MockBookerServer(host=host, port=port)
        _global_mock_server.start()
    return _global_mock_server


def stop_mock_server():
    global _global_mock_server
    if _global_mock_server:
        _global_mock_server.stop()
        _global_mock_server = None


if __name__ == "__main__":
    import time
    server = start_mock_server()
    print("Local Mock Restful-Booker server started on http://127.0.0.1:8001. Press Ctrl+C to terminate.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_mock_server()
        print("\nMock server stopped.")
