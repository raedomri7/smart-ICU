"""app/schemas/ai.py — DTO Pydantic pour la sortie IA (décision, prédiction, agents)."""

from __future__ import annotations

from pydantic import BaseModel


class AgentResultDTO(BaseModel):
    agent_name: str
    signal: str
    value: str
    detected_event: str
    confidence: int
    severity: str
    explanation: str
    recommendation: str
    trend: str


class DecisionDTO(BaseModel):
    overall_severity: str
    diagnosis: str
    recommended_action: str
    top_signal: str
    contributing: list[str]


class PredictionDTO(BaseModel):
    cardiac_arrest_risk: int
    respiratory_failure_risk: int
    shock_risk: int
    deterioration_risk: int
    horizons: dict[str, int]


class AISnapshotDTO(BaseModel):
    patient_id: str
    ts: float
    vitals: dict
    ecg: dict
    agents: dict[str, AgentResultDTO]
    decision: DecisionDTO
    prediction: PredictionDTO
