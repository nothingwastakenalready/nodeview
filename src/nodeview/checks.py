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
    request = Request(service.url, headers={"User-Agent": "nodeview/0.2"})

    try:
        with urlopen(request, timeout=service.timeout) as response:
            latency = round((perf_counter() - started) * 1000)
            code = response.status
            return CheckResult(service.name, service.url, "up" if 200 <= code < 400 else "down", latency, code)
    except HTTPError as exc:
        latency = round((perf_counter() - started) * 1000)
        return CheckResult(service.name, service.url, "down", latency, exc.code, str(exc.reason))
    except (URLError, TimeoutError, OSError) as exc:
        return CheckResult(service.name, service.url, "down", None, None, str(getattr(exc, "reason", exc)))


def check_tcp(service: Service) -> CheckResult:
    if not service.host or service.port is None:
        raise ValueError("tcp check needs a host and port")

    target = f"{service.host}:{service.port}"
    started = perf_counter()
    try:
        with socket.create_connection((service.host, service.port), timeout=service.timeout):
            latency = round((perf_counter() - started) * 1000)
            return CheckResult(service.name, target, "up", latency, None, kind="tcp")
    except (TimeoutError, OSError) as exc:
        return CheckResult(service.name, target, "down", None, None, str(exc), kind="tcp")


def check_service(service: Service) -> CheckResult:
    if service.type == "tcp":
        return check_tcp(service)
    if service.type == "http":
        return check_http(service)
    raise ValueError(f"don't know how to check {service.type}")
