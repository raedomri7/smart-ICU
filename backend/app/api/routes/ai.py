"""
app/api/routes/ai.py
====================
Endpoints IA canal froid : contrôle de scénario/source et résumé clinique
Gemini (optionnel, hors temps réel).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.monitoring import monitoring_service
from app.acquisition.simulator import WAVEFORM_RANGES
from app.llm.gemini import gemini_client

router = APIRouter(prefix="/ai", tags=["ai"])


class ScenarioRequest(BaseModel):
    patient_id: str
    scenario: str


@router.get("/scenarios")
def scenarios() -> list[str]:
    """Scénarios cliniques disponibles pour le simulateur."""
    return list(WAVEFORM_RANGES.keys())


@router.post("/scenario")
def set_scenario(body: ScenarioRequest) -> dict:
    if body.scenario not in WAVEFORM_RANGES:
        raise HTTPException(status_code=400, detail="Scénario inconnu")
    monitoring_service.set_scenario(body.patient_id, body.scenario)
    return {"ok": True, "patient_id": body.patient_id, "scenario": body.scenario}


@router.post("/summary/{patient_id}")
def clinical_summary(patient_id: str) -> dict:
    """
    Résumé clinique textuel (Gemini). Désactivé par défaut : renvoie une source
    'disabled' si Gemini n'est pas configuré. JAMAIS sur le chemin temps réel.
    """
    monitor = monitoring_service.get_or_create(patient_id)
    if monitor.last_snapshot is None:
        monitor.tick()
    snap = monitor.last_snapshot

    context = {
        "diagnosis": snap.decision.diagnosis,
        "overall_severity": snap.decision.overall_severity,
        "contributing": snap.decision.contributing,
        "deterioration_risk": snap.prediction.deterioration_risk,
    }
    text = gemini_client.clinical_summary(context)
    if text is None:
        # Repli local (aucune dépendance externe) — le système reste utilisable
        return {
            "source": "local",
            "text": f"{snap.decision.diagnosis} Action recommandée : "
                    f"{snap.decision.recommended_action} "
                    f"(risque de dégradation {snap.prediction.deterioration_risk}%).",
        }
    return {"source": "gemini", "text": text}
