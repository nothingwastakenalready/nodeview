import os
from dataclasses import asdict
from pathlib import Path
from typing import Callable

from fastapi import FastAPI
from pydantic import BaseModel, model_validator

from .checks import CheckResult, check_service
from .config import Service, load_services

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


def create_app(config_path: str | Path | None = None, checker: Checker = check_service) -> FastAPI:
    path = Path(config_path or os.environ.get("NODEVIEW_CONFIG", "/config/services.yaml"))
    app = FastAPI(title="nodeview", version="0.2.0")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/services")
    def services():
        return [result_json(checker(service)) for service in load_services(path)]

    @app.post("/check")
    def check(service: ServiceInput):
        return result_json(checker(service.service()))

    return app


app = create_app()
