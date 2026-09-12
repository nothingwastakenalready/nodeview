import asyncio
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from raffael.api import create_app
from raffael.checks import CheckResult
from raffael.config import Service
from raffael.engine import MonitoringEngine
from raffael.history import Measurement


def test_health_does_not_run_checks(tmp_path):
    config = tmp_path / "services.yaml"
    config.write_text("services: []\n")
    client = TestClient(create_app(config_path=config))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_services_returns_shared_check_results(tmp_path):
    config = tmp_path / "services.yaml"
    config.write_text("services:\n  - name: ssh\n    type: tcp\n    host: 127.0.0.1\n    port: 22\n")

    def fake_check(service: Service) -> CheckResult:
        return CheckResult(service.name, "127.0.0.1:22", "up", 7, None, kind="tcp")

    client = TestClient(create_app(config_path=config, checker=fake_check))
    response = client.get("/services")

    assert response.status_code == 200
    assert response.json() == [{
        "name": "ssh",
        "type": "tcp",
        "status": "up",
        "latency_ms": 7,
        "http_status": None,
        "error": None,
    }]


def test_check_runs_one_adhoc_http_check(tmp_path):
    config = tmp_path / "services.yaml"
    config.write_text("services: []\n")

    def fake_check(service: Service) -> CheckResult:
        return CheckResult(service.name, service.url or "", "up", 12, 200, kind="http")

    client = TestClient(create_app(config_path=config, checker=fake_check))
    response = client.post("/check", json={"name": "example", "type": "http", "url": "https://example.com", "timeout": 2})

    assert response.status_code == 200
    assert response.json()["status"] == "up"
    assert response.json()["latency_ms"] == 12


def test_state_returns_engine_snapshot(tmp_path):
    config = tmp_path / "services.yaml"
    config.write_text("services: []\n")
    service = Service(name="api", url="https://example.com")

    def fake_check(service: Service) -> CheckResult:
        return CheckResult(service.name, service.url or "", "up", 9, 200)

    engine = MonitoringEngine([service], checker=fake_check)
    asyncio.run(engine.run_once(service))

    client = TestClient(create_app(config_path=config, checker=fake_check, engine=engine))
    response = client.get("/state")

    assert response.status_code == 200
    assert response.json()[0]["name"] == "api"
    assert response.json()[0]["status"] == "up"
    assert response.json()[0]["latency_ms"] == 9
    assert response.json()[0]["last_checked"].endswith("+00:00")


def test_lifespan_starts_and_stops_injected_engine(tmp_path):
    config = tmp_path / "services.yaml"
    config.write_text("services: []\n")

    class FakeEngine:
        def __init__(self):
            self.started = False
            self.stopped = False

        async def start(self):
            self.started = True

        async def stop(self):
            self.stopped = True

        def states(self):
            return {}

    engine = FakeEngine()
    app = create_app(config_path=config, engine=engine)

    with TestClient(app) as client:
        assert engine.started is True
        assert client.get("/state").json() == []

    assert engine.stopped is True


def test_history_returns_bounded_measurements_for_a_service(tmp_path):
    config = tmp_path / "services.yaml"
    config.write_text("services: []\n")

    class FakeHistory:
        def history(self, service_name, start=None, end=None, limit=500):
            assert service_name == "api"
            assert start == datetime(2026, 9, 12, 8, 0, tzinfo=timezone.utc)
            assert end is None
            assert limit == 25
            return [
                Measurement(
                    service_name="api",
                    status="up",
                    latency_ms=9,
                    http_status=200,
                    error=None,
                    checked_at=datetime(2026, 9, 12, 8, 1, tzinfo=timezone.utc),
                )
            ]

    client = TestClient(create_app(config_path=config, history=FakeHistory()))
    response = client.get(
        "/history/api",
        params={"from": "2026-09-12T08:00:00Z", "limit": 25},
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "service_name": "api",
            "status": "up",
            "latency_ms": 9,
            "http_status": 200,
            "error": None,
            "checked_at": "2026-09-12T08:01:00+00:00",
        }
    ]


def test_history_limit_is_capped_by_validation(tmp_path):
    config = tmp_path / "services.yaml"
    config.write_text("services: []\n")
    client = TestClient(create_app(config_path=config, history=object()))

    response = client.get("/history/api", params={"limit": 1001})

    assert response.status_code == 422


def test_serves_built_ui_from_supplied_directory(tmp_path):
    config = tmp_path / "services.yaml"
    config.write_text("services: []\n")
    ui = tmp_path / "dist"
    assets = ui / "assets"
    assets.mkdir(parents=True)
    (ui / "index.html").write_text("<html><body>raffael ui</body></html>")
    (assets / "app.js").write_text("console.log('raffael')")

    client = TestClient(create_app(config_path=config, ui_path=ui))

    root = client.get("/")
    asset = client.get("/assets/app.js")

    assert root.status_code == 200
    assert "raffael ui" in root.text
    assert asset.status_code == 200
    assert "raffael" in asset.text
