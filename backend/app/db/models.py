"""
app/db/models.py
================
Modèles ORM SQLAlchemy (async) reflétant docs/DATABASE.md.

La persistence est OPTIONNELLE : si `DATABASE_URL` est vide, ces modèles ne
sont jamais créés et le MVP tourne entièrement en mémoire.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Numeric, Boolean, DateTime, ForeignKey, BigInteger, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, default="clinician")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[str] = mapped_column(String, unique=True)
    full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    bed: Mapped[str | None] = mapped_column(String, nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sex: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="monitored")
    admitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class VitalsSampleRow(Base):
    __tablename__ = "vitals_samples"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"))
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    hr: Mapped[int] = mapped_column(Integer)
    spo2: Mapped[int] = mapped_column(Integer)
    rr: Mapped[int] = mapped_column(Integer)
    temp: Mapped[float] = mapped_column(Numeric(3, 1))
    sbp: Mapped[int] = mapped_column(Integer)
    dbp: Mapped[int] = mapped_column(Integer)
    map: Mapped[int] = mapped_column(Integer)
    rhythm: Mapped[str] = mapped_column(String)
    overall_severity: Mapped[str] = mapped_column(String)
    risk_score: Mapped[int] = mapped_column(Integer)


class AlertRow(Base):
    __tablename__ = "alerts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"))
    signal: Mapped[str] = mapped_column(String)
    event: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    confidence: Mapped[int] = mapped_column(Integer)
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="active")
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AISnapshotRow(Base):
    __tablename__ = "ai_snapshots"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"))
    sample_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    decision: Mapped[dict] = mapped_column(JSONB)
    prediction: Mapped[dict] = mapped_column(JSONB)
    agents: Mapped[dict] = mapped_column(JSONB)
    clinical_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
