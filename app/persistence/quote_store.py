"""Was Dienste und Router vom Kursspeicher sehen — das Repository-Interface.

Dienste bekommen einen `QuoteStore` per Dependency Injection
(`app/container.py`) und kennen weder Verbindung noch SQL. Die Umsetzung ist
`QuoteRepository` in `app/persistence/repository.py`; Tests dürfen jede andere
Klasse mit denselben Methoden einsetzen.

Hier steht auch, was beide Seiten des Vertrags teilen: der Rückgabetyp
`SavedQuote` und die Feldregel `PROTECTED_META_FIELDS`. Die Umsetzung importiert
sie von hier, nicht umgekehrt — sonst hinge das Interface an ihr.
"""

from dataclasses import dataclass
from typing import Protocol

from app.detail_models import DetailDefinition
from app.models import IdentityOut, QuoteResponse


@dataclass(frozen=True)
class SavedQuote:
    """Was das Speichern eines Kurses am Instrument bewirkt hat.

    `created` ist eine **Tatsache der schreibenden Transaktion**, keine
    Vorabfrage (T-21 Teil 3, `#2j2`). Ein Existenzcheck *vor* dem Schreiben
    wäre falsch: Ein konkurrierender Insert kann ihn überholen, und der
    Aufnahmeweg meldete `201` für ein Papier, das jemand anders gerade angelegt
    hat. Wahr ist `created` deshalb nur, wenn der `INSERT` selbst durchkam —
    im abgefangenen UNIQUE-Rennen ist er falsch.

    Bis T-21 Teil 3 gab `save_quote` nur die ID zurück und warf diese
    Information weg, obwohl sie an der Stelle vorlag, an der sie entsteht.
    """

    instrument_id: int
    created: bool


# Die Felder, über die allein justETF Auskunft gibt.
#
# Sie dürfen nur geschrieben werden, wenn die Antwort tatsächlich von dort
# kommt (`QuoteResponse.metadata_complete`). Sonst löscht ein einzelner
# Ausfall den gesamten gepflegten Stand — genau das ist am 2026-08-18
# passiert. `source` gehört dazu, weil er die stehengebliebenen Werte
# beschreibt und nicht den Abruf, der nichts geliefert hat.
#
# Teil des Vertrags, weil dieselbe Menge zweimal gebraucht wird: Im Repository
# entscheidet sie, was **nicht geschrieben** wird, und in `CachedQuoteService`
# darüber, was in der Antwort aus dem gespeicherten Stand **stehen bleibt**.
# Zwei Listen liefen auseinander, und die Antwort widerspräche der Zeile
# daneben.
PROTECTED_META_FIELDS = frozenset(
    {
        "provider",
        "ter",
        "replication",
        "fund_size",
        "fund_domicile",
        "fund_currency",
        "volatility",
        "accumulating",
        "source",
    }
)


class QuoteStore(Protocol):
    """Kurse, Instrumente, Tagesschlusskurse, Detailwerte und Wechselkurse."""

    # ─── Instrumente ─────────────────────────────────────────────────────────

    def count_instruments(self) -> int: ...

    def list_instruments(self) -> list[dict]: ...

    def list_instruments_with_latest(self) -> list[dict]: ...

    def get_instrument_by_isin(self, isin: str) -> dict | None: ...

    def get_instrument_by_symbol(self, symbol: str) -> dict | None: ...

    def get_instrument_by_identity(self, identity: IdentityOut) -> dict | None: ...

    def get_instrument_by_listing_id(self, listing_id: str) -> dict | None: ...

    def get_instrument_with_latest(self, instrument_id: int) -> dict | None: ...

    def save_instrument(self, resolved: object, fetched_at: str) -> SavedQuote: ...

    def set_isin(self, symbol: str, isin: str) -> None: ...

    def delete_instrument(self, isin: str) -> bool: ...

    def delete_by_symbol(self, symbol: str) -> bool: ...

    # ─── Kurse und Tagesschlusskurse ─────────────────────────────────────────

    def save_quote(self, response: QuoteResponse) -> SavedQuote: ...

    def get_latest_quote(self, instrument_id: int) -> dict | None: ...

    def get_history(
        self,
        instrument_id: int,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 100,
    ) -> list[dict]: ...

    def get_daily_closes(
        self, instrument_id: int, date_from: str | None = None
    ) -> list[dict]: ...

    def upsert_daily_closes(self, instrument_id: int, rows: list[dict]) -> None: ...

    def get_daily_meta(self, instrument_id: int) -> dict | None: ...

    def set_daily_meta(
        self, instrument_id: int, fetched_from: str | None, fetched_to: str | None
    ) -> None: ...

    # ─── Detailwerte und manuelle Eingaben ───────────────────────────────────

    def detail_catalog(
        self, definitions: list[DetailDefinition] | None = None
    ) -> tuple[list[DetailDefinition], int]: ...

    def has_detail_catalog(self) -> bool: ...

    def detail_generation(self) -> str: ...

    def set_volatility(
        self, instrument_id: int, volatility: float, as_of: str | None = None
    ) -> None: ...

    def get_overrides(self, instrument_id: int) -> dict | None: ...

    def set_overrides(
        self,
        instrument_id: int,
        values: dict[str, object],
        updated_at: str,
        currency: str | None = None,
    ) -> None: ...

    def set_detail_overrides(
        self, instrument_id: int, values: dict, updated_at: str
    ) -> None: ...

    # ─── Wechselkurse ────────────────────────────────────────────────────────

    def get_fx_rate(self, base: str, quote: str) -> dict | None: ...

    def save_fx_rate(
        self,
        base: str,
        quote: str,
        rate: float,
        quote_time: str,
        fetched_at: str,
        source: str | None = None,
    ) -> None: ...
