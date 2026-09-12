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


def test_auth_lifecycle_uses_server_side_session_and_csrf(tmp_path):
    config = tmp_path / "services.yaml"
    config.write_text("services: []\n")
    with TestClient(create_app(config_path=config, database_url=f"sqlite:///{tmp_path / 'auth.db'}")) as client:
        registered = client.post("/auth/register", json={"email": " User@example.com ", "password": "a sufficiently long password"})
        assert registered.status_code == 201
        assert registered.json()["email"] == "user@example.com"
        assert registered.json()["workspaces"][0]["role"] == "owner"
        assert "HttpOnly" in registered.headers["set-cookie"]
        assert client.get("/auth/me").json()["workspaces"][0]["name"] == "default"

        without_csrf = client.post("/auth/logout")
        assert without_csrf.status_code == 403
        csrf = client.cookies.get("raffael_csrf")
        logged_out = client.post("/auth/logout", headers={"X-CSRF-Token": csrf})
        assert logged_out.status_code == 204
        assert client.get("/auth/me").status_code == 401


def test_auth_rejects_duplicate_registration(tmp_path):
    config = tmp_path / "services.yaml"
    config.write_text("services: []\n")
    with TestClient(create_app(config_path=config, database_url=f"sqlite:///{tmp_path / 'auth.db'}")) as client:
        payload = {"email": "user@example.com", "password": "a sufficiently long password"}
        assert client.post("/auth/register", json=payload).status_code == 201
        assert client.post("/auth/register", json=payload).status_code == 400


def test_household_devices_use_workspace_scope_and_connector_catalog(tmp_path):
    config = tmp_path / "services.yaml"
    config.write_text("services: []\n")
    with TestClient(create_app(config_path=config, database_url=f"sqlite:///{tmp_path / 'auth.db'}")) as client:
        assert client.get("/integrations/catalog").status_code == 401
        registered = client.post(
            "/auth/register",
            json={"email": "owner@example.com", "password": "a sufficiently long password"},
        )
        assert registered.status_code == 201
        catalog = client.get("/integrations/catalog")
        assert catalog.status_code == 200
        assert {item["key"] for item in catalog.json()} >= {"unifi", "hue", "proxmox", "windows-agent", "macos-agent"}

        csrf = client.cookies.get("raffael_csrf")
        added = client.post(
            "/household/devices",
            headers={"X-CSRF-Token": csrf},
            json={
                "connector": "proxmox",
                "name": "pve living room",
                "endpoint": "https://pve.local:8006",
                "credential_ref": "keychain://raffael/pve-living-room",
                "metadata": {"node": "pve"},
            },
        )
        assert added.status_code == 201
        assert added.json()["status"] == "pending"
        assert added.json()["credential_ref"] == "keychain://raffael/pve-living-room"
        assert client.get("/household/devices").json()[0]["name"] == "pve living room"


def test_household_devices_reject_unknown_connector(tmp_path):
    config = tmp_path / "services.yaml"
    config.write_text("services: []\n")
    with TestClient(create_app(config_path=config, database_url=f"sqlite:///{tmp_path / 'auth.db'}")) as client:
        client.post("/auth/register", json={"email": "owner@example.com", "password": "a sufficiently long password"})
        csrf = client.cookies.get("raffael_csrf")
        response = client.post(
            "/household/devices",
            headers={"X-CSRF-Token": csrf},
            json={"connector": "ssh-root", "name": "unsafe"},
        )
        assert response.status_code == 400


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
