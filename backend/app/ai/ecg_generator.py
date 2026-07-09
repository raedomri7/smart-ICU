"""
app/ai/ecg_generator.py
=======================
Générateur ECG avancé pour simulateur de moniteur ICU réaliste.

Supporte :
- Dérivations multiples (II, V1, V5, aVR)
- Morphologie PQRST réaliste par dérivation
- Incréments ST segment (elevation/depression)
- Intervalle QT variable
- Extrasystoles ventriculaires (PVCs)
- Qualité signal variable
- Flag anomalie par échantillon pour surlignage segment unique
"""

from __future__ import annotations

import numpy as np


class ECGGenerator:
    BEAT_LEN = 500

    def __init__(self, fs: int = 250):
        self.fs = fs
        self._phase = 0.0
        self._last_anomaly_type: str | None = None
        self._anomaly_flags: list[bool] = []
        self._current_lead: str = "II"

    def set_lead(self, lead: str) -> None:
        self._current_lead = lead

    def get_next_samples(self, rhythm_type: str, n: int, quality: float = 0.95) -> np.ndarray:
        out = np.zeros(n)
        flags: list[bool] = []
        anom_type: str | None = None
        q = max(0.0, min(1.0, quality))
        noise_scale = 0.015 + (1.0 - q) * 0.12

        for i in range(n):
            t = (self._phase % self.BEAT_LEN) / self.BEAT_LEN
            val, is_anom, a_type = self._sample_with_flag(rhythm_type, t, self._phase)
            val += (np.random.random() - 0.5) * noise_scale * 2.0
            out[i] = val
            flags.append(is_anom)
            self._phase += self._speed_factor(rhythm_type)
            if is_anom and q > 0.5:
                anom_type = a_type

        self._anomaly_flags = flags
        self._last_anomaly_type = anom_type
        return out

    def get_last_anomaly_flags(self) -> list[bool]:
        return self._anomaly_flags

    def get_last_anomaly_type(self) -> str | None:
        return self._last_anomaly_type

    def _speed_factor(self, rhythm_type: str) -> float:
        speeds = {
            "normal": 1.0, "tachy": 1.75, "brady": 0.55, "afib": 1.15,
            "pvc": 1.0, "st_elevation": 1.0, "st_depression": 1.0,
            "vtach": 2.4, "torsades": 3.0, "asystole": 0.0, "vf": 2.8,
        }
        return speeds.get(rhythm_type, 1.0)

    def _sample_with_flag(self, rhythm_type, t, idx):
        if rhythm_type == "normal":
            return self._normal_beat(self._current_lead, t), False, None

        if rhythm_type == "tachy":
            return self._normal_beat(self._current_lead, t) * 0.92 + self._noise(), True, "Tachycardie"

        if rhythm_type == "brady":
            return self._normal_beat(self._current_lead, t) * 1.05 + self._noise(), True, "Bradycardie"

        if rhythm_type == "afib":
            v = self._normal_beat(self._current_lead, t)
            v -= 0.15 * np.exp(-((t - 0.12) / 0.025) ** 2)
            v += 0.05 * np.sin(idx * 0.9) * 0.6
            return v + self._noise(scale=0.03), True, "Fibrillation Auriculaire"

        if rhythm_type == "pvc":
            beat_number = int(idx // self.BEAT_LEN)
            if beat_number % 4 == 3:
                if 0.45 < t < 0.75:
                    v = -0.35 + 1.6 * np.exp(-((t - 0.56) / 0.03) ** 2) - 0.5 * np.exp(-((t - 0.66) / 0.025) ** 2)
                    return v + self._noise(), True, "ESV (Extrasystole Ventriculaire)"
                return self._normal_beat(self._current_lead, t * 0.6) + self._noise(), False, None
            return self._normal_beat(self._current_lead, t) + self._noise(), False, None

        if rhythm_type == "st_elevation":
            v = self._normal_beat(self._current_lead, t)
            if 0.27 < t < 0.40:
                v += 0.20 + 0.05 * np.sin(t * 20)
                return v + self._noise(), True, "Sus-décalage ST"
            return v + self._noise(), False, None

        if rhythm_type == "st_depression":
            v = self._normal_beat(self._current_lead, t)
            if 0.27 < t < 0.40:
                v -= 0.16 + 0.04 * np.sin(t * 18)
                return v + self._noise(), True, "Sous-décalage ST"
            return v + self._noise(), False, None

        if rhythm_type == "vtach":
            v = 0.8 * np.sin(t * 2 * np.pi * 1.4) + 0.22 * np.sin(t * 2 * np.pi * 3.1)
            return v + self._noise(scale=0.02), True, "Tachycardie Ventriculaire"

        if rhythm_type == "torsades":
            v = 0.6 * np.sin(t * 2 * np.pi * 1.2 + np.sin(t * 3) * 0.8)
            return v + self._noise(scale=0.015), True, "Torsades de Pointes"

        if rhythm_type == "vf":
            v = (np.random.random() - 0.5) * 1.2
            return v, True, "Fibrillation Ventriculaire"

        if rhythm_type == "asystole":
            return np.zeros(1) + self._noise(scale=0.01), True, "Asystolie"

        return self._normal_beat(self._current_lead, t) + self._noise(), False, None

    def _normal_beat(self, lead: str, t: float) -> float:
        if lead == "V1":
            v = 0.10 * np.exp(-((t - 0.12) / 0.025) ** 2)
            v += 0.05 * np.exp(-((t - 0.20) / 0.010) ** 2)
            v += 0.60 * np.exp(-((t - 0.23) / 0.012) ** 2)
            v += 0.90 * np.exp(-((t - 0.265) / 0.012) ** 2)
            v -= 0.20 * np.exp(-((t - 0.35) / 0.040) ** 2)
            return v
        if lead == "V5":
            v = 0.12 * np.exp(-((t - 0.12) / 0.025) ** 2)
            v += 1.10 * np.exp(-((t - 0.23) / 0.012) ** 2)
            v -= 0.18 * np.exp(-((t - 0.26) / 0.012) ** 2)
            v += 0.25 * np.exp(-((t - 0.38) / 0.050) ** 2)
            return v
        if lead == "aVR":
            v = 0.10 * np.exp(-((t - 0.12) / 0.025) ** 2)
            v -= 0.08 * np.exp(-((t - 0.20) / 0.010) ** 2)
            v -= 0.90 * np.exp(-((t - 0.23) / 0.012) ** 2)
            v += 0.20 * np.exp(-((t - 0.26) / 0.012) ** 2)
            v -= 0.15 * np.exp(-((t - 0.38) / 0.050) ** 2)
            return v
        # Lead II (default)
        v = 0.0
        v += 0.15 * np.exp(-((t - 0.12) / 0.025) ** 2)
        v -= 0.08 * np.exp(-((t - 0.20) / 0.010) ** 2)
        v += 1.20 * np.exp(-((t - 0.23) / 0.012) ** 2)
        v -= 0.25 * np.exp(-((t - 0.26) / 0.012) ** 2)
        v += 0.35 * np.exp(-((t - 0.38) / 0.050) ** 2)
        return v

    def _noise(self, scale: float = 0.015):
        return (np.random.random() - 0.5) * scale


ECG_CLINICAL_INFO = {
    "Tachycardie": {"meaning": "FC > 100 bpm — demande myocardique ↑", "severity": "medium", "base_confidence": 91},
    "Bradycardie": {"meaning": "FC < 60 bpm — perfusion ↓", "severity": "medium", "base_confidence": 89},
    "Fibrillation Auriculaire": {"meaning": "Arythmie irrégulière, ondes P absentes — risque AVC/embolie", "severity": "high", "base_confidence": 94},
    "ESV (Extrasystole Ventriculaire)": {"meaning": "Battement ectopique ventriculaire", "severity": "medium", "base_confidence": 97},
    "Sus-décalage ST": {"meaning": "STEMI possible — occlusion coronaire aiguë", "severity": "critical", "base_confidence": 93},
    "Sous-décalage ST": {"meaning": "Ischémie myocardique possible", "severity": "high", "base_confidence": 88},
    "Tachycardie Ventriculaire": {"meaning": "Rythme menaçant la vie — risque arrêt cardiaque immédiat", "severity": "critical", "base_confidence": 96},
    "Torsades de Pointes": {"meaning": "Torsades — polymorphique, risque VT/VF", "severity": "critical", "base_confidence": 92},
    "Fibrillation Ventriculaire": {"meaning": "FV — arrêt circulatoire, défibrillation immédiate", "severity": "critical", "base_confidence": 98},
    "Asystolie": {"meaning": "Activité électrique nulle — arrêt cardiaque", "severity": "critical", "base_confidence": 99},
}
