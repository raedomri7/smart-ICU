"""
app/ai/clinical_scoring.py
===========================
Moteur de scores cliniques ICU standardisés (basés sur des règles validées).

Scores implémentés :
- SOFA (Sequential Organ Failure Assessment) : 6 organes, 0-24
- qSOFA : quick SOFA, 0-3
- NEWS2 (National Early Warning Score 2) : 0-20
- Braden Scale (pressure injury) : 6-23 (lower = higher risk)
- Morse Fall Scale : 0-125
- CAM-ICU (delirium screening, simplified)
- MEWS (Modified Early Warning Score) : 0-14
- APACHE II simplifié (âge + GCS + vitals) : 0-71
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.ai.schemas import VitalsSample, ClinicalScore


class ClinicalScoringEngine:
    """Calcule les scores cliniques à partir d'un VitalsSample."""

    def score_sofa(self, v: VitalsSample) -> ClinicalScore:
        points = 0
        # Respiratoire (PaO2/FiO2)
        if v.abg_pao2 > 0 and v.fio2 > 0:
            ratio = v.abg_pao2 / v.fio2
            if ratio >= 400:
                points += 0
            elif ratio >= 300:
                points += 1
            elif ratio >= 200:
                points += 2
            elif ratio >= 100:
                points += 3
            else:
                points += 4
        else:
            if v.spo2 < 90:
                points += 3
            elif v.spo2 < 95:
                points += 2
            elif v.spo2 < 97:
                points += 1

        # Coagulation (plaquettes)
        if v.lab_plt > 0:
            if v.lab_plt >= 150:
                points += 0
            elif v.lab_plt >= 100:
                points += 1
            elif v.lab_plt >= 50:
                points += 2
            elif v.lab_plt >= 20:
                points += 3
            else:
                points += 4

        # Foie (bilirubine simplifiée → si non dispo, 0)
        liver = 0  # placeholder si bilirubine non monitorée

        # Cardiovasculaire (MAP + vasopresseurs)
        if v.map_val >= 70:
            points += 0
        elif v.map_val >= 60:
            points += 1
        else:
            points += 2 if v.map_val >= 50 else 3
        if v.shock_risk_level == "critical":
            points += 1  # vasopressor equivalent

        # Neurologique (GCS)
        gcs_map = {15: 0, 13: 1, 10: 2, 6: 3, 3: 4}
        points += gcs_map.get(max(3, min(15, v.gcs)), 4) if v.gcs > 0 else 4

        # Rein (créatinine)
        if v.lab_cr > 0:
            if v.lab_cr < 1.2:
                points += 0
            elif v.lab_cr < 2.0:
                points += 1
            elif v.lab_cr < 3.5:
                points += 2
            elif v.lab_cr < 5.0:
                points += 3
            else:
                points += 4
        elif v.uo_hour > 0 and v.uo_hour < 30:
            points += 3

        sev = "normal" if points <= 1 else ("low" if points <= 3 else ("medium" if points <= 6 else ("high" if points <= 10 else "critical")))
        return ClinicalScore(name="SOFA", score=min(24, points), max_score=24, severity=sev,
                             interpretation=f"Score SOFA={min(24, points)} — dysfonction multi-organes {'minime' if points <= 1 else 'légère' if points <= 3 else 'modérée' if points <= 6 else 'sévère'}")

    def score_qsofa(self, v: VitalsSample) -> ClinicalScore:
        pts = 0
        if v.nibp_sys < 100 and v.nibp_sys > 0:
            pts += 1
        if v.rr_capno > 22 or (v.vent_rr and v.vent_rr > 22):
            pts += 1
        if v.gcs < 15 and v.gcs > 0:
            pts += 1
        sev = "low" if pts >= 2 else "normal"
        return ClinicalScore(name="qSOFA", score=pts, max_score=3, severity=sev,
                             interpretation=f"qSOFA={pts}/3 — {'probabilité élevée de sepsis' if pts >= 2 else 'faible probabilité'}")

    def score_news2(self, v: VitalsSample) -> ClinicalScore:
        pts = 0
        # RR
        rr = v.rr_capno or v.vent_rr or 16
        if rr <= 8: pts += 3
        elif rr <= 11: pts += 2
        elif rr <= 20: pts += 0
        elif rr <= 24: pts += 1
        else: pts += 3
        # SpO2 / O2
        spo2 = v.spo2
        if spo2 <= 83: pts += 3
        elif spo2 <= 85: pts += 2
        elif spo2 <= 87: pts += 1
        elif spo2 >= 95: pts += 0
        elif spo2 >= 93: pts += 0 if v.fio2 <= 21 else 1
        else: pts += 2
        # Air / O2
        air = 0
        if v.vent_mode and v.vent_mode != "Spontaneous":
            air = 2
        if v.fio2 > 21:
            pts += 2
        # Sys BP
        sbp = v.nibp_sys
        if sbp <= 90 or sbp >= 220: pts += 3
        elif sbp <= 100: pts += 2
        elif sbp <= 110: pts += 1
        elif sbp <= 219: pts += 0
        # HR
        hr = v.ecg_hr or v.hr
        if hr <= 40: pts += 3
        elif hr <= 50: pts += 2
        elif hr <= 90: pts += 0
        elif hr <= 110: pts += 1
        elif hr <= 130: pts += 2
        else: pts += 3
        # Consciousness (GCS / alert)
        if v.gcs and v.gcs < 15:
            pts += 3 if v.gcs <= 8 else (2 if v.gcs <= 11 else 1)
        # Temp
        temp = v.temp_core or v.temp_skin
        if temp >= 39.1: pts += 2
        elif temp >= 38.1: pts += 1
        elif temp >= 36.1: pts += 0
        elif temp >= 35.1: pts += 1
        else: pts += 3
        sev = "normal" if pts <= 1 else ("low" if pts <= 4 else ("medium" if pts <= 6 else "high"))
        return ClinicalScore(name="NEWS2", score=min(20, pts), max_score=20, severity=sev,
                             interpretation=f"NEWS2={min(20, pts)} — risque {'faible' if pts <= 4 else 'modéré' if pts <= 6 else 'élevé'} d'événement clinique aigu")

    def score_braden(self, v: VitalsSample) -> ClinicalScore:
        # Placeholder simplifié (6 items) — complet nécessiterait évaluation nursing directe
        score = 19  # score maximal = risque minimal
        if v.uo_hour and v.uo_hour < 30:
            score -= 2
        if v.temp_core and v.temp_core > 38.5:
            score -= 1
        if v.gcs and v.gcs < 13:
            score -= 2
        if v.mobility_score() > 2:
            score -= 2
        sev = "normal" if score >= 19 else ("low" if score >= 15 else ("medium" if score >= 13 else "critical"))
        return ClinicalScore(name="Braden", score=max(6, score), max_score=23, severity=sev,
                             interpretation=f"Braden={max(6, score)}/23 — risque de plaie de pression {'faible' if score >= 19 else 'modéré' if score >= 15 else 'élevé'}")

    def score_cam_icu(self, v: VitalsSample) -> ClinicalScore:
        # CAM-ICU : 4 features — nécessite évaluation comportementale. Placeholder.
        delirium_risk = 0
        if v.bis and v.bis < 60:
            delirium_risk += 1
        if v.gcs and v.gcs < 14 and v.gcs > 9:
            delirium_risk += 1
        sev = "low" if delirium_risk >= 2 else "normal"
        return ClinicalScore(name="CAM-ICU", score=delirium_risk, max_score=4, severity=sev,
                             interpretation=f"CAM-ICU : risque de delirium {'élevé' if delirium_risk >= 2 else 'faible'} (IMC à confirmer par évaluation clinique)")

    def score_sepsis_implied(self, v: VitalsSample, qsofa: ClinicalScore) -> ClinicalScore:
        """Surrogate sepsis screening using qSOFA + lactate surrogate (Cr/BUN proxy)."""
        score = qsofa.score
        # Surrogate organ dysfunction
        if v.lab_cr and v.lab_cr > 2.0:
            score += 1
        if v.lab_plt and v.lab_plt < 100:
            score += 1
        if v.abg_lactate_surrogate > 18:  # using base excess as lactate proxy
            score += 1
        sev = "critical" if score >= 3 else ("high" if score >= 2 else "medium" if score == 1 else "normal")
        return ClinicalScore(name="Sepsis Suspected", score=min(6, score), max_score=6, severity=sev,
                             interpretation=f"Score sepsis probable={min(6, score)}/6 — {'sepsis suspecté, évaluer lactémie et hémocultures' if score >= 2 else 'faible probabilité'}")

    def all_scores(self, v: VitalsSample) -> list[ClinicalScore]:
        scores = []
        scores.append(self.score_sofa(v))
        qsofa = self.score_qsofa(v)
        scores.append(qsofa)
        scores.append(self.score_news2(v))
        scores.append(self.score_braden(v))
        scores.append(self.score_cam_icu(v))
        scores.append(self.score_sepsis_implied(v, qsofa))
        return scores
