"""
app/acquisition/manager.py
==========================
Fabrique et sélectionne la source de données active pour un patient.

Point d'extension unique pour brancher de nouvelles sources (moniteur réel,
API médicale) : ajouter un cas dans `create_source()`.
"""

from __future__ import annotations

from app.acquisition.base import DataSource
from app.acquisition.simulator import MonitorSimulatorSource
from app.acquisition.csv_source import CSVSource


def create_source(mode: str, patient_id: str, **kwargs) -> DataSource:
    """Instancie la source correspondant au mode demandé."""
    mode = (mode or "simulator").lower()

    if mode == "simulator":
        return MonitorSimulatorSource(
            patient_id=patient_id,
            scenario=kwargs.get("scenario", "normal"),
            ecg_samples=kwargs.get("ecg_samples", 125),
        )
    if mode == "csv":
        return CSVSource(
            path=kwargs["path"],
            patient_id=patient_id,
            loop=kwargs.get("loop", True),
            ecg_samples_per_read=kwargs.get("ecg_samples_per_read", 125),
        )

    # Extensible : "monitor" (HL7/constructeur), "api" (API hospitalière), "ws_in"
    raise ValueError(f"Mode d'acquisition non supporté : {mode!r}")
