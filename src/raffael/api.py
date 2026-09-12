import os
from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Callable

from fastapi import Cookie, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

from .checks import CheckResult, check_service
from .config import Service, load_services
from .engine import MonitoringEngine
from .history import HistoryStore, SqlAlchemyHistoryStore
from .auth import AuthStore, CSRF_COOKIE, SESSION_COOKIE
from .client_sources import ClientSourceError, ImportedClient, fetch_api_clients, fetch_snmp_clients
from .email_templates import confirmation_email, newsletter_confirmation_email, password_reset_email
from .households import DeviceStore, connector_catalog
from .connectors import discover_network
from .mailer import SmtpMailer
from .unifi import fetch_unifi_clients

Checker = Callable[[Service], CheckResult]
ClientSourceLoader = Callable[[], list[ImportedClient]]


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


class AccountInput(BaseModel):
    email: str
    password: str
    workspace_name: str = "default"
    newsletter_opt_in: bool = False


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    token: str
    password: str


class DeviceInput(BaseModel):
    connector: str
    name: str
    endpoint: str | None = None
    credential_ref: str | None = None
    metadata: dict = Field(default_factory=dict)
    parent_id: int | None = None


class ClientInput(BaseModel):
    name: str
    endpoint: str | None = None
    mac_address: str | None = None
    connector: str = "icmp"
    parent_id: int | None = None
    metadata: dict = Field(default_factory=dict)


class DiscoveryInput(BaseModel):
    network: str = Field(pattern=r"^\d{1,3}(?:\.\d{1,3}){3}/\d{1,2}$")
    workers: int = Field(default=32, ge=1, le=128)


class DiscoveryAdoptInput(BaseModel):
    address: str
    hostname: str | None = None
    open_ports: list[int] = Field(default_factory=list)
    parent_id: int | None = None


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
    mailer: SmtpMailer | None = None,
    client_source_loaders: dict[str, ClientSourceLoader] | None = None,
    unifi_client_loader: ClientSourceLoader | None = None,
) -> FastAPI:
    path = Path(config_path or os.environ.get("RAFFAEL_CONFIG", "/config/services.yaml"))
    runtime_engine = engine
    runtime_history = history
    runtime_auth: AuthStore | None = None
    runtime_devices: DeviceStore | None = None
    runtime_mailer = mailer or SmtpMailer()
    runtime_client_source_loaders = {
        "unifi": unifi_client_loader or fetch_unifi_clients,
        "api": fetch_api_clients,
        "snmp": fetch_snmp_clients,
    }
    if client_source_loaders:
        runtime_client_source_loaders.update(client_source_loaders)
    ui_root = Path(ui_path or os.environ.get("RAFFAEL_UI", "/app/web/dist"))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        nonlocal runtime_engine, runtime_history, runtime_auth, runtime_devices
        owns_history = False
        if runtime_history is None and monitor:
            runtime_history = SqlAlchemyHistoryStore(
                database_url
                or os.environ.get("RAFFAEL_DATABASE_URL", "sqlite:////data/raffael.db")
            )
            runtime_history.initialize()
            owns_history = True
        if runtime_auth is None and (database_url or monitor):
            runtime_auth = AuthStore(database_url or os.environ.get("RAFFAEL_DATABASE_URL", "sqlite:////data/raffael.db"))
            runtime_auth.initialize()
        if runtime_auth is not None:
            runtime_devices = DeviceStore(runtime_auth.engine)
        if runtime_engine is None and monitor:
            runtime_engine = MonitoringEngine(
                load_services(path), checker=checker, history=runtime_history
            )
        app.state.engine = runtime_engine
        app.state.history = runtime_history
        app.state.auth = runtime_auth
        app.state.devices = runtime_devices
        if runtime_engine is not None:
            await runtime_engine.start()
        try:
            yield
        finally:
            if runtime_engine is not None:
                await runtime_engine.stop()
            if owns_history and runtime_history is not None:
                runtime_history.close()
            if runtime_auth is not None:
                runtime_auth.close()

    app = FastAPI(title="raffael", version="0.4.0", lifespan=lifespan)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    def require_authenticated_user(session_token: str | None) -> object:
        if runtime_auth is None:
            return None
        user = runtime_auth.user_for_token(session_token)
        if user is None:
            raise HTTPException(status_code=401, detail="authentication required")
        return user

    def current_workspace(session_token: str | None) -> tuple[object, int]:
        user = require_authenticated_user(session_token)
        if runtime_auth is None or user is None:
            raise HTTPException(status_code=503, detail="authentication storage unavailable")
        memberships = runtime_auth.memberships(user.id)
        if not memberships:
            raise HTTPException(status_code=403, detail="workspace membership required")
        return user, int(memberships[0]["id"])

    def require_csrf(session_token: str | None, csrf: str | None) -> None:
        if runtime_auth is None or not session_token or not runtime_auth.csrf_valid(session_token, csrf):
            raise HTTPException(status_code=403, detail="csrf validation failed")

    @app.post("/auth/register", status_code=201)
    def register(account: AccountInput, response: Response):
        if runtime_auth is None:
            raise HTTPException(status_code=503, detail="authentication storage unavailable")
        try:
            user = runtime_auth.register(account.email, account.password, account.workspace_name)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        public_url = os.environ.get("RAFFAEL_PUBLIC_URL", "http://127.0.0.1:8080").rstrip("/")
        verification_token = runtime_auth.issue_token(user.id, "email_verification")
        email_logo_url = f"{public_url}/assets/02-logo-varianten/logo-liquid-silver-weiss-transparent.png"
        verification_message = confirmation_email(recipient=user.email, confirmation_url=f"{public_url}/auth/confirm?token={verification_token}", logo_url=email_logo_url)
        if runtime_mailer.enabled:
            runtime_mailer.send(user.email, verification_message)
        if account.newsletter_opt_in:
            newsletter_token = runtime_auth.start_newsletter(user.id, "i want to receive the raffael newsletter")
            newsletter_message = newsletter_confirmation_email(recipient=user.email, confirmation_url=f"{public_url}/auth/newsletter/confirm?token={newsletter_token}", logo_url=email_logo_url)
            if runtime_mailer.enabled:
                runtime_mailer.send(user.email, newsletter_message)
        token, csrf = runtime_auth.create_session(user.id)
        response.set_cookie(SESSION_COOKIE, token, httponly=True, secure=os.environ.get("RAFFAEL_SECURE_COOKIES", "0") == "1", samesite="lax", max_age=7 * 24 * 3600)
        response.set_cookie(CSRF_COOKIE, csrf, httponly=False, secure=os.environ.get("RAFFAEL_SECURE_COOKIES", "0") == "1", samesite="lax", max_age=7 * 24 * 3600)
        return {"id": user.id, "email": user.email, "email_verified": False, "workspaces": runtime_auth.memberships(user.id)}

    @app.get("/auth/confirm")
    def confirm_email(token: str):
        if runtime_auth is None or not runtime_auth.confirm_email(token):
            raise HTTPException(status_code=400, detail="invalid or expired confirmation token")
        return {"status": "confirmed"}

    @app.get("/auth/newsletter/confirm")
    def confirm_newsletter(token: str):
        if runtime_auth is None or not runtime_auth.confirm_newsletter(token):
            raise HTTPException(status_code=400, detail="invalid or expired newsletter token")
        return {"status": "subscribed"}

    @app.post("/auth/login")
    def login(account: AccountInput, response: Response):
        if runtime_auth is None:
            raise HTTPException(status_code=503, detail="authentication storage unavailable")
        user = runtime_auth.authenticate(account.email, account.password)
        if user is None:
            raise HTTPException(status_code=401, detail="invalid credentials")
        token, csrf = runtime_auth.create_session(user.id)
        response.set_cookie(SESSION_COOKIE, token, httponly=True, secure=os.environ.get("RAFFAEL_SECURE_COOKIES", "0") == "1", samesite="lax", max_age=7 * 24 * 3600)
        response.set_cookie(CSRF_COOKIE, csrf, httponly=False, secure=os.environ.get("RAFFAEL_SECURE_COOKIES", "0") == "1", samesite="lax", max_age=7 * 24 * 3600)
        return {"id": user.id, "email": user.email, "workspaces": runtime_auth.memberships(user.id)}

    @app.post("/auth/password-reset/request")
    def request_password_reset(account: PasswordResetRequest):
        if runtime_auth is None:
            raise HTTPException(status_code=503, detail="authentication storage unavailable")
        try:
            result = runtime_auth.request_password_reset(account.email)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if result is not None and runtime_mailer.enabled:
            user, token = result
            public_url = os.environ.get("RAFFAEL_PUBLIC_URL", "http://127.0.0.1:8080").rstrip("/")
            logo_url = f"{public_url}/assets/02-logo-varianten/logo-liquid-silver-weiss-transparent.png"
            message = password_reset_email(recipient=user.email, reset_url=f"{public_url}/#/reset?token={token}", logo_url=logo_url)
            runtime_mailer.send(user.email, message)
        return {"status": "accepted"}

    @app.post("/auth/password-reset/confirm")
    def confirm_password_reset(account: PasswordResetConfirm):
        if runtime_auth is None:
            raise HTTPException(status_code=503, detail="authentication storage unavailable")
        try:
            valid = runtime_auth.reset_password(account.token, account.password)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if not valid:
            raise HTTPException(status_code=400, detail="invalid or expired reset token")
        return {"status": "updated"}

    @app.get("/auth/me")
    def current_user(session_token: str | None = Cookie(None, alias=SESSION_COOKIE)):
        if runtime_auth is None:
            raise HTTPException(status_code=503, detail="authentication storage unavailable")
        user = runtime_auth.user_for_token(session_token)
        if user is None:
            raise HTTPException(status_code=401, detail="authentication required")
        return {"id": user.id, "email": user.email, "workspaces": runtime_auth.memberships(user.id)}

    @app.post("/auth/logout", status_code=204)
    def logout(response: Response, request: Request, session_token: str | None = Cookie(None, alias=SESSION_COOKIE), csrf_token: str | None = Cookie(None, alias=CSRF_COOKIE), x_csrf_token: str | None = Header(None)):
        if runtime_auth is None:
            raise HTTPException(status_code=503, detail="authentication storage unavailable")
        if session_token and not runtime_auth.csrf_valid(session_token, x_csrf_token):
            raise HTTPException(status_code=403, detail="csrf validation failed")
        runtime_auth.revoke(session_token)
        response.delete_cookie(SESSION_COOKIE)
        response.delete_cookie(CSRF_COOKIE)

    @app.get("/services")
    def services(session_token: str | None = Cookie(None, alias=SESSION_COOKIE)):
        require_authenticated_user(session_token)
        return [result_json(checker(service)) for service in load_services(path)]

    @app.get("/integrations/catalog")
    def integrations_catalog(session_token: str | None = Cookie(None, alias=SESSION_COOKIE)):
        current_workspace(session_token)
        return connector_catalog()

    @app.get("/household/devices")
    def household_devices(session_token: str | None = Cookie(None, alias=SESSION_COOKIE)):
        _, workspace_id = current_workspace(session_token)
        if runtime_devices is None:
            raise HTTPException(status_code=503, detail="device storage unavailable")
        return runtime_devices.list(workspace_id)

    @app.post("/household/devices", status_code=201)
    def add_household_device(
        device: DeviceInput,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
        csrf_token: str | None = Cookie(None, alias=CSRF_COOKIE),
        x_csrf_token: str | None = Header(None),
    ):
        _, workspace_id = current_workspace(session_token)
        require_csrf(session_token, x_csrf_token or csrf_token)
        if runtime_devices is None:
            raise HTTPException(status_code=503, detail="device storage unavailable")
        try:
            return runtime_devices.create(
                workspace_id,
                device.connector,
                device.name,
                device.endpoint,
                device.credential_ref,
                device.metadata,
                device.parent_id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/household/clients")
    def household_clients(session_token: str | None = Cookie(None, alias=SESSION_COOKIE)):
        _, workspace_id = current_workspace(session_token)
        if runtime_devices is None:
            raise HTTPException(status_code=503, detail="device storage unavailable")
        return runtime_devices.list_clients(workspace_id)

    @app.post("/household/clients", status_code=201)
    def add_household_client(
        client: ClientInput,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
        csrf_token: str | None = Cookie(None, alias=CSRF_COOKIE),
        x_csrf_token: str | None = Header(None),
    ):
        _, workspace_id = current_workspace(session_token)
        require_csrf(session_token, x_csrf_token or csrf_token)
        if runtime_devices is None:
            raise HTTPException(status_code=503, detail="device storage unavailable")
        try:
            return runtime_devices.create_client(
                workspace_id,
                client.name,
                endpoint=client.endpoint,
                mac_address=client.mac_address,
                connector=client.connector,
                parent_id=client.parent_id,
                metadata=client.metadata,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/integrations/{source}/clients/import")
    def import_clients_from_source(
        source: str,
        parent_id: int | None = None,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
        csrf_token: str | None = Cookie(None, alias=CSRF_COOKIE),
        x_csrf_token: str | None = Header(None),
    ):
        _, workspace_id = current_workspace(session_token)
        require_csrf(session_token, x_csrf_token or csrf_token)
        if runtime_devices is None:
            raise HTTPException(status_code=503, detail="device storage unavailable")
        source_loader = runtime_client_source_loaders.get(source)
        if source_loader is None:
            raise HTTPException(status_code=400, detail=f"{source} client import is not implemented yet")
        try:
            imported_clients = source_loader()
            created = 0
            updated = 0
            devices = []
            for client in imported_clients:
                device, was_created = runtime_devices.upsert_client(
                    workspace_id,
                    client.name,
                    endpoint=client.endpoint,
                    mac_address=client.mac_address,
                    connector=client.connector,
                    parent_id=parent_id,
                    metadata=client.metadata,
                )
                devices.append(device)
                if was_created:
                    created += 1
                else:
                    updated += 1
            return {"created": created, "updated": updated, "clients": devices}
        except ClientSourceError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/household/discover")
    def discover_devices(
        request: DiscoveryInput,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
        csrf_token: str | None = Cookie(None, alias=CSRF_COOKIE),
        x_csrf_token: str | None = Header(None),
    ):
        current_workspace(session_token)
        require_csrf(session_token, x_csrf_token or csrf_token)
        try:
            return [item.__dict__ for item in discover_network(request.network, workers=request.workers)]
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/household/discover/adopt", status_code=201)
    def adopt_discovered_device(
        device: DiscoveryAdoptInput,
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
        csrf_token: str | None = Cookie(None, alias=CSRF_COOKIE),
        x_csrf_token: str | None = Header(None),
    ):
        _, workspace_id = current_workspace(session_token)
        require_csrf(session_token, x_csrf_token or csrf_token)
        if runtime_devices is None:
            raise HTTPException(status_code=503, detail="device storage unavailable")
        name = device.hostname or device.address
        try:
            return runtime_devices.create(
                workspace_id, "icmp", name, endpoint=device.address,
                metadata={"role": "client", "discovered": True, "open_ports": device.open_ports},
                parent_id=device.parent_id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/check")
    def check(service: ServiceInput):
        return result_json(checker(service.service()))

    @app.get("/state")
    def state(session_token: str | None = Cookie(None, alias=SESSION_COOKIE)):
        require_authenticated_user(session_token)
        if runtime_engine is None:
            return []
        return [asdict(item) for item in runtime_engine.states().values()]

    @app.get("/history/{service_name}")
    def service_history(
        service_name: str,
        start: datetime | None = Query(None, alias="from"),
        end: datetime | None = Query(None, alias="to"),
        limit: int = Query(500, ge=1, le=1000),
        session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
    ):
        require_authenticated_user(session_token)
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
