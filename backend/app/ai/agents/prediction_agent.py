"""
app/ai/agents/prediction_agent.py
=================================
Agent de prédiction multi-risque pour réanimation.

Estime les probabilités de :
- Arrêt cardiaque
- Détresse / défaillance respiratoire
- Choc / effondrement hémodynamique
- Sepsis / dégradation infectieuse
- IRA (insuffisance rénale aiguë)
- VAE (événement associé ventilation)
- Dégradation globale multi-horizon (5/15/30/60 min)

MVP : modèle heuristique déterministe basé sur scores gravité + tendances.
Phase 3 : gradient boosting (Scikit-Learn) / réseau de neurones (PyTorch)
entraîné sur MIMIC-IV, derrière la même interface `predict()`.
"""

from __future__ import annotations

from app.ai.schemas import AgentResult, Prediction, VitalsSample, Severity, severity_rank


class PredictionAgent:
    name = "Agent de Prédiction"
    HORIZONS = [5, 15, 30, 60]

    def predict(self, results: list[AgentResult], sample: VitalsSample | None = None) -> Prediction:
        severity_score = sum(severity_rank(r.severity) for r in results) / max(1, len(results))
        rising_count = sum(1 for r in results if r.trend == "rising" and r.severity != "normal")
        base_risk = min(92, severity_score * 18 + rising_count * 6)

        cardiac = [r for r in results if r.signal in ("ECG", "Fréquence Cardiaque", "Pression Artérielle", "Hémodynamique")]
        resp = [r for r in results if r.signal in ("SpO2", "Fréquence Respiratoire", "Ventilation", "ETCO₂")]
        shock = [r for r in results if r.signal in ("Pression Artérielle", "Fréquence Cardiaque", "Hémodynamique", "Température")]
        sepsis = [r for r in results if r.signal in ("Température", "Laboratoire")]
        aki = [r for r in results if r.signal in ("Laboratoire",)]

        cardiac_arrest = self._group_risk(cardiac, base_risk, 1.2)
        resp_failure = self._group_risk(resp, base_risk, 1.1)
        shock_risk = self._group_risk(shock, base_risk, 1.0)
        sepsis_risk = self._group_risk(sepsis, base_risk, 1.15)
        aki_risk = self._group_risk(aki, base_risk, 0.9) + (15 if (sample and sample.lab_cr and sample.lab_cr > 2.0) else 0)
        vae_risk = self._compute_vae(sample) if sample else 15

        deterioration = round(min(96, (base_risk * 0.7 + cardiac_arrest * 0.30) + (rising_count * 3)))

        horizons: dict[str, int] = {}
        for h in self.HORIZONS:
            factor = 1 - (1 / (1 + h / 20))
            horizons[str(h)] = round(min(97, deterioration * (0.5 + factor * 0.5) + vae_risk * 0.1))

        return Prediction(
            cardiac_arrest_risk=round(cardiac_arrest),
            respiratory_failure_risk=round(resp_failure),
            shock_risk=round(shock_risk),
            deterioration_risk=min(96, deterioration),
            sepsis_risk=round(min(96, sepsis_risk + (10 if (sample and sample.temp_core and sample.temp_core > 38.3) else 0))),
            aki_risk=round(min(96, aki_risk)),
            vae_risk=round(min(96, vae_risk)),
            horizons=horizons,
        )

    def _compute_vae(self, sample: VitalsSample | None) -> float:
        if not sample:
            return 15.0
        score = 0.0
        if sample.vent_peep and sample.vent_peep >= 10:
            score += 20
        if sample.vent_pip and sample.vent_pip > 30:
            score += 15
        if sample.etco2 and sample.etco2 > 45:
            score += 10
        if sample.lab_wbc and sample.lab_wbc > 12:
            score += 10
        if sample.temp_core and sample.temp_core > 38.5:
            score += 10
        if sample.vent_mode and "V" in sample.vent_mode:
            score += 5
        return min(95.0, max(5.0, score))

    def _group_risk(self, group: list[AgentResult], base_risk: float, weight: float) -> float:
        if not group:
            return base_risk * 0.35 * weight
        group_score = sum(severity_rank(r.severity) for r in group) / len(group)
        return min(95.0, (group_score * 22 + base_risk * 0.35) * weight)
