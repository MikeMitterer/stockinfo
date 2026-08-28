"""Die fachlichen Prüfungen, auf denen alle fünf Verträge stehen.

Sie werden hier **gegen bekannte Werte** geprüft, nicht gegen sich selbst. Der
Erwartungswert einer Prüfziffernrechnung darf nicht aus derselben Rechnung
kommen — sonst bestätigt die Funktion sich selbst, und das ist genau das
Muster, an dem in diesem Projekt schon zwei Prüfungen gescheitert sind.

Die ISINs unten sind deshalb echte, öffentlich nachschlagbare Kennzeichen:
Apple, iShares Core MSCI World, Royal Bank of Canada, Barrick Gold.
"""

from datetime import date, datetime, timezone, tzinfo

import pytest

from stockinfo_plugin.invariants import (
    ISO_4217,
    ISO_4217_AS_OF,
    MINOR_UNIT_CODES,
    currency_is_valid,
    currency_is_wellformed,
    currency_problem,
    days_are_ordered,
    has_timezone,
    is_finite_number,
    is_finite_price,
    is_real_mic,
    isin_check_digit_is_valid,
    isin_is_wellformed,
    mic_is_wellformed,
)

VALID_ISINS = ["US0378331005", "IE00B4L5Y983", "CA78012H5675", "CA0679011084"]


@pytest.mark.parametrize("isin", VALID_ISINS)
def test_echte_isins_bestehen_die_pruefziffer(isin: str) -> None:
    """Vier echte Kennzeichen aus vier Ländern — der Erwartungswert ist die Welt."""
    assert isin_check_digit_is_valid(isin)


@pytest.mark.parametrize("isin", VALID_ISINS)
def test_eine_vertauschte_ziffer_faellt_auf(isin: str) -> None:
    """Wofür die Prüfziffer da ist: der Zahlendreher.

    Er ist der häufigste Tippfehler beim Abschreiben, und ohne diese Prüfung
    wandert er unbemerkt in eine von Hand gepflegte Tabelle. Später findet dort
    keine Quelle etwas — und es sieht aus wie ein Ausfall der Quelle.

    Der Test dreht die beiden letzten Zeichen **vor** der Prüfziffer. Sind sie
    zufällig gleich, ändert das nichts; dann wird der Fall übersprungen, statt
    eine Aussage zu behaupten, die der Wert nicht hergibt.
    """
    if isin[9] == isin[10]:
        pytest.skip(f"{isin}: die getauschten Stellen sind gleich")
    swapped = isin[:9] + isin[10] + isin[9] + isin[11]

    assert isin_is_wellformed(swapped), "der Zahlendreher bleibt formal eine ISIN"
    assert not isin_check_digit_is_valid(swapped), (
        f"{swapped} müsste an der Prüfziffer scheitern"
    )


@pytest.mark.parametrize(
    "broken",
    [
        None,
        "",
        "CA00000000000",  # dreizehn Zeichen — die Falle aus der alten Beispielsuite
        "US037833100",  # eine Stelle zu kurz
        "us0378331005",  # klein geschrieben
        "US037833100X",  # Prüfziffer ist keine Ziffer
        "US0378331005\n",  # `$` würde das durchlassen, `fullmatch` nicht
    ],
)
def test_was_keine_isin_ist_wird_nicht_geprueft(broken: str | None) -> None:
    """Ungültige Gestalt ist nie gültig — auch nicht „aus Versehen".

    `isin_check_digit_is_valid` prüft die Gestalt selbst mit. Ohne das müsste
    jeder Aufrufer beides einzeln fragen, und einer vergäße es.
    """
    assert not isin_is_wellformed(broken)
    assert not isin_check_digit_is_valid(broken)


@pytest.mark.parametrize("mic", ["XETR", "XTSE", "XNAS", "ARCX", "360T"])
def test_echte_mics_gelten(mic: str) -> None:
    """Auch der Tabelle unbekannte gelten — geprüft wird die Schreibweise.

    `XNAS` steht in keiner Liste dieses Pakets und ist genau der Wert, den eine
    manuelle Zuordnung setzen soll. Ein Verzeichnis aller MICs führt hier
    niemand, und „unbekannt" wäre kein Befund, sondern eine Lücke.
    """
    assert mic_is_wellformed(mic)
    assert is_real_mic(mic)


@pytest.mark.parametrize("broken", [None, "", "US", "XETRA", "xetr", "XET R", "XETR\n"])
def test_was_kein_mic_ist_faellt_durch(broken: str | None) -> None:
    """`US` ist der Sammelcode dieser App — zwei Zeichen, also nie ein MIC."""
    assert not is_real_mic(broken)


def test_ein_vierstelliger_sammelcode_braucht_die_liste() -> None:
    """Die Längenregel allein reicht nicht — und deshalb bleibt die Menge.

    Heute fängt sie jeden Sammelcode ab, weil `US` zwei Zeichen hat. Käme ein
    vierstelliger dazu, sähe er aus wie ein MIC. Ohne diesen Test würde die
    Menge beim nächsten Aufräumen als „wirkungslos" entfernt.
    """
    assert is_real_mic("USXX") is True
    assert is_real_mic("USXX", frozenset({"USXX"})) is False


@pytest.mark.parametrize("code", ["EUR", "USD", "CAD", "CHF", "JPY"])
def test_echte_waehrungen_gelten(code: str) -> None:
    assert currency_is_valid(code)


@pytest.mark.parametrize("code", [None, "", "eur", "EURO", "EU", "E1R"])
def test_was_keine_waehrung_ist_faellt_durch(code: str | None) -> None:
    assert not currency_is_valid(code)


@pytest.mark.parametrize("code", ["ZZZ", "ABC", "QQQ"])
def test_ein_erfundener_code_faellt_durch(code: str) -> None:
    """**Befund aus Runde 1: `currency_is_valid("ZZZ")` war `True`.**

    Die Funktion prüfte die Form und hieß „valid". ``ZZZ`` ist aber genau, wie
    das Feld aussieht, wenn ein Anbieter nichts hat und trotzdem etwas
    hinschreibt — drei Großbuchstaben, tadellose Gestalt, keine Währung.

    Die Form allein ist weiterhin abfragbar, nur heißt sie jetzt so.
    """
    assert currency_is_wellformed(code), "die Gestalt stimmt — darum ging es nie"
    assert not currency_is_valid(code)
    assert "kein vergebener ISO-4217-Code" in currency_problem(code)


@pytest.mark.parametrize("code", ["XXX", "XTS"])
def test_die_platzhalter_der_norm_sind_keine_waehrungen(code: str) -> None:
    """``XXX`` heißt wörtlich „keine Währung", ``XTS`` ist für Tests reserviert.

    Beide stehen **in** ISO 4217 — und sind genau der Platzhalter, den ein
    Anbieter einsetzt, wenn er nichts weiß. Sie durchzulassen hieße, den Zweck
    der Prüfung an ihrer formal korrektesten Stelle aufzugeben.
    """
    assert not currency_is_valid(code)
    assert "keine Währung" in currency_problem(code)


@pytest.mark.parametrize(
    ("code", "withdrawn"),
    [("BGN", "2026-01-01, Euro-Einführung in Bulgarien"), ("ANG", "2025-06-30, abgelöst durch XCG")],
)
def test_zurueckgezogene_codes_gelten_nicht(code: str, withdrawn: str) -> None:
    """**Befund aus Runde 2 — und der zweite Code stand nicht im Review.**

    Ein zurückgezogener Code ist der heimtückischere Fall: Er war einmal
    richtig, steht in alten Aufzeichnungen und sieht in keiner Meldung falsch
    aus. Ein Anbieter, der nach der Umstellung weiter in `BGN` liefert, meldet
    keinen Fehler — er meldet einen Kurs in einer Währung, die es nicht mehr
    gibt.

    Gefunden wurde `ANG` erst beim vollständigen Abgleich gegen die List One.
    Deshalb steht dieser Test parametrisiert da und nicht als Einzelfall: Der
    nächste zurückgezogene Code bekommt hier seine Zeile.
    """
    assert currency_is_wellformed(code), "die Gestalt bleibt tadellos — darum geht es"
    assert not currency_is_valid(code), f"{code} ist zurückgezogen ({withdrawn})"


def test_ein_vergebener_code_wird_nicht_abgewiesen() -> None:
    """Die Gegenprobe: Der schlimmere Fehler ist die zu kurze Liste.

    ``XAD`` — Arab Accounting Dinar — fehlte, obwohl es vergeben ist. Ohne
    diese Richtung prüfte die Liste nur, dass sie streng ist; eine leere Liste
    wäre am strengsten und wertlos.
    """
    assert currency_is_valid("XAD")


def test_der_gemeldete_stand_und_die_liste_gehoeren_zusammen() -> None:
    """Der Stolperdraht gegen genau den Fehler aus Runde 2.

    Dort behauptete `ISO_4217_AS_OF` einen Stand, den die Liste nicht hatte —
    und nichts schlug an, weil beide Angaben unabhängig voneinander gepflegt
    wurden. Dieser Test verknüpft sie: Wer die Liste ändert, muss die Anzahl
    hier nachziehen, und wer die Anzahl nachzieht, hat den Abgleich gegen die
    List One gemacht — anders kommt er nicht an die Zahl.

    Ein Netzabruf gehört **nicht** hierher. Ein Test, der von der Erreichbarkeit
    von six-group.com abhängt, ist rot, wenn jemand im Zug sitzt, und das hat
    mit der Sache nichts zu tun. Der Abgleich ist Handarbeit bei der Pflege;
    dieser Test erzwingt nur, dass sie stattgefunden hat.
    """
    assert ISO_4217_AS_OF == "2026-01-01"
    assert len(ISO_4217) == 176, (
        "Liste und gemeldeter Stand sind auseinandergelaufen — gegen die "
        "offizielle List One abgleichen (siehe Docstring von ISO_4217), dann "
        "Anzahl und ISO_4217_AS_OF gemeinsam setzen"
    )


def test_die_meldung_nennt_den_stand_der_liste() -> None:
    """Sonst weiß der Autor nicht, ob sein Code neu ist oder falsch.

    Die Liste veraltet — langsam, aber sie tut es. Wird ein Code neu vergeben,
    weist die Prüfung ihn ab; dann muss die Meldung sagen, gegen welchen Stand
    geprüft wurde, sonst sucht der Autor den Fehler bei sich.
    """
    assert ISO_4217_AS_OF in currency_problem("ZZZ")


def test_die_drei_beanstandungen_sind_unterscheidbar() -> None:
    """Der Wert von `currency_problem` liegt in der Unterscheidung.

    „Ungültig" schickt den Autor auf die Suche. „Untereinheit — rechne um",
    „Platzhalter" und „nicht vergeben" verlangen drei verschiedene Handlungen.
    """
    reasons = {
        currency_problem("gbx"),  # Gestalt
        currency_problem("GBX"),  # Untereinheit
        currency_problem("XXX"),  # Platzhalter
        currency_problem("ZZZ"),  # nicht vergeben
    }

    assert len(reasons) == 4, f"zwei Fälle melden dasselbe: {reasons}"
    assert currency_problem("EUR") == ""


@pytest.mark.parametrize("code", sorted(MINOR_UNIT_CODES))
def test_untereinheiten_sind_keine_waehrungen(code: str) -> None:
    """Der Faktor-100-Fehler, und er sieht völlig harmlos aus.

    ``GBX`` besteht jede Formprüfung: drei Großbuchstaben, wie ``GBP``. Nur ist
    ein Kurs in Pence hundertmal so groß wie derselbe Kurs in Pfund, und wer
    beides in derselben Spalte sammelt, merkt es an keiner einzigen Stelle.
    """
    assert not currency_is_valid(code)


def test_das_pfund_bleibt_eine_waehrung() -> None:
    """Die Gegenprobe zur Untereinheiten-Liste — und der Grund für ihre Form.

    Stünde ``GBp`` mit in der Menge und würde groß normalisiert verglichen,
    wäre ``GBP`` plötzlich keine Währung mehr. Die kleingeschriebene Variante
    scheitert schon an der Formprüfung und darf deshalb **nicht** in der Liste
    stehen.
    """
    assert currency_is_valid("GBP")
    assert not currency_is_valid("GBp")


@pytest.mark.parametrize("value", [1, 0.01, 141.55, 1e9])
def test_brauchbare_kurse(value: float) -> None:
    assert is_finite_price(value)


@pytest.mark.parametrize(
    "value",
    [
        None,
        "141.55",  # eine Zeichenkette rechnet sich nicht
        0,  # keine Angabe, die sich als Zahl ausgibt
        -1.0,
        float("nan"),
        float("inf"),
        float("-inf"),
        True,  # in Python eine Zahl — als Preis immer ein Fehler
    ],
)
def test_unbrauchbare_kurse(value: object) -> None:
    """``NaN`` und ``True`` sind die beiden, die jede Typprüfung überleben."""
    assert not is_finite_price(value)


@pytest.mark.parametrize("value", [0, -10, -0.5, 1, 141.55, 1e9])
def test_endliche_zahlen_duerfen_null_und_negativ_sein(value: float) -> None:
    """Der Unterschied zu `is_finite_price` — und der Grund für die Trennung.

    Eine Bereichsgrenze ist keine Kurszahl: ``(-10, 10)`` ist ein völlig
    richtiger Bereich für eine Tagesveränderung in Prozent, und ``0`` ist eine
    gültige Untergrenze. Wäre die Prüfung dieselbe wie beim Preis, müsste jeder
    solche Bereich als Beschreibungsfehler gemeldet werden.
    """
    assert is_finite_number(value)
    if value <= 0:
        assert not is_finite_price(value), "der Preis bleibt strenger"


@pytest.mark.parametrize(
    "value", [None, "10", float("nan"), float("inf"), float("-inf"), True]
)
def test_was_keine_endliche_zahl_ist(value: object) -> None:
    assert not is_finite_number(value)


def test_ein_zeitpunkt_ohne_zone_zaehlt_nicht() -> None:
    """``17:30`` ist in Toronto ein anderer Augenblick als in Frankfurt."""
    assert has_timezone(datetime(2026, 1, 2, 17, 30, tzinfo=timezone.utc))
    assert not has_timezone(datetime(2026, 1, 2, 17, 30))
    assert not has_timezone(None)


def test_eine_wirkungslose_zone_zaehlt_ebenfalls_nicht() -> None:
    """**Befund aus Runde 1**, und es ist der Fall, den man ohne Nachdenken lässt.

    Eine `tzinfo`, deren `utcoffset()` ``None`` liefert, ist erlaubt — und
    **Python selbst** behandelt einen damit versehenen Zeitpunkt als naiv. Ein
    Test auf `tzinfo is not None` ließ also gerade den Fall durch, der später
    beim ersten Vergleich mit `TypeError` abstürzt.

    Der Test weist beides nach: dass die alte Bedingung getäuscht worden wäre,
    und dass der Absturz real ist.
    """

    class HalfHearted(tzinfo):
        def utcoffset(self, moment):
            return None

        def dst(self, moment):
            return None

        def tzname(self, moment):
            return "halbherzig"

    moment = datetime(2026, 1, 2, 17, 30, tzinfo=HalfHearted())

    assert moment.tzinfo is not None, "die alte Bedingung wäre erfüllt gewesen"
    assert not has_timezone(moment)
    with pytest.raises(TypeError):
        _ = moment < datetime(2026, 1, 2, 18, 0, tzinfo=timezone.utc)


def test_streng_aufsteigend_erschlaegt_sortierung_und_duplikate() -> None:
    """Ein Tag doppelt ist der häufigere Fehler — und der unauffälligere."""
    days = [date(2025, 12, 29), date(2025, 12, 30), date(2025, 12, 31)]

    assert days_are_ordered(days)
    assert days_are_ordered([])
    assert days_are_ordered(days[:1])
    assert not days_are_ordered(list(reversed(days)))
    assert not days_are_ordered([days[0], days[0]]), "zwei Einträge für denselben Tag"
