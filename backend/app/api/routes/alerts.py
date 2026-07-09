"""app/api/routes/alerts.py — alertes actives, historique, acquittement."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services.monitoring import monitoring_service
from app.schemas.alert import AlertDTO, AckAlertRequest

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/{patient_id}", response_model=list[AlertDTO])
def active_alerts(patient_id: str) -> list[AlertDTO]:
    return [AlertDTO(**a.to_dict()) for a in monitoring_service.alerts.active_alerts(patient_id)]


@router.get("/{patient_id}/history", response_model=list[AlertDTO])
def alert_history(patient_id: str, limit: int = 50) -> list[AlertDTO]:
    return [AlertDTO(**a.to_dict()) for a in monitoring_service.alerts.history(patient_id, limit)]


@router.post("/ack", response_model=AlertDTO)
def acknowledge(body: AckAlertRequest) -> AlertDTO:
    alert = monitoring_service.alerts.acknowledge(body.patient_id, body.alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    return AlertDTO(**alert.to_dict())
