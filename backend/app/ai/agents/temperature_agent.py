"""app/ai/agents/temperature_agent.py — fièvre / hypothermie."""

from __future__ import annotations

from app.ai.schemas import VitalsSample, AgentResult, Severity
from app.ai.agents.base import Agent, AgentContext, trend_from


class TemperatureAgent:
    name = "Agent Température"

    def analyze(self, sample: VitalsSample, ctx: AgentContext) -> AgentResult:
        temp = sample.temp_core or sample.temp_skin or 37.0
        trend = trend_from(temp, ctx.previous("temp"), threshold=0.1)
        if temp >= 40.0:
            severity, event = Severity.CRITICAL, "Hyperpyrexie"
            expl = f"Temp={temp:.1f}°C — hyperthermie extrême."
            rec = "Refroidissement actif immédiat. Investiguer sepsis/infection."
        elif temp >= 39.0:
            severity, event = Severity.HIGH, "Forte Fièvre"
            expl = f"Temp={temp:.1f}°C — forte fièvre, sepsis possible."
            rec = "Antipyrétiques. Hémocultures recommandées."
        elif temp >= 38.0:
            severity, event = Severity.MEDIUM, "Fièvre"
            expl = f"Temp={temp:.1f}°C — fièvre, processus infectieux possible."
            rec = "Surveiller. Antipyrétiques + bilan infectieux."
        elif temp < 35.0:
            severity, event = Severity.CRITICAL, "Hypothermie Sévère"
            expl = f"Temp={temp:.1f}°C — hypothermie sévère, risque d'arythmie."
            rec = "Réchauffement actif. Surveillance cardiaque continue."
        elif temp < 36.0:
            severity, event = Severity.HIGH, "Hypothermie"
            expl = f"Temp={temp:.1f}°C — sous la plage normale."
            rec = "Mesures de réchauffement. Surveiller arythmie."
        else:
            severity, event = Severity.NORMAL, "Normal"
            expl = f"Temp={temp:.1f}°C — dans la plage normale."
            rec = "Poursuivre la surveillance de routine."
        confidence = 96 if severity != Severity.NORMAL else 99
        return AgentResult(self.name, "Température", f"{temp:.1f}°C", event,
                           confidence, severity.value, expl, rec, trend)
