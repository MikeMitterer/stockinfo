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

    @property
    def is_open(self) -> bool:
        """Wird gerade unterdrückt?

        Nach Ablauf von `open_for` meldet die Eigenschaft ``False``: Das ist
        der halb offene Zustand — der nächste Aufruf darf es versuchen, und
        `record_failure` würde ihn sofort wieder öffnen.
        """
        if self.opened_at is None:
            return False
        return self.clock() - self.opened_at < self.open_for

    def record_success(self) -> None:
        """Ein Aufruf hat funktioniert — der Schalter schließt vollständig."""
        self.failures = 0
        self.opened_at = None

    def record_failure(self) -> None:
        """Ein Aufruf ist fehlgeschlagen; ab der Schwelle öffnet der Schalter."""
        self.failures += 1
        if self.failures >= self.threshold:
            self.opened_at = self.clock()


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
            if self._breaker.is_open:
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
