"""Die eine Stelle, an der fremdem Code misstraut wird.

Ein geladenes Plugin läuft im Prozess der App. Es kann werfen, wo der Vertrag
`Unavailable` verlangt, und es kann bei jedem Aufruf erneut scheitern. Beides
darf die App weder abstürzen lassen noch bei jedem Abruf aufhalten.

**Genau ein Ort dafür.** Wäre das Abfangen über die Aufrufer verteilt, gäbe es
so viele Fassungen wie Aufrufstellen — und die vergessene wäre die, die den
Dienst umwirft.

**Was hier ausdrücklich nicht geht: einen laufenden Aufruf abbrechen.** Für
synchronen Python-Code im selben Prozess gibt es keine harte Zeitgrenze. Ein
Future-Timeout ließe den Aufrufer zurückkehren, der Thread liefe weiter — die
Quelle wäre also weder gestoppt noch frei. Zeitgrenzen setzt deshalb das Plugin
bei seinen eigenen I/O-Aufrufen; der Vertrag verlangt es, erzwingen kann er es
nicht.

Daraus folgt, was der Schutzschalter ehrlich kann: Er zählt Fehlschläge, wenn
ein Aufruf **zurückkehrt**. Ein endlos hängender Aufruf kehrt nie zurück, und
daran ändert auch eine eingespeiste Uhr nichts. Das ist eine dokumentierte
Grenze, keine Lücke — echte Abbruchgarantien bräuchten eigene Worker-Prozesse
samt IPC, und das ist für eine selbstgehostete App mit wenigen Quellen
unverhältnismäßig.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from threading import Lock
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog

from stockinfo_plugin.types import Unavailable

logger = structlog.get_logger()

FAILURE_THRESHOLD = 3
"""Fehlschläge in Folge, bis der Schalter öffnet.

Drei und nicht einer: Ein einzelner Ausfall ist Alltag — ein Zeitfehler, ein
502, ein Ratenlimit. Wer danach sofort stilllegt, schaltet eine gesunde Quelle
wegen eines Schluckaufs ab. Drei in Folge sind ein Muster.
"""

OPEN_FOR = timedelta(minutes=5)
"""Wie lange der Schalter offen bleibt, bevor ein Versuch erlaubt ist."""


def _now() -> datetime:
    """Die echte Uhr — im Test wird eine andere hereingereicht."""
    return datetime.now(timezone.utc)


@dataclass
class CircuitBreaker:
    """Zählt Fehlschläge und legt eine Quelle vorübergehend still.

    Drei Zustände, und der mittlere ist der wichtige:

    * **geschlossen** — alles läuft, Fehlschläge werden gezählt.
    * **offen** — die Quelle wird gar nicht erst gefragt. Jeder Aufruf gibt
      sofort `Unavailable` zurück, ohne zu warten.
    * **halb offen** — nach `open_for` darf **ein** Versuch durch. Gelingt er,
      ist der Schalter wieder zu und der Zähler bei null; scheitert er, öffnet
      er erneut.

    Ohne den mittleren Zustand gäbe es nur zwei Möglichkeiten, und beide sind
    falsch: dauerhaft still (die Quelle kommt nie zurück) oder sofort wieder
    voll (bei jedem Abruf wieder in denselben Fehler).

    Attributes:
        clock: Woher die Zeit kommt. Hereingereicht, damit Half-open und Reset
            **ohne echte Wartezeit** prüfbar sind — sonst dauerte ein Test
            fünf Minuten und liefe deshalb nie.
    """

    threshold: int = FAILURE_THRESHOLD
    open_for: timedelta = OPEN_FOR
    clock: Callable[[], datetime] = _now
    failures: int = 0
    opened_at: datetime | None = field(default=None)
    probing: bool = False
    """Läuft gerade der **eine** Probeaufruf des halb offenen Zustands?

    Ohne dieses Feld war „genau ein Versuch" eine Zusage der Prosa und nicht
    des Codes: Nach Ablauf der Frist meldete `is_open` schlicht ``False``, und
    zwei gleichzeitige Aufrufer gingen beide durch. Eine Gegenprobe mit zwei
    Threads an einer Barriere hat genau das gezeigt.
    """

    _lock: Lock = field(default_factory=Lock, repr=False, compare=False)

    def try_enter(self) -> bool:
        """Darf dieser Aufruf durch? Reserviert dabei den Probeplatz.

        **Fragen und Reservieren in einem Schritt, unter einer Sperre.** Eine
        getrennte Abfrage („ist offen?") und ein späteres Durchgehen wären
        genau das Rennen, das der halb offene Zustand vermeiden soll: Zwischen
        beiden Schritten kommt der zweite Thread durch.

        Returns:
            ``True``, wenn die Quelle gefragt werden darf.
        """
        with self._lock:
            if self.opened_at is None:
                return True
            if self.clock() - self.opened_at < self.open_for:
                return False
            if self.probing:
                # Ein anderer Aufrufer ist bereits der Probeversuch. Für alle
                # weiteren bleibt der Schalter zu — sonst liefe die Quelle in
                # genau den Sturm, vor dem sie geschützt werden soll.
                return False
            self.probing = True
            return True

    @property
    def is_open(self) -> bool:
        """Wird gerade unterdrückt? — **Auskunft, keine Reservierung.**

        Für Diagnose und Tests. Wer entscheiden will, ob er durchdarf, nimmt
        `try_enter`: Diese Eigenschaft fragt nur nach und hält nichts fest.
        """
        with self._lock:
            if self.opened_at is None:
                return False
            return self.clock() - self.opened_at < self.open_for

    def record_success(self) -> None:
        """Ein Aufruf hat funktioniert — der Schalter schließt vollständig."""
        with self._lock:
            self.failures = 0
            self.opened_at = None
            self.probing = False

    def record_failure(self) -> None:
        """Ein Aufruf ist fehlgeschlagen; ab der Schwelle öffnet der Schalter.

        Ein gescheiterter **Probeversuch** öffnet sofort wieder: Die Frist
        beginnt von vorn, und der reservierte Platz wird freigegeben.
        """
        with self._lock:
            self.failures += 1
            if self.probing or self.failures >= self.threshold:
                self.opened_at = self.clock()
            self.probing = False


class GuardedSource:
    """Legt sich um eine Quelle und fängt ab, was sie nicht halten kann.

    Jeder Methodenaufruf geht durch dieselbe Kapsel:

    * Der Schalter ist offen → sofort `Unavailable`, ohne die Quelle zu fragen.
    * Die Quelle wirft → `Unavailable` mit Typ und Text der Ausnahme, und der
      Fehlschlag wird gezählt. Ein Verstoß gegen den Vertrag wird damit zu
      einer **Antwort**, nicht zu einem Abbruch der App.
    * Die Quelle liefert `Unavailable` → ebenfalls ein Fehlschlag. Sie hat sich
      korrekt verhalten, aber sie konnte nicht arbeiten, und für den
      Schutzschalter ist das dasselbe.
    * Alles andere → Erfolg, Zähler zurück auf null.

    Nicht aufrufbare Attribute werden **unverändert** durchgereicht: `name`,
    `cost` und `api_version` sind Angaben über die Quelle, keine Aufrufe an
    sie.
    """

    def __init__(self, source: object, breaker: CircuitBreaker | None = None) -> None:
        """
        Args:
            source: Die zu kapselnde Quelle.
            breaker: Ein eigener Schalter. Ohne Angabe bekommt jede Quelle
                ihren eigenen — ein geteilter würde eine gesunde Quelle
                stilllegen, weil eine andere ausgefallen ist.
        """
        self._source = source
        self._breaker = breaker or CircuitBreaker()

    @property
    def source(self) -> object:
        """Die gekapselte Quelle — für Diagnose, nicht zum Umgehen."""
        return self._source

    @property
    def breaker(self) -> CircuitBreaker:
        """Der Schalter dieser Quelle."""
        return self._breaker

    def __getattr__(self, name: str) -> Any:
        """Reicht Attribute durch und kapselt Methoden.

        `__getattr__` läuft nur für das, was diese Klasse nicht selbst hat —
        die Kapsel steht also nicht im Weg, wenn jemand `breaker` oder `source`
        will.
        """
        attribute = getattr(self._source, name)
        if not callable(attribute):
            return attribute

        def guarded(*args: object, **kwargs: object) -> object:
            source_name = getattr(self._source, "name", type(self._source).__name__)
            if not self._breaker.try_enter():
                logger.info("source_suppressed", source=source_name, method=name)
                return Unavailable(
                    f"{source_name} ist nach wiederholtem Fehlschlag vorübergehend "
                    "stillgelegt"
                )
            try:
                answer = attribute(*args, **kwargs)
            except Exception as error:  # noqa: BLE001 — fremder Code, jeder Fehler zählt
                self._breaker.record_failure()
                logger.warning(
                    "source_raised",
                    source=source_name,
                    method=name,
                    error=f"{type(error).__name__}: {error}",
                    failures=self._breaker.failures,
                )
                return Unavailable(f"{source_name}: {type(error).__name__}: {error}")

            if isinstance(answer, Unavailable):
                self._breaker.record_failure()
            else:
                self._breaker.record_success()
            return answer

        return guarded
