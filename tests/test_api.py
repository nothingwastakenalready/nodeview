import asyncio

from fastapi.testclient import TestClient

from nodeview.api import create_app
from nodeview.checks import CheckResult
from nodeview.config import Service
from nodeview.engine import MonitoringEngine


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


def test_serves_built_ui_from_supplied_directory(tmp_path):
    config = tmp_path / "services.yaml"
    config.write_text("services: []\n")
    ui = tmp_path / "dist"
    assets = ui / "assets"
    assets.mkdir(parents=True)
    (ui / "index.html").write_text("<html><body>nodeview ui</body></html>")
    (assets / "app.js").write_text("console.log('nodeview')")

    client = TestClient(create_app(config_path=config, ui_path=ui))

    root = client.get("/")
    asset = client.get("/assets/app.js")

    assert root.status_code == 200
    assert "nodeview ui" in root.text
    assert asset.status_code == 200
    assert "nodeview" in asset.text
