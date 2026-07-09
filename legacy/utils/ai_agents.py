"""
utils/ai_agents.py
====================
Architecture d'agents IA indépendants pour le monitoring ICU.

Chaque signal physiologique a son propre agent dédié :
    - ECGAgent
    - SpO2Agent
    - HeartRateAgent
    - TemperatureAgent
    - BloodPressureAgent
    - RespiratoryAgent

Chaque agent :
    - reçoit les données en temps réel
    - détecte les anomalies
    - estime la sévérité (normal/low/medium/high/critical)
    - génère une explication lisible par l'humain
    - propose une action recommandée
    - retourne un score de confiance

Le ClinicalDecisionAgent agrège les sorties de tous les agents en :
    - un diagnostic unifié
    - un niveau de risque global
    - une action recommandée prioritaire

Le PredictionAgent estime le risque de détérioration à court terme
(5 / 15 / 30 / 60 minutes) en fonction de la tendance récente et
des niveaux de sévérité actuels.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import random

from utils.ecg_generator import ECG_CLINICAL_INFO


# ======================================================================
# Structure de résultat partagée
# ======================================================================
@dataclass
class AgentResult:
    agent_name: str
    signal: str
    value: str
    detected_event: str          # ex: "Tachycardie", "Normal", "Hypoxémie"
    confidence: int               # 0-100
    severity: str                 # normal / low / medium / high / critical
    explanation: str
    recommendation: str
    trend: str = "stable"         # rising / falling / stable


SEVERITY_RANK = {'normal': 0, 'low': 1, 'medium': 2, 'high': 3, 'critical': 4}


# ======================================================================
# Agents individuels par signal
# ======================================================================
class ECGAgent:
    """Analyse la classification du rythme ECG fournie par le moteur de tracé."""

    name = "Agent ECG"

    def analyze(self, rhythm_type: str, anomaly_type: Optional[str]) -> AgentResult:
        if anomaly_type is None or rhythm_type == 'normal':
            return AgentResult(
                agent_name=self.name, signal="ECG", value="Rythme Sinusal Normal",
                detected_event="Normal", confidence=98, severity="normal",
                explanation="Morphologie P-QRS-T régulière, axe normal, aucun battement ectopique.",
                recommendation="Poursuivre la surveillance de routine.",
                trend="stable"
            )

        info = ECG_CLINICAL_INFO.get(anomaly_type, {
            'meaning': 'Morphologie de battement anormale non classifiée détectée.',
            'severity': 'medium', 'base_confidence': 80
        })
        confidence = min(99, info['base_confidence'] + random.randint(-3, 3))
        recommendations = {
            'critical': "Notification immédiate du médecin. Préparer une intervention d'urgence.",
            'high': "Évaluation cardiologique urgente recommandée dans les 15 minutes.",
            'medium': "Augmenter la fréquence de surveillance. Notifier le médecin traitant.",
            'low': "Poursuivre l'observation étroite.",
        }
        return AgentResult(
            agent_name=self.name, signal="ECG", value=anomaly_type,
            detected_event=anomaly_type, confidence=confidence,
            severity=info['severity'], explanation=info['meaning'],
            recommendation=recommendations.get(info['severity'], "Surveiller étroitement."),
            trend="rising" if info['severity'] in ('high', 'critical') else "stable"
        )


class HeartRateAgent:
    name = "Agent Fréquence Cardiaque"

    def analyze(self, hr: int, prev_hr: int = None) -> AgentResult:
        trend = "stable"
        if prev_hr is not None:
            if hr > prev_hr + 3:
                trend = "rising"
            elif hr < prev_hr - 3:
                trend = "falling"

        if hr > 150 or hr < 35:
            severity, event = "critical", "Anomalie Sévère de Fréquence"
            expl = f"FC={hr} bpm est critiquement hors des limites physiologiques sûres."
            rec = "Intervention immédiate requise — envisager une réponse cardiaque d'urgence."
        elif hr > 120 or hr < 45:
            severity, event = "high", "Tachy/Bradycardie Marquée"
            expl = f"FC={hr} bpm indique une anomalie de fréquence significative."
            rec = "Notifier le médecin. Réévaluer dans 5 minutes."
        elif hr > 100:
            severity, event = "medium", "Tachycardie"
            expl = f"FC={hr} bpm dépasse la plage de repos normale (60-100 bpm)."
            rec = "Surveiller les déclencheurs : douleur, fièvre, anxiété, hypovolémie."
        elif hr < 60:
            severity, event = "medium", "Bradycardie"
            expl = f"FC={hr} bpm est inférieure à la plage de repos normale."
            rec = "Évaluer l'effet médicamenteux, la stimulation vagale ou un bloc de conduction."
        else:
            severity, event = "normal", "Normal"
            expl = f"FC={hr} bpm dans la plage de repos normale (60-100 bpm)."
            rec = "Poursuivre la surveillance de routine."

        confidence = 95 if severity != 'normal' else 99
        return AgentResult(self.name, "Fréquence Cardiaque", f"{hr} bpm", event, confidence, severity, expl, rec, trend)


class SpO2Agent:
    name = "Agent SpO2"

    def analyze(self, spo2: int, prev_spo2: int = None) -> AgentResult:
        trend = "stable"
        if prev_spo2 is not None:
            if spo2 < prev_spo2 - 1:
                trend = "falling"
            elif spo2 > prev_spo2 + 1:
                trend = "rising"

        if spo2 < 85:
            severity, event = "critical", "Hypoxémie Sévère"
            expl = f"SpO₂={spo2}% — déficience critique en oxygène, risque de lésion organique."
            rec = "Administrer immédiatement de l'oxygène à haut débit. Préparer une intubation possible."
        elif spo2 < 90:
            severity, event = "high", "Hypoxémie"
            expl = f"SpO₂={spo2}% — désaturation en oxygène significative."
            rec = "Augmenter l'oxygène supplémentaire. Réévaluer les voies respiratoires."
        elif spo2 < 95:
            severity, event = "medium", "Désaturation Légère"
            expl = f"SpO₂={spo2}% — sous la plage cible, compromission respiratoire précoce possible."
            rec = "Surveiller étroitement. Envisager un apport en oxygène supplémentaire."
        else:
            severity, event = "normal", "Normal"
            expl = f"SpO₂={spo2}% — oxygénation adéquate."
            rec = "Poursuivre la surveillance de routine."

        confidence = 97 if severity != 'normal' else 99
        return AgentResult(self.name, "SpO2", f"{spo2}%", event, confidence, severity, expl, rec, trend)


class TemperatureAgent:
    name = "Agent Température"

    def analyze(self, temp: float, prev_temp: float = None) -> AgentResult:
        trend = "stable"
        if prev_temp is not None:
            if temp > prev_temp + 0.1:
                trend = "rising"
            elif temp < prev_temp - 0.1:
                trend = "falling"

        if temp >= 40.0:
            severity, event = "critical", "Hyperpyrexie"
            expl = f"Temp={temp:.1f}°C — hyperthermie extrême, risque de lésion organique et de convulsions."
            rec = "Initier un refroidissement actif immédiatement. Investiguer une source de sepsis/infection."
        elif temp >= 39.0:
            severity, event = "high", "Forte Fièvre"
            expl = f"Temp={temp:.1f}°C — forte fièvre, infection sévère ou sepsis possible."
            rec = "Administrer des antipyrétiques. Hémocultures recommandées."
        elif temp >= 38.0:
            severity, event = "medium", "Fièvre"
            expl = f"Temp={temp:.1f}°C — fièvre présente, processus infectieux/inflammatoire possible."
            rec = "Surveiller la tendance. Envisager antipyrétiques et bilan infectieux."
        elif temp < 35.0:
            severity, event = "critical", "Hypothermie Sévère"
            expl = f"Temp={temp:.1f}°C — hypothermie sévère, risque d'arythmie cardiaque."
            rec = "Initier un réchauffement actif. Surveillance cardiaque continue requise."
        elif temp < 36.0:
            severity, event = "high", "Hypothermie"
            expl = f"Temp={temp:.1f}°C — sous la plage normale."
            rec = "Appliquer des mesures de réchauffement. Surveiller frissons et arythmie."
        else:
            severity, event = "normal", "Normal"
            expl = f"Temp={temp:.1f}°C — dans la plage normale (36.1-37.5°C)."
            rec = "Poursuivre la surveillance de routine."

        confidence = 96 if severity != 'normal' else 99
        return AgentResult(self.name, "Température", f"{temp:.1f}°C", event, confidence, severity, expl, rec, trend)


class BloodPressureAgent:
    name = "Agent Pression Artérielle"

    def analyze(self, sbp: int, dbp: int, prev_sbp: int = None) -> AgentResult:
        trend = "stable"
        if prev_sbp is not None:
            if sbp > prev_sbp + 3:
                trend = "rising"
            elif sbp < prev_sbp - 3:
                trend = "falling"

        map_val = round(dbp + (sbp - dbp) / 3)

        if sbp < 80 or map_val < 60:
            severity, event = "critical", "Risque de Choc"
            expl = f"PA={sbp}/{dbp} mmHg (PAM {map_val}) — perfusion organique inadéquate, risque de choc."
            rec = "Initier une réanimation liquidienne/vasopresseurs. Notifier le médecin immédiatement."
        elif sbp < 90:
            severity, event = "high", "Hypotension"
            expl = f"PA={sbp}/{dbp} mmHg — hypotension significative."
            rec = "Évaluer le statut volémique. Envisager des fluides IV."
        elif sbp > 180 or dbp > 120:
            severity, event = "critical", "Crise Hypertensive"
            expl = f"PA={sbp}/{dbp} mmHg — urgence hypertensive, risque de lésion d'organe cible."
            rec = "Thérapie antihypertensive immédiate. Évaluer les lésions d'organes cibles."
        elif sbp > 140:
            severity, event = "medium", "Hypertension"
            expl = f"PA={sbp}/{dbp} mmHg — élevée au-dessus de la plage normale."
            rec = "Surveiller la tendance. Réviser le traitement antihypertenseur."
        else:
            severity, event = "normal", "Normal"
            expl = f"PA={sbp}/{dbp} mmHg (PAM {map_val}) — dans la plage normale."
            rec = "Poursuivre la surveillance de routine."

        confidence = 94 if severity != 'normal' else 98
        return AgentResult(self.name, "Pression Artérielle", f"{sbp}/{dbp}", event, confidence, severity, expl, rec, trend)


class RespiratoryAgent:
    name = "Agent Respiratoire"

    def analyze(self, rr: int, spo2: int = None, prev_rr: int = None) -> AgentResult:
        trend = "stable"
        if prev_rr is not None:
            if rr > prev_rr + 1:
                trend = "rising"
            elif rr < prev_rr - 1:
                trend = "falling"

        if rr > 30 or rr < 8:
            severity, event = "critical", "Détresse Respiratoire Sévère"
            expl = f"FR={rr} resp/min — anomalie critique, défaillance respiratoire imminente."
            rec = "Préparer un support ventilatoire. Évaluation médicale immédiate."
        elif rr > 24 or rr < 10:
            severity, event = "high", "Détresse Respiratoire"
            expl = f"FR={rr} resp/min — anomalie marquée du rythme respiratoire."
            rec = "Réévaluer les voies respiratoires et l'oxygénation. Notifier le médecin."
        elif rr > 20:
            severity, event = "medium", "Tachypnée"
            expl = f"FR={rr} resp/min — élevée au-dessus de la plage normale (12-20)."
            rec = "Investiguer la cause : douleur, anxiété, hypoxie, acidose métabolique."
        elif rr < 12:
            severity, event = "medium", "Bradypnée"
            expl = f"FR={rr} resp/min — sous la plage normale."
            rec = "Évaluer le niveau de sédation et l'état du SNC."
        else:
            severity, event = "normal", "Normal"
            expl = f"FR={rr} resp/min — dans la plage normale (12-20)."
            rec = "Poursuivre la surveillance de routine."

        confidence = 93 if severity != 'normal' else 98
        return AgentResult(self.name, "Fréquence Respiratoire", f"{rr} /min", event, confidence, severity, expl, rec, trend)


# ======================================================================
# Agent de Décision Clinique — agrège tous les signaux
# ======================================================================
class ClinicalDecisionAgent:
    name = "Agent de Décision Clinique"

    def decide(self, results: List[AgentResult]) -> dict:
        sorted_results = sorted(results, key=lambda r: SEVERITY_RANK[r.severity], reverse=True)
        top = sorted_results[0]
        overall_severity = top.severity

        active_abnormal = [r for r in sorted_results if r.severity != 'normal']

        if not active_abnormal:
            diagnosis = "Aucune anomalie aiguë détectée. Patient stable."
            action = "Poursuivre la surveillance de routine."
        else:
            diagnosis = self._infer_diagnosis(active_abnormal)
            action = top.recommendation

        return {
            'overall_severity': overall_severity,
            'diagnosis': diagnosis,
            'recommended_action': action,
            'contributing_agents': active_abnormal,
            'top_concern': top,
        }

    def _infer_diagnosis(self, active_abnormal: List[AgentResult]) -> str:
        events = {r.detected_event for r in active_abnormal}

        if 'Hypoxémie Sévère' in events or 'Hypoxémie' in events:
            if 'Détresse Respiratoire' in events or 'Détresse Respiratoire Sévère' in events:
                return "Possible Insuffisance Respiratoire Aiguë — hypoxémie avec détresse respiratoire."
        if 'Risque de Choc' in events:
            if {'Fièvre', 'Forte Fièvre', 'Hyperpyrexie'} & events:
                return "Possible Choc Septique — hypotension avec fièvre/hyperthermie."
            return "Possible Choc Hypovolémique/Cardiogénique — hypotension critique."
        if 'Tachycardie Ventriculaire' in events:
            return "Arythmie Potentiellement Mortelle — Tachycardie Ventriculaire, risque d'arrêt cardiaque."
        if 'Sus-décalage ST' in events:
            return "Possible Infarctus du Myocarde Aigu (STEMI)."
        if 'Fibrillation Auriculaire' in events:
            return "Fibrillation Auriculaire — rythme irrégulier, risque thromboembolique."
        if {'Forte Fièvre', 'Hyperpyrexie'} & events:
            return "Possible Infection Sévère / Sepsis — hyperthermie marquée."
        if len(active_abnormal) >= 3:
            return "Instabilité Multi-Systémique — anomalies concomitantes sur plusieurs signaux."

        top = active_abnormal[0]
        return f"{top.detected_event} sur {top.signal} — corrélation clinique recommandée."


# ======================================================================
# Agent de Prédiction — risque de détérioration à court terme
# ======================================================================
class PredictionAgent:
    name = "Agent de Prédiction"
    HORIZONS = [5, 15, 30, 60]  # minutes

    def predict(self, results: List[AgentResult]) -> dict:
        """
        Combine la sévérité + la direction de tendance de tous les signaux
        pour estimer le risque d'arrêt cardiaque / défaillance respiratoire /
        choc / détérioration générale sur plusieurs horizons temporels.
        """
        severity_score = sum(SEVERITY_RANK[r.severity] for r in results) / max(1, len(results))
        rising_count = sum(1 for r in results if r.trend == 'rising' and r.severity != 'normal')

        base_risk = min(95, severity_score * 18 + rising_count * 6)

        cardiac_signals = [r for r in results if r.signal in ('ECG', 'Fréquence Cardiaque', 'Pression Artérielle')]
        resp_signals = [r for r in results if r.signal in ('SpO2', 'Fréquence Respiratoire')]
        shock_signals = [r for r in results if r.signal in ('Pression Artérielle', 'Fréquence Cardiaque', 'Température')]

        cardiac_arrest_risk = self._signal_group_risk(cardiac_signals, base_risk, weight=1.15)
        resp_failure_risk = self._signal_group_risk(resp_signals, base_risk, weight=1.05)
        shock_risk = self._signal_group_risk(shock_signals, base_risk, weight=1.0)
        deterioration_risk = round(min(96, base_risk))

        horizons = {}
        for h in self.HORIZONS:
            factor = 1 - (1 / (1 + h / 20))
            horizons[h] = round(min(97, deterioration_risk * (0.5 + factor)))

        return {
            'cardiac_arrest_risk': round(cardiac_arrest_risk),
            'respiratory_failure_risk': round(resp_failure_risk),
            'shock_risk': round(shock_risk),
            'deterioration_risk': deterioration_risk,
            'horizons': horizons,
        }

    def _signal_group_risk(self, group: List[AgentResult], base_risk, weight):
        if not group:
            return base_risk * 0.4 * weight
        group_score = sum(SEVERITY_RANK[r.severity] for r in group) / len(group)
        return min(96, (group_score * 20 + base_risk * 0.3) * weight)


# ======================================================================
# Orchestrateur principal
# ======================================================================
class AIAgentOrchestrator:
    """
    Exécute tous les agents sur le tick courant des données patient et
    retourne un ensemble unifié de résultats pour l'affichage UI.
    """

    def __init__(self):
        self.ecg_agent = ECGAgent()
        self.hr_agent = HeartRateAgent()
        self.spo2_agent = SpO2Agent()
        self.temp_agent = TemperatureAgent()
        self.bp_agent = BloodPressureAgent()
        self.resp_agent = RespiratoryAgent()
        self.decision_agent = ClinicalDecisionAgent()
        self.prediction_agent = PredictionAgent()

        self._prev = {}

    def run(self, vitals: dict, rhythm_type: str, ecg_anomaly_type: Optional[str]) -> dict:
        prev = self._prev

        ecg_res = self.ecg_agent.analyze(rhythm_type, ecg_anomaly_type)
        hr_res = self.hr_agent.analyze(vitals['hr'], prev.get('hr'))
        spo2_res = self.spo2_agent.analyze(vitals['spo2'], prev.get('spo2'))
        temp_res = self.temp_agent.analyze(vitals['temp'], prev.get('temp'))
        bp_res = self.bp_agent.analyze(vitals['sbp'], vitals['dbp'], prev.get('sbp'))
        resp_res = self.resp_agent.analyze(vitals['rr'], vitals['spo2'], prev.get('rr'))

        all_results = [ecg_res, hr_res, spo2_res, temp_res, bp_res, resp_res]

        decision = self.decision_agent.decide(all_results)
        prediction = self.prediction_agent.predict(all_results)

        self._prev = {
            'hr': vitals['hr'], 'spo2': vitals['spo2'], 'temp': vitals['temp'],
            'sbp': vitals['sbp'], 'rr': vitals['rr']
        }

        return {
            'agents': {
                'ecg': ecg_res, 'heart_rate': hr_res, 'spo2': spo2_res,
                'temperature': temp_res, 'blood_pressure': bp_res, 'respiratory': resp_res,
            },
            'all_results': all_results,
            'decision': decision,
            'prediction': prediction,
        }
