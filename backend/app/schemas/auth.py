"""app/schemas/auth.py — DTO Pydantic pour l'authentification."""

from __future__ import annotations

from pydantic import BaseModel


class LoginRequest(BaseModel):
    # str (et non EmailStr) pour accepter les domaines internes type ".local"
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class UserDTO(BaseModel):
    email: str
    full_name: str | None = None
    role: str
