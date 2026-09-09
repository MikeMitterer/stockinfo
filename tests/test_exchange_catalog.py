"""Konkrete MICs, App-Aliase und ihre Katalogdarstellung."""

import pytest
from pydantic import TypeAdapter, ValidationError

from app.exchanges import (
    EXCHANGES,
    is_real_mic,
    mic_for_alias,
    preference_kind,
    preferred_mics,
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
    assert is_real_mic("US") is False


def test_jeder_boerseneintrag_ist_ein_echter_mic() -> None:
    """Kein Eintrag der Tabelle darf durch die eigene MIC-Prüfung fallen."""
    rejected = [mic for mic in EXCHANGES if not is_real_mic(mic)]

    assert rejected == []


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("XETR", "exchange"),
        ("XSTU", "exchange"),
        ("XNAS", "exchange"),
        ("US", None),
        ("XXXX", None),
        ("", None),
    ],
)
def test_eine_praeferenz_ist_nur_ein_konkreter_handelsplatz(code: str, expected: str | None) -> None:
    """Nur ein geführter MIC ist eine bekannte Börsenpräferenz."""
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
    aliases = [
        definition.alias for definition in EXCHANGES.values() if definition.alias
    ]

    assert len(aliases) == len(set(aliases))


def test_jeder_eintrag_hat_waehrung_und_anzeigename() -> None:
    """Beides hängt an der Anzeige und an der Abweichungsprüfung."""
    incomplete = [
        code
        for code, definition in EXCHANGES.items()
        if not definition.name or not definition.currency
    ]

    assert incomplete == []


def test_der_alias_traegt_kein_punkt() -> None:
    """Die Punktkonvention steht an genau einer Stelle: in `provider_alias`.

    Vorher stand `".DE"` in der Tabelle, während der Lookup `DE` verglich.
    Beide Schichten hätten ohne eine weitere, nirgends beschriebene
    Normalisierung aneinander vorbeigesucht.
    """
    with_dot = [
        (mic, definition.alias)
        for mic, definition in EXCHANGES.items()
        if definition.alias and "." in definition.alias
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


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("XETR", ("XETR",)),
        ("XNAS", ("XNAS",)),
        ("US", ("XETR",)),
        ("XXXX", ("XETR",)),
    ],
    ids=["boerse_mit_alias", "boerse_ohne_alias", "alte_us_praeferenz", "unbekannt"],
)
def test_eine_praeferenz_umfasst_ihre_handelsplaetze(
    code: str, expected: tuple[str, ...]
) -> None:
    """Eine Präferenz bezeichnet genau einen MIC; unbekannt fällt auf Xetra zurück."""
    assert preferred_mics(code) == expected


@pytest.mark.parametrize(
    ("alias", "expected"),
    [
        ("DE", "XETR"),
        ("SG", "XSTU"),
        ("ZZ", None),
        ("", None),
    ],
    ids=["xetra", "stuttgart", "unbekannt", "leer"],
)
def test_der_alias_findet_seine_boerse_zurueck(alias: str, expected: str | None) -> None:
    """Die Umkehrung von `ExchangeDef.alias` — an genau einer Stelle.

    Der Leerstring gehört zu den Negativfällen: Eine Börse **ohne** Alias
    lässt sich nicht über ihn finden. Gäbe es hier einen Treffer, träfe
    `AAPL.` auf einen der fünf US-Plätze.

    Zwei Schichten stellen diese Frage — die Zerlegung eines gespeicherten
    Symbols und die Börsenauswahl im Resolver. Beantworteten sie sie getrennt,
    liefen sie beim ersten neuen Eintrag auseinander.
    """
    assert mic_for_alias(alias) == expected


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
