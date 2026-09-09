import socket
from dataclasses import dataclass
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import Service


@dataclass(frozen=True)
class CheckResult:
    name: str
    url: str
    status: str
    latency_ms: int | None
    http_status: int | None
    error: str | None = None
    kind: str = "http"


def check_http(service: Service) -> CheckResult:
    if not service.url:
        raise ValueError("http check needs a url")

    started = perf_counter()
    request = Request(service.url, headers={"User-Agent": "nodeview/0.1"})

    try:
        with urlopen(request, timeout=service.timeout) as response:
            latency = round((perf_counter() - started) * 1000)
            code = response.status
            return CheckResult(
                name=service.name,
                url=service.url,
                status="up" if 200 <= code < 400 else "down",
                latency_ms=latency,
                http_status=code,
            )
    except HTTPError as exc:
        latency = round((perf_counter() - started) * 1000)
        return CheckResult(
            name=service.name,
            url=service.url,
            status="down",
            latency_ms=latency,
            http_status=exc.code,
            error=str(exc.reason),
        )
    except (URLError, TimeoutError, OSError) as exc:
        return CheckResult(
            name=service.name,
            url=service.url,
            status="down",
            latency_ms=None,
            http_status=None,
            error=str(getattr(exc, "reason", exc)),
        )


def check_tcp(service: Service) -> CheckResult:
    if not service.host or service.port is None:
        raise ValueError("tcp check needs a host and port")

    target = f"{service.host}:{service.port}"
    started = perf_counter()

    try:
        with socket.create_connection((service.host, service.port), timeout=service.timeout):
            latency = round((perf_counter() - started) * 1000)
            return CheckResult(
                name=service.name,
                url=target,
                status="up",
                latency_ms=latency,
                http_status=None,
                kind="tcp",
            )
    except (TimeoutError, OSError) as exc:
        return CheckResult(
            name=service.name,
            url=target,
            status="down",
            latency_ms=None,
            http_status=None,
            error=str(exc),
            kind="tcp",
        )
