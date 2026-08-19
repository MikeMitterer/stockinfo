"""Contract-Tests — der eigentliche Zweck dieses Pakets.

Ein Plugin-Autor erbt von `ResolverContract`, nennt drei Anfragen und bekommt
den ganzen Vertrag maschinell geprüft. Das ist der Hebel für eine App, die
weltweit funktionieren soll: Wer in Toronto ein Plugin schreibt, weist damit
nach, dass es den Vertrag erfüllt — an einem Papier, das niemand sonst je
gesehen hat.

Verwendung::

    from stockinfo_plugin.testing import ResolverContract

    class TestCanadaFile(ResolverContract):
        def make_source(self):
            return CanadaFileResolver({"path": "tests/fixtures/canada.csv"})

        responsible = ResolveRequest(isin="CA78012H5675")
        not_responsible = ResolveRequest(isin="IE00B4L5Y983")
        unknown = ResolveRequest(isin="CA00000000000")
"""

import pytest

from stockinfo_plugin.types import (
    API_VERSION,
    NotFound,
    NotResponsible,
    Resolved,
    ResolveRequest,
    Unavailable,
)


class SourceContract:
    """Was für jede Quelle gilt, unabhängig von ihrer Rolle."""

    def make_source(self):
        """Baut die zu prüfende Quelle. Muss überschrieben werden."""
        raise NotImplementedError

    def test_hat_einen_namen(self) -> None:
        """Ohne Namen lässt sich die Quelle nicht konfigurieren und nicht melden."""
        source = self.make_source()
        assert source.name, "name ist leer — die Quelle wäre nicht adressierbar"
        assert " " not in source.name, "name darf kein Leerzeichen enthalten"

    def test_vertragsversion_ist_bekannt(self) -> None:
        """Ein Plugin gegen eine spätere Version würde stillschweigend brechen."""
        assert self.make_source().api_version <= API_VERSION

    def test_kosten_sind_deklariert(self) -> None:
        """Die Kette sortiert danach — ein falscher Wert kostet echtes Geld."""
        assert self.make_source().cost in ("free", "metered", "paid")

    def test_konfigurationsstand_ist_beantwortbar(self) -> None:
        """`is_configured` darf nicht werfen — sie wird vor allem anderen gefragt."""
        assert isinstance(self.make_source().is_configured(), bool)


class ResolverContract(SourceContract):
    """Der vollständige Vertrag eines Resolvers.

    Drei Anfragen sind zu setzen: eine zuständige mit bekanntem Papier, eine
    unzuständige, und eine zuständige mit unbekanntem Papier.
    """

    responsible: ResolveRequest
    not_responsible: ResolveRequest
    unknown: ResolveRequest

    def test_zustaendigkeit_wird_erkannt(self) -> None:
        source = self.make_source()
        assert source.handles(self.responsible) is True
        assert source.handles(self.not_responsible) is False

    def test_unzustaendig_meldet_das_auch_so(self) -> None:
        """`NotResponsible` statt `NotFound` — sonst bricht die Kette zu früh ab.

        Der Unterschied ist nicht Formsache: Aus `NotFound` folgt am Ende ein
        404, aus `NotResponsible` nur „der Nächste, bitte".
        """
        antwort = self.make_source().resolve(self.not_responsible)
        assert isinstance(antwort, NotResponsible), (
            f"unzuständige Anfrage beantwortet mit {type(antwort).__name__}"
        )

    def test_bekanntes_papier_wird_aufgeloest(self) -> None:
        antwort = self.make_source().resolve(self.responsible)
        assert isinstance(antwort, Resolved), (
            f"bekanntes Papier beantwortet mit {type(antwort).__name__}"
        )
        assert antwort.ticker, "ticker fehlt"
        assert antwort.mic, "mic fehlt — ohne Börse ist der Ticker mehrdeutig"
        assert "." not in antwort.ticker, (
            f"ticker '{antwort.ticker}' trägt ein Börsensuffix — "
            "Ticker und MIC gehören getrennt"
        )

    def test_unbekanntes_papier_ist_nicht_dasselbe_wie_unzustaendig(self) -> None:
        antwort = self.make_source().resolve(self.unknown)
        assert isinstance(antwort, (NotFound, Unavailable)), (
            f"unbekanntes Papier im Zuständigkeitsbereich beantwortet mit "
            f"{type(antwort).__name__} — erwartet NotFound"
        )

    @pytest.mark.parametrize(
        "kaputt",
        [
            ResolveRequest(),
            ResolveRequest(isin=""),
            ResolveRequest(isin="nicht-wirklich-eine-isin"),
            ResolveRequest(isin="X" * 500),
        ],
    )
    def test_wirft_niemals(self, kaputt: ResolveRequest) -> None:
        """Eine Ausnahme aus fremdem Code darf die App nicht mitreißen.

        Die Registry fängt zwar ab, aber ein Plugin, das sich darauf verlässt,
        verliert die Möglichkeit, den Grund zu benennen — `Unavailable` trägt
        eine Meldung, ein abgefangener Stacktrace nicht.
        """
        source = self.make_source()
        try:
            antwort = source.resolve(kaputt)
        except Exception as exc:  # noqa: BLE001 — genau das ist der Prüfgegenstand
            pytest.fail(f"resolve() warf {type(exc).__name__}: {exc}")
        assert antwort is not None


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
        namen = [spec.name for spec in source.FIELDS]
        assert len(namen) == len(set(namen)), f"doppelte Felder: {namen}"

    def test_neue_felder_tragen_eine_beschriftung(self) -> None:
        """Ein Feld, das die App nicht kennt, braucht wenigstens einen englischen Namen.

        Sonst steht in der Oberfläche der rohe Feldname — und der Nutzer sieht
        ``tracking_error`` statt „Tracking error".
        """
        for spec in self.make_source().FIELDS:
            assert spec.label_en or spec.label_de, (
                f"Feld '{spec.name}' hat keine Beschriftung"
            )

    def test_zustaendigkeit_wird_erkannt(self) -> None:
        source = self.make_source()
        assert source.handles(self.responsible) is True
        assert source.handles(self.not_responsible) is False

    def test_liefert_nur_deklarierte_felder(self) -> None:
        """Was nicht deklariert ist, kann die App weder umrechnen noch anzeigen.

        Der Test ist die Gegenprobe zur Deklaration: Ohne ihn driften `FIELDS`
        und die tatsächlich gelieferten Werte auseinander, und die Abweichung
        fällt erst auf, wenn ein Wert stumm verschwindet.
        """
        source = self.make_source()
        readings = source.fetch(self.responsible) or []
        for reading in readings:
            assert source.declared(reading.field) is not None, (
                f"Feld '{reading.field}' geliefert, aber nicht in FIELDS deklariert"
            )

    def test_einheiten_stimmen_mit_der_deklaration_ueberein(self) -> None:
        """Sonst rechnet die App mit dem falschen Faktor — und zwar unbemerkt."""
        source = self.make_source()
        for reading in source.fetch(self.responsible) or []:
            spec = source.declared(reading.field)
            if spec is not None and spec.unit is not None:
                assert reading.unit is spec.unit, (
                    f"Feld '{reading.field}': geliefert als {reading.unit}, "
                    f"deklariert als {spec.unit}"
                )

    def test_werte_tragen_ihre_herkunft(self) -> None:
        """Bei mehreren Quellen je Feld ist „wer war das" die erste Frage."""
        source = self.make_source()
        for reading in source.fetch(self.responsible) or []:
            assert reading.source, f"Feld '{reading.field}' nennt keine Herkunft"

    def test_unzustaendig_liefert_nichts(self) -> None:
        """Eine unzuständige Quelle darf keine Werte erfinden."""
        readings = self.make_source().fetch(self.not_responsible)
        assert not readings, f"unzuständige Quelle lieferte {readings}"

    @pytest.mark.parametrize(
        "kaputt",
        [
            ResolveRequest(),
            ResolveRequest(isin=""),
            ResolveRequest(isin="nicht-wirklich-eine-isin"),
        ],
    )
    def test_fetch_wirft_niemals(self, kaputt: ResolveRequest) -> None:
        """Fehler werden zu ``None``, nicht zu einer Ausnahme."""
        try:
            self.make_source().fetch(kaputt)
        except Exception as exc:  # noqa: BLE001 — genau das ist der Prüfgegenstand
            pytest.fail(f"fetch() warf {type(exc).__name__}: {exc}")
