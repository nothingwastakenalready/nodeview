import os
from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Callable

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, model_validator

from .checks import CheckResult, check_service
from .config import Service, load_services
from .engine import MonitoringEngine
from .history import HistoryStore, SqlAlchemyHistoryStore

Checker = Callable[[Service], CheckResult]


class ServiceInput(BaseModel):
    name: str
    type: str = "http"
    url: str | None = None
    host: str | None = None
    port: int | None = None
    timeout: float = 2.0

    @model_validator(mode="after")
    def validate_target(self):
        self.type = self.type.lower()
        if self.type == "http" and not self.url:
            raise ValueError("http checks need a url")
        if self.type == "tcp" and (not self.host or self.port is None):
            raise ValueError("tcp checks need a host and port")
        if self.type not in {"http", "tcp"}:
            raise ValueError(f"don't know how to check {self.type}")
        return self

    def service(self) -> Service:
        return Service(name=self.name, type=self.type, url=self.url, host=self.host, port=self.port, timeout=self.timeout)


def result_json(result: CheckResult) -> dict:
    data = asdict(result)
    data["type"] = data.pop("kind")
    data.pop("url", None)
    return data


def create_app(
    config_path: str | Path | None = None,
    checker: Checker = check_service,
    engine: MonitoringEngine | None = None,
    monitor: bool = False,
    ui_path: str | Path | None = None,
    history: HistoryStore | None = None,
    database_url: str | None = None,
) -> FastAPI:
    path = Path(config_path or os.environ.get("RAFFAEL_CONFIG", "/config/services.yaml"))
    runtime_engine = engine
    runtime_history = history
    ui_root = Path(ui_path or os.environ.get("RAFFAEL_UI", "/app/web/dist"))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        nonlocal runtime_engine, runtime_history
        owns_history = False
        if runtime_history is None and monitor:
            runtime_history = SqlAlchemyHistoryStore(
                database_url
                or os.environ.get("RAFFAEL_DATABASE_URL", "sqlite:////data/raffael.db")
            )
            runtime_history.initialize()
            owns_history = True
        if runtime_engine is None and monitor:
            runtime_engine = MonitoringEngine(
                load_services(path), checker=checker, history=runtime_history
            )
        app.state.engine = runtime_engine
        app.state.history = runtime_history
        if runtime_engine is not None:
            await runtime_engine.start()
        try:
            yield
        finally:
            if runtime_engine is not None:
                await runtime_engine.stop()
            if owns_history and runtime_history is not None:
                runtime_history.close()

    app = FastAPI(title="raffael", version="0.4.0", lifespan=lifespan)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/services")
    def services():
        return [result_json(checker(service)) for service in load_services(path)]

    @app.post("/check")
    def check(service: ServiceInput):
        return result_json(checker(service.service()))

    @app.get("/state")
    def state():
        if runtime_engine is None:
            return []
        return [asdict(item) for item in runtime_engine.states().values()]

    @app.get("/history/{service_name}")
    def service_history(
        service_name: str,
        start: datetime | None = Query(None, alias="from"),
        end: datetime | None = Query(None, alias="to"),
        limit: int = Query(500, ge=1, le=1000),
    ):
        if runtime_history is None:
            return []
        return [
            asdict(item)
            for item in runtime_history.history(
                service_name, start=start, end=end, limit=limit
            )
        ]

    assets = ui_root / "assets"
    index = ui_root / "index.html"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    if index.is_file():
        @app.get("/", include_in_schema=False)
        def ui_index():
            return FileResponse(index)

    return app


app = create_app(monitor=True)
