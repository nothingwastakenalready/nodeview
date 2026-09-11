from pathlib import Path

import pytest

from nodeview.config import load_services


def test_loads_http_and_tcp_services_from_yaml(tmp_path: Path):
    config = tmp_path / "services.yaml"
    config.write_text(
        """services:
  - name: one
    url: https://example.com
  - name: ssh-ish
    type: tcp
    host: 127.0.0.1
    port: 22
    timeout: 4
"""
    )

    services = load_services(config)

    assert services[0].name == "one"
    assert services[0].type == "http"
    assert services[0].url == "https://example.com"
    assert services[0].interval == 30.0
    assert services[0].failure_threshold == 2
    assert services[0].success_threshold == 1
    assert services[1].name == "ssh-ish"
    assert services[1].type == "tcp"
    assert services[1].host == "127.0.0.1"
    assert services[1].port == 22
    assert services[1].timeout == 4.0


def test_loads_custom_monitoring_values(tmp_path: Path):
    config = tmp_path / "services.yaml"
    config.write_text(
        """services:
  - name: api
    url: https://example.com
    interval: 5
    failure_threshold: 3
    success_threshold: 2
"""
    )

    service = load_services(config)[0]

    assert service.interval == 5.0
    assert service.failure_threshold == 3
    assert service.success_threshold == 2


@pytest.mark.parametrize(
    ("field", "value"),
    [("interval", 0), ("failure_threshold", 0), ("success_threshold", 0)],
)
def test_rejects_non_positive_monitoring_values(tmp_path: Path, field: str, value: int):
    config = tmp_path / "services.yaml"
    config.write_text(
        f"services:\n  - name: bad\n    url: https://example.com\n    {field}: {value}\n"
    )

    with pytest.raises(ValueError, match=field):
        load_services(config)


def test_rejects_config_without_services(tmp_path: Path):
    config = tmp_path / "services.yaml"
    config.write_text("whatever: true\n")

    with pytest.raises(ValueError, match="services"):
        load_services(config)


def test_tcp_needs_host_and_port(tmp_path: Path):
    config = tmp_path / "services.yaml"
    config.write_text("services:\n  - name: nope\n    type: tcp\n    host: localhost\n")

    with pytest.raises(ValueError, match="host and port"):
        load_services(config)
