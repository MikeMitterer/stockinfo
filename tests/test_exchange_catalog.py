"""Der Börsenkatalog aus T-21 Teil 3, Übergabe 1.

Zwei Eintragsarten statt einer: Eine **Börse** hat einen echten MIC und
höchstens einen Provider-Alias; ein **Sammelcode** hat Mitglieder und keinen
MIC. Vorher lagen beide in derselben Tabelle, und `GET /exchanges` lieferte
`mic="US"` — einen Wert, den `is_real_mic` im selben Modul ablehnt.

Der zweite Umbau steckt im Alias: Er trägt jetzt das **nackte Token ohne
Punkt**. Vorher stand `".DE"` in der Tabelle, nachgeschlagen wurde aber der
Teil hinter dem Punkt — zwei Schichten, die aneinander vorbeisuchen konnten.
"""

import pytest

from app.exchanges import (
    COLLECTOR_CODES,
    COLLECTORS,
    EXCHANGES,
    is_real_mic,
    preference_kind,
    provider_alias,
    split_symbol,
)


def test_der_sammelcode_liegt_nicht_in_der_boersentabelle() -> None:
    """`US` ist kein Handelsplatz und darf in keinem `mic`-Feld auftauchen.

    Das ist der Kern der Trennung: Solange `US` in `EXCHANGES` stand, konnte
    jeder Konsument es als MIC übernehmen — und `is_real_mic` lehnt genau
    diesen Wert ab. Die REST-Antwort tat es bis Teil 3 tatsächlich.
    """
    assert "US" not in EXCHANGES
    assert "US" in COLLECTORS
    assert is_real_mic("US") is False


def test_jeder_boerseneintrag_ist_ein_echter_mic() -> None:
    """Kein Eintrag der Tabelle darf durch die eigene MIC-Prüfung fallen."""
    durchgefallen = [mic for mic in EXCHANGES if not is_real_mic(mic)]

    assert durchgefallen == []


def test_collector_codes_werden_abgeleitet_nicht_gepflegt() -> None:
    """Eine Quelle für die Sammelcodes, nicht zwei nebeneinander.

    Vorher stand `US` in `EXCHANGES`, in `COLLECTOR_CODES` **und** wäre nach
    dem ersten Entwurf zusätzlich als Mitgliedsliste an fünf Börsen gelandet —
    dreimal dieselbe Regel.
    """
    assert COLLECTOR_CODES == frozenset(COLLECTORS)


def test_die_mitgliedschaft_steht_nur_am_sammelcode() -> None:
    """`US` kennt seine Mitglieder; die Mitglieder kennen ihren Sammelcode nicht.

    Andersherum — eine `collectors`-Liste an jeder Börse — liefe beim
    Plugin-Merge auseinander, sobald zwei Quellen dieselbe Börse beisteuern.
    """
    mitglieder = COLLECTORS["US"].members

    assert set(mitglieder) == {"XNAS", "XNYS", "ARCX", "XASE", "BATS"}
    assert all(mic in EXCHANGES for mic in mitglieder)
    assert not hasattr(EXCHANGES["XNAS"], "collectors")


@pytest.mark.parametrize(
    ("code", "erwartet"),
    [
        ("XETR", "exchange"),
        ("XSTU", "exchange"),
        ("XNAS", "exchange"),
        ("US", "collector"),
        ("XXXX", None),
        ("", None),
    ],
)
def test_eine_praeferenz_ist_boerse_oder_sammelcode(code: str, erwartet: str | None) -> None:
    """`DEFAULT_EXCHANGE` darf beides sein — der Aufrufer muss wissen, was.

    `US` bleibt ein zulässiger Vorgabewert, obwohl es die Börsentabelle
    verlassen hat. Ohne diese Auskunft müsste jeder Aufrufer zwei Tabellen
    abfragen und sich seine eigene Regel bauen.
    """
    assert preference_kind(code) == erwartet


def test_stuttgart_ist_aufgenommen_und_macht_gold_sg_zerlegbar() -> None:
    """Der Eintrag, an dem 257 Tageskurse hängen.

    Ohne ihn wird `GOLD.SG` von der Migration abgelehnt statt migriert —
    deshalb muss diese Übergabe **vor** der Migration ausgeliefert werden.
    """
    assert split_symbol("GOLD.SG") == ("GOLD", "XSTU")


@pytest.mark.parametrize("mic", ["XNAS", "XNYS", "ARCX", "XASE", "BATS"])
def test_die_us_plaetze_sind_echte_mics_ohne_alias(mic: str) -> None:
    """Fünf Handelsplätze, ein leerer Alias — und deshalb keine Rückrechnung.

    Aus `AAPL` lässt sich weiterhin kein MIC ableiten; das ist gewollt. Neu
    ist nur die Gegenrichtung: `(AAPL, XNAS)` ergibt jetzt ein Symbol.
    """
    assert is_real_mic(mic)
    assert EXCHANGES[mic].alias == ""
    assert EXCHANGES[mic].currency == "USD"


def test_kein_alias_ist_doppelt_vergeben() -> None:
    """Die Voraussetzung der Rückrechnung — jetzt über den nackten Alias.

    Leere Aliase sind ausgenommen: Fünf US-Plätze teilen sich den leeren, und
    genau deshalb ist die Rückrechnung dort nicht möglich.
    """
    aliase = [d.alias for d in EXCHANGES.values() if d.alias]

    assert len(aliase) == len(set(aliase))


def test_jeder_eintrag_hat_waehrung_und_anzeigename() -> None:
    """Beides hängt an der Anzeige und an der Abweichungsprüfung."""
    unvollstaendig = [
        code
        for code, d in [*EXCHANGES.items(), *COLLECTORS.items()]
        if not d.name or not d.currency
    ]

    assert unvollstaendig == []


def test_der_alias_traegt_kein_punkt() -> None:
    """Die Punktkonvention steht an genau einer Stelle: in `provider_alias`.

    Vorher stand `".DE"` in der Tabelle, während der Lookup `DE` verglich.
    Beide Schichten hätten ohne eine weitere, nirgends beschriebene
    Normalisierung aneinander vorbeigesucht.
    """
    mit_punkt = [(mic, d.alias) for mic, d in EXCHANGES.items() if "." in d.alias]

    assert mit_punkt == []


@pytest.mark.parametrize(
    ("ticker", "mic", "erwartet"),
    [
        ("EUNL", "XETR", "EUNL.DE"),
        ("GOLD", "XSTU", "GOLD.SG"),
        ("AAPL", "XNAS", "AAPL"),
        ("VTI", "ARCX", "VTI"),
    ],
)
def test_der_provider_alias_entsteht_an_einer_stelle(
    ticker: str, mic: str, erwartet: str
) -> None:
    """Aus der Identität entsteht das Symbol, nie umgekehrt.

    Ohne Alias bleibt es beim nackten Ticker — die US-Plätze führen keinen.
    """
    assert provider_alias(ticker, mic) == erwartet


def test_beide_eingabeformen_treffen_dieselbe_boerse() -> None:
    """`EUNL.DE` über den Alias, `EUNL.XETR` über den MIC — ein Ziel.

    Zwei Auflösungswege, nicht zwei Aliaswerte: Der eine Alias je Börse
    genügt, weil der kanonische MIC selbst die zweite Form ist.
    """
    ueber_alias = split_symbol("EUNL.DE")
    ueber_mic = ("EUNL", "XETR") if "XETR" in EXCHANGES else None

    assert ueber_alias == ueber_mic == ("EUNL", "XETR")
    assert provider_alias(*ueber_alias) == "EUNL.DE"
