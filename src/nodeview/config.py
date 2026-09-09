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

        if kind == "http":
            if not item.get("url"):
                raise ValueError("http services need a url")
            services.append(
                Service(name=str(item["name"]), url=str(item["url"]), timeout=timeout, type="http")
            )
        elif kind == "tcp":
            if not item.get("host") or item.get("port") is None:
                raise ValueError("tcp services need a host and port")
            services.append(
                Service(
                    name=str(item["name"]),
                    timeout=timeout,
                    type="tcp",
                    host=str(item["host"]),
                    port=int(item["port"]),
                )
            )
        else:
            raise ValueError(f"don't know how to check {kind}")

    return services
