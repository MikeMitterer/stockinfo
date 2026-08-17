# ETF-Extras nachtragen + aufklappbare Zeile — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Alle acht ETF-Kennzahlen von Hand nachtragbar machen und die Pflege in eine aufklappbare Zeile verlegen, damit auch Papiere ohne justETF-Quelle vollständig gepflegt werden können.

**Architecture:** `instrument_overrides` wächst von drei auf acht Spalten; `OVERRIDE_FIELDS` in `app/models.py` ist die einzige Feldliste und treibt Repository, Vorrang-Regel, Endpoint und Tests. Im Frontend wird `ManualMetric.vue` in `MetricValue` (zeigen) und `MetricEditor` (pflegen) geteilt; die Tabelle wird lesend, gepflegt wird in `InstrumentDrilldown`.

**Tech Stack:** Python 3.11, FastAPI, Pydantic v2, SQLite · Vue 3 (script setup), TypeScript, Naive UI, vue-i18n, Vitest, pytest

**Spec:** `docs/superpowers/specs/2026-08-17-etf-extras-nachtragen-und-schublade-design.md`

## Global Constraints

- **Alle Bezeichner im Code englisch, alle Kommentare und Doku deutsch.** Testnamen deutsch (`def test_...` mit deutschem Namen), wie im Bestand.
- **`OVERRIDE_FIELDS` ist die einzige Feldliste.** Keine zweite Aufzählung der acht Felder irgendwo — weder in SQL, noch im Endpoint, noch in Tests.
- **Kein sichtbarer Text ohne Katalog-Eintrag** (`de.ts` **und** `en.ts`).
- **Vorrang-Regel unverändert:** Was die Quelle liefert, gewinnt; ein manueller Wert füllt nur Lücken. `accumulating` prüft auf `None`, nicht auf Falschheit.
- **Migrationen idempotent** — `CREATE TABLE IF NOT EXISTS` plus `ALTER TABLE ADD COLUMN` nur, wenn die Spalte fehlt.
- **Testbefehle:** Backend `.venv/bin/python -m pytest -q`, Frontend `cd dashboard && npx vitest run`, Typecheck `cd dashboard && npx vue-tsc -b`, Lint `.venv/bin/python -m ruff check app tests`.
- **Commits** nach `git-conventions`: `<type>(<scope>): <subject>`, Imperativ, ≤ 72 Zeichen, deutscher Body.

---

### Task 1: Schema und Migration

**Files:**
- Modify: `app/db.py` (Block `instrument_overrides` in `_SCHEMA`, Funktion `_migrate`)
- Test: `tests/test_repository.py`

**Interfaces:**
- Consumes: nichts
- Produces: Spalten `instruments.fund_domicile TEXT`, `instruments.fund_currency TEXT`, sowie `instrument_overrides.provider TEXT`, `.replication TEXT`, `.fund_size REAL`, `.fund_domicile TEXT`, `.fund_currency TEXT`

- [ ] **Step 1: Write the failing test**

In `tests/test_repository.py` anhängen:

```python
def test_migration_ergaenzt_die_neuen_spalten(tmp_path) -> None:
    """Bestehende Datenbanken ziehen beim Start nach — ohne Zutun.

    Nachgestellt wird eine DB im alten Stand: beide Tabellen ohne die neuen
    Spalten. `init_db` muss sie ergaenzen, und ein zweiter Lauf darf nicht
    daran scheitern, dass sie schon da sind.
    """
    import sqlite3

    from app.db import init_db

    pfad = str(tmp_path / "alt.db")
    with sqlite3.connect(pfad) as verbindung:
        verbindung.executescript(
            """
            CREATE TABLE instruments (
                id INTEGER PRIMARY KEY, isin TEXT, symbol TEXT NOT NULL,
                exchange TEXT, name TEXT, type TEXT, currency TEXT,
                provider TEXT, ter REAL, replication TEXT, fund_size REAL,
                meta_fetched_at TEXT
            );
            CREATE TABLE instrument_overrides (
                instrument_id INTEGER PRIMARY KEY,
                ter REAL, volatility REAL, accumulating INTEGER,
                updated_at TEXT NOT NULL
            );
            """
        )

    init_db(pfad)
    init_db(pfad)  # zweimal: die Migration muss idempotent sein

    with sqlite3.connect(pfad) as verbindung:
        verbindung.row_factory = sqlite3.Row
        instrumente = {r["name"] for r in verbindung.execute("PRAGMA table_info(instruments)")}
        overrides = {
            r["name"] for r in verbindung.execute("PRAGMA table_info(instrument_overrides)")
        }

    assert {"fund_domicile", "fund_currency"} <= instrumente
    assert {"provider", "replication", "fund_size", "fund_domicile", "fund_currency"} <= overrides
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_repository.py::test_migration_ergaenzt_die_neuen_spalten -v`
Expected: FAIL — `assert {'fund_domicile', 'fund_currency'} <= {...}` ist falsch, die Spalten fehlen.

- [ ] **Step 3: Write minimal implementation**

In `app/db.py`, im `_SCHEMA`-Block `instrument_overrides` die fünf Spalten ergänzen (für frische Datenbanken):

```sql
CREATE TABLE IF NOT EXISTS instrument_overrides (
    instrument_id INTEGER PRIMARY KEY REFERENCES instruments(id) ON DELETE CASCADE,
    ter           REAL,
    volatility    REAL,
    accumulating  INTEGER,
    provider      TEXT,
    replication   TEXT,
    fund_size     REAL,
    fund_domicile TEXT,
    fund_currency TEXT,
    updated_at    TEXT NOT NULL
);
```

Im `_SCHEMA`-Block `instruments` zusätzlich `fund_domicile TEXT,` und `fund_currency TEXT,` aufnehmen.

`_migrate` auf beide Tabellen ziehen — die Schleife stand bisher nur für `instruments`:

```python
def _migrate(connection: sqlite3.Connection) -> None:
    """Ergänzt fehlende Spalten/Indizes in bestehenden Datenbanken (idempotent)."""
    _ergaenze_spalten(
        connection,
        "instruments",
        (
            ("volatility", "REAL"),
            ("accumulating", "INTEGER"),
            ("fund_domicile", "TEXT"),
            ("fund_currency", "TEXT"),
        ),
    )
    # Die Override-Tabelle wuchs mit: Nachgetragen wird jetzt alles, was
    # justETF beisteuert — nicht mehr nur die drei aus T-09.
    _ergaenze_spalten(
        connection,
        "instrument_overrides",
        (
            ("provider", "TEXT"),
            ("replication", "TEXT"),
            ("fund_size", "REAL"),
            ("fund_domicile", "TEXT"),
            ("fund_currency", "TEXT"),
        ),
    )

    # Vor dem UNIQUE-Index Alt-Duplikate zusammenführen — sonst schlägt die
    # Index-Erstellung auf bestehenden Datenbanken fehl.
    _dedupe_symbols(connection)
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_instruments_symbol "
        "ON instruments (symbol)"
    )


def _ergaenze_spalten(
    connection: sqlite3.Connection, tabelle: str, spalten: tuple[tuple[str, str], ...]
) -> None:
    """Fügt fehlende Spalten hinzu; vorhandene bleiben unangetastet."""
    vorhanden = {row["name"] for row in connection.execute(f"PRAGMA table_info({tabelle})")}
    for name, typ in spalten:
        if name not in vorhanden:
            connection.execute(f"ALTER TABLE {tabelle} ADD COLUMN {name} {typ}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_repository.py -q`
Expected: PASS, alle bisherigen Repository-Tests weiterhin grün.

- [ ] **Step 5: Commit**

```bash
git add app/db.py tests/test_repository.py
git commit -m "feat(db): Spalten für alle ETF-Extras und deren Overrides"
```

---

### Task 2: Modelle und Validierung

**Files:**
- Modify: `app/models.py:63` (`OVERRIDE_FIELDS`), `app/models.py:71-84` (`InstrumentOverrides`), `QuoteResponse`, `InstrumentSummary`
- Test: `tests/test_overrides.py`

**Interfaces:**
- Consumes: Task 1 (Spalten existieren)
- Produces: `OVERRIDE_FIELDS = ("ter", "volatility", "accumulating", "provider", "replication", "fund_size", "fund_domicile", "fund_currency")`; `InstrumentOverrides` mit acht Feldern; `QuoteResponse.fund_domicile: str | None`, `.fund_currency: str | None`; dieselben zwei Felder auf `InstrumentSummary` plus `manual_*` für alle acht

- [ ] **Step 1: Write the failing test**

In `tests/test_overrides.py` anhängen:

```python
def test_die_neuen_felder_werden_validiert(client: TestClient) -> None:
    """Der Grund, Spalten statt einer generischen Tabelle zu nehmen."""
    gueltig = client.put(
        "/instruments/by-symbol/GOLD.SG/overrides",
        json={"fund_size": 129445.0, "fund_currency": "USD", "fund_domicile": "Irland"},
    )
    assert gueltig.status_code == 200
    assert gueltig.json()["fund_currency"] == "USD"


@pytest.mark.parametrize(
    "nutzlast",
    [
        {"fund_currency": "Euro"},          # kein ISO-Code
        {"fund_currency": "usd"},           # klein geschrieben
        {"fund_size": -1},                  # negativ
        {"fund_size": 2_000_001},           # groesser als der ETF-Markt
        {"provider": "x" * 101},            # laenger als erlaubt
    ],
)
def test_die_neuen_felder_weisen_unsinn_ab(client: TestClient, nutzlast: dict) -> None:
    antwort = client.put("/instruments/by-symbol/GOLD.SG/overrides", json=nutzlast)

    assert antwort.status_code == 422
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_overrides.py -k "neuen_felder" -v`
Expected: FAIL — Pydantic verwirft `fund_size` als unbekanntes Feld bzw. akzeptiert es kommentarlos, `fund_currency` fehlt in der Antwort.

- [ ] **Step 3: Write minimal implementation**

In `app/models.py`:

```python
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
    provider: str | None = Field(default=None, max_length=100, description="Fondsanbieter")
    replication: str | None = Field(default=None, max_length=100, description="Replikationsart")
    # Obergrenze in Mio. EUR: 2 Bio. — der größte Fonds der Welt liegt bei rund 1,5.
    fund_size: float | None = Field(
        default=None, ge=0, le=2_000_000, description="Fondsvolumen in Mio. EUR"
    )
    fund_domicile: str | None = Field(default=None, max_length=100, description="Fondsdomizil")
    fund_currency: str | None = Field(
        default=None,
        pattern=r"^[A-Z]{3}$",
        description="Fondswährung als ISO-4217-Code",
    )
```

In `QuoteResponse` nach `fund_size` ergänzen:

```python
    fund_domicile: str | None = None
    fund_currency: str | None = Field(
        default=None, description="Währung des Fonds — nicht die des Handelsplatzes"
    )
```

In `InstrumentSummary` dieselben zwei Felder ergänzen sowie die fehlenden rohen Eingaben:

```python
    fund_domicile: str | None = None
    fund_currency: str | None = None

    manual_ter: float | None = None
    manual_volatility: float | None = None
    manual_accumulating: bool | None = None
    manual_provider: str | None = None
    manual_replication: str | None = None
    manual_fund_size: float | None = None
    manual_fund_domicile: str | None = None
    manual_fund_currency: str | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_overrides.py -q`
Expected: PASS. Der Wächter `test_jede_kennzahl_tragende_antwort_kennt_die_regel` bleibt grün — die Modellmenge ändert sich nicht, nur ihre Felder.

- [ ] **Step 5: Commit**

```bash
git add app/models.py tests/test_overrides.py
git commit -m "feat(api): alle acht ETF-Extras im Override-Modell"
```

---

### Task 3: Repository feldgetrieben machen

**Files:**
- Modify: `app/repository.py:275-315` (`set_overrides`), `app/repository.py:200-227` (`list_instruments_with_latest`), Instrument-Upsert in `save_quote`
- Test: `tests/test_overrides.py`

**Interfaces:**
- Consumes: Task 2 (`OVERRIDE_FIELDS`)
- Produces: `QuoteRepository.set_overrides(instrument_id: int, werte: dict[str, object], updated_at: str) -> None` — **geänderte Signatur**, nimmt statt drei Einzelwerten ein Dict über `OVERRIDE_FIELDS`

- [ ] **Step 1: Write the failing test**

```python
def test_alle_acht_felder_ueberleben_das_erneute_lesen(repo: QuoteRepository) -> None:
    instrument_id = repo.save_quote(_quote())

    repo.set_overrides(
        instrument_id,
        {
            "ter": 0.25,
            "volatility": 30.0,
            "accumulating": True,
            "provider": "iShares",
            "replication": "Physical",
            "fund_size": 129445.0,
            "fund_domicile": "Irland",
            "fund_currency": "USD",
        },
        "2026-08-17T10:00:00+00:00",
    )

    gespeichert = repo.get_overrides(instrument_id)
    assert gespeichert is not None
    assert gespeichert["provider"] == "iShares"
    assert gespeichert["fund_currency"] == "USD"
    assert gespeichert["accumulating"] == 1


def test_alles_leeren_entfernt_die_zeile_auch_bei_acht_feldern(repo: QuoteRepository) -> None:
    # Sonst sammeln sich Karteileichen ohne Inhalt.
    instrument_id = repo.save_quote(_quote())
    repo.set_overrides(instrument_id, {"provider": "iShares"}, "2026-08-17T10:00:00+00:00")

    repo.set_overrides(instrument_id, dict.fromkeys(OVERRIDE_FIELDS), "2026-08-17T11:00:00+00:00")

    assert repo.get_overrides(instrument_id) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_overrides.py -k "acht_felder" -v`
Expected: FAIL — `set_overrides() takes 5 positional arguments but 4 were given` bzw. `TypeError`, weil die alte Signatur drei Einzelwerte erwartet.

- [ ] **Step 3: Write minimal implementation**

In `app/repository.py` — `set_overrides` feldgetrieben:

```python
    def set_overrides(
        self, instrument_id: int, werte: dict[str, object], updated_at: str
    ) -> None:
        """Schreibt die manuellen Kennzahlen — immer den vollständigen Satz.

        ``None`` heißt **löschen**, nicht „unverändert": Die Oberfläche schickt
        stets alle Felder, und ein geleertes muss den Wert auch wieder entfernen
        können. Bleibt nichts übrig, verschwindet die Zeile ganz.

        Die Spaltenliste kommt aus ``OVERRIDE_FIELDS`` statt aus getippten
        Parametern — bei acht Feldern wäre eine Signatur aus Einzelwerten nicht
        mehr zu lesen, und jede neue Kennzahl müsste an vier Stellen nachgezogen
        werden.
        """
        gefiltert = {feld: werte.get(feld) for feld in OVERRIDE_FIELDS}
        gefiltert["accumulating"] = (
            None if gefiltert["accumulating"] is None else int(bool(gefiltert["accumulating"]))
        )

        with self._connect() as connection:
            if all(wert is None for wert in gefiltert.values()):
                connection.execute(
                    "DELETE FROM instrument_overrides WHERE instrument_id = ?",
                    (instrument_id,),
                )
                return

            spalten = ", ".join(OVERRIDE_FIELDS)
            platzhalter = ", ".join("?" for _ in OVERRIDE_FIELDS)
            zuweisungen = ", ".join(f"{feld} = excluded.{feld}" for feld in OVERRIDE_FIELDS)
            connection.execute(
                f"INSERT INTO instrument_overrides (instrument_id, {spalten}, updated_at) "
                f"VALUES (?, {platzhalter}, ?) "
                f"ON CONFLICT(instrument_id) DO UPDATE SET {zuweisungen}, "
                "updated_at = excluded.updated_at",
                (instrument_id, *(gefiltert[feld] for feld in OVERRIDE_FIELDS), updated_at),
            )
```

Import ergänzen: `from app.models import OVERRIDE_FIELDS`.

In `list_instruments_with_latest` die Auswahl der manuellen Werte feldgetrieben bauen — statt drei fester Zeilen:

```python
        manuell = ",\n                   ".join(
            f"o.{feld} AS manual_{feld}" for feld in OVERRIDE_FIELDS
        )
        query = f"""
            SELECT i.*,
                   q.price      AS latest_price,
                   q.quote_time AS latest_quote_time,
                   q.currency   AS latest_currency,
                   q.fetched_at AS latest_fetched_at,
                   {manuell},
                   (SELECT COUNT(*) FROM quotes WHERE instrument_id = i.id)
                       AS history_count
            FROM instruments i
            LEFT JOIN quotes q ON q.id = (
                SELECT id FROM quotes WHERE instrument_id = i.id
                ORDER BY quote_time DESC LIMIT 1
            )
            LEFT JOIN instrument_overrides o ON o.instrument_id = i.id
            ORDER BY i.symbol
        """
```

Im Instrument-Upsert von `save_quote` die zwei neuen Quellen-Spalten mitschreiben (`fund_domicile`, `fund_currency`) — analog zu `ter`/`replication`.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS. Die Aufrufer aus Task 4 sind noch nicht umgestellt — schlagen dort Tests fehl, gehört das in Task 4, nicht hierher.

- [ ] **Step 5: Commit**

```bash
git add app/repository.py tests/test_overrides.py
git commit -m "refactor(db): Overrides über OVERRIDE_FIELDS statt Einzelparameter"
```

---

### Task 4: Dienst und Endpoint durchreichen

**Files:**
- Modify: `app/services/quote_cache.py` (`set_overrides`, `get_overrides`), `app/routers/dashboard.py:172-194`
- Test: `tests/test_overrides.py`

**Interfaces:**
- Consumes: Task 3 (`repository.set_overrides(instrument_id, werte, updated_at)`)
- Produces: `CachedQuoteService.set_overrides(symbol: str, werte: dict[str, object]) -> dict` — **geänderte Signatur**

- [ ] **Step 1: Write the failing test**

```python
def test_endpoint_schreibt_und_liest_alle_acht(client: TestClient) -> None:
    antwort = client.put(
        "/instruments/by-symbol/GOLD.SG/overrides",
        json={"provider": "iShares", "fund_domicile": "Irland", "ter": 0.25},
    )

    assert antwort.status_code == 200
    gelesen = client.get("/instruments/by-symbol/GOLD.SG/overrides").json()
    assert gelesen["provider"] == "iShares"
    assert gelesen["fund_domicile"] == "Irland"
    assert gelesen["ter"] == 0.25
```

Die Attrappe `_FakeService` in derselben Datei auf die neue Signatur ziehen:

```python
class _FakeService:
    """Merkt sich, was geschrieben wurde — der Endpoint soll nur durchreichen."""

    def __init__(self) -> None:
        self.gespeichert: dict = dict.fromkeys(OVERRIDE_FIELDS)

    def get_overrides(self, symbol: str) -> dict:
        if symbol.startswith("XX"):
            raise InstrumentNotFoundError(symbol)
        return dict(self.gespeichert)

    def set_overrides(self, symbol: str, werte: dict) -> dict:
        if symbol.startswith("XX"):
            raise InstrumentNotFoundError(symbol)
        self.gespeichert = {feld: werte.get(feld) for feld in OVERRIDE_FIELDS}
        return dict(self.gespeichert)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_overrides.py -k "alle_acht" -v`
Expected: FAIL — der Router ruft `service.set_overrides(symbol, payload.ter, payload.volatility, payload.accumulating)` und übergibt damit drei Positionsargumente an eine Methode, die ein Dict erwartet.

- [ ] **Step 3: Write minimal implementation**

In `app/services/quote_cache.py`:

```python
    def set_overrides(self, symbol: str, werte: dict[str, object]) -> dict:
        """Schreibt die manuellen Kennzahlen eines Instruments und liest sie zurück.

        Args:
            symbol: Yahoo-Symbol des Instruments.
            werte: Werte je Feld aus ``OVERRIDE_FIELDS``; fehlende gelten als
                ``None`` und löschen damit.

        Raises:
            InstrumentNotFoundError: Symbol unbekannt.
        """
        instrument = self._repository.get_instrument_by_symbol(symbol)
        if instrument is None:
            raise InstrumentNotFoundError(symbol)

        self._repository.set_overrides(
            instrument["id"], werte, datetime.now(timezone.utc).isoformat()
        )
        gespeichert = self._repository.get_overrides(instrument["id"]) or {}
        return {feld: gespeichert.get(feld) for feld in OVERRIDE_FIELDS}
```

`get_overrides` analog auf `OVERRIDE_FIELDS` ziehen, `accumulating` weiterhin über `_as_bool`.

Im Router `app/routers/dashboard.py`:

```python
    try:
        return InstrumentOverrides(
            **service.set_overrides(symbol, payload.model_dump())
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest -q && .venv/bin/python -m ruff check app tests`
Expected: PASS, Lint sauber.

- [ ] **Step 5: Commit**

```bash
git add app/services/quote_cache.py app/routers/dashboard.py tests/test_overrides.py
git commit -m "feat(api): Endpoint nimmt alle acht Kennzahlen entgegen"
```

---

### Task 5: Beschaffung — Domizil holen, Fondswährung trennen

**Files:**
- Modify: `app/providers/base.py:44-54` (`EtfDetails`), `app/providers/justetf_provider.py:75-84`, `app/services/quote_service.py:121-155`, `app/services/quote_cache.py` (`_from_cache`)
- Test: `tests/test_providers.py`, `tests/test_quote_service.py`

**Interfaces:**
- Consumes: Task 2 (`QuoteResponse.fund_domicile`, `.fund_currency`)
- Produces: `EtfDetails.fund_domicile: str | None`, `EtfDetails.fund_currency: str | None` (ersetzt `EtfDetails.currency`)

- [ ] **Step 1: Write the failing test**

In `tests/test_providers.py`:

```python
def test_justetf_liefert_domizil_und_fondswaehrung(monkeypatch) -> None:
    overview = {
        "name": "iShares Core MSCI World",
        "fund_domicile": "Ireland",
        "fund_currency": "USD",
    }
    monkeypatch.setattr(
        justetf_module.justetf_scraping, "get_etf_overview", lambda isin, **kw: overview
    )

    details = JustEtfProvider().fetch_etf("IE00B4L5Y983")

    assert details is not None
    assert details.fund_domicile == "Ireland"
    assert details.fund_currency == "USD"
```

In `tests/test_quote_service.py` — Aufbau wie `test_etf_uebernimmt_volatilitaet_und_thesaurierend_von_justetf`:

```python
def test_die_fondswaehrung_blutet_nicht_in_die_handelswaehrung() -> None:
    """Zwei Begriffe, zwei Felder.

    Fiel yfinance ohne Währung aus, rutschte bisher die Fondswährung in
    `currency` — bei einem Euro-Kurs stand dann USD daneben.
    """
    ohne_waehrung = RawQuote(
        symbol="VGWL.DE",
        price=160.98,
        quote_time="2026-07-12T17:35:00+00:00",
        currency=None,
        volume=1000,
        type="etf",
    )
    service = QuoteService(
        FakeQuoteProvider(ohne_waehrung),
        FakeEtfProvider(EtfDetails(fund_currency="USD", fund_domicile="Ireland")),
        FakeResolver(
            ResolvedInstrument(symbol="VGWL.DE", isin="IE00B3RBWM25", type="etf")
        ),
    )

    result = service.get_quote_by_isin("IE00B3RBWM25")

    assert result.currency is None
    assert result.fund_currency == "USD"
    assert result.fund_domicile == "Ireland"
```

Achtung beim Ausführen: `ResolvedInstrument` trägt selbst eine `currency`; für
diesen Test muss sie leer bleiben, sonst greift `raw.currency or
resolved.currency` und die Aussage verpufft.

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_providers.py tests/test_quote_service.py -k "domizil or fondswaehrung" -v`
Expected: FAIL — `EtfDetails` kennt `fund_domicile` nicht; `antwort.currency` ist `"USD"` statt `None`.

- [ ] **Step 3: Write minimal implementation**

In `app/providers/base.py` — `currency` wird zu `fund_currency`, `fund_domicile` kommt dazu:

```python
@dataclass
class EtfDetails:
    """ETF-spezifische Zusatzdaten (z.B. von justETF)."""

    ter: float | None = None
    provider: str | None = None
    replication: str | None = None
    fund_size: float | None = None
    # Die Währung des **Fonds** — nicht die des Handelsplatzes. Die kommt von
    # yfinance und ist eine andere Aussage: EUNL handelt in EUR, der Fonds
    # rechnet in USD.
    fund_currency: str | None = None
    fund_domicile: str | None = None
    name: str | None = None
    volatility: float | None = None  # 1-Jahres-Volatilität in % (justETF)
    accumulating: bool | None = None  # Thesaurierend (True) vs. Ausschüttend (False)
```

In `justetf_provider.py` das Mapping:

```python
            fund_currency=overview.get("fund_currency"),
            fund_domicile=overview.get("fund_domicile"),
```

In `quote_service.py::_enrich_etf` den Rückfall streichen und beide Felder setzen:

```python
        response.fund_size = details.fund_size
        response.name = response.name or details.name
        # Kein Rückfall auf die Handelswährung: Zwei Begriffe, zwei Felder.
        response.fund_currency = details.fund_currency
        response.fund_domicile = details.fund_domicile
```

In `quote_cache.py::_from_cache` die zwei Felder aus der Instrumentenzeile mitgeben:

```python
            fund_domicile=instrument["fund_domicile"],
            fund_currency=instrument["fund_currency"],
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/providers app/services tests
git commit -m "feat(justetf): Fondsdomizil holen, Fondswährung getrennt führen"
```

---

### Task 6: MetricValue — die Tabelle wird lesend

**Files:**
- Create: `dashboard/src/components/MetricValue.vue`
- Modify: `dashboard/src/components/InstrumentsTable.vue:216-244`
- Test: `dashboard/tests/components/MetricValue.spec.ts`

**`InstrumentCard.vue` bleibt in diesem Task unangetastet.** Die Karte nutzt
`ManualMetric` ebenfalls dreimal — aber in ihrem **aufgeklappten** Bereich
(`<dl v-if="expanded">`), also genau dort, wo mobil ohnehin gepflegt wird. Sie
auf reine Anzeige umzustellen wäre ein Rückschritt gegen T-09 #8. Die Karte
zieht in Task 8 auf die Schublade um; bis dahin läuft sie unverändert weiter.

**Interfaces:**
- Consumes: `manualValue`, `overrideState` aus `../composables/useOverrides`
- Produces: `MetricValue` mit Props `{ item: InstrumentSummary, field: OverrideField }` — zeigt den wirksamen Wert plus Merkmal, **ohne** jede Bearbeitung

- [ ] **Step 1: Write the failing test**

```typescript
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import MetricValue from '../../src/components/MetricValue.vue'
import { i18n } from '../../src/i18n'
import { makeInstrument } from '../fixtures/instrument'

describe('MetricValue', () => {
  it('zeigt den wirksamen Wert ohne jede Bedienung', () => {
    const wrapper = mount(MetricValue, {
      global: { plugins: [i18n] },
      props: { item: makeInstrument({ ter: 0.2 }), field: 'ter' },
    })

    expect(wrapper.text()).toMatch(/0[.,]20/)
    expect(wrapper.find('button').exists()).toBe(false)
  })

  it('markiert einen von Hand eingetragenen Wert', () => {
    const wrapper = mount(MetricValue, {
      global: { plugins: [i18n] },
      props: {
        item: makeInstrument({ ter: 0.2, manual_ter: 0.2, manual_fields: ['ter'] }),
        field: 'ter',
      },
    })

    expect(wrapper.find('.metric__mark').exists()).toBe(true)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd dashboard && npx vitest run tests/components/MetricValue.spec.ts`
Expected: FAIL — `Failed to resolve import "../../src/components/MetricValue.vue"`.

- [ ] **Step 3: Write minimal implementation**

`dashboard/src/components/MetricValue.vue` neu — Anzeige und Merkmal aus `ManualMetric.vue` übernehmen (die dortige `metric__static`-Hälfte samt `metric__mark`), ohne `UxInlineNumber`, ohne Umschalter, ohne `commit`-Event. Die Formatierung über `n()` mit zwei Nachkommastellen bleibt, ebenso die absolute Lage des Merkmals (`position: absolute; left: 100%`) — sie hält die Spalte bündig.

In `InstrumentsTable.vue` die drei `ManualMetric`-Blöcke durch `MetricValue` ersetzen und die `@click.stop`-Wrapper entfernen, da nichts mehr zu klicken ist:

```vue
            <td class="num mono dim"><MetricValue :item="item" field="ter" /></td>
            <td class="num mono dim"><MetricValue :item="item" field="volatility" /></td>
            <td class="center"><MetricValue :item="item" field="accumulating" /></td>
```

Import und der Kommentar über den Zellen werden entsprechend angepasst: Gepflegt wird jetzt in der Schublade.


- [ ] **Step 4: Run test to verify it passes**

Run: `cd dashboard && npx vitest run && npx vue-tsc -b`
Expected: PASS. `ManualMetric.spec.ts` schlägt jetzt fehl, weil die Komponente in Task 7 ersetzt wird — die Datei wird dort gelöscht.

- [ ] **Step 5: Commit**

```bash
git add dashboard/src/components/MetricValue.vue dashboard/src/components/InstrumentsTable.vue dashboard/tests/components/MetricValue.spec.ts
git commit -m "refactor(ui): Tabelle zeigt Kennzahlen nur noch an"
```

---

### Task 7: MetricEditor — pflegen, sperren, entfernen

**Files:**
- Create: `dashboard/src/components/MetricEditor.vue`
- Test: `dashboard/tests/components/MetricEditor.spec.ts`

`ManualMetric.vue` bleibt vorerst bestehen — die Kartenliste hängt noch daran.
Gelöscht wird sie in Task 8, wenn der letzte Aufrufer umgezogen ist.

**Interfaces:**
- Consumes: Task 6 (`MetricValue` existiert, Tabelle ist lesend)
- Produces: `MetricEditor` mit Props `{ item: InstrumentSummary, field: OverrideField, busy?: boolean }` und Event `commit(patch: Partial<InstrumentOverrides>)`

- [ ] **Step 1: Write the failing test**

```typescript
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import MetricEditor from '../../src/components/MetricEditor.vue'
import { i18n } from '../../src/i18n'
import type { InstrumentSummary, OverrideField } from '../../src/types'
import { makeInstrument } from '../fixtures/instrument'

function mountEditor(item: InstrumentSummary, field: OverrideField = 'ter') {
  return mount(MetricEditor, { global: { plugins: [i18n] }, props: { item, field } })
}

describe('MetricEditor', () => {
  it('lässt ein Feld pflegen, das die Quelle nicht liefert', () => {
    const wrapper = mountEditor(makeInstrument({ ter: null }))

    expect(wrapper.findComponent({ name: 'UxInlineNumber' }).exists()).toBe(true)
  })

  it('sperrt das Feld, sobald die Quelle etwas hat', () => {
    const wrapper = mountEditor(makeInstrument({ ter: 0.2 }))

    expect(wrapper.findComponent({ name: 'UxInlineNumber' }).exists()).toBe(false)
  })

  it('lässt einen verdeckten Eintrag entfernen', async () => {
    /*
     * Ohne diese Aktion wäre das Feature eine Falle: Wer während eines
     * Quellen-Ausfalls acht Felder nachträgt, käme nach dessen Ende an keinen
     * davon mehr heran.
     */
    const wrapper = mountEditor(
      makeInstrument({ ter: 0.2, manual_ter: 0.1, shadowed_fields: ['ter'] }),
    )

    await wrapper.get('.metric-editor__remove').trigger('click')

    expect(wrapper.emitted('commit')?.[0]?.[0]).toEqual({ ter: null })
  })

  it('bietet nichts zum Entfernen, wo es keine Eingabe gibt', () => {
    const wrapper = mountEditor(makeInstrument({ ter: 0.2 }))

    expect(wrapper.find('.metric-editor__remove').exists()).toBe(false)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd dashboard && npx vitest run tests/components/MetricEditor.spec.ts`
Expected: FAIL — `Failed to resolve import "../../src/components/MetricEditor.vue"`.

- [ ] **Step 3: Write minimal implementation**

`MetricEditor.vue` neu, aufgebaut aus dem Bearbeitungs-Teil von `ManualMetric.vue`:

- `quelleHatWert = zustand !== 'manual' && wert !== null` steuert wie bisher, ob gepflegt werden darf.
- Für `accumulating` der Dreier-Umschalter über `naechster(item.manual_accumulating)` (ja → nein → nicht gesetzt → ja), für die übrigen Zahlenfelder `UxInlineNumber` mit `:value="manuelleZahl"`, für `provider`/`replication`/`fund_domicile`/`fund_currency` ein `NInput` mit `@blur`-Commit.
- Zusätzlich, und das ist neu gegenüber `ManualMetric`: Gibt es einen manuellen Wert (`manualValue(item, field) !== null`), erscheint ein Knopf `.metric-editor__remove` mit `:title="t('overrides.removeOwn')"`, der `commit({ [field]: null })` schickt — **auch dann, wenn das Feld gesperrt ist**.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd dashboard && npx vitest run && npx vue-tsc -b`
Expected: PASS — auch `ManualMetric.spec.ts`, die Komponente lebt ja noch.

- [ ] **Step 5: Commit**

```bash
git add dashboard/src/components/MetricEditor.vue dashboard/tests/components/MetricEditor.spec.ts
git commit -m "feat(ui): Kennzahlen-Editor mit Entfernen für verdeckte Werte"
```

---

### Task 8: Die Schublade

**Files:**
- Create: `dashboard/src/components/InstrumentDrilldown.vue`
- Modify: `dashboard/src/components/InstrumentsTable.vue` (Kennung öffnet die Zeile, Detailzeile), `dashboard/src/components/InstrumentCard.vue:138-170` (aufgeklappter Bereich), `dashboard/src/i18n/de.ts`, `dashboard/src/i18n/en.ts`
- Delete: `dashboard/src/components/ManualMetric.vue`, `dashboard/tests/components/ManualMetric.spec.ts`
- Test: `dashboard/tests/components/InstrumentDrilldown.spec.ts`

**Interfaces:**
- Consumes: Task 7 (`MetricEditor`)
- Produces: `InstrumentDrilldown` mit Props `{ item: InstrumentSummary, busy?: boolean }` und Event `commit(patch: Partial<InstrumentOverrides>)`

- [ ] **Step 1: Write the failing test**

```typescript
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import InstrumentDrilldown from '../../src/components/InstrumentDrilldown.vue'
import { i18n } from '../../src/i18n'
import { makeInstrument } from '../fixtures/instrument'

describe('InstrumentDrilldown', () => {
  it('zeigt alle acht Kennzahlen zum Pflegen', () => {
    const wrapper = mount(InstrumentDrilldown, {
      global: { plugins: [i18n] },
      props: { item: makeInstrument() },
    })

    expect(wrapper.findAllComponents({ name: 'MetricEditor' })).toHaveLength(8)
  })

  it('erklärt, warum die Quelle nichts beigesteuert hat', () => {
    // Nicht-europäisches Domizil wird bewusst übersprungen — genau diese
    // Erklärung fehlt dem Nutzer heute.
    const wrapper = mount(InstrumentDrilldown, {
      global: { plugins: [i18n] },
      props: { item: makeInstrument({ isin: 'US0378331005', ter: null }) },
    })

    expect(wrapper.text()).toContain(i18n.global.t('drilldown.noEuropeanSource'))
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd dashboard && npx vitest run tests/components/InstrumentDrilldown.spec.ts`
Expected: FAIL — Komponente existiert nicht.

- [ ] **Step 3: Write minimal implementation**

`InstrumentDrilldown.vue` neu, zweispaltig:

- **Links** acht `MetricEditor`, je Feld beschriftet, `@commit` nach oben durchgereicht.
- **Rechts** die Herkunft: `item.meta_fetched_at` als Zeitpunkt, dazu die Erklärung. Ist die ISIN nicht europäisch (dieselbe Präfix-Prüfung wie im Backend, als kleine Hilfsfunktion im Frontend), steht dort `t('drilldown.noEuropeanSource')`; sonst, wenn alle ETF-Extras leer sind, `t('drilldown.sourceEmpty')`.

In `InstrumentsTable.vue`:

```vue
            <td class="sym mono">
              <button type="button" class="row-toggle" :aria-expanded="isOpen(item)"
                      @click.stop="toggle(item)">{{ item.symbol }}</button>
            </td>
```

Der Name analog. Eine zweite `<tr v-if="isOpen(item)">` mit `<td :colspan="columns.length + 1">` trägt die Schublade. Der bestehende Zeilen-Klick (`emit('select', item)`, öffnet das Chart) **bleibt** — nur Symbol und Name klinken sich mit `@click.stop` aus.

In `InstrumentCard.vue` den aufgeklappten Bereich auf dieselbe Schublade ziehen:
Die drei `ManualMetric` in `<dl v-if="expanded" class="icard__details">`
weichen einem `<InstrumentDrilldown :item="item" :busy="saving" @commit="emit('override', $event)" />`.
Mobil steht damit dasselbe zur Verfügung wie am Schreibtisch — acht Felder
statt drei, an derselben Stelle wie bisher.

Danach hat `ManualMetric.vue` keinen Aufrufer mehr und wird samt ihrer Spec
gelöscht.

Katalog-Einträge in `de.ts` und `en.ts` für: die fünf neuen Feldnamen, `overrides.removeOwn`, `drilldown.noEuropeanSource`, `drilldown.sourceEmpty`, `drilldown.fetchedAt`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd dashboard && npx vitest run && npx vue-tsc -b && cd .. && .venv/bin/python -m pytest -q`
Expected: PASS in allen dreien.

- [ ] **Step 5: Im Browser nachmessen**

Dev-Server starten, dann in der laufenden App prüfen — gemessen, nicht geschätzt:

```js
// Spalten bündig gegen ihre Köpfe (alle Werte einer Spalte gleich)
[...document.querySelectorAll('tbody tr')].map(tr => tr.querySelectorAll('td')[5]
  .querySelector('.metric__static')?.getBoundingClientRect().right)

// Kein waagrechter Überhang bei 375 px
document.documentElement.scrollWidth - document.documentElement.clientWidth
```

Erwartet: je Spalte ein einziger Wert, Überhang 0. Zusätzlich die Schublade in `sepia` öffnen und den Kontrast ihrer Flächen prüfen.

- [ ] **Step 6: Commit**

```bash
git add dashboard/src/components/InstrumentDrilldown.vue dashboard/src/components/InstrumentsTable.vue dashboard/src/components/InstrumentCard.vue dashboard/src/i18n dashboard/tests/components/InstrumentDrilldown.spec.ts
git rm dashboard/src/components/ManualMetric.vue dashboard/tests/components/ManualMetric.spec.ts
git commit -m "feat(ui): aufklappbare Zeile mit allen ETF-Kennzahlen"
```

---

## Offene Entscheidung für den Ausführenden

Die Spec sagt „Die Kennung öffnet die Zeile", die Zeile reagiert aber schon auf
Klick: `@click="emit('select', item)"` öffnet das Chart. Dieser Plan löst es so,
dass **Symbol und Name** die Schublade öffnen (`@click.stop`) und der übrige
Zeilenbereich weiterhin das Chart. Wer das anders will, ändert nur Task 8,
Schritt 3.
