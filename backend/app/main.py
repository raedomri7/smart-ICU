"""
app/main.py
===========
Point d'entrée FastAPI — assemble routers REST + WebSocket, CORS, lifespan.

Lancer :
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logging import setup_logging
from app.db.session import init_db, close_db
from app.api.routes import auth, patients, alerts, ai, ws, reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logging.getLogger("icu").info("Démarrage %s v%s", settings.app_name, settings.app_version)
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Plateforme IA de surveillance ICU — acquisition, IA multi-agent, "
                "décision clinique, alertes et prédiction en temps réel.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers REST ---
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(patients.router, prefix=settings.api_prefix)
app.include_router(alerts.router, prefix=settings.api_prefix)
app.include_router(ai.router, prefix=settings.api_prefix)
app.include_router(reports.router, prefix=settings.api_prefix)

# --- WebSocket (hors préfixe API) ---
app.include_router(ws.router)


@app.get("/health", tags=["system"])
def health() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "db_enabled": settings.db_enabled,
        "gemini_enabled": settings.gemini_enabled,
    }
