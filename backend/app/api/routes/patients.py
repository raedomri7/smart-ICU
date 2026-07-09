"""app/api/routes/patients.py — liste/état des patients monitorés."""

from __future__ import annotations

from fastapi import APIRouter

from app.services.monitoring import monitoring_service

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("")
def list_patients() -> list[dict]:
    """Liste les patients actuellement monitorés et leur dernier état."""
    out = []
    for pid in monitoring_service.patients():
        monitor = monitoring_service.get_or_create(pid)
        snap = monitor.last_snapshot
        out.append({
            "patient_id": pid,
            "rhythm": snap.vitals.rhythm if snap else "normal",
            "overall_severity": snap.decision.overall_severity if snap else "normal",
            "risk": snap.prediction.deterioration_risk if snap else 0,
        })
    return out


@router.get("/{patient_id}/latest")
def latest(patient_id: str) -> dict:
    """Dernier snapshot IA connu pour un patient (canal froid REST)."""
    monitor = monitoring_service.get_or_create(patient_id)
    if monitor.last_snapshot is None:
        monitor.tick()
    return monitor.last_snapshot.to_public_dict()
