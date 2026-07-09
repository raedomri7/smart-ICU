"""
app/api/routes/reports.py
=========================
Génération et consultation de rapports médicaux automatiques.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException

from app.services.monitoring import monitoring_service
from app.schemas.ai import AISnapshotDTO

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{patient_id}/latest")
def latest_reports(patient_id: str, report_type: Optional[str] = None) -> list[dict]:
    monitor = monitoring_service.get_or_create(patient_id)
    if monitor.last_snapshot is None:
        monitor.tick()
    snap = monitor.last_snapshot
    reports = snap.reports if snap else []
    if report_type:
        reports = [r for r in reports if r.report_type == report_type]
    return [
        {
            "report_type": r.report_type,
            "patient_id": r.patient_id,
            "ts": r.ts,
            "content_md": r.content_md,
            "summary": r.summary,
            "critical_flags": r.critical_flags,
        }
        for r in reports
    ]


@router.get("/{patient_id}/progress")
def progress_note(patient_id: str) -> dict:
    monitor = monitoring_service.get_or_create(patient_id)
    if monitor.last_snapshot is None:
        monitor.tick()
    report = monitor.last_snapshot.reports[0] if monitor.last_snapshot and monitor.last_snapshot.reports else None
    if not report:
        raise HTTPException(status_code=404, detail="Aucun rapport disponible")
    return {
        "report_type": report.report_type,
        "patient_id": report.patient_id,
        "ts": report.ts,
        "content_md": report.content_md,
        "summary": report.summary,
        "critical_flags": report.critical_flags,
    }
