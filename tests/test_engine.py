import asyncio
import threading
import time

from nodeview.checks import CheckResult
from nodeview.config import Service
from nodeview.engine import MonitoringEngine


def make_service(name="api", **overrides):
    values = {
        "name": name,
        "url": "https://example.com",
        "interval": 0.02,
        "failure_threshold": 2,
        "success_threshold": 1,
    }
    values.update(overrides)
    return Service(**values)


def healthy(service: Service) -> CheckResult:
    return CheckResult(service.name, service.url or "", "up", 7, 200)


def test_engine_starts_with_pending_states():
    engine = MonitoringEngine([make_service("one"), make_service("two")], checker=healthy)

    states = engine.states()

    assert set(states) == {"one", "two"}
    assert states["one"].status == "pending"
    assert states["two"].status == "pending"


def test_run_once_updates_state():
    async def scenario():
        service = make_service()
        engine = MonitoringEngine([service], checker=healthy)

        await engine.run_once(service)

        assert engine.states()["api"].status == "up"
        assert engine.states()["api"].latency_ms == 7

    asyncio.run(scenario())


def test_checker_exception_becomes_unknown_without_escaping():
    def broken(service: Service) -> CheckResult:
        raise RuntimeError("checker exploded")

    async def scenario():
        service = make_service()
        engine = MonitoringEngine([service], checker=broken)

        await engine.run_once(service)

        state = engine.states()["api"]
        assert state.status == "unknown"
        assert state.error == "checker exploded"

    asyncio.run(scenario())


def test_start_runs_checks_automatically_and_is_idempotent():
    calls = 0
    lock = threading.Lock()

    def checker(service: Service) -> CheckResult:
        nonlocal calls
        with lock:
            calls += 1
        return healthy(service)

    async def scenario():
        service = make_service(interval=0.02)
        engine = MonitoringEngine([service], checker=checker)

        await engine.start()
        await engine.start()
        await asyncio.sleep(0.055)
        await engine.stop()

        assert engine.states()["api"].status == "up"
        assert 2 <= calls <= 4

    asyncio.run(scenario())


def test_scheduler_respects_max_concurrency():
    active = 0
    max_active = 0
    lock = threading.Lock()

    def slow_checker(service: Service) -> CheckResult:
        nonlocal active, max_active
        with lock:
            active += 1
            max_active = max(max_active, active)
        time.sleep(0.03)
        with lock:
            active -= 1
        return healthy(service)

    async def scenario():
        services = [make_service("one"), make_service("two"), make_service("three")]
        engine = MonitoringEngine(services, checker=slow_checker, max_concurrency=1)

        await engine.start()
        await asyncio.sleep(0.12)
        await engine.stop()

        assert max_active == 1
        assert all(state.status == "up" for state in engine.states().values())

    asyncio.run(scenario())


def test_stop_is_safe_before_or_after_start():
    async def scenario():
        engine = MonitoringEngine([make_service()], checker=healthy)
        await engine.stop()
        await engine.start()
        await asyncio.sleep(0.01)
        await engine.stop()
        await engine.stop()

    asyncio.run(scenario())
