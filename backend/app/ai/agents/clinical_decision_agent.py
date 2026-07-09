"""
app/ai/agents/clinical_decision_agent.py
=========================================
Agent de fusion : combine toutes les analyses en un diagnostic unifié, risque
global, scores cliniques standardisés, et action prioritaire.

Intègre automatiquement : SOFA, qSOFA, NEWS2, Braden, CAM-ICU, sepsis surrogate.
"""

from __future__ import annotations

from app.ai.schemas import AgentResult, Decision, Severity, severity_rank, ClinicalScore


class ClinicalDecisionAgent:
    name = "Agent de Décision Clinique"

    def decide(self, results: list[AgentResult], scores: list[ClinicalScore] | None = None) -> Decision:
        sorted_results = sorted(results, key=lambda r: severity_rank(r.severity), reverse=True)
        top = sorted_results[0]
        active_abnormal = [r for r in sorted_results if r.severity != Severity.NORMAL.value]
        scores = scores or []

        if not active_abnormal:
            diagnosis = "Aucune anomalie aiguë détectée. Patient stable."
            action = "Poursuivre la surveillance de routine."
        else:
            diagnosis = self._infer_diagnosis(active_abnormal)
            action = top.recommendation

        # Surrogate sepsis score prominence
        top_score = scores[0] if scores else None
        if top_score and top_score.name == "Sepsis Suspected" and top_score.score >= 2:
            diagnosis = f"SEPSIS SUSPECTÉ (qSOFA ≥ 2) — " + diagnosis
            action = top_score.interpretation + ". " + action

        return Decision(
            overall_severity=top.severity,
            diagnosis=diagnosis,
            recommended_action=action,
            top_signal=top.signal,
            contributing=[f"{r.signal}: {r.detected_event}" for r in active_abnormal],
            clinical_scores=scores,
        )

    def _infer_diagnosis(self, active_abnormal: list[AgentResult]) -> str:
        events = {r.detected_event for r in active_abnormal}
        signals = {r.signal for r in active_abnormal}

        if "Fibrillation Ventriculaire" in events:
            return "ARRÊT CARDIAQUE — Fibrillation Ventriculaire, défibrillation immédiate."
        if "Torsades de Pointes" in events:
            return "Torsades de Pointes — risque proche de FV, magnésium IV + correction facteurs aggravants."
        if "Asystolie" in events:
            return "ASYSTOLIE — réanimation CPR immédiate, recherche cause réversible (4H/H's)."
        if "Tachycardie Ventriculaire" in events:
            return "ARYTHMIE POTENTIELLEMENT MORTELLE — Tachycardie Ventriculaire. Cardioversion si instable."
        if "Sus-décalage ST" in events:
            return "Infarctus du Myocarde Aigu (STEMI) suspecté — activation code STEMI, angiographie en urgence."
        if "Risque de Choc" in events:
            if {"Forte Fièvre", "Hyperpyrexie"} & events:
                return "CHOC SEPTIQUE suspecté — hypotension + fièvre/hyperthermie."
            return "CHOC HYPOVOLÉMIQUE/CARDIOGÉNIQUE — hypotension critique, expansion + vasopresseurs."
        if {"Hypoxémie Sévère", "Hypoxémie"} & events:
            if {"Détresse Respiratoire", "Détresse Respiratoire Sévère"} & events:
                return "INSUFFISANCE RESPIRATOIRE AIGUË — hypoxémie + détresse. Intubation probable."
            return "DÉSATURATION SIGNIFICATIVE — oxygénothérapie plus, évaluation voies respiratoires."
        if "Fibrillation Auriculaire" in events:
            return "Fibrillation Auriculaire — rythme irrégulier, risque thromboembolique (anticoagulation?)."
        if {"Forte Fièvre", "Hyperpyrexie"} & events:
            return "INFECTION SÉVÈRE / SEPSIS suspecté — hyperthermie marquée."
        if len(active_abnormal) >= 3:
            return "INSTABILITÉ MULTI-SYSTÉMIQUE — anomalies concomitantes multiples. Mobilisation équipe pluridisciplinaire."
        if "ICP Critique" in events:
            return "HYPERTENSION INTRACRÂNIENNE CRITIQUE — neurochirurgien urgent, osmothérapie."
        if "Pplat Excessive" in events:
            return "Risk barotrauma — ajuster ventilation protectrice."
        if "IRA Sévère" in events:
            return "INSUFFISANCE RÉNALE AIGUË sévère — adaptation médicamenteuse, néphrologue."

        top = active_abnormal[0]
        return f"{top.detected_event} sur {top.signal} — corrélation clinique recommandée."
