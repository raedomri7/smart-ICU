"""app/ai/agents/etco2_agent.py — surveillance capnométrie."""

from __future__ import annotations

from app.ai.schemas import VitalsSample, AgentResult, Severity
from app.ai.agents.base import Agent, AgentContext, trend_from


class Etco2Agent:
    name = "Agent Capnométrie"

    def analyze(self, sample: VitalsSample, ctx) -> AgentResult:
        etco2 = sample.etco2
        prev = ctx.previous("etco2") if ctx else None
        trend = trend_from(float(etco2), float(prev) if prev else None, threshold=2.0)

        if etco2 > 50:
            sev, ev = Severity.HIGH, "Hypercapnie"
            expl = f"ETCO₂={etco2} mmHg — hypoventilation."
            rec = "Réviser paramètres ventilatoires."
        elif etco2 < 30:
            sev, ev = Severity.MEDIUM, "Hypocapnie"
            expl = f"ETCO₂={etco2} mmHg — hyperventilation."
            rec = "Surveiller cause neurologique / douleur / agitation."
        else:
            sev, ev = Severity.NORMAL, "Normal"
            expl = f"ETCO₂={etco2} mmHg — normocapnie."
            rec = "Surveillance."

        return AgentResult(self.name, "ETCO₂", f"{etco2} mmHg", ev, 93 if sev != Severity.NORMAL else 97, sev.value, expl, rec, trend)
