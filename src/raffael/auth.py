"""Password and session primitives for the local-account boundary."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from sqlalchemy import DateTime, ForeignKey, String, create_engine, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from .history import Base

PASSWORD_HASHER = PasswordHasher()
SESSION_COOKIE = "raffael_session"
CSRF_COOKIE = "raffael_csrf"
SESSION_TTL = timedelta(days=7)


class UserRow(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class WorkspaceRow(Base):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MembershipRow(Base):
    __tablename__ = "memberships"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(16))


class SessionRow(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_digest: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    csrf_digest: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuthStore:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)

    def initialize(self) -> None:
        Base.metadata.create_all(self.engine)

    def close(self) -> None:
        self.engine.dispose()

    def register(self, email: str, password: str, workspace_name: str = "default") -> UserRow:
        normalized = normalize_email(email)
        now = datetime.now(timezone.utc)
        with Session(self.engine) as session:
            if session.scalar(select(UserRow).where(UserRow.email == normalized)):
                raise ValueError("account already exists")
            user = UserRow(email=normalized, password_hash=hash_password(password), created_at=now)
            workspace = WorkspaceRow(name=workspace_name[:120] or "default", created_at=now)
            session.add_all([user, workspace])
            session.flush()
            session.add(MembershipRow(user_id=user.id, workspace_id=workspace.id, role="owner"))
            session.commit()
            session.refresh(user)
            return user

    def authenticate(self, email: str, password: str) -> UserRow | None:
        normalized = normalize_email(email)
        with Session(self.engine) as session:
            user = session.scalar(select(UserRow).where(UserRow.email == normalized))
            if user is None or not verify_password(user.password_hash, password):
                return None
            return user

    def create_session(self, user_id: int) -> tuple[str, str]:
        token = new_session_token()
        csrf = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        with Session(self.engine) as session:
            session.add(SessionRow(user_id=user_id, token_digest=session_digest(token), csrf_digest=session_digest(csrf), created_at=now, expires_at=session_expiry(now)))
            session.commit()
        return token, csrf

    def user_for_token(self, token: str | None) -> UserRow | None:
        if not token:
            return None
        now = datetime.now(timezone.utc)
        with Session(self.engine) as session:
            row = session.scalar(select(SessionRow).where(SessionRow.token_digest == session_digest(token)))
            expires_at = row.expires_at.replace(tzinfo=timezone.utc) if row and row.expires_at.tzinfo is None else (row.expires_at if row else None)
            if row is None or row.revoked_at is not None or expires_at <= now:
                return None
            return session.get(UserRow, row.user_id)

    def revoke(self, token: str | None) -> None:
        if not token:
            return
        with Session(self.engine) as session:
            row = session.scalar(select(SessionRow).where(SessionRow.token_digest == session_digest(token)))
            if row is not None:
                row.revoked_at = datetime.now(timezone.utc)
                session.commit()

    def csrf_valid(self, token: str, csrf: str | None) -> bool:
        if not csrf:
            return False
        with Session(self.engine) as session:
            row = session.scalar(select(SessionRow).where(SessionRow.token_digest == session_digest(token)))
            return bool(row and secrets.compare_digest(row.csrf_digest, session_digest(csrf)))

    def memberships(self, user_id: int) -> list[dict[str, int | str]]:
        with Session(self.engine) as session:
            rows = session.execute(
                select(MembershipRow, WorkspaceRow)
                .join(WorkspaceRow, WorkspaceRow.id == MembershipRow.workspace_id)
                .where(MembershipRow.user_id == user_id)
                .order_by(WorkspaceRow.id)
            )
            return [
                {"id": workspace.id, "name": workspace.name, "role": membership.role}
                for membership, workspace in rows
            ]


def normalize_email(email: str) -> str:
    value = email.strip().casefold()
    if not value or "@" not in value or len(value) > 320:
        raise ValueError("valid email required")
    return value


def hash_password(password: str) -> str:
    if len(password) < 12:
        raise ValueError("password must contain at least 12 characters")
    return PASSWORD_HASHER.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return PASSWORD_HASHER.verify(password_hash, password)
    except (InvalidHashError, VerificationError, VerifyMismatchError):
        return False


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def session_digest(token: str) -> str:
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def session_expiry(now: datetime | None = None) -> datetime:
    current = now or datetime.now(timezone.utc)
    return current + SESSION_TTL
