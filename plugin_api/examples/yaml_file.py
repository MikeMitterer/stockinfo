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

**Eine Datei, ein Parser, ein Schema — und das ist die ganze Zusage.** Die
Rollen unterscheiden sich in dem, was sie aus demselben Eintrag lesen, nicht
darin, wie sie ihn finden. Fünf Implementierungen liefen beim ersten
Formatnachtrag auseinander, und der Benutzer merkte es an einer Rolle, die
stumm nichts mehr lieferte.

**Was hier ausdrücklich *nicht* zugesagt wird: genau ein Lesevorgang.** Der
Host baut je Rolle eine Instanz; gemessen wird die Datei damit fünfmal
gelesen. Das ist eine Eigenschaft des Hosts, keine dieser Quelle, und eine
rollenübergreifende Zwischenspeicherung wäre eine Lifecycle-Architektur für
ein Problem, das niemand hat: Die Datei ist klein und wird beim Start gelesen.

Der Unterschied ist keine Wortklauberei. „Einmal gelesen" wäre eine Zusage
über den Host, die diese Datei nicht halten kann; „ein Parser, ein Schema" ist
eine über sie selbst, und sie hält.

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

from stockinfo_plugin.invariants import (
    currency_problem,
    has_timezone,
    identity_problem,
    is_finite_price,
)
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


_KNOWN_VERSIONS = frozenset({1})
"""Die Formatfassungen, die diese Fassung des Plugins lesen kann.

Eine höhere Zahl still zu lesen hieße, ein Format zu verstehen, das es noch
nicht gab — und der Benutzer bekäme eine Datei, die *fast* funktioniert.
"""


def _require_list(value: object, name: str, path: object) -> None:
    """Ein Block, der eine Liste sein muss, ist eine.

    Raises:
        FileProblem: Der Block trägt etwas anderes. Ohne diese Prüfung stirbt
            die Schleife darüber mit einem `AttributeError`, und der Betreiber
            liest einen Stacktrace statt der Zeile, die er ändern muss.
    """
    if value is None or isinstance(value, list):
        return
    where = f"{path}: {name}" if path else name
    raise FileProblem(
        f"{where} ist {type(value).__name__} statt einer Liste"
    )


def _require_mapping(value: object, name: str) -> None:
    """Ein Block, der ein Objekt sein muss, ist eines.

    Raises:
        FileProblem: Der Block trägt etwas anderes.
    """
    if not isinstance(value, dict):
        raise FileProblem(f"{name} ist {type(value).__name__} statt eines Objekts")


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
    """Der gelesene Stand der Datei — beim Bau geprüft, danach nur gelesen.

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

        # **Die Formprüfung steht vor der Inhaltsprüfung**, und der Grund ist
        # gemessen: `instruments: {}` ließ den Konstruktor mit einem
        # `AttributeError` sterben. Der Betreiber las einen Stacktrace statt
        # der Zeile, die er ändern muss.
        version = raw.get("version")
        if version not in _KNOWN_VERSIONS:
            raise FileProblem(
                f"{path}: version {version!r} ist unbekannt — diese Fassung "
                f"liest {sorted(_KNOWN_VERSIONS)}. Eine höhere Zahl bedeutet "
                "ein Format, das hier niemand kennt; sie stillschweigend zu "
                "lesen hieße, etwas anderes zu verstehen als gemeint"
            )
        _require_list(raw.get("instruments"), "instruments", path)
        _require_list(raw.get("fx_rates"), "fx_rates", path)

        self.by_isin: dict[str, dict] = {}
        self.by_symbol: dict[str, dict] = {}
        self.fx: dict[tuple[str, str], dict] = {}
        seen_ids: set[str] = set()

        for entry in raw.get("instruments") or []:
            self._add_instrument(entry, seen_ids)

        for rate in raw.get("fx_rates") or []:
            self._add_rate(rate)

    def _add_instrument(self, entry: dict, seen_ids: set[str]) -> None:
        """Prüft einen Eintrag und legt ihn in die Indexe.

        **Geprüft wird beim Laden, nicht beim Abruf.** Eine Datei mit einem
        kaputten Eintrag soll die Quelle abschalten und den Grund nennen —
        nicht Monate später eine einzelne Anfrage scheitern lassen, wenn
        niemand mehr weiß, dass jemand die Datei bearbeitet hat.

        Geprüft wird mit `stockinfo_plugin.invariants`, also denselben
        Funktionen, an denen der Host jede Antwort misst. Eigene Prüfungen
        wären eine zweite Wahrheit über dieselbe Sache.

        Raises:
            FileProblem: Der Eintrag verletzt eine Invariante. Die Meldung
                nennt die Kennung und die verletzte Regel — ohne beides sucht
                der Betreiber in einer Datei mit hundert Zeilen.
        """
        if not isinstance(entry, dict):
            raise FileProblem(
                f"instruments enthält {type(entry).__name__} statt eines "
                "Eintrags — jeder Listenpunkt ist ein Objekt mit id, identity, "
                "name und instrument_type"
            )
        entry_id = entry.get("id")
        where = f"Eintrag {entry_id!r}"
        if entry_id in seen_ids:
            raise FileProblem(
                f"die Kennung {entry_id!r} steht doppelt in der Datei — "
                "welcher der beiden Einträge gälte, wäre Zufall"
            )
        seen_ids.add(entry_id)

        identity = _identity_of(entry)
        problem = identity_problem(identity)
        if problem:
            raise FileProblem(f"{where}: {problem}")

        if not (entry.get("name") or "").strip():
            raise FileProblem(f"{where}: name fehlt — Pflichtfeld seit T-38")
        instrument_type = (entry.get("instrument_type") or "").strip()
        if not instrument_type:
            raise FileProblem(
                f"{where}: instrument_type fehlt — an ihm hängt, welche "
                "Metadatenquellen überhaupt gefragt werden"
            )
        # **Gegen die eigene Zusage geprüft, nicht gegen einen fremden
        # Katalog.** Was der Host führt, entscheidet er; was *diese* Quelle
        # zusagt, steht in `SUPPORTED_TYPES`. Eine Gattung daneben wäre eine
        # Zeile, die der Host nach seiner Deklaration gar nicht erst erfragt —
        # die Quelle behauptete etwas, das sie selbst nicht bedient.
        if instrument_type not in YamlFileSource.SUPPORTED_TYPES:
            raise FileProblem(
                f"{where}: instrument_type {instrument_type!r} steht nicht im "
                f"Katalog {sorted(YamlFileSource.SUPPORTED_TYPES)}"
            )

        price = entry.get("price") or {}
        if price:
            _require_mapping(price, f"{where}.price")
            self._check_amount(price, f"{where}, price")

        metadata = entry.get("metadata") or {}
        if metadata:
            _require_mapping(metadata, f"{where}.metadata")
            self._check_metadata(metadata, where)

        history = entry.get("history") or {}
        if history:
            _require_mapping(history, f"{where}.history")
            problem = currency_problem(history.get("currency"))
            if problem:
                raise FileProblem(f"{where}: history.currency {problem}")
            _require_list(history.get("closes"), f"{where}.history.closes", None)
            self._check_closes(history.get("closes") or [], where)

        record = {**entry, "identity": identity}
        symbol = _symbol_of(identity)
        if symbol:
            self._claim(self.by_symbol, symbol.upper(), record, where, "Symbol")
        isin = isin_of(identity)
        if isin:
            self._claim(self.by_isin, isin.upper(), record, where, "ISIN")

    @staticmethod
    def _claim(index: dict, key: str, record: dict, where: str, label: str) -> None:
        """Trägt einen Eintrag ein — und weist einen zweiten Anspruch ab.

        **Der stillste Fehler des ganzen Formats.** Zwei Einträge mit
        derselben ISIN sind keine Verdopplung, sondern ein Widerspruch: Beide
        behaupten, dasselbe Papier zu beschreiben. Bis hierher gewann der
        zweite, weil eine Zuweisung den ersten überschrieb — die Datei sah
        gültig aus, und welcher Eintrag galt, hing an der Zeilenreihenfolge.
        """
        if key in index:
            raise FileProblem(
                f"{where}: {label} {key} ist schon vergeben — zwei Einträge "
                "können nicht dasselbe Papier beschreiben"
            )
        index[key] = record

    @staticmethod
    def _check_amount(amount: dict, where: str) -> None:
        """Währung, Zeitpunkt und Betrag eines Kurses.

        Raises:
            FileProblem: Eine der drei Angaben taugt nicht. Ein Betrag ohne
                Währung ist eine Zahl, ein Zeitpunkt ohne Zone ist in Toronto
                ein anderer als in Frankfurt, und ``0`` ist keine Angabe,
                sondern eine fehlende Angabe, die sich als Zahl ausgibt.
        """
        problem = currency_problem(amount.get("currency"))
        if problem:
            raise FileProblem(f"{where}.currency {problem}")
        if not is_finite_price(amount.get("value")):
            raise FileProblem(
                f"{where}.value {amount.get('value')!r} ist kein brauchbarer "
                "Betrag — verlangt ist eine positive, endliche Zahl"
            )
        _as_moment(amount.get("as_of"), where)

    @staticmethod
    def _check_metadata(metadata: dict, where: str) -> None:
        """Die optionalen Kennzahlen — Zahlen müssen Zahlen sein.

        Raises:
            FileProblem: Ein als Zahl deklariertes Feld trägt etwas anderes.
                Bis hierher fiel das erst beim Abruf auf, als `float("nope")`
                warf — mitten in einer Metadatenanfrage, lange nachdem jemand
                die Datei bearbeitet hatte.
        """
        for key, field in YamlFileSource._METADATA_KEYS:
            if key not in metadata:
                continue
            spec = next(
                (item for item in YamlFileSource.FIELDS if item.name == field), None
            )
            if spec is None or spec.kind != "number":
                continue
            try:
                float(metadata[key])
            except (TypeError, ValueError) as error:
                raise FileProblem(
                    f"{where}: metadata.{key} ist {metadata[key]!r} und damit "
                    "keine Zahl"
                ) from error

    @staticmethod
    def _check_closes(closes: list[dict], where: str) -> None:
        """Die gepflegten Schlusskurse — Datum, Betrag, keine Dubletten.

        Raises:
            FileProblem: Ein Datum ist unlesbar, ein Betrag unbrauchbar, oder
                derselbe Tag steht zweimal. Zwei Werte für einen Tag sind
                keine Reihe, sondern ein Widerspruch; welcher gälte, entschiede
                die Sortierung.
        """
        seen: set[date] = set()
        for close in closes:
            day = _as_date(close.get("date"), where)
            if day in seen:
                raise FileProblem(
                    f"{where}: der {day.isoformat()} steht zweimal in der "
                    "History — zwei Werte für einen Tag sind kein Verlauf"
                )
            seen.add(day)
            if not is_finite_price(close.get("value")):
                raise FileProblem(
                    f"{where}: Schlusskurs {close.get('value')!r} am "
                    f"{day.isoformat()} ist kein brauchbarer Betrag"
                )

    def _add_rate(self, rate: dict) -> None:
        """Prüft einen Wechselkurs und legt ihn ab."""
        base = str(rate.get("base", "")).upper()
        quote = str(rate.get("quote", "")).upper()
        where = f"fx_rates {base}/{quote}"
        for field, value in (("base", base), ("quote", quote)):
            problem = currency_problem(value)
            if problem:
                raise FileProblem(f"{where}: {field} {problem}")
        if not is_finite_price(rate.get("rate")):
            raise FileProblem(
                f"{where}: rate {rate.get('rate')!r} ist kein brauchbarer Kurs"
            )
        _as_moment(rate.get("as_of"), where)
        if (base, quote) in self.fx:
            raise FileProblem(f"{where}: das Paar steht doppelt in der Datei")
        self.fx[(base, quote)] = rate

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


def _lookup_key(identity: object) -> str:
    """Woran sich dieses Papier in der Datei finden lässt — oder ``""``.

    Eine Identität ohne Ticker, ohne Basiswert und ohne ISIN ist keine Frage,
    die diese Quelle beantworten könnte. Sie zu verneinen heißt `NotResponsible`
    und nicht `NotFound`: Der Unterschied entscheidet in der Kette, ob am Ende
    ein 404 oder ein „der Nächste, bitte" steht.
    """
    isin = isin_of(identity)
    if isin:
        return isin
    return _symbol_of(identity) or ""


def _closes(entry: dict) -> list[dict]:
    """Die gepflegten Schlusskurse eines Eintrags, aufsteigend nach Datum."""
    history = entry.get("history") or {}
    return sorted(history.get("closes") or [], key=lambda close: str(close["date"]))


def _as_date(value: object, where: str = "") -> date:
    """Ein Datum aus der Datei — YAML liefert je nach Schreibweise beides.

    Args:
        value: Der Wert aus der Datei.
        where: Fundort für die Meldung.

    Raises:
        FileProblem: Der Wert ist kein Datum. Ohne diese Prüfung stürbe der
            Parser hier mit einem `ValueError`, und der Betreiber läse einen
            Stacktrace statt der Zeile, die er ändern muss.
    """
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError) as error:
        raise FileProblem(f"{where}: {value!r} ist kein Datum") from error


def _as_moment(value: object, where: str = "") -> datetime:
    """Ein Zeitpunkt aus der Datei, mit Zone.

    Args:
        value: Der Wert aus der Datei.
        where: Fundort für die Meldung.

    Raises:
        FileProblem: Kein lesbarer Zeitpunkt, oder einer **ohne Zone**. Ohne
            Zone ist der Augenblick nicht rekonstruierbar — 17:30 ist in
            Toronto ein anderer als in Frankfurt, und hinterher sieht man es
            der Angabe nicht mehr an.
    """
    if isinstance(value, datetime):
        moment = value
    else:
        try:
            moment = datetime.fromisoformat(str(value))
        except (TypeError, ValueError) as error:
            raise FileProblem(f"{where}: {value!r} ist kein Zeitpunkt") from error
    if not has_timezone(moment):
        raise FileProblem(f"{where}: {value!r} trägt keine Zeitzone")
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
    # Ein **Tupel** und kein dict: Ein veränderliches Klassenattribut gehört
    # allen Instanzen gemeinsam, und der Vertrag weist es zu Recht ab.
    _METADATA_KEYS = (
        ("ter_bps", "ter"),
        ("provider", "provider"),
        ("fund_domicile", "fund_domicile"),
    )

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
        """Führt die Datei etwas zu dieser Anfrage?

        **Die Frage ist je Rolle eine andere Zeile.** Eine `FxRequest` sucht in
        `fx_rates`, alles übrige unter den Instrumenten. Bis hierher fragte
        jede Rolle denselben Instrumentenindex — die Devisenrolle fand dort
        nie etwas und verneinte ihre Zuständigkeit, während `fetch_rate`
        denselben Kurs lieferte. Eine Quelle, die sich für unzuständig erklärt
        und dann doch antwortet, macht den Vorfilter des Hosts wertlos.

        Diese Quelle hat keine Marktgrenze und kein Länderpräfix: Die Datei
        ist die Antwort auf die Zuständigkeitsfrage.
        """
        if self._catalogue is None:
            return False
        if isinstance(request, FxRequest):
            return self._rate_for(request) is not None
        return self._catalogue.find(request) is not None

    def _rate_for(self, request: FxRequest) -> dict | None:
        """Der Eintrag zu einem Währungspaar — oder der Identitätskurs.

        `CAD/CAD` steht in keiner Datei, weil ihn niemand pflegt. Ihn als
        „kenne ich nicht" abzuweisen zwänge den Host, dieselbe Rechnung selbst
        anzustellen — für eine Zahl, die feststeht.
        """
        if self._catalogue is None:
            return None
        base, quote = request.base.upper(), request.quote.upper()
        if base and base == quote:
            return {"base": base, "quote": quote, "rate": 1.0, "as_of": None}
        return self._catalogue.fx.get((base, quote))

    # ─── Auflösen ─────────────────────────────────────────────────────────────

    def resolve(self, request: ResolveRequest) -> Resolution:
        """Identität, Name und Gattung aus der Datei."""
        if self._catalogue is None:
            return Unavailable(self._problem)
        if not (request.isin or request.symbol):
            return NotResponsible(
                f"{self.name} schlägt über ISIN oder Symbol nach — die "
                "Anfrage nennt beides nicht"
            )
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
        if not _lookup_key(request.identity):
            return NotResponsible(
                f"{self.name}: die Identität trägt weder ISIN noch Symbol"
            )
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
        if not _lookup_key(request.identity):
            return NotResponsible(
                f"{self.name}: die Identität trägt weder ISIN noch Symbol"
            )
        entry = self._catalogue.find(request)
        if entry is None:
            return NotFound()

        # **Das angefragte Fenster, nicht die ganze Datei.** Wer `start` und
        # `end` ignoriert, liefert auf jede Frage dieselbe Reihe: Für den
        # Aufrufer sieht das aus wie eine Antwort auf seine Frage und ist die
        # Antwort auf eine andere. Gemessen lieferte eine Anfrage ab 2030 drei
        # Werte aus 2026.
        bars = [
            DailyBar(day=day, close=float(close["value"]))
            for close in _closes(entry)
            for day in (_as_date(close["date"]),)
            if (request.start is None or day >= request.start)
            and (request.end is None or day <= request.end)
        ]
        if not bars:
            return NotFound()
        return DailySeries(
            bars=tuple(bars),
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
        for key, field in self._METADATA_KEYS:
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
        base, quote = request.base.upper(), request.quote.upper()
        rate = self._rate_for(request)
        if rate is None:
            return NotResponsible(f"{self.name} führt {base}/{quote} nicht")
        moment = rate["as_of"]
        return FxRate(
            base=base,
            quote=quote,
            rate=float(rate["rate"]),
            # Der Identitätskurs trägt keinen Zeitpunkt aus der Datei — er gilt
            # immer. `now` ist hier die ehrlichste Angabe: Der Wert ist gerade
            # entstanden, nicht gepflegt worden.
            as_of=_as_moment(moment) if moment else datetime.now(timezone.utc),
        )


SOURCES = [YamlFileSource]
