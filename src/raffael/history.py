from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy import DateTime, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from .engine import ServiceState


@dataclass(frozen=True)
class Measurement:
    service_name: str
    status: str
    latency_ms: int | None
    http_status: int | None
    error: str | None
    checked_at: datetime


class HistoryStore(Protocol):
    def record(self, state: ServiceState) -> None: ...

    def history(
        self,
        service_name: str,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 500,
    ) -> list[Measurement]: ...


class Base(DeclarativeBase):
    pass


class MeasurementRow(Base):
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_name: Mapped[str] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(32))
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("measurement timestamps must include a timezone")
    return value.astimezone(timezone.utc)


class SqlAlchemyHistoryStore:
    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(database_url)

    def initialize(self) -> None:
        Base.metadata.create_all(self._engine)

    def close(self) -> None:
        self._engine.dispose()

    def record(self, state: ServiceState) -> None:
        if state.last_checked is None:
            raise ValueError("cannot record a state that has not been checked")

        with Session(self._engine) as session:
            session.add(
                MeasurementRow(
                    service_name=state.name,
                    status=state.status,
                    latency_ms=state.latency_ms,
                    http_status=state.http_status,
                    error=state.error,
                    checked_at=_utc(state.last_checked),
                )
            )
            session.commit()

    def history(
        self,
        service_name: str,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 500,
    ) -> list[Measurement]:
        if limit < 1 or limit > 1000:
            raise ValueError("history limit must be between 1 and 1000")

        statement = select(MeasurementRow).where(MeasurementRow.service_name == service_name)
        if start is not None:
            statement = statement.where(MeasurementRow.checked_at >= _utc(start))
        if end is not None:
            statement = statement.where(MeasurementRow.checked_at <= _utc(end))
        statement = statement.order_by(
            MeasurementRow.checked_at.desc(), MeasurementRow.id.desc()
        ).limit(limit)

        with Session(self._engine) as session:
            rows = list(reversed(session.scalars(statement).all()))

        return [
            Measurement(
                service_name=row.service_name,
                status=row.status,
                latency_ms=row.latency_ms,
                http_status=row.http_status,
                error=row.error,
                checked_at=_utc(row.checked_at.replace(tzinfo=row.checked_at.tzinfo or timezone.utc)),
            )
            for row in rows
        ]
