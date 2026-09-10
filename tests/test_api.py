from fastapi.testclient import TestClient

from nodeview.api import create_app
from nodeview.checks import CheckResult
from nodeview.config import Service


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
