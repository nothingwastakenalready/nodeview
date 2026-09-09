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
    assert services[1].name == "ssh-ish"
    assert services[1].type == "tcp"
    assert services[1].host == "127.0.0.1"
    assert services[1].port == 22
    assert services[1].timeout == 4.0


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
