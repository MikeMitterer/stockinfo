"""Tests für den cachenden FX-Service."""

from pathlib import Path

import pytest

from app.db import init_db
from app.repository import QuoteRepository
from app.services.fx_service import CachedFxService, FxUnavailableError


@pytest.fixture
def repo(tmp_path: Path) -> QuoteRepository:
    db_path = str(tmp_path / "fx.db")
    init_db(db_path)
    return QuoteRepository(db_path)


class _FakeFx:
    #: Wie jede Kettenquelle nennt auch dieses Double seinen Namen — seit
    #: T-37 steht `name` im `FxRateProvider`-Protokoll.
    name = "yfinance"

    def __init__(self, rate: float | None) -> None:
        self.rate = rate
        self.calls = 0

    def fetch_fx_rate(self, base: str, quote: str) -> float | None:
        self.calls += 1
        return self.rate


def test_gleiche_waehrung_ist_eins_ohne_fetch(repo: QuoteRepository) -> None:
    provider = _FakeFx(None)
    service = CachedFxService(provider, repo, ttl_hours=1)
    result = service.get_rate("EUR", "EUR")
    assert result.rate == 1.0
    assert result.source == "identity"
    assert provider.calls == 0


def test_miss_holt_live_und_speichert(repo: QuoteRepository) -> None:
    provider = _FakeFx(1.15)
    service = CachedFxService(provider, repo, ttl_hours=1)
    result = service.get_rate("eur", "usd")  # wird normalisiert
    assert result.base == "EUR" and result.quote == "USD"
    assert result.rate == 1.15 and result.cached is False
    # zweiter Aufruf → Cache, kein weiterer Fetch
    provider.rate = 999.0
    again = service.get_rate("EUR", "USD")
    assert again.rate == 1.15 and again.cached is True and provider.calls == 1


def test_fetch_fehler_mit_cache_liefert_stale(repo: QuoteRepository) -> None:
    repo.save_fx_rate("EUR", "USD", 1.10, "2020-01-01T00:00:00+00:00",
                      "2020-01-01T00:00:00+00:00")  # uralt → nicht fresh
    provider = _FakeFx(None)  # Fetch schlägt fehl
    service = CachedFxService(provider, repo, ttl_hours=1)
    result = service.get_rate("EUR", "USD")
    assert result.rate == 1.10 and result.stale is True


def test_fetch_fehler_ohne_cache_wirft(repo: QuoteRepository) -> None:
    service = CachedFxService(_FakeFx(None), repo, ttl_hours=1)
    with pytest.raises(FxUnavailableError):
        service.get_rate("EUR", "USD")


def test_die_devisenherkunft_nennt_die_quelle_die_geliefert_hat(
    repo: QuoteRepository,
) -> None:
    """**Die FX-Gegenprobe, die Codex in Runde 2 verlangt hat.**

    Bei `fx.source` sagt der Vertrag ausdrücklich „Woher der **Kurs** stammt"
    — anders als bei `quote.source`, wo es die Metadaten sind. Zwei Felder mit
    demselben Namen und verschiedener Bedeutung; genau daran ist der erste
    Anlauf gescheitert, der beide über einen Kamm schor.

    Hier steht deshalb wirklich der Lieferant. Geprüft mit einem **anderen**
    Namen als dem eingebauten, sonst bestünde der Test auch dann, wenn die
    Konstante `"yfinance"` zurückkäme.
    """

    class FileFxSource(_FakeFx):
        name = "fx-file"

    service = CachedFxService(FileFxSource(0.6412), repo, ttl_hours=6)

    assert service.get_rate("CAD", "EUR").source == "fx-file"


def test_eine_namenlose_devisenquelle_erfindet_keinen_namen(
    repo: QuoteRepository,
) -> None:
    """Derselbe Rückfall wie beim Kurs: ``None``, kein deutsches Ersatzwort.

    ``"unbekannt"`` stand hier im ersten Anlauf und wäre in der englischen
    Oberfläche unübersetzt erschienen — `source` wird roh angezeigt.
    """

    class NamelessFxSource(_FakeFx):
        name = ""

    service = CachedFxService(NamelessFxSource(0.6412), repo, ttl_hours=6)

    assert service.get_rate("CAD", "EUR").source is None


def test_die_herkunft_ueberlebt_den_cache(repo: QuoteRepository) -> None:
    """**Der Befund aus Codex-Runde 3 — die Herkunft ging beim Cachen verloren.**

    `fx_rates` speicherte sie gar nicht, und der Leseweg setzte ersatzweise
    ``"cache"`` ein. Das ist doppelt falsch: `cached: true` sagt bereits, dass
    der Wert aus dem Cache kommt, und `fx.source` beantwortet laut Vertrag die
    **andere** Frage — woher der Kurs stammt. Nach genau einem Treffer war der
    Lieferant nicht mehr feststellbar.

    Geprüft werden alle drei Wege mit einem **nicht eingebauten** Namen; mit
    `"yfinance"` bestünde der Test auch dann, wenn die alte Konstante
    zurückkäme.
    """

    class FileFxSource(_FakeFx):
        name = "fx-file"

    provider = FileFxSource(0.6412)
    service = CachedFxService(provider, repo, ttl_hours=6)

    fresh = service.get_rate("CAD", "EUR")
    assert fresh.source == "fx-file"
    assert fresh.cached is False

    # Zweiter Aufruf: aus dem frischen Cache — und **derselbe** Lieferant.
    from_cache = service.get_rate("CAD", "EUR")
    assert from_cache.cached is True, "der zweite Aufruf holt nicht neu"
    assert provider.calls == 1, "es wurde doch neu geholt"
    assert from_cache.source == "fx-file", (
        "die Herkunft ist beim Cachen verloren gegangen"
    )


def test_die_herkunft_ueberlebt_auch_einen_stale_treffer(
    repo: QuoteRepository,
) -> None:
    """Der dritte Weg: abgelaufener Cache, Quelle antwortet nicht mehr.

    Dann wird der alte Wert als `stale` geliefert — und auch er muss sagen,
    **wer** ihn geliefert hat. Gerade hier zählt es: Ein veralteter Kurs ohne
    Herkunft lässt sich nicht einordnen.
    """

    class FileFxSource(_FakeFx):
        name = "fx-file"

    service = CachedFxService(FileFxSource(0.6412), repo, ttl_hours=6)
    service.get_rate("CAD", "EUR")

    # TTL 0 macht den gespeicherten Wert alt; die Quelle liefert nichts mehr.
    failing_service = CachedFxService(FileFxSource(None), repo, ttl_hours=0)
    stale = failing_service.get_rate("CAD", "EUR")

    assert stale.stale is True
    assert stale.source == "fx-file"


# ─── Die konfigurierte Reihenfolge wird abgefragt ─────────────────────────────


class _NamedFx(_FakeFx):
    """Eine Devisenquelle mit eigenem Namen — für die Herkunftsprüfung."""

    def __init__(self, name: str, rate: float | None) -> None:
        super().__init__(rate)
        self.name = name


def test_der_erste_kurs_gewinnt(repo: QuoteRepository) -> None:
    """Wer zuerst liefert, gewinnt — und danach wird niemand mehr gefragt.

    Ein Wechselkurs kostet bei jedem Anbieter ein Ratenlimit. Alle zu fragen
    und dann auszuwählen wäre teurer und würde nichts besser machen: Die
    Reihenfolge in `sources.yaml` *ist* die Auswahl.
    """
    first = _NamedFx("yfinance", 0.9)
    second = _NamedFx("yaml-file", 0.6412)

    result = CachedFxService([first, second], repo, ttl_hours=1).get_rate("CAD", "EUR")

    assert result.rate == 0.9
    assert result.source == "yfinance"
    assert second.calls == 0, "die zweite Quelle wurde trotz Treffer gefragt"


def test_ein_fehlschlag_faellt_zur_naechsten_quelle(repo: QuoteRepository) -> None:
    """**Die Zusage, an der es hing** — und die Herkunft muss mitwandern.

    Der gespeicherte `source` muss die Quelle nennen, die den Kurs *wirklich*
    geliefert hat. Stünde dort die erste, läse ein Betreiber „yfinance" über
    einem Wert, den seine Datei beigesteuert hat — und suchte den Fehler bei
    einem Anbieter, der gar nicht geantwortet hat.
    """
    first = _NamedFx("yfinance", None)
    second = _NamedFx("yaml-file", 0.6412)

    result = CachedFxService([first, second], repo, ttl_hours=1).get_rate("CAD", "EUR")

    assert result.rate == 0.6412
    assert result.source == "yaml-file", "die Herkunft nennt die falsche Quelle"
    assert first.calls == 1 and second.calls == 1


def test_die_herkunft_der_zweiten_quelle_ueberlebt_den_cache(
    repo: QuoteRepository,
) -> None:
    """Wie der Fall weiter oben, aber für die Quelle **hinter** der ersten.

    Der Unterschied ist der Prüfgegenstand: Dort steht die Herkunft schon beim
    Speichern fest, hier entsteht sie erst in der Schleife. Eine Fassung, die
    den Namen aus `self._provider` nimmt statt aus dem Schleifenlauf, bestünde
    den Test darüber und fiele hier durch.
    """
    first = _NamedFx("yfinance", None)
    second = _NamedFx("yaml-file", 0.6412)
    service = CachedFxService([first, second], repo, ttl_hours=1)

    service.get_rate("CAD", "EUR")
    from_cache = service.get_rate("CAD", "EUR")

    assert from_cache.cached is True
    assert from_cache.source == "yaml-file"
    assert second.calls == 1, "trotz frischem Cache wurde erneut beschafft"


def test_erst_nach_dem_gesamtausfall_greift_der_stale_cache(
    repo: QuoteRepository,
) -> None:
    """Der gespeicherte Stand ist der **letzte** Ausweg, nicht der zweite.

    Solange irgendeine konfigurierte Quelle antwortet, ist ein veralteter Wert
    die schlechtere Auskunft. Erst wenn alle geschwiegen haben, ist er besser
    als nichts.
    """
    working = _NamedFx("yaml-file", 0.6412)
    CachedFxService([working], repo, ttl_hours=0).get_rate("CAD", "EUR")

    dead = [_NamedFx("yfinance", None), _NamedFx("yaml-file", None)]
    stale = CachedFxService(dead, repo, ttl_hours=0).get_rate("CAD", "EUR")

    assert stale.stale is True
    assert stale.source == "yaml-file", "die gespeicherte Herkunft ging verloren"
    assert [source.calls for source in dead] == [1, 1], (
        "nicht jede Quelle wurde gefragt, bevor der alte Wert herhalten musste"
    )


def test_ohne_cache_bleibt_der_typisierte_fehler(repo: QuoteRepository) -> None:
    """Alle Quellen stumm und nichts gespeichert — dann der bekannte Fehler.

    Das Verhalten ändert sich durch die Kaskade **nicht**; es tritt nur später
    ein. Der Aufrufer sieht denselben Fall wie bisher.
    """
    sources = [_NamedFx("yfinance", None), _NamedFx("yaml-file", None)]

    with pytest.raises(FxUnavailableError):
        CachedFxService(sources, repo, ttl_hours=1).get_rate("CAD", "EUR")

    assert [source.calls for source in sources] == [1, 1]


def test_eine_einzelne_quelle_bleibt_zulaessig(repo: QuoteRepository) -> None:
    """Eine einzelne Quelle bleibt als direkte Aufrufform gültig.

    Eine Signaturänderung, die jeden Aufrufer bricht, wäre für dieselbe
    Wirkung teurer; die Kaskade ist eine Erweiterung, kein Umbau.
    """
    provider = _NamedFx("yfinance", 0.9)

    result = CachedFxService(provider, repo, ttl_hours=1).get_rate("CAD", "EUR")

    assert result.rate == 0.9 and result.source == "yfinance"
