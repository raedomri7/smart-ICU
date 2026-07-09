"""app/ai/agents/ecg_agent.py — analyse le rythme ECG classifié."""

from __future__ import annotations

import random

from app.ai.schemas import VitalsSample, AgentResult, Severity
from app.ai.ecg_generator import ECG_CLINICAL_INFO
from app.ai.agents.base import Agent, AgentContext


class ECGAgent:
    name = "Agent ECG"

    _RECS = {
        Severity.CRITICAL: "Notification immédiate du médecin. Préparer une intervention d'urgence.",
        Severity.HIGH: "Évaluation cardiologique urgente recommandée dans les 15 minutes.",
        Severity.MEDIUM: "Augmenter la fréquence de surveillance. Notifier le médecin traitant.",
        Severity.LOW: "Poursuivre l'observation étroite.",
    }

    def analyze(self, sample: VitalsSample, ctx: AgentContext) -> AgentResult:
        rhythm = getattr(sample, "ecg_rhythm", getattr(sample, "rhythm", "normal"))
        anomaly_type = getattr(sample, "ecg_anomaly_type", None)
        if anomaly_type is None or rhythm == "normal":
            return AgentResult(
                agent_name=self.name, signal="ECG", value="Rythme Sinusal Normal",
                detected_event="Normal", confidence=98, severity=Severity.NORMAL.value,
                explanation="Morphologie P-QRS-T régulière, axe normal.",
                recommendation="Poursuivre la surveillance de routine.", trend="stable",
            )

        info = ECG_CLINICAL_INFO.get(anomaly_type, {
            "meaning": "Morphologie de battement anormale non classifiée détectée.",
            "severity": "medium", "base_confidence": 80,
        })
        confidence = min(99, info["base_confidence"] + random.randint(-3, 3))
        severity = Severity(info["severity"])
        return AgentResult(
            agent_name=self.name, signal="ECG", value=anomaly_type,
            detected_event=anomaly_type, confidence=confidence, severity=severity.value,
            explanation=info["meaning"],
            recommendation=self._RECS.get(severity, "Surveiller étroitement."),
            trend="rising" if severity in (Severity.HIGH, Severity.CRITICAL) else "stable",
        )
