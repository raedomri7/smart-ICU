"""app/api/deps.py — dépendances FastAPI (auth courante)."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import decode_token

_bearer = HTTPBearer(auto_error=False)


def get_current_user(cred: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    if cred is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token manquant")
    payload = decode_token(cred.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide ou expiré")
    return payload
