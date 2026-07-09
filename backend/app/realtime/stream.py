"""
app/realtime/stream.py
======================
Boucle de streaming temps réel par patient.

Pour chaque patient ayant des abonnés WS, une tâche async :
  1. lit la source                     (acquisition)
  2. exécute les agents IA             (traitement local, synchrone)
  3. évalue les alertes                (cycle de vie)
  4. broadcaste le tick + alertes      (transport WS)

La persistence PostgreSQL (si activée) est faite hors du chemin critique.
Gemini n'est JAMAIS appelé ici.
"""

from __future__ import annotations

import asyncio
import logging

from app.config import settings
from app.services.monitoring import monitoring_service
from app.realtime.connection import connection_manager

logger = logging.getLogger("icu.stream")


class StreamHub:
    """Gère une tâche de streaming par patient, démarrée à la demande."""

    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task] = {}

    def ensure_running(self, patient_id: str) -> None:
        if patient_id in self._tasks and not self._tasks[patient_id].done():
            return
        self._tasks[patient_id] = asyncio.create_task(self._run(patient_id))

    async def _run(self, patient_id: str) -> None:
        logger.info("Démarrage du flux temps réel pour %s", patient_id)
        try:
            while connection_manager.has_subscribers(patient_id):
                snapshot, new_alerts, resolved = monitoring_service.tick(patient_id)

                await connection_manager.broadcast(patient_id, {
                    "type": "tick",
                    **snapshot.to_public_dict(),
                })

                for alert in new_alerts:
                    await connection_manager.broadcast(patient_id, {
                        "type": "alert", "alert": alert.to_dict(),
                    })
                for alert in resolved:
                    await connection_manager.broadcast(patient_id, {
                        "type": "alert_resolved", "alert": alert.to_dict(),
                    })

                await asyncio.sleep(settings.tick_interval_s)
        except asyncio.CancelledError:
            pass
        finally:
            logger.info("Arrêt du flux temps réel pour %s", patient_id)
            self._tasks.pop(patient_id, None)


stream_hub = StreamHub()
