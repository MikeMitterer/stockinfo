"""Tests der Börsentabelle und der Symbol-Rückrechnung (T-21)."""

from dataclasses import replace

import pytest

from app.exchanges import (
    EXCHANGES,
    REASON_AMBIGUOUS_SUFFIX,
    identity_form,
    identity_from_input,
    input_failure,
    is_real_mic,
    split_symbol,
)


@pytest.mark.parametrize(
    ("symbol", "expected"),
    [
        ("EUNL.DE", ("EUNL", "XETR")),
        ("XIC.TO", ("XIC", "XTSE")),
        ("EQQQ.MI", ("EQQQ", "XMIL")),
        ("7203.T", ("7203", "XTKS")),
    ],
)
def test_bekannte_suffixe_sind_eindeutig_umkehrbar(
    symbol: str, expected: tuple[str, str]
) -> None:
    """Die Rückrechnung funktioniert, weil kein Suffix doppelt vergeben ist."""
    assert split_symbol(symbol) == expected


@pytest.mark.parametrize(
    "symbol",
    [
        "AAPL",       # suffixlos → kein Handelsplatz bestimmbar
        "BRK-B",      # fremde Schreibweise aus der Yahoo-Suche
        "EUNL.XYZ",   # Suffix, das die Tabelle nicht kennt
        ".DE",        # kein Ticker vor dem Punkt
        "",           # leer
    ],
)
def test_unklare_symbole_werden_nicht_geraten(symbol: str) -> None:
    """Im Zweifel ``(None, None)`` — die Zeile bleibt offen und sichtbar.

    Jede dieser Vermutungen wäre plausibel und keine davon belegt: `AAPL`
    könnte an der NYSE oder der NASDAQ liegen, `BRK-B` könnte `BRK.B` meinen.
    Geraten wird nichts.
    """
    assert split_symbol(symbol) == (None, None)


def test_kein_suffix_ist_doppelt_vergeben() -> None:
    """Die Voraussetzung der ganzen Rückrechnung — hier festgehalten.

    Käme eine Börse mit einem schon belegten Alias dazu, wäre `split_symbol`
    stillschweigend mehrdeutig. Dieser Test schlägt dann an, statt dass die
    Migration ein falsches Listing zuordnet.

    Leere Aliase sind ausgenommen: Die fünf US-Plätze teilen sich den leeren,
    und genau deshalb ist `AAPL` nicht rückrechenbar.
    """
    aliases = [
        definition.alias for definition in EXCHANGES.values() if definition.alias
    ]

    assert len(aliases) == len(set(aliases))


def test_kein_token_ist_alias_und_mic_zugleich() -> None:
    """Der **heutige** Katalog trägt keine Doppeldeutigkeit — gemessen.

    Diese Zeile misst nur den Bestand; was passiert, *wenn* doch eine
    entsteht, prüft der Test darunter. Beides wird gebraucht: Der Bestand kann
    still driften, und ein Plugin darf den Katalog erweitern.
    """
    ambiguous = {
        definition.alias: mic
        for mic, definition in EXCHANGES.items()
        if definition.alias and definition.alias in EXCHANGES
    }

    assert ambiguous == {}, f"Token sind Alias und MIC zugleich: {ambiguous}"


def test_ein_doppeldeutiger_suffix_wird_abgelehnt_statt_entschieden(monkeypatch) -> None:
    """`#2f`: Der benannte Konflikt aus dem Entwurf, mit erweitertem Katalog.

    Ein Plugin trägt eine Börse `XFOO` ein, die ausgerechnet den Alias `XNAS`
    führt. Damit zeigt dasselbe Token auf zwei Handelsplätze: als MIC auf die
    NASDAQ, als Alias auf `XFOO`.

    Der frühere Entwurf sagte „der Alias gewinnt" — und hätte `AAPL.XNAS`
    still als `AAPL/XFOO` gedeutet. Es gibt hier aber keine richtige Wahl, nur
    zwei falsche; also wird abgelehnt und der Grund benannt.

    Der Alias ist **vierstellig**, und genau das ist der Punkt: Nicht die
    Länge entscheidet, sondern dass zwei Deutungen auf verschiedene Börsen
    zeigen.
    """
    four_letter_alias = replace(EXCHANGES["XETR"], alias="XNAS")
    monkeypatch.setitem(EXCHANGES, "XFOO", four_letter_alias)

    assert identity_from_input("AAPL.XNAS") is None
    assert input_failure("AAPL.XNAS") == REASON_AMBIGUOUS_SUFFIX
    # Der übrige Katalog bleibt unberührt — die Ablehnung gilt dem einen Token.
    assert identity_from_input("EUNL.DE") == ("EUNL", "XETR")


def test_ein_vierstelliger_alias_derselben_boerse_ist_kein_konflikt(monkeypatch) -> None:
    """Die Gegenprobe zur Gegenprobe: gleiche Börse, kein Widerspruch.

    Führte eine Börse ihren eigenen MIC zusätzlich als Alias, zeigten beide
    Deutungen auf **dieselbe** Notierung. Das ist redundant, aber nicht
    doppeldeutig — und darf deshalb nicht abgelehnt werden. Ohne diese Zeile
    wäre `suffix_is_ambiguous` auch mit einem simplen „vierstellig heißt
    Konflikt" grün.
    """
    monkeypatch.setitem(EXCHANGES, "XETR", replace(EXCHANGES["XETR"], alias="XETR"))

    assert identity_from_input("EUNL.XETR") == ("EUNL", "XETR")
    assert input_failure("EUNL.XETR") is None


def test_die_schema_schicht_zieht_kein_yfinance_mit() -> None:
    """`app/db.py` darf für den Umzug nicht den halben Netzstack laden.

    Die Zerlegung sitzt deshalb in `app/exchanges.py` und nicht im Resolver:
    Dort steht `import yfinance`, und die Schema-Schicht hat damit nichts zu
    tun.

    **Der Test misst jetzt die Wirklichkeit statt der Importzeilen.** Vorher
    parste er `app/db.py` und verlangte, dass `app.exchanges` dort *wörtlich*
    steht. Das war ein Stellvertreter, und er ging in dem Moment kaputt, in
    dem `db.py` denselben Code über `app.migration` bezieht — obwohl die
    eigentliche Zusage unberührt blieb. Schlimmer noch: Eine indirekte
    Abhängigkeit auf den Resolver hätte er **nicht** gesehen, denn er las nur
    eine einzige Datei.

    Geprüft wird deshalb der ganze Importbaum, in einem frischen Prozess:
    Nach `import app.db` darf `yfinance` nicht geladen sein.
    """
    import subprocess
    import sys

    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import app.db; "
            "print('yfinance' in sys.modules or 'app.resolver' in sys.modules)",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    assert completed.stdout.strip() == "False", (
        "app.db zieht den Netzstack mit: " + completed.stdout
    )


@pytest.mark.parametrize("mic", ["XETR", "XTSE", "XNAS", "XNYS", "X0AT"])
def test_echte_mics_werden_angenommen(mic: str) -> None:
    """Vier Großbuchstaben oder Ziffern — auch wenn die Tabelle sie nicht kennt.

    `XNAS` steht nicht in der eigenen Börsentabelle und ist trotzdem der Wert,
    den eine manuelle Zuordnung setzen soll. Die Tabelle ist eine Auswahl, kein
    Verzeichnis aller MICs.
    """
    assert is_real_mic(mic) is True


@pytest.mark.parametrize(
    ("mic", "reason"),
    [
        ("US", "Länderpräfix, kein ISO-MIC"),
        (None, "gar kein Wert"),
        ("", "leer"),
        ("NOT-A-MIC", "zu lang"),
        ("XNA", "zu kurz"),
        ("xnAs", "Kleinbuchstaben"),
        ("XN@S", "Sonderzeichen"),
        ("XNAS ", "Leerzeichen am Ende"),
        (" US", "Leerzeichen am Anfang"),
        ("XNAS\n", "Zeilenumbruch am Ende — `$` würde ihn durchlassen"),
        ("XNAS\t", "Tabulator am Ende"),
    ],
)
def test_ungueltige_mics_werden_abgelehnt(mic: str | None, reason: str) -> None:
    """Unbekannt heißt nicht gültig.

    Meine erste Fassung ließ jeden nichtleeren String durch, den die Tabelle
    nicht kannte — damit konnte im kanonischen Feld alles stehen, auch
    `NOT-A-MIC`. Ein MIC nach ISO 10383 hat genau vier Zeichen, Großbuchstaben
    oder Ziffern.

    Der Zeilenumbruch am Ende ist der tückischste Fall: In Python matcht `$`
    auch **vor** einem abschließenden `\n`. Der Ausdruck sah richtig aus und
    ließ `XNAS\n` durch — ein Wert, den der Eindeutigkeits-Index sogar von
    `XNAS` unterscheidet.
    """
    assert is_real_mic(mic) is False, reason


# ─── Die eine Weiche über die Union (T-31, Matrix #3) ─────────────────────────


@pytest.mark.parametrize(
    ("columns", "expected"),
    [
        ({"kind": "listed", "ticker": "EUNL", "mic": "XETR"}, "listed"),
        ({"kind": "pair", "base": "BTC", "quote_currency": "EUR"}, "pair"),
        ({"kind": "isin_only", "isin": "DE0001102531"}, "isin_only"),
        # Ohne `kind` ist die Form `listed` — so stehen die Zeilen da, die
        # vor T-31 angelegt wurden, und so kommen sie aus `ResolvedInstrument`.
        ({"ticker": "EUNL", "mic": "XETR"}, "listed"),
    ],
    ids=["listed", "pair", "isin_only", "kind_fehlt_heisst_listed"],
)
def test_jede_vollstaendige_form_wird_erkannt(columns: dict, expected: str) -> None:
    """Die drei Formen, jede in ihrer vollständigen Belegung.

    Diese Funktion ist die **einzige** Stelle, die entscheidet, welche Form
    vorliegt — REST-Modell, Core-Typ und Repository bauen ihren Typ daraus.
    Codex hat in Runde 4 drei auseinandergelaufene Fassungen davon gefunden;
    seither gibt es eine, und ohne diesen Test hätte ausgerechnet sie keinen
    eigenen.
    """
    assert identity_form(columns) == expected


@pytest.mark.parametrize(
    ("columns", "reason"),
    [
        ({"kind": "pair", "base": "BTC"}, "Paar ohne Quote-Währung"),
        ({"kind": "pair", "quote_currency": "EUR"}, "Paar ohne Basiswert"),
        ({"kind": "isin_only", "isin": "DE0001102532"}, "ISIN mit falscher Prüfziffer"),
        ({"kind": "isin_only", "isin": None}, "ISIN-only ohne ISIN"),
        ({"kind": "listed", "ticker": "EUNL"}, "Listing ohne MIC"),
        ({"kind": "listed", "mic": "XETR"}, "Listing ohne Ticker"),
        ({"kind": "listed", "ticker": "EUNL", "mic": "US"}, "Länderpräfix ist kein MIC"),
        ({"kind": "listed", "ticker": "BRK-B", "mic": "XNAS"}, "fremde Schreibweise"),
        ({"kind": "erfunden", "ticker": "EUNL", "mic": "XETR"}, "unbekannte Form"),
        ({}, "gar nichts"),
    ],
)
def test_eine_halbe_identitaet_bekommt_keine_form(columns: dict, reason: str) -> None:
    """``None`` heißt „noch keine Identität" — und nie „nimm die naheliegende".

    Der letzte Fall ist der wichtigste: Eine **unbekannte** `kind` fällt
    durch, statt auf `listed` zurückzufallen. Ein Rückfall wäre hier
    besonders teuer, weil er genau dann greift, wenn eine spätere Version
    eine vierte Form einführt — die alte Fassung deutete sie dann still zu
    einem Listing um.
    """
    assert identity_form(columns) is None, reason


def test_die_form_liest_auch_aus_einem_objekt() -> None:
    """Mapping, `sqlite3.Row` und Objekt — dieselbe Antwort.

    Die drei Verwender reichen dasselbe in drei Verpackungen herein. Liefe
    der Feldzugriff auseinander, fiele es zuerst dort auf, wo am wenigsten
    hingesehen wird: beim Objektweg aus dem Core.
    """
    from app.providers.base import ResolvedInstrument

    pair = ResolvedInstrument(
        symbol="BTC-EUR", kind="pair", base="BTC", quote_currency="EUR"
    )

    assert identity_form(pair) == "pair"
    assert identity_form({"kind": "pair", "base": "BTC", "quote_currency": "EUR"}) == (
        "pair"
    )
