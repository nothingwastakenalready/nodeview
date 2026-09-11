import os
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Callable

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, model_validator

from .checks import CheckResult, check_service
from .config import Service, load_services
from .engine import MonitoringEngine

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
) -> FastAPI:
    path = Path(config_path or os.environ.get("NODEVIEW_CONFIG", "/config/services.yaml"))
    runtime_engine = engine
    ui_root = Path(ui_path or os.environ.get("NODEVIEW_UI", "/app/web/dist"))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        nonlocal runtime_engine
        if runtime_engine is None and monitor:
            runtime_engine = MonitoringEngine(load_services(path), checker=checker)
        app.state.engine = runtime_engine
        if runtime_engine is not None:
            await runtime_engine.start()
        try:
            yield
        finally:
            if runtime_engine is not None:
                await runtime_engine.stop()

    app = FastAPI(title="nodeview", version="0.3.0", lifespan=lifespan)

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
