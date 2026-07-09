"""
app/realtime/connection.py
==========================
Gestionnaire de connexions WebSocket, avec abonnement par patient (rooms).
Permet de broadcaster un tick à tous les clients suivant un même patient.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import WebSocket

logger = logging.getLogger("icu.ws")


class ConnectionManager:
    def __init__(self) -> None:
        # patient_id -> set[WebSocket]
        self._rooms: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket, patient_id: str) -> None:
        await ws.accept()
        async with self._lock:
            self._rooms.setdefault(patient_id, set()).add(ws)
        logger.info("Client abonné au patient %s (%d actifs)", patient_id, len(self._rooms[patient_id]))

    async def disconnect(self, ws: WebSocket, patient_id: str) -> None:
        async with self._lock:
            room = self._rooms.get(patient_id)
            if room and ws in room:
                room.discard(ws)
                if not room:
                    self._rooms.pop(patient_id, None)

    async def switch(self, ws: WebSocket, old_pid: str, new_pid: str) -> None:
        await self.disconnect(ws, old_pid)
        async with self._lock:
            self._rooms.setdefault(new_pid, set()).add(ws)

    async def broadcast(self, patient_id: str, message: dict) -> None:
        room = list(self._rooms.get(patient_id, set()))
        dead: list[WebSocket] = []
        for ws in room:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws, patient_id)

    def has_subscribers(self, patient_id: str) -> bool:
        return bool(self._rooms.get(patient_id))


connection_manager = ConnectionManager()
