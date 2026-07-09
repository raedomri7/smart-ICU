"""
app/acquisition/csv_source.py
=============================
Source de données rejouant un fichier CSV.

Colonnes attendues (minimum) : hr, spo2, rr, temp, sbp, dbp
Colonnes optionnelles        : ts, rhythm

L'ECG n'étant généralement pas dans un CSV de vitals, il est reconstruit
synthétiquement à partir du champ `rhythm` (ou 'normal'), afin de conserver
un affichage cohérent. Pour un vrai flux ECG, brancher une source WFDB.
"""

from __future__ import annotations

import csv
import time

from app.acquisition.base import DataSource
from app.ai.schemas import VitalsSample
from app.ai.ecg_generator import ECGGenerator


class CSVSource(DataSource):
    mode = "csv"

    def __init__(self, path: str, patient_id: str = "ICU-CSV", loop: bool = True,
                 ecg_samples_per_read: int = 125):
        self.path = path
        self.patient_id = patient_id
        self.loop = loop
        self.ecg_n = ecg_samples_per_read
        self._ecg = ECGGenerator()
        self._rows = self._load()
        self._i = 0

    def _load(self) -> list[dict]:
        with open(self.path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def read(self) -> VitalsSample:
        if not self._rows:
            raise RuntimeError("CSV vide ou introuvable")

        if self._i >= len(self._rows):
            if self.loop:
                self._i = 0
            else:
                self._i = len(self._rows) - 1

        row = self._rows[self._i]
        self._i += 1

        ecg_rhythm = (row.get("ecg_rhythm") or row.get("rhythm") or "normal").strip()
        ecg = self._ecg.get_next_samples(ecg_rhythm, self.ecg_n)

        return VitalsSample(
            patient_id=self.patient_id,
            ts=float(row.get("ts") or time.time()),
            ecg_hr=int(float(row.get("ecg_hr", row.get("hr", 72)))),
            spo2=int(float(row.get("spo2", 98))),
            rr_capno=int(float(row.get("rr_capno", row.get("rr", 16)))),
            nibp_sys=int(float(row.get("nibp_sys", row.get("sbp", 120)))),
            nibp_dia=int(float(row.get("nibp_dia", row.get("dbp", 80)))),
            nibp_map=int(float(row.get("nibp_map", 90))),
            temp_core=round(float(row.get("temp_core", row.get("temp", 37.2))), 1),
            temp_skin=round(float(row.get("temp_skin", 34.5)), 1),
            etco2=int(float(row.get("etco2", 40))),
            vent_mode=row.get("vent_mode", "VCV"),
            vent_fio2=int(float(row.get("vent_fio2", 21))),
            vent_peep=float(row.get("vent_peep", 5.0)),
            vent_vt=int(float(row.get("vent_vt", 500))),
            vent_rr=int(float(row.get("vent_rr", 12))),
            vent_pip=float(row.get("vent_pip", 20.0)),
            vent_mv=float(row.get("vent_mv", 6.0)),
            vent_pplat=float(row.get("vent_pplat", 15.0)),
            cvp=float(row.get("cvp", 5.0)),
            co=float(row.get("co", 5.0)),
            ci=float(row.get("ci", 2.8)),
            icp=float(row.get("icp", 8.0)),
            bis=int(float(row.get("bis", 85))),
            gcs=int(float(row.get("gcs", 14))),
            uo_hour=int(float(row.get("uo_hour", 50))),
            lab_k=float(row.get("lab_k", 4.0)),
            lab_cr=float(row.get("lab_cr", 1.0)),
            lab_hb=float(row.get("lab_hb", 11.0)),
            lab_wbc=float(row.get("lab_wbc", 9.0)),
            lab_plt=float(row.get("lab_plt", 200)),
            abg_ph=float(row.get("abg_ph", 7.38)),
            abg_pao2=float(row.get("abg_pao2", 90.0)),
            abg_paco2=float(row.get("abg_paco2", 40.0)),
            abg_hco3=float(row.get("abg_hco3", 24.0)),
            abg_sat=float(row.get("abg_sat", 97.0)),
            abg_be=float(row.get("abg_be", 0.0)),
            coag_inr=float(row.get("coag_inr", 1.1)),
            ecg_rhythm=ecg_rhythm,
            ecg_samples=[round(float(x), 4) for x in ecg],
            ecg_anomaly_flags=self._ecg.get_last_anomaly_flags(),
            ecg_anomaly_type=self._ecg.get_last_anomaly_type(),
            ecg_waveform_type=row.get("ecg_waveform_type", "II"),
        )
