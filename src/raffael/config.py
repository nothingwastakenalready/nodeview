from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Service:
    name: str
    url: str | None = None
    timeout: float = 2.0
    type: str = "http"
    host: str | None = None
    port: int | None = None
    interval: float = 30.0
    failure_threshold: int = 2
    success_threshold: int = 1
    check_id: int | None = None
    workspace_id: int | None = None
    device_id: int | None = None
    probe_ports: tuple[int, ...] = (22, 53, 80, 443, 445, 548, 8123, 8006, 8080, 9100)


def load_services(path: str | Path) -> list[Service]:
    data = yaml.safe_load(Path(path).read_text())

    if not isinstance(data, dict) or not isinstance(data.get("services"), list):
        raise ValueError("config needs a services list")

    services: list[Service] = []
    for item in data["services"]:
        if not isinstance(item, dict) or not item.get("name"):
            raise ValueError("every service needs a name")

        kind = str(item.get("type", "http")).lower()
        timeout = float(item.get("timeout", 2.0))
        interval = float(item.get("interval", 30.0))
        failure_threshold = int(item.get("failure_threshold", 2))
        success_threshold = int(item.get("success_threshold", 1))

        if interval <= 0:
            raise ValueError("interval must be greater than zero")
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be at least one")
        if success_threshold < 1:
            raise ValueError("success_threshold must be at least one")

        common = {
            "name": str(item["name"]),
            "timeout": timeout,
            "type": kind,
            "interval": interval,
            "failure_threshold": failure_threshold,
            "success_threshold": success_threshold,
        }

        if kind == "http":
            if not item.get("url"):
                raise ValueError("http services need a url")
            services.append(Service(url=str(item["url"]), **common))
        elif kind == "tcp":
            if not item.get("host") or item.get("port") is None:
                raise ValueError("tcp services need a host and port")
            services.append(
                Service(host=str(item["host"]), port=int(item["port"]), **common)
            )
        else:
            raise ValueError(f"don't know how to check {kind}")

    return services
