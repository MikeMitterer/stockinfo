"""Die Verträge gegen absichtlich kaputte Plugins — dauerhaft, nicht einmalig.

**Warum es diese Datei gibt.** In Runde 1 bestanden die Verträge Quellen, die
gar nichts lieferten: Ein `MetadataContract` war grün mit
`Reading(value="not-a-number", unit=ABSOLUTE, currency=None)`, ein
`DailyContract` mit einer stets leeren Reihe, und der FX-Identitätsfall mit
einer Antwort über ein völlig anderes Währungspaar. Alle Schleifen liefen null
Mal, alle Zusicherungen waren grün, und der Vertrag hatte nichts geprüft.

Ein Vertrag, dessen Greifen niemand nachweist, ist eine Zusage über eine Zusage.
Deshalb steht hier je Regel ein Plugin, das genau **einen** Fehler macht, und
die Erwartung, dass genau die zuständige Vertragszeile ihn findet.

Die Mutanten bleiben liegen. Ein einmal gelaufener Mutant beweist den Stand von
heute; ein festgehaltener beweist ihn auch nach dem nächsten Umbau — und dieses
Kit ist das Abnahmemittel für T-23, also für Code, den es noch nicht gibt.
"""

from datetime import date, datetime, timezone, tzinfo
from typing import Any

import pytest

from stockinfo_plugin import (
    DailyBar,
    DailyRequest,
    DailySeries,
    FieldSpec,
    FxRate,
    FxRequest,
    MetadataSource,
    Quote,
    QuoteRequest,
    Reading,
    Resolved,
    ResolveRequest,
    Unit,
)
from stockinfo_plugin.testing import (
    DailyContract,
    FakeDailySource,
    FakeFxSource,
    FakeQuoteSource,
    FakeResolver,
    FxContract,
    MetadataContract,
    QuoteContract,
    ResolverContract,
    SourceContract,
)

UTC_NOON = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)


def assert_contract_rejects(
    contract_class: type,
    method: str,
    source_factory,
    fragment: str,
    **attributes: Any,
) -> None:
    """Lässt **eine** Vertragszeile gegen ein kaputtes Plugin laufen.

    Args:
        contract_class: Die Vertragsklasse, etwa `QuoteContract`.
        method: Der Name der Zeile, die anschlagen soll.
        source_factory: Baut das kaputte Plugin.
        fragment: Ein Stück der erwarteten Meldung. **Nicht optional**: Ohne
            ihn wäre nur belegt, dass *irgendetwas* fehlschlägt — auch ein
            Tippfehler im Vertrag selbst. Geprüft wird, dass die Meldung von
            der gemeinten Regel kommt.
        **attributes: Die Prüfanfragen (`responsible` und so weiter).

    Raises:
        Failed: Die Vertragszeile hat den Fehler **nicht** gefunden. Das ist
            der eigentliche Befund dieser Datei.
    """
    case_class = type(
        "Mutant",  # nicht `Test…`: pytest würde die Klasse sonst einsammeln
        (contract_class,),
        {"make_source": lambda self: source_factory(), **attributes},
    )
    with pytest.raises(Exception) as caught:
        getattr(case_class(), method)()
    message = str(caught.value)
    assert fragment in message, (
        f"{contract_class.__name__}.{method} schlug an, aber mit einer anderen "
        f"Meldung als erwartet.\nErwartetes Stück: {fragment!r}\nBekommen: {message}"
    )


# ─── Gemeinsam für alle Rollen ────────────────────────────────────────────────


class _StummeQuelle(FakeResolver):
    """Steht still und sagt nicht, warum. Der Befund aus Runde 1, als Plugin."""

    name = "stumm"

    def is_configured(self) -> bool:
        return False


def test_wer_stillsteht_muss_es_begruenden() -> None:
    """`is_configured() = False` ohne Diagnose lässt den Betreiber ratlos zurück."""
    assert_contract_rejects(
        SourceContract,
        "test_wer_stillsteht_sagt_warum",
        _StummeQuelle,
        "begründet es mit",
    )


class _SchwaetzerischeQuelle(FakeResolver):
    """Arbeitet und beanstandet sich trotzdem — Rauschen in der Diagnose."""

    name = "schwaetzer"

    def configuration_problem(self) -> str:
        return "alles bestens, nur so zur Information"

    def is_configured(self) -> bool:
        return True


def test_wer_arbeitet_schweigt() -> None:
    """Die andere Hälfte, und sie ist nicht Zierde.

    Eine Diagnose, die auch im Normalfall spricht, wird nach dem dritten Mal
    überlesen. Dann fehlt sie genau in dem Augenblick, für den sie gebaut wurde.
    """
    assert_contract_rejects(
        SourceContract,
        "test_wer_stillsteht_sagt_warum",
        _SchwaetzerischeQuelle,
        "die Quelle arbeitet, meldet aber",
    )


# ─── Resolver ─────────────────────────────────────────────────────────────────

RESOLVER_REQUESTS = {
    "responsible": ResolveRequest(isin="CA78012H5675"),
    "not_responsible": ResolveRequest(isin="IE00B4L5Y983"),
    "unknown": ResolveRequest(isin="CA0679011084"),
}


def test_ein_sammelcode_gilt_nicht_als_boerse() -> None:
    """`US` fasst NYSE und NASDAQ zusammen und ist kein MIC.

    Ein Feld, das mal echte MICs und mal solche Codes enthält, wird beim ersten
    Anbieter zum Problem, der echte MICs erwartet — und dann ist der Bestand
    schon gemischt.
    """
    assert_contract_rejects(
        ResolverContract,
        "test_bekanntes_papier_wird_aufgeloest",
        lambda: FakeResolver(Resolved(ticker="RY", mic="US")),
        "ist kein MIC nach ISO 10383",
        **RESOLVER_REQUESTS,
    )


def test_eine_antwort_zu_einem_anderen_papier_faellt_auf() -> None:
    """Der unauffälligste teure Fehler: unscharf gesucht, ähnliches gefunden.

    Formal ist alles in Ordnung — Ticker da, MIC da, ISIN da. Nur gehört die
    Antwort zu einem anderen Wertpapier, und danach hängen Kurse und Kennzahlen
    am falschen Bestand.
    """
    assert_contract_rejects(
        ResolverContract,
        "test_die_antwort_gehoert_zur_frage",
        lambda: FakeResolver(
            Resolved(ticker="ABX", mic="XTSE", isin="CA0679011084")
        ),
        "das ist ein anderes Wertpapier",
        **RESOLVER_REQUESTS,
    )


def test_eine_ungueltige_pruef_isin_faellt_auf() -> None:
    """Zuerst die Prüfdaten, dann das Plugin — der Fund aus Runde 1 dieses Tickets."""
    assert_contract_rejects(
        ResolverContract,
        "test_die_eigenen_pruefdaten_sind_gueltige_isins",
        lambda: FakeResolver(Resolved(ticker="RY", mic="XTSE")),
        "ist keine gültige ISIN",
        **{**RESOLVER_REQUESTS, "unknown": ResolveRequest(isin="CA00000000000")},
    )


# ─── Metadaten ────────────────────────────────────────────────────────────────

METADATA_REQUESTS = {
    "responsible": ResolveRequest(isin="CA78012H5675"),
    "not_responsible": ResolveRequest(isin="IE00B4L5Y983"),
}


class _MetadataMutant(MetadataSource):
    """Eine Metadaten-Quelle, die je nach Bauart genau einen Fehler macht.

    `FIELDS` ist ein Tupel und kein Listenattribut — sonst schlüge zuerst
    `test_kein_veraenderlicher_zustand_an_der_klasse` an, und der Mutant
    bewiese etwas anderes als das Gemeinte.
    """

    name = "metadata-mutant"
    FIELDS = (
        FieldSpec(
            "ter",
            kind="number",
            unit=Unit.BASIS_POINTS,
            plausible=(0.5, 500.0),
            label_en="Total expense ratio",
        ),
        FieldSpec(
            "fund_size",
            kind="number",
            unit=Unit.ABSOLUTE,
            label_en="Fund size",
        ),
    )

    def __init__(self, answer: Any) -> None:
        super().__init__({})
        self._answer = answer

    def handles(self, request: ResolveRequest) -> bool:
        return bool(request.isin) and request.isin.upper().startswith("CA")

    def fetch(self, request: ResolveRequest) -> list[Reading] | None:
        if not self.handles(request):
            return []
        return self._answer


def test_eine_quelle_ohne_werte_prueft_nichts() -> None:
    """Die leere Liste für den **bekannten** Fall — jede Schleife lief null Mal."""
    assert_contract_rejects(
        MetadataContract,
        "test_der_bekannte_fall_liefert_ueberhaupt_werte",
        lambda: _MetadataMutant([]),
        "liefe als leere Schleife grün durch",
        **METADATA_REQUESTS,
    )


def test_none_fuer_den_bekannten_fall_prueft_erst_recht_nichts() -> None:
    """``None`` heißt „konnte nicht nachsehen" — für den selbst benannten Fall."""
    assert_contract_rejects(
        MetadataContract,
        "test_der_bekannte_fall_liefert_ueberhaupt_werte",
        lambda: _MetadataMutant(None),
        "konnte nicht nachsehen",
        **METADATA_REQUESTS,
    )


def test_eine_zeichenkette_in_einem_zahlenfeld_faellt_auf() -> None:
    """`kind="number"`, geliefert wird Text — genau der Fall aus dem Befund."""
    assert_contract_rejects(
        MetadataContract,
        "test_der_werttyp_passt_zur_deklarierten_bedienart",
        lambda: _MetadataMutant(
            [
                Reading(
                    field="ter",
                    value="not-a-number",
                    unit=Unit.BASIS_POINTS,
                    source="mutant",
                )
            ]
        ),
        "ist als number deklariert",
        **METADATA_REQUESTS,
    )


def test_ein_wert_ausserhalb_des_selbst_deklarierten_bereichs_faellt_auf() -> None:
    """Die stille Null: ``0.0`` als Kostenquote für einen Fonds, der Geld kostet."""
    assert_contract_rejects(
        MetadataContract,
        "test_werte_liegen_im_deklarierten_bereich",
        lambda: _MetadataMutant(
            [Reading(field="ter", value=0.0, unit=Unit.BASIS_POINTS, source="mutant")]
        ),
        "liegt außerhalb des selbst deklarierten Bereichs",
        **METADATA_REQUESTS,
    )


def test_ein_absoluter_betrag_ohne_waehrung_faellt_auf() -> None:
    """Ein Fondsvolumen ohne Währung ist eine Zahl. Der Befund, wörtlich."""
    assert_contract_rejects(
        MetadataContract,
        "test_ein_betrag_ohne_waehrung_ist_bedeutungslos",
        lambda: _MetadataMutant(
            [
                Reading(
                    field="fund_size",
                    value=2_289_978_572_800.0,
                    unit=Unit.ABSOLUTE,
                    currency=None,
                    source="mutant",
                )
            ]
        ),
        "absoluter Betrag ohne",
        **METADATA_REQUESTS,
    )


# ─── Kurs ─────────────────────────────────────────────────────────────────────

QUOTE_REQUESTS = {
    "responsible": QuoteRequest(ticker="RY", mic="XTSE"),
    "not_responsible": QuoteRequest(ticker="", mic=""),
    "unknown": QuoteRequest(ticker="ZZZZ", mic="XTSE"),
}


def test_eine_erfundene_waehrung_faellt_auf() -> None:
    """``ZZZ`` hat die Gestalt eines Codes und ist keiner — Befund aus Runde 1.

    So sieht das Feld aus, wenn ein Anbieter nichts hat und trotzdem etwas
    hinschreibt.
    """
    assert_contract_rejects(
        QuoteContract,
        "test_der_kurs_traegt_seine_waehrung",
        lambda: FakeQuoteSource(Quote(price=141.55, currency="ZZZ", as_of=UTC_NOON)),
        "kein vergebener ISO-4217-Code",
        **QUOTE_REQUESTS,
    )


def test_pence_als_waehrung_faellt_auf() -> None:
    """Der Faktor-100-Fehler, und er sieht völlig harmlos aus."""
    assert_contract_rejects(
        QuoteContract,
        "test_der_kurs_traegt_seine_waehrung",
        lambda: FakeQuoteSource(Quote(price=14155.0, currency="GBX", as_of=UTC_NOON)),
        "bezeichnet eine Untereinheit",
        **QUOTE_REQUESTS,
    )


def test_ein_kurs_von_null_faellt_auf() -> None:
    """``0`` ist kein Kurs, sondern eine fehlende Angabe, die sich als Zahl ausgibt."""
    assert_contract_rejects(
        QuoteContract,
        "test_der_preis_ist_eine_brauchbare_zahl",
        lambda: FakeQuoteSource(Quote(price=0.0, currency="CAD", as_of=UTC_NOON)),
        "ist kein brauchbarer Kurs",
        **QUOTE_REQUESTS,
    )


class _HalbherzigeZone(tzinfo):
    """Eine `tzinfo`, deren `utcoffset()` ``None`` liefert.

    Das ist erlaubt — und Python behandelt einen damit versehenen Zeitpunkt als
    **naiv**: Er lässt sich nicht mit einem echten aware-Zeitpunkt vergleichen
    und wirft dabei `TypeError`. Ein Vertrag, der nur `tzinfo is not None`
    prüft, lässt also gerade den Fall durch, der später abstürzt. Genau das war
    der Befund aus Runde 1.
    """

    def utcoffset(self, moment):  # noqa: D102 — Vertrag steht in `datetime.tzinfo`
        return None

    def dst(self, moment):  # noqa: D102
        return None

    def tzname(self, moment):  # noqa: D102
        return "halbherzig"


@pytest.mark.parametrize(
    ("label", "moment"),
    [
        ("ohne tzinfo", datetime(2026, 1, 2, 12, 0)),
        ("mit wirkungsloser tzinfo", datetime(2026, 1, 2, 12, 0, tzinfo=_HalbherzigeZone())),
    ],
)
def test_ein_zeitpunkt_ohne_wirksame_zone_faellt_auf(label: str, moment: datetime) -> None:
    """Beide Fälle, weil nur einer davon offensichtlich ist."""
    assert_contract_rejects(
        QuoteContract,
        "test_der_zeitpunkt_traegt_eine_zone",
        lambda: FakeQuoteSource(Quote(price=141.55, currency="CAD", as_of=moment)),
        "hat keine Zeitzone",
        **QUOTE_REQUESTS,
    )


# ─── Historie ─────────────────────────────────────────────────────────────────

DAILY_REQUESTS = {
    "responsible": DailyRequest(ticker="RY", mic="XTSE", start=date(2025, 12, 30)),
    "not_responsible": DailyRequest(ticker="", mic=""),
    "unknown": DailyRequest(ticker="ZZZZ", mic="XTSE"),
}


def test_eine_leere_reihe_prueft_nichts() -> None:
    """Der Befund, wörtlich: Sortierung, Kurse und Zeitraum liefen leer durch."""
    assert_contract_rejects(
        DailyContract,
        "test_die_reihe_hat_ueberhaupt_tage",
        lambda: FakeDailySource(
            DailySeries(bars=(), currency="CAD", adjusted=False)
        ),
        "ist leer",
        **DAILY_REQUESTS,
    )


def test_ein_doppelter_handelstag_faellt_auf() -> None:
    """Zwei überlappende Seiten eines Anbieters — und der Tag zählt doppelt."""
    same_day = date(2025, 12, 30)
    assert_contract_rejects(
        DailyContract,
        "test_die_reihe_ist_sortiert_und_doppelfrei",
        lambda: FakeDailySource(
            DailySeries(
                bars=(
                    DailyBar(day=same_day, close=140.10),
                    DailyBar(day=same_day, close=140.10),
                ),
                currency="CAD",
                adjusted=False,
            )
        ),
        "nicht streng aufsteigend",
        **DAILY_REQUESTS,
    )


def test_ein_tag_ausserhalb_des_zeitraums_faellt_auf() -> None:
    """Großzügig gelieferte Ränder überlappen sich beim nächsten Abruf."""
    assert_contract_rejects(
        DailyContract,
        "test_der_angefragte_zeitraum_wird_eingehalten",
        lambda: FakeDailySource(
            DailySeries(
                bars=(DailyBar(day=date(2025, 12, 1), close=138.0),),
                currency="CAD",
                adjusted=False,
            )
        ),
        "liegt vor dem angefragten Beginn",
        **DAILY_REQUESTS,
    )


def test_ein_erschlossener_bereinigungsstand_faellt_auf() -> None:
    """``adjusted`` steht nicht im Zahlenmaterial — es muss deklariert werden."""
    assert_contract_rejects(
        DailyContract,
        "test_waehrung_und_bereinigungsstand_sind_deklariert",
        lambda: FakeDailySource(
            DailySeries(
                bars=(DailyBar(day=date(2025, 12, 31), close=141.55),),
                currency="CAD",
                adjusted="vielleicht",  # type: ignore[arg-type]
            )
        ),
        "statt bool",
        **DAILY_REQUESTS,
    )


# ─── Devisen ──────────────────────────────────────────────────────────────────

FX_REQUESTS = {
    "responsible": FxRequest(base="CAD", quote="EUR"),
    "not_responsible": FxRequest(base="CA", quote="EU"),
}


def test_der_identitaetsfall_mit_falschem_paar_faellt_auf() -> None:
    """**Der Befund aus Runde 1, wörtlich nachgestellt.**

    Vorher prüfte der Identitätsfall nur die Rate — und bestand deshalb mit
    ``FxRate(base="USD", quote="JPY", rate=1.0)`` auf eine CAD→CAD-Anfrage.
    Eine ``1.0`` ohne ihr Paar ist keine Aussage: für dieses Paar immer richtig,
    für fast jedes andere grob falsch.
    """
    assert_contract_rejects(
        FxContract,
        "test_eine_waehrung_in_sich_selbst_ist_genau_eins",
        lambda: FakeFxSource(
            FxRate(base="USD", quote="JPY", rate=1.0, as_of=UTC_NOON)
        ),
        "die Rate 1.0 gilt dann für ein anderes Paar",
        **FX_REQUESTS,
    )


def test_eine_identitaet_ueber_einen_umweg_faellt_auf() -> None:
    """``0.9998`` für EUR→EUR heißt: Die Quelle rechnet über den Dollar.

    Derselbe Umweg verfälscht dann jedes andere Paar auch, nur unsichtbar — bei
    EUR→USD fällt eine Abweichung im Promillebereich niemandem auf.
    """
    assert_contract_rejects(
        FxContract,
        "test_eine_waehrung_in_sich_selbst_ist_genau_eins",
        lambda: FakeFxSource(
            FxRate(base="CAD", quote="CAD", rate=0.9998, as_of=UTC_NOON)
        ),
        "die Quelle rechnet über einen Umweg",
        **FX_REQUESTS,
    )


def test_ein_vertauschtes_paar_faellt_auf() -> None:
    """``0.92`` und ``1.087`` sehen beide plausibel aus — eines ist EUR→USD."""
    assert_contract_rejects(
        FxContract,
        "test_der_kurs_nennt_sein_paar",
        lambda: FakeFxSource(
            FxRate(base="EUR", quote="CAD", rate=1.56, as_of=UTC_NOON)
        ),
        "gefragt nach CAD→EUR",
        **FX_REQUESTS,
    )


# ─── Und die Gegenprobe zur Gegenprobe ────────────────────────────────────────


def test_ein_heiles_plugin_wird_nicht_beanstandet() -> None:
    """Ohne diese Zeile bewiese die ganze Datei nur, dass die Verträge streng sind.

    Ein Vertrag, der **alles** ablehnt, besteht jeden Mutantentest hier und ist
    trotzdem wertlos. Deshalb dieselbe Anordnung ein letztes Mal mit einer
    Quelle, die nichts falsch macht — und `pytest.raises` schlägt fehl, wenn
    doch etwas anschlägt.
    """
    intact = type(
        "Mutant",
        (FxContract,),
        {
            "make_source": lambda self: FakeFxSource(
                keyed={
                    FxRequest(base="CAD", quote="EUR"): FxRate(
                        base="CAD", quote="EUR", rate=0.6412, as_of=UTC_NOON
                    ),
                    FxRequest(base="CAD", quote="CAD"): FxRate(
                        base="CAD", quote="CAD", rate=1.0, as_of=UTC_NOON
                    ),
                },
                responsible=True,
            ),
            **FX_REQUESTS,
        },
    )()

    intact.test_eine_waehrung_in_sich_selbst_ist_genau_eins()
    intact.test_der_kurs_nennt_sein_paar()
    intact.test_die_rate_ist_eine_brauchbare_zahl()
