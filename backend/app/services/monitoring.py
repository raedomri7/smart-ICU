"""
app/services/monitoring.py
==========================
Service central de monitoring : maintient, par patient, la source de données,
l'orchestrateur IA et l'état d'alertes. Registre en mémoire partagé par le
transport REST et WebSocket.

Une instance de `MonitoringService` est créée au démarrage (lifespan) et
injectée dans les routes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.acquisition.base import DataSource
from app.acquisition.manager import create_source
from app.ai.orchestrator import AIAgentOrchestrator
from app.ai.schemas import AISnapshot
from app.alerts.manager import AlertManager, Alert
from app.config import settings


@dataclass
class PatientMonitor:
    patient_id: str
    source: DataSource
    orchestrator: AIAgentOrchestrator = field(default_factory=AIAgentOrchestrator)
    last_snapshot: AISnapshot | None = None

    def tick(self) -> AISnapshot:
        sample = self.source.read()
        snapshot = self.orchestrator.run(sample)
        self.last_snapshot = snapshot
        return snapshot


class MonitoringService:
    def __init__(self) -> None:
        self._monitors: dict[str, PatientMonitor] = {}
        self.alerts = AlertManager()

    def get_or_create(self, patient_id: str, mode: str = "simulator", **kwargs) -> PatientMonitor:
        if patient_id not in self._monitors:
            source = create_source(
                mode, patient_id,
                ecg_samples_per_read=settings.ecg_samples_per_tick, **kwargs
            )
            self._monitors[patient_id] = PatientMonitor(patient_id=patient_id, source=source)
        return self._monitors[patient_id]

    def set_scenario(self, patient_id: str, scenario: str) -> None:
        monitor = self._monitors.get(patient_id)
        if monitor:
            monitor.source.configure(scenario=scenario)

    def set_source(self, patient_id: str, mode: str, **kwargs) -> PatientMonitor:
        source = create_source(mode, patient_id, ecg_samples_per_read=settings.ecg_samples_per_tick, **kwargs)
        monitor = self._monitors.get(patient_id)
        if monitor:
            monitor.source = source
        else:
            monitor = PatientMonitor(patient_id=patient_id, source=source)
            self._monitors[patient_id] = monitor
        return monitor

    def tick(self, patient_id: str) -> tuple[AISnapshot, list[Alert], list[Alert]]:
        monitor = self.get_or_create(patient_id)
        snapshot = monitor.tick()
        new_alerts, resolved = self.alerts.evaluate(snapshot)
        return snapshot, new_alerts, resolved

    def patients(self) -> list[str]:
        return list(self._monitors.keys())


# Instance partagée (initialisée au lifespan)
monitoring_service = MonitoringService()
