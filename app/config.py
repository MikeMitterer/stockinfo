"""Anwendungs-Konfiguration — geladen aus Umgebung/.env via pydantic-settings."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.exchanges import DEFAULT_EXCHANGE


class Settings(BaseSettings):
    """Zentrale Einstellungen der StockInfo-App.

    Alle Werte sind über das .env-File oder Umgebungsvariablen überschreibbar.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server — gebunden wird in Procfile.dev bzw. im Container-CMD; hier nur für
    # GET /env. Lokal ist 127.0.0.1 die Vorgabe, das Image setzt HOST=0.0.0.0.
    host: str = "127.0.0.1"
    port: int = 8000

    # Cache / Refresh
    database_path: str = "data/stockinfo.db"
    cache_ttl_hours: int = 6
    # Intervall des Hintergrund-Refresh: REFRESH_INTERVAL_MINUTES geht vor, sonst gilt
    # REFRESH_INTERVAL_HOURS. Ein Wert ≤ 0 bricht den Start ab, statt still zu wirken.
    refresh_interval_hours: int = Field(default=6, gt=0)
    refresh_interval_minutes: int | None = Field(default=None, gt=0)
    # Erster Refresh direkt nach dem Start des Schedulers, nicht erst nach einem Intervall.
    refresh_on_start: bool = True
    metadata_ttl_days: int = 7
    fx_ttl_hours: int = 1  # maximales Alter eines Devisenkurses, bevor neu geholt wird

    # ISIN-Auflösung
    default_exchange: str = DEFAULT_EXCHANGE  # bevorzugte Börse für ISIN-Abfragen (MIC)
    strict_exchange: bool = False  # True = nur Default-Börse, sonst 404 (kein Fallback)
    openfigi_api_key: str = ""  # optional — höheres Rate-Limit bei OpenFIGI

    # Dashboard / CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    # Profil-Links (Platzhalter {isin} bzw. {symbol})
    extraetf_etf_url: str = "https://extraetf.com/de/etf-profile/{isin}"
    extraetf_stock_url: str = "https://extraetf.com/de/stock-profile/{isin}"
    yahoo_url: str = "https://de.finance.yahoo.com/quote/{symbol}/"

    # Statisches Dashboard — Verzeichnis mit dem gebauten Vue-Bundle.
    # Existiert es nicht (z.B. lokaler Dev), wird nichts ausgeliefert.
    static_dir: str = "/app/web"

    @field_validator("refresh_interval_minutes", mode="before")
    @classmethod
    def _empty_minutes_mean_unset(cls, value: object) -> object:
        """Ein leerer Wert (etwa ein leeres Feld im Unraid-Template) gilt als nicht gesetzt."""
        return None if value == "" else value

    @property
    def refresh_minutes(self) -> int:
        """Wirksames Refresh-Intervall in Minuten: die Minuten-Angabe, sonst Stunden × 60."""
        return self.refresh_interval_minutes or self.refresh_interval_hours * 60


@lru_cache
def get_settings() -> Settings:
    """Gibt die zwischengespeicherte Settings-Instanz zurück.

    Returns:
        Die einmalig geladene Settings-Instanz (Singleton via lru_cache).
    """
    return Settings()
