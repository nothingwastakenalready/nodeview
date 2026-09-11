from dataclasses import dataclass, replace
from datetime import datetime

from .checks import CheckResult
from .config import Service


@dataclass(frozen=True)
class ServiceState:
    name: str
    status: str = "pending"
    latency_ms: int | None = None
    http_status: int | None = None
    error: str | None = None
    last_checked: datetime | None = None
    consecutive_successes: int = 0
    consecutive_failures: int = 0


def initial_state(service: Service) -> ServiceState:
    return ServiceState(name=service.name)


def apply_result(
    previous: ServiceState,
    result: CheckResult,
    service: Service,
    checked_at: datetime,
) -> ServiceState:
    if result.status == "up":
        successes = previous.consecutive_successes + 1
        status = "up"
        if previous.status in {"warning", "critical", "unknown"} and successes < service.success_threshold:
            status = previous.status
        return ServiceState(
            name=service.name,
            status=status,
            latency_ms=result.latency_ms,
            http_status=result.http_status,
            error=None,
            last_checked=checked_at,
            consecutive_successes=successes,
            consecutive_failures=0,
        )

    failures = previous.consecutive_failures + 1
    return ServiceState(
        name=service.name,
        status="critical" if failures >= service.failure_threshold else "warning",
        latency_ms=result.latency_ms,
        http_status=result.http_status,
        error=result.error,
        last_checked=checked_at,
        consecutive_successes=0,
        consecutive_failures=failures,
    )


def apply_error(
    previous: ServiceState,
    service: Service,
    error: Exception,
    checked_at: datetime,
) -> ServiceState:
    return replace(
        previous,
        name=service.name,
        status="unknown",
        error=str(error),
        last_checked=checked_at,
        consecutive_successes=0,
        consecutive_failures=0,
    )
