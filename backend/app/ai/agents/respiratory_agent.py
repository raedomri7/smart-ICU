"""app/ai/agents/respiratory_agent.py — FR, SpO2+, hypoxémie, détresse."""

from __future__ import annotations

from app.ai.schemas import VitalsSample, AgentResult, Severity
from app.ai.agents.base import Agent, AgentContext, trend_from


class RespiratoryAgent:
    name = "Agent Respiratoire"

    def analyze(self, sample: VitalsSample, ctx: AgentContext) -> AgentResult:
        rr = sample.rr_capno or sample.vent_rr or 16
        spo2 = sample.spo2
        prev_rr = ctx.previous("rr")
        trend = trend_from(rr, float(prev_rr) if prev_rr is not None else None, threshold=1.0)

        if rr > 30 or (spo2 < 85 and rr > 24):
            severity, event = Severity.CRITICAL, "Détresse Respiratoire Sévère"
            expl = f"FR={rr}/min, SpO₂={spo2}% — défaillance respiratoire imminente."
            rec = "Support ventilatoire immédiat. Évaluation médicale. Préparer intubation."
        elif rr > 24 or rr < 10 or spo2 < 90:
            severity, event = Severity.HIGH, "Détresse Respiratoire"
            expl = f"FR={rr}/min, SpO₂={spo2}% — anomalie marquée."
            rec = "Réévaluer voies respiratoires et oxygénation. Notifier médecin."
        elif rr > 20:
            severity, event = Severity.MEDIUM, "Tachypnée"
            expl = f"FR={rr}/min — élevée (12-20 normal)."
            rec = "Investiguer : douleur, fièvre, hypoxie, acidose métabolique."
        elif rr < 12:
            severity, event = Severity.MEDIUM, "Bradypnée"
            expl = f"FR={rr}/min — sous normale. Déficit ventilation/aléolaire."
            rec = "Évaluer sédation, dépression SNC, pathologie neuromusculaire."
        else:
            severity, event = Severity.NORMAL, "Normal"
            expl = f"FR={rr}/min dans plage normale (12-20)."
            rec = "Poursuivre surveillance."

        confidence = 93 if severity != Severity.NORMAL else 98
        return AgentResult(self.name, "Respiratoire", f"{rr}/min", event,
                           confidence, severity.value, expl, rec, trend)
