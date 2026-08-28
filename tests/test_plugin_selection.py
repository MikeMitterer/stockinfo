"""Die Konfiguration entscheidet, welches Plugin läuft — CSV oder echter Anbieter.

Das ist die Aussage, an der T-23 hängt: Zwei Plugins beantworten dieselbe Frage
in derselben Rolle, und **nur** `sources.yaml` bestimmt, welches. Kein
`if` im Code, keine Umgebungsvariable, keine Sonderbehandlung für das eine oder
das andere.

Der Nutzen ist nicht Theorie. Ein CSV-Plugin macht die App ohne Netz
betreibbar — für einen Test, für eine Vorführung, für jemanden, der offline
etwas nachstellen will. Dass dafür keine Zeile Anwendungscode anders läuft, ist
der ganze Punkt der Registry.

Beide Wege sind hier geprüft: Der CSV-Weg läuft **ohne Netz** und deshalb bei
jedem Commit mit; der echte Anbieter steht daneben in
`test_plugin_yfinance_integration.py` unter dem Marker `integration`.
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from stockinfo_plugin import FxRate, FxRequest, Quote, QuoteRequest

from app.config import Settings
from app.plugin_loader import load_all
from app.plugins.yfinance_quotes import YFinancePlugin
from app.sources_config import SourcesConfig
from app.sources_registry import build_chain, describe_chain, register_loaded

CLOSES = """ticker;mic;date;close;currency
EUNL;XETR;2026-01-02;95.10;EUR
EUNL;XETR;2026-01-03;95.80;EUR
RY;XTSE;2026-01-03;141.55;CAD
"""

FX = """base;quote;rate;date
EUR;CHF;0.9376;2026-01-03
"""

# So sieht eine Datei in `data/plugins/` wirklich aus: eigenständig, ohne
# Abhängigkeit auf ein Paket dieses Repositories. Sie liegt hier als Text und
# nicht als Import, weil sie **im Test genau den Weg nimmt, den sie beim
# Betreiber nimmt** — von der Platte geladen, nicht aus dem Suchpfad geholt.
PLUGIN = '''
"""Kurse und Wechselkurse aus zwei CSV-Dateien."""

import csv
from datetime import date, datetime, time, timezone

from stockinfo_plugin import (
    FxRate,
    FxRequest,
    NotFound,
    Quote,
    QuoteRequest,
    Unavailable,
)
from stockinfo_plugin.sources import FxSource, QuoteSource


def _rows(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


def _at_midnight(day):
    return datetime.combine(date.fromisoformat(day), time.min, tzinfo=timezone.utc)


class CsvQuoteSource(QuoteSource):
    """Der letzte Eintrag je Papier ist der Kurs."""

    name = "csv-quotes"

    def handles(self, request):
        return bool(request.ticker and request.mic)

    def fetch_quote(self, request):
        rows = [
            row
            for row in _rows(self._config["path"])
            if row["ticker"] == request.ticker and row["mic"] == request.mic
        ]
        if not rows:
            return NotFound()
        currencies = {r["currency"] for r in rows}
        if len(currencies) > 1:
            return Unavailable(f"gemischte Waehrungen: {sorted(currencies)}")
        last = rows[-1]
        return Quote(
            price=float(last["close"]),
            currency=last["currency"],
            as_of=_at_midnight(last["date"]),
        )


class CsvFxSource(FxSource):
    """Ein Wechselkurs je Zeile."""

    name = "csv-fx"

    def handles(self, request):
        return bool(request.base and request.quote)

    def fetch_rate(self, request):
        for row in _rows(self._config["path"]):
            if row["base"] == request.base and row["quote"] == request.quote:
                return FxRate(
                    base=request.base,
                    quote=request.quote,
                    rate=float(row["rate"]),
                    as_of=_at_midnight(row["date"]),
                )
        return NotFound()


SOURCES = [CsvQuoteSource, CsvFxSource]
'''


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    """Ein Datenverzeichnis, wie ein Betreiber es hätte: Tabellen und ein Plugin."""
    (tmp_path / "closes.csv").write_text(CLOSES, encoding="utf-8")
    (tmp_path / "fx.csv").write_text(FX, encoding="utf-8")
    plugins = tmp_path / "plugins"
    plugins.mkdir()
    (plugins / "aus_dateien.py").write_text(PLUGIN, encoding="utf-8")
    return tmp_path


@pytest.fixture(autouse=True)
def _leere_registry():
    """Kein Test erbt die geladenen Plugins eines anderen."""
    register_loaded(())
    yield
    register_loaded(())


def _config(chains: dict[str, tuple[str, ...]], providers: dict) -> SourcesConfig:
    """Eine Konfiguration, wie `sources.yaml` sie ergäbe."""
    return SourcesConfig(chains=chains, providers=providers)


def test_die_konfiguration_waehlt_das_csv_plugin(data_dir: Path) -> None:
    """`quotes: [csv-quotes]` — und die Kurse kommen aus der Datei.

    Der Beweis ist der **Kurs selbst**: `95.80` steht in der CSV und sonst
    nirgends. Ein Test, der nur den Typ der gebauten Quelle prüft, bewiese, dass
    die Registry etwas gebaut hat — nicht, dass die App diesen Wert benutzt.

    Dass es der **letzte** Eintrag ist und nicht der erste, ist ebenfalls eine
    Aussage: Die Datei trägt zwei Tage, und ein Plugin, das den ersten nähme,
    lieferte einen alten Kurs, ohne dass ein Test es merkte.
    """
    register_loaded(load_all(data_dir).specs)
    config = _config(
        {"quotes": ("csv-quotes",)},
        {"csv-quotes": {"path": str(data_dir / "closes.csv")}},
    )

    chain = build_chain("quotes", config, Settings())

    assert len(chain) == 1
    answer = chain[0].fetch_quote(QuoteRequest(ticker="EUNL", mic="XETR"))
    assert isinstance(answer, Quote), answer
    assert answer.price == 95.80, "der letzte Eintrag der Datei"
    assert answer.currency == "EUR"


def test_die_tabelle_unterscheidet_die_papiere(data_dir: Path) -> None:
    """**Die Gegenprobe zu einem Fehler, den ich beim Schreiben hatte.**

    Mein erster Entwurf filterte nach `isin` — die `QuoteRequest` trägt aber
    `ticker` und `mic`. Der Filter lief damit ins Leere, und das Plugin hätte
    für **jedes** Papier denselben Kurs geliefert. Mit nur einer Zeile in der
    Tabelle wäre das nie aufgefallen: Der Test wäre grün gewesen, weil zufällig
    die richtige Zeile die einzige war.

    Deshalb trägt die Tabelle zwei Papiere, und der Test fragt nach dem
    zweiten. Ein Plugin, das die Frage ignoriert, liefert hier `95.80` in `EUR`
    statt `141.55` in `CAD`.
    """
    register_loaded(load_all(data_dir).specs)
    chain = build_chain(
        "quotes",
        _config(
            {"quotes": ("csv-quotes",)},
            {"csv-quotes": {"path": str(data_dir / "closes.csv")}},
        ),
        Settings(),
    )

    antwort = chain[0].fetch_quote(QuoteRequest(ticker="RY", mic="XTSE"))

    assert isinstance(antwort, Quote), antwort
    assert (antwort.price, antwort.currency) == (141.55, "CAD")


def test_ein_unbekanntes_papier_ist_not_found(data_dir: Path) -> None:
    """„Steht nicht in der Tabelle" ist eine Antwort, keine Störung."""
    register_loaded(load_all(data_dir).specs)
    chain = build_chain(
        "quotes",
        _config(
            {"quotes": ("csv-quotes",)},
            {"csv-quotes": {"path": str(data_dir / "closes.csv")}},
        ),
        Settings(),
    )

    antwort = chain[0].fetch_quote(QuoteRequest(ticker="GIBTESNICHT", mic="XETR"))

    assert type(antwort).__name__ == "NotFound"


def test_dieselbe_rolle_mit_dem_echten_anbieter(data_dir: Path) -> None:
    """`quotes: [yfinance]` — dieselbe Rolle, anderes Plugin, kein Codeunterschied.

    Der Anbieter wird hier **nicht** wirklich gefragt: Das Plugin bekommt eine
    Anbindung hereingereicht. Geprüft wird die Auswahl, nicht das Netz — dafür
    gibt es den Integrationstest.
    """
    register_loaded(load_all(data_dir).specs)
    config = _config({"quotes": ("yfinance",)}, {})

    chain = build_chain("quotes", config, Settings())

    assert len(chain) == 1
    assert not isinstance(chain[0], YFinancePlugin), (
        "die eingebaute Quelle ist weiterhin die verdrahtete — das Plugin "
        "danebenzustellen wäre eine zweite Fassung derselben Anbindung"
    )


def test_beide_plugins_stehen_gleichwertig_in_der_auskunft(data_dir: Path) -> None:
    """`GET /sources` liest dieselbe Entscheidung wie der Bauweg.

    Zwei getrennte Auswertungen hätten sich beim ersten Sonderfall
    unterschieden — und ausgerechnet die Diagnose hätte dann das Falsche
    gemeldet.
    """
    register_loaded(load_all(data_dir).specs)
    config = _config(
        {"quotes": ("csv-quotes",), "fx": ("csv-fx",)},
        {
            "csv-quotes": {"path": str(data_dir / "closes.csv")},
            "csv-fx": {"path": str(data_dir / "fx.csv")},
        },
    )

    quotes = describe_chain("quotes", config)
    fx = describe_chain("fx", config)

    assert [entry.name for entry in quotes] == ["csv-quotes"]
    assert quotes[0].usable is True
    assert [entry.name for entry in fx] == ["csv-fx"]
    assert fx[0].usable is True


def test_ein_csv_plugin_beantwortet_auch_die_devisenrolle(data_dir: Path) -> None:
    """Zwei Rollen aus einer Datei — der Offline-Betrieb ist damit vollständig."""
    register_loaded(load_all(data_dir).specs)
    config = _config(
        {"fx": ("csv-fx",)}, {"csv-fx": {"path": str(data_dir / "fx.csv")}}
    )

    chain = build_chain("fx", config, Settings())
    answer = chain[0].fetch_rate(FxRequest(base="EUR", quote="CHF"))

    assert isinstance(answer, FxRate), answer
    assert answer.rate == 0.9376


def test_ein_geladenes_plugin_ist_gekapselt(data_dir: Path) -> None:
    """Fremder Code bekommt die Kapsel, eingebauter nicht.

    Der Unterschied ist am gebauten Objekt sichtbar: Das geladene Plugin trägt
    einen Schutzschalter, die eingebaute Quelle nicht. Ohne diesen Test wäre
    die Kapselung eine Zeile in `build_chain`, die niemand belegt.
    """
    register_loaded(load_all(data_dir).specs)
    aus_datei = build_chain(
        "quotes",
        _config(
            {"quotes": ("csv-quotes",)},
            {"csv-quotes": {"path": str(data_dir / "closes.csv")}},
        ),
        Settings(),
    )[0]
    eingebaut = build_chain("quotes", _config({"quotes": ("yfinance",)}, {}), Settings())[0]

    assert hasattr(aus_datei, "breaker"), "geladenes Plugin ist gekapselt"
    assert not hasattr(eingebaut, "breaker"), "eingebaute Quelle bleibt unverpackt"


def test_ein_unbekannter_mic_liefert_keinen_geratenen_kurs() -> None:
    """**Gemessen, und deshalb steht der Test hier.**

    `provider_alias('RY', 'ZZZZ')` liefert den nackten Ticker `'RY'` — für die
    US-Plätze ohne Alias ist das richtig, für eine unbekannte Börse still
    falsch: yfinance läse `'RY'` als NYSE-Listing und lieferte einen Kurs in
    der falschen Währung, ohne dass irgendwo ein Fehler entstünde.

    Der Client ist einer, dessen Benutzung ein Fehler ist: Ohne ihn bewiese der
    Test nur, dass `NotResponsible` herauskommt — nicht, dass unterwegs niemand
    gefragt wurde.
    """

    class VerbotenerProvider:
        def fetch_quote(self, symbol: str) -> object:
            raise AssertionError(f"es wurde nach {symbol!r} gefragt")

    plugin = YFinancePlugin(provider=VerbotenerProvider())
    request = QuoteRequest(ticker="RY", mic="ZZZZ")

    assert plugin.handles(request) is False
    answer = plugin.fetch_quote(request)
    assert type(answer).__name__ == "NotResponsible"


def test_ein_kurs_ohne_waehrung_ist_keiner() -> None:
    """Er sähe in der Datenbank aus wie ein Wert und wäre eine Zahl ohne Bedeutung."""

    class OhneWaehrung:
        def fetch_quote(self, symbol: str) -> object:
            class Raw:
                price = 95.1
                currency = None
                volume = None
                quote_time = datetime.now(timezone.utc).isoformat()

            return Raw()

    plugin = YFinancePlugin(provider=OhneWaehrung())

    answer = plugin.fetch_quote(QuoteRequest(ticker="EUNL", mic="XETR"))

    assert type(answer).__name__ == "Unavailable"
    assert "ohne Währung" in answer.error
