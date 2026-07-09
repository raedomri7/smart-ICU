"""app/schemas/vitals.py — DTO Pydantic pour vitals et patients (I/O REST)."""

from __future__ import annotations

from pydantic import BaseModel


class VitalsDTO(BaseModel):
    hr: int
    spo2: int
    rr: int
    temp: float
    sbp: int
    dbp: int
    map: int
    rhythm: str


class PatientDTO(BaseModel):
    id: str
    external_id: str
    full_name: str
    bed: str | None = None
    age: int | None = None
    sex: str | None = None
    status: str = "monitored"
