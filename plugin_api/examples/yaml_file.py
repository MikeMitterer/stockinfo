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

Zwei Vorlagen liegen in `examples/`: `assets-standalone.yaml` für eine
Instanz, die nur aus dieser Datei lebt, und `assets-fallback.yaml` für die
Datei hinter einer Online-Kette.
"""

import logging
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from stockinfo_plugin.invariants import (
    currency_problem,
    is_finite_number,
    has_timezone,
    identity_problem,
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

logger = logging.getLogger(__name__)
"""Die Standardbibliothek, nicht das Protokoll des Hosts: Ein Beispiel-Plugin
soll seinen Grund nennen können, ohne sich an eine fremde Bibliothek zu binden."""



class FileProblem(Exception):
    """Die Datei ist nicht benutzbar — mit einem Grund, den ein Mensch liest."""


_KNOWN_VERSIONS = frozenset({1})
"""Die Formatfassungen, die diese Fassung des Plugins lesen kann.

Eine höhere Zahl still zu lesen hieße, ein Format zu verstehen, das es noch
nicht gab — und der Benutzer bekäme eine Datei, die *fast* funktioniert.
"""


def _require_list(value: object, name: str, of_objects: bool = True) -> list:
    """Ein Block, der eine Liste von Objekten sein muss, ist eine.

    Args:
        value: Der Wert aus der Datei; ``None`` heißt „nicht vorhanden".
        name: Fundort für die Meldung.
        of_objects: Ob jeder Listenpunkt ein Objekt sein muss.

    Returns:
        Die Liste, oder ``[]`` wenn der Block fehlt.

    Raises:
        FileProblem: Der Block oder einer seiner Punkte trägt etwas anderes.
            Ohne diese Prüfung stirbt die Schleife darüber mit einem
            `AttributeError`, und der Betreiber liest einen Stacktrace statt
            der Zeile, die er ändern muss.
    """
    if value is None:
        return []
    if not isinstance(value, list):
        raise FileProblem(f"{name} ist {type(value).__name__} statt einer Liste")
    if of_objects:
        for position, item in enumerate(value, start=1):
            if not isinstance(item, dict):
                raise FileProblem(
                    f"{name}[{position}] ist {type(item).__name__} statt eines "
                    "Objekts"
                )
    return value


def _require_mapping(entry: dict, key: str, where: str) -> dict:
    """Ein optionaler Unterblock ist ein Objekt — oder er fehlt.

    **`or {}` war hier der Fehler.** Es macht aus jedem falsey Wert ein
    „fehlt": Eine leere Liste an `price` verschwand still, statt beanstandet
    zu werden. Ein Benutzer, der `price: []` schreibt, meint etwas — und
    bekam eine Datei, die tat, als stünde dort nichts.

    Returns:
        Der Unterblock, oder ``{}`` wenn der Schlüssel fehlt.

    Raises:
        FileProblem: Der Schlüssel ist da und trägt kein Objekt.
    """
    if key not in entry or entry[key] is None:
        return {}
    value = entry[key]
    if not isinstance(value, dict):
        raise FileProblem(
            f"{where}.{key} ist {type(value).__name__} statt eines Objekts"
        )
    return value


def _require_text(value: object, name: str) -> str:
    """Ein Feld, das Text sein muss, ist Text — und nicht leer.

    Raises:
        FileProblem: Der Wert fehlt, ist leer, ist keine Zeichenkette oder
            trägt umgebenden Leerraum.

    **Der Leerraum ist der unauffällige Teil.** Diese Funktion gab bis hierher
    den getrimmten Wert zurück, während die Aufrufer den rohen speichern:
    ``currency: " EUR "`` bestand die Prüfung und wurde anschließend als
    Währung ausgeliefert. Zwei Wahrheiten über denselben Wert, und die
    geprüfte war nicht die gespeicherte.

    Abgewiesen statt stillschweigend getrimmt — dieselbe Regel, die
    `identity_problem` für `base` schon führt. Trimmen hieße zu entscheiden,
    dass der Leerraum nicht gemeint war; abweisen fragt den Benutzer.
    """
    if not isinstance(value, str):
        raise FileProblem(
            f"{name} ist {type(value).__name__} statt einer Zeichenkette"
        )
    if not value.strip():
        raise FileProblem(f"{name} ist leer")
    if value != value.strip():
        raise FileProblem(
            f"{name} ist {value!r} — umgebender Leerraum gehört nicht zum Wert"
        )
    return value


def _require_version(value: object) -> None:
    """Die Formatfassung ist **genau** eine bekannte Ganzzahl.

    Raises:
        FileProblem: Die Angabe fehlt, ist keine Ganzzahl oder keine bekannte.

    **`isinstance(value, int)` allein genügt nicht**, und das ist eine Falle
    von Python selbst: ``True`` *ist* eine Ganzzahl und ``True == 1``. Eine
    Datei mit ``version: true`` galt damit als Fassung 1. Dasselbe für
    ``1.0``, das in einer Menge von Ganzzahlen ebenfalls gefunden wird.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise FileProblem(
            f"version ist {value!r} ({type(value).__name__}) statt einer "
            f"Ganzzahl aus {sorted(_KNOWN_VERSIONS)}"
        )
    if value not in _KNOWN_VERSIONS:
        raise FileProblem(
            f"version {value} ist unbekannt — diese Fassung liest "
            f"{sorted(_KNOWN_VERSIONS)}. Eine höhere Zahl bedeutet ein Format, "
            "das hier niemand kennt; sie stillschweigend zu lesen hieße, etwas "
            "anderes zu verstehen als gemeint"
        )


def _require_currency(value: object, where: str) -> str:
    """Eine Währung ist ein ISO-4217-Code — und zuerst überhaupt Text.

    `currency_problem` erwartet eine Zeichenkette; eine Zahl aus der Datei käme
    dort als `TypeError` heraus statt als Befund. Die Typprüfung steht deshalb
    davor und nicht daneben.

    Raises:
        FileProblem: Kein Text, oder kein gültiger Code.
    """
    code = _require_text(value, f"{where}.currency")
    problem = currency_problem(code)
    if problem:
        raise FileProblem(f"{where}.currency {problem}")
    return code


def _require_number(
    value: object,
    where: str,
    *,
    positive: bool = False,
    bounds: tuple[float, float] | None = None,
) -> float:
    """Eine Zahl aus der Datei — geprüft am **rohen** Wert, nicht am Ergebnis.

    Args:
        value: Der Wert, wie YAML ihn geliefert hat.
        where: Fundort für die Meldung.
        positive: Ob nur echte positive Werte zählen — Kurse und Raten.
        bounds: Zulässiger Bereich, falls die Quelle einen deklariert.

    Returns:
        Der Wert als `float`.

    Raises:
        FileProblem: Der Wert ist keine Zahl, ist ``True``/``False``, ist eine
            Zeichenkette, ist nicht endlich, liegt außerhalb oder lässt sich
            nicht als Gleitkommazahl darstellen.

    Drei Fälle sehen wie Zahlen aus und sind keine. ``True`` ist in Python eine
    Ganzzahl und käme sonst als ``1.0`` durch. ``"20"`` ist Text; ihn
    umzuwandeln hieße zu raten, was der Benutzer meinte. Und eine Ganzzahl mit
    tausend Stellen ist zwar eine Zahl, aber keine, die sich als
    Gleitkommazahl ausdrücken lässt — sie warf bisher erst beim Abruf.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise FileProblem(
            f"{where} ist {value!r} ({type(value).__name__}) statt einer Zahl"
        )
    try:
        number = float(value)
    except (OverflowError, ValueError) as error:
        raise FileProblem(
            f"{where} ist zu groß für eine Gleitkommazahl"
        ) from error
    if not is_finite_number(number):
        raise FileProblem(f"{where} ist {value!r} und damit nicht endlich")
    if positive and number <= 0:
        raise FileProblem(
            f"{where} ist {value!r} — verlangt ist ein positiver Kurs. "
            "Ein negativer ist keiner, und 0 ist keine Angabe, sondern eine "
            "fehlende, die sich als Zahl ausgibt"
        )
    if bounds is not None:
        low, high = bounds
        if not low <= number <= high:
            raise FileProblem(
                f"{where} = {number} liegt außerhalb des deklarierten "
                f"Bereichs {low}..{high}"
            )
    return number


def _identity_of(entry: dict) -> object:
    """Baut die Identität eines Eintrags in ihrer Form.

    Jedes Feld läuft durch `_require_text`, **bevor** `identity_problem` es
    sieht: Eine Zahl in `ticker` warf sonst aus dem Konstruktor, weil dort
    jemand `.strip()` ruft.

    Raises:
        FileProblem: Die Form fehlt, ist unbekannt, oder ein Feld trägt keinen
            Text. Zu raten wäre hier besonders teuer: Aus einem `pair` ohne
            `kind` würde ein Listing ohne Handelsplatz, und das Papier landete
            unter falscher Identität im Bestand.
    """
    identity = entry.get("identity") or {}
    where = f"Eintrag {entry.get('id')!r}.identity"
    kind = _require_text(identity.get("kind"), f"{where}.kind")

    if kind == "listed":
        isin = identity.get("isin")
        return ListedIdentity(
            ticker=_require_text(identity.get("ticker"), f"{where}.ticker"),
            mic=_require_text(identity.get("mic"), f"{where}.mic"),
            isin=_require_text(isin, f"{where}.isin") if isin is not None else None,
        )
    if kind == "pair":
        return PairIdentity(
            base=_require_text(identity.get("base"), f"{where}.base"),
            quote_currency=_require_text(
                identity.get("quote_currency"), f"{where}.quote_currency"
            ),
        )
    if kind == "isin_only":
        return IsinOnlyIdentity(isin=_require_text(identity.get("isin"), f"{where}.isin"))
    raise FileProblem(
        f"{where}.kind ist {kind!r} — erlaubt sind listed, pair und isin_only"
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
        except UnicodeError as error:
            raise FileProblem(
                f"{path} ist nicht als UTF-8 lesbar: {error}"
            ) from error
        except yaml.YAMLError as error:
            raise FileProblem(f"{path} ist kein gültiges YAML: {error}") from error
        except ValueError as error:
            # Python bricht das Umwandeln sehr langer Ganzzahlen ab (Grenze
            # 4300 Stellen). Das ist ein Wert in der Datei, kein Fehler der
            # App — und gehört deshalb in dieselbe Meldung wie ein Syntaxfehler.
            raise FileProblem(f"{path} enthält einen unlesbaren Wert: {error}") from error

        if not isinstance(raw, dict):
            raise FileProblem(f"{path} enthält kein Objekt auf oberster Ebene")

        # **Die Formprüfung steht vor der Inhaltsprüfung**, und der Grund ist
        # gemessen: `instruments: {}` ließ den Konstruktor mit einem
        # `AttributeError` sterben. Der Betreiber las einen Stacktrace statt
        # der Zeile, die er ändern muss.
        _require_version(raw.get("version"))
        instruments = _require_list(raw.get("instruments"), "instruments")
        rates = _require_list(raw.get("fx_rates"), "fx_rates")

        self.by_isin: dict[str, dict] = {}
        self.by_symbol: dict[str, dict] = {}
        self.fx: dict[tuple[str, str], dict] = {}
        seen_ids: set[str] = set()

        for entry in instruments:
            self._add_instrument(entry, seen_ids)

        for rate in rates:
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
        entry_id = _require_text(entry.get("id"), "instruments[].id")
        where = f"Eintrag {entry_id!r}"
        if entry_id in seen_ids:
            raise FileProblem(
                f"die Kennung {entry_id!r} steht doppelt in der Datei — "
                "welcher der beiden Einträge gälte, wäre Zufall"
            )
        seen_ids.add(entry_id)

        _require_mapping(entry, "identity", where)
        identity = _identity_of(entry)
        problem = identity_problem(identity)
        if problem:
            raise FileProblem(f"{where}: {problem}")

        _require_text(entry.get("name"), f"{where}.name")
        instrument_type = _require_text(
            entry.get("instrument_type"), f"{where}.instrument_type"
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

        price = _require_mapping(entry, "price", where)
        if price:
            self._check_amount(price, f"{where}, price")

        metadata = _require_mapping(entry, "metadata", where)
        if metadata:
            self._check_metadata(metadata, where)

        history = _require_mapping(entry, "history", where)
        if history:
            _require_currency(history.get("currency"), f"{where}.history")
            self._check_closes(
                _require_list(history.get("closes"), f"{where}.history.closes"),
                where,
            )

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
        _require_currency(amount.get("currency"), where)
        _require_number(amount.get("value"), f"{where}.value", positive=True)
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
            if spec is None:
                continue
            if spec.kind != "number":
                _require_text(metadata[key], f"{where}.metadata.{key}")
                continue
            _require_number(
                metadata[key],
                f"{where}.metadata.{key}",
                bounds=spec.plausible or None,
            )

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
            day = _as_date(close.get("date"), f"{where}.history")
            if day in seen:
                raise FileProblem(
                    f"{where}: der {day.isoformat()} steht zweimal in der "
                    "History — zwei Werte für einen Tag sind kein Verlauf"
                )
            seen.add(day)
            _require_number(
                close.get("value"),
                f"{where}.history[{day.isoformat()}].value",
                positive=True,
            )

    def _add_rate(self, rate: dict) -> None:
        """Prüft einen Wechselkurs und legt ihn ab."""
        where = f"fx_rates {rate.get('base')!r}/{rate.get('quote')!r}"
        base = _require_text(rate.get("base"), f"{where}.base").upper()
        quote = _require_text(rate.get("quote"), f"{where}.quote").upper()
        for field, value in (("base", base), ("quote", quote)):
            problem = currency_problem(value)
            if problem:
                raise FileProblem(f"{where}: {field} {problem}")
        _require_number(rate.get("rate"), f"{where}.rate", positive=True)
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
    data_version = 1  # Increase only for incompatible changes to stored data.
    SUPPORTED_KINDS = frozenset({"listed", "pair", "isin_only"})
    SUPPORTED_TYPES = frozenset({"stock", "etf", "etc", "fund", "crypto", "bond"})

    FIELDS = (
        FieldSpec(
            "ter",
            kind="number",
            instrument_types=frozenset({"etf", "etc", "fund"}),
            unit=Unit.BASIS_POINTS,
            plausible=(0.5, 500.0),
            label_en="Total expense ratio (TER)",
            label_de="Gesamtkostenquote (TER)",
        ),
        FieldSpec(
            "provider", kind="text", instrument_types=frozenset({"etf", "etc", "fund"}), label_en="Fund provider", label_de="Anbieter"
        ),
        FieldSpec(
            "fund_domicile",
            kind="text", instrument_types=frozenset({"etf", "etc", "fund"}),
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

    cacheable = False
    """Eine gepflegte Datei kostet nichts und soll sofort wirken — ein
    Zwischenspeicher schützte hier kein Kontingent."""

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
        self._loaded: _Catalogue | None = None
        self._signature: tuple[int, int] | None = None
        self._reload()

    @property
    def _catalogue(self) -> "_Catalogue | None":
        """Der Katalog — nachgeladen, falls sich die Datei geändert hat.

        Eine Eigenschaft und keine sieben Aufrufe: Jede der fünf Rollen liest
        hierüber, und eine Regel, die an sieben Stellen wiederholt wird, fehlt
        beim achten Eintrittspunkt.

        **Während einer Störung liefert sie nichts.** Der letzte gültige
        Katalog bleibt für den atomaren Tausch erhalten; ihn als aktuellen Wert
        auszugeben hieße, einen Stand zu behaupten, den die Datei nicht trägt.
        """
        self._reload()
        return None if self._problem else self._loaded

    def _reload(self) -> None:
        """Liest die Datei neu, **wenn sie sich geändert hat**.

        Die Signatur ist `st_mtime_ns` und Größe: Ein `stat()` kostet Bruchteile
        einer Mikrosekunde, ein Katalogaufbau Millisekunden bis Sekunden.

        **Der Tausch ist atomar.** Der neue Katalog entsteht vollständig in
        einer lokalen Variablen; erst wenn er gültig ist, ersetzt er den alten.
        Nach der nächsten gültigen Fassung erholt sich dieselbe Instanz.
        """
        try:
            info = self._path.stat()
        except OSError as error:
            self._problem = f"{self._path} nicht lesbar: {error}"
            logger.warning("yaml-file: %s", self._problem)
            return
        signature = (info.st_mtime_ns, info.st_size)
        if signature == self._signature and self._loaded is not None and not self._problem:
            # **Ein offener Grund sperrt diese Abkürzung.** Dann ist die
            # Signatur kein Beleg mehr dafür, dass die Datei den geladenen
            # Stand trägt: Eine Korrektur kann gleich groß und gleich datiert
            # sein und trotzdem etwas anderes enthalten.
            return
        try:
            fresh = _Catalogue(self._path)
        except FileProblem as error:
            # Der Grund gehört ins Protokoll, nicht nur ins Feld: Eine Quelle,
            # die stumm ausfällt, ließe den Betreiber rätseln.
            #
            # Die Signatur wird trotzdem vermerkt — sonst versuchte jede
            # Anfrage denselben aussichtslosen Aufbau erneut. Die Erholung
            # blockiert das nicht: Die nächste gültige Fassung trägt eine
            # andere Signatur.
            # **Eine abgelehnte Signatur wird nicht gemerkt** — weder als
            # geladener Stand noch als Sperre: Beides schlösse eine gültige
            # Fassung aus, die zufällig dieselbe Größe und Zeit trägt. Der
            # Preis ist ein Zerlegeversuch je Anfrage; er scheitert früh.
            self._problem = str(error)
            logger.warning("yaml-file: %s", self._problem)
            return
        self._loaded = fresh
        self._signature = signature
        self._problem = ""

    def configuration_problem(self) -> str:
        """Warum diese Quelle nicht arbeiten kann — oder ``""``.

        Eine Quelle, die sich wegen einer kaputten Datei abschaltet und dazu
        schweigt, kostet den Betreiber den Nachmittag: Er sieht leere Listen
        und sucht den Fehler in der App.
        """
        self._reload()
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
        if base and base == quote and not currency_problem(base):
            # **Nur für eine echte Währung.** `ZZZ/ZZZ` ist keine Identität,
            # sondern ein Tippfehler; ihm 1.0 zu antworten hieße, einen Code
            # zu bestätigen, den ISO 4217 nicht vergibt.
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
        history = entry.get("history") or {}
        if not history:
            # Kein gepflegter Verlauf — dazu gibt es nichts zu sagen, auch
            # keine leere Reihe: Die trüge eine Währung, die niemand genannt
            # hat.
            return NotFound()

        bars = [
            DailyBar(day=day, close=float(close["value"]))
            for close in _closes(entry)
            for day in (_as_date(close["date"]),)
            if (request.start is None or day >= request.start)
            and (request.end is None or day <= request.end)
        ]
        # **Leer ist nicht dasselbe wie unbekannt.** Ein bekanntes Papier ohne
        # Punkte im angefragten Fenster hat einen Verlauf — nur nicht dort.
        # `NotFound` hieße „dieses Papier kenne ich nicht" und schickte den
        # Aufrufer eine Quelle weiter, die es auch nicht besser weiß.
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
