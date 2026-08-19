"""Die Datentypen des Plugin-Vertrags.

Alles hier ist **öffentlich** und versioniert: Was in diesem Modul steht, dürfen
fremde Plugins verwenden und darauf bauen. Änderungen daran sind Änderungen an
`API_VERSION`.

Zwei Entwurfsentscheidungen prägen die Typen:

* **Anfragen sind Objekte, keine Parameterlisten.** Ein `ResolveRequest` lässt
  sich um Felder erweitern, ohne dass eine einzige fremde Signatur bricht. Bei
  ``resolve_isin(isin: str)`` wäre jede Erweiterung ein Bruch — und fremde
  Plugins kann man nicht einfach nachziehen.
* **Antworten sind vier verschiedene Dinge, kein ``None``.** Ein leeres Ergebnis
  beantwortet nicht die Frage, *warum* es leer ist. „Nicht mein Bereich",
  „kenne ich nicht" und „gerade kaputt" verlangen unterschiedliche Reaktionen
  der Kette: überspringen, aufhören, später erneut versuchen.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Literal

API_VERSION = 1
"""Version des Vertrags. Ein Plugin nennt die Version, gegen die es gebaut ist."""

Cost = Literal["free", "metered", "paid"]
"""Was eine Anfrage kostet — steuert die Reihenfolge in der Kette."""


# ─── Anfrage ──────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ResolveRequest:
    """Die Frage an einen Resolver: Welches Listing gehört zu diesem Papier?

    Attributes:
        isin: ISIN, falls bekannt. Sie ist der übliche Einstieg, aber nicht
            garantiert vorhanden — manche Märkte liefern keine.
        symbol: Vom Nutzer genanntes Symbol, falls die Aufnahme darüber lief.
        preferred_mic: Bevorzugte Börse als MIC (ISO 10383), z.B. ``XETR``.
            Ein Resolver darf davon abweichen, wenn er dort nichts findet —
            er sollte es dann im Ergebnis kenntlich machen.
    """

    isin: str | None = None
    symbol: str | None = None
    preferred_mic: str = "XETR"


# ─── Antworten ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Resolved:
    """Treffer: So heißt das Papier an dieser Börse.

    Bewusst **kein** fertiges Anbieter-Symbol, sondern Ticker und MIC getrennt.
    Wie daraus ``EUNL.DE`` (Yahoo) oder ``EUNL.XETRA`` (EODHD) wird, ist Sache
    dessen, der die Kurse holt — ein Resolver muss keine fremden
    Symbol-Konventionen kennen.

    ``currency`` fehlt mit Absicht: Die Handelswährung stammt immer aus dem
    Live-Kurs, nie aus der Auflösung.
    """

    ticker: str
    mic: str
    isin: str | None = None
    name: str | None = None
    instrument_type: str | None = None  # "etf" | "stock" | None


@dataclass(frozen=True)
class NotResponsible:
    """Nicht mein Zuständigkeitsbereich — die Kette geht weiter, ohne Kosten."""

    reason: str = ""


@dataclass(frozen=True)
class NotFound:
    """Zuständig, aber dieses Papier ist mir unbekannt.

    Anders als `NotResponsible`: Hier hat jemand nachgesehen. Die Kette darf
    weitergehen, aber ein leeres Gesamtergebnis heißt dann tatsächlich
    „gibt es nicht" und rechtfertigt ein 404.
    """


@dataclass(frozen=True)
class Unavailable:
    """Zuständig, aber gerade nicht arbeitsfähig — Netz, Kontingent, Fehler.

    Die Kette darf weitergehen, aber ein leeres Gesamtergebnis heißt hier
    **nicht** „gibt es nicht", sondern „konnte nicht nachsehen" — das ist ein
    502, kein 404. Der Unterschied entscheidet auch, ob ein gespeicherter
    Stand überschrieben werden darf.
    """

    error: str = ""


Resolution = Resolved | NotResponsible | NotFound | Unavailable
"""Was ein Resolver antworten kann."""


# ─── Einheiten (für Metadaten-Quellen) ────────────────────────────────────────


class Unit(Enum):
    """Maßeinheit eines gelieferten Werts.

    Sie steht am Wert, nicht in der Dokumentation: Dieselbe Kostenquote kommt
    als ``0.19`` (Prozent), ``0.0019`` (Anteil) oder ``19`` (Basispunkte) —
    gemessen bei zwei Quellen, die beide „TER" dazu sagen.
    """

    PERCENT = "percent"
    RATIO = "ratio"
    BASIS_POINTS = "basis_points"
    MILLIONS = "millions"
    ABSOLUTE = "absolute"  # braucht zusätzlich eine Währungsangabe


@dataclass(frozen=True)
class Reading:
    """Was eine Quelle zu genau einem Feld sagt — samt Einheit und Herkunft.

    Die Herkunft steht am einzelnen Wert und nicht an der ganzen Antwort: Wenn
    zwei Quellen dasselbe Papier ergänzen, ist „wer hat das TER geliefert" eine
    andere Frage als „wer hat das Domizil geliefert".
    """

    field: str
    value: float | str | bool | None
    unit: Unit | None = None
    source: str = ""


FieldKind = Literal["number", "text", "boolean"]
"""Bedienart eines Feldes — bestimmt, womit die Oberfläche es bearbeitet."""

# Umrechnungsfaktoren auf eine gemeinsame Basis je Dimension. Einheiten
# verschiedener Dimensionen lassen sich nicht ineinander überführen — ein
# Fondsvolumen ist keine Kostenquote, auch wenn beide Zahlen sind.
_RATIO_BASE: dict[Unit, float] = {
    Unit.RATIO: 1.0,
    Unit.PERCENT: 0.01,
    Unit.BASIS_POINTS: 0.0001,
}


@dataclass(frozen=True)
class FieldSpec:
    """Die Deklaration eines Feldes: Bedeutung, Einheit, Wertebereich.

    Eine Quelle deklariert damit, **was** sie liefert — die App weiß dadurch,
    wie sie es umrechnen, prüfen und anzeigen muss, ohne den Feldnamen zu
    kennen.

    Attributes:
        name: Kanonischer Feldname, z.B. ``ter``.
        kind: Bedienart für die Oberfläche.
        unit: Einheit der gelieferten Werte. Ohne Angabe findet keine
            Umrechnung statt.
        plausible: Erlaubter Wertebereich **nach** der Umrechnung. Was
            außerhalb liegt, gilt als *kein Wert* — nicht als *dieser Wert*.
            Der Anlass ist gemessen: Eine Quelle meldete ``0.0000`` als
            Kostenquote für einen Fonds, der real rund 0,06 % kostet. Eine
            stille Null tarnt sich als gültiger Wert.
        label_en: Englische Beschriftung. Pflicht für Felder, die eine Quelle
            neu einführt — die App hat für sie keinen Katalogeintrag.
        label_de: Deutsche Beschriftung, falls der Autor sie liefern kann.
        overridable: Ob ein Mensch den Wert von Hand nachtragen darf.
    """

    name: str
    kind: FieldKind = "text"
    unit: Unit | None = None
    plausible: tuple[float, float] | None = None
    label_en: str = ""
    label_de: str = ""
    overridable: bool = True

    def is_plausible(self, value: object) -> bool:
        """Liegt der Wert im erwarteten Bereich?

        Args:
            value: Der zu prüfende Wert, bereits in der Zieleinheit.

        Returns:
            ``True``, wenn kein Bereich gesetzt ist, der Wert keine Zahl ist
            (dann greift die Prüfung nicht) oder er innerhalb liegt.
        """
        if self.plausible is None or not isinstance(value, (int, float)):
            return True
        low, high = self.plausible
        return low <= float(value) <= high


def convert(value: float, from_unit: Unit | None, to_unit: Unit | None) -> float | None:
    """Rechnet einen Wert zwischen zwei Einheiten um.

    Der Grund, warum das im Vertrag steht und nicht in der App: Dieselbe
    Kostenquote kommt bei zwei Quellen als ``0.19`` und als ``0.0003`` an —
    beide nennen es „TER". Wer die Einheit nicht mitliefert, liefert eine Zahl
    ohne Bedeutung.

    Args:
        value: Der umzurechnende Wert.
        from_unit: Einheit des Werts. ``None`` heißt „keine Angabe".
        to_unit: Zieleinheit. ``None`` heißt „keine Angabe".

    Returns:
        Den umgerechneten Wert; den unveränderten Wert, wenn eine der
        Einheiten fehlt oder beide gleich sind; ``None``, wenn die Einheiten
        verschiedenen Dimensionen angehören — ein Fondsvolumen lässt sich
        nicht in Prozent ausdrücken.
    """
    if from_unit is None or to_unit is None or from_unit is to_unit:
        return value
    if from_unit in _RATIO_BASE and to_unit in _RATIO_BASE:
        # Auf zehn Stellen gerundet: Der Weg über die gemeinsame Basis sind
        # zwei Gleitkomma-Operationen, und 6 Basispunkte ergeben dabei
        # 0.060000000000000005 statt 0.06. Der Wert geht in die Datenbank und
        # in die Anzeige — zehn Stellen entfernen das Artefakt und lassen jede
        # Genauigkeit stehen, die eine Kennzahl je braucht.
        return round(value * _RATIO_BASE[from_unit] / _RATIO_BASE[to_unit], 10)
    # Verschiedene Dimensionen — bewusst kein Rateversuch. Beträge in
    # Landeswährung brauchen einen Wechselkurs und damit einen Stichtag; das
    # ist eine Entscheidung der App, nicht eine Umrechnung im Vertrag.
    return None
