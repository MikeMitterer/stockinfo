"""Anwendungs-Konfiguration — geladen aus Umgebung/.env via pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Zentrale Einstellungen der StockInfo-App.

    Alle Werte sind über das .env-File oder Umgebungsvariablen überschreibbar.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"

    # Cache / Refresh
    database_path: str = "data/stockinfo.db"
    cache_ttl_hours: int = 6
    refresh_interval_hours: int = 6
    metadata_ttl_days: int = 7

    # ISIN-Auflösung
    default_exchange: str = "XETR"  # bevorzugte Börse für ISIN-Abfragen (MIC)
    openfigi_api_key: str = ""  # optional — höheres Rate-Limit bei OpenFIGI

    # Auth (leer = deaktiviert)
    api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    """Gibt die zwischengespeicherte Settings-Instanz zurück.

    Returns:
        Die einmalig geladene Settings-Instanz (Singleton via lru_cache).
    """
    return Settings()
