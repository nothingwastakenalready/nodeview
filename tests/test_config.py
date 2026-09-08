from pathlib import Path

import pytest

from nodeview.config import load_services


def test_loads_services_from_yaml(tmp_path: Path):
    config = tmp_path / "services.yaml"
    config.write_text(
        """services:
  - name: one
    url: https://example.com
  - name: two
    url: https://example.org
    timeout: 4
"""
    )

    services = load_services(config)

    assert [(s.name, s.url, s.timeout) for s in services] == [
        ("one", "https://example.com", 2.0),
        ("two", "https://example.org", 4.0),
    ]


def test_rejects_config_without_services(tmp_path: Path):
    config = tmp_path / "services.yaml"
    config.write_text("whatever: true\n")

    with pytest.raises(ValueError, match="services"):
        load_services(config)
