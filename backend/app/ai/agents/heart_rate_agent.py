"""app/ai/agents/heart_rate_agent.py — détection tachy/bradycardie."""

from __future__ import annotations

from app.ai.schemas import VitalsSample, AgentResult, Severity
from app.ai.agents.base import Agent, AgentContext, trend_from


class HeartRateAgent:
    name = "Agent Fréquence Cardiaque"

    def analyze(self, sample: VitalsSample, ctx: AgentContext) -> AgentResult:
        hr = sample.ecg_hr or sample.hr
        trend = trend_from(hr, ctx.previous("hr"), threshold=3)

        if hr > 150 or hr < 35:
            severity, event = Severity.CRITICAL, "Anomalie Sévère de Fréquence"
            expl = f"FC={hr} bpm est critiquement hors limites."
            rec = "Intervention immédiate requise."
        elif hr > 120 or hr < 45:
            severity, event = Severity.HIGH, "Tachy/Bradycardie Marquée"
            expl = f"FC={hr} bpm — anomalie de fréquence significative."
            rec = "Notifier médecin. Réévaluer dans 5 min."
        elif hr > 100:
            severity, event = Severity.MEDIUM, "Tachycardie"
            expl = f"FC={hr} bpm dépasse plage normale (60-100 bpm)."
            rec = "Surveiller déclencheurs : douleur, fièvre, anxiété."
        elif hr < 60:
            severity, event = Severity.MEDIUM, "Bradycardie"
            expl = f"FC={hr} bpm — sous la plage normale."
            rec = "Évaluer médicaments, stimulation vagale, bloc conduction."
        else:
            severity, event = Severity.NORMAL, "Normal"
            expl = f"FC={hr} bpm dans plage normale (60-100 bpm)."
            rec = "Poursuivre surveillance."

        confidence = 95 if severity != Severity.NORMAL else 99
        return AgentResult(self.name, "Fréquence Cardiaque", f"{hr} bpm", event,
                           confidence, severity.value, expl, rec, trend)
