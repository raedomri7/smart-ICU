"""app/ai/agents/ventilation_agent.py — surveillance ventilation mécanique."""

from __future__ import annotations

from app.ai.schemas import VitalsSample, AgentResult, Severity
from app.ai.agents.base import Agent, AgentContext, trend_from


class VentilationAgent:
    name = "Agent Ventilation Mécanique"

    def analyze(self, sample: VitalsSample, ctx: AgentContext) -> AgentResult:
        v = sample
        details: dict = {}
        trend_vent = trend_from(v.vent_mv or 0, ctx.previous("vent_mv"), threshold=0.3)
        trend_peep = trend_from(v.vent_peep, ctx.previous("vent_peep"), threshold=0.5)

        # Pplat excessif (barotrauma risk)
        if v.vent_pplat > 35:
            severity, event = Severity.HIGH, "Pplat Excessive"
            details["barotrauma_risk"] = True
            expl = f"Pplat={v.vent_pplat:.0f} cmH₂O > 30 cmH₂O — risque de barotrauma."
            rec = "Envisager réduction VT ou Pplat target <30 cmH₂O. Évaluer compliance."
        # Auto-PEEP (PEEPi)
        elif v.vent_mode in ["VCV", "PCV", "PSV"] and v.vent_rr < 12 and v.vent_peep <= 5:
            severity, event = Severity.MEDIUM, "Hypoventilation Possible"
            details["auto_peep_risk"] = False
            expl = f"RR={v.vent_rr}/min, PEEP={v.vent_peep:.0f} — risque d'atélectasie sous-basale."
            rec = "Surveiller gazométrie. Envisager PEEP accrue ou recrutement."
        # Vt trop élevé (seuil 600 mL ≈ 8.6 mL/kg pour 70kg)
        if v.vent_vt > 600 and v.vent_mode in ["VCV", "PRVC"]:
            severity, event = Severity.MEDIUM, "Vt Élevé"
            details["volutrauma_risk"] = True if v.vent_vt > 700 else False
            expl = f"Vt={v.vent_vt} mL — risque de volutrauma en ventilation protectrice."
            rec = "Cibler Vt 4-8 mL/kg P/cmc idéal (6-8). Réduire volume courant."
        # VAE risk
        elif v.vent_pip > 30 and v.vent_peep >= 10:
            severity, event = Severity.MEDIUM, "Surveillance VAE"
            details["vae_risk"] = True
            expl = "Paramètres ventilatoires à risque d'événement associé à la ventilation (VAE)."
            rec = "Optimiser sédation, PEEP, weaning selon protocole VAE."
        else:
            severity, event = Severity.NORMAL, "Ventilation Stable"
            expl = f"Mode={v.vent_mode}, FiO₂={v.vent_fio2}%, PEEP={v.vent_peep:.0f} cmH₂O, MV={v.vent_mv:.1f} L/min."
            rec = "Poursuivre la ventilation actuelle. Surveiller gazométrie périodique."

        confidence = 88 if severity != Severity.NORMAL else 94
        return AgentResult(self.name, "Ventilation", v.vent_mode, event,
                           confidence, severity.value, expl, rec, trend_vent, details)
