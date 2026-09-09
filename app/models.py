"""Pydantic-Response-Modelle der API."""

from collections.abc import Callable
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

from app.detail_models import DetailDefinition, DetailValue


def always_present(*fields: str) -> Callable[[dict[str, Any]], None]:
    """Erklärt Felder im **veröffentlichten Schema** für immer vorhanden.

    Pydantics `required`-Liste beantwortet die Frage der *Eingabe*: Muss der
    Aufrufer das Feld mitgeben? FastAPI veröffentlicht dieselbe Liste aber als
    Zusage über die **Antwort** — und dort heißt „nicht required", ein
    generierter Konsument müsse mit einem fehlenden Feld rechnen.

    Für ein Feld mit Vorgabewert ist das falsch: Es wird **immer**
    serialisiert. Genau diese Lücke hat Codex in Runde 42 gefunden, und meine
    erste Antwort darauf — „die `required`-Liste sagt bei Antwortmodellen
    nichts aus" — war sachlich verkehrt. Sie sagt etwas; sie sagte nur das
    Falsche.

    Der Vorgabewert bleibt trotzdem stehen: Er erspart vierzig
    Testkonstruktionen die Wiederholung zweier Transportflags, über die sie
    nichts aussagen wollen. Was der Konsument sieht, ist damit richtig, und was
    der Erzeuger schreibt, bleibt knapp.

    **Nicht für Nullability.** Ob ein Wert `null` sein darf, ist eine Aussage
    über die Daten und wird nie über das Schema geglättet — dort ändert sich
    der Typ, nicht die Beschreibung.

    Args:
        fields: Die Feldnamen, die in `required` gehören.

    Returns:
        Ein `json_schema_extra`-Callable für `ConfigDict`.
    """

    def extend_required(schema: dict[str, Any]) -> None:
        schema["required"] = sorted(set(schema.get("required", ())) | set(fields))

    return extend_required


class HealthResponse(BaseModel):
    """Antwort des Liveness-Endpoints — „läuft der Prozess?", mehr nicht.

    Bewusst ohne Aussage über Datenbank oder Betriebsbereitschaft; die
    beantworten `OperationalResponse` und `ReadinessResponse`.
    """

    status: str = "ok"
    version: str


class ReadinessResponse(BaseModel):
    """Antwort des Readiness-Endpoints.

    Getrennt von `HealthResponse`, weil beide verschiedene Fragen beantworten:
    „Läuft der Prozess noch?" (billig, ohne Abhängigkeiten) gegen
    „Ist der normale Fachbetrieb freigegeben?" (prüft die Datenbank **und**
    den Migrationszustand).

    **`status` ist ein `Literal`, kein freier `str`** (T-21 Teil 3, `#2b6b`).
    Ein Konsument muss die Gründe auseinanderhalten können; bei einem freien
    String wäre ein neuer Wert nicht im Vertrag sichtbar und ein Tippfehler
    nicht prüfbar.

    | Lage | Status | `status` |
    |---|---|---|
    | DB nicht erreichbar | `503` | `degraded` |
    | Umzug ausstehend oder läuft | `503` | `migration_pending` |
    | Umzug durch, Betrieb läuft an | `503` | `starting` |
    | Umzug durch, Start gescheitert | `503` | `degraded` |
    | Normalbetrieb | `200` | `ok` |

    **`starting` kam in Runde 32 dazu.** Ohne diese Zeile war der Zustand
    zwischen festgeschriebenem Umzug und zurückgekehrtem Scheduler-Start als
    `ok` beobachtbar — bei einem hängenden Start unbegrenzt lange. Dass ein
    gescheiterter Start dieselbe Kennung `degraded` trägt wie die
    unerreichbare Datenbank, ist Absicht: Beide sagen „hier ist etwas kaputt",
    und der Unterschied steht in `database`.
    """

    status: Literal["ok", "degraded", "migration_pending", "starting"]
    version: str
    database: str = Field(description="ok | error")


class OperationalResponse(BaseModel):
    """Kann der Prozess seine **derzeitige** Aufgabe erfüllen?

    Die dritte Frage neben `/health` und `/ready`, und der Endpunkt, an dem
    seit T-21 Teil 3 der Docker-`HEALTHCHECK` hängt. Der Unterschied zu
    `/ready` ist der ganze Zweck: Während eines ausstehenden Umzugs weist der
    Guard jeden Fachrequest ab — `/ready` sagt dann ehrlich `503`, denn der
    normale Betrieb ist nicht freigegeben. Der Prozess ist deshalb aber nicht
    kaputt: Er tut genau das, was er tun soll, nämlich auf die Bestätigung
    warten.

    Ein Healthcheck, der in dieser Lage `unhealthy` meldete, würde einen
    Fehler behaupten, wo eine Rückfrage läuft.

    | Lage | Status | `mode` |
    |---|---|---|
    | Umzug ausstehend oder läuft, DB erreichbar | `200` | `migration_pending` |
    | Umzug durch, Betrieb läuft an | `200` | `starting` |
    | normaler Betrieb, DB erreichbar | `200` | `serving` |
    | Umzug durch, Betriebsstart gescheitert | `503` | `degraded` |
    | DB nicht erreichbar | `503` | `degraded` |

    **`503` heißt hier „kaputt", nicht „noch nicht fertig".** `starting` steht
    deshalb auf `200`: Ein anlaufender Betrieb ist der Normalpfad, und ein
    `503` machte den `HEALTHCHECK` genau dann kurz `unhealthy`, wenn alles
    funktioniert. `serving` wäre trotzdem falsch — der Refresh läuft noch
    nicht, und ein hängender Start bliebe unter diesem Wort unsichtbar.
    """

    mode: Literal["serving", "migration_pending", "degraded", "starting"]
    version: str


class RejectedInstrument(BaseModel):
    """Ein Papier, das den gültigen Bestand verlässt oder verlassen hat.

    Dasselbe Modell für **Vorschau und Bericht**, und das mit Absicht: Was der
    Benutzer vorher sieht, muss er hinterher wiedererkennen. Zwei Modelle
    liefen beim ersten zusätzlichen Feld auseinander, und ausgerechnet an
    dieser Stelle wäre der Unterschied teuer — er beträfe die Liste, auf deren
    Grundlage jemand einer Löschung zustimmt.

    `reason` ist eine **stabile Kennung**, kein Satz. Der Text gehört ins UI
    und muss in DE und EN vorliegen; wer darauf reagiert, prüft diesen Wert.
    """

    symbol: str
    isin: str | None = None
    name: str | None = None
    exchange: str | None = None
    type: str | None = None
    currency: str | None = None
    reason: str = Field(description="stabile Kennung, siehe app/migration.py")
    quotes: int = Field(description="Intraday-Kurspunkte, die entfallen")
    daily_closes: int = Field(description="Tagesschlusskurse, die entfallen")


class MigrationPreview(BaseModel):
    """Was der bestätigte Umzug tun **würde** — Phase 1.

    `migrating` und `unchanged` stehen neben den Ablehnungen, damit die Liste
    als vollständige Bilanz lesbar ist. Ohne sie könnte der Benutzer nicht
    sehen, ob die genannten Zeilen *alle* betroffenen sind — und genau das
    muss er wissen, bevor er zustimmt.
    """

    pending: bool
    migrating: int
    unchanged: int
    rejected: list[RejectedInstrument]
    lost_quotes: int
    lost_daily_closes: int


class MigrationReport(BaseModel):
    """Was tatsächlich geschehen ist — abrufbar auch später noch.

    Der Bericht überlebt die gelöschten Zeilen; das ist sein Zweck. Ohne ihn
    stünde der Benutzer vor einem Bestand, aus dem etwas fehlt, ohne zu
    erfahren, was und warum.
    """

    completed: bool
    rejected: list[RejectedInstrument]


class QuotePoint(BaseModel):
    """Ein einzelner Kurspunkt der Zeitreihe."""

    price: float
    quote_time: str
    volume: int | None = None
    # Pflicht und nicht nullable — das Artefakt sagt sie seit T-24 zu, und ein
    # Kurspunkt ohne Währung ist nicht verwertbar. `_to_points` wirft dafür
    # bereits; das Schema sagt es jetzt auch.
    currency: str
    fetched_at: str


class DailyPoint(BaseModel):
    """Ein Tages-Schlusskurs (EOD) der Langfrist-Historie."""

    date: str
    close: float
    # Siehe `QuotePoint.currency` — dieselbe Zusage, derselbe Grund.
    currency: str


class ListedIdentityOut(BaseModel):
    """Ein Listing an einem echten Handelsplatz — Ticker und MIC."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["listed"] = "listed"
    ticker: str = Field(description="Kanonischer Ticker")
    mic: str = Field(description="ISO-10383-MIC des Handelsplatzes")
    isin: str | None = Field(default=None, description="ISIN, falls bekannt")


class PairIdentityOut(BaseModel):
    """Ein Währungspaar — die Form für natives Krypto."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["pair"] = "pair"
    base: str = Field(description="Basiswert, z.B. BTC")
    quote_currency: str = Field(description="Quote-Währung, ISO 4217")


class IsinOnlyIdentityOut(BaseModel):
    """Nur eine ISIN — die Form für OTC-Anleihen ohne Handelsplatz."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["isin_only"] = "isin_only"
    isin: str = Field(description="Die ISIN; hier ist sie die ganze Identität")


IdentityOut = Annotated[
    ListedIdentityOut | PairIdentityOut | IsinOnlyIdentityOut,
    Field(discriminator="kind"),
]
"""Die Identität am REST-Rand — diskriminiert über ``kind``.

Ein Konsument liest zuerst `kind` und weiß danach, welche Felder es gibt.
Ohne den Diskriminator müsste er aus der Feldbelegung schließen, und genau
dieses Raten ist der Zustand, den T-31 beendet.
"""

# Die Identitätsspalten der Instrumententabelle, in einer Aufzählung. Sie steht
# hier und nicht im Repository, weil beide Richtungen — hinein und heraus —
# dieselbe Menge meinen; zwei Listen liefen beim ersten Zusatzfeld auseinander.
IDENTITY_COLUMNS = ("kind", "ticker", "mic", "base", "quote_currency", "isin")


def identity_columns(identity: IdentityOut) -> dict[str, str | None]:
    """Die Identität als **vollständige** Spaltenbelegung.

    Vollständig heißt: Jede der sechs Spalten kommt vor, die nicht zur Form
    gehörenden mit ``None``. Das ist keine Umständlichkeit, sondern die
    Bedingung des `CHECK` — er verlangt je Form ihre Felder *und schließt die
    der anderen aus*. Eine Belegung, die nur die eigenen Felder setzt, ließe
    beim Wechsel der Form die alten stehen und verletzte ihn.

    Args:
        identity: Die Identität in ihrer Form.

    Returns:
        Spaltenname → Wert, für alle sechs Identitätsspalten.
    """
    columns: dict[str, str | None] = dict.fromkeys(IDENTITY_COLUMNS)
    columns["kind"] = identity.kind
    if isinstance(identity, ListedIdentityOut):
        columns["ticker"] = identity.ticker
        columns["mic"] = identity.mic
        columns["isin"] = identity.isin
    elif isinstance(identity, PairIdentityOut):
        columns["base"] = identity.base
        columns["quote_currency"] = identity.quote_currency
    else:
        columns["isin"] = identity.isin
    return columns


def identity_from_columns(row: object) -> IdentityOut | None:
    """Die Identität aus flachen Spalten — oder ``None``.

    **Welche Form** entscheidet `app.exchanges.identity_form`; hier wird nur
    noch gebaut. Bis Runde 4 stand die Fallunterscheidung dreimal im Code —
    hier, an `ResolvedInstrument.identity()` und in `identity_from_row()`.
    Drei Fassungen derselben Regel laufen beim ersten Sonderfall auseinander,
    und Codex hat sie zu Recht beanstandet.

    ``None`` heißt „diese Zeile trägt keine vollständige Identität".

    Args:
        row: Eine Instrumentenzeile als Mapping — oder ein Objekt mit
            denselben Feldnamen, etwa ein `ResolvedInstrument`.

    Returns:
        Die passende Identität, oder ``None``.
    """
    # Lokal, weil `app.exchanges` seinerseits nichts aus den Modellen braucht
    # und ein Modulimport in beide Richtungen den Kreis schlösse.
    from app.exchanges import identity_form

    read = (
        row.get
        if hasattr(row, "get")
        else (
            (lambda key: row[key])
            if hasattr(row, "keys")
            else (lambda key: getattr(row, key, None))
        )
    )
    form = identity_form(row)
    if form == "pair":
        return PairIdentityOut(base=read("base"), quote_currency=read("quote_currency"))
    if form == "isin_only":
        return IsinOnlyIdentityOut(isin=read("isin"))
    if form == "listed":
        return ListedIdentityOut(
            ticker=read("ticker"), mic=read("mic"), isin=read("isin")
        )
    return None


def with_identity(row: dict) -> dict:
    """Faltet die Identitätsspalten einer Zeile zu einem `identity`-Feld.

    Die Datenbank führt die Union flach, die öffentliche Form führt **ein**
    Feld. Diese Funktion ist die Naht dazwischen, und sie steht neben den
    Modellen und nicht in jedem Router: Sonst entstünde die Faltung an jeder
    Ausgabestelle neu und ließe beim ersten Zusatzfeld eine davon zurück.

    Die sechs flachen Spalten werden dabei **entfernt**. Sie daneben stehen zu
    lassen wäre die zweite Wahrheit, die T-31 gerade beseitigt.

    Args:
        row: Eine Instrumentenzeile mit den flachen Identitätsspalten.

    Returns:
        Dieselbe Zeile mit `identity` statt der sechs Spalten. Trägt die Zeile
        keine vollständige Form, fehlt `identity` — die Modellprüfung meldet
        das dann als das, was es ist, statt eine halbe Identität auszuliefern.
    """
    folded = {key: value for key, value in row.items() if key not in IDENTITY_COLUMNS}
    identity = identity_from_columns(row)
    if identity is not None:
        folded["identity"] = identity
    return folded


def identity_where(identity: IdentityOut) -> tuple[str, tuple]:
    """Die `WHERE`-Bedingung, die genau diese Identität trifft.

    Je Form eine andere, und je Form liegt ein eigener partieller Unique-Index
    darauf. Eine gemeinsame Bedingung über alle sechs Spalten gäbe es zwar,
    aber sie könnte keinen Index nutzen und träfe bei ``NULL`` ohnehin nichts —
    SQLite hält zwei ``NULL`` nie für gleich.

    Args:
        identity: Die gesuchte Identität.

    Returns:
        Die Bedingung und ihre Parameter, für ein ``SELECT … WHERE``.
    """
    if isinstance(identity, PairIdentityOut):
        return (
            "kind = 'pair' AND base = ? AND quote_currency = ?",
            (identity.base, identity.quote_currency),
        )
    if isinstance(identity, IsinOnlyIdentityOut):
        return ("kind = 'isin_only' AND isin = ?", (identity.isin,))
    return (
        "kind = 'listed' AND ticker = ? AND mic = ?",
        (identity.ticker, identity.mic),
    )


class QuoteResponse(BaseModel):
    """Vollständige Kurs- und Metadaten-Antwort für ein Wertpapier.

    Nicht ermittelbare Felder bleiben ``None`` (z.B. ``ter`` bei Einzelaktien).
    """

    # **`extra="forbid"`, und der Anlass ist gemessen.** Beim Umbau auf die
    # Identitäts-Union blieb an fünf Stellen ein `isin=` neben dem neuen
    # `identity=` stehen. Pydantic verwarf es kommentarlos — die Zeile ging
    # ohne ISIN in die Datenbank, und der Fehler fiel erst zwei Schichten
    # später auf, als ein `get_instrument_by_isin` nichts mehr fand.
    #
    # Das ist genau das Muster, gegen das T-38 geschrieben wird: Ein Wert
    # fehlte, und nichts hat gefragt. Ein unbekannter Feldname ist fast immer
    # ein Tippfehler oder ein Rest aus einem Umbau; beides gehört gemeldet.
    model_config = ConfigDict(
        extra="forbid", json_schema_extra=always_present("cached", "stale")
    )

    details: dict[str, DetailValue] = Field(default_factory=dict)
    detail_readings: dict[str, dict[str, dict]] = Field(default_factory=dict, exclude=True)
    symbol: str
    exchange: str | None = None
    # **Pflicht seit T-38** (Mike, 2026-08-30). Bis dahin war beides
    # optional, und drei Befunde aus dem UI-Lauf waren dieselbe Folge davon:
    # ein leeres Feld, das niemand gemeldet hat. Die Zusage gilt jetzt
    # gegenüber dem Konsumenten — jede Antwort trägt Name und Gattung, oder
    # es gibt keine Antwort.
    #
    # Die Vorabprüfung `require_core_values` fängt das Fehlen eine Ebene
    # früher ab und macht daraus eine typisierte 502 mit Grund. Ohne sie käme
    # hier ein `ValidationError` an — ein 500, der dem Aufrufer nichts sagt.
    name: str
    type: str = Field(description="stock | etf | etc | fund | crypto | bond")
    # Ebenfalls Pflicht und nicht nullable — aus demselben Grund wie `ticker`
    # und `mic` weiter unten. Das Artefakt sagt sie seit T-24 zu, das
    # veröffentlichte Schema führte sie trotzdem als nullable. Ein Preis ohne
    # Währung ist für eine Depotrechnung wertlos, und „wird schon Euro sein"
    # ist bei einem Londoner Listing in Pence falsch.
    currency: str = Field(description="Handelswährung, ISO-4217 (oder 'GBp')")

    # Die kanonische Identität — seit `core_version 2.0.0` zugesagt (T-21
    # Übergabe 3). Sie reiste schon vorher bis zum Repository mit, war am
    # REST-Rand aber ausgeblendet: Ein Feld auszuliefern, das der Vertrag nicht
    # nennt, wäre eine stille Zusage gewesen.
    #
    # **Pflicht, nicht nullable** — und zwar im Modell, nicht nur im Artefakt.
    # Bis Runde 39 stand hier `str | None`, weil `ensure_core_complete` die
    # Pflichtliste ohnehin aus dem Vertrag liest. Das erzeugte aber genau den
    # Widerspruch, den ein Konsument nicht auflösen kann: Das Artefakt sagte
    # „Pflicht", das veröffentlichte OpenAPI-Schema sagte „optional, nullable",
    # und ein generierter Client durfte mit dem Zustand rechnen, den `2.0.0`
    # gerade abschafft. Fehlt die Identität, scheitert die Antwort jetzt
    # **vor** dem Bauen, in `QuoteService._build`.
    #
    # **`listing_id` steht hier bewusst nicht.** Sie entsteht beim Anlegen der
    # Zeile; eine frisch beschaffte Antwort hat noch keine. Sie auf `quote`
    # zuzusagen hieße, der Beschaffung eine Speicher-Identität abzuverlangen,
    # die es zu dem Zeitpunkt nicht gibt. Zugesagt wird sie auf `instrument`,
    # wo die Zeile bereits existiert.
    #
    # **Seit T-31 ein Feld statt zweier** — und `isin` ist mit hineingewandert.
    # `ticker`/`mic` daneben stehen zu lassen „wo sie wahr sind" wäre dieselbe
    # zweite Wahrheit, die der Vertrag bei `QuoteRequest.isin` gerade
    # beseitigt, nur an der teureren Stelle: Ein Konsument müsste raten, ob ein
    # leeres `mic` „gibt es nicht" oder „wurde nicht ermittelt" heißt — und
    # genau diese Unterscheidung ist der Grund für die Union.
    identity: IdentityOut = Field(
        description="Die Identität in ihrer Form — listed, pair oder isin_only"
    )

    price: float
    quote_time: str
    volume: int | None = None

    ter: float | None = None
    provider: str | None = None
    replication: str | None = None
    fund_size: float | None = None
    fund_domicile: str | None = None
    fund_currency: str | None = Field(
        default=None, description="Währung des Fonds — nicht die des Handelsplatzes"
    )
    volatility: float | None = Field(
        default=None, description="1-Jahres-Volatilität in %"
    )
    accumulating: bool | None = Field(
        default=None, description="Thesaurierend (true) vs. ausschüttend (false)"
    )

    source: str | None = None
    cached: bool = False
    stale: bool = False
    fetched_at: str

    metadata_complete: bool = Field(
        default=True,
        exclude=True,
        description=(
            "Weiss diese Antwort ueber die ETF-Extras Bescheid? False heisst: "
            "justETF wurde nicht gefragt oder hat nicht geantwortet."
        ),
    )
    """Sagt dem Repository, ob es die ETF-Extras ueberschreiben darf.

    Ohne diese Unterscheidung sind zwei voellig verschiedene Lagen nicht
    auseinanderzuhalten: „justETF hat geantwortet und das Feld ist leer" und
    „justETF war nicht erreichbar". Das Repository schrieb deshalb beide Male
    ``NULL`` — ein einzelner Ausfall loeschte den ganzen gepflegten
    Metadatenstand.

    ``exclude=True``: Das Flag ist eine interne Absprache zwischen Service und
    Repository und gehoert nicht in die API-Antwort.
    """


OVERRIDE_FIELDS = (
    "ter",
    "volatility",
    "accumulating",
    "provider",
    "replication",
    "fund_size",
    "fund_domicile",
    "fund_currency",
)
"""Kennzahlen, die von Hand nachgetragen werden können.

Eine Quelle für Modell, Repository, Endpoint und Tests — sonst kennt jede
Stelle eine andere Teilmenge. Die Menge ist genau das, was justETFs
`get_etf_overview` beisteuert: Wo die Quelle nichts hat, springt der Mensch ein.
"""


class InstrumentOverrides(BaseModel):
    """Von Hand nachgetragene Kennzahlen.

    ``None`` heißt „nicht gepflegt". Beim Schreiben ist das gleichbedeutend mit
    „löschen": Die Oberfläche schickt immer den vollständigen Satz.
    """

    ter: float | None = Field(default=None, ge=0, le=5, description="TER in %")
    volatility: float | None = Field(
        default=None, ge=0, le=500, description="1-Jahres-Volatilität in %"
    )
    accumulating: bool | None = Field(
        default=None, description="Thesaurierend (true) vs. ausschüttend (false)"
    )
    provider: str | None = Field(
        default=None, max_length=100, description="Fondsanbieter"
    )
    replication: str | None = Field(
        default=None, max_length=100, description="Replikationsart"
    )
    # Obergrenze in Mio. EUR: 2 Bio. — der größte Fonds der Welt liegt bei rund 1,5.
    fund_size: float | None = Field(
        default=None, ge=0, le=2_000_000, description="Fondsvolumen in Mio. EUR"
    )
    fund_domicile: str | None = Field(
        default=None, max_length=100, description="Fondsdomizil"
    )
    fund_currency: str | None = Field(
        default=None,
        pattern=r"^[A-Z]{3}$",
        description="Fondswährung als ISO-4217-Code",
    )


class InstrumentSummary(BaseModel):
    """Ein Instrument mit seinem letzten Kurs — für die DB-Übersicht.

    ``ter``, ``volatility`` und ``accumulating`` sind die **wirksamen** Werte:
    Was die Quelle liefert, gewinnt; ein manueller Wert füllt nur Lücken. Damit
    die Oberfläche das erklären kann, kommen die manuellen Werte zusätzlich roh
    mit — und zwei Listen sagen, wo sie gerade greifen und wo sie verdeckt sind.
    """

    model_config = ConfigDict(
        json_schema_extra=always_present(
            "history_count", "manual_fields", "shadowed_fields"
        )
    )

    details: dict[str, DetailValue] = Field(default_factory=dict)
    symbol: str
    # Die kanonische Identität. **Pflicht, nicht nullable** — eine gespeicherte
    # Zeile ohne vollständige Identität kann es seit dem `CHECK` nicht geben,
    # und `nullable` wäre die Zusage an Konsumenten, mit einem Zustand zu
    # rechnen, den es nicht gibt.
    #
    # **Seit T-31 ein Feld statt dreier.** Welche Felder darin stehen, sagt
    # `kind`; siehe `QuoteResponse.identity` für die Begründung.
    identity: IdentityOut = Field(
        description="Die Identität in ihrer Form — listed, pair oder isin_only"
    )
    # **Kein Teil der Identität**, sondern der Schlüssel der gespeicherten
    # Zeile: opak, dauerhaft, unabhängig von der Form. Deshalb steht sie
    # daneben und nicht darin.
    listing_id: str = Field(
        description="Opake, dauerhafte Kennung des Listings — nie zerlegen"
    )
    exchange: str | None = None
    # **Dieselbe Zusage wie in `QuoteResponse`** (Mike, 2026-08-30). Eine
    # Bestandsliste, in der Zeilen namenlos sind, war der sichtbarste Teil des
    # Befunds aus dem UI-Lauf — und der Grund, warum dieses Ticket existiert.
    #
    # **Ein Unterschied bleibt und ist bekannt:** Für den Kursweg fängt
    # `require_core_values` ein fehlendes Feld ab und macht daraus eine 502 mit
    # Grund. Für die Liste gibt es dieses Gegenstück nicht. Neu entstehende
    # Zeilen tragen beide Felder, weil keine Auflösung mehr ohne sie
    # durchkommt; für Altbestand gilt Mikes Entscheidung aus T-31, die
    # Entwicklungsdatenbank zu verwerfen.
    name: str
    type: str
    currency: str | None = None
    provider: str | None = None
    ter: float | None = None
    replication: str | None = None
    fund_size: float | None = None
    fund_domicile: str | None = None
    fund_currency: str | None = None
    volatility: float | None = None
    accumulating: bool | None = None
    source: str | None = Field(
        default=None, description="Herkunft der Metadaten: yfinance | yfinance+justetf"
    )
    meta_fetched_at: str | None = None
    latest_price: float | None = None
    latest_quote_time: str | None = None
    latest_currency: str | None = None
    latest_fetched_at: str | None = None
    history_count: int = 0

    manual_ter: float | None = None
    manual_volatility: float | None = None
    manual_accumulating: bool | None = None
    manual_provider: str | None = None
    manual_replication: str | None = None
    manual_fund_size: float | None = None
    manual_fund_domicile: str | None = None
    manual_fund_currency: str | None = None
    manual_fields: list[str] = Field(
        default_factory=list, description="Kennzahlen, die gerade von Hand kommen"
    )
    shadowed_fields: list[str] = Field(
        default_factory=list,
        description="Kennzahlen mit manuellem Wert, den die Quelle gerade verdeckt",
    )


class FieldSpec(BaseModel):
    """Ein Feld des Core-Vertrags samt Art, Pflicht und Bedeutung."""

    name: str
    kind: str = Field(
        description="string | number | integer | boolean | array | object"
    )
    required: bool
    meaning: str


class EndpointSpec(BaseModel):
    """Ein öffentlicher Endpunkt samt Methode und zulässigen Query-Namen."""

    path: str
    method: str
    query: list[str] = Field(default_factory=list)


class FieldsResponse(BaseModel):
    """Antwort von ``GET /fields`` — der Vertrag zur Laufzeit.

    Nach Antworttyp gegliedert, nicht flach: Ein Array mit `price` und
    `currency` sagt nicht, in welcher Antwort sie Pflicht sind, und wäre damit
    ungenauer als das OpenAPI-Dokument.

    Zwei Nummern, zwei Ebenen: `core_version` folgt SemVer über den
    geschlossenen Core, `details_version` zählt die offene Detailmenge
    (siehe T-26). Ein Konsument mit gecachter Feldliste erkennt an ihnen, dass
    er neu holen muss, ohne den Inhalt zu vergleichen.
    """

    core_version: str = Field(description="SemVer des geschlossenen Core")
    core: dict[str, list[FieldSpec]]
    endpoints: dict[str, list[EndpointSpec]]
    generation_id: str = Field(description="Stabile Generation des Detailkatalogs")
    details_version: int = Field(description="Zähler der offenen Detailmenge")
    details: list[DetailDefinition] = Field(default_factory=list)
    plugin_contract: dict[str, list[FieldSpec]] = Field(
        default_factory=dict,
        description=(
            "Die Pflicht- und Optionalfelder des **Plugin**-Vertrags (T-38). "
            "Ein Plugin-Autor liest hier, was er liefern muss, statt den "
            "Quelltext zu lesen — und die Angabe ist aus den Typen abgeleitet, "
            "nicht danebengepflegt."
        ),
    )


class EnvInfo(BaseModel):
    """Sichtbarer Ausschnitt der Konfiguration (Secrets nur als Booleans)."""

    version: str
    database_path: str
    cache_ttl_hours: int
    refresh_interval_hours: int
    metadata_ttl_days: int
    default_exchange: str
    strict_exchange: bool
    host: str
    port: int
    openfigi_key_set: bool
    extraetf_etf_url: str = ""
    extraetf_stock_url: str = ""
    yahoo_url: str = ""


class CoreProvenance(BaseModel):
    """Der Eintrag stammt aus dem Core — und trägt deshalb **keine** Plugin-ID.

    `extra="forbid"` ist hier die halbe Aussage: Ohne das Verbot nähme das
    Modell ein mitgeschicktes ``id`` stillschweigend an und ließe es unter den
    Tisch fallen. Ein Konsument, der ``{"kind": "core", "id": "demo"}``
    schickt, meint etwas — und muss erfahren, dass es diesen Zustand nicht
    gibt.
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["core"] = "core"


class PluginProvenance(BaseModel):
    """Der Eintrag stammt aus einem Plugin — und nennt **welchem**.

    Die ID ist Pflicht und nichtleer. „Von irgendeinem Plugin" ist für T-30
    keine verwertbare Herkunft: Beim Merge entscheidet sie über Vorrang,
    Kollision und Invalidierung.
    """

    kind: Literal["plugin"]
    id: str = Field(min_length=1)


Provenance = Annotated[CoreProvenance | PluginProvenance, Field(discriminator="kind")]
"""Woher ein Katalogeintrag stammt — Core **oder** ein benanntes Plugin.

Eine diskriminierte Union statt eines Modells mit zwei optionalen Feldern:
Jenes ließ ``{"kind": "plugin", "id": null}`` und ``{"kind": "core",
"id": "demo"}`` durch, also genau die beiden Kombinationen, die T-30
auseinanderhalten muss. Der Typ kann sie jetzt nicht mehr ausdrücken.
"""


class ExchangeSource(BaseModel):
    """Eine konfigurierte Quelle in einer Listing-Rolle."""

    source: str
    role: str
    usable: bool


class ExchangeSupport(ExchangeSource):
    """Deklarierte Marktabdeckung oder bestandsabhängige Unterstützung."""

    scope: Literal["market", "inventory"]


class ExchangeEntry(BaseModel):
    """Ein **Handelsplatz** im Katalog — hat einen echten MIC.

    ``alias`` ist das nackte App-Suffix ohne Punkt — oder ``None`` bei einer
    Börse ohne App-Suffix (etwa die fünf US-Plätze). Neue Plugin-Börsen
    verwenden ihren MIC. Anbieterübersetzungen bleiben im jeweiligen Plugin.
    Die zweite zulässige Eingabeform ist der kanonische MIC selbst.

    ``None`` und nicht ``""``: Abwesenheit ist kein Alias aus null Zeichen.
    Der Leerstring wird deshalb auch **abgelehnt** — sonst gäbe es die
    Abwesenheit zweimal, und jede Vergleichsstelle müsste beide Formen kennen.
    Siehe `ExchangeDef` in `app.exchanges` für den Grund.
    """

    kind: Literal["exchange"] = "exchange"
    mic: str
    alias: Annotated[str, Field(min_length=1)] | None = None
    declared_by: list[str] = Field(default_factory=list)
    support: list[ExchangeSupport] = Field(default_factory=list)
    name: str
    region: str
    currency: str
    provenance: Provenance = CoreProvenance()


CatalogEntry = ExchangeEntry


class FxRate(BaseModel):
    """Ein Wechselkurs: 1 ``base`` = ``rate`` ``quote`` (base=von, quote=nach)."""

    model_config = ConfigDict(json_schema_extra=always_present("cached", "stale"))

    base: str
    quote: str
    rate: float
    quote_time: str
    source: str | None = None
    cached: bool = False
    stale: bool = False
    fetched_at: str


class SourceEntry(BaseModel):
    """Eine Quelle in einer Rolle — mit dem, was der Betreiber wissen muss.

    `configured` ist die Antwort von `is_configured()`: „kann ich arbeiten",
    nicht „ist alles gesetzt". Eine Quelle mit `false` ist **kein Fehler** —
    sie fällt aus der Kette, und genau das soll sichtbar sein, statt dass
    jemand rätselt, warum eine eingetragene Quelle nichts liefert.

    `cost` ist ausdrücklich **Information, keine Sortierregel**. Die Reihenfolge
    bestimmt allein `sources.yaml`; dieser Wert dient der Warnung, damit eine
    kostenpflichtige Quelle nicht unbemerkt vor einer kostenlosen steht.
    """

    data_version: int = Field(default=1, ge=1, description="Vom Plugin deklarierte Datenkompatibilität")
    name: str = Field(description="Kurzname aus der Konfiguration")
    role: str = Field(description="resolvers, etf_meta, quotes, daily oder fx")
    position: int = Field(description="Rang in der Kette, 1-basiert")
    configured: bool = Field(description="Kann diese Quelle arbeiten?")
    reason: str = Field(
        default="",
        description=(
            "Warum sie es nicht kann — leer, wenn sie arbeitet. Ohne diesen "
            "Grund bliebe nur ein `false`, und der Betreiber müsste raten."
        ),
    )
    cost: str = Field(description="free | metered | paid — Anzeige, keine Sortierung")


class SourcesResponse(BaseModel):
    """Welche Quellen in welcher Reihenfolge greifen.

    **Der Beleg dafür, dass die Konfiguration wirkt.** Ohne diesen Weg müsste
    ein Betreiber die Kette aus dem Log oder dem Quelltext erschließen — und
    genau das war der Zustand, den T-22 abschafft.

    `config_path` ist `null`, wenn keine Datei da ist und die Vorgaben gelten.
    Das ist kein Mangel: Eine frische Installation ohne `sources.yaml` ist der
    Normalfall.
    """

    config_path: str | None = Field(
        default=None, description="Gelesene Datei, oder null bei Vorgaben"
    )
    profile: str | None = Field(
        default=None, description="Eingetragenes Profilpaket, sofern eines gilt"
    )
    provenance_warning: str = Field(
        default="",
        description=(
            "Der Bestand stammt aus einer **anderen** Quellenlage als der "
            "laufenden — etwa nach einem erzwungenen Wiederherstellen. Die "
            "Papiere darin können in einer Form vorliegen, die die laufende "
            "Kette nicht bedient; leer, solange beides zusammenpasst"
        ),
    )
    sources: list[SourceEntry]

    model_config = ConfigDict(
        json_schema_extra=always_present("config_path", "profile")
    )


class ExchangesResponse(BaseModel):
    """Konkrete Handelsplätze und die konfigurierte MIC-Präferenz.

    Eine nicht im Katalog geführte Präferenz wird als unknown ausgewiesen.
    """

    default_exchange: str
    default_exchange_kind: Literal["exchange", "unknown"]
    catalog: list[CatalogEntry]
    unspecified_support: list[ExchangeSource] = Field(default_factory=list)


class RefreshResult(BaseModel):
    """Ergebnis eines globalen Refresh-Laufs."""

    total: int
    refreshed: int


class IsinUpdate(BaseModel):
    """Body zum nachträglichen Eintragen einer ISIN."""

    isin: str


class AnalyzeStage(BaseModel):
    """Eine gemessene Quelle in einer Rolle.

    **Rolle und Quelle, nicht ein fester Anbietername.** Vorher hieß das Feld
    `stage` und trug Werte wie `openfigi` oder `justetf` — Namen von Anbietern,
    die eine Instanz gar nicht konfiguriert haben muss. Eine Diagnose, die
    misst, was die App **tut**, kennt nur die Rolle und die Quelle, die in ihr
    steht.

    `skipped` heißt „nicht gefragt": Eine Kaskade hört beim ersten Treffer auf,
    und die dahinterliegenden Quellen haben nichts geantwortet, weil sie nichts
    gefragt wurden. Sie mit `0 ms, ok` zu melden wäre richtig gemessen und
    falsch verstanden.
    """

    role: str = Field(description="resolvers | quotes | daily | etf_meta")
    source: str = Field(description="Name der Quelle aus `sources.yaml`")
    seconds: float
    status: str = Field(description="ok | empty | error | skipped")
    #: Was die Kette gemeldet hat, oder das aufgelöste Symbol. **Freitext**,
    #: möglicherweise in einer Sprache — der Analyzer legt hier nichts Eigenes
    #: mehr hinein, weiter oben entstehender Text bleibt unangetastet.
    detail: str | None = None
    rows: int | None = Field(default=None, description="Zeilen einer Tagesreihe")
    instrument_type: str | None = Field(
        default=None, description="Gattung, die nicht geführt wird"
    )


class AnalyzeResult(BaseModel):
    """Timing-Aufschlüsselung eines Live-Fetch für ein Wertpapier."""

    symbol: str
    isin: str | None = None
    total: float
    stages: list[AnalyzeStage]


class IntakeRequest(BaseModel):
    """Body des Aufnahmewegs — **ein** roher Feldwert.

    Kein `isin`/`symbol`-Verzweigen am Client und kein zweiter Parameter für
    den MIC: Was der Wert bedeutet, entscheidet allein der Core (T-21 Teil 3).
    Ein Dashboard, das die Form selbst klassifizierte, hätte dieselbe Grammatik
    ein zweites Mal — und beide liefen auseinander, sobald ein Plugin weitere
    Formen erlaubt.
    """

    # **Keine `min_length`.** Sie schien harmlos, machte aber ausgerechnet die
    # leere Eingabe zum Sonderfall: `""` lief in FastAPIs untypisiertes `422`,
    # während `" "` den vorgesehenen `400 identifier_empty` bekam — zwei
    # Fehlerformen für denselben Fehler, und die zugesagte Kennung war für den
    # häufigeren der beiden Fälle unerreichbar. Die Leere beantwortet jetzt
    # allein der Service, und zwar in der Form des Fehlervertrags.
    identifier: str = Field(
        max_length=32,
        description="ISIN, TICKER.ALIAS (EUNL.DE) oder TICKER.MIC (EUNL.XETR)",
    )


class ErrorDetail(BaseModel):
    """Ein Fehler als **Kennung**, nicht als Satz.

    Der Text gehört ins UI und muss in DE und EN vorliegen; ein deutscher
    Backendtext in der englischen Oberfläche wäre auch bei sauberem Parsen
    falsch. `params` trägt die Werte, die der übersetzte Satz einsetzt — etwa
    den erkannten Ticker.

    Bewusst **nicht** unter `detail` verschachtelt: FastAPIs Vorgabeform
    `{"detail": …}` zwänge jeden Konsumenten, erst auszupacken, was er dann
    doch typisiert erwartet.
    """

    code: str = Field(description="Stabile Kennung, z.B. unknown_exchange_suffix")
    params: dict[str, str] = Field(
        default_factory=dict, description="Werte für den übersetzten Text"
    )


class ListingCandidate(BaseModel):
    """Ein Listing, das für ein mehrdeutiges Symbol in Frage kommt.

    Der Aufrufer bekommt genug, um selbst zu entscheiden — vor allem die
    `listing_id`, die als einzige eindeutig ist. `symbol` steht bewusst mit
    dabei, obwohl es bei allen Kandidaten gleich ist: Der Rumpf soll auch
    dann lesbar sein, wenn er ohne die Anfrage weitergereicht wird.
    """

    listing_id: str = Field(description="Opake UUID des Listings")
    symbol: str = Field(description="Der mehrdeutige Anzeigename")
    mic: str = Field(description="Echter MIC nach ISO 10383")
    exchange: str | None = Field(default=None, description="Anzeigename der Börse")
    isin: str | None = Field(default=None, description="ISIN, sofern bekannt")

    model_config = ConfigDict(json_schema_extra=always_present("exchange", "isin"))


class AmbiguousSymbolDetail(BaseModel):
    """Der `409`, wenn mehrere Listings dasselbe Symbol tragen.

    **Die Form kommt aus T-24**, nicht aus diesem Ticket:
    `contract/fixtures/quote-409-ambiguous-symbol.json` zeigt `detail` und
    `candidates`, und die Fixture ist von außen benutzbar — StockPortfolio
    liest sie, ohne StockInfo zu starten.

    `code` und `params` kommen additiv dazu, damit dieser `409` dieselbe
    maschinenlesbare Kennung trägt wie jede andere Ablehnung: Ein deutscher
    Backendtext in der englischen Oberfläche wäre auch bei sauberem Parsen
    falsch, und `detail` ist genau so einer. Nach der Konsumentenregel des
    Vertrags ignoriert ein bestehender Leser die zwei neuen Felder; ein neuer
    liest `code` und lässt `detail` liegen.
    """

    detail: str = Field(description="Meldung aus dem T-24-Vertrag")
    code: str = Field(description="Stabile Kennung: symbol_ambiguous")
    params: dict[str, str] = Field(
        default_factory=dict, description="Werte für den übersetzten Text"
    )
    candidates: list[ListingCandidate] = Field(
        description="Alle Listings, die dieses Symbol tragen"
    )


# Die veröffentlichte Form der beiden `409`-Fälle. Erzeugt werden sie zentral
# in `app/main.py`, weil sie tief in Repository und Speicherweg entstehen; die
# Router sagen sie nur zu. Ausgeschrieben je Router wären es acht Texte, die
# auseinanderlaufen, sobald einer davon genauer wird.
#
# **Zwei Konstanten, weil nicht jeder Endpunkt beide Fälle kennt.** Ein
# Endpunkt, der kein Symbol entgegennimmt, kann nicht mehrdeutig werden; ihm
# den Fall trotzdem zuzusagen wäre eine Zusage ins Blaue.
IDENTITY_CONFLICT_RESPONSE: dict[int | str, dict[str, object]] = {
    409: {
        "model": ErrorDetail,
        "description": (
            "Zwei Zeilen beanspruchen dieselbe kanonische Identität "
            "(`code: identity_conflict`)"
        ),
    }
}

_INVALID_ISIN_SCHEMA = {"$ref": "#/components/schemas/ErrorDetail"}
_VALIDATION_SCHEMA = {"$ref": "#/components/schemas/HTTPValidationError"}
_DETAIL_TEXT_SCHEMA = {
    "title": "DetailText",
    "type": "object",
    # **Pflicht, nicht nur beschrieben.** Ohne `required` erlaubt der Vertrag
    # `{}` — und sagt damit gerade nicht zu, was diese Variante ausmacht.
    "required": ["detail"],
    "properties": {"detail": {"type": "string"}},
}


def invalid_isin_response(
    *, validation: bool = False, detail_text: bool = False
) -> dict[int | str, dict[str, object]]:
    """Die `422`-Zusage eines Weges, der eine ISIN entgegennimmt.

    **Ein `422` hat an mehreren Routen mehr als eine gültige Form**, und die
    Zusage muss alle nennen, die dort wirklich vorkommen. Eine einzelne
    `ErrorDetail`-Zusage verschwiege die beiden anderen und wäre damit
    genauso falsch wie die frühere Lage, in der `ErrorDetail` fehlte.

    Die drei Formen und woher sie kommen:

    * `ErrorDetail` — die ungültige ISIN, aus der gemeinsamen Prüfung. **An
      jedem dieser Wege möglich**, denn sie ist der Grund, warum diese Zusage
      überhaupt hier steht.
    * `HTTPValidationError` — FastAPIs eigene Prüfung, wo die Route weitere
      Parameter oder einen Rumpf validiert.
    * `{"detail": "…"}` — die verbliebenen Fließtext-Ablehnungen der Route
      (Zeitfenster, Symbolformat, fehlende Kennung). Sie werden hier **nicht**
      umgebaut, aber auch nicht verschwiegen.

    Args:
        validation: Ob die Route zusätzlich FastAPI-Validierung auslösen kann.
        detail_text: Ob sie eine eigene Fließtext-Ablehnung kennt.

    Returns:
        Ein `responses`-Eintrag für genau diese Route.
    """
    schemas: list[dict[str, object]] = [_INVALID_ISIN_SCHEMA]
    if validation:
        schemas.append(_VALIDATION_SCHEMA)
    if detail_text:
        schemas.append(_DETAIL_TEXT_SCHEMA)
    return {
        422: {
            "description": (
                "Die Eingabe hat nicht das Format einer ISIN "
                "(`code: invalid_isin_format`, `params.isin` nennt sie) — der "
                "Rumpf steht **nicht** unter `detail`. Wo weitere Formen "
                "möglich sind, nennt `anyOf` sie mit."
            ),
            "content": {
                "application/json": {
                    "schema": schemas[0] if len(schemas) == 1 else {"anyOf": schemas}
                }
            },
        }
    }

INSTRUMENT_NOT_FOUND_RESPONSE: dict[int | str, dict[str, object]] = {
    404: {
        "model": ErrorDetail,
        "description": (
            "Keine Quelle konnte dieses Papier auflösen "
            "(`code: instrument_not_found`, `params.identifier` nennt die "
            "Eingabe). **Nicht** dasselbe wie `502`: Dort haben die Quellen "
            "nicht geantwortet, hier haben sie geantwortet und kennen es nicht"
        ),
    }
}
"""Die `404`-Zusage der ISIN-Wege.

**Bis T-36 fehlte sie im veröffentlichten Vertrag**, obwohl die Routen den
Status zur Laufzeit lieferten — erst als deutschen Fließtext, seit T-35 als
`ErrorDetail`. Der OpenAPI-Schnappschuss blieb dabei grün: Er vergleicht, was
deklariert ist, mit sich selbst, und eine Antwort, die niemand deklariert,
fällt ihm nicht auf. Ein Konsument, der sich auf die veröffentlichte Form
verlässt, hätte den Fall nie behandelt.

Die Symbol-Wege bekommen sie **nicht**: Dort scheitert keine Auflösung, die
scheitern könnte — `fetch_quote` liefert `None`, ob der Anbieter das Symbol
nicht kennt oder gerade nicht antwortet. Beides als `404` auszugeben wäre
geraten; deshalb steht dort `502`. Die Begründung steht ausführlich bei
`daily_history_by_symbol`.
"""

SYMBOL_CONFLICT_RESPONSE: dict[int | str, dict[str, object]] = {
    409: {
        "model": Union[ErrorDetail, AmbiguousSymbolDetail],
        "description": (
            "Zwei Fälle unter einem Status, unterschieden über `code`: "
            "`symbol_ambiguous` — mehrere Listings tragen dieses Symbol, der "
            "Rumpf nennt die Kandidaten samt `listing_id`; "
            "`identity_conflict` — zwei Zeilen beanspruchen dieselbe "
            "kanonische Identität"
        ),
    }
}


class SourceDifference(BaseModel):
    """Eine Stelle, an der zwei Quellenlagen auseinandergehen."""

    field: str = Field(description="Eine Rolle (`quotes`, …) oder `packages`")
    theirs: list[str] = Field(description="Was die Sicherung führte")
    ours: list[str] = Field(description="Was die laufende Instanz führt")


class BackupReason(BaseModel):
    """Warum eine Sicherung nicht passt — als **Kennung**, nicht als Satz.

    Dieselbe Regel wie bei `ErrorDetail`: Der Server nennt den Grund, den Satz
    bildet das UI. Ein deutscher Backendtext stünde sonst in der englischen
    Oberfläche.
    """

    code: str = Field(
        description=(
            "Genau eine der drei **Passungs**ursachen: `backup_schema_too_new` · "
            "`backup_fingerprint_mismatch` · `backup_data_version_differ`. Ein "
            "unbekannter Name ist keine davon — dort fehlt die Ursache"
        )
    )
    params: dict[str, str] = Field(default_factory=dict, description="Werte für den Satz")
    differences: list[SourceDifference] = Field(
        default_factory=list, description="Nur bei `backup_data_version_differ`"
    )


class BackupEntry(BaseModel):
    """Eine Sicherung, so wie die Liste sie zeigt."""

    name: str = Field(description="Dateiname der Sicherung")
    created_at: str = Field(description="Zeitpunkt der Sicherung, ISO-8601 in UTC")
    size: int = Field(description="Größe der Datenbankdatei in Bytes")
    fingerprint: str = Field(description="Quellenkennung, unter der sie entstand")
    compatible: bool = Field(description="Passt sie zur **laufenden** Quellenlage?")
    reason: BackupReason | None = Field(
        default=None, description="Warum sie nicht passt; `null`, solange sie passt"
    )


class BackupErrorDetail(ErrorDetail):
    """Eine abgelehnte Wiederherstellung — mit ihrer Ursache.

    `ErrorDetail` trägt nur `dict[str, str]` und könnte die abweichenden Ketten
    nicht nennen. Die Erweiterung hängt sie an, statt den Aufrufer auf die
    Liste zu verweisen: Ein REST-Konsument soll den Grund aus der Ablehnung
    selbst erfahren.

    **`reason` fehlt beim `404`.** Ein unbekannter Name ist keine
    Passungsursache; dort trägt `params` den Namen, und eine erfundene vierte
    Kennung wäre eine Ursache, die es nicht gibt.
    """

    reason: BackupReason | None = Field(
        default=None, description="Die Passungsursache; `null` bei `backup_not_found`"
    )


class BackupList(BaseModel):
    """Die Sicherungen einer Instanz, jüngste zuerst.

    Auch die unpassenden stehen darin — mit ihrem Grund, nicht ausgeblendet.
    """

    fingerprint: str = Field(description="Quellenkennung der laufenden Konfiguration")
    pending_restore: str | None = Field(
        default=None,
        description=(
            "Name der vorgemerkten Sicherung, solange ein Neustart aussteht — "
            "dann ist die laufende Datenbank noch die alte"
        ),
    )
    restore_error: str = Field(
        default="",
        description=(
            "Warum der Tausch beim letzten Start scheiterte. Steht hier etwas, "
            "wird **nicht** erneut versucht: Derselbe Grund träfe beim nächsten "
            "Start wieder zu. Eine neue Anforderung löst den Zustand ab"
        ),
    )
    backups: list[BackupEntry]


class RestoreAccepted(BaseModel):
    """Die Antwort auf ein vorgemerktes Wiederherstellen — `202`, nicht `200`.

    **Der Dienst startet sich nicht selbst neu.** Ein Prozess, der seinen
    Lebenszyklus an der HTTP-Grenze übernimmt, entzieht ihn dem Container, der
    ihn führt. Die Antwort sagt, was noch fehlt, statt es zu tun.
    """

    backup: BackupEntry
    restart_required: bool = True
    detail: str = Field(description="Klartext: der Neustart steht noch aus")
