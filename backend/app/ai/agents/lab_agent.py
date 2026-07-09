"""app/ai/agents/lab_agent.py — interprétation automatisée des résultats biologiques."""

from __future__ import annotations

from app.ai.schemas import VitalsSample, AgentResult, Severity
from app.ai.agents.base import Agent, AgentContext


class LabAgent:
    name = "Agent Laboratoire"

    def analyze(self, sample: VitalsSample, ctx: AgentContext) -> AgentResult:
        v = sample
        alerts: list[str] = []
        explanations: list[str] = []

        # Electrolytes
        if v.lab_k > 0:
            if v.lab_k > 5.5:
                alerts.append(("Hyperkaliémie", "critical", f"K⁺={v.lab_k:.1f} mEq/L > 5.5 — risque arythmie."))
            elif v.lab_k < 3.0:
                alerts.append(("Hypokaliémie", "high", f"K⁺={v.lab_k:.1f} mEq/L < 3.0 — risque arythmie, faiblesse."))

        # Créatinine (AKI staging KDIGO)
        if v.lab_cr > 0:
            if v.lab_cr >= 4.0:
                alerts.append(("IRA Sévère", "critical", f"Cr={v.lab_cr:.1f} mg/dL — insuffisance rénale aiguë avancée."))
            elif v.lab_cr >= 2.0:
                alerts.append(("IRA Modérée", "high", f"Cr={v.lab_cr:.1f} mg/dL — AKI stage 2-3."))
            elif v.lab_cr >= 1.5:
                alerts.append(("IRA Débutante", "medium", f"Cr={v.lab_cr:.1f} mg/dL — AKI stage 1."))

        # Glycémie
        if v.lab_glu > 0:
            if v.lab_glu > 180:
                alerts.append(("Hyperglycémie", "medium", f"Glu={v.lab_glu:.0f} mg/dL — hyperglycémie de stress."))
            elif v.lab_glu < 70:
                alerts.append(("Hypoglycémie", "high", f"Glu={v.lab_glu:.0f} mg/dL — risque neurologique."))

        # Hémoglobine
        if v.lab_hb > 0:
            if v.lab_hb < 7.0:
                alerts.append(("Anémie Sévère", "high", f"Hb={v.lab_hb:.1f} g/dL — transfusion à évaluer."))
            elif v.lab_hb < 8.5:
                alerts.append(("Anémie", "medium", f"Hb={v.lab_hb:.1f} g/dL — surveillance."))

        # Leucocytes
        if v.lab_wbc > 0:
            if v.lab_wbc > 15:
                explanations.append(f"Leucocytose={v.lab_wbc:.1f} K/µL — inflammation/infection possible.")
            elif v.lab_wbc < 3:
                alerts.append(("Leucopénie", "medium", f"WBC={v.lab_wbc:.1f} K/µL — risque infectieux accru."))

        # Plaquettes
        if v.lab_plt > 0:
            if v.lab_plt < 50:
                alerts.append(("Thrombopénie Sévère", "critical", f"Plt={v.lab_plt:.0f} K/µL — risque hémorragique."))
            elif v.lab_plt < 100:
                alerts.append(("Thrombopénie", "medium", f"Plt={v.lab_plt:.0f} K/µL."))

        # Gaz du sang
        if v.abg_ph > 0:
            if v.abg_ph < 7.30:
                explanations.append(f"Acidose : pH={v.abg_ph:.2f}, PaCO₂={v.abg_paco2:.0f}, HCO₃={v.abg_hco3:.1f}.")
            elif v.abg_ph > 7.50:
                explanations.append(f"Alcalose : pH={v.abg_ph:.2f}, PaCO₂={v.abg_paco2:.0f}.")

        # Coagulation
        if v.coag_inr > 0:
            if v.coag_inr > 2.5:
                alerts.append(("Coagulopathie", "high", f"INR={v.coag_inr:.1f} — risque hémorragique."))

        if not alerts:
            return AgentResult(self.name, "Laboratoire", "Normal", "Normal", 95,
                               Severity.NORMAL.value,
                               "Bilan biologique dans les limites acceptables ou en amélioration.",
                               "Poursuivre surveillance.", "stable", {})

        top_event, top_sev, top_msg = max(alerts, key=lambda x: Severity(x[1]).value)
        return AgentResult(
            self.name, "Laboratoire", top_event, top_event,
            min(96, 80 + len(alerts) * 3), top_sev,
            f"{len(alerts)} anomalie(s) détectée(s) : {top_msg} " + " ".join(e for _, e in explanations),
            "Réévaluer la situation clinique et discuter avec l'équipe.",
            "stable", {"alerts": alerts, "explanations": explanations},
        )
