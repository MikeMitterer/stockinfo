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
from pydantic import TypeAdapter, ValidationError

from app.exchanges import (
    COLLECTOR_CODES,
    COLLECTORS,
    EXCHANGES,
    is_real_mic,
    preference_kind,
    provider_alias,
    split_symbol,
)
from app.models import ExchangeEntry, Provenance


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
    rejected = [mic for mic in EXCHANGES if not is_real_mic(mic)]

    assert rejected == []


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
    members = COLLECTORS["US"].members

    assert set(members) == {"XNAS", "XNYS", "ARCX", "XASE", "BATS"}
    assert all(mic in EXCHANGES for mic in members)
    assert not hasattr(EXCHANGES["XNAS"], "collectors")


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("XETR", "exchange"),
        ("XSTU", "exchange"),
        ("XNAS", "exchange"),
        ("US", "collector"),
        ("XXXX", None),
        ("", None),
    ],
)
def test_eine_praeferenz_ist_boerse_oder_sammelcode(code: str, expected: str | None) -> None:
    """`DEFAULT_EXCHANGE` darf beides sein — der Aufrufer muss wissen, was.

    `US` bleibt ein zulässiger Vorgabewert, obwohl es die Börsentabelle
    verlassen hat. Ohne diese Auskunft müsste jeder Aufrufer zwei Tabellen
    abfragen und sich seine eigene Regel bauen.
    """
    assert preference_kind(code) == expected


def test_stuttgart_ist_aufgenommen_und_macht_gold_sg_zerlegbar() -> None:
    """Der Eintrag, an dem 257 Tageskurse hängen.

    Ohne ihn wird `GOLD.SG` von der Migration abgelehnt statt migriert —
    deshalb muss diese Übergabe **vor** der Migration ausgeliefert werden.
    """
    assert split_symbol("GOLD.SG") == ("GOLD", "XSTU")


@pytest.mark.parametrize("mic", ["XNAS", "XNYS", "ARCX", "XASE", "BATS"])
def test_die_us_plaetze_sind_echte_mics_ohne_alias(mic: str) -> None:
    """Fünf Handelsplätze **ohne** Alias — und deshalb keine Rückrechnung.

    Abwesenheit steht als `None` da, nicht als Leerstring: Ein Alias aus null
    Zeichen wäre ein magischer Wert, den jede Schicht eigens deuten müsste.

    Aus `AAPL` lässt sich weiterhin kein MIC ableiten; das ist gewollt. Neu
    ist nur die Gegenrichtung: `(AAPL, XNAS)` ergibt jetzt ein Symbol.
    """
    assert is_real_mic(mic)
    assert EXCHANGES[mic].alias is None
    assert EXCHANGES[mic].currency == "USD"


def test_kein_alias_ist_doppelt_vergeben() -> None:
    """Die Voraussetzung der Rückrechnung — jetzt über den nackten Alias.

    Börsen ohne Alias sind ausgenommen: Fünf US-Plätze führen keinen, und
    genau deshalb ist die Rückrechnung dort nicht möglich.
    """
    aliases = [d.alias for d in EXCHANGES.values() if d.alias]

    assert len(aliases) == len(set(aliases))


def test_jeder_eintrag_hat_waehrung_und_anzeigename() -> None:
    """Beides hängt an der Anzeige und an der Abweichungsprüfung."""
    incomplete = [
        code
        for code, d in [*EXCHANGES.items(), *COLLECTORS.items()]
        if not d.name or not d.currency
    ]

    assert incomplete == []


def test_der_alias_traegt_kein_punkt() -> None:
    """Die Punktkonvention steht an genau einer Stelle: in `provider_alias`.

    Vorher stand `".DE"` in der Tabelle, während der Lookup `DE` verglich.
    Beide Schichten hätten ohne eine weitere, nirgends beschriebene
    Normalisierung aneinander vorbeigesucht.
    """
    with_dot = [
        (mic, d.alias) for mic, d in EXCHANGES.items() if d.alias and "." in d.alias
    ]

    assert with_dot == []


@pytest.mark.parametrize(
    ("ticker", "mic", "expected"),
    [
        ("EUNL", "XETR", "EUNL.DE"),
        ("GOLD", "XSTU", "GOLD.SG"),
        ("AAPL", "XNAS", "AAPL"),
        ("VTI", "ARCX", "VTI"),
    ],
)
def test_der_provider_alias_entsteht_an_einer_stelle(
    ticker: str, mic: str, expected: str
) -> None:
    """Aus der Identität entsteht das Symbol, nie umgekehrt.

    Ohne Alias bleibt es beim nackten Ticker — die US-Plätze führen keinen.
    """
    assert provider_alias(ticker, mic) == expected


def test_der_alias_weg_landet_beim_kanonischen_mic() -> None:
    """Der Aliasweg endet bei einem MIC, den die Tabelle als Börse führt.

    **Was dieser Test nicht zeigt.** Die zweite Eingabeform `EUNL.XETR` läuft
    noch durch keinen Parser — der Aufnahmeweg kommt erst mit Übergabe 3. Bis
    dahin wäre eine Gleichheit „beide Formen treffen dieselbe Börse" nur eine
    von Hand konstruierte Behauptung. Geprüft wird deshalb genau das, was es
    heute gibt: die Katalogzuordnung des Aliaswegs.
    """
    assert split_symbol("EUNL.DE") == ("EUNL", "XETR")
    assert preference_kind("XETR") == "exchange"


# --- Der Antworttyp: was er ausdrücken kann und was nicht -------------------
#
# Die folgenden Prüfungen gelten dem **Modell**, nicht der Tabelle. Sie sind
# der Grund, warum T-30 seinen Plugin-Eintrag später anfügen kann, ohne die
# Bedeutung bestehender Felder nachzuverhandeln: Ein Typ, der ungültige
# Zustände ausdrücken kann, wird genau dort zur Auslegungssache.

_PROVENANCE = TypeAdapter(Provenance)


@pytest.mark.parametrize(
    "payload",
    [
        {"kind": "exchange", "mic": "XNAS", "name": "NASDAQ", "region": "usa", "currency": "USD"},
        {"kind": "exchange", "mic": "XNAS", "alias": None, "name": "NASDAQ", "region": "usa", "currency": "USD"},
    ],
    ids=["alias_weggelassen", "alias_null"],
)
def test_ein_fehlender_alias_ist_gueltig(payload: dict) -> None:
    """Abwesenheit ist eine zulässige Angabe — weggelassen wie ausdrücklich.

    Vor dieser Korrektur war `alias` Pflicht, und die fünf US-Plätze trugen
    einen Leerstring. Ein Konsument musste wissen, dass „null Zeichen" hier
    „kein Alias" heißt — eine Übereinkunft, die im Vertrag nirgends stand.
    """
    assert ExchangeEntry(**payload).alias is None


def test_ein_leerer_alias_ist_kein_zulaessiger_wert() -> None:
    """Der Leerstring darf nicht als zweite Schreibweise für „keiner" leben.

    Sonst gäbe es die Abwesenheit zweimal, und jede Vergleichsstelle müsste
    beide Formen kennen.
    """
    with pytest.raises(ValidationError):
        ExchangeEntry(
            kind="exchange", mic="XNAS", alias="", name="NASDAQ", region="usa", currency="USD"
        )


def test_die_us_plaetze_serialisieren_ihre_abwesenheit_als_null() -> None:
    """Die Gegenprobe am ausgelieferten JSON, nicht nur am Python-Objekt."""
    entry = ExchangeEntry(
        mic="XNAS", alias=EXCHANGES["XNAS"].alias, name="NASDAQ", region="usa", currency="USD"
    )

    assert entry.model_dump(mode="json")["alias"] is None


def test_die_herkunft_ist_core_ohne_id_oder_plugin_mit_id() -> None:
    """Die beiden **gültigen** Kombinationen — der Positivfall der Union."""
    core = _PROVENANCE.validate_python({"kind": "core"})
    plugin = _PROVENANCE.validate_python({"kind": "plugin", "id": "at-boersen"})

    assert core.model_dump() == {"kind": "core"}
    assert plugin.model_dump() == {"kind": "plugin", "id": "at-boersen"}


@pytest.mark.parametrize(
    "payload",
    [
        {"kind": "plugin"},
        {"kind": "plugin", "id": None},
        {"kind": "plugin", "id": ""},
        {"kind": "core", "id": "demo"},
    ],
    ids=["plugin_ohne_id", "plugin_id_null", "plugin_id_leer", "core_mit_id"],
)
def test_die_herkunft_lehnt_die_ungueltigen_kombinationen_ab(payload: dict) -> None:
    """„Irgendein Plugin" und „Core von Plugin X" sind keine Herkunft.

    T-30 entscheidet an genau dieser Angabe über Vorrang, Kollision und
    Invalidierung. Ein Typ, der beide Unsinnszustände zulässt, verschiebt
    diese Entscheidung in eine Prüfung, die jeder Konsument selbst schreiben
    müsste.
    """
    with pytest.raises(ValidationError):
        _PROVENANCE.validate_python(payload)
