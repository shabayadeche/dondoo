from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from datetime import date, datetime, timezone
from functools import lru_cache
from pathlib import Path
import sqlite3
from uuid import uuid4

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, LargeBinary, String, Text, create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.settings import get_settings


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ClinicalCaseRecord(Base):
    __tablename__ = "clinical_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    external_case_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    case_status: Mapped[str] = mapped_column(String(32), index=True)
    procedure_type: Mapped[str] = mapped_column(String(32), index=True)
    patient_identifier: Mapped[str] = mapped_column(String(128), index=True)
    procedure_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    facility_unit: Mapped[str] = mapped_column(String(128))
    endoscopist_name: Mapped[str] = mapped_column(String(128))
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    payload_json: Mapped[dict] = mapped_column(JSON)
    current_pdf_bytes: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    current_pdf_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    tasks: Mapped[list[ClinicalTaskRecord]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    image_attachments: Mapped[list[ClinicalCaseImageRecord]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    revisions: Mapped[list[ClinicalCaseRevisionRecord]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )
    audit_events: Mapped[list[ClinicalAuditEventRecord]] = relationship(
        back_populates="case",
        cascade="all, delete-orphan",
    )


class ClinicalTaskRecord(Base):
    __tablename__ = "clinical_followup_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    external_task_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("clinical_cases.id", ondelete="CASCADE"), index=True)
    task_type: Mapped[str] = mapped_column(String(64), index=True)
    task_owner_user_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    task_owner_user_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    task_status: Mapped[str] = mapped_column(String(32), index=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by_user_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    closed_by_user_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    case: Mapped[ClinicalCaseRecord] = relationship(back_populates="tasks")


class ClinicalCaseImageRecord(Base):
    __tablename__ = "clinical_case_images"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    external_image_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("clinical_cases.id", ondelete="CASCADE"), index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    uploaded_by_user_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    uploaded_by_user_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    image_bytes: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    case: Mapped[ClinicalCaseRecord] = relationship(back_populates="image_attachments")


class ClinicalCaseRevisionRecord(Base):
    __tablename__ = "clinical_case_revisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    case_id: Mapped[str] = mapped_column(ForeignKey("clinical_cases.id", ondelete="CASCADE"), index=True)
    revision_number: Mapped[int] = mapped_column(index=True)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finalized_by_user_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    finalized_by_user_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    template_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    report_narrative_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_bytes: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    pdf_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    snapshot_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    case: Mapped[ClinicalCaseRecord] = relationship(back_populates="revisions")


class ClinicalAuditEventRecord(Base):
    __tablename__ = "clinical_audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    case_id: Mapped[str] = mapped_column(ForeignKey("clinical_cases.id", ondelete="CASCADE"), index=True)
    actor_user_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    actor_display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_type: Mapped[str] = mapped_column(String(128), index=True)
    entity_type: Mapped[str] = mapped_column(String(64), default="case")
    entity_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload_json: Mapped[dict | list | str | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)

    case: Mapped[ClinicalCaseRecord] = relationship(back_populates="audit_events")


def _resolved_database_url() -> str:
    raw_url = get_settings().database_url.strip()
    if not raw_url.startswith("sqlite:///"):
        return raw_url

    sqlite_target = raw_url.removeprefix("sqlite:///")
    if sqlite_target in {":memory:", ""} or sqlite_target.startswith("/"):
        return raw_url

    database_path = Path(sqlite_target)
    if not database_path.is_absolute():
        database_path = Path.cwd() / database_path
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{database_path.as_posix()}"


def _engine_kwargs(database_url: str) -> dict:
    if not database_url.startswith("sqlite"):
        return {}

    kwargs: dict = {"connect_args": {"check_same_thread": False}}
    if database_url in {"sqlite://", "sqlite:///:memory:"}:
        kwargs["poolclass"] = StaticPool
    return kwargs


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ANN001, ARG001
    if not isinstance(dbapi_connection, sqlite3.Connection):
        return

    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    except Exception:
        return


@lru_cache
def get_engine() -> Engine:
    database_url = _resolved_database_url()
    return create_engine(database_url, future=True, **_engine_kwargs(database_url))


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, future=True)


def init_database() -> None:
    Base.metadata.create_all(bind=get_engine())


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_database_runtime() -> None:
    engine = get_engine()
    engine.dispose()
    get_session_factory.cache_clear()
    get_engine.cache_clear()
