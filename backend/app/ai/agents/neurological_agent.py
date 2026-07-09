"""app/ai/agents/neurological_agent.py — surveillance neurologique (neuro critique)."""

from __future__ import annotations

from app.ai.schemas import VitalsSample, AgentResult, Severity
from app.ai.agents.base import Agent, AgentContext, trend_from


CEREBRAL_PERFUSION_LOW = 60
ICP_HIGH = 20
ICP_CRITICAL = 30
BIS_DEEP = 40
BIS_LIGHT = 70


class NeurologicalAgent:
    name = "Agent Neurologique"

    def analyze(self, sample: VitalsSample, ctx: AgentContext) -> AgentResult:
        v = sample
        cpp = v.cpp_val
        icp = v.icp
        bis = v.bis
        gcs = v.gcs

        if gcs and gcs <= 8 and v.ecg_rhythm != "normal":
            severity, event = Severity.CRITICAL, "État de Mal Épileptique Suspecté"
            expl = f"GCS={gcs}, rythme anormal — activité épileptique possible (chutes tensionnelles)."
            rec = "EEG urgent, protéger voies aériennes, anticonvulsivants."
        elif 0 < icp >= ICP_CRITICAL:
            severity, event = Severity.CRITICAL, "ICP Critique"
            expl = f"ICP={icp:.0f} mmHg — engagement cérébral imminent, hernie possible."
            rec = "Mesure ICP continue. Osmothérapie (mannitol/hypertonique). Neurochirurgien urgent."
        elif 0 < icp >= ICP_HIGH:
            severity, event = Severity.HIGH, "ICP Élevée"
            expl = f"ICP={icp:.0f} mmHg > 20 mmHg — hypertension intracrânienne."
            rec = "Sédation, hyperventilation courte, position tête surélevée 30°. Commerce thérapeutique."
        elif 0 < cpp and cpp < CEREBRAL_PERFUSION_LOW:
            severity, event = Severity.HIGH, "CPP Critique"
            expl = f"PCP={cpp:.0f} mmHg < 60 mmHg — perfusion cérébrale insuffisante."
            rec = "Optimiser PAM (vasopresseurs), réduire ICP si possible."
        elif bis and bis < BIS_DEEP:
            severity, event = Severity.HIGH, "Sédation Profonde"
            expl = f"BIS={bis} — sédation très profonde, risque de retard diagnostic neurologique."
            rec = "Réduire sédation pour évaluation neurologique. Surveillance GCS/BIS continue."
        elif bis and bis < BIS_LIGHT and gcs and gcs >= 13:
            severity, event = Severity.NORMAL, "Agitation Possible"
            expl = f"BIS={bis} — éveil, risque d'agitation, d'extubation."
            rec = "Sédation analgésie adaptée. Prévenir l'équipe si extubation non prévue."
        elif gcs and gcs < 14:
            severity, event = Severity.MEDIUM, "Trouble Conscience"
            expl = f"GCS={gcs}/15 — altération du niveau de conscience."
            rec = "Rechercher cause métabolique / toxique / structurelle. Surveillance rapprochée."
        else:
            severity, event = Severity.NORMAL, "Neuro Normal"
            expl = f"GCS={gcs}/15, ICP={icp:.0f}, PCP={cpp:.0f}, BIS={bis}."
            rec = "Surveillance neurologique de routine."

        confidence = 85 if severity != Severity.NORMAL else 96
        return AgentResult(self.name, "Neurologie", f"GCS {gcs}", event,
                           confidence, severity.value, expl, rec, "stable", {
                               "icp": icp, "cpp": cpp, "bis": bis, "gcs": gcs,
                           })
