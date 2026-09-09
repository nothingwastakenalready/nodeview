from nodeview.checks import CheckResult
from nodeview.cli import format_result


def test_formats_http_up_result():
    result = CheckResult("dns", "http://example", "up", 14, 200, kind="http")
    assert format_result(result) == "dns  HTTP  UP  14ms  200"


def test_formats_tcp_up_result():
    result = CheckResult("ssh", "127.0.0.1:22", "up", 8, None, kind="tcp")
    assert format_result(result) == "ssh  TCP  UP  8ms"


def test_formats_down_result_with_error():
    result = CheckResult(
        "home", "http://example", "down", None, None, "connection refused", kind="http"
    )
    assert format_result(result) == "home  HTTP  DOWN  connection refused"
