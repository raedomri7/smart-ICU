"""
app/config.py
=============
Configuration centralisée via variables d'environnement (pydantic-settings).
Aucun secret n'est codé en dur. Copier `.env.example` vers `.env` pour surcharger.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Application ---
    app_name: str = "ICU Smart Monitoring"
    app_version: str = "1.0.0"
    environment: str = "development"

    # --- API / CORS ---
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:3000"

    # --- Sécurité / Auth ---
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720
    seed_admin_email: str = "admin@icu.local"
    seed_admin_password: str = "admin"

    # --- Base de données ---
    # Si vide, la persistence est désactivée (MVP fonctionne sans PostgreSQL).
    database_url: str = ""

    # --- Temps réel ---
    tick_interval_s: float = 1.0        # période de la boucle de streaming
    ecg_samples_per_tick: int = 125     # échantillons ECG poussés par tick

    # --- Gemini (OPTIONNEL — jamais dans la boucle temps réel) ---
    gemini_enabled: bool = False
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def db_enabled(self) -> bool:
        return bool(self.database_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
