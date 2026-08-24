"""Die Außengrenzen, an denen sonst das Netz hinge — leer und typisiert.

Ein Test, der die echte Kette prüfen will, muss genau **eine** Sorte Ersatz
einsetzen: die Stellen, an denen StockInfo den eigenen Prozess verlässt. Alles
davor und danach soll echter Code sein.

Diese Grenzen sind austauschbar und in fast jedem solchen Test dieselben.
Vorher standen sie viermal nebeneinander (`test_quote_cache.py`,
`test_quote_cache_dashboard.py`, `test_refresh.py` und der neue
Aufnahmewege-Test) — mit dem Ergebnis, dass eine Änderung am Provider-Vertrag
an vier Stellen nachgezogen werden müsste und die vierte Fassung dabei
schwächer war als die anderen: Sie nahm `*args, **kwargs` statt der echten
Signatur und hätte einen gebrochenen Vertrag stillschweigend geschluckt.

**Deshalb hier mit exakter Signatur.** `test_boundaries.py` vergleicht sie
laufend gegen die Protokolle; weicht eine ab, fällt der Test — und nicht erst
der Integrationstest, der sie benutzt.

Szenariospezifisches Verhalten gehört **nicht** hierher: Was ein Test an einer
Grenze konkret zurückgeben lassen will, bleibt bei ihm.
"""

from app.providers.base import EtfDetails
from app.repository import QuoteRepository
from app.services.daily_sync import DailyCloseSync


class EmptyDailyCloseProvider:
    """Liefert nie Tages-Schlusskurse — erfüllt `DailyCloseProvider`.

    Die leere Liste heißt „erfolgreich abgefragt, aber keine Daten" und ist
    damit ausdrücklich **kein** Fehler; dafür stünde ``None``. Für Tests, die
    sich nicht für Volatilität interessieren, ist das der ruhigste Zustand.
    """

    def fetch_daily_closes(
        self, symbol: str, start: str | None = None
    ) -> list[dict] | None:
        return []


def empty_daily_sync(repository: QuoteRepository) -> DailyCloseSync:
    """Ein `DailyCloseSync`, der nie echte Tages-Schlusskurse holt.

    Stand ebenfalls dreimal wortgleich in den Testdateien. Der Sync selbst ist
    **echter** Code — nur seine Quelle ist leer.

    Args:
        repository: Die Persistenz, auf der der Sync arbeitet.

    Returns:
        Ein einsatzfähiger Sync ohne Netz dahinter.
    """
    return DailyCloseSync(repository, EmptyDailyCloseProvider())


class EmptyEtfEnricher:
    """Antwortet auf keine ETF-Frage — erfüllt `EtfEnricher`.

    Die beiden Methoden beantworten verschiedene Fragen, und diese Fassung
    beantwortet beide verneinend: nicht zuständig, keine Daten. Wer den
    Unterschied zwischen „nicht zuständig" und „ausgefallen" prüfen will,
    braucht eine eigene Grenze — hier ist er bewusst nicht abgebildet.
    """

    def is_responsible(
        self,
        isin: str | None,
        *,
        exchange: str | None = None,
        currency: str | None = None,
    ) -> bool:
        return False

    def fetch_etf(
        self,
        isin: str | None,
        symbol: str | None = None,
        *,
        exchange: str | None = None,
        currency: str | None = None,
    ) -> EtfDetails | None:
        return None
