import asyncio
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Protocol

from .checks import CheckResult, check_service
from .config import Service

Checker = Callable[[Service], CheckResult]


class HistoryRecorder(Protocol):
    def record(self, state: "ServiceState") -> None: ...


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


class MonitoringEngine:
    def __init__(
        self,
        services: list[Service],
        checker: Checker = check_service,
        max_concurrency: int = 10,
        history: HistoryRecorder | None = None,
    ) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be at least one")
        self._services = list(services)
        self._checker = checker
        self._history = history
        self._states = {service.name: initial_state(service) for service in services}
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._tasks: dict[str, asyncio.Task[None]] = {}

    def states(self) -> dict[str, ServiceState]:
        return dict(self._states)

    async def run_once(self, service: Service) -> ServiceState:
        previous = self._states[service.name]
        checked_at = datetime.now(timezone.utc)

        try:
            async with self._semaphore:
                result = await asyncio.to_thread(self._checker, service)
        except Exception as exc:
            state = apply_error(previous, service, exc, checked_at)
        else:
            state = apply_result(previous, result, service, checked_at)

        self._states[service.name] = state
        if self._history is not None:
            await asyncio.to_thread(self._history.record, state)
        return state

    async def start(self) -> None:
        if self._tasks:
            return

        self._tasks = {
            service.name: asyncio.create_task(self._run_service(service), name=f"raffael:{service.name}")
            for service in self._services
        }

    async def stop(self) -> None:
        if not self._tasks:
            return

        tasks = list(self._tasks.values())
        self._tasks = {}
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _run_service(self, service: Service) -> None:
        while True:
            await self.run_once(service)
            await asyncio.sleep(service.interval)
