"""Der Identitäts-Umzug des Bestands — was er täte, bevor er es tut.

Dieses Modul **rechnet vor**. Es ändert nichts. Das ist der ganze Zweck: Seit
der Entscheidung nach Runde 16 darf eine nicht auflösbare Altzeile nirgends
als halbe Identität weiterleben, und was nicht migriert werden kann, verlässt
den gültigen Bestand. Ein solcher Schritt darf dem Benutzer nicht als
Überraschung beim nächsten Start begegnen — er muss ihn vorher sehen,
mitsamt dem Preis in Kurspunkten.

`init_db()` läuft im FastAPI-Lifespan, also **bevor** die App den ersten
Request bedient (`app/main.py`). Ein UI, das erst danach erreichbar wird, kann
niemanden mehr warnen. Deshalb trennt Teil 2 das Erkennen vom Ausführen, und
die Vorschau hier ist die Hälfte, die ohne jede Schreiboperation auskommt.
"""

import sqlite3
from dataclasses import dataclass

import structlog

# Die Ablehnungsgründe stehen seit T-21 Übergabe 3 in `app.exchanges` — bei der
# Regel, nicht bei einem ihrer Aufrufer, seit der Aufnahmeweg dieselben drei
# Fälle beantwortet. Werte und Namen sind unverändert, damit Ticket, REST-
# Bericht und die i18n-Schlüssel des Dashboards nichts merken.
from app.exchanges import (
    REASON_NO_SUFFIX,
    REASON_NON_CANONICAL_TICKER,
    REASON_UNKNOWN_SUFFIX,
    REJECTION_REASONS,  # noqa: F401  — weitergereicht an den Katalogtest
    identity_from_symbol,
    is_real_mic,
    mic_for_alias,
)

logger = structlog.get_logger()

IDENTITY_CHECK = """CHECK (
        (kind = 'listed'
            AND ticker IS NOT NULL AND mic IS NOT NULL
            AND base IS NULL AND quote_currency IS NULL)
     OR (kind = 'pair'
            AND base IS NOT NULL AND quote_currency IS NOT NULL
            AND ticker IS NULL AND mic IS NULL AND isin IS NULL)
     OR (kind = 'isin_only'
            AND isin IS NOT NULL
            AND ticker IS NULL AND mic IS NULL
            AND base IS NULL AND quote_currency IS NULL)
    )"""
"""Die Formregel der Identität — **eine** Fassung, zwei Verwender.

Sie steht im frischen Schema und im Tabellen-Neuaufbau des Umzugs. Zwei
abgeschriebene Fassungen liefen beim ersten Zusatzfeld auseinander, und die
Folge waere ein Bestand, dessen Zusage davon abhinge, auf welchem Weg er
entstanden ist.

Je Form verlangend **und** ausschliessend: Ein `CHECK`, der bloss die
Pflichtfelder der eigenen Form fordert, liesse eine `listed`-Zeile mit
zusaetzlichem `base` zu — eine Zeile mit zwei Identitaeten.
"""




# Der Berichtsspeicher. **Eine** Tabelle, nicht zwei.
#
# Der Entwurf nennt „Quarantäne" und „Berichtsspeicher" nebeneinander. Beide
# beantworten aber dieselbe Frage — *welche Zeile ist warum gegangen, und was
# hing daran* —, und der Bericht braucht dieselben Felder, die die Quarantäne
# hält. Zwei Tabellen wären dieselbe Auskunft an zwei Orten, die beim ersten
# zusätzlichen Feld auseinanderlaufen.
#
# Gehalten wird, was zur **Neuerfassung von Hand** reicht: Symbol, ISIN, Name,
# Börse, Gattung, Währung. Für die vollständige Wiederherstellung ist der
# SQLite-Snapshot zuständig, nicht diese Tabelle — sonst gäbe es zwei
# Rettungswege, von denen einer nur so tut.
#
# **Eine** Anweisung, kein Script. `executescript` setzt vor dem Ausführen ein
# COMMIT ab — dokumentiertes `sqlite3`-Verhalten. Innerhalb des Umzugs hätte
# das die offene Transaktion beendet, und „alles oder nichts" wäre eine
# Zusage ohne Deckung gewesen. Ein Test hat es gezeigt, kein Review.
REJECTIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS migration_rejections (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol        TEXT NOT NULL,
    isin          TEXT,
    name          TEXT,
    exchange      TEXT,
    type          TEXT,
    currency      TEXT,
    reason        TEXT NOT NULL,
    quotes        INTEGER NOT NULL,
    daily_closes  INTEGER NOT NULL,
    rejected_at   TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class Rejection:
    """Eine Zeile, die den gültigen Bestand verlässt — samt Preis.

    `quotes` und `daily_closes` stehen **getrennt** da, weil sie verschiedene
    Dinge sind: die Intraday-Zeitreihe und die Tagesschlusskurse. Der reale
    Fall aus der Messung hängt an den Tagesschlüssen — `GOLD.SG` trägt 257
    davon —, und eine einzige Summe hätte das verwischt.
    """

    instrument_id: int
    symbol: str
    isin: str | None
    name: str | None
    exchange: str | None
    type: str | None
    currency: str | None
    reason: str
    quotes: int
    daily_closes: int


@dataclass(frozen=True)
class Migration:
    """Eine Zeile, die ihre kanonische Identität bekommt."""

    instrument_id: int
    symbol: str
    ticker: str
    mic: str


@dataclass(frozen=True)
class MigrationPlan:
    """Was ein Lauf tun **würde** — ohne dass etwas geschehen ist.

    `unchanged` zählt die Zeilen, die ihre Identität schon tragen. Sie stehen
    hier, damit die Vorschau eine vollständige Bilanz zeigt: Ohne sie könnte
    der Benutzer nicht sehen, dass die genannten Zeilen *alle* betroffenen
    sind.
    """

    migrated: tuple[Migration, ...]
    rejected: tuple[Rejection, ...]
    unchanged: int
    schema_outdated: bool = False

    @property
    def needs_migration(self) -> bool:
        """Ist überhaupt etwas zu tun — an Zeilen **oder** am Schema?

        **Der Schemazustand gehört dazu, und das war ein Fehler.** Bis Runde 30
        zählte nur die Zeilenarbeit. Damit galt eine **leere** Pre-T-21-Datenbank
        als fertig, obwohl `ticker`, `mic` und `listing_id` ganz fehlten — die
        nächste Neuanlage wäre an den fehlenden Spalten gebrochen. Und ein
        bereits vollständig zugeordneter Bestand aus Teil 1 galt ebenfalls als
        fertig, obwohl die Spalten nullable blieben und `identity_status` noch
        stand: Die zugesagte Invariante war schlicht falsch.
        """
        return bool(self.migrated or self.rejected) or self.schema_outdated

    @property
    def needs_confirmation(self) -> bool:
        """Muss der Benutzer zustimmen — weil etwas **verloren** geht?

        Nur dann. Ein verlustloser Umzug — nichts abzulehnen, nur Spalten und
        Zuordnungen nachzuziehen — darf beim Start durchlaufen: Es gibt nichts
        zu warnen, und eine Bestätigung für nichts wäre bloß eine Hürde.

        Die Zustimmung schützt vor **Datenverlust**, nicht vor Schemaarbeit.
        """
        return bool(self.rejected)

    @property
    def lost_daily_closes(self) -> int:
        """Tagesschlusskurse, die mit den abgelehnten Zeilen verschwinden."""
        return sum(rejection.daily_closes for rejection in self.rejected)

    @property
    def lost_quotes(self) -> int:
        """Intraday-Kurspunkte, die mit den abgelehnten Zeilen verschwinden."""
        return sum(rejection.quotes for rejection in self.rejected)


def rejection_reason(symbol: str) -> str | None:
    """Warum lässt sich aus diesem Symbol keine Identität gewinnen?

    ``None`` heißt: **doch**, die Zeile migriert. Die Funktion ist damit das
    genaue Gegenstück zu `identity_of` — genau eine der beiden liefert ein
    Ergebnis, nie beide und nie keine. Gäbe sie auch für `EUNL.DE` einen Grund
    zurück, könnte ein Aufrufer eine migrierende Zeile mit einer Ablehnung
    beschriften, ohne dass der Typ ihn daran hindert.

    Die drei Gründe sind die drei Wege, auf denen die Zerlegung scheitert —
    hier aber **eigens formuliert**, nicht aus einem `(None, None)`
    zurückgeraten. Ein Grund, der nur „die andere Funktion sagt nein"
    bedeutet, sagt dem Benutzer nichts.

    Args:
        symbol: Das gespeicherte Listing-Symbol, etwa ``'VTI'``.

    Returns:
        Eine der Kennungen aus `REJECTION_REASONS`, oder ``None`` wenn die
        Zeile migriert.
    """
    if identity_of(symbol) is not None:
        return None

    if not symbol or "." not in symbol:
        # `VTI`, `AAPL`: Suffixlos notiert bei Yahoo genau ein Markt, die USA
        # — und dort führt die Tabelle nur den Sammelcode `US`. Welcher der
        # fünf Handelsplätze gemeint ist, weiß das Symbol nicht.
        return REASON_NO_SUFFIX

    ticker, _, alias = symbol.partition(".")
    if mic_for_alias(alias) is None:
        # `FOO.ZZ`: Ein Suffix, das der Katalog nicht führt. Es an einen MIC
        # zu binden, ohne die Börse aufzunehmen, hinge in der Luft.
        return REASON_UNKNOWN_SUFFIX

    # Die Börse steht fest, der Ticker nicht: `BRK-B.DE`, `RDS-A.L`. Der
    # Bindestrich ist Yahoos Zeichensetzung, nicht die der Börse, und ihn
    # umzuschreiben wäre geraten.
    return REASON_NON_CANONICAL_TICKER


# Die Zerlegungsregel steht in `app.exchanges` — **einmal**.
#
# Hier stand bis Runde 30 eine eigene, gleich aussehende Implementierung: Punkt
# prüfen, `partition`, `mic_for_alias`, `is_canonical_ticker`. Nur die
# Fehlerform unterschied sich. Zwei Implementierungen derselben Fachregel
# laufen beim ersten neuen Fall auseinander, und dann entscheidet der Umzug
# anders als der übrige Core — über die Identität von Papieren.
identity_of = identity_from_symbol


def keeps_its_identity(ticker: str | None, mic: str | None) -> bool:
    """Trägt diese Zeile bereits eine **vollständige** kanonische Identität?

    Entschieden wird nach den Daten. Vollständig heißt: ein Ticker **und** ein
    echter MIC. Der Sammelcode `US` zählt nicht — er ist ein interner
    Suchcode und darf im kanonischen Feld nie stehen; eine Zeile, die ihn
    trägt, wird deshalb neu bewertet statt durchgewunken.

    Args:
        ticker: Der gespeicherte Ticker.
        mic: Der gespeicherte MIC.

    Returns:
        ``True``, wenn die Zeile so bleiben darf, wie sie ist.
    """
    return bool(ticker) and is_real_mic(mic)


def plan_migration(connection: sqlite3.Connection) -> MigrationPlan:
    """Rechnet vor, was ein Lauf täte — **ohne** eine einzige Schreiboperation.

    Das ist Phase 1 des zweiphasigen Ablaufs. Der Benutzer bekommt die Liste
    der Zeilen, die den Bestand verlassen, mit Grund und Preis; erst seine
    Bestätigung löst `apply_migration` aus.

    **Zeilen mit gültiger Identität werden nicht neu bewertet.** Eine von Hand
    gesetzte Zuordnung wie ``AAPL``/``XNAS`` überlebt den Umzug, obwohl sich
    ihr Symbol nicht zerlegen lässt — sonst nähme die Migration genau die
    Arbeit zurück, die jemand vorher hineingesteckt hat.

    Args:
        connection: Offene Verbindung; wird nur gelesen.

    Returns:
        Der Plan. `needs_migration` sagt, ob etwas zu tun ist; `needs_confirmation`, ob dabei etwas verloren geht.
    """
    migrated: list[Migration] = []
    rejected: list[Rejection] = []
    unchanged = 0

    # **Die Identitätsspalten müssen es noch gar nicht geben.** Auf einer
    # Datenbank, die noch nie umgezogen ist, fehlen `ticker` und `mic` — und
    # sie hier anzulegen wäre bereits eine Schemaänderung. Phase 1 ändert
    # nichts, also fragt sie erst, was da ist, statt es sich zurechtzulegen.
    has_identity = _has_identity_columns(connection)
    # Name, Börse, Gattung und Währung stehen **hier** und nicht erst beim
    # Löschen: Der Benutzer soll in der Vorschau sehen, welches Papier er neu
    # erfassen muss — und ein Symbol allein sagt ihm das nicht. Bis Runde 30
    # holte der Plan sie nicht, und der Bericht bekam sie deshalb nur aus der
    # Tabelle; über REST kamen sie nie an.
    columns = (
        "id, symbol, isin, name, exchange, type, currency"
        + (", ticker, mic" if has_identity else "")
    )

    for row in connection.execute(
        f"SELECT {columns} FROM instruments ORDER BY symbol"
    ).fetchall():
        if has_identity and keeps_its_identity(row["ticker"], row["mic"]):
            unchanged += 1
            continue

        identity = identity_of(row["symbol"])
        if identity is not None:
            ticker, mic = identity
            migrated.append(
                Migration(
                    instrument_id=row["id"],
                    symbol=row["symbol"],
                    ticker=ticker,
                    mic=mic,
                )
            )
            continue

        reason = rejection_reason(row["symbol"])
        assert reason is not None  # `identity_of` hat gerade `None` gesagt.
        rejected.append(
            Rejection(
                instrument_id=row["id"],
                symbol=row["symbol"],
                isin=row["isin"],
                name=row["name"],
                exchange=row["exchange"],
                type=row["type"],
                currency=row["currency"],
                reason=reason,
                quotes=_count_rows(connection, "quotes", row["id"]),
                daily_closes=_count_rows(connection, "daily_closes", row["id"]),
            )
        )

    return MigrationPlan(
        migrated=tuple(migrated),
        rejected=tuple(rejected),
        unchanged=unchanged,
        schema_outdated=schema_outdated(connection),
    )


def schema_outdated(connection: sqlite3.Connection) -> bool:
    """Trägt `instruments` noch **nicht** die Zielform?

    Drei Dinge machen die Zielform aus, und jedes einzelne fehlt für sich
    genommen:

    * die Spalten der Identität — seit T-31 auch `kind`, `base` und
      `quote_currency`, dazu `listing_id`,
    * der `CHECK` je `kind`, der die Belegung je Form erzwingt,
    * das **Fehlen** von `identity_status`.

    **`NOT NULL` auf `ticker`/`mic` stand hier bis T-31 und ist der Grund für
    einen P0.** Es war die richtige Invariante, solange es nur Listings gab;
    seit die Identität drei Formen hat, ist es die falsche — eine Coin hat
    keinen Ticker. Ein Frischstart auf dem neuen `_SCHEMA` galt damit als
    „veraltet", und der anschließende Umbau härtete die Spalten zurück und
    warf den `CHECK` weg. Ergebnis: Eine frische Datenbank konnte keine
    Paar-Zeile aufnehmen, und keiner der 828 Tests merkte es, weil alle nur
    Listings anlegten.

    Was die Form heute ausmacht, steht deshalb im `CHECK` und wird auch dort
    abgefragt.

    Gefragt wird `PRAGMA table_info`, nicht der Zeilenbestand: Eine leere
    Datenbank hat keine Zeile, die etwas verrät, und genau sie war der Fall,
    der bis Runde 30 durchrutschte.

    Args:
        connection: Offene Verbindung; wird nur gelesen.

    Returns:
        ``True``, wenn am Schema noch etwas zu tun ist.
    """
    columns = {
        row["name"]: row for row in connection.execute("PRAGMA table_info(instruments)")
    }
    if not IDENTITY_COLUMNS <= set(columns):
        return True
    if "identity_status" in columns:
        return True
    return not _has_identity_check(connection)


# Die Spalten, die die Identität in ihren drei Formen ausmacht (T-31).
IDENTITY_COLUMNS = frozenset(
    {"kind", "ticker", "mic", "base", "quote_currency", "listing_id"}
)


def _has_identity_check(connection: sqlite3.Connection) -> bool:
    """Trägt die Tabelle den `CHECK`, der die Form erzwingt?

    Am Tabellen-DDL abgelesen und nicht an einer Spaltenliste: `PRAGMA
    table_info` kennt `CHECK` nicht, und ein `PRAGMA integrity_check` sagt
    etwas über die Daten, nicht über die Zusage.
    """
    row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'instruments'"
    ).fetchone()
    return bool(row) and "kind = 'listed'" in (row["sql"] or "")


def _has_identity_columns(connection: sqlite3.Connection) -> bool:
    """Trägt `instruments` die Identitätsspalten schon?

    Auf einer Datenbank, die den Umzug noch vor sich hat, fehlen sie. Die
    Vorschau darf sie **nicht** anlegen, um sie lesen zu können — sonst hätte
    Phase 1 die Datenbank angefasst, und die Zusage „es wird nichts verändert"
    wäre schon gebrochen, bevor der Benutzer die Liste gesehen hat.

    Args:
        connection: Offene Verbindung; wird nur gelesen.

    Returns:
        ``True``, wenn `ticker` **und** `mic` existieren.
    """
    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(instruments)")
    }
    return {"ticker", "mic"} <= columns


def _count_rows(
    connection: sqlite3.Connection, table: str, instrument_id: int
) -> int:
    """Zählt die Kurszeilen eines Instruments in genau einer Tabelle.

    Der Tabellenname wird interpoliert, weil SQLite ihn nicht als Parameter
    zulässt. Er kommt aus **keiner** Eingabe — die beiden Aufrufstellen oben
    übergeben Literale —, und genau deshalb steht dieser Satz hier: Sobald
    jemand den Namen von außen hereinreicht, ist die Zeile eine Injektion.

    Args:
        connection: Offene Verbindung; wird nur gelesen.
        table: ``'quotes'`` oder ``'daily_closes'``.
        instrument_id: Die Zeile, deren Kurspunkte gezählt werden.

    Returns:
        Die Anzahl.
    """
    if table not in {"quotes", "daily_closes"}:
        raise ValueError(f"unbekannte Kurstabelle: {table}")
    return connection.execute(
        f"SELECT COUNT(*) FROM {table} WHERE instrument_id = ?", (instrument_id,)
    ).fetchone()[0]


# Die Kindtabellen eines Instruments. Sie stehen hier als **eine** Liste,
# damit das Löschen einer abgelehnten Zeile keine vergisst.
#
# Verlassen wird sich dabei **nicht** auf `ON DELETE CASCADE`: Der
# Tabellen-Neuaufbau weiter unten läuft mit abgeschalteten Fremdschlüsseln,
# und eine Kaskade, die mal greift und mal nicht, ist keine Zusage. Gelöscht
# wird ausdrücklich — und gezählt wird dabei auch.
_CHILD_TABLES = ("quotes", "daily_closes", "daily_meta", "instrument_overrides")


def apply_migration(
    connection: sqlite3.Connection, rejected_at: str
) -> MigrationPlan:
    """Führt den Umzug aus — **alles oder nichts**, in einer Transaktion.

    Phase 2 des zweiphasigen Ablaufs, ausgelöst allein durch die Bestätigung
    des Benutzers. Die Reihenfolge ist nicht beliebig:

    1. **Erst der Bericht, dann die Löschung.** Beide in derselben
       Transaktion — sonst könnte ein Abbruch dazwischen eine Zeile entfernen,
       deren Verschwinden danach niemand mehr erklären kann. Genau das
       verlangt `#2b4`.
    2. **Dann die Identitäten.** Was migriert, bekommt `(ticker, mic)`.

    Das **Schema** härtet danach `harden_identity_schema` — getrennt, weil
    der Tabellen-Neuaufbau abgeschaltete Fremdschlüssel braucht und die
    Reihenfolge damit am Aufrufer hängt, nicht hier drinnen.

    Der Aufrufer verantwortet Transaktion und `PRAGMA foreign_keys` — beides
    lässt sich nicht sinnvoll hier drinnen setzen, weil SQLite das PRAGMA
    innerhalb einer Transaktion ignoriert.

    Args:
        connection: Offene Verbindung innerhalb der Transaktion.
        rejected_at: Zeitstempel für die Berichtseinträge (ISO-8601).

    Returns:
        Der ausgeführte Plan — dieselbe Bilanz, die die Vorschau gezeigt hat.
    """
    plan = plan_migration(connection)
    connection.execute(REJECTIONS_SCHEMA)

    for rejection in plan.rejected:
        _record_rejection(connection, rejection, rejected_at)
        _delete_instrument(connection, rejection.instrument_id)

    _ensure_identity_columns(connection)
    for migration in plan.migrated:
        connection.execute(
            "UPDATE instruments SET ticker = ?, mic = ? WHERE id = ?",
            (migration.ticker, migration.mic, migration.instrument_id),
        )

    logger.info(
        "migration_applied",
        migrated=len(plan.migrated),
        rejected=len(plan.rejected),
        unchanged=plan.unchanged,
        lost_quotes=plan.lost_quotes,
        lost_daily_closes=plan.lost_daily_closes,
    )
    return plan


def _record_rejection(
    connection: sqlite3.Connection, rejection: Rejection, rejected_at: str
) -> None:
    """Schreibt den Berichtseintrag, **bevor** die Zeile verschwindet.

    Die Metadaten kommen aus dem Plan, der sie beim Lesen mitgenommen hat —
    nach dem Löschen sind sie weg, und ein Bericht, der nur „irgendein Symbol"
    nennt, hilft bei der Neuerfassung nicht. Sie hier ein zweites Mal aus der
    Datenbank zu holen wäre dieselbe Abfrage zweimal, und die Vorschau bekäme
    sie trotzdem nicht.

    Args:
        connection: Offene Verbindung innerhalb der Transaktion.
        rejection: Der Eintrag aus dem Plan.
        rejected_at: Zeitstempel (ISO-8601).
    """
    connection.execute(
        "INSERT INTO migration_rejections "
        "(symbol, isin, name, exchange, type, currency, reason, quotes, "
        " daily_closes, rejected_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            rejection.symbol,
            rejection.isin,
            rejection.name,
            rejection.exchange,
            rejection.type,
            rejection.currency,
            rejection.reason,
            rejection.quotes,
            rejection.daily_closes,
            rejected_at,
        ),
    )


def _delete_instrument(connection: sqlite3.Connection, instrument_id: int) -> None:
    """Entfernt ein Instrument samt allem, was daran hängt.

    Ausdrücklich statt über die Kaskade — siehe `_CHILD_TABLES`.

    Args:
        connection: Offene Verbindung innerhalb der Transaktion.
        instrument_id: Die Zeile, die geht.
    """
    for table in _CHILD_TABLES:
        if _table_exists(connection, table):
            connection.execute(
                f"DELETE FROM {table} WHERE instrument_id = ?", (instrument_id,)
            )
    connection.execute("DELETE FROM instruments WHERE id = ?", (instrument_id,))


def _ensure_identity_columns(connection: sqlite3.Connection) -> None:
    """Legt die Identitätsspalten an, falls sie fehlen.

    Erst hier und nicht in der Vorschau: Eine Spalte anzulegen ist bereits
    eine Änderung, und Phase 1 verspricht, keine zu machen.

    **`kind`, `base` und `quote_currency` kommen seit T-31 dazu**, und zwar
    vor dem Tabellen-Neuaufbau: Der `IDENTITY_CHECK` nennt sie, und eine
    Tabelle, die auf eine fehlende Spalte prüft, lässt sich nicht anlegen.

    `kind` bekommt `'listed'` als Vorgabewert — jede Altzeile **ist** ein
    Listing, denn die beiden anderen Formen gab es vor T-31 nicht. Das ist
    kein Raten, sondern die einzige Möglichkeit.

    Args:
        connection: Offene Verbindung innerhalb der Transaktion.
    """
    existing = {
        row["name"] for row in connection.execute("PRAGMA table_info(instruments)")
    }
    for column in ("ticker", "mic", "listing_id", "base", "quote_currency"):
        if column not in existing:
            connection.execute(f"ALTER TABLE instruments ADD COLUMN {column} TEXT")
    if "kind" not in existing:
        connection.execute(
            "ALTER TABLE instruments ADD COLUMN kind TEXT NOT NULL DEFAULT 'listed'"
        )


def harden_identity_schema(connection: sqlite3.Connection) -> None:
    """Setzt die Formregel ins Schema und entfernt `identity_status`.

    **Der Punkt ohne Wiederkehr.** Danach kann keine halbe Identität mehr
    entstehen — nicht durch einen Programmierfehler, nicht durch einen
    Endpunkt, den jemand übersehen hat. Die Invariante aus `#2b2` steht damit
    im Schema und nicht in einer Prüfung, die man vergessen kann.

    **Seit T-31 ist die Invariante der `CHECK` je `kind`, nicht `NOT NULL`.**
    Eine Coin hat keinen Ticker; die alte Fassung machte die neuen Formen
    unspeicherbar und war der P0 aus Runde 4.

    SQLite kann eine Spalte nicht nachträglich auf `NOT NULL` setzen; die
    Tabelle wird deshalb neu gebaut und umkopiert. Die Spaltenliste entsteht
    aus dem **realen** Bestand der Tabelle, nicht aus einer abgeschriebenen
    Aufzählung: Welche Metadatenspalten eine gewachsene Installation trägt,
    weiß nur sie selbst, und eine Kopie hier wäre eine zweite Wahrheit, die
    beim nächsten `_add_missing_columns` driftet.

    `identity_status` fällt beim Umkopieren weg — die Spalte trüge nur noch
    einen einzigen Wert, und die beste Zahl an Quellen für einen Wert, den es
    nicht mehr gibt, ist null.

    Args:
        connection: Offene Verbindung innerhalb der Transaktion, mit
            **abgeschalteten** Fremdschlüsseln.
    """
    columns = [
        row for row in connection.execute("PRAGMA table_info(instruments)")
        if row["name"] != "identity_status"
    ]
    if not any(column["name"] == "ticker" for column in columns):
        raise RuntimeError("harden_identity_schema vor _ensure_identity_columns")

    definitions = ", ".join(_column_definition(column) for column in columns)
    names = ", ".join(column["name"] for column in columns)
    # **Die Formregel kommt mit, sonst faellt sie beim Umbau weg.** Genau das
    # war der P0 aus Runde 4: Die neue Tabelle entstand ohne `CHECK`, und eine
    # frische Installation konnte danach keine Paar-Zeile mehr aufnehmen.
    definitions += f", {IDENTITY_CHECK}"

    connection.execute("DROP TABLE IF EXISTS instruments_hardened")
    connection.execute(f"CREATE TABLE instruments_hardened ({definitions})")
    connection.execute(
        f"INSERT INTO instruments_hardened ({names}) SELECT {names} FROM instruments"
    )
    connection.execute("DROP TABLE instruments")
    connection.execute("ALTER TABLE instruments_hardened RENAME TO instruments")


def _column_definition(column: sqlite3.Row) -> str:
    """Baut die DDL einer Spalte für die gehärtete Tabelle nach.

    **`ticker` und `mic` bekommen ihr `NOT NULL` seit T-31 nicht mehr.** Es war
    die richtige Invariante, solange es nur Listings gab; eine Coin hat keinen
    Ticker. Was „vollstaendig" heisst, sagt jetzt `IDENTITY_CHECK` je Form.
    Alles andere behaelt, was es hatte: Typ, `NOT NULL`, `PRIMARY KEY` und
    Vorgabewert.

    ``UNIQUE`` steht **nicht** hier: SQLite führt es als eigenen Index, nicht
    als Spalteneigenschaft, und `PRAGMA table_info` nennt es gar nicht. Die
    Eindeutigkeit von `isin`, `(ticker, mic)` und `listing_id` wird deshalb
    nach dem Umbau als Index neu gesetzt — dort, wo sie ohnehin steht.

    Args:
        column: Eine Zeile aus `PRAGMA table_info`.

    Returns:
        Das DDL-Fragment, etwa ``'ticker TEXT NOT NULL'``.
    """
    parts = [column["name"], column["type"] or "TEXT"]
    if column["pk"]:
        parts.append("PRIMARY KEY AUTOINCREMENT")
    elif column["notnull"]:
        parts.append("NOT NULL")
    if column["dflt_value"] is not None:
        parts.append(f"DEFAULT {column['dflt_value']}")
    return " ".join(parts)


def _table_exists(connection: sqlite3.Connection, table: str) -> bool:
    """Gibt es diese Tabelle?

    Eine Alt-Datenbank kennt nicht jede Kindtabelle — `daily_meta` und
    `instrument_overrides` kamen später dazu. Ohne diese Frage bräche der
    Umzug an einem Bestand, der alt genug ist, um ihn nötig zu haben.

    Args:
        connection: Offene Verbindung.
        table: Tabellenname.

    Returns:
        ``True``, wenn die Tabelle existiert.
    """
    return (
        connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
        ).fetchone()
        is not None
    )
