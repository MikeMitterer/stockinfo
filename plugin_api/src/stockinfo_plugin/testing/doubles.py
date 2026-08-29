"""Doubles — Werkzeug hier, Verantwortung beim Host.

Wer eine Kette prüft, braucht Quellen, die auf Ansage antworten: die eine
findet nichts, die zweite ist ausgefallen, die dritte liefert. Ohne solche
Doubles wird jeder Kettentest ein Netztest, und ein Netztest beweist am Tag
seines Laufs etwas anderes als am nächsten.

**Was diese Doubles nicht tun.** Sie halten nicht endlos, um einen Zeitablauf
zu erzwingen. Ein Double, das wirklich hängt, prüft nicht den Schutzschalter,
sondern die Geduld des Testlaufs — und ein Abbruch, den niemand ausgelöst hat,
lässt sich auch nicht nachweisen. Wer eine Verzögerung braucht, stellt die Uhr
vor; das ist genau so aussagekräftig und kostet keine Sekunde.

**Die Kettensemantik bleibt beim Host.** Reihenfolge, Registry und
Schutzschalter prüft T-23, die Aggregation bis zum HTTP-Status T-20. Hier steht
nur das Werkzeug — sonst wäre das öffentliche Paket mit StockInfo-Interna
beladen, und ein fremder Plugin-Autor zöge sie mit.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from stockinfo_plugin.sources import (
    DailyCloseSource,
    FxSource,
    MetadataSource,
    QuoteSource,
    Resolver,
    Source,
)
from stockinfo_plugin.types import API_VERSION, NotFound

EPOCH = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)
"""Der Vorgabe-Startpunkt der Fake-Uhr — ein Freitagmittag in UTC.

Ein fester Wert und kein ``datetime.now()``: Ein Test, dessen Erwartung von der
Uhr der Maschine abhängt, ist am Monatsersten ein anderer Test. Freitag, damit
„der nächste Handelstag" nicht zufällig auf ein Wochenende fällt.
"""


class FakeClock:
    """Eine Uhr, die nur geht, wenn man sie stellt.

    Der Zweck ist nicht Bequemlichkeit, sondern Aussagekraft: Ein TTL von einer
    Stunde lässt sich mit einer echten Uhr nur prüfen, indem man eine Stunde
    wartet oder den TTL für den Test kleiner macht. Das eine ist unbezahlbar,
    das andere prüft eine Einstellung, die im Betrieb nie gilt.

    ``advance`` ist die einzige Art, die Zeit zu bewegen — sie läuft nicht von
    selbst. Zwei Aufrufe von `now` ohne `advance` dazwischen liefern denselben
    Augenblick, und genau das macht Erwartungen exakt statt ungefähr.
    """

    def __init__(self, start: datetime = EPOCH) -> None:
        """
        Args:
            start: Startzeitpunkt, **mit** Zeitzone.

        Raises:
            ValueError: Der Startzeitpunkt trägt keine Zone. Eine naive Uhr
                erzeugt naive Zeitstempel, und die kommen genau dort an, wo der
                Vertrag eine Zone verlangt — der Contract-Test schlüge dann bei
                einem Plugin an, dessen Fehler in Wahrheit im Testaufbau liegt.
        """
        if start.tzinfo is None:
            raise ValueError("FakeClock braucht einen Startzeitpunkt mit Zeitzone")
        self._now = start

    def now(self) -> datetime:
        """Der aktuelle Stand der Uhr."""
        return self._now

    def advance(self, seconds: float) -> datetime:
        """Stellt die Uhr vor.

        Args:
            seconds: Sekunden. Negative Werte sind erlaubt und gemeint — eine
                zurückgestellte Systemuhr ist ein realer Fall, und wer sich auf
                monotones Wachsen verlässt, soll das prüfen können.

        Returns:
            Der neue Stand.
        """
        self._now += timedelta(seconds=seconds)
        return self._now


@dataclass(frozen=True)
class Call:
    """Ein Aufruf, wie er im Protokoll steht.

    Attributes:
        request: Die Anfrage, unverändert.
        at: Der Stand der Uhr **beim Eintritt** in den Aufruf — vor der
            eingestellten Verzögerung. Sonst ließe sich nicht mehr sagen, wann
            gefragt wurde, sondern nur, wann geantwortet wurde.
    """

    request: object
    at: datetime


class FakeSource(Source):
    """Eine Quelle, die antwortet, was man ihr vorgibt — und mitschreibt.

    Die Antworten werden **der Reihe nach** verbraucht; ist die Liste am Ende,
    wiederholt sich die letzte. Das ist die Vorgabe, weil es der häufigere Fall
    ist: „diese Quelle ist ausgefallen" gilt für jeden Aufruf, nicht nur für den
    ersten. Wer je Anfrage eine eigene Antwort braucht, gibt `keyed` mit.

    Drei Sonderfälle, die kein Ergebnistyp abbildet, und die eine Kette trotzdem
    aushalten muss:

    * Ist die Antwort eine **Ausnahme-Instanz**, wird sie geworfen. Fremder Code
      wirft, auch wenn der Vertrag es verbietet — die Kette darf daran nicht
      sterben.
    * Ist die Antwort ein Wert, der **kein** Ergebnistyp ist (``None``, ein
      String, ein Dict), kommt er unverändert zurück. Ein Plugin, das den
      Vertrag missversteht, sieht genau so aus.
    * `delay_seconds` stellt die Uhr vor, statt zu warten.

    Beispiel::

        source = FakeResolver(
            [Unavailable("Netz"), Resolved(ListedIdentity("RY", "XTSE"))]
        )
        assert isinstance(source.resolve(request), Unavailable)   # erster Aufruf
        assert isinstance(source.resolve(request), Resolved)      # zweiter
        assert len(source.calls) == 2
    """

    name = "fake"
    api_version = API_VERSION

    def __init__(
        self,
        answers: object = (),
        *,
        keyed: dict | None = None,
        name: str | None = None,
        clock: FakeClock | None = None,
        delay_seconds: float = 0.0,
        responsible: bool = True,
        configured: bool = True,
        config: dict | None = None,
        log: "CallLog | None" = None,
    ) -> None:
        """
        Args:
            answers: Antworten in Reihenfolge. Ein einzelner Wert wird als
                Einerliste verstanden — ``FakeResolver(NotFound())`` ist der
                häufigste Fall und soll nicht nach Klammern verlangen.
            keyed: Antwort je Anfrage. Wird zuerst befragt; was hier steht,
                verbraucht nichts aus `answers`.
            name: Überschreibt den Quellennamen — nötig, sobald zwei Doubles in
                derselben Kette auseinandergehalten werden sollen.
            clock: Die Uhr für Protokoll und Verzögerung.
            delay_seconds: Um so viel wird die Uhr je Aufruf vorgestellt.
            responsible: Was `handles` antwortet.
            configured: Was `is_configured` antwortet.
            config: Der eigene Konfigurationsabschnitt, wie bei jeder Quelle.
            log: Gemeinsames Protokoll mehrerer Doubles — siehe `CallLog`.
        """
        super().__init__(config)
        if isinstance(answers, (list, tuple)):
            self._answers = list(answers)
        else:
            self._answers = [answers]
        self._keyed = dict(keyed or {})
        if name is not None:
            self.name = name
        self.clock = clock or FakeClock()
        self._delay = delay_seconds
        self._responsible = responsible
        self._configured = configured
        self._log = log
        self.calls: list[Call] = []
        """Das Aufrufprotokoll — Reihenfolge und Anzahl, in einer Liste.

        Eine Instanzliste und kein Klassenattribut: Als Klassenattribut wäre sie
        allen Doubles gemeinsam, und der zweite Testfall zählte die Aufrufe des
        ersten mit. Genau davor warnt
        `SourceContract.test_kein_veraenderlicher_zustand_an_der_klasse`.
        """

    # ─── Was jede Rolle gleich macht ─────────────────────────────────────────

    def is_configured(self) -> bool:
        return self._configured

    def handles(self, request: object) -> bool:
        """Zuständig, wie beim Bau angegeben. Zählt **nicht** als Aufruf.

        `handles` soll nach dem Vertrag nichts kosten. Stünde es im Protokoll,
        ließe sich nicht mehr prüfen, ob die Kette eine unzuständige Quelle
        wirklich übersprungen hat — das Protokoll zeigte in beiden Fällen einen
        Eintrag.
        """
        return self._responsible

    def _answer(self, request: object) -> object:
        """Schreibt den Aufruf mit und liefert die nächste vorgegebene Antwort."""
        self.calls.append(Call(request=request, at=self.clock.now()))
        if self._log is not None:
            self._log.record(self.name, request)
        if self._delay:
            self.clock.advance(self._delay)
        if request in self._keyed:
            answer = self._keyed[request]
        elif not self._answers:
            answer = NotFound()
        elif len(self._answers) == 1:
            answer = self._answers[0]
        else:
            answer = self._answers.pop(0)
        if isinstance(answer, BaseException):
            raise answer
        return answer

    # ─── Die fünf Rollen ─────────────────────────────────────────────────────

    def resolve(self, request):  # noqa: D102 — Vertrag steht in `Resolver`
        return self._answer(request)

    def fetch(self, request):  # noqa: D102 — Vertrag steht in `MetadataSource`
        return self._answer(request)

    def fetch_quote(self, request):  # noqa: D102 — Vertrag steht in `QuoteSource`
        return self._answer(request)

    def fetch_daily(self, request):  # noqa: D102 — Vertrag in `DailyCloseSource`
        return self._answer(request)

    def fetch_rate(self, request):  # noqa: D102 — Vertrag steht in `FxSource`
        return self._answer(request)


# Fünf schmale Klassen statt einer, die alles ist. Der Unterschied zählt, sobald
# jemand die Rolle prüft: Ein Double, das `isinstance(x, Resolver)` **und**
# `isinstance(x, QuoteSource)` erfüllt, käme durch eine Rollenprüfung, die einen
# echten Fehler hätte finden sollen. Das Verhalten steht trotzdem nur einmal da.


class FakeResolver(FakeSource, Resolver):
    """Ein `Resolver` auf Ansage."""

    name = "fake-resolver"
    api_version = API_VERSION


class FakeMetadataSource(FakeSource, MetadataSource):
    """Eine `MetadataSource` auf Ansage.

    `FIELDS` ist hier leer und wird beim Bau gesetzt, wenn ein Test sie
    braucht — eine Deklaration ins Double zu erfinden hieße, dem geprüften Host
    Felder unterzuschieben, die kein Autor je erklärt hat.
    """

    name = "fake-metadata"
    api_version = API_VERSION


class FakeQuoteSource(FakeSource, QuoteSource):
    """Eine `QuoteSource` auf Ansage."""

    name = "fake-quote"
    api_version = API_VERSION


class FakeDailySource(FakeSource, DailyCloseSource):
    """Eine `DailyCloseSource` auf Ansage."""

    name = "fake-daily"
    api_version = API_VERSION


class FakeFxSource(FakeSource, FxSource):
    """Eine `FxSource` auf Ansage."""

    name = "fake-fx"
    api_version = API_VERSION


@dataclass
class CallLog:
    """Ein gemeinsames Protokoll über **mehrere** Doubles.

    Ein Kettentest fragt nicht „wie oft wurde A gefragt", sondern „in welcher
    Reihenfolge wurden A, B und C gefragt". Diese Frage lässt sich aus drei
    getrennten Listen nicht beantworten: Sie enthalten die Zeitpunkte, aber die
    Fake-Uhr steht still, solange niemand sie stellt — zwei Aufrufe tragen
    dieselbe Zeit.

    Deshalb ein Protokoll, das alle teilen. Wer es benutzt, gibt jedem Double
    denselben `CallLog` mit; die Reihenfolge steht dann in `entries`.
    """

    entries: list[tuple[str, object]] = field(default_factory=list)

    def record(self, source_name: str, request: object) -> None:
        """Hängt einen Aufruf an."""
        self.entries.append((source_name, request))

    @property
    def order(self) -> list[str]:
        """Nur die Namen, in Aufrufreihenfolge — die übliche Erwartung."""
        return [name for name, _ in self.entries]
