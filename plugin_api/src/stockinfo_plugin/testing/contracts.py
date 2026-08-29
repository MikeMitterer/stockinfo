"""Contract-Tests — der eigentliche Zweck dieses Pakets.

Ein Plugin-Autor erbt von der Vertragsklasse seiner Rolle, nennt zwei oder drei
Anfragen und bekommt den ganzen Vertrag maschinell geprüft. Das ist der Hebel
für eine App, die weltweit funktionieren soll: Wer in Toronto ein Plugin
schreibt, weist damit nach, dass es den Vertrag erfüllt — an einem Papier, das
niemand sonst je gesehen hat.

Fünf Rollen, fünf Verträge:

============================ ==================================================
`ResolverContract`           Zuständigkeit, Treffer, unbekannt, Fehler, ISIN
                             und **echter** MIC
`MetadataContract`           Deklaration, Einheit, Herkunft, Plausibilität
`QuoteContract`              Preis mit **Pflichtwährung**, endliche Werte,
                             Zeitpunkt mit Zone
`DailyContract`              Datum, Schlusskurs, Währung, Sortierung, keine
                             Duplikate, `adjusted` deklariert
`FxContract`                 Paar, positive endliche Rate, Zeitpunkt,
                             Identitäts- und Fehlerfall
============================ ==================================================

Verwendung::

    from stockinfo_plugin.testing import ResolverContract

    class TestCanadaFile(ResolverContract):
        def make_source(self):
            return CanadaFileResolver({"path": "tests/fixtures/canada.csv"})

        responsible = ResolveRequest(isin="CA78012H5675")
        not_responsible = ResolveRequest(isin="IE00B4L5Y983")
        unknown = ResolveRequest(isin="CA0679011084")
"""

from datetime import date

import pytest

from stockinfo_plugin.invariants import (
    currency_problem,
    days_are_ordered,
    has_timezone,
    identity_problem,
    is_finite_price,
    isin_check_digit_is_valid,
)
from stockinfo_plugin.types import (
    API_VERSION,
    DailyRequest,
    DailySeries,
    FxRate,
    FxRequest,
    ListedIdentity,
    NotFound,
    NotResponsible,
    Quote,
    QuoteRequest,
    Resolved,
    ResolveRequest,
    Unavailable,
    Unit,
    Unsupported,
    isin_of,
)

# Antworten, die eine Quelle statt eines Treffers geben darf. Als Tupel und
# nicht je Vertrag neu geschrieben: Käme irgendwann eine fünfte Ergebnisart
# hinzu, liefe die Aufzählung sonst an fünf Stellen auseinander.
NON_HITS = (NotResponsible, NotFound, Unavailable)


def _lacks_hit(answer: object, expected: type) -> str:
    """Formuliert die Meldung, wenn statt eines Treffers etwas anderes kam."""
    reason = getattr(answer, "error", "") or getattr(answer, "reason", "")
    detail = f" ({reason})" if reason else ""
    return (
        f"erwartet {expected.__name__}, bekommen {type(answer).__name__}{detail}"
    )


class SourceContract:
    """Was für jede Quelle gilt, unabhängig von ihrer Rolle."""

    def make_source(self):
        """Baut die zu prüfende Quelle. Muss überschrieben werden."""
        raise NotImplementedError

    def test_kein_veraenderlicher_zustand_an_der_klasse(self) -> None:
        """Zwei Testfälle dürfen sich nicht beeinflussen — und tun es doch.

        Eine Liste oder ein Dict **an der Klasse** gehört allen Instanzen
        gemeinsam. Ein Cache als ``_seen = {}`` neben `name` sieht harmlos aus,
        macht aber jeden Testfall zur Vorbedingung des nächsten: Der zweite
        Fall bekommt den Treffer des ersten, und beide sind grün — bis jemand
        die Reihenfolge ändert.

        Geprüft wird die **Klasse**, nicht das Verhalten. Das ist Absicht: Ein
        Verhaltenstest müsste raten, welcher Aufruf den Zustand verändert;
        veränderliche Klassenattribute lassen sich dagegen aufzählen. Deshalb
        ist auch `MetadataSource.FIELDS` ein Tupel und keine Liste.

        Instanzzustand (``self._cache = {}`` im ``__init__``) ist ausdrücklich
        erlaubt — er verschwindet mit der Instanz.
        """
        source_class = type(self.make_source())
        found = [
            f"{ancestor.__name__}.{name}"
            for ancestor in source_class.__mro__
            if ancestor is not object
            for name, value in vars(ancestor).items()
            if not name.startswith("__") and isinstance(value, (list, dict, set))
        ]
        assert not found, (
            f"veränderliche Klassenattribute: {', '.join(found)} — sie sind "
            "allen Instanzen gemeinsam, ein Testfall wird damit zur "
            "Vorbedingung des nächsten. Ausweg je nach Zweck: eine Konstante "
            "als tuple/frozenset/MappingProxyType deklarieren, veränderlichen "
            "Zustand nach __init__ verschieben."
        )

    def test_hat_einen_namen(self) -> None:
        """Ohne Namen lässt sich die Quelle nicht konfigurieren und nicht melden."""
        source = self.make_source()
        assert source.name, "name ist leer — die Quelle wäre nicht adressierbar"
        assert " " not in source.name, "name darf kein Leerzeichen enthalten"

    def test_vertragsversion_ist_bekannt(self) -> None:
        """Die Quelle nennt ihre Vertragsversion **selbst**.

        Die untere Grenze ist nicht überflüssig: ``api_version = 0`` oder ein
        negativer Wert kämen sonst durch, und beides heißt in der Praxis „nicht
        gesetzt" — der Vorgabewert der Basisklasse wurde überschrieben, ohne
        eine gültige Version zu nennen.

        **Geprüft wird die eigene Deklaration, nicht der geerbte Wert.** Bis
        T-31 stand hier `self.make_source().api_version`, und das las den
        Vorgabewert von `Source` mit. Ein Plugin ohne eigene Deklaration
        bestand damit diesen Vertragstest und wurde vom Loader unmittelbar
        danach abgewiesen — die beiden Schranken widersprachen sich, und der
        Autor erfuhr es erst im Betrieb.

        Der Blick geht in `__dict__` der **konkreten** Klasse und nicht die
        Klassenhierarchie entlang: Sonst deklarierte eine gemeinsame
        Basisklasse für alle ihre Ableitungen mit, und die Vererbung wäre
        zurück, die diese Regel gerade ausschließt.
        """
        source_class = type(self.make_source())
        assert "api_version" in source_class.__dict__, (
            f"{source_class.__name__} erbt api_version nur. Jede Quelle nennt "
            f"die Vertragsversion selbst — der Loader weist sie sonst ab, und "
            f"zwar erst im Betrieb."
        )
        version = source_class.__dict__["api_version"]
        assert isinstance(version, int), f"api_version ist {type(version).__name__}"
        assert 1 <= version <= API_VERSION, (
            f"api_version {version} liegt außerhalb von 1..{API_VERSION}"
        )

    def test_kosten_sind_deklariert(self) -> None:
        """Was eine Anfrage kostet — **Information, keine Sortierregel**.

        Der Docstring hier behauptete bis Runde 1, die Kette sortiere danach.
        Das war falsch und widersprach dem eigenen Vertrag: Seit T-22 bestimmt
        **ausschließlich** `sources.yaml` die Reihenfolge, und `Source.cost`
        sagt das auch. Der Wert dient der Anzeige und der Warnung („diese Kette
        fragt eine kostenpflichtige Quelle zuerst") — damit eine teure Quelle
        nicht unbemerkt vor einer kostenlosen steht.

        Ein falscher Wert kostet trotzdem Geld, nur anders: Er unterdrückt die
        Warnung, statt die Reihenfolge zu ändern.
        """
        assert self.make_source().cost in ("free", "metered", "paid")

    def test_konfigurationsstand_ist_beantwortbar(self) -> None:
        """`is_configured` darf nicht werfen — sie wird vor allem anderen gefragt."""
        assert isinstance(self.make_source().is_configured(), bool)

    def test_wer_stillsteht_sagt_warum(self) -> None:
        """Eine Quelle, die nicht arbeiten kann, nennt den Grund.

        **Befund aus Runde 1: Der Vertrag verlangte eine verständliche Diagnose
        und prüfte nur ein `bool`.** Ein Betreiber sah in `GET /sources` eine
        Quelle als nicht einsatzbereit und hatte keine einzige Handlung, die
        daraus folgte — fehlt ein Schlüssel, eine Datei, ein Kontingent?

        Geprüft wird deshalb beides zusammen: dass `configuration_problem`
        nicht wirft, dass sie einen Satz liefert, wenn die Quelle stillsteht,
        und dass sie **schweigt**, wenn die Quelle läuft. Die letzte Hälfte ist
        nicht Zierde: Eine Quelle, die arbeitet und trotzdem eine Beanstandung
        meldet, füllt die Diagnose mit Rauschen, bis niemand mehr hinsieht.

        Die Länge ist eine Untergrenze gegen `"nein"` und `"error"` — kein
        Beweis für Verständlichkeit, aber die Grenze, unterhalb derer keine
        stehen kann.
        """
        source = self.make_source()
        try:
            problem = source.configuration_problem()
        except Exception as exc:  # noqa: BLE001 — genau das ist der Prüfgegenstand
            pytest.fail(f"configuration_problem() warf {type(exc).__name__}: {exc}")

        assert isinstance(problem, str), (
            f"configuration_problem() gab {type(problem).__name__} zurück, "
            "erwartet wird ein Satz für einen Menschen"
        )
        if source.is_configured():
            assert problem == "", (
                f"die Quelle arbeitet, meldet aber {problem!r} — eine Diagnose, "
                "die auch im Normalfall spricht, wird nicht mehr gelesen"
            )
        else:
            assert len(problem.strip()) >= 10, (
                f"die Quelle steht still und begründet es mit {problem!r}. Der "
                "Satz richtet sich an jemanden, der die Quelle nicht gebaut "
                "hat: Was fehlt, und was soll er tun?"
            )


class ResolverContract(SourceContract):
    """Der vollständige Vertrag eines Resolvers.

    Drei Anfragen sind zu setzen: eine zuständige mit bekanntem Papier, eine
    unzuständige, und eine zuständige mit unbekanntem Papier.
    """

    responsible: ResolveRequest
    not_responsible: ResolveRequest
    unknown: ResolveRequest

    unsupported: ResolveRequest | None = None
    """Ein Papier, das die Quelle **erkennt, aber nicht führt** — etwa ein Index.

    Optional, weil nicht jede Quelle so einen Fall hat: Wer nur eine
    Wertpapierdatei liest, erkennt außerhalb seiner Datei gar nichts und hat
    zwischen `NotFound` und `Unsupported` nichts zu unterscheiden. Wer den Fall
    aber hat, setzt ihn hier — sonst bliebe die einzige Antwortart ungeprüft,
    deren Sinn gerade darin besteht, nicht mit `NotFound` verwechselt zu werden.
    """

    collector_codes: frozenset[str] = frozenset()
    """Sammelcodes des Hosts, die **kein** MIC sind — etwa StockInfos ``US``.

    Der Vertrag kennt sie nicht: Welche es gibt, hängt daran, welche Quellen
    jemand einsetzt. Ein Host, der eigene führt, setzt sie hier; die
    Längenregel fängt zweistellige Codes ohnehin ab.
    """

    def test_zustaendigkeit_wird_erkannt(self) -> None:
        source = self.make_source()
        assert source.handles(self.responsible) is True
        assert source.handles(self.not_responsible) is False

    def test_die_eigenen_pruefdaten_sind_gueltige_isins(self) -> None:
        """Zuerst die Prüfdaten, dann das Plugin.

        Eine Anfrage mit kaputter ISIN prüft nicht, was der Autor glaubt: Wer
        „unbekanntes Papier" mit ``CA00000000000`` prüft — dreizehn Zeichen,
        keine gültige ISIN —, misst die Formprüfung der Quelle und nicht ihr
        Verhalten bei einem gültigen, aber nicht geführten Papier. Das sind
        zwei verschiedene Fälle, und der zweite ist der interessante.

        Genau dieser Fehler stand in der Beispielsuite dieses Pakets, bis die
        Regel ihn gefunden hat.
        """
        for slot, request in (
            ("responsible", self.responsible),
            ("not_responsible", self.not_responsible),
            ("unknown", self.unknown),
        ):
            if request.isin is None:
                continue
            assert isin_check_digit_is_valid(request.isin), (
                f"{slot}: {request.isin!r} ist keine gültige ISIN "
                "(Gestalt oder Prüfziffer)"
            )

    def test_unzustaendig_meldet_das_auch_so(self) -> None:
        """`NotResponsible` statt `NotFound` — sonst bricht die Kette zu früh ab.

        Der Unterschied ist nicht Formsache: Aus `NotFound` folgt am Ende ein
        404, aus `NotResponsible` nur „der Nächste, bitte".
        """
        answer = self.make_source().resolve(self.not_responsible)
        assert isinstance(answer, NotResponsible), (
            f"unzuständige Anfrage beantwortet mit {type(answer).__name__}"
        )

    def test_bekanntes_papier_wird_aufgeloest(self) -> None:
        """Die gelieferte Identität ist in ihrer Form vollständig.

        Was „vollständig" heißt, hängt an der Form und steht in
        `invariants.identity_problem`: Ticker und echter MIC bei `listed`,
        Basiswert und Quote-Währung bei `pair`, eine ISIN mit gültiger
        Prüfziffer bei `isin_only`.

        Hier stand einmal ``"." not in ticker`` als Prüfung darauf, dass kein
        Börsensuffix mitkommt. Das war falsch: Ein Punkt gehört bei
        Anteilsklassen zum Ticker selbst (``BRK.A``). Ob ein Suffix vorliegt,
        lässt sich nur gegen die Börsentabelle entscheiden — und die kennt der
        Vertrag bewusst nicht. Diese Prüfung gehört auf die App-Seite.
        """
        answer = self.make_source().resolve(self.responsible)
        assert isinstance(answer, Resolved), _lacks_hit(answer, Resolved)
        problem = identity_problem(answer.identity, self.collector_codes)
        assert not problem, f"gelieferte Identität ist unbrauchbar: {problem}"

    def test_wer_eine_form_liefert_hat_sie_deklariert(self) -> None:
        """Die Antwort bleibt innerhalb der zugesagten Fähigkeiten.

        **Beim Resolver kann der Host nicht vorher filtern.** Eine
        `ResolveRequest` trägt ISIN, Symbol, Vorzugsbörse und Währung — weder
        die Identitätsform noch die Gattung, denn beide sind das *Ergebnis*
        der Auflösung. Die Zusage lässt sich deshalb nur an der Antwort
        prüfen, und genau das tut dieser Test: Wer eine `pair`-Identität
        liefert, ohne `pair` zu deklarieren, hat etwas zugesagt, worauf der
        Host seine Kette nicht einrichten konnte.
        """
        source = self.make_source()
        answer = source.resolve(self.responsible)
        assert isinstance(answer, Resolved), _lacks_hit(answer, Resolved)
        assert answer.identity.kind in source.SUPPORTED_KINDS, (
            f"liefert eine Identität der Form {answer.identity.kind!r}, "
            f"deklariert aber nur {sorted(source.SUPPORTED_KINDS)}"
        )
        if answer.instrument_type is not None:
            assert answer.instrument_type in source.SUPPORTED_TYPES, (
                f"liefert die Gattung {answer.instrument_type!r}, deklariert "
                f"aber nur {sorted(source.SUPPORTED_TYPES)}"
            )

    def test_erkannt_und_nicht_gefuehrt_heisst_nicht_unbekannt(self) -> None:
        """`Unsupported` statt `NotFound` — und die Gattung muss dabeistehen.

        Der Fall wird nur geprüft, wenn die Suite ihn gesetzt hat; ohne
        `unsupported` gibt es nichts zu behaupten.

        Geprüft wird beides, was diese Antwort ausmacht:

        1. **Sie ist nicht `NotFound`.** Wer ein Papier erkannt hat, darf nicht
           „kenne ich nicht" sagen — der Host baut daraus ein 404 und der
           Benutzer sucht den Fehler in seiner Eingabe.
        2. **Die genannte Gattung steht nicht in der eigenen Zusage.** Sonst
           widerspricht die Quelle sich selbst: Sie hat `bond` deklariert und
           lehnt eine Anleihe als nicht geführt ab. Der Host hätte seine Kette
           dann auf eine Fähigkeit eingerichtet, die es nicht gibt — dieselbe
           Verwechslung wie in `test_wer_eine_form_liefert_hat_sie_deklariert`,
           nur aus der anderen Richtung.
        """
        if self.unsupported is None:
            return
        source = self.make_source()
        answer = source.resolve(self.unsupported)
        assert isinstance(answer, Unsupported), (
            "ein erkanntes, aber nicht geführtes Papier beantwortet mit "
            f"{type(answer).__name__} — der Host kann daraus keinen Grund nennen"
        )
        assert answer.instrument_type, "Unsupported ohne Gattung ist ein NotFound"
        assert answer.instrument_type not in source.SUPPORTED_TYPES, (
            f"lehnt die Gattung {answer.instrument_type!r} als nicht geführt ab, "
            f"deklariert sie aber in {sorted(source.SUPPORTED_TYPES)}"
        )

    def test_die_antwort_gehoert_zur_frage(self) -> None:
        """Die Ergebnis-ISIN ist die Anfrage-ISIN — oder es gibt keine.

        Der Fehler, den das findet, ist unauffällig und teuer: Eine Quelle
        sucht unscharf, findet ein *ähnliches* Papier und antwortet mit dessen
        Kennung. Formal ist alles in Ordnung — Ticker da, MIC da, ISIN da —,
        nur gehört die Antwort zu einem anderen Wertpapier. Danach hängen
        Kurse und Kennzahlen am falschen Bestand.

        Liefert die Quelle **keine** ISIN zurück, ist das in Ordnung: Sie hat
        nichts behauptet. Geprüft wird nur, wer etwas behauptet.
        """
        answer = self.make_source().resolve(self.responsible)
        assert isinstance(answer, Resolved), _lacks_hit(answer, Resolved)
        delivered = isin_of(answer.identity)
        if delivered is None or self.responsible.isin is None:
            return
        assert delivered.upper() == self.responsible.isin.upper(), (
            f"gefragt nach {self.responsible.isin}, geantwortet zu "
            f"{delivered} — das ist ein anderes Wertpapier"
        )
        assert isin_check_digit_is_valid(delivered.upper()), (
            f"gelieferte ISIN {delivered!r} hat eine falsche Prüfziffer"
        )

    def test_dieselbe_frage_zweimal_gibt_dieselbe_antwort(self) -> None:
        """Zwei Fälle beeinflussen sich nicht — die Verhaltensseite.

        `test_kein_veraenderlicher_zustand_an_der_klasse` sieht die Ursache,
        dieser Test die Wirkung. Beide zusammen, weil keiner allein trägt: Ein
        Zustand kann auch in einem Modul stehen statt an der Klasse, und eine
        saubere Klasse beweist noch keine wiederholbare Antwort.

        Nur beim Resolver, nicht in `SourceContract`: Eine Auflösung ist ihrer
        Natur nach stabil, ein Kurs nicht. Denselben Test für `QuoteContract`
        zu verlangen hieße, von einer Live-Quelle zu fordern, dass sich der
        Markt zwischen zwei Aufrufen nicht bewegt.
        """
        source = self.make_source()

        first = source.resolve(self.responsible)
        second = source.resolve(self.responsible)

        assert first == second, (
            f"zwei gleiche Anfragen, zwei Antworten: {first!r} / {second!r}"
        )

    def test_unbekanntes_papier_ist_nicht_dasselbe_wie_unzustaendig(self) -> None:
        answer = self.make_source().resolve(self.unknown)
        assert isinstance(answer, (NotFound, Unavailable)), (
            f"unbekanntes Papier im Zuständigkeitsbereich beantwortet mit "
            f"{type(answer).__name__} — erwartet NotFound"
        )

    @pytest.mark.parametrize(
        "broken",
        [
            ResolveRequest(),
            ResolveRequest(isin=""),
            ResolveRequest(isin="nicht-wirklich-eine-isin"),
            ResolveRequest(isin="X" * 500),
        ],
    )
    def test_wirft_niemals(self, broken: ResolveRequest) -> None:
        """Eine Ausnahme aus fremdem Code darf die App nicht mitreißen.

        Die Registry fängt zwar ab, aber ein Plugin, das sich darauf verlässt,
        verliert die Möglichkeit, den Grund zu benennen — `Unavailable` trägt
        eine Meldung, ein abgefangener Stacktrace nicht.
        """
        source = self.make_source()
        try:
            answer = source.resolve(broken)
        except Exception as exc:  # noqa: BLE001 — genau das ist der Prüfgegenstand
            pytest.fail(f"resolve() warf {type(exc).__name__}: {exc}")
        # Auf den Typ prüfen, nicht auf `is not None`: Sonst käme auch ein
        # zurückgegebener String oder ein leeres Dict durch, und der Vertrag
        # wäre nur scheinbar erfüllt.
        #
        # **`Unsupported` steht hier und nur hier** (T-31). Die Liste ist
        # `NON_HITS` plus diese eine Antwort — die anderen Rollen benutzen
        # `NON_HITS` unverändert weiter. Das ist Absicht und keine
        # Vergesslichkeit: „erkannt, aber nicht geführt" ist ein Befund der
        # *Auflösung*. Eine Kursquelle, die ihn zurückgäbe, hätte über die
        # Gattung eines Papiers geurteilt, das ihr bereits identifiziert
        # gereicht wurde — die Entscheidung war da längst gefallen.
        assert isinstance(answer, (Resolved, *NON_HITS, Unsupported)), (
            f"resolve() gab {type(answer).__name__} zurück, keine Resolution"
        )


class MetadataContract(SourceContract):
    """Der vollständige Vertrag einer Metadaten-Quelle.

    Zwei Anfragen sind zu setzen: eine zuständige mit bekanntem Papier und
    eine unzuständige.
    """

    responsible: ResolveRequest
    not_responsible: ResolveRequest

    def test_felder_sind_deklariert(self) -> None:
        """Ohne Deklaration weiß die App nicht, wie sie den Wert behandeln soll."""
        source = self.make_source()
        assert source.FIELDS, "FIELDS ist leer — die Quelle sagt nicht, was sie liefert"
        names = [spec.name for spec in source.FIELDS]
        assert len(names) == len(set(names)), f"doppelte Felder: {names}"

    def test_jedes_feld_traegt_eine_beschriftung(self) -> None:
        """Jedes deklarierte Feld braucht wenigstens einen englischen Namen.

        Der Vertrag kann nicht wissen, welches Feld für die App neu ist — den
        kanonischen Katalog kennt nur sie. Deshalb wird die Beschriftung für
        **alle** Felder verlangt: Für bekannte gewinnt ohnehin der Katalog der
        App, für unbekannte ist sie die einzige Rettung vor einem rohen
        Feldnamen in der Oberfläche.
        """
        for spec in self.make_source().FIELDS:
            assert spec.label_en or spec.label_de, (
                f"Feld '{spec.name}' hat keine Beschriftung"
            )

    def test_zustaendigkeit_wird_erkannt(self) -> None:
        source = self.make_source()
        assert source.handles(self.responsible) is True
        assert source.handles(self.not_responsible) is False

    def _readings_for_responsible(self) -> list:
        """Die Werte des bekannten Falls — und der Nachweis, dass es welche gibt.

        **Der Kern des Runde-1-Befunds.** Vorher stand in jedem Test
        ``source.fetch(self.responsible) or []``, und danach lief eine Schleife.
        Bei ``None`` und bei ``[]`` lief sie **null Mal** — jede Zusicherung
        darunter war grün, ohne je einen Wert gesehen zu haben. Eine Quelle,
        die für ihr eigenes bekanntes Papier nichts liefert, bestand damit den
        ganzen Vertrag.

        ``None`` ist hier besonders falsch: Es heißt „konnte nicht nachsehen".
        Der Autor hat diesen Fall als **bekannt** benannt; kann seine Quelle
        ihn im Test nicht beantworten, prüft der ganze Vertrag nichts.
        """
        source = self.make_source()
        readings = source.fetch(self.responsible)
        assert readings is not None, (
            "fetch() gab None für den als bekannt benannten Fall — None heißt "
            "konnte nicht nachsehen, und damit prüft der Vertrag nichts"
        )
        assert readings, (
            "fetch() gab eine leere Liste für den als bekannt benannten Fall. "
            "Jede Prüfung darunter liefe als leere Schleife grün durch; bitte "
            "einen Fall als `responsible` nennen, den die Quelle wirklich führt"
        )
        return readings

    def test_der_bekannte_fall_liefert_ueberhaupt_werte(self) -> None:
        """Ohne diese Zeile prüft der ganze Metadaten-Vertrag nichts. Siehe oben."""
        self._readings_for_responsible()

    def test_liefert_nur_deklarierte_felder(self) -> None:
        """Was nicht deklariert ist, kann die App weder umrechnen noch anzeigen.

        Der Test ist die Gegenprobe zur Deklaration: Ohne ihn driften `FIELDS`
        und die tatsächlich gelieferten Werte auseinander, und die Abweichung
        fällt erst auf, wenn ein Wert stumm verschwindet.
        """
        source = self.make_source()
        for reading in self._readings_for_responsible():
            assert source.declared(reading.field) is not None, (
                f"Feld '{reading.field}' geliefert, aber nicht in FIELDS deklariert"
            )

    def test_einheiten_stimmen_mit_der_deklaration_ueberein(self) -> None:
        """Sonst rechnet die App mit dem falschen Faktor — und zwar unbemerkt."""
        source = self.make_source()
        for reading in self._readings_for_responsible():
            spec = source.declared(reading.field)
            if spec is not None and spec.unit is not None:
                assert reading.unit is spec.unit, (
                    f"Feld '{reading.field}': geliefert als {reading.unit}, "
                    f"deklariert als {spec.unit}"
                )

    def test_der_werttyp_passt_zur_deklarierten_bedienart(self) -> None:
        """``kind="number"`` und dann ``"not-a-number"`` — genau das ging durch.

        **Befund aus Runde 1.** Die App entscheidet anhand von `FieldSpec.kind`,
        womit sie das Feld anzeigt und ob sie damit rechnet. Kommt dort eine
        Zeichenkette an, wo eine Zahl deklariert ist, scheitert nicht die
        Quelle, sondern der Verbraucher — irgendwann später, an einer Stelle,
        die mit der Quelle nichts zu tun hat.

        ``None`` bleibt erlaubt: „das Feld führe ich, habe aber diesmal keinen
        Wert" ist eine gültige Aussage und etwas anderes als ein falscher Typ.
        """
        source = self.make_source()
        expected_types = {"number": (int, float), "boolean": (bool,), "text": (str,)}
        for reading in self._readings_for_responsible():
            spec = source.declared(reading.field)
            if spec is None or reading.value is None:
                continue
            allowed = expected_types.get(spec.kind)
            if allowed is None:
                continue
            # `bool` ist in Python ein `int` — ein Wahrheitswert in einem
            # Zahlenfeld ist trotzdem ein Fehler und wird hier nicht als Zahl
            # durchgewinkt.
            is_bool = isinstance(reading.value, bool)
            fits = isinstance(reading.value, allowed) and (
                spec.kind == "boolean" or not is_bool
            )
            assert fits, (
                f"Feld '{reading.field}' ist als {spec.kind} deklariert, "
                f"geliefert wurde {reading.value!r} "
                f"({type(reading.value).__name__})"
            )

    def test_werte_liegen_im_deklarierten_bereich(self) -> None:
        """Die Quelle deklariert ihren eigenen Wertebereich — und hält ihn ein.

        **Befund aus Runde 1: `FieldSpec.is_plausible()` wurde nie aufgerufen.**
        Die Methode stand da, war getestet, und kein Vertrag benutzte sie — die
        Deklaration war damit eine Absichtserklärung.

        Der Anlass ist gemessen: Eine Quelle meldete ``0.0000`` als Kostenquote
        für einen Fonds, der real rund 0,06 % kostet. Eine stille Null tarnt
        sich als gültiger Wert, und niemand sieht sie sich an.
        """
        source = self.make_source()
        for reading in self._readings_for_responsible():
            spec = source.declared(reading.field)
            if spec is None or spec.plausible is None:
                continue
            assert spec.is_plausible(reading.value), (
                f"Feld '{reading.field}': {reading.value!r} liegt außerhalb des "
                f"selbst deklarierten Bereichs {spec.plausible}"
            )

    def test_ein_betrag_ohne_waehrung_ist_bedeutungslos(self) -> None:
        """``Unit.ABSOLUTE`` verlangt eine Währung — sonst ist es nur eine Zahl.

        **Befund aus Runde 1.** `Reading.currency` trug den Hinweis im
        Docstring und niemand prüfte ihn. Ein Fondsvolumen von
        2.289.978.572.800 sagt nichts, solange nicht dabeisteht, ob es USD oder
        CAD sind — und es sind, gemessen, oft nicht die, die man annimmt.
        """
        source = self.make_source()
        for reading in self._readings_for_responsible():
            spec = source.declared(reading.field)
            unit = reading.unit or (spec.unit if spec else None)
            if unit is not Unit.ABSOLUTE or reading.value is None:
                continue
            problem = currency_problem(reading.currency)
            assert not problem, (
                f"Feld '{reading.field}' ist ein absoluter Betrag ohne "
                f"brauchbare Währung: {problem}"
            )

    def test_werte_tragen_ihre_herkunft(self) -> None:
        """Bei mehreren Quellen je Feld ist „wer war das" die erste Frage."""
        for reading in self._readings_for_responsible():
            assert reading.source, f"Feld '{reading.field}' nennt keine Herkunft"

    def test_unzustaendig_liefert_eine_leere_liste(self) -> None:
        """Unzuständig ist ``[]``, nicht ``None`` — der Unterschied trägt Bedeutung.

        ``None`` heißt „konnte nicht nachsehen" und schützt den gespeicherten
        Stand. Wer bei Unzuständigkeit ``None`` zurückgibt, macht aus einer
        klaren Aussage einen Ausfall — und die Kette kann nicht mehr
        unterscheiden, ob es sich zu warten lohnt.
        """
        readings = self.make_source().fetch(self.not_responsible)
        assert readings == [], (
            f"unzuständige Quelle lieferte {readings!r} statt einer leeren Liste"
        )

    @pytest.mark.parametrize(
        "broken",
        [
            ResolveRequest(),
            ResolveRequest(isin=""),
            ResolveRequest(isin="nicht-wirklich-eine-isin"),
        ],
    )
    def test_fetch_wirft_niemals(self, broken: ResolveRequest) -> None:
        """Fehler werden zu ``None``, nicht zu einer Ausnahme."""
        try:
            self.make_source().fetch(broken)
        except Exception as exc:  # noqa: BLE001 — genau das ist der Prüfgegenstand
            pytest.fail(f"fetch() warf {type(exc).__name__}: {exc}")


class QuoteContract(SourceContract):
    """Der vollständige Vertrag einer Kursquelle.

    Drei Anfragen sind zu setzen: ein geführtes Listing, ein Listing außerhalb
    des Zuständigkeitsbereichs, und ein zuständiges, aber unbekanntes.
    """

    responsible: QuoteRequest
    not_responsible: QuoteRequest
    unknown: QuoteRequest

    def test_zustaendigkeit_wird_erkannt(self) -> None:
        source = self.make_source()
        assert source.handles(self.responsible) is True
        assert source.handles(self.not_responsible) is False

    def test_unzustaendig_meldet_das_auch_so(self) -> None:
        """`NotResponsible` statt `NotFound` — sonst bricht die Kette zu früh ab."""
        answer = self.make_source().fetch_quote(self.not_responsible)
        assert isinstance(answer, NotResponsible), _lacks_hit(answer, NotResponsible)

    def test_der_kurs_traegt_seine_waehrung(self) -> None:
        """Ein Kurs ohne Währung ist eine Zahl — und wird als solche verrechnet.

        Deshalb ist `Quote.currency` Pflichtfeld und nicht ``str | None``: Was
        optional ist, fehlt irgendwann, und der Kurs sieht danach genauso aus
        wie einer mit Währung. Geprüft wird zusätzlich **welche** — ``GBX`` ist
        keine Währung, sondern eine Untereinheit, und der Fehler kostet den
        Faktor 100.
        """
        answer = self.make_source().fetch_quote(self.responsible)
        assert isinstance(answer, Quote), _lacks_hit(answer, Quote)
        problem = currency_problem(answer.currency)
        assert not problem, f"currency: {problem}"

    def test_der_preis_ist_eine_brauchbare_zahl(self) -> None:
        """``NaN``, ``inf`` und ``0`` sind keine Kurse — und überleben jeden Typtest.

        Sie entstehen still: ein leeres Feld, das als ``float("nan")``
        durchgereicht wird, eine Division durch ein fehlendes Volumen. Danach
        steckt der Wert jede spätere Rechnung an, und die Spur zurück zur
        Quelle ist kalt.
        """
        answer = self.make_source().fetch_quote(self.responsible)
        assert isinstance(answer, Quote), _lacks_hit(answer, Quote)
        assert is_finite_price(answer.price), (
            f"price {answer.price!r} ist kein brauchbarer Kurs — endlich und "
            "größer null. Wer nichts hat, meldet Unavailable statt einer Null."
        )

    def test_der_zeitpunkt_traegt_eine_zone(self) -> None:
        """``17:30`` ist in Toronto ein anderer Augenblick als in Frankfurt."""
        answer = self.make_source().fetch_quote(self.responsible)
        assert isinstance(answer, Quote), _lacks_hit(answer, Quote)
        assert has_timezone(answer.as_of), (
            f"as_of {answer.as_of!r} hat keine Zeitzone — hinterher ist nicht "
            "mehr feststellbar, welcher Augenblick gemeint war"
        )

    def test_unbekanntes_listing_ist_nicht_dasselbe_wie_unzustaendig(self) -> None:
        answer = self.make_source().fetch_quote(self.unknown)
        assert isinstance(answer, (NotFound, Unavailable)), (
            f"unbekanntes Listing im Zuständigkeitsbereich beantwortet mit "
            f"{type(answer).__name__} — erwartet NotFound"
        )

    @pytest.mark.parametrize(
        "broken",
        [
            QuoteRequest(ListedIdentity(ticker="", mic="")),
            QuoteRequest(ListedIdentity(ticker="X" * 500, mic="XXXX")),
            QuoteRequest(ListedIdentity(ticker="RY", mic="nicht-wirklich-ein-mic")),
        ],
    )
    def test_wirft_niemals(self, broken: QuoteRequest) -> None:
        """Eine Ausnahme aus fremdem Code darf die App nicht mitreißen."""
        try:
            answer = self.make_source().fetch_quote(broken)
        except Exception as exc:  # noqa: BLE001 — genau das ist der Prüfgegenstand
            pytest.fail(f"fetch_quote() warf {type(exc).__name__}: {exc}")
        assert isinstance(answer, (Quote, *NON_HITS)), (
            f"fetch_quote() gab {type(answer).__name__} zurück, kein QuoteResult"
        )


class DailyContract(SourceContract):
    """Der vollständige Vertrag einer Historienquelle."""

    responsible: DailyRequest
    not_responsible: DailyRequest
    unknown: DailyRequest

    def test_zustaendigkeit_wird_erkannt(self) -> None:
        source = self.make_source()
        assert source.handles(self.responsible) is True
        assert source.handles(self.not_responsible) is False

    def test_unzustaendig_meldet_das_auch_so(self) -> None:
        answer = self.make_source().fetch_daily(self.not_responsible)
        assert isinstance(answer, NotResponsible), _lacks_hit(answer, NotResponsible)

    def _series_for_responsible(self) -> DailySeries:
        """Die Reihe des bekannten Listings — und der Nachweis, dass sie Tage hat.

        **Der Kern des Runde-1-Befunds für diesen Vertrag.** Eine stets leere
        `DailySeries` bestand ihn vollständig: Sortierung, Schlusskurse und
        Zeitraum liefen als **leere Schleifen** grün durch, und `currency` und
        `adjusted` prüfte niemand gegen Inhalt.

        Eine leere Reihe ist als *Antwort* völlig zulässig — „nachgesehen, in
        diesem Zeitraum lag nichts" ist eine gültige Aussage. Sie taugt nur
        nicht als **Prüffall**: Der Autor hat dieses Listing als bekannt
        benannt, und wenn seine Quelle dafür nichts liefert, prüft der Vertrag
        nichts.
        """
        answer = self.make_source().fetch_daily(self.responsible)
        assert isinstance(answer, DailySeries), _lacks_hit(answer, DailySeries)
        assert answer.bars, (
            "die Reihe für das als bekannt benannte Listing ist leer. Als "
            "Antwort wäre das zulässig, als Prüffall nicht: Sortierung, Kurse "
            "und Zeitraum liefen darunter als leere Schleifen grün durch. "
            "Bitte einen Zeitraum wählen, in dem die Quelle wirklich Tage hat."
        )
        return answer

    def test_die_reihe_hat_ueberhaupt_tage(self) -> None:
        """Ohne diese Zeile prüft der ganze Historien-Vertrag nichts. Siehe oben."""
        self._series_for_responsible()

    def test_die_reihe_ist_sortiert_und_doppelfrei(self) -> None:
        """Zwei Einträge für denselben Tag entstehen still — und zählen doppelt.

        Der übliche Weg dorthin: Ein Anbieter liefert seitenweise, und zwei
        Seiten überlappen sich am Rand. Wer die Reihe danach summiert oder eine
        Rendite darüber rechnet, bekommt ein Ergebnis, das niemand nachprüft,
        weil es plausibel aussieht.

        Geprüft wird **streng** aufsteigend: Das erschlägt Sortierung und
        Duplikate in einer Aussage.
        """
        answer = self._series_for_responsible()
        days = [bar.day for bar in answer.bars]
        assert days_are_ordered(days), (
            "die Tage sind nicht streng aufsteigend — unsortiert oder doppelt: "
            f"{[str(day) for day in days[:12]]}"
        )

    def test_jeder_schlusskurs_ist_eine_brauchbare_zahl(self) -> None:
        answer = self._series_for_responsible()
        for bar in answer.bars:
            assert is_finite_price(bar.close), (
                f"Schlusskurs am {bar.day} ist {bar.close!r} — endlich und "
                "größer null erwartet"
            )

    def test_waehrung_und_bereinigungsstand_sind_deklariert(self) -> None:
        """``adjusted`` ist nicht ableitbar — es steht nicht im Zahlenmaterial.

        Bereinigte und unbereinigte Reihen desselben Papiers unterscheiden sich
        um zweistellige Prozentwerte, und beide sehen für sich völlig plausibel
        aus. Wer sie mischt, sieht einen Kurssprung, wo eine Ausschüttung war.
        """
        answer = self._series_for_responsible()
        problem = currency_problem(answer.currency)
        assert not problem, f"currency der Reihe: {problem}"
        assert isinstance(answer.adjusted, bool), (
            f"adjusted ist {type(answer.adjusted).__name__} statt bool — der "
            "Bereinigungsstand muss deklariert sein, nicht erschlossen"
        )

    def test_der_angefragte_zeitraum_wird_eingehalten(self) -> None:
        """Was außerhalb liegt, hat der Aufrufer nicht bestellt.

        Ein Anbieter, der großzügig ein paar Tage mehr liefert, wirkt
        harmlos — bis jemand die Reihen zweier Abrufe aneinanderhängt und die
        Ränder sich überlappen. Dann steht wieder derselbe Tag zweimal da, und
        diesmal hat ihn keine einzelne Antwort verletzt.
        """
        answer = self._series_for_responsible()
        for bar in answer.bars:
            if self.responsible.start is not None:
                assert bar.day >= self.responsible.start, (
                    f"{bar.day} liegt vor dem angefragten Beginn "
                    f"{self.responsible.start}"
                )
            if self.responsible.end is not None:
                assert bar.day <= self.responsible.end, (
                    f"{bar.day} liegt nach dem angefragten Ende "
                    f"{self.responsible.end}"
                )

    def test_unbekanntes_listing_ist_nicht_dasselbe_wie_unzustaendig(self) -> None:
        answer = self.make_source().fetch_daily(self.unknown)
        assert isinstance(answer, (NotFound, Unavailable)), (
            f"unbekanntes Listing beantwortet mit {type(answer).__name__}"
        )

    @pytest.mark.parametrize(
        "broken",
        [
            DailyRequest(ListedIdentity(ticker="", mic="")),
            DailyRequest(ListedIdentity(ticker="X" * 500, mic="XXXX")),
            DailyRequest(
                ListedIdentity(ticker="RY", mic="XTSE"), start=date(2030, 1, 1)
            ),
        ],
    )
    def test_wirft_niemals(self, broken: DailyRequest) -> None:
        try:
            answer = self.make_source().fetch_daily(broken)
        except Exception as exc:  # noqa: BLE001 — genau das ist der Prüfgegenstand
            pytest.fail(f"fetch_daily() warf {type(exc).__name__}: {exc}")
        assert isinstance(answer, (DailySeries, *NON_HITS)), (
            f"fetch_daily() gab {type(answer).__name__} zurück, kein DailyResult"
        )


class FxContract(SourceContract):
    """Der vollständige Vertrag einer Devisenquelle.

    Zwei Anfragen sind zu setzen: ein geführtes Paar und ein Paar außerhalb des
    Zuständigkeitsbereichs. Den Identitätsfall bildet der Vertrag selbst aus
    ``responsible.base`` — der Autor soll nicht dieselbe Währung zweimal
    hinschreiben müssen, und so kann er den Fall auch nicht versehentlich
    weglassen.
    """

    responsible: FxRequest
    not_responsible: FxRequest

    def test_zustaendigkeit_wird_erkannt(self) -> None:
        source = self.make_source()
        assert source.handles(self.responsible) is True
        assert source.handles(self.not_responsible) is False

    def test_unzustaendig_meldet_das_auch_so(self) -> None:
        answer = self.make_source().fetch_rate(self.not_responsible)
        assert isinstance(answer, NotResponsible), _lacks_hit(answer, NotResponsible)

    def test_der_kurs_nennt_sein_paar(self) -> None:
        """Ein Wechselkurs ohne sein Paar ist eine Zahl ohne Bedeutung.

        Und die Richtung zu verwechseln ist der häufigste Fehler mit
        Devisenkursen überhaupt: ``0.92`` und ``1.087`` sehen beide plausibel
        aus, und nur eines von beidem ist EUR→USD.
        """
        answer = self.make_source().fetch_rate(self.responsible)
        assert isinstance(answer, FxRate), _lacks_hit(answer, FxRate)
        assert (answer.base, answer.quote) == (
            self.responsible.base,
            self.responsible.quote,
        ), (
            f"gefragt nach {self.responsible.base}→{self.responsible.quote}, "
            f"geantwortet zu {answer.base}→{answer.quote}"
        )
        problems = [
            currency_problem(code) for code in (answer.base, answer.quote)
        ]
        assert not any(problems), f"das Paar taugt nicht: {'; '.join(filter(None, problems))}"

    def test_die_rate_ist_eine_brauchbare_zahl(self) -> None:
        answer = self.make_source().fetch_rate(self.responsible)
        assert isinstance(answer, FxRate), _lacks_hit(answer, FxRate)
        assert is_finite_price(answer.rate), (
            f"rate {answer.rate!r} ist unbrauchbar — endlich und größer null "
            "erwartet"
        )
        assert has_timezone(answer.as_of), (
            f"as_of {answer.as_of!r} hat keine Zeitzone"
        )

    def test_eine_waehrung_in_sich_selbst_ist_genau_eins(self) -> None:
        """Der Identitätsfall — und er ist keine Formalie.

        Eine Quelle, die für EUR→EUR ``0.9998`` meldet, rechnet über einen
        Umweg, typischerweise über den Dollar. Derselbe Umweg verfälscht dann
        jedes andere Paar auch, nur unsichtbar: Bei EUR→USD fällt eine
        Abweichung im Promillebereich niemandem auf.

        Deshalb ``== 1.0`` und keine Toleranz. Die einzige Zahl, die hier
        richtig ist, kennt jeder — sie muss nicht gemessen werden.
        """
        identity = FxRequest(base=self.responsible.base, quote=self.responsible.base)

        answer = self.make_source().fetch_rate(identity)

        assert isinstance(answer, FxRate), _lacks_hit(answer, FxRate)
        # **Erst das Paar, dann die Rate** — Befund aus Runde 1. Hier stand nur
        # die Ratenprüfung, und deshalb bestand eine Quelle den Identitätsfall
        # mit `FxRate(base="USD", quote="JPY", rate=1.0)` auf eine
        # CAD→CAD-Anfrage. Eine `1.0` ohne ihr Paar ist keine Aussage: Sie ist
        # für irgendein Paar fast immer falsch und für dieses immer richtig.
        assert (answer.base, answer.quote) == (identity.base, identity.quote), (
            f"gefragt nach {identity.base}→{identity.quote}, geantwortet zu "
            f"{answer.base}→{answer.quote} — die Rate 1.0 gilt dann für ein "
            "anderes Paar und ist dort mit hoher Wahrscheinlichkeit falsch"
        )
        assert answer.rate == 1.0, (
            f"{identity.base}→{identity.base} ergab {answer.rate!r} statt 1.0 — "
            "die Quelle rechnet über einen Umweg"
        )

    @pytest.mark.parametrize(
        "broken",
        [
            FxRequest(base="", quote=""),
            FxRequest(base="EUR", quote="nicht-wirklich-eine-waehrung"),
            FxRequest(base="ZZZ", quote="QQQ"),
        ],
    )
    def test_wirft_niemals(self, broken: FxRequest) -> None:
        try:
            answer = self.make_source().fetch_rate(broken)
        except Exception as exc:  # noqa: BLE001 — genau das ist der Prüfgegenstand
            pytest.fail(f"fetch_rate() warf {type(exc).__name__}: {exc}")
        assert isinstance(answer, (FxRate, *NON_HITS)), (
            f"fetch_rate() gab {type(answer).__name__} zurück, kein FxResult"
        )
