"""
app/alerts/manager.py
=====================
Gestion des alertes cliniques.

Transforme les résultats d'agents (severity >= medium) en alertes, avec :
  - déduplication (une alerte active par (signal, event) et par patient) ;
  - priorisation par gravité ;
  - résolution automatique quand le signal redevient normal ;
  - acquittement manuel par un clinicien.

Le calcul de gravité N'EST PAS fait ici (responsabilité des agents) : ce module
ne fait que router/gérer le cycle de vie des alertes.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict

from app.ai.schemas import AISnapshot, severity_rank


ALERT_MIN_SEVERITY = "medium"  # seuil de génération d'alerte


@dataclass
class Alert:
    id: str
    patient_id: str
    signal: str
    event: str
    severity: str
    confidence: int
    message: str
    status: str = "active"          # active / acknowledged / resolved
    created_at: float = field(default_factory=time.time)
    resolved_at: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class AlertManager:
    """État en mémoire des alertes actives par patient (source de vérité chaude)."""

    def __init__(self) -> None:
        # patient_id -> { dedup_key -> Alert }
        self._active: dict[str, dict[str, Alert]] = {}
        # patient_id -> [Alert] (historique récent, borné)
        self._history: dict[str, list[Alert]] = {}

    @staticmethod
    def _dedup_key(signal: str, event: str) -> str:
        return f"{signal}::{event}"

    def evaluate(self, snapshot: AISnapshot) -> tuple[list[Alert], list[Alert]]:
        """
        Compare l'état IA courant aux alertes actives.
        Retourne (nouvelles_alertes, alertes_resolues).
        """
        pid = snapshot.patient_id
        active = self._active.setdefault(pid, {})
        new_alerts: list[Alert] = []
        resolved: list[Alert] = []

        # Signaux actuellement anormaux (>= seuil)
        current_keys: set[str] = set()
        for result in snapshot.agents.values():
            if severity_rank(result.severity) >= severity_rank(ALERT_MIN_SEVERITY):
                key = self._dedup_key(result.signal, result.detected_event)
                current_keys.add(key)
                if key not in active:
                    alert = Alert(
                        id=str(uuid.uuid4()), patient_id=pid, signal=result.signal,
                        event=result.detected_event, severity=result.severity,
                        confidence=result.confidence, message=result.explanation,
                    )
                    active[key] = alert
                    new_alerts.append(alert)
                    self._history.setdefault(pid, []).append(alert)
                else:
                    # met à jour la gravité/confiance de l'alerte existante
                    active[key].severity = result.severity
                    active[key].confidence = result.confidence

        # Résolution : alertes actives dont le signal est redevenu normal
        for key in list(active.keys()):
            if key not in current_keys and active[key].status != "resolved":
                alert = active.pop(key)
                alert.status = "resolved"
                alert.resolved_at = time.time()
                resolved.append(alert)

        # borne l'historique
        hist = self._history.setdefault(pid, [])
        if len(hist) > 200:
            self._history[pid] = hist[-200:]

        return new_alerts, resolved

    def acknowledge(self, patient_id: str, alert_id: str) -> Alert | None:
        for alert in self._active.get(patient_id, {}).values():
            if alert.id == alert_id:
                alert.status = "acknowledged"
                return alert
        return None

    def active_alerts(self, patient_id: str) -> list[Alert]:
        alerts = list(self._active.get(patient_id, {}).values())
        return sorted(alerts, key=lambda a: severity_rank(a.severity), reverse=True)

    def history(self, patient_id: str, limit: int = 50) -> list[Alert]:
        return list(reversed(self._history.get(patient_id, [])))[:limit]
