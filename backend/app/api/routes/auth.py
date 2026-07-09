"""
app/api/routes/auth.py
======================
Authentification JWT. MVP : vérifie contre l'admin seed (config). Extensible
vers une table `users` PostgreSQL sans changer le contrat de l'API.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.config import settings
from app.core.security import create_access_token, verify_password, hash_password
from app.schemas.auth import LoginRequest, TokenResponse, UserDTO
from app.api.deps import get_current_user
from fastapi import Depends

router = APIRouter(prefix="/auth", tags=["auth"])

# Admin seed hashé au chargement (aucun secret en clair persistant)
_SEED_ADMIN = {
    "email": settings.seed_admin_email,
    "role": "admin",
    "full_name": "Administrateur",
    "hashed_password": hash_password(settings.seed_admin_password),
}


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest) -> TokenResponse:
    if body.email == _SEED_ADMIN["email"] and verify_password(body.password, _SEED_ADMIN["hashed_password"]):
        token = create_access_token(subject=body.email, role=_SEED_ADMIN["role"])
        return TokenResponse(access_token=token, role=_SEED_ADMIN["role"])
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")


@router.get("/me", response_model=UserDTO)
def me(user: dict = Depends(get_current_user)) -> UserDTO:
    return UserDTO(email=user["sub"], role=user.get("role", "viewer"))
