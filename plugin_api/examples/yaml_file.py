"""Beispiel-Plugin: alle fünf Rollen aus **einer** vom Benutzer gepflegten Datei.

Wo keine automatische Quelle etwas weiß, trägt der Betreiber es von Hand ein.
Bis hierher gab es dafür vier getrennte CSV-Quellen mit je eigenem Format,
eigenem Parser und eigener Zuständigkeitsregel — für den Benutzer vier Dateien,
die zusammenpassen mussten, ohne dass etwas das geprüft hätte.

Diese Quelle liest **eine** YAML-Datei und bedient daraus jede Rolle:

============= ===============================================================
`resolvers`   Identität, Name und Gattung
`quotes`      der aktuelle `price` — oder der jüngste Schlusskurs
`daily`       die manuell gepflegte `history`
`etf_meta`    die optionalen `metadata`
`fx`          die Einträge aus `fx_rates`
============= ===============================================================

**Ein Parser, nicht fünf.** Die Rollen unterscheiden sich in dem, was sie aus
demselben Eintrag lesen, nicht darin, wie sie ihn finden. Fünf Implementierungen
liefen beim ersten Formatnachtrag auseinander, und der Benutzer merkte es an
einer Rolle, die stumm nichts mehr lieferte.

**Die manuelle History ist ein Rückfall, kein Vorrang.** Sie gilt für ein
Papier, dessen History keine konfigurierte Quelle abfragen kann — eine
OTC-Anleihe etwa. Steht die Quelle in der Kette hinter den Online-Quellen,
gewinnt ohnehin die erste, die antwortet.

Format::

    version: 1
    instruments:
      - id: german-bond
        identity: {kind: isin_only, isin: DE0001102531}
        name: Bundesrepublik Deutschland
        instrument_type: bond
        history:
          currency: EUR
          closes:
            - {date: "2026-08-27", value: 99.42}
    fx_rates:
      - {base: CAD, quote: EUR, rate: 0.6412, as_of: "2026-08-27T17:30:00+02:00"}

Das vollständige Beispiel liegt in `_tickets/T-37-single-file-sample.yaml`.
"""

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from stockinfo_plugin import (
    DailyBar,
    DailyCloseSource,
    DailyRequest,
    DailyResult,
    DailySeries,
    FieldSpec,
    FxRate,
    FxRequest,
    FxResult,
    FxSource,
    IsinOnlyIdentity,
    ListedIdentity,
    MetadataSource,
    NotFound,
    NotResponsible,
    PairIdentity,
    Quote,
    QuoteRequest,
    QuoteResult,
    QuoteSource,
    Reading,
    Resolution,
    Resolved,
    ResolveRequest,
    Resolver,
    Unavailable,
    Unit,
    isin_of,
)


class FileProblem(Exception):
    """Die Datei ist nicht benutzbar — mit einem Grund, den ein Mensch liest."""


def _identity_of(entry: dict) -> object:
    """Baut die Identität eines Eintrags in ihrer Form.

    Raises:
        FileProblem: Die Form fehlt oder ist unbekannt. Zu raten wäre hier
            besonders teuer: Aus einem `pair` ohne `kind` würde ein Listing
            ohne Handelsplatz, und das Papier landete unter falscher Identität
            im Bestand.
    """
    identity = entry.get("identity") or {}
    kind = identity.get("kind")
    if kind == "listed":
        return ListedIdentity(
            ticker=identity.get("ticker") or "",
            mic=identity.get("mic") or "",
            isin=identity.get("isin"),
        )
    if kind == "pair":
        return PairIdentity(
            base=identity.get("base") or "",
            quote_currency=identity.get("quote_currency") or "",
        )
    if kind == "isin_only":
        return IsinOnlyIdentity(isin=identity.get("isin") or "")
    raise FileProblem(
        f"Eintrag {entry.get('id')!r}: identity.kind ist {kind!r} — "
        "erlaubt sind listed, pair und isin_only"
    )


def _symbol_of(identity: object) -> str:
    """Unter welchem Symbol dieses Papier gefunden wird.

    Für ein Paar ist es `{base}-{quote_currency}` — die Schreibweise, die auch
    yfinance führt und die einzige, die ein Paar überhaupt hat.
    """
    if isinstance(identity, PairIdentity):
        return f"{identity.base}-{identity.quote_currency}"
    if isinstance(identity, ListedIdentity):
        return identity.ticker
    return identity.isin


class _Catalogue:
    """Der gelesene Stand der Datei — einmal geprüft, danach nur noch gelesen.

    Die Indexe sind der Grund für diese Klasse: Jede Rolle sucht denselben
    Eintrag, nur über einen anderen Schlüssel. Sie je Rolle neu aufzubauen
    hieße, dieselbe Zuordnung fünfmal zu pflegen.
    """

    def __init__(self, path: Path) -> None:
        """
        Args:
            path: Die Fachdatendatei.

        Raises:
            FileProblem: Datei fehlt, ist kein gültiges YAML, oder ihr Inhalt
                verletzt eine Invariante.
        """
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except OSError as error:
            raise FileProblem(f"{path} nicht lesbar: {error}") from error
        except yaml.YAMLError as error:
            raise FileProblem(f"{path} ist kein gültiges YAML: {error}") from error

        if not isinstance(raw, dict):
            raise FileProblem(f"{path} enthält kein Objekt auf oberster Ebene")

        self.by_isin: dict[str, dict] = {}
        self.by_symbol: dict[str, dict] = {}
        self.fx: dict[tuple[str, str], dict] = {}
        seen_ids: set[str] = set()

        for entry in raw.get("instruments") or []:
            entry_id = entry.get("id")
            if entry_id in seen_ids:
                raise FileProblem(
                    f"die Kennung {entry_id!r} steht doppelt in der Datei — "
                    "welcher der beiden Einträge gälte, wäre Zufall"
                )
            seen_ids.add(entry_id)

            identity = _identity_of(entry)
            if not entry.get("name") or not entry.get("instrument_type"):
                raise FileProblem(
                    f"Eintrag {entry_id!r}: name und instrument_type sind "
                    "Pflicht — ohne sie ist die Auflösung unbrauchbar"
                )

            record = {**entry, "identity": identity}
            symbol = _symbol_of(identity)
            if symbol:
                self.by_symbol[symbol.upper()] = record
            isin = isin_of(identity)
            if isin:
                self.by_isin[isin.upper()] = record

        for rate in raw.get("fx_rates") or []:
            key = (str(rate.get("base", "")).upper(), str(rate.get("quote", "")).upper())
            self.fx[key] = rate

    def find(self, request: object) -> dict | None:
        """Den Eintrag zu einer Anfrage — über ISIN oder Symbol.

        Beide Wege stehen hier zusammen, weil jede Rolle beide braucht: Eine
        Anleihe kommt über die ISIN herein, eine Coin über ihr Symbol.
        """
        isin = getattr(request, "isin", None)
        if isin is None:
            isin = isin_of(getattr(request, "identity", None))
        if isin and isin.upper() in self.by_isin:
            return self.by_isin[isin.upper()]

        symbol = getattr(request, "symbol", None)
        if symbol is None:
            identity = getattr(request, "identity", None)
            symbol = _symbol_of(identity) if identity is not None else None
        if symbol and symbol.upper() in self.by_symbol:
            return self.by_symbol[symbol.upper()]
        return None


def _closes(entry: dict) -> list[dict]:
    """Die gepflegten Schlusskurse eines Eintrags, aufsteigend nach Datum."""
    history = entry.get("history") or {}
    return sorted(history.get("closes") or [], key=lambda close: str(close["date"]))


def _as_date(value: object) -> date:
    """Ein Datum aus der Datei — YAML liefert je nach Schreibweise beides."""
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    return date.fromisoformat(str(value))


def _as_moment(value: object) -> datetime:
    """Ein Zeitpunkt aus der Datei, mit Zone.

    Raises:
        FileProblem: Ohne Zone ist der Augenblick nicht rekonstruierbar —
            17:30 ist in Toronto ein anderer als in Frankfurt.
    """
    moment = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    if moment.tzinfo is None:
        raise FileProblem(f"Zeitangabe {value!r} trägt keine Zeitzone")
    return moment


class YamlFileSource(
    Resolver, QuoteSource, DailyCloseSource, MetadataSource, FxSource
):
    """Eine Datei, fünf Rollen.

    Die Deklaration ist bewusst **vollständig**: Diese Quelle liest eine
    Dateizeile und ist damit für jede Identitätsform und jede Gattung des
    Katalogs zuständig. Eine leere Menge hieße „nichts zugesagt", und der Host
    überspränge die Quelle für jede bekannte Gattung — ausgerechnet die, die
    als einzige antworten könnte.
    """

    name = "yaml-file"
    cost = "free"
    api_version = 2
    SUPPORTED_KINDS = frozenset({"listed", "pair", "isin_only"})
    SUPPORTED_TYPES = frozenset({"stock", "etf", "etc", "fund", "crypto", "bond"})

    FIELDS = (
        FieldSpec(
            "ter",
            kind="number",
            unit=Unit.BASIS_POINTS,
            plausible=(0.5, 500.0),
            label_en="Total expense ratio",
            label_de="Gesamtkostenquote",
        ),
        FieldSpec(
            "provider", kind="text", label_en="Fund provider", label_de="Anbieter"
        ),
        FieldSpec(
            "fund_domicile",
            kind="text",
            label_en="Fund domicile",
            label_de="Fondsdomizil",
        ),
    )

    # Schlüssel in der Datei → Feldname im Vertrag. Die Namen unterscheiden sich
    # dort, wo die Datei die Einheit mitträgt: `ter_bps` sagt dem Benutzer, in
    # welcher Einheit die Zahl steht.
    _METADATA_KEYS = {
        "ter_bps": "ter",
        "provider": "provider",
        "fund_domicile": "fund_domicile",
    }

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """
        Args:
            config: ``path`` — Pfad zur Fachdatendatei. Es gibt **keine**
                Dateisuche und keinen zweiten Vorgabepfad: Zwei Orte, an denen
                eine Datei liegen darf, sind ein Ort, an dem sie fehlt.
        """
        super().__init__(config)
        self._path = Path(self._config.get("path", "/data/assets.yaml"))
        self._problem = ""
        self._catalogue: _Catalogue | None = None
        try:
            self._catalogue = _Catalogue(self._path)
        except FileProblem as error:
            self._problem = str(error)

    def configuration_problem(self) -> str:
        """Warum diese Quelle nicht arbeiten kann — oder ``""``.

        Eine Quelle, die sich wegen einer kaputten Datei abschaltet und dazu
        schweigt, kostet den Betreiber den Nachmittag: Er sieht leere Listen
        und sucht den Fehler in der App.
        """
        if not self._path.exists():
            return f"Datei {self._path} nicht gefunden — Pfad in der Konfiguration prüfen"
        return self._problem

    def handles(self, request: object) -> bool:
        """Zuständig, wenn die Datei den Eintrag führt.

        Diese Quelle hat keine Marktgrenze und kein Länderpräfix — sie kennt
        genau das, was der Benutzer eingetragen hat. Die Datei ist die Antwort
        auf die Zuständigkeitsfrage.
        """
        return self._catalogue is not None and self._catalogue.find(request) is not None

    # ─── Auflösen ─────────────────────────────────────────────────────────────

    def resolve(self, request: ResolveRequest) -> Resolution:
        """Identität, Name und Gattung aus der Datei."""
        if self._catalogue is None:
            return Unavailable(self._problem)
        entry = self._catalogue.find(request)
        if entry is None:
            return NotFound()
        return Resolved(
            identity=entry["identity"],
            name=entry["name"],
            instrument_type=entry["instrument_type"],
        )

    # ─── Kurs ─────────────────────────────────────────────────────────────────

    def fetch_quote(self, request: QuoteRequest) -> QuoteResult:
        """Der aktuelle Kurs — oder der jüngste gepflegte Schlusskurs.

        Der Rückfall ist ausdrücklich gewollt: Ein Papier ohne abfragbare
        Kursquelle hat oft nur die von Hand gepflegte History, und die
        jüngste Zeile darin ist der beste bekannte Preis. Ihn liegen zu lassen
        hieße, eine Angabe zu verschweigen, die in der Datei steht.
        """
        if self._catalogue is None:
            return Unavailable(self._problem)
        entry = self._catalogue.find(request)
        if entry is None:
            return NotFound()

        price = entry.get("price")
        if price:
            return Quote(
                price=float(price["value"]),
                currency=str(price["currency"]),
                as_of=_as_moment(price["as_of"]),
            )

        closes = _closes(entry)
        if not closes:
            return NotFound()
        newest = closes[-1]
        return Quote(
            price=float(newest["value"]),
            currency=str((entry.get("history") or {})["currency"]),
            # **Mitternacht UTC, und das ist eine Konvention, keine Messung.**
            # Ein gepflegter Schlusskurs trägt ein Datum, keine Uhrzeit; die
            # Zone hier ist die einzige, die überall dasselbe bedeutet. Die
            # lokale Zone der Maschine zu nehmen hieße, dass derselbe Eintrag
            # auf zwei Servern zwei Augenblicke bezeichnet.
            as_of=datetime.combine(
                _as_date(newest["date"]), datetime.min.time(), tzinfo=timezone.utc
            ),
        )

    # ─── Historie ─────────────────────────────────────────────────────────────

    def fetch_daily(self, request: DailyRequest) -> DailyResult:
        """Die manuell gepflegte Reihe, aufsteigend und ohne Duplikate."""
        if self._catalogue is None:
            return Unavailable(self._problem)
        entry = self._catalogue.find(request)
        if entry is None:
            return NotFound()
        closes = _closes(entry)
        if not closes:
            return NotFound()
        return DailySeries(
            bars=tuple(
                DailyBar(day=_as_date(close["date"]), close=float(close["value"]))
                for close in closes
            ),
            currency=str((entry.get("history") or {})["currency"]),
            # Von Hand gepflegte Kurse sind, was der Benutzer eingetragen hat.
            # `True` zu behaupten wäre eine Aussage über eine Bereinigung, die
            # niemand vorgenommen hat.
            adjusted=False,
        )

    # ─── Metadaten ────────────────────────────────────────────────────────────

    def fetch(self, request: ResolveRequest) -> list[Reading] | None:
        """Die optionalen Kennzahlen eines Eintrags.

        ``[]`` heißt „nachgesehen, nichts eingetragen"; ``None`` hieße „konnte
        nicht nachsehen" und schützte einen gespeicherten Stand. Der
        Unterschied entscheidet, ob ein gepflegter Wert überschrieben wird.
        """
        if self._catalogue is None:
            return None
        entry = self._catalogue.find(request)
        if entry is None:
            return []

        metadata = entry.get("metadata") or {}
        readings: list[Reading] = []
        for key, field in self._METADATA_KEYS.items():
            if key not in metadata:
                continue
            value = metadata[key]
            spec = self.declared(field)
            readings.append(
                Reading(
                    field=field,
                    value=float(value) if spec and spec.kind == "number" else value,
                    unit=spec.unit if spec else None,
                    source=self.name,
                )
            )
        return readings

    # ─── Devisen ──────────────────────────────────────────────────────────────

    def fetch_rate(self, request: FxRequest) -> FxResult:
        """Ein Wechselkurs aus `fx_rates`."""
        if self._catalogue is None:
            return Unavailable(self._problem)
        key = (request.base.upper(), request.quote.upper())
        rate = self._catalogue.fx.get(key)
        if rate is None:
            return NotResponsible(f"{self.name} führt {key[0]}/{key[1]} nicht")
        return FxRate(
            base=key[0],
            quote=key[1],
            rate=float(rate["rate"]),
            as_of=_as_moment(rate["as_of"]),
        )


SOURCES = [YamlFileSource]
