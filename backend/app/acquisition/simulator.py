"""
app/acquisition/simulator.py
============================
Simulateur de moniteur de réanimation médical réaliste.

Génère l'ensemble des paramètres monitorés dans un service de réanimation :
- ECG multicanaux (II, V1, V5, aVR) avec décalage ST, QT, PVCs, qualité signal
- SpO2+ avec indice de perfusion, pléthysmographe
- NIBP automatique
- Température core + peau + gradient
- Capnométrie ETCO2
- Paramètres de ventilation mécanique
- Hémodynamique avancée (CVP, CO/CI, PAP, PCWP, SVR)
- Neurologie (ICP, CPP, BIS, GCS)
- Diurèse horaire
- Laboratoire (BMP, CBC, ABG, coagulation)
- Scores cliniques (SOFA, qSOFA, NEWS2, Braden, CAM-ICU)
"""

from __future__ import annotations

import random
import time

from app.acquisition.base import DataSource
from app.ai.schemas import VitalsSample
from app.ai.ecg_generator import ECGGenerator
from app.ai.ecg_analysis import signal_quality, analyze_qt_st, count_pvcs, detect_r_peaks
from app.ai.clinical_scoring import ClinicalScoringEngine

# Ranges physiologiques par scénario clinique (ranges réalistes)
WAVEFORM_RANGES: dict[str, dict[str, tuple]] = {
    "normal": {
        "hr": (65, 80), "spo2": (96, 99), "pi": (1.0, 5.0),
        "nibp_sys": (110, 128), "nibp_dia": (70, 84),
        "temp_core": (36.5, 37.4), "temp_skin": (34.0, 35.5),
        "etco2": (35, 45), "rr_capno": (12, 18),
        "vent_peep": (5.0, 8.0), "vent_vt": (450, 550), "vent_pip": (18.0, 24.0),
        "cvp": (2.0, 8.0), "co": (4.0, 6.0), "ci": (2.5, 4.0),
        "icp": (0, 12), "bis": (80, 95), "gcs": (14, 15),
        "uo_hour": (30, 80), "lab_k": (3.5, 4.5), "lab_cr": (0.7, 1.3),
        "lab_hb": (11.0, 14.0), "lab_wbc": (4.0, 11.0), "lab_plt": (150, 400),
        "abg_ph": (7.35, 7.45), "abg_pao2": (80, 100), "abg_paco2": (35, 45),
        "coag_inr": (0.9, 1.2),
    },
    "tachy": {
        "hr": (105, 135), "spo2": (93, 97), "pi": (0.8, 3.5),
        "nibp_sys": (130, 150), "nibp_dia": (80, 95),
        "temp_core": (37.0, 38.0), "temp_skin": (35.0, 36.5),
        "etco2": (30, 40), "rr_capno": (18, 24),
        "vent_peep": (5.0, 8.0), "vent_vt": (450, 550), "vent_pip": (20.0, 28.0),
        "cvp": (4.0, 10.0), "co": (5.0, 8.0), "ci": (3.0, 4.8),
        "icp": (5, 15), "bis": (70, 90), "gcs": (13, 15),
        "uo_hour": (40, 100), "lab_k": (3.5, 4.8), "lab_cr": (0.8, 1.5),
        "lab_hb": (10.0, 13.0), "lab_wbc": (5.0, 13.0), "lab_plt": (100, 350),
        "abg_ph": (7.30, 7.44), "abg_pao2": (70, 95), "abg_paco2": (30, 42),
        "coag_inr": (1.0, 1.4),
    },
    "brady": {
        "hr": (35, 50), "spo2": (92, 97), "pi": (1.0, 4.0),
        "nibp_sys": (88, 108), "nibp_dia": (52, 68),
        "temp_core": (36.0, 37.0), "temp_skin": (33.0, 35.0),
        "etco2": (30, 38), "rr_capno": (10, 14),
        "vent_peep": (5.0, 10.0), "vent_vt": (400, 500), "vent_pip": (16.0, 24.0),
        "cvp": (5.0, 12.0), "co": (2.5, 4.0), "ci": (1.5, 2.5),
        "icp": (8, 18), "bis": (60, 85), "gcs": (10, 14),
        "uo_hour": (20, 50), "lab_k": (3.0, 4.2), "lab_cr": (1.0, 2.0),
        "lab_hb": (9.0, 12.0), "lab_wbc": (3.0, 9.0), "lab_plt": (80, 250),
        "abg_ph": (7.32, 7.44), "abg_pao2": (60, 90), "abg_paco2": (38, 50),
        "coag_inr": (1.0, 1.5),
    },
    # --- Scénarios rythmiques (cohérents avec le générateur ECG + UI) ---
    "afib": {
        "hr": (75, 150), "spo2": (92, 98), "pi": (0.8, 3.5),
        "nibp_sys": (105, 132), "nibp_dia": (65, 84),
        "temp_core": (36.5, 37.5), "temp_skin": (34.0, 35.5),
        "etco2": (30, 42), "rr_capno": (14, 22),
        "vent_peep": (5.0, 8.0), "vent_vt": (450, 550), "vent_pip": (18.0, 26.0),
        "cvp": (4.0, 10.0), "co": (4.0, 7.0), "ci": (2.5, 4.0),
        "icp": (5, 15), "bis": (70, 90), "gcs": (12, 15),
        "uo_hour": (30, 80), "lab_k": (3.5, 4.6), "lab_cr": (0.8, 1.4),
        "lab_hb": (9.0, 13.0), "lab_wbc": (4.0, 11.0), "lab_plt": (120, 350),
        "abg_ph": (7.32, 7.44), "abg_pao2": (70, 100), "abg_paco2": (32, 45),
        "coag_inr": (1.0, 1.4),
    },
    "pvc": {
        "hr": (70, 100), "spo2": (95, 99), "pi": (1.0, 5.0),
        "nibp_sys": (110, 128), "nibp_dia": (70, 84),
        "temp_core": (36.5, 37.4), "temp_skin": (34.0, 35.5),
        "etco2": (35, 45), "rr_capno": (12, 18),
        "vent_peep": (5.0, 8.0), "vent_vt": (450, 550), "vent_pip": (18.0, 24.0),
        "cvp": (2.0, 8.0), "co": (4.0, 6.0), "ci": (2.5, 4.0),
        "icp": (0, 12), "bis": (80, 95), "gcs": (14, 15),
        "uo_hour": (30, 80), "lab_k": (3.5, 4.5), "lab_cr": (0.7, 1.3),
        "lab_hb": (11.0, 14.0), "lab_wbc": (4.0, 11.0), "lab_plt": (150, 400),
        "abg_ph": (7.35, 7.45), "abg_pao2": (80, 100), "abg_paco2": (35, 45),
        "coag_inr": (0.9, 1.2),
    },
    "st_elevation": {
        "hr": (70, 95), "spo2": (93, 98), "pi": (0.8, 3.5),
        "nibp_sys": (110, 140), "nibp_dia": (70, 85),
        "temp_core": (36.5, 37.5), "temp_skin": (34.0, 35.5),
        "etco2": (32, 45), "rr_capno": (14, 20),
        "vent_peep": (5.0, 8.0), "vent_vt": (450, 550), "vent_pip": (18.0, 26.0),
        "cvp": (3.0, 9.0), "co": (4.0, 6.0), "ci": (2.5, 4.0),
        "icp": (3, 13), "bis": (78, 92), "gcs": (13, 15),
        "uo_hour": (30, 80), "lab_k": (3.5, 4.6), "lab_cr": (0.8, 1.4),
        "lab_hb": (10.0, 13.0), "lab_wbc": (4.0, 11.0), "lab_plt": (130, 380),
        "abg_ph": (7.33, 7.44), "abg_pao2": (75, 95), "abg_paco2": (34, 45),
        "coag_inr": (1.0, 1.3),
    },
    "st_depression": {
        "hr": (70, 100), "spo2": (92, 97), "pi": (0.8, 3.5),
        "nibp_sys": (115, 145), "nibp_dia": (72, 88),
        "temp_core": (36.5, 37.5), "temp_skin": (34.0, 35.5),
        "etco2": (33, 46), "rr_capno": (14, 22),
        "vent_peep": (5.0, 8.0), "vent_vt": (450, 550), "vent_pip": (18.0, 26.0),
        "cvp": (3.0, 9.0), "co": (4.0, 6.0), "ci": (2.5, 4.0),
        "icp": (3, 13), "bis": (78, 92), "gcs": (13, 15),
        "uo_hour": (30, 80), "lab_k": (3.5, 4.8), "lab_cr": (0.8, 1.5),
        "lab_hb": (10.0, 13.0), "lab_wbc": (4.0, 11.0), "lab_plt": (130, 380),
        "abg_ph": (7.32, 7.44), "abg_pao2": (72, 95), "abg_paco2": (35, 46),
        "coag_inr": (1.0, 1.3),
    },
    "vtach": {
        "hr": (150, 220), "spo2": (85, 93), "pi": (0.4, 2.5),
        "nibp_sys": (80, 110), "nibp_dia": (50, 75),
        "temp_core": (36.5, 37.5), "temp_skin": (34.0, 36.0),
        "etco2": (28, 40), "rr_capno": (18, 26),
        "vent_peep": (6.0, 10.0), "vent_vt": (420, 520), "vent_pip": (22.0, 32.0),
        "cvp": (6.0, 14.0), "co": (3.0, 5.0), "ci": (1.8, 3.2),
        "icp": (6, 18), "bis": (55, 80), "gcs": (8, 13),
        "uo_hour": (15, 45), "lab_k": (3.0, 5.0), "lab_cr": (1.0, 2.0),
        "lab_hb": (8.0, 12.0), "lab_wbc": (3.0, 10.0), "lab_plt": (80, 280),
        "abg_ph": (7.28, 7.40), "abg_pao2": (65, 90), "abg_paco2": (35, 50),
        "coag_inr": (1.0, 1.5),
    },
    "sepsis": {
        "hr": (100, 130), "spo2": (90, 96), "pi": (0.5, 3.0),
        "nibp_sys": (70, 95), "nibp_dia": (40, 65),
        "temp_core": (38.5, 40.5), "temp_skin": (35.0, 37.5),
        "etco2": (28, 38), "rr_capno": (22, 32),
        "vent_peep": (8.0, 12.0), "vent_vt": (400, 500), "vent_pip": (24.0, 35.0),
        "cvp": (8.0, 15.0), "co": (4.0, 7.0), "ci": (2.0, 4.0),
        "icp": (10, 20), "bis": (65, 90), "gcs": (8, 13),
        "uo_hour": (10, 40), "lab_k": (3.0, 5.5), "lab_cr": (1.5, 3.0),
        "lab_hb": (7.0, 11.0), "lab_wbc": (2.0, 8.0), "lab_plt": (30, 120),
        "abg_ph": (7.25, 7.38), "abg_pao2": (55, 85), "abg_paco2": (32, 48),
        "coag_inr": (1.3, 2.5),
    },
    "post_op_cardiac": {
        "hr": (70, 100), "spo2": (94, 98), "pi": (1.5, 5.0),
        "nibp_sys": (100, 130), "nibp_dia": (60, 80),
        "temp_core": (36.0, 37.5), "temp_skin": (33.0, 36.0),
        "etco2": (32, 42), "rr_capno": (12, 18),
        "vent_peep": (5.0, 8.0), "vent_vt": (450, 550), "vent_pip": (18.0, 26.0),
        "cvp": (5.0, 12.0), "co": (3.5, 5.5), "ci": (2.0, 3.5),
        "icp": (5, 15), "bis": (70, 90), "gcs": (13, 15),
        "uo_hour": (30, 80), "lab_k": (3.5, 4.5), "lab_cr": (0.8, 1.5),
        "lab_hb": (8.0, 11.0), "lab_wbc": (5.0, 12.0), "lab_plt": (80, 200),
        "abg_ph": (7.32, 7.44), "abg_pao2": (70, 100), "abg_paco2": (35, 48),
        "coag_inr": (1.2, 2.0),
    },
    "neuro_critical": {
        "hr": (55, 85), "spo2": (95, 99), "pi": (1.0, 5.0),
        "nibp_sys": (140, 180), "nibp_dia": (80, 105),
        "temp_core": (37.0, 38.5), "temp_skin": (33.0, 36.0),
        "etco2": (30, 38), "rr_capno": (12, 16),
        "vent_peep": (5.0, 8.0), "vent_vt": (450, 550), "vent_pip": (18.0, 26.0),
        "cvp": (5.0, 10.0), "co": (4.0, 6.0), "ci": (2.5, 4.0),
        "icp": (15, 28), "bis": (50, 75), "gcs": (5, 12),
        "uo_hour": (20, 60), "lab_k": (3.5, 4.5), "lab_cr": (0.8, 1.3),
        "lab_hb": (10.0, 14.0), "lab_wbc": (5.0, 13.0), "lab_plt": (120, 350),
        "abg_ph": (7.32, 7.43), "abg_pao2": (80, 110), "abg_paco2": (32, 40),
        "coag_inr": (1.0, 1.4),
    },
    "respiratory_failure": {
        "hr": (90, 120), "spo2": (82, 92), "pi": (0.3, 2.5),
        "nibp_sys": (100, 140), "nibp_dia": (60, 90),
        "temp_core": (36.5, 38.0), "temp_skin": (34.0, 36.5),
        "etco2": (50, 70), "rr_capno": (24, 36),
        "vent_peep": (10.0, 18.0), "vent_vt": (400, 500), "vent_pip": (28.0, 45.0),
        "cvp": (6.0, 14.0), "co": (3.5, 5.5), "ci": (2.0, 3.5),
        "icp": (8, 18), "bis": (70, 90), "gcs": (9, 14),
        "uo_hour": (25, 70), "lab_k": (3.2, 4.8), "lab_cr": (0.9, 1.8),
        "lab_hb": (10.0, 14.0), "lab_wbc": (4.0, 12.0), "lab_plt": (100, 300),
        "abg_ph": (7.28, 7.40), "abg_pao2": (55, 80), "abg_paco2": (45, 65),
        "coag_inr": (1.0, 1.4),
    },
}

LEADS = ["II", "V1", "V5", "aVR"]
ECG_SAMPLES_PER_READ = 125


def _clamp(v, a, b):
    return max(a, min(b, v))


def _rand_in(a, b):
    return a + random.random() * (b - a)


class MonitorSimulatorSource(DataSource):
    mode = "monitor"

    def __init__(self, patient_id: str = "ICU-204", scenario: str = "normal", ecg_samples: int = ECG_SAMPLES_PER_READ):
        self.patient_id = patient_id
        self.scenario = scenario if scenario in WAVEFORM_RANGES else "normal"
        self.ecg_n = ecg_samples
        self._ecg_gen = ECGGenerator()
        self._lead_idx = 0
        self._scoring = ClinicalScoringEngine()
        # Courant valeurs (dérivent doucement)
        self.v = self._init_vitals()
        self._cycle_count = 0

    def _init_vitals(self) -> dict:
        r = WAVEFORM_RANGES.get(self.scenario, WAVEFORM_RANGES["normal"])
        return {k: _rand_in(v[0], v[1]) if isinstance(v, tuple) else v for k, v in r.items()}

    def configure(self, scenario: str | None = None, **kwargs) -> None:
        if scenario and scenario in WAVEFORM_RANGES:
            self.scenario = scenario
            self.v = self._init_vitals()

    def _update_vitals(self):
        r = WAVEFORM_RANGES.get(self.scenario, WAVEFORM_RANGES["normal"])
        v = self.v
        v["hr"] = _clamp(v["hr"] + (random.random() - 0.5) * 3, *r["hr"])
        v["spo2"] = _clamp(v["spo2"] + (random.random() - 0.5) * 0.8, *r["spo2"])
        v["pi"] = _clamp(v["pi"] + (random.random() - 0.5) * 0.4, *r["pi"])
        v["nibp_sys"] = _clamp(v["nibp_sys"] + (random.random() - 0.5) * 3, *r["nibp_sys"])
        v["nibp_dia"] = _clamp(v["nibp_dia"] + (random.random() - 0.5) * 2, *r["nibp_dia"])
        v["temp_core"] = _clamp(v["temp_core"] + (random.random() - 0.5) * 0.08, *r["temp_core"])
        v["temp_skin"] = _clamp(v["temp_skin"] + (random.random() - 0.5) * 0.06, *r["temp_skin"])
        v["etco2"] = _clamp(v["etco2"] + (random.random() - 0.5) * 1.5, *r["etco2"])
        v["rr_capno"] = _clamp(v["rr_capno"] + (random.random() - 0.5) * 1.0, *r["rr_capno"])
        v["vent_peep"] = _clamp(v["vent_peep"] + (random.random() - 0.5) * 0.3, *r["vent_peep"])
        v["vent_pip"] = _clamp(v["vent_pip"] + (random.random() - 0.5) * 0.5, *r["vent_pip"])
        v["cvp"] = _clamp(v["cvp"] + (random.random() - 0.5) * 0.3, *r["cvp"])
        v["co"] = _clamp(v["co"] + (random.random() - 0.5) * 0.2, *r["co"])
        v["icp"] = _clamp(v["icp"] + (random.random() - 0.5) * 1.0, *r["icp"])
        v["bis"] = _clamp(v["bis"] + (random.random() - 0.5) * 3.0, *r["bis"])
        v["uo_hour"] = _clamp(v["uo_hour"] + (random.random() - 0.5) * 8, *r["uo_hour"])
        v["lab_k"] = _clamp(v["lab_k"] + (random.random() - 0.5) * 0.1, *r["lab_k"])
        v["lab_cr"] = _clamp(v["lab_cr"] + (random.random() - 0.5) * 0.05, *r["lab_cr"])
        v["lab_wbc"] = _clamp(v["lab_wbc"] + (random.random() - 0.5) * 0.5, *r["lab_wbc"])
        v["lab_plt"] = _clamp(v["lab_plt"] + (random.random() - 0.5) * 15, *r["lab_plt"])
        v["abg_ph"] = _clamp(v["abg_ph"] + (random.random() - 0.5) * 0.01, *r["abg_ph"])
        v["abg_paco2"] = _clamp(v["abg_paco2"] + (random.random() - 0.5) * 1.5, *r["abg_paco2"])
        v["coag_inr"] = _clamp(v["coag_inr"] + (random.random() - 0.5) * 0.1, *r["coag_inr"])
        # Arrondis
        for k in ["hr", "spo2", "rr_capno", "nibp_sys", "nibp_dia", "uo_hour", "lab_plt", "lab_wbc"]:
            v[k] = int(v.get(k, 0))
        for k in ["temp_core", "temp_skin", "etco2", "vent_peep", "vent_pip", "cvp", "co", "ci", "icp",
                   "lab_k", "lab_cr", "lab_hb", "lab_wbc", "lab_plt", "abg_ph", "abg_pao2",
                   "abg_paco2", "abg_hco3", "abg_sat", "abg_be", "coag_pt", "coag_inr", "coag_aptt",
                   "abg_pao2", "abg_paco2", "abg_hco3", "abg_sat", "abg_be", "coag_pt", "coag_inr", "coag_aptt"]:
            v[k] = round(float(v.get(k, 0.0)), 1)
        v["map_val"] = round(v["nibp_dia"] + (v["nibp_sys"] - v["nibp_dia"]) / 3)
        v["cpp_val"] = round(max(0.0, v["map_val"] - v["icp"]), 0) if v["icp"] > 0 else 0
        v["temp_gradient"] = round(v["temp_core"] - v["temp_skin"], 1)
        self._cycle_count += 1

    def read(self) -> VitalsSample:
        self._update_vitals()
        v = self.v
        lead = LEADS[self._lead_idx % len(LEADS)]
        self._lead_idx += 1
        if self._lead_idx % (len(LEADS) * 4) == 0:
            self._ecg_gen = ECGGenerator()
        self._ecg_gen.set_lead(lead)
        qual = _clamp(v.get("ecg_qual", 0.95), 0.3, 1.0)
        ecg_samples = self._ecg_gen.get_next_samples(self.scenario, self.ecg_n, quality=qual)
        flags = self._ecg_gen.get_last_anomaly_flags()
        anom_type = self._ecg_gen.get_last_anomaly_type()
        qt_st = analyze_qt_st(ecg_samples, detect_r_peaks(ecg_samples), fs=250)
        pvcs = count_pvcs(ecg_samples, detect_r_peaks(ecg_samples))
        sig_qual = signal_quality(ecg_samples)

        sample = VitalsSample(
            patient_id=self.patient_id,
            ts=time.time(),
            scenario=self.scenario,
            ecg_hr=int(v["hr"]),
            ecg_rhythm=self.scenario if self.scenario != "normal" else "normal",
            ecg_st=qt_st.get("st_mm", 0.0),
            ecg_qt=qt_st.get("qt_ms", 400),
            ecg_pvcs=pvcs,
            ecg_qual=sig_qual,
            hr=int(v["hr"]),
            spo2=int(v["spo2"]),
            pi=round(v.get("pi", 2.0), 1),
            pleth_amp=round(random.uniform(2.0, 18.0), 1),
            nibp_sys=int(v["nibp_sys"]),
            nibp_dia=int(v["nibp_dia"]),
            nibp_map=int(v.get("map_val", 90)),
            nibp_pulse=int(v.get("hr", 70)),
            nibp_cycle=15 if (self._cycle_count % 15 == 0) else 1,  # NIBP cycle
            temp_core=round(v.get("temp_core", 37.0), 1),
            temp_skin=round(v.get("temp_skin", 34.5), 1),
            temp_gradient=round(v.get("temp_gradient", 2.5), 1),
            etco2=int(v.get("etco2", 40)),
            rr_capno=int(v.get("rr_capno", 16)),
            fio2=21 if v.get("vent_mode") in ["VCV", "PCV", "PSV"] else 40,
            vent_mode=random.choice(["VCV", "PCV", "PSV", "SIMV", "CPAP"]) if self.scenario == "normal" else ("VCV" if self.scenario in ["respiratory_failure"] else random.choice(["VCV", "PCV", "SIMV"])),
            vent_fio2=30 if self.scenario == "respiratory_failure" else 40 if self.scenario == "sepsis" else 21,
            vent_peep=round(v.get("vent_peep", 5.0), 0),
            vent_vt=int(v.get("vent_vt", 500)),
            vent_rr=int(v.get("vent_rr", 12)),
            vent_pip=round(v.get("vent_pip", 20.0), 0),
            vent_mv=round(v.get("vent_mv", 6.0), 1),
            vent_ie="1:2",
            vent_pplat=round(v.get("vent_pip", 20.0) * 0.75, 0),
            vent_trigger="flow",
            cvp=round(v.get("cvp", 5.0), 1),
            co=round(v.get("co", 5.0), 1),
            ci=round(v.get("ci", 2.8), 1),
            sv=round(v.get("co", 5.0) / max(v.get("hr", 70), 1) * 1000, 0),
            svr=round((v.get("map_val", 90) - v.get("cvp", 5.0)) / max(v.get("co", 5.0), 0.1) * 80, 0),
            pap_sys=int(v.get("cvp", 5.0) * 1.5 + random.uniform(5, 15)),
            pap_dia=int(v.get("cvp", 5.0) * 0.6 + random.uniform(2, 8)),
            pap_map=int(0.67 * (v.get("cvp", 5.0) * 1.5 + random.uniform(5, 15)) + 0.33 * (v.get("cvp", 5.0) * 0.6 + random.uniform(2, 8))),
            pcwp=round(v.get("cvp", 5.0) * 0.8 + random.uniform(2, 6), 1),
            icp=round(v.get("icp", 8.0), 0),
            cpp=round(v.get("cpp_val", 82.0), 0),
            bis=int(v.get("bis", 85)),
            gcs=int(v.get("gcs", 14)),
            uo_hour=int(v.get("uo_hour", 50)),
            uo_6h=int(v.get("uo_hour", 50) * 6 + random.randint(-20, 20)),
            uo_24h=int(v.get("uo_hour", 50) * 24 + random.randint(-50, 50)),
            lab_na=round(v.get("lab_na", 140.0), 0),
            lab_k=round(v.get("lab_k", 4.0), 1),
            lab_cr=round(v.get("lab_cr", 1.0), 1),
            lab_bun=round(v.get("lab_cr", 1.0) * 8 + random.uniform(5, 15), 0),
            lab_glu=round(v.get("lab_glu", 110.0), 0),
            lab_hb=round(v.get("lab_hb", 11.0), 1),
            lab_hct=round(v.get("lab_hb", 11.0) * 2.9, 0),
            lab_wbc=round(v.get("lab_wbc", 9.0), 1),
            lab_plt=int(v.get("lab_plt", 200)),
            abg_ph=round(v.get("abg_ph", 7.38), 2),
            abg_pao2=round(v.get("abg_pao2", 90.0), 0),
            abg_paco2=round(v.get("abg_paco2", 40.0), 0),
            abg_hco3=round(0.03 * 10 ** (v.get("abg_ph", 7.38) - 6.1) * v.get("abg_paco2", 40.0), 1),
            abg_sat=round(min(100.0, max(70.0, v.get("spo2", 97.0) - random.uniform(0, 5))), 0),
            abg_be=round(-v.get("abg_hco3", 24.0) + 24.0 + random.uniform(-2, 2), 1),
            coag_pt=round(v.get("coag_inr", 1.1) * 12 + random.uniform(-1, 1), 1),
            coag_inr=round(v.get("coag_inr", 1.1), 2),
            coag_aptt=round(25 + v.get("coag_inr", 1.1) * 5 + random.uniform(0, 10), 0),
            ecg_samples=[round(float(x), 4) for x in ecg_samples],
            ecg_anomaly_flags=flags,
            ecg_anomaly_type=anom_type,
            ecg_waveform_type=lead,
        )
        return sample
