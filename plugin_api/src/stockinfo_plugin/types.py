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
from datetime import date, datetime
from enum import Enum
from typing import Literal

API_VERSION = 2
"""Version des Vertrags. Ein Plugin nennt die Version, gegen die es gebaut ist.

**2 seit T-31:** Die Identität ist eine getaggte Union, und `Resolved`,
`QuoteRequest` und `DailyRequest` tragen sie als Feld `identity` statt als
`ticker`/`mic`. Das bricht jedes Plugin nach Vertrag 1 — deshalb die neue Zahl
und nicht ein zusätzliches Feld mit Vorgabewert.
"""

Cost = Literal["free", "metered", "paid"]
"""Was eine Anfrage kostet — steuert die Reihenfolge in der Kette."""


# ─── Identität ────────────────────────────────────────────────────────────────
#
# Nicht jedes Papier wird an einer Börse gehandelt. Eine Kryptowährung hat
# keinen MIC nach ISO 10383, und eine OTC-Anleihe hat keinen Ticker — für beide
# wäre jeder Wert in diesen Feldern erfunden.
#
# Die Union macht die Form **ausdrücklich**, statt sie aus der Feldbelegung
# raten zu lassen: Ein Plugin sagt, welche Identität es liefert, und der Host
# verzweigt über `kind`. Das ist die T-21-Lehre in ihrer allgemeinen Form —
# kein Wert, der etwas anderes vorgibt zu sein.


@dataclass(frozen=True)
class ListedIdentity:
    """Ein Listing an einem echten Handelsplatz: Ticker **und** MIC.

    Die Form für Aktien, ETFs, ETCs und börsengehandelte Anleihen. Beide Werte
    zusammen — ein Ticker ohne Handelsplatz ist mehrdeutig (`RY` gibt es in
    Toronto und in New York, zu verschiedenen Kursen in verschiedenen
    Währungen), ein Handelsplatz ohne Ticker sagt gar nichts.

    Attributes:
        ticker: Kanonischer Ticker, ohne Börsensuffix.
        mic: Börse als MIC (ISO 10383), z.B. ``XETR``.
        isin: Falls bekannt. Nicht jeder Markt vergibt eine.
    """

    ticker: str
    mic: str
    isin: str | None = None
    kind: Literal["listed"] = "listed"


@dataclass(frozen=True)
class PairIdentity:
    """Ein Währungspaar: Basiswert und Quote-Währung.

    Die Form für natives Krypto. ``BTC`` allein hat keinen Preis — einen Preis
    gibt es nur relativ zu einer Währung, und ``BTC-EUR`` ist ein anderes
    Instrument als ``BTC-USD``. Die Rolle, die bei der Aktie der Handelsplatz
    spielt (*wo gilt dieser Preis?*), spielt hier die Quote-Währung.

    Ein Krypto-**ETP** gehört nicht hierher: Es hat ISIN und MIC und ist
    `ListedIdentity`.

    Attributes:
        base: Basiswert, z.B. ``BTC``.
        quote_currency: Quote-Währung als ISO-4217-Code, z.B. ``EUR``.
    """

    base: str
    quote_currency: str
    kind: Literal["pair"] = "pair"


@dataclass(frozen=True)
class IsinOnlyIdentity:
    """Nur eine ISIN — die Form für OTC-Anleihen.

    Es gibt keinen Handelsplatz und keinen Ticker; die ISIN *ist* die
    Identität. Ein Preis kommt für diese Form nicht von jeder Quelle, und wo
    keine liefert, ist die ehrliche Antwort `NotFound` und kein geschätzter
    Kurs.

    Attributes:
        isin: Die ISIN, mit gültiger Prüfziffer.
    """

    isin: str
    kind: Literal["isin_only"] = "isin_only"


Identity = ListedIdentity | PairIdentity | IsinOnlyIdentity
"""Welche Identitätsformen es gibt — unterschieden über ``kind``.

**Bewusst ohne `ticker`/`mic`-Properties auf der Union.** Sie müssten für ein
Paar etwas erfinden, und ein erfundener Wert, der wie ein echter aussieht, ist
genau der Fehler, den diese Union beseitigt. Wer Ticker und MIC braucht, prüft
vorher die Form.
"""


def isin_of(identity: Identity) -> str | None:
    """Die ISIN dieser Identität, falls die Form eine hat.

    Der Unterschied zu einer `isin`-Property auf der Union: Hier wird nichts
    erfunden. Ein Währungspaar **hat** keine ISIN, und ``None`` sagt genau
    das — anders als ein Ticker, den man für ein Paar nur erfinden könnte.

    Args:
        identity: Die Identität.

    Returns:
        Die ISIN, oder ``None`` bei einem Paar und bei einem Listing ohne.
    """
    if isinstance(identity, ListedIdentity):
        return identity.isin
    if isinstance(identity, IsinOnlyIdentity):
        return identity.isin
    return None


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
        currency: Handelswährung, falls sie schon bekannt ist.

            **Neu mit T-23, und der Anlass ist gemessen.** Eine Metadatenquelle
            entscheidet ihre Zuständigkeit ohne ISIN anhand des Listings: Ein
            Papier in CAD an einer kanadischen Börse steht nicht bei einem
            europäischen Fondsanbieter. Ohne dieses Feld ließ sich die Regel im
            Vertrag nicht ausdrücken — die App hatte sie, ein fremdes Plugin
            nicht.

            Ein Feld mit Vorgabewert bricht kein bestehendes Plugin; die
            `api_version` bleibt deshalb unverändert. Wer es nicht braucht,
            merkt nichts davon.
    """

    isin: str | None = None
    symbol: str | None = None
    preferred_mic: str = "XETR"
    currency: str | None = None


# ─── Antworten ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Resolved:
    """Treffer: So ist das Papier identifiziert.

    Bewusst **kein** fertiges Anbieter-Symbol, sondern die Identität in ihrer
    Form. Wie daraus ``EUNL.DE`` (Yahoo) oder ``EUNL.XETRA`` (EODHD) wird, ist
    Sache dessen, der die Kurse holt — ein Resolver muss keine fremden
    Symbol-Konventionen kennen.

    ``currency`` fehlt mit Absicht: Die Handelswährung stammt immer aus dem
    Live-Kurs, nie aus der Auflösung. Bei `PairIdentity` ist ``quote_currency``
    etwas anderes — sie gehört zur Identität und sagt, *worin* der Preis
    notiert, nicht *wieviel* er ist.

    Attributes:
        identity: Die Identität in ihrer Form. **Seit `API_VERSION` 2** statt
            der Felder ``ticker``/``mic``, die nur die `listed`-Form abdeckten.
        name: Anzeigename, falls die Quelle ihn kennt.
        instrument_type: Gattung, falls die Quelle sie kennt — der Katalog
            steht in T-38.
    """

    identity: Identity
    name: str | None = None
    instrument_type: str | None = None


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


@dataclass(frozen=True)
class Unsupported:
    """Erkannt — aber nicht von dieser Quelle geführt.

    **Die vierte Antwort, und sie hat einen gemessenen Anlass** (T-31, Matrix
    `#6`). Yahoo kennt ``^GDAXI`` und meldet ``INDEX``. Ohne diesen Typ konnte
    die Quelle diesen Befund nicht aussprechen: `Resolved` verlangt eine
    Identität, und ein Index trägt keine der drei Formen — kein kanonisches
    Listing, kein Paar, keine ISIN. Übrig blieb `NotFound`, also „kenne ich
    nicht" über ein Papier, das die Quelle gerade erkannt hatte. Der Benutzer
    las am Ende „das Symbol nennt keinen Handelsplatz": richtig beobachtet und
    am Grund vorbei.

    **Der Unterschied zu den drei anderen** ist die Richtung der Aussage.
    `NotResponsible`, `NotFound` und `Unavailable` sagen etwas über die
    *Quelle* — sie ist nicht gefragt, hat nichts gefunden, konnte nicht
    nachsehen. `Unsupported` sagt etwas über das *Papier*: Es gibt es, es ist
    von dieser Art, und diese Art bedient die Quelle nicht.

    **Die Kette geht trotzdem weiter.** „Ich führe keine Anleihen" heißt nicht
    „niemand führt Anleihen"; eine spätere Quelle darf dasselbe Papier
    auflösen und gewinnt. Bleibt es bei der Ablehnung, ist die Gesamtantwort
    aber diese hier und nicht `NotFound` — der Host kann dem Benutzer damit
    den wirklichen Grund nennen.

    Attributes:
        instrument_type: Die erkannte Gattung, kleingeschrieben. Pflicht: Ohne
            sie wäre die Antwort nur ein `NotFound` mit anderem Namen.
        detail: Optionaler Zusatz für Protokoll und Fehlermeldung.
    """

    instrument_type: str
    detail: str = ""


Resolution = Resolved | NotResponsible | NotFound | Unavailable | Unsupported
"""Was ein Resolver antworten kann."""


# ─── Kurs, Historie, Devisen ──────────────────────────────────────────────────
#
# Die drei Rollen, die bis T-27a fehlten. Sie teilen sich drei Entscheidungen,
# und jede hat einen gemessenen Anlass in dieser App:
#
# * **Die Anfrage nennt Ticker und MIC, nicht ein fertiges Symbol.** Wie daraus
#   `EUNL.DE` oder `EUNL.XETRA` wird, weiß nur die Quelle selbst — sie kennt
#   ihre eigene Konvention, und keine andere muss sie kennen.
# * **Die Währung ist Pflicht, nicht optional.** Ein Kurs ohne Währung ist eine
#   Zahl; als solche wurde er in dieser App schon einmal mit einem Betrag in
#   einer anderen Währung verrechnet.
# * **Zeitpunkte tragen eine Zone.** `17:30` ist in Toronto ein anderer
#   Augenblick als in Frankfurt, und hinterher ist die Angabe nicht mehr
#   rekonstruierbar.


@dataclass(frozen=True)
class QuoteRequest:
    """Die Frage an eine Kursquelle: Was kostet dieses Papier gerade?

    **Seit `API_VERSION` 2 trägt die Anfrage die Identität als Union.** Vorher
    standen hier `ticker` und `mic` als Pflichtfelder, und damit ließ sich ein
    Papier ohne Handelsplatz zwar auflösen, aber nicht bepreisen — für eine
    Coin und eine OTC-Anleihe war die Kursfrage schlicht nicht formulierbar.

    Ein eigenes `isin`-Feld gibt es nicht mehr: Die ISIN steckt in
    `ListedIdentity` und `IsinOnlyIdentity`, und ein zweites Feld daneben wäre
    eine zweite Wahrheit über dieselbe Sache.

    Attributes:
        identity: Das Papier, in seiner Identitätsform.
    """

    identity: Identity


@dataclass(frozen=True)
class Quote:
    """Ein Kurs — mit Währung und Zeitpunkt, beides Pflicht.

    Attributes:
        price: Der Kurs. Positiv und endlich; ``0`` ist keine Angabe, sondern
            eine fehlende Angabe, die sich als Zahl ausgibt.
        currency: ISO-4217-Code. Wer in Untereinheiten notiert (London in
            Pence), **rechnet vorher um** — siehe `invariants.MINOR_UNIT_CODES`.
        as_of: Wann dieser Kurs galt, mit Zeitzone.
        volume: Tagesvolumen, falls der Anbieter es kennt.
    """

    price: float
    currency: str
    as_of: datetime
    volume: int | None = None


QuoteResult = Quote | NotResponsible | NotFound | Unavailable
"""Was eine Kursquelle antworten kann."""


@dataclass(frozen=True)
class DailyRequest:
    """Die Frage an eine Historienquelle: Wie liefen die Schlusskurse?

    Attributes:
        identity: Das Papier, in seiner Identitätsform. **Seit `API_VERSION`
            2** statt ``ticker``/``mic`` — aus demselben Grund wie bei
            `QuoteRequest`.
        start: Frühester gewünschter Tag, einschließlich. ``None`` heißt „so
            weit zurück, wie du hast".
        end: Spätester gewünschter Tag, einschließlich. ``None`` heißt „bis
            heute".
    """

    identity: Identity
    start: date | None = None
    end: date | None = None


@dataclass(frozen=True)
class DailyBar:
    """Ein Handelstag: Datum und Schlusskurs.

    Bewusst nur diese zwei Werte. Eröffnung, Hoch und Tief braucht diese App
    nicht, und ein Vertrag, der sie verlangt, schlösse jede Quelle aus, die nur
    Schlusskurse führt — das sind gerade die einfachen, kostenlosen.
    """

    day: date
    close: float


@dataclass(frozen=True)
class DailySeries:
    """Eine Reihe von Handelstagen, mit Währung und Bereinigungsstand.

    ``currency`` und ``adjusted`` stehen an der **Reihe**, nicht am einzelnen
    Tag: Beides gilt für alle Punkte gemeinsam, und sie an jedem Tag zu
    wiederholen lüde dazu ein, sie innerhalb einer Reihe wechseln zu lassen.

    Attributes:
        bars: Die Tage, **streng aufsteigend** und ohne Duplikate. Zwei
            Einträge für denselben Tag entstehen still, wenn ein Anbieter zwei
            sich überlappende Seiten liefert.
        currency: ISO-4217-Code der Schlusskurse.
        adjusted: Ob die Kurse um Splits und Ausschüttungen bereinigt sind.
            **Deklariert, nicht geraten** — dieselbe Reihe unterscheidet sich
            je nach Antwort um zweistellige Prozentwerte, und welche Variante
            ein Anbieter liefert, steht nirgends im Zahlenmaterial.
    """

    bars: tuple[DailyBar, ...]
    currency: str
    adjusted: bool


DailyResult = DailySeries | NotResponsible | NotFound | Unavailable
"""Was eine Historienquelle antworten kann."""


@dataclass(frozen=True)
class FxRequest:
    """Die Frage an eine Devisenquelle: Was ist eine Einheit ``base`` in ``quote``?

    Attributes:
        base: Ausgangswährung (ISO 4217).
        quote: Zielwährung (ISO 4217).
    """

    base: str
    quote: str


@dataclass(frozen=True)
class FxRate:
    """Ein Wechselkurs: eine Einheit ``base`` kostet ``rate`` in ``quote``.

    ``base`` und ``quote`` stehen **auch in der Antwort**, obwohl sie schon in
    der Anfrage stehen. Der Grund ist praktisch: Ein gespeicherter oder
    weitergereichter Kurs ohne sein Paar ist eine Zahl ohne Bedeutung, und die
    Richtung zu verwechseln ist der häufigste Fehler mit Devisenkursen
    überhaupt — ``0.92`` und ``1.087`` sehen beide plausibel aus.

    Attributes:
        base: Ausgangswährung.
        quote: Zielwährung.
        rate: Der Kurs, positiv und endlich. Bei ``base == quote`` **genau**
            ``1.0``: Eine Quelle, die für EUR→EUR ``0.9998`` meldet, rechnet
            über einen Umweg und ist an dieser Stelle nicht vertrauenswürdig.
        as_of: Wann dieser Kurs galt, mit Zeitzone.
    """

    base: str
    quote: str
    rate: float
    as_of: datetime


FxResult = FxRate | NotResponsible | NotFound | Unavailable
"""Was eine Devisenquelle antworten kann."""


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
    currency: str | None = None
    """Währung bei ``Unit.ABSOLUTE`` — ohne sie ist ein Betrag bedeutungslos.

    Ein Fondsvolumen von 2.289.978.572.800 sagt nichts, solange nicht dabeisteht,
    ob es USD oder CAD sind. Bei allen anderen Einheiten bleibt das Feld leer.
    """


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
        unit: Einheit, in der **diese Quelle** liefert. Die kanonische
            Zieleinheit kennt nur die App; hier steht die Quellenseite.
        plausible: Erlaubter Wertebereich, **in der Einheit dieser
            Deklaration** — also vor der Umrechnung. Eine Quelle kennt ihren
            eigenen Wertebereich; was danach in der kanonischen Einheit noch
            plausibel ist, prüft die App ein zweites Mal gegen ihren Katalog.
            Zwei Prüfungen, jede dort, wo das Wissen sitzt.

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
            value: Der zu prüfende Wert, in der Einheit dieser Deklaration
                (`unit`) — also so, wie die Quelle ihn liefert.

        Returns:
            ``True``, wenn kein Bereich gesetzt ist, der Wert keine Zahl ist
            (dann greift die Prüfung nicht) oder er innerhalb liegt.

        **Ohne `float()` — Befund aus Runde 3, zweite Fundstelle.** Die
        Umwandlung war überflüssig: Python vergleicht `int` und `float` exakt,
        ohne eines von beiden umzurechnen. Sie war zugleich gefährlich, denn
        ein beliebig großer Integer wie ``10**10000`` lässt sich gar nicht in
        einen `float` wandeln und beendete die Prüfung mit `OverflowError` —
        mitten im Contract-Lauf, für den `is_plausible` seit Runde 2 aufgerufen
        wird.
        """
        if self.plausible is None or not isinstance(value, (int, float)):
            return True
        low, high = self.plausible
        return low <= value <= high


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
