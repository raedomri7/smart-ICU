"""
app/api/routes/ws.py
====================
Endpoint WebSocket temps réel : /ws

Protocole (voir docs/ARCHITECTURE.md §6) :
  Client → { "type": "subscribe", "patient_id": "ICU-204" }
  Client → { "type": "set_scenario", "scenario": "vtach" }
  Client → { "type": "ack_alert", "alert_id": "..." }
  Server → { "type": "tick", ... } | { "type": "alert", ... } | ...
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.realtime.connection import connection_manager
from app.realtime.stream import stream_hub
from app.services.monitoring import monitoring_service

logger = logging.getLogger("icu.ws")
router = APIRouter()


@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    # Abonnement initial via query param facultatif ?patient_id=
    patient_id = ws.query_params.get("patient_id", "ICU-204")
    await connection_manager.connect(ws, patient_id)
    monitoring_service.get_or_create(patient_id, mode="simulator")
    stream_hub.ensure_running(patient_id)

    try:
        while True:
            msg = await ws.receive_json()
            mtype = msg.get("type")

            if mtype == "subscribe":
                new_pid = msg.get("patient_id", patient_id)
                if new_pid != patient_id:
                    await connection_manager.switch(ws, patient_id, new_pid)
                    patient_id = new_pid
                    monitoring_service.get_or_create(patient_id, mode="simulator")
                    stream_hub.ensure_running(patient_id)

            elif mtype == "set_scenario":
                scenario = msg.get("scenario", "normal")
                monitoring_service.set_scenario(patient_id, scenario)

            elif mtype == "ack_alert":
                alert_id = msg.get("alert_id")
                if alert_id:
                    monitoring_service.alerts.acknowledge(patient_id, alert_id)

    except WebSocketDisconnect:
        await connection_manager.disconnect(ws, patient_id)
    except Exception as exc:
        logger.warning("WS erreur : %s", exc)
        await connection_manager.disconnect(ws, patient_id)
