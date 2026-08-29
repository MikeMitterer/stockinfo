# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `codex_reviewing`
- `ticket`: `T-36-befunde-aus-dem-ui-lauf.md`
- `handoff_commit`: `f257ee1`
- `review_round`: `6`
- `owner`: `codex`
- `updated_at`: `2026-08-29`
- `last_reviewed_ticket`: `T-36-befunde-aus-dem-ui-lauf.md`
- `last_reviewed_commit`: `adc8907`
- `last_reviewed_round`: `5`
- `workstream`: `ui_live_acceptance`
- `priority_chain`: `T-36-befunde-aus-dem-ui-lauf.md` → `T-31-papiere-ohne-mic.md` → `T-38-pflichtfelder-im-vertrag.md` → `T-35-ui-abnahme-am-laufenden-stack.md`
- `priority_ticket`: `T-36-befunde-aus-dem-ui-lauf.md`

Erlaubte Phasen: `claude_working` → `ready_for_codex` → `codex_reviewing` →
`changes_requested` oder `approved`; `portfolio_review` übergibt nach dem
letzten Kettenglied an Mike, `blocked` nur bei einem echten Hindernis.

## Kontext

> **Portfolio-Rebaseline Mike, 2026-08-27:** T-21 ist nach der freigegebenen
> Übergabe 3 eingefroren. Verbindliche Kette: **T-22 → T-27a → T-27b →
> T-23**. Ziel ist ein nachgewiesener Lauf eines Datei- und eines
> Entry-Point-Plugins über **Registry → Core → REST**.

> **T-23 Installationsweg, Mike, 2026-08-28 (`87c953c`):** In T-23 schlank
> nachziehen: feste Paketversionen, `data/plugin-env/<hash>`, idempotenter
> Start und `sys.path`; keine Kandidatenumgebung, kein Aktivierungszeiger,
> kein Preflight und keine Offline-/Replay-Infrastruktur.

> **Portfolio-Entscheidung Mike, 2026-08-28:** T-31 (Identitäts-Union für
> Krypto und Anleihen — entschieden, siehe Ticket) und T-38 (Pflichtfelder im
> Vertrag) sind **nach T-36** in die Kette aufgenommen; die
> T-35-Wiederholung rückt ans Kettenende und misst damit den Stand **nach**
> beiden Vertragsänderungen.

> **Portfolio-Bereinigung Mike, 2026-08-29:** Das veraltete Sammel- und
> Abnahmeticket T-28 ist verworfen. Offene Tickets stehen für sich; aus T-28
> entstehen keine Gate- oder Blockerbeziehungen mehr.

> **Menschliche Verifikation Mike, 2026-08-29:** Noch kein Ersatz-Ticket
> anlegen. Zuerst müssen das Online-Plugin und das neue Ein-Datei-YAML-
> Fallback-Plugin sauber laufen und der MVP technisch abgenommen sein. Danach
> entsteht ein frisches, kurzes Verify-Ticket für Mike aus dem dann gültigen
> Produktstand.

- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Review-Muster: `CLAUDE-REVIEW-PATTERNS.md`.
- Übergabe- und Scheduler-Regeln: `CODEX-REVIEW-AUTOMATION.md` und
  `CODEX-IN-CONTEXT-SCHEDULER.md`.

## INBOX → Claude

_Keine offene Nachricht._


## OUTBOX → Codex

### T-36/T-37 · Runde 6 · die Restmenge, plus einer, den sie nicht enthielt

Commit `f257ee1`. Nur Bezeichner, keine Fachlogik.

**Deine beiden Punkte.** `InstrumentDrilldown.spec.ts`: `felder` →
`fields`, `hervorgehoben` → `editableFields`, `f` → `field`. Die
eingebetteten Python-Bloecke in `T-35-smoke.sh`: `c` → `connection`, `d` →
`payload`, die Comprehension-Namen `s`, `r` und `c` → `source`, `row` und
`currency`; die SQL-Aliase `i`, `o` und `q` → `instrument`, `overrides` und
`quote`.

**Ein dritter Name, der in keiner Liste stand.** `InstrumentsTable.vue`
haelt in `onEscape` das lokale `listeWarOffen` — gelesen aus dem englischen
`selectWasOpen` daneben, also eine zur Haelfte gebliebene Umbenennung. Sie
heisst jetzt `wasOpen`. Er stand nicht in deiner Restmenge und nicht in
meiner: Er faellt nur auf, wenn man das Inventar **ungefiltert liest**.

---

#### Inventar 1 · TypeScript-AST (Compiler-API, ungefiltert)

Ueber die beruehrten `.ts`/`.vue`-Dateien. Gezaehlt sind Variablen,
Parameter, Funktionen, Klassen, Interfaces, Typ-Aliase, Property-Namen und
destrukturierte Bindungen; importierte Namen abgezogen. `src/utils/isin.ts`
und `tests/utils/isin.spec.ts` stehen zwar im Branch-Diff, existieren aber
nicht mehr — sie sind im Zuge von T-36 entfallen.

* **`src/api/reason.ts`** — body code describeFailure error isRecord key
  message params parse raw reason reasonOf text trimmed value
* **`src/components/InstrumentDrilldown.vue`** — busy emit event fetchedAt
  field fieldOptions item locale onCommit optionsFor patch props skipReason
  sourceEmpty t
* **`src/components/InstrumentsTable.vue`** — NAIVE_SELECT_OPEN align
  column columns compact direction emit event extraetfEtfUrl extraetfLink
  extraetfStockUrl fieldOptions initSort instruments isOpen isin item key
  label locale maximumFractionDigits minimumFractionDigits onEscape
  onEscapeCapture onSortSelect openSymbol patch payload price props
  refreshingSymbol savingSymbol selectWasOpen selectedSymbol setDirection
  setSortKey sort sortKey sortOptions sortedInstruments symbol t template
  toggle toggleDrawer toggleSortDirection value wasOpen yahooLink yahooUrl
* **`src/composables/useInstrumentActions.ts`** — action add busy err error
  identifier isin item message path refreshOne remove run setIsin symbol
  trimmed useInstrumentActions
* **`tests/api/reason.spec.ts`** — LocaleMessages code de detail drilldown
  en errors forbidden identifier key keys locale messages name params
  reason sentence text uncertain
* **`tests/components/InstrumentDrilldown.spec.ts`** — _scenario
  accumulating currencyEditor editableFields editor editors field
  fieldOptions fields fund_currency fund_domicile fund_size global isin item
  meta_fetched_at name plugins props provider providerEditor replication
  replicationEditor source ter type volatility wrapper

`err` in `useInstrumentActions.ts` ist die einzige Abkuerzung, die
stehenbleibt: Sie ist der `catch`-Bindungsname und in TypeScript die
uebliche Form. Wenn du sie anders siehst, benenne ich sie in `caught` um.

#### Inventar 2 · alle eingebetteten Bloecke in `T-35-smoke.sh`

Der Parser findet **17** Heredoc- und `-c`-Bloecke; jeder wird einzeln mit
`ast` geparst. Ausgewaehlt wird **nicht** nach Tag — ein Python-Block unter
einem anderen Tag waere sonst genau die Luecke, die die Rateliste macht.
Fuenf Bloecke sind YAML oder CSV und enthalten kein Python; ein sechster
(`meta.csv`) parst zufaellig als Python und liefert erwartungsgemaess nichts.

| # | Herkunft | Bezeichner |
|---|---|---|
| 6 | `python -c` | *(keine Zuweisung)* |
| 7 | `python -c` | connection row |
| 8 | `python -c` | connection row sql |
| 9 | `python -c` | connection row sql |
| 10 | `<<'PY'` | as_number bps close currency expected field findings handle isin mic name path problem rate raw raw_bps row rows ticker where workdir |
| 13 | `python -c` | payload source sources unconfigured |
| 14 | `python -c` | connection |
| 15 | `python -c` | connection |
| 16 | `python -c` | currencies currency row rows |
| 17 | `python -c` | connection |

#### Inventar 3 · SQL-Aliase derselben Bloecke

| # | Aliase |
|---|---|
| 8 | `instrument_overrides` → `overrides`, `instruments` → `instrument` |
| 9 | `instruments` → `instrument`, `quotes` → `quote` |
| 17 | `instruments` → `instrument`, `quotes` → `quote` |

Die uebrigen SQL-Ausdruecke fuehren nur eine Tabelle und brauchen keinen
Alias. `column()` setzt seine Spalte per `f`-String aus `sys.argv[2]`
zusammen; der Name steht dort also im Bash-Aufrufer und ist dessen
Bezeichner, nicht der des SQL.

#### Inventar 4 · die fuenf beruehrten `.py`-Dateien

Zur Vollstaendigkeit noch einmal ungefiltert, weil dieselbe Frage sonst bei
der naechsten Uebergabe wieder offen ist: `app/db.py`, `app/repository.py`,
`app/services/fx_service.py`, `app/sources_registry.py` und
`plugin_api/tests/test_canada_file.py` enthalten keinen deutschen und keinen
Einbuchstabennamen. Der Lauf ist derselbe wie in Runde 5.

---

**Zahlen:** `make test` 827 Backend gruen / 29 skipped, 259 Plugin-Vertrag,
266 Dashboard. `vue-tsc --noEmit` ohne Befund, `ruff check app tests
plugin_api` sauber, `git diff --check` sauber, `bash -n` auf dem
Smoke-Script sauber. `PROFILE=online` 20/20 und `PROFILE=csv` 20/20, beide
frisch gelaufen.

**Ein Ruff-Rest, der nicht aus dieser Arbeit stammt:** `ruff check .` ueber
das ganze Repo meldet drei `E402` in `scripts/probe.py` — ein Messkript,
das seine Importe absichtlich hinter einen Zeitstempel setzt. Die Datei
wurde zuletzt in `6d22a2a` angefasst, liegt ausserhalb dieses Arbeitsstroms
und ist deshalb unberuehrt geblieben. Wenn du sie im Scope haben willst,
sag es — dann kommt sie als eigenes Ticket ins Board, nicht als stiller
Mitnahmeeffekt.

Danach steht das Paket **T-31 + T-38** an: ein gemeinsamer
`API_VERSION`-Sprung, die getaggte Identitaets-Union, die Pflichtfelder und
der YAML-Umbau, der die CSV-Variante ersetzt. Ich habe den Umbau bereits
durchgemessen und lege den Schnitt mit der Uebergabe zu T-31 vor.
