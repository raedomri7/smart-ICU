"""
app/db/session.py
=================
Gestion optionnelle du moteur async SQLAlchemy.

Si `DATABASE_URL` est vide, `engine`/`SessionLocal` restent None et toute la
persistence est ignorée : le MVP fonctionne en mémoire, sans PostgreSQL.
"""

from __future__ import annotations

import logging

from app.config import settings

logger = logging.getLogger("icu.db")

engine = None
SessionLocal = None


async def init_db() -> None:
    """Initialise le moteur et crée les tables si une DB est configurée."""
    global engine, SessionLocal
    if not settings.db_enabled:
        logger.info("Persistence désactivée (DATABASE_URL vide) — mode mémoire.")
        return

    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from app.db.models import Base

    engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("PostgreSQL connecté, schéma synchronisé.")


async def close_db() -> None:
    if engine is not None:
        await engine.dispose()
