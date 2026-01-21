"""Configuración de entorno y variables de entorno."""

import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación desde variables de entorno."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Groq Configuration
    groq_api_key: str

    # Supabase Configuration
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    supabase_db_url: Optional[str] = None
    """Cadena de conexión directa a PostgreSQL de Supabase (postgresql://...)"""

    # Application Configuration
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"


# Instancia global de configuración
settings = Settings()
