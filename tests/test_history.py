from datetime import datetime, timedelta, timezone

from raffael.engine import ServiceState
from raffael.history import SqlAlchemyHistoryStore


def state(name: str, checked_at: datetime, latency_ms: int | None = 12) -> ServiceState:
    return ServiceState(
        name=name,
        status="up",
        latency_ms=latency_ms,
        http_status=200,
        last_checked=checked_at,
        consecutive_successes=1,
    )


def test_measurements_survive_a_new_store_instance(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'raffael.db'}"
    checked_at = datetime(2026, 9, 12, 8, 30, tzinfo=timezone.utc)

    first = SqlAlchemyHistoryStore(database_url)
    first.initialize()
    first.record(state("api", checked_at))
    first.close()

    reopened = SqlAlchemyHistoryStore(database_url)
    reopened.initialize()
    measurements = reopened.history("api")

    assert len(measurements) == 1
    assert measurements[0].service_name == "api"
    assert measurements[0].status == "up"
    assert measurements[0].latency_ms == 12
    assert measurements[0].checked_at == checked_at


def test_history_filters_by_service_and_utc_time_range(tmp_path):
    store = SqlAlchemyHistoryStore(f"sqlite:///{tmp_path / 'raffael.db'}")
    store.initialize()
    base = datetime(2026, 9, 12, 9, 0, tzinfo=timezone.utc)
    store.record(state("api", base))
    store.record(state("api", base + timedelta(minutes=5), latency_ms=18))
    store.record(state("dns", base + timedelta(minutes=5), latency_ms=3))

    measurements = store.history(
        "api",
        start=base + timedelta(minutes=1),
        end=base + timedelta(minutes=10),
    )

    assert [item.latency_ms for item in measurements] == [18]


def test_history_rejects_naive_timestamps(tmp_path):
    store = SqlAlchemyHistoryStore(f"sqlite:///{tmp_path / 'raffael.db'}")
    store.initialize()

    try:
        store.record(state("api", datetime(2026, 9, 12, 9, 0)))
    except ValueError as exc:
        assert str(exc) == "measurement timestamps must include a timezone"
    else:
        raise AssertionError("naive timestamp was accepted")


def test_history_limit_returns_the_latest_measurements_in_time_order(tmp_path):
    store = SqlAlchemyHistoryStore(f"sqlite:///{tmp_path / 'raffael.db'}")
    store.initialize()
    base = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)
    store.record(state("api", base, latency_ms=5))
    store.record(state("api", base + timedelta(minutes=1), latency_ms=6))
    store.record(state("api", base + timedelta(minutes=2), latency_ms=7))

    measurements = store.history("api", limit=2)

    assert [item.latency_ms for item in measurements] == [6, 7]
