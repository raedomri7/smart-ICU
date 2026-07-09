"""app/ai/agents/hemodynamic_agent.py — CVP, CO/CI, PAP, SVR."""

from __future__ import annotations

from app.ai.schemas import VitalsSample, AgentResult, Severity
from app.ai.agents.base import Agent, AgentContext, trend_from


class HemodynamicAgent:
    name = "Agent Hémodynamique"

    def analyze(self, sample: VitalsSample, ctx: AgentContext) -> AgentResult:
        v = sample
        cvp_t = trend_from(v.cvp, ctx.previous("cvp"), threshold=1.0)
        co_t = trend_from(v.co, ctx.previous("co"), threshold=0.3)

        if v.map_val < 65 and v.map_val > 0:
            severity, event = Severity.CRITICAL, "Choc Cardiogénique / Distributif"
            expl = f"PAM={v.map_val} mmHg, CvP={v.cvp:.1f}, CO={v.co:.1f} — perfusion inadéquate."
            rec = "Vasopresseurs / inotropes. Réanimation liquidienne prudente. Cathéter artériel."
        elif v.cvp > 15:
            severity, event = Severity.HIGH, "Hypervolémie / Dysfonction VD"
            expl = f"CvP={v.cvp:.1f} mmHg élevé — risque de surcharge."
            rec = "Évaluer remplissage, fonction VD. Envisager diurétiques / support inotrope."
        elif v.co > 0 and (v.co < 3.0 or (v.ci and v.ci < 1.8)):
            severity, event = Severity.HIGH, "Débit Cardiaque Bas"
            expl = f"CO={v.co:.1f} L/min (CI={v.ci:.1f} L/min/m²) — bas débit."
            rec = "Inotropes (dobutamine). Évaluer épanchement, ischémie, tamponnade."
        elif v.svr and v.svr > 2000:
            severity, event = Severity.HIGH, "SVR Élevé"
            expl = f"SVR={v.svr} dyn.s.cm⁻⁵ — résistance vasculaire systémique élevée."
            rec = "Vasodilatateurs si tolérés. Réévaluer après-vent, rétrécissement aortique."
        elif v.co > 0 and v.co < 3.5:
            severity, event = Severity.MEDIUM, "CO Limite"
            expl = f"CO={v.co:.1f}, CI={v.ci:.1f} — surveillance rapprochée."
            rec = "Surveillance continue. Optimiser précharge/contractilité."
        else:
            severity, event = Severity.NORMAL, "Hémodynamique Stable"
            expl = f"MAP={v.map_val} mmHg, CvP={v.cvp:.1f}, CO={v.co:.1f}, CI={v.ci:.1f}."
            rec = "Poursuivre surveillance hémodynamique de routine."

        confidence = 90 if severity != Severity.NORMAL else 93
        return AgentResult(self.name, "Hémodynamique", f"CO {v.co:.1f}", event,
                           confidence, severity.value, expl, rec, co_t, {
                               "cvp": v.cvp, "ci": v.ci, "svr": v.svr,
                               "pap_sys": v.pap_sys, "pcwp": v.pcwp,
                           })
