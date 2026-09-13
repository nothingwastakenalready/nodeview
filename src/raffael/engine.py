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
    check_id: int | None = None
    workspace_id: int | None = None
    device_id: int | None = None
    details: dict | None = None


def initial_state(service: Service) -> ServiceState:
    return ServiceState(
        name=service.name,
        check_id=service.check_id,
        workspace_id=service.workspace_id,
        device_id=service.device_id,
    )


def service_key(service: Service) -> str:
    return str(service.check_id) if service.check_id is not None else service.name


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
            check_id=service.check_id,
            workspace_id=service.workspace_id,
            device_id=service.device_id,
            details=result.details,
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
        check_id=service.check_id,
        workspace_id=service.workspace_id,
        device_id=service.device_id,
        details=result.details,
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
        check_id=service.check_id,
        workspace_id=service.workspace_id,
        device_id=service.device_id,
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
        self._services: dict[str, Service] = {service_key(service): service for service in services}
        self._checker = checker
        self._history = history
        self._states = {service_key(service): initial_state(service) for service in services}
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._tasks: dict[str, asyncio.Task[None]] = {}

    def states(self) -> dict[str, ServiceState]:
        return dict(self._states)

    async def run_once(self, service: Service) -> ServiceState:
        key = service_key(service)
        previous = self._states[key]
        checked_at = datetime.now(timezone.utc)

        try:
            async with self._semaphore:
                result = await asyncio.to_thread(self._checker, service)
        except Exception as exc:
            state = apply_error(previous, service, exc, checked_at)
        else:
            state = apply_result(previous, result, service, checked_at)

        self._states[key] = state
        if self._history is not None:
            await asyncio.to_thread(self._history.record, state)
        return state

    async def run_key_once(self, key: str) -> ServiceState:
        service = self._services.get(key)
        if service is None:
            raise KeyError(key)
        return await self.run_once(service)

    async def replace_services(self, services: list[Service]) -> None:
        was_running = bool(self._tasks)
        if was_running:
            await self.stop()
        self._services = {service_key(service): service for service in services}
        self._states = {key: self._states.get(key, initial_state(service)) for key, service in self._services.items()}
        if was_running:
            await self.start()

    async def start(self) -> None:
        if self._tasks:
            return

        self._tasks = {
            key: asyncio.create_task(self._run_service(key, service), name=f"raffael:{key}")
            for key, service in self._services.items()
        }

    async def stop(self) -> None:
        if not self._tasks:
            return

        tasks = list(self._tasks.values())
        self._tasks = {}
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _run_service(self, key: str, service: Service) -> None:
        while True:
            current = self._services.get(key)
            if current is None:
                return
            service = current
            await self.run_once(service)
            await asyncio.sleep(service.interval)
