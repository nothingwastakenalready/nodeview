from datetime import datetime, timezone

from raffael.checks import CheckResult
from raffael.config import Service
from raffael.engine import apply_error, apply_result, initial_state

NOW = datetime(2026, 9, 11, 3, 45, tzinfo=timezone.utc)


def service(**overrides):
    values = {
        "name": "api",
        "url": "https://example.com",
        "interval": 30.0,
        "failure_threshold": 2,
        "success_threshold": 1,
    }
    values.update(overrides)
    return Service(**values)


def up_result(latency=12):
    return CheckResult("api", "https://example.com", "up", latency, 200)


def down_result(error="timeout"):
    return CheckResult("api", "https://example.com", "down", None, None, error)


def test_initial_state_is_pending():
    state = initial_state(service())

    assert state.status == "pending"
    assert state.last_checked is None
    assert state.consecutive_successes == 0
    assert state.consecutive_failures == 0


def test_first_success_becomes_up():
    svc = service()
    state = apply_result(initial_state(svc), up_result(), svc, NOW)

    assert state.status == "up"
    assert state.latency_ms == 12
    assert state.http_status == 200
    assert state.consecutive_successes == 1
    assert state.consecutive_failures == 0
    assert state.last_checked == NOW


def test_first_failure_is_warning_before_threshold():
    svc = service(failure_threshold=2)
    state = apply_result(initial_state(svc), down_result(), svc, NOW)

    assert state.status == "warning"
    assert state.consecutive_failures == 1
    assert state.error == "timeout"


def test_second_failure_becomes_critical():
    svc = service(failure_threshold=2)
    first = apply_result(initial_state(svc), down_result(), svc, NOW)
    second = apply_result(first, down_result("still down"), svc, NOW)

    assert second.status == "critical"
    assert second.consecutive_failures == 2
    assert second.consecutive_successes == 0


def test_success_resets_failure_counter():
    svc = service(failure_threshold=3)
    failed = apply_result(initial_state(svc), down_result(), svc, NOW)
    recovered = apply_result(failed, up_result(), svc, NOW)

    assert recovered.status == "up"
    assert recovered.consecutive_failures == 0
    assert recovered.consecutive_successes == 1


def test_success_threshold_delays_recovery_from_critical():
    svc = service(failure_threshold=1, success_threshold=2)
    critical = apply_result(initial_state(svc), down_result(), svc, NOW)
    first_success = apply_result(critical, up_result(), svc, NOW)
    second_success = apply_result(first_success, up_result(), svc, NOW)

    assert critical.status == "critical"
    assert first_success.status == "critical"
    assert first_success.consecutive_successes == 1
    assert second_success.status == "up"
    assert second_success.consecutive_successes == 2


def test_engine_exception_becomes_unknown():
    svc = service()
    state = apply_error(initial_state(svc), svc, RuntimeError("boom"), NOW)

    assert state.status == "unknown"
    assert state.error == "boom"
    assert state.last_checked == NOW
