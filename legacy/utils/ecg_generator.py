"""
utils/ecg_generator.py
========================
Synthetic ECG waveform generator.

Generates realistic PQRST morphology for multiple rhythm classes,
and tracks WHICH samples in the rolling buffer correspond to an
abnormal beat, so the UI can highlight ONLY that segment in red
instead of recoloring the entire trace.
"""

import numpy as np


class ECGGenerator:
    """
    Produces continuous ECG sample streams for a chosen rhythm type.
    Each call to get_next_samples() advances the internal phase and
    returns new samples plus metadata about whether those samples
    belong to an abnormal beat (and which class of abnormality).
    """

    BEAT_LEN = 500  # samples per nominal beat cycle at base resolution

    def __init__(self, fs=250):
        self.fs = fs
        self._phase = 0.0
        self._cycle_pos = 0  # position within current "logical" cycle
        self._last_anomaly_type = None
        self._anomaly_flags = []  # parallel list to output samples: True/False per sample

    # ------------------------------------------------------------------
    def generate_waveform(self, rhythm_type, length):
        """Generate a static buffer (used to pre-fill the plot)."""
        samples = np.zeros(length)
        for i in range(length):
            t = (i % self.BEAT_LEN) / self.BEAT_LEN
            samples[i] = self._sample_at(rhythm_type, t, i)
        return samples

    def get_next_samples(self, rhythm_type, n):
        """Generate the next n samples continuously (streaming)."""
        out = np.zeros(n)
        flags = []
        for i in range(n):
            t = (self._phase % self.BEAT_LEN) / self.BEAT_LEN
            val, is_anom, anom_type = self._sample_with_flag(rhythm_type, t, self._phase)
            out[i] = val
            flags.append(is_anom)
            self._phase += self._speed_factor(rhythm_type)
            if is_anom:
                self._last_anomaly_type = anom_type
        self._anomaly_flags = flags
        return out

    def get_last_anomaly_flags(self):
        """Returns list[bool] aligned with the last get_next_samples() call."""
        return self._anomaly_flags

    def get_last_anomaly_type(self):
        return self._last_anomaly_type

    # ------------------------------------------------------------------
    def _speed_factor(self, rhythm_type):
        speeds = {
            'normal': 1.0,
            'tachy': 1.75,
            'brady': 0.55,
            'afib': 1.15,
            'pvc': 1.0,
            'st_elevation': 1.0,
            'st_depression': 1.0,
            'vtach': 2.4,
        }
        return speeds.get(rhythm_type, 1.0)

    def _sample_at(self, rhythm_type, t, idx):
        val, _, _ = self._sample_with_flag(rhythm_type, t, idx)
        return val

    def _sample_with_flag(self, rhythm_type, t, idx):
        """Returns (value, is_anomalous_sample, anomaly_type_or_None)."""
        if rhythm_type == 'normal':
            return self._normal_beat(t) + self._noise(), False, None

        if rhythm_type == 'tachy':
            return self._normal_beat(t) * 0.92 + self._noise(), True, 'Tachycardie'

        if rhythm_type == 'brady':
            return self._normal_beat(t) + self._noise(), True, 'Bradycardie'

        if rhythm_type == 'afib':
            v = self._normal_beat(t)
            v -= 0.15 * np.exp(-((t - 0.12) / 0.025) ** 2)  # remove P wave
            v += 0.05 * np.sin(idx * 0.9) * 0.6
            v += self._noise(scale=0.03)
            return v, True, 'Fibrillation Auriculaire'

        if rhythm_type == 'pvc':
            # Every ~4th beat is a wide bizarre PVC complex
            beat_number = int(idx // self.BEAT_LEN)
            if beat_number % 4 == 3:
                if 0.45 < t < 0.75:
                    v = -0.35 + 1.6 * np.exp(-((t - 0.56) / 0.03) ** 2) - 0.5 * np.exp(-((t - 0.66) / 0.025) ** 2)
                    return v + self._noise(), True, 'ESV (Extrasystole Ventriculaire)'
                return self._normal_beat(t * 0.6) + self._noise(), False, None
            return self._normal_beat(t) + self._noise(), False, None

        if rhythm_type == 'st_elevation':
            v = self._normal_beat(t)
            if 0.27 < t < 0.40:
                v += 0.22  # elevate ST segment
                return v + self._noise(), True, 'Sus-décalage ST'
            return v + self._noise(), False, None

        if rhythm_type == 'st_depression':
            v = self._normal_beat(t)
            if 0.27 < t < 0.40:
                v -= 0.18
                return v + self._noise(), True, 'Sous-décalage ST'
            return v + self._noise(), False, None

        if rhythm_type == 'vtach':
            v = 0.9 * np.sin(t * 2 * np.pi * 1.4) + 0.25 * np.sin(t * 2 * np.pi * 3.1)
            return v + self._noise(scale=0.02), True, 'Tachycardie Ventriculaire'

        return self._normal_beat(t) + self._noise(), False, None

    def _normal_beat(self, t):
        v = 0.0
        v += 0.15 * np.exp(-((t - 0.12) / 0.025) ** 2)       # P wave
        v -= 0.08 * np.exp(-((t - 0.20) / 0.010) ** 2)       # Q
        v += 1.20 * np.exp(-((t - 0.23) / 0.012) ** 2)       # R spike
        v -= 0.25 * np.exp(-((t - 0.26) / 0.012) ** 2)       # S
        v += 0.35 * np.exp(-((t - 0.38) / 0.050) ** 2)       # T wave
        return v

    def _noise(self, scale=0.015):
        return (np.random.random() - 0.5) * scale


# ----------------------------------------------------------------------
# Anomaly clinical metadata (used by ECGAgent / UI labels)
# ----------------------------------------------------------------------
ECG_CLINICAL_INFO = {
    'Tachycardie': {
        'meaning': 'Fréquence cardiaque supérieure à 100 bpm — demande accrue en oxygène du myocarde',
        'severity': 'medium',
        'base_confidence': 91,
    },
    'Bradycardie': {
        'meaning': 'Fréquence cardiaque inférieure à 60 bpm — risque de perfusion inadéquate',
        'severity': 'medium',
        'base_confidence': 89,
    },
    'Fibrillation Auriculaire': {
        'meaning': 'Activité auriculaire irrégulière, ondes P absentes — risque accru d\'AVC/embolie',
        'severity': 'high',
        'base_confidence': 94,
    },
    'ESV (Extrasystole Ventriculaire)': {
        'meaning': 'Extrasystole Ventriculaire — battement ectopique d\'origine ventriculaire',
        'severity': 'medium',
        'base_confidence': 97,
    },
    'Sus-décalage ST': {
        'meaning': 'Possible infarctus du myocarde aigu (STEMI) — évaluation cardiologique urgente requise',
        'severity': 'critical',
        'base_confidence': 93,
    },
    'Sous-décalage ST': {
        'meaning': 'Possible ischémie myocardique — perfusion coronarienne réduite',
        'severity': 'high',
        'base_confidence': 88,
    },
    'Tachycardie Ventriculaire': {
        'meaning': 'Rythme menaçant la vie — risque d\'arrêt cardiaque, intervention immédiate requise',
        'severity': 'critical',
        'base_confidence': 96,
    },
}
