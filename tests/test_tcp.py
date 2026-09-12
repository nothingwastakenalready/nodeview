import socket
from threading import Thread

from raffael.checks import check_tcp
from raffael.config import Service


def listening_socket():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)

    def accept_one():
        try:
            connection, _ = server.accept()
        except OSError:
            return
        connection.close()

    Thread(target=accept_one, daemon=True).start()
    return server


def test_open_tcp_port_is_up():
    server = listening_socket()
    try:
        result = check_tcp(
            Service(name="ssh-ish", type="tcp", host="127.0.0.1", port=server.getsockname()[1])
        )
        assert result.status == "up"
        assert result.kind == "tcp"
        assert result.latency_ms is not None
        assert result.error is None
    finally:
        server.close()


def test_closed_tcp_port_is_down():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    port = server.getsockname()[1]
    server.close()

    result = check_tcp(Service(name="closed", type="tcp", host="127.0.0.1", port=port, timeout=0.1))

    assert result.status == "down"
    assert result.kind == "tcp"
    assert result.error
