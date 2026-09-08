from nodeview.checks import CheckResult
from nodeview.cli import format_result


def test_formats_up_result():
    result = CheckResult("dns", "http://example", "up", 14, 200)
    assert format_result(result) == "dns  UP  14ms  200"


def test_formats_down_result_with_error():
    result = CheckResult("home", "http://example", "down", None, None, "connection refused")
    assert format_result(result) == "home  DOWN  connection refused"
