"""app/ai/agents/spo2_agent.py — SpO2+, indice de perfusion, pléthysmographe."""

from __future__ import annotations

from app.ai.schemas import VitalsSample, AgentResult, Severity
from app.ai.agents.base import Agent, AgentContext, trend_from


class SpO2Agent:
    name = "Agent SpO2 / Oximétrie"

    def analyze(self, sample: VitalsSample, ctx: AgentContext) -> AgentResult:
        spo2 = sample.spo2
        pi = sample.pi
        pleth = sample.pleth_amp
        prev = ctx.previous("spo2")
        trend = "stable"
        if prev is not None:
            if spo2 < prev - 1:
                trend = "falling"
            elif spo2 > prev + 1:
                trend = "rising"

        if spo2 < 85:
            severity, event = Severity.CRITICAL, "Hypoxémie Sévère"
            expl = f"SpO₂={spo2}% — déficience critique en oxygène, risque lésion organique."
            rec = "Oxygène haut débit immédiat. Préparer intubation."
        elif spo2 < 90:
            severity, event = Severity.HIGH, "Hypoxémie"
            expl = f"SpO₂={spo2}% — désaturation significative."
            rec = "Augmenter O₂ suppl. Réévaluer voies respiratoires."
        elif spo2 < 95:
            severity, event = Severity.MEDIUM, "Désaturation Légère"
            expl = f"SpO₂={spo2}% — sous plage cible, compromission respiratoire précoce."
            rec = "Surveiller étroitement. Envisager O₂ suppl."
        else:
            severity, event = Severity.NORMAL, "Normal"
            expl = f"SpO₂={spo2}%, PI={pi:.1f}% — oxygénation adéquate, signal de bonne qualité."
            rec = "Poursuivre surveillance."

        details: dict = {"pi": pi, "pleth_amp": pleth}
        if pi < 1.0:
            details["perfusion_warning"] = True
            details["perfusion_warning_msg"] = "PI bas (<1%) → fiabilité SpO₂ réduite, vérifier capteur / perfusion."

        confidence = 97 if severity != Severity.NORMAL else 99
        return AgentResult(self.name, "SpO₂ / Oximétrie", f"{spo2}%", event,
                           confidence, severity.value, expl, rec, trend, details)
