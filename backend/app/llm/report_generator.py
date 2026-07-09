"""
app/llm/report_generator.py
============================
Moteur de génération de rapports médicaux hospitaliers pour service de
réanimation. Formats : progrès quotidien, transfert, famille, code status,
nursing, laboratoire.

Tous les rapports sont générés localement en Markdown — sans IA externe
(hors Gemini optionnel pour reformulation/relecture en tâche de fond).
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Optional

from app.ai.schemas import AISnapshot, VitalsSample
from app.ai.clinical_scoring import ClinicalScoringEngine


class ReportGenerator:
    def __init__(self) -> None:
        self._scoring = ClinicalScoringEngine()

    def generate_progress_note(self, snapshot: AISnapshot, history: list[dict] | None = None) -> str:
        v = snapshot.vitals
        d = snapshot.decision
        p = snapshot.prediction
        scores = snapshot.decision.clinical_scores or self._scoring.all_scores(v)
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        trends = self._format_trends(history or [])

        lines = [
            f"# NOTE DE PROGRÈS — SERVICE DE RÉANIMATION",
            f"## Patient : {v.patient_id}  |  {now}",
            f"",
            f"### ÉTAT CLINIQUE ACTUEL",
            f"- **Scénario** : {v.scenario}",
            f"- **Diagnostic actuel** : {d.diagnosis}",
            f"- **Niveau de risque global** : {d.overall_severity.upper()}",
            f"- **Action recommandée** : {d.recommended_action}",
            "",
        ]

        if d.contributing:
            lines.append(f"### FACTEURS CONTRIBUTIFS")
            for c in d.contributing:
                lines.append(f"- {c}")
            lines.append("")

        # Vitals
        lines.extend([
            "### PARAMÈTRES VITAUX",
            "| Paramètre | Valeur | Unité | Tendance |",
            "|-----------|--------|-------|----------|",
            f"| FC (ECG) | {v.ecg_hr or v.hr} | bpm | {trends.get('hr','—')} |",
            f"| SpO₂ | {v.spo2} | % | {trends.get('spo2','—')} |",
            f"| PI | {v.pi:.1f} | % | — |",
            f"| PA (NIBP) | {v.nibp_sys}/{v.nibp_dia} | mmHg | {trends.get('sbp','—')} |",
            f"| PAM | {v.map_val} | mmHg | — |",
            f"| Température (core) | {v.temp_core:.1f} | °C | {trends.get('temp','—')} |",
            f"| Température (peau) | {v.temp_skin:.1f} | °C | — |",
            f"| Gradient T | {v.temp_gradient:.1f} | °C | — |",
            f"| ETCO₂ | {v.etco2} | mmHg | — |",
            f"| RR (capno) | {v.rr_capno or v.vent_rr} | /min | — |",
            f"| FiO₂ | {v.fio2} | % | — |",
            "",
            "### VENTILATION MÉCANIQUE",
            f"- **Mode** : {v.vent_mode}",
            f"- **FiO₂** : {v.vent_fio2}%",
            f"- **PEEP** : {v.vent_peep} cmH₂O",
            f"- **Vt** : {v.vent_vt} mL",
            f"- **RR** : {v.vent_rr} /min",
            f"- **PIP** : {v.vent_pip} cmH₂O",
            f"- **MV** : {v.vent_mv:.1f} L/min",
            f"- **Pplat** : {v.vent_pplat:.1f} cmH₂O",
            "",
            "### HÉMODYNAMIQUE",
            f"- **CvP** : {v.cvp:.1f} mmHg" if v.cvp > 0 else "",
            f"- **CO** : {v.co:.1f} L/min" if v.co > 0 else "",
            f"- **CI** : {v.ci:.1f} L/min/m²" if v.ci > 0 else "",
            f"- **ICD** : {v.icp:.0f} mmHg" if v.icp > 0 else "",
            f"- **PCP** : {v.cpp_val:.0f} mmHg" if v.cpp_val > 0 else "",
            f"- **BIS** : {v.bis}" if v.bis > 0 else "",
            "",
            "### LABORATOIRE",
            f"- **Hb** : {v.lab_hb:.1f} g/dL  **Plt** : {v.lab_plt:.0f} K/µL  **WBC** : {v.lab_wbc:.1f} K/µL",
            f"- **Na** : {v.lab_na:.0f}  **K** : {v.lab_k:.1f}  **Cr** : {v.lab_cr:.1f}  **Glu** : {v.lab_glu:.0f}",
            f"- **pH** : {v.abg_ph:.2f}  **PaO₂** : {v.abg_pao2:.0f}  **PaCO₂** : {v.abg_paco2:.0f}  **HCO₃** : {v.abg_hco3:.1f}",
            f"- **INR** : {v.coag_inr:.1f}" if v.coag_inr > 0 else "",
            "",
        ])

        lines.extend([
            "### SCORES CLINIQUES",
            "| Score | Valeur | Max | Gravité | Interprétation |",
            "|-------|--------|-----|---------|----------------|",
        ])
        for s in scores:
            lines.append(f"| {s.name} | {s.score} | {s.max_score} | {s.severity.upper()} | {s.interpretation} |")

        lines.extend([
            "| Horizon | Risque |",
            "|---------|--------|",
        ])
        for h, r in p.horizons.items():
            lines.append(f"| {h} min | {r}% |")
        lines.append("")

        return "\n".join([l for l in lines if l is not None])

    def generate_transfer_summary(self, snapshot: AISnapshot) -> str:
        d = snapshot.decision
        p = snapshot.prediction
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        return "\n".join([
            f"# RÉSUMÉ DE TRANSFERT — SERVICE DE RÉANIMATION",
            f"## {snapshot.vitals.patient_id}  |  {now}",
            "",
            f"### DIAGNOSTIC PRINCIPAL",
            d.diagnosis,
            "",
            f"### GRAVITÉ & RISQUES",
            f"- Gravité globale : {d.overall_severity.upper()}",
            f"- Risque de dégradation : {p.deterioration_risk}%",
            f"- Risque arrêt cardiaque : {p.cardiac_arrest_risk}%",
            "",
            f"### CONSTANTES CLÉS À TRANSMETTRE",
            f"- FC : {snapshot.vitals.ecg_hr or snapshot.vitals.hr} bpm",
            f"- SpO₂ : {snapshot.vitals.spo2}% (FiO₂ {snapshot.vitals.fio2}%)",
            f"- PA : {snapshot.vitals.nibp_sys}/{snapshot.vitals.nibp_dia} (PAM {snapshot.vitals.map_val})",
            f"- Température : {snapshot.vitals.temp_core:.1f}°C",
            f"- Ventilation : {snapshot.vitals.vent_mode}, Vt {snapshot.vitals.vent_vt} mL, PEEP {snapshot.vitals.vent_peep}",
            f"- GCS : {snapshot.vitals.gcs}",
            "",
            f"### ACTIONS URGENTES",
            d.recommended_action,
            "",
            f"---",
            f"*Rapport généré automatiquement — {now}*",
        ])

    def generate_nursing_note(self, snapshot: AISnapshot) -> str:
        v = snapshot.vitals
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        return "\n".join([
            f"# NOTE DE SURVEILLANCE INFIRMIÈRE",
            f"## {v.patient_id}  |  {now}",
            "",
            "### VIGILANCE",
            f"- Rythme ECG : {v.ecg_rhythm} (FC {v.ecg_hr or v.hr} bpm) — qualité signal {v.ecg_qual:.0%}",
            f"- Moniteur : dérivation {v.ecg_waveform_type}",
            f"- Qualité signal ECG : {v.ecg_qual:.0%}" if v.ecg_qual > 0 else "",
            "",
            "### VENTILATION",
            f"- Mode : {v.vent_mode}",
            f"- Paramètres : FiO₂ {v.vent_fio2}%, PEEP {v.vent_peep} cmH₂O, Vt {v.vent_vt} mL, RR {v.vent_rr}/min",
            f"- SpO₂ : {v.spo2}% | ETCO₂ : {v.etco2} mmHg | RR capno : {v.rr_capno}/min",
            "",
            "### HÉMODYNAMIQUE",
            f"- NIBP : {v.nibp_sys}/{v.nibp_dia} (PAM {v.map_val}) — cycle {v.nibp_cycle} min",
            f"- CvP : {v.cvp:.1f} mmHg" if v.cvp else "",
            f"- Diurèse : {v.uo_hour} mL/h (cumul 6h : {v.uo_6h} mL, 24h : {v.uo_24h} mL)",
            "",
            f"### SURVEILLANCE NEUROLOGIQUE",
            f"- GCS : {v.gcs}/15",
            f"- BIS : {v.bis}" if v.bis else "",
            f"- ICP : {v.icp:.0f} mmHg | CPP : {v.cpp_val:.0f} mmHg" if v.icp > 0 else "",
            "",
            f"### ALERTES ACTIVES",
            f"- {snapshot.decision.diagnosis}",
            f"- Action : {snapshot.decision.recommended_action}",
            "",
            f"---",
            f"*Infirmier(ère)  |  {now}*",
        ])

    def generate_lab_summary(self, v: VitalsSample) -> str:
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        lines = [
            f"# COMPTE RENDU DE LABORATOIRE — RÉANIMATION",
            f"## {v.patient_id}  |  {now}",
            "",
            "## HÉMATOLOGIE",
            f"- Hémoglobine : {v.lab_hb:.1f} g/dL  (normale 12-16)",
            f"- Hématocrite : {v.lab_hct:.1f}%  (normal 36-46%)",
            f"- Leucocytes : {v.lab_wbc:.1f} K/µL  (normal 4-11)",
            f"- Plaquettes : {v.lab_plt:.0f} K/µL  (normal 150-450)",
            "",
            "## BIOCHIMIE",
            f"- Sodium : {v.lab_na:.0f} mEq/L  (normal 135-145)",
            f"- Potassium : {v.lab_k:.1f} mEq/L  (normal 3.5-5.0)",
            f"- Créatinine : {v.lab_cr:.1f} mg/dL  (normal 0.7-1.3)",
            f"- BUN : {v.lab_bun:.1f} mg/dL  (normal 7-20)",
            f"- Glucose : {v.lab_glu:.0f} mg/dL  (normal 70-110)",
            "",
            "## GAZ DU SANG ARTÉRIEL",
            f"- pH : {v.abg_ph:.3f}  (normal 7.35-7.45)",
            f"- PaO₂ : {v.abg_pao2:.0f} mmHg  (normal 80-100)",
            f"- PaCO₂ : {v.abg_paco2:.0f} mmHg  (normal 35-45)",
            f"- HCO₃⁻ : {v.abg_hco3:.1f} mEq/L  (normal 22-26)",
            f"- Sat O₂ : {v.abg_sat:.0f}%  (normal 95-100)",
            f"- BE : {v.abg_be:.1f} mEq/L  (normal -2 à +2)",
            "",
            "## COAGULATION",
            f"- PT : {v.coag_pt:.1f} sec" if v.coag_pt else "",
            f"- INR : {v.coag_inr:.1f}" if v.coag_inr else "",
            f"- aPTT : {v.coag_aptt:.0f} sec" if v.coag_aptt else "",
            "",
            f"---",
            f"*Rapport généré automatiquement — {now} — Aide à la décision, validation clinique requise.*",
        ]
        return "\n".join([l for l in lines if l])

    def generate_alert_report(self, alerts: list[dict]) -> str:
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        lines = [
            f"# RAPPORT D'ALERTES CLINIQUES",
            f"## {now}",
            "",
        ]
        for a in alerts:
            lines.extend([
                f"### {a['event']} — {a['signal']}",
                f"- **Gravité** : {a['severity'].upper()}",
                f"- **Confiance IA** : {a['confidence']}%",
                f"- **Message** : {a['message']}",
                f"- **Statut** : {a['status']}",
                "",
            ])
        lines.append("---")
        lines.append("*Rapport généré automatiquement — ICU Smart Monitoring*")
        return "\n".join(lines)

    def generate_family_summary(self, snapshot: AISnapshot) -> str:
        v = snapshot.vitals
        d = snapshot.decision
        p = snapshot.prediction
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        return "\n".join([
            f"# RÉSUMÉ POUR LA FAMILLE",
            f"## Patient {v.patient_id} — {now}",
            "",
            "### SITUATION ACTUELLE",
            f"**{d.diagnosis}**",
            "",
            "### CONSTANTES PRINCIPALES",
            f"- Cœur : {v.ecg_hr or v.hr} battements par minute",
            f"- Oxygénation : {v.spo2}% (saturation en oxygène)",
            f"- Tension artérielle : {v.nibp_sys}/{v.nibp_dia}",
            f"- Température : {v.temp_core:.1f}°C",
            f"- Ventilation : {v.vent_mode}, machine en place pour aider la respiration",
            "",
            "### CE QUE FAIT L'ÉQUIPE",
            d.recommended_action,
            "",
            "### QUESTIONS À POSER À L'ÉQUIPE",
            "- Quel est le plan de traitement pour les prochaines 24h ?",
            "- Quels sont les risques principaux pour le patient ?",
            "- Comment puis-je soutenir mon proche ?",
            "",
            "> Ce document est un résumé simplifié destiné à la famille. ",
            "> Les décisions médicales sont prises par l'équipe soignante en fonction de l'évaluation clinique complète.",
            "",
            f"---",
            f"*Document généré le {now} — ICU Smart Monitoring — Ce document complète mais ne remplace pas les informations données par l'équipe médicale.*",
        ])

    def generate_code_status(self, snapshot: AISnapshot) -> str:
        v = snapshot.vitals
        now = datetime.now().strftime("%d/%m/%Y %H:%H")
        return "\n".join([
            f"# DOCUMENT DE CODE STATUS",
            f"## Patient {v.patient_id}  |  {now}",
            "",
            "### ORDRE DE NON-RÉANIMATION (ONR)",
            "- [ ] Réanimation cardiopulmonaire (RCP) : ____",
            "- [ ] Intubation orotrachéale : ____",
            "- [ ] Traitement par vasopresseurs : ____",
            "- [ ] Épuration extrarénale (EER) : ____",
            "- [ ] Autotransfusion : ____",
            "",
            "### VOLONTÉS DU PATIENT / FAMILLE",
            "- [ ] Patient capable de décider",
            "- [ ] Personne de confiance désignée",
            "- [ ] Directives anticipées connues",
            "",
            "### OBSERVATIONS",
            f"Diagnostic actuel : {snapshot.decision.diagnosis}",
            f"Niveau de conscience (GCS) : {v.gcs}/15",
            f"Gravité globale : {snapshot.decision.overall_severity.upper()}",
            "",
            "### SIGNATURES",
            "- Médecin responsable : _________________ Date : _______",
            "- Infirmier(ère) : _____________________ Date : _______",
            "- Famille / Représentant légal : ________ Date : _______",
            "",
            f"---",
            f"*Document généré automatiquement — {now} — ICU Smart Monitoring*",
        ])

    def _format_trends(self, history: list[dict]) -> dict[str, str]:
        trends = {}
        for key in ["hr", "spo2", "sbp", "dbp", "temp"]:
            values = [h.get(key) for h in history[-5:] if h.get(key)]
            if len(values) >= 2:
                if values[-1] > values[0] + 2:
                    trends[key] = "↑"
                elif values[-1] < values[0] - 2:
                    trends[key] = "↓"
                else:
                    trends[key] = "→"
            else:
                trends[key] = "—"
        return trends
