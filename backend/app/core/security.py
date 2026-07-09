"""
app/core/security.py
====================
Sécurité : hachage de mot de passe (bcrypt) et jetons JWT.

MVP : un utilisateur admin seed en mémoire si la DB est désactivée.
"""

from __future__ import annotations

import time
from typing import Any

import bcrypt
import jwt

from app.config import settings


def hash_password(password: str) -> str:
    # bcrypt limite l'entrée à 72 octets — on tronque explicitement.
    pw = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(subject: str, role: str) -> str:
    now = int(time.time())
    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + settings.jwt_expire_minutes * 60,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except Exception:
        return None
