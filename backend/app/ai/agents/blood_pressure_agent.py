"""app/ai/agents/blood_pressure_agent.py — hypo/hypertension, risque de choc."""

from __future__ import annotations

from app.ai.schemas import VitalsSample, AgentResult, Severity
from app.ai.agents.base import Agent, AgentContext, trend_from


class BloodPressureAgent:
    name = "Agent Pression Artérielle"

    def analyze(self, sample: VitalsSample, ctx: AgentContext) -> AgentResult:
        sbp, dbp = sample.nibp_sys, sample.nibp_dia
        trend = trend_from(sbp, ctx.previous("sbp"), threshold=3)
        map_val = sample.map_val
        if sbp < 80 or map_val < 60:
            severity, event = Severity.CRITICAL, "Risque de Choc"
            expl = f"PA={sbp}/{dbp} mmHg (PAM {map_val}) — perfusion inadéquate, risque choc."
            rec = "Réanimation liquidienne/vasopresseurs. Notifier médecin immédiatement."
        elif sbp < 90:
            severity, event = Severity.HIGH, "Hypotension"
            expl = f"PA={sbp}/{dbp} mmHg — hypotension significative."
            rec = "Évaluer statut volémique. Envisager fluides IV."
        elif sbp > 180 or dbp > 120:
            severity, event = Severity.CRITICAL, "Crise Hypertensive"
            expl = f"PA={sbp}/{dbp} mmHg — urgence hypertensive."
            rec = "Thérapie antihypertensive immédiate. Évaluer organes cibles."
        elif sbp > 140:
            severity, event = Severity.MEDIUM, "Hypertension"
            expl = f"PA={sbp}/{dbp} mmHg — élevée au-dessus normale."
            rec = "Surveiller tendance. Réviser traitement antihypertenseur."
        else:
            severity, event = Severity.NORMAL, "Normal"
            expl = f"PA={sbp}/{dbp} mmHg (PAM {map_val}) — dans plage normale."
            rec = "Poursuivre surveillance."
        confidence = 94 if severity != Severity.NORMAL else 98
        return AgentResult(self.name, "Pression Artérielle", f"{sbp}/{dbp}", event,
                           confidence, severity.value, expl, rec, trend)
