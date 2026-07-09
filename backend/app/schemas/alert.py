"""app/schemas/alert.py — DTO Pydantic pour les alertes."""

from __future__ import annotations

from pydantic import BaseModel


class AlertDTO(BaseModel):
    id: str
    patient_id: str
    signal: str
    event: str
    severity: str
    confidence: int
    message: str
    status: str
    created_at: float
    resolved_at: float | None = None


class AckAlertRequest(BaseModel):
    patient_id: str
    alert_id: str
