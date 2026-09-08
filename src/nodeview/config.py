from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Service:
    name: str
    url: str
    timeout: float = 2.0


def load_services(path: str | Path) -> list[Service]:
    data = yaml.safe_load(Path(path).read_text())

    if not isinstance(data, dict) or not isinstance(data.get("services"), list):
        raise ValueError("config needs a services list")

    services: list[Service] = []
    for item in data["services"]:
        if not isinstance(item, dict) or not item.get("name") or not item.get("url"):
            raise ValueError("every service needs a name and url")

        services.append(
            Service(
                name=str(item["name"]),
                url=str(item["url"]),
                timeout=float(item.get("timeout", 2.0)),
            )
        )

    return services
