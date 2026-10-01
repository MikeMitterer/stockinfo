# T-88 · Fondsgröße einheitlich in Mio. EUR

Die Detailansicht eines ETFs zeigte die Fondsgröße ohne Einheit „Mio.“. Beim
iShares Core MSCI World (`EUNL.DE`) stand „129,791 EUR“; der Fonds verwaltet
rund 129,8 Milliarden Euro. Dazu stand die Replikation ohne Leerzeichen da:
„Physical(Optimized sampling)“.

**Beispiel:** justETF schreibt „EUR 129,791 m“. Die Bibliothek
`justetf_scraping` liefert daraus `fund_size_eur = 129791.0`, laut ihrer Doku
„Fund size in EUR millions“. StockInfo war uneins über die Einheit:

| Stelle vorher | Einheit |
|---|---|
| manuelles Feld `InstrumentOverrides.fund_size` (`app/models.py`) | Mio. EUR, Grenze 2.000.000 |
| Detailkatalog `app/details.py`, `MetricEditor.vue` | Grenze 2.000.000 (passt zu Mio.) |
| justETF-Plugin, Adapter (`Unit.ABSOLUTE`), Vertrags-Fixtures (`89123000000.0`) | absolut |
| Anzeige | Zahl plus „EUR“, ohne „Mio.“ |

**Stand:** Gefunden am 2026-10-01 beim Erneuern der Screenshots. Mike:
„Erst Fehler beheben“, „Das Ticket kannst du gleich bei doing ablegen“ und
zur Einheit „Mio. EUR überall“. Coder `claude`, Verifier `codex`;
maßgeblich ist `STATUS.md`. Der Dateiname `…-in-euro` stammt aus dem ersten
Entwurf vor Mikes Einheiten-Entscheidung.

## Scope-Vertrag (Claude, 2026-10-01, nach Mikes Entscheidung)

Der erste Entwurf wollte absolute Euro. Beim Inventar zeigte sich der
Widerspruch oben; Mike entschied „Mio. EUR überall“. Damit wurde der
Vertrag berührt (Plugin-Einheit, Fixtures, Feldbeschreibung). Das ist ein
Scope-Checkpoint-Auslöser; die nötige Produktentscheidung hat Mike direkt
getroffen, deshalb ging die Arbeit ohne Verifier-Zwischenstopp weiter.

- **Ergebnis:** Die Fondsgröße hat überall eine Einheit: Mio. EUR. Die
  Detailansicht zeigt „129,791 million EUR“ bzw. „129.791 Mio. EUR“. Die
  Replikation steht als „Physical (Optimized sampling)“ da.
- **Fachliche Änderungen (3):**
  1. Einheit: Katalog (`app/details.py`) `millions`; justETF-Plugin und
     Adapter `Unit.MILLIONS`. Der Plugin-Vertrag erhält `MONEY_UNITS`
     (`ABSOLUTE`, `MILLIONS`); beide verlangen eine Währung. App, Plugin und
     Vertragsprüfsuite nutzen diese eine Menge.
  2. Anzeige: ein Katalogtext `details.amountMillions` für alle drei
     Anzeigewege (`DetailEditor`, `MetricValue`, `MetricEditor`); die
     flachen Altfelder nutzen `utils/fundSize.ts` mit EUR.
  3. Replikation: `JustEtfProvider` setzt das fehlende Leerzeichen vor „(“.
- **Vertrag:** `contract/core-contract.json` beschreibt `fund_size` als
  Millionen; drei Fixtures von `89123000000.0` auf `89123.0`.
- **Budget geplant / tatsächlich:** Produktdateien 3 / 12 (app 4,
  plugin_api 2, dashboard 6); Test-/Doku-/Vertragsdateien 4 / 15 (Tests 8,
  READMEs 2, Vertrag 4, Screenshot 1); Diff-Zeilen 200 / 249. Grund: Mikes
  Einheiten-Entscheidung betrifft Vertrag, Plugin-Paket und alle drei
  Anzeigewege.
- **Nicht-Ziele:** keine Datenmigration (Entwicklungsstand; gespeicherte
  justETF-Werte stehen schon in Millionen), keine Änderung an StockPortfolio,
  keine andere Quelle.

### Akzeptanzkriterien

- [ ] Die Fondsgröße hat in Katalog, Plugin, Adapter, Vertrag und Anzeige
      dieselbe Einheit: Mio. EUR.
- [ ] Ein Betrag in Millionen verlangt eine Währung (App und Vertragsprüfsuite).
- [ ] Die Detailansicht zeigt „129,791 million EUR“ / „129.791 Mio. EUR“.
- [ ] Die Replikation enthält das Leerzeichen vor der Klammer.
- [ ] Doku-Abgleich für `README.md`, `docker/README.md` und `contract/`.

### Side-Effects

StockPortfolio liest `fund_size` (`frontend/src/api/types.ts`,
`normalizers.ts`) und zeigt es in keiner `.vue`-Datei an. Der Wert kam schon
immer in Millionen; nur StockInfos Vertrags-Fixtures sagten „absolut“.
StockPortfolio führt eine eigene Kopie der Fixtures unter
`frontend/tests/fixtures/stockinfo/`; der Abgleich auf `89123.0` gehört ins
StockPortfolio-Board.

## Übergabe Runde 1 (Claude, 2026-10-01)

Prüfgegenstand: `67c86f8` gegen `master` (`f268ced`); darin `20b673a`
(Umsetzung) und `67c86f8` (Testwerte im Vertragstest nachgezogen).

### Verify

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | Einheit über alle Stellen verfolgen (`git grep fund_size`, `ABSOLUTE`, `2_000_000`) | Nirgends mehr „absolut“ für die Fondsgröße; Grenzen passen zu Millionen. Coder-Suche nach `fund_size` neben `ABSOLUTE`/„absolut“ und nach `1_200_000_000` über `app`, `tests`, `plugin_api`, `dashboard`, `contract`: einziger Treffer ist der Docstring des Mutantentests, der bewusst beide Einheiten prüft | ➖ |
| 2 | `.venv/bin/python -m pytest -q` und `cd plugin_api && ../.venv/bin/python -m pytest -q` | grün | ➖ |
| 3 | `cd dashboard && npx vitest run && npx vue-tsc -b && npx eslint src tests` | grün | ➖ |
| 4 | Detailansicht im Browser (Temp-Datenbank, ETF aufklappen, deutsch und englisch) | „129,791 million EUR“ / „129.791 Mio. EUR“, „Physical (Optimized sampling)“ | ➖ |
| 5 | Bezeichner-Inventar (Python `ast`, TS-Compiler-API) über die geänderten Dateien | nur englische Bezeichner | ➖ |
| 6 | Doku- und Vertragsabgleich | README, Docker-README und `contract/` nennen Millionen; Docker-Hub-Vorschau unter 25.000 Bytes | ➖ |

**Coder-Belege:**

- **#2:** Backend 1252 passed, 35 skipped; Plugin-Vertrag 324 passed,
  1 skipped; Ruff ohne Befund.
- **#3:** Dashboard 52 Dateien, 393 Tests grün; `vue-tsc -b` und ESLint ohne
  Befund. Der Stacktrace „useBackups.create boom“ im Lauf ist ein gewollter
  Fehler aus einem vorhandenen Test.
- **#4:** Echte StockInfo-Instanz mit Temp-Datenbank im Scratchpad, Dashboard
  aus dem Branch in einen eigenen Ordner gebaut. API liefert für EUNL.DE
  `fund_size` 129791.0 mit `unit` `millions` und `currency` EUR. Screenshot
  `unraid/screenshots/detail-area.png` zeigt „129,791 million EUR“ und
  „Physical (Optimized sampling)“. Die deutsche Anzeige deckt der
  Komponententest ab.
- **#5:** `ast`-Inventar (66 Namen in den geänderten Python-Dateien) und
  TS-Compiler-Inventar der sieben geänderten TS-/Vue-Dateien: alle englisch.
- **#6:** Docker-Hub-Vorschau 8.784 UTF-8-Bytes.

**Doku-Abgleich:** `README.md` (Quellentabelle, justETF: „fund size (in
millions of EUR)“) und `docker/README.md` (Funktionsliste) sagen dasselbe.
`unraid/README.md` nennt die Fondsgröße nicht und bleibt unverändert.
`contract/core-contract.json` beschreibt beide `fund_size`-Felder als
Millionen; Quellenwerte in EUR, manuelle Werte in der eingegebenen Währung.

Kein Merge, kein Push, kein Docker-Hub- oder Unraid-Update.
