from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from nodeview.checks import check_http
from nodeview.config import Service


class Handler(BaseHTTPRequestHandler):
    status = 200

    def do_GET(self):
        self.send_response(self.status)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format, *args):
        pass


def server_with(status: int):
    Handler.status = status
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def test_200_is_up():
    server = server_with(200)
    try:
        result = check_http(Service("local", f"http://127.0.0.1:{server.server_port}"))
        assert result.status == "up"
        assert result.http_status == 200
        assert result.latency_ms is not None
        assert result.error is None
    finally:
        server.shutdown()


def test_503_answered_but_is_down():
    server = server_with(503)
    try:
        result = check_http(Service("local", f"http://127.0.0.1:{server.server_port}"))
        assert result.status == "down"
        assert result.http_status == 503
        assert result.latency_ms is not None
    finally:
        server.shutdown()


def test_connection_failure_is_down():
    result = check_http(Service("nope", "http://127.0.0.1:1", timeout=0.1))

    assert result.status == "down"
    assert result.http_status is None
    assert result.error
