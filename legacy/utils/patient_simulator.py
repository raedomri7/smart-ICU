"""
utils/patient_simulator.py
=============================
Simule le flux de données physiologiques d'un patient ICU et exécute
l'orchestrateur d'agents IA à chaque tick.

En production, ce module serait remplacé par un flux temps réel issu de
PhysioNet / MIMIC-IV / matériel de monitoring, mais les interfaces des
agents restent identiques.
"""

import random
import time
from collections import deque

from utils.ai_agents import AIAgentOrchestrator
from utils.ecg_generator import ECGGenerator, ECG_CLINICAL_INFO


WAVEFORM_VITAL_RANGES = {
    'normal':         {'hr': (65, 80),   'spo2': (96, 99), 'rr': (14, 18), 'temp': (36.5, 37.4), 'sbp': (110, 128), 'dbp': (70, 84)},
    'tachy':          {'hr': (105, 135), 'spo2': (93, 97), 'rr': (18, 24), 'temp': (37.0, 38.0), 'sbp': (130, 150), 'dbp': (80, 95)},
    'brady':          {'hr': (35, 50),   'spo2': (94, 97), 'rr': (10, 14), 'temp': (36.0, 37.0), 'sbp': (88, 108),  'dbp': (52, 68)},
    'afib':           {'hr': (80, 132),  'spo2': (90, 96), 'rr': (16, 22), 'temp': (37.0, 38.4), 'sbp': (98, 142),  'dbp': (62, 90)},
    'pvc':            {'hr': (60, 86),   'spo2': (94, 98), 'rr': (14, 20), 'temp': (36.8, 37.8), 'sbp': (108, 134), 'dbp': (68, 88)},
    'st_elevation':   {'hr': (85, 115),  'spo2': (90, 95), 'rr': (18, 26), 'temp': (36.9, 37.6), 'sbp': (95, 125),  'dbp': (58, 80)},
    'st_depression':  {'hr': (80, 110),  'spo2': (91, 96), 'rr': (16, 22), 'temp': (36.8, 37.5), 'sbp': (100, 130), 'dbp': (60, 82)},
    'vtach':           {'hr': (160, 210), 'spo2': (82, 90), 'rr': (24, 34), 'temp': (36.8, 38.0), 'sbp': (60, 88),   'dbp': (40, 58)},
}


def _rand_in(a, b):
    return a + random.random() * (b - a)


def _clamp(v, a, b):
    return max(a, min(b, v))


class PatientSimulator:
    def __init__(self, patient_id="ICU-204"):
        self.patient_id = patient_id
        self.waveform = 'normal'
        self.anomaly_active = False

        self.vitals = {'hr': 72, 'spo2': 98, 'rr': 16, 'temp': 37.2, 'sbp': 120, 'dbp': 80}

        self.ecg_gen = ECGGenerator()
        self.orchestrator = AIAgentOrchestrator()

        self.history = {k: deque(maxlen=120) for k in self.vitals}
        self.timeline_events = deque(maxlen=50)

        self.last_ai_output = None
        self._seed_history()

    def _seed_history(self):
        ranges = WAVEFORM_VITAL_RANGES['normal']
        for _ in range(20):
            for key in self.vitals:
                lo, hi = ranges.get(key, (self.vitals[key], self.vitals[key]))
                if key == 'temp':
                    self.history[key].append(round(_rand_in(lo, hi), 1))
                else:
                    self.history[key].append(round(_rand_in(lo, hi)))

    # ------------------------------------------------------------------
    def set_waveform(self, waveform_type):
        if waveform_type != self.waveform:
            labels = {
                'normal': 'NORMAL', 'tachy': 'TACHYCARDIE', 'brady': 'BRADYCARDIE',
                'afib': 'FIBRILLATION AURICULAIRE', 'pvc': 'ESV',
                'st_elevation': 'SUS-DÉCALAGE ST', 'st_depression': 'SOUS-DÉCALAGE ST',
                'vtach': 'TACHYCARDIE VENTRICULAIRE',
            }
            self.timeline_events.append({
                'time': time.strftime('%H:%M:%S'),
                'event': f"Rythme changé en {labels.get(waveform_type, waveform_type.upper())}",
                'severity': 'info'
            })
        self.waveform = waveform_type

    # ------------------------------------------------------------------
    def step(self):
        """Avance la simulation d'un tick (~2s) et exécute les agents IA."""
        ranges = WAVEFORM_VITAL_RANGES.get(self.waveform, WAVEFORM_VITAL_RANGES['normal'])

        self.vitals['hr'] = round(_clamp(self.vitals['hr'] + (random.random() - 0.5) * 4, *ranges['hr']))
        self.vitals['spo2'] = round(_clamp(self.vitals['spo2'] + (random.random() - 0.5) * 1.0, *ranges['spo2']))
        self.vitals['rr'] = round(_clamp(self.vitals['rr'] + (random.random() - 0.5) * 1.2, *ranges['rr']))
        self.vitals['temp'] = round(_clamp(self.vitals['temp'] + (random.random() - 0.5) * 0.12, *ranges['temp']), 1)
        self.vitals['sbp'] = round(_clamp(self.vitals['sbp'] + (random.random() - 0.5) * 4, *ranges['sbp']))
        self.vitals['dbp'] = round(_clamp(self.vitals['dbp'] + (random.random() - 0.5) * 3, *ranges['dbp']))

        for key in self.vitals:
            self.history[key].append(self.vitals[key])

        # Détermine le type d'anomalie ECG courant (correspond au rythme choisi)
        anomaly_map = {
            'normal': None, 'tachy': 'Tachycardie', 'brady': 'Bradycardie',
            'afib': 'Fibrillation Auriculaire', 'pvc': 'ESV (Extrasystole Ventriculaire)',
            'st_elevation': 'Sus-décalage ST', 'st_depression': 'Sous-décalage ST',
            'vtach': 'Tachycardie Ventriculaire'
        }
        anomaly_type = anomaly_map.get(self.waveform)
        self.anomaly_active = anomaly_type is not None

        # Exécute tous les agents IA
        ai_output = self.orchestrator.run(self.vitals, self.waveform, anomaly_type)
        self.last_ai_output = ai_output

        # Journalise les événements significatifs dans la timeline
        decision = ai_output['decision']
        if decision['overall_severity'] in ('high', 'critical'):
            self.timeline_events.append({
                'time': time.strftime('%H:%M:%S'),
                'event': decision['diagnosis'],
                'severity': decision['overall_severity']
            })

        return ai_output

    # ------------------------------------------------------------------
    def get_vitals(self):
        return dict(self.vitals)

    def get_ai_prediction(self):
        """
        Résumé compatible avec les panneaux UI simples (conservé pour la
        compatibilité avec le code antérieur des panneaux plus simples).
        """
        if self.last_ai_output is None:
            self.step()

        decision = self.last_ai_output['decision']
        prediction = self.last_ai_output['prediction']
        top = decision['top_concern']

        from utils.theme import SEVERITY_COLORS
        color = SEVERITY_COLORS.get(decision['overall_severity'], '#00ff88')

        severity_labels = {
            'normal': '🟢 État Stable',
            'low': '🔵 Risque Faible Détecté',
            'medium': '🟡 Risque Moyen Détecté',
            'high': '🟠 Risque Élevé — Action Requise',
            'critical': '🔴 Critique — Attention d\'Urgence Requise',
        }

        factors = []
        for r in decision['contributing_agents'][:4] or [top]:
            color_key = {'normal': 'green', 'low': 'green', 'medium': 'yellow', 'high': 'red', 'critical': 'red'}
            factors.append((color_key.get(r.severity, 'green'), f"{r.signal}: {r.explanation}"))
        while len(factors) < 4:
            factors.append(('green', 'Aucune anomalie supplémentaire détectée.'))

        return {
            'risk': prediction['deterioration_risk'],
            'status': severity_labels.get(decision['overall_severity'], '🟢 État Stable'),
            'color': color,
            'confidence': [
                self.last_ai_output['agents']['ecg'].confidence if self.anomaly_active else 10,
                prediction['deterioration_risk'],
                prediction['cardiac_arrest_risk'],
            ],
            'factors': factors,
            'waveform': self.waveform,
            'decision': decision,
            'prediction': prediction,
            'agents': self.last_ai_output['agents'],
        }

    def get_history_arrays(self):
        return {k: list(v) for k, v in self.history.items()}

    def get_timeline_events(self):
        return list(self.timeline_events)[::-1]
