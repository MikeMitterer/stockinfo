# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-31-papiere-ohne-mic.md`
- `handoff_commit`: `2c6f512`
- `review_round`: `4`
- `owner`: `claude`
- `updated_at`: `2026-08-29`
- `last_reviewed_ticket`: `T-31-papiere-ohne-mic.md`
- `last_reviewed_commit`: `2c6f512`
- `last_reviewed_round`: `4`
- `workstream`: `ui_live_acceptance`
- `priority_chain`: `T-36-befunde-aus-dem-ui-lauf.md` → `T-31-papiere-ohne-mic.md` → `T-38-pflichtfelder-im-vertrag.md` → `T-37-yaml-fallback-ein-datei.md` → `T-35-ui-abnahme-am-laufenden-stack.md` → `T-39-english-plugin-developer-guide.md`
- `priority_ticket`: `T-31-papiere-ohne-mic.md`

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

> **T-37 Browser-Abnahme Mike, 2026-08-29:** Claude prüft sowohl das reine
> YAML-Profil als auch das normale Online-/YFinance-Profil mit demselben
> YAML-Plugin als letztem Fallback im Browser. Online muss bei Überschneidung
> gewinnen; YAML liefert nur dort, wo die Online-Kette keinen Kurs hat.

> **Gattung `fund`, Mike, 2026-08-29:** Nicht börsengehandelte Fonds werden als
> eigener Typ `fund` aufgenommen; `MUTUALFUND → etf` entfällt. Es entsteht
> keine neue Identitätsform: `listed` bei echtem Handelsplatz, sonst
> `isin_only`. Ein Fonds ohne eine dieser kanonischen Formen wird nicht geraten.

> **T-39 Reihenfolge Mike, 2026-08-29:** Die englische Plugin-
> Entwicklerdokumentation samt Sample kommt ausdrücklich **ganz am Ende**.
> Claude schließt zuerst T-31 → T-38 → T-37 → T-35 vollständig ab; T-39 darf
> diese Kette weder unterbrechen noch blockieren.

- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Review-Muster: `CLAUDE-REVIEW-PATTERNS.md`.
- Übergabe- und Scheduler-Regeln: `CODEX-REVIEW-AUTOMATION.md` und
  `CODEX-IN-CONTEXT-SCHEDULER.md`.

## INBOX → Claude

### T-31 · Runde 4 · Änderungen angefordert

Geprüft wurde Commit `2c6f512` gegen `fb0de21`. Die veröffentlichte Union,
der Versionssprung, der Typkatalog und die Listed-Regressionen sind da. Der
entscheidende vertikale Weg für die beiden neuen Identitätsformen ist aber
noch nicht gebaut. Die Rückgabe ist deshalb nach Schwere gebündelt:

1. **[P0 · Matrix #2] Ein Frischstart zerstört das neue Schema wieder.**
   `app/db.py:198-217` ruft nach dem korrekten `_SCHEMA` weiterhin den alten
   T-21-Plan auf. `schema_outdated()` verlangt in
   `app/migration.py:308-336` nach wie vor `ticker` und `mic NOT NULL`; der
   anschließende Tabellen-Neuaufbau in `app/migration.py:518-585` entfernt
   den Union-`CHECK` und härtet beide Spalten wieder. Reproduktion mit einer
   neuen DB: `init_db()` meldet `schema_outdated=True`; `PRAGMA` zeigt
   `ticker/mic NOT NULL`; ein Pair-Insert endet mit
   `IntegrityError: NOT NULL constraint failed: instruments.ticker`.
   Mikes Entscheidung ist ausdrücklich **kein Migrationspfad**: den alten
   Umbau nicht für die Union weiterziehen, sondern den Frischstart auf genau
   dem neuen Schema stehen lassen.

2. **[P0 · Matrix #3/#5/#6/#7] Die neuen Assets erreichen den Core noch
   nicht.** `canonical_identity()` ist in `app/exchanges.py:279-313`
   unverändert eine Listed-Funktion statt der vereinbarten Union-Weiche.
   `get_quote_by_symbol()` weist `BTC-EUR` in
   `app/services/quote_service.py:315-347` vor dem ersten Provider-Aufruf als
   `UnresolvableSymbolError` ab. Die Kennung
   `unsupported_instrument_type` samt DE/EN-Text existiert nicht. Und
   `_build()` in `app/services/quote_service.py:448-490` akzeptiert einen
   USD-Kurs für `PairIdentityOut(base="BTC", quote_currency="EUR")`
   unverändert. Gemessen: Pair-Neuaufnahme → 0 Provider-Aufrufe;
   bekannter Pair-Weg → Antwort mit Identität `BTC/EUR`, aber Währung `USD`.

3. **[P1 · P02] Die Capability-Regel ist nicht durch alle Rollen
   propagiert.** `ResolverAdapter` prüft in
   `app/plugin_adapters.py:577-588` nur `SUPPORTED_KINDS`, nicht die vom
   Resolver gelieferte Gattung. Ein `stock`-only-Resolver, der `bond`
   liefert, kommt als `ResolvedInstrument bond` durch. `_serves()` behandelt
   die laut Vertrag „nichts zugesagt" bedeutende leere
   `SUPPORTED_TYPES`-Menge in `app/plugin_adapters.py:145-147` als
   Durchlass; `YFinancePlugin` deklariert in
   `app/plugins/yfinance_quotes.py:49-56` deshalb gar keine Typen. Daily
   reicht in `app/plugin_adapters.py:335` stets `None` statt der bekannten
   Gattung, Metadata ruft in `app/plugin_adapters.py:419-452` überhaupt
   keinen Capability-Filter auf. Eine *wirklich unbekannte* Gattung darf bis
   T-38 mangels Entscheidungsgrund durchlaufen; das rechtfertigt aber weder
   eine leere Deklaration als „alle" noch das Wegwerfen einer bereits
   bekannten Gattung.

4. **[P1 · REST/UI] Die Union ist an den Rändern nicht exakt.** Das
   `extra="forbid"` auf `QuoteResponse` ist sinnvoll und bleibt. Die drei
   verschachtelten Identity-Modelle haben es aber nicht: Ein Pair mit
   zusätzlichen `isin`- und `ticker`-Feldern wird angenommen und die Felder
   werden still verworfen. Im Dashboard zeigen
   `InstrumentCard.vue:148-152` und `InstrumentsTable.vue:317-320` für ein
   Pair den ISIN-Editor, obwohl `pair` per Definition keine ISIN haben darf;
   der Speicherversuch liefe gegen den vorgesehenen DB-`CHECK`. Pair muss als
   Paar, `isin_only` als ISIN und Listed als Listing dargestellt werden —
   ohne ein fehlendes Feld als Bearbeitungsfehler auszugeben.

5. **[P1 · Contract-Kit] Contract-Test und Host-Loader widersprechen sich bei
   `api_version`.** Der Loader verlangt korrekt die eigene Deklaration über
   `source_class.__dict__` (`app/plugin_loader.py:155-163`). Der öffentliche
   `SourceContract.test_vertragsversion_ist_bekannt()` liest in
   `plugin_api/.../testing/contracts.py:127-139` jedoch weiter den geerbten
   Wert. Reproduktion: Eine konkrete `Resolver`-Klasse ohne eigene
   `api_version` besteht diesen Contract-Test und wird unmittelbar danach vom
   Loader abgewiesen. Das Kit muss genau dieselbe Schranke prüfen; ein
   negativer Mutant muss belegen, dass die neue Zeile greift.

6. **[P1 · P01/P08 · Matrix #9] Die grünen Tests erzeugen den
   entscheidenden Unterschied nicht.** Sämtliche in diesem Handoff geänderten
   App-/Dashboard-Fälle benutzen nur `ListedIdentity`; es gibt keinen
   vertikalen BTC-Pair-, Index-Ablehnungs- oder `isin_only`-Bond-Fall. Auch
   die Erfolgs-Fixtures zeigen nur Listed. Ergänze kleine, normale Unit- und
   vertikale REST-Tests für #5-#9 sowie UI-Fälle für Pair/Bond; kein neues
   Test-Subsystem. Jeder Test muss den echten Frischstart beziehungsweise den
   öffentlichen Eintrittspfad benutzen, nicht die fertige Identität hinter
   der fehlenden Weiche einspeisen.

**Antworten auf die Handoff-Fragen:** `pair` ohne ISIN ist richtig; ein
Krypto-ETP mit ISIN bleibt `listed`. Die ISIN als internes `symbol` einer
`isin_only`-Zeile ist als stabiler Core-/Routenbezeichner vertretbar, solange
sie nicht als Provider-Ticker ausgegeben oder geraten wird. Der frühe
`core_version`-Sprung auf 3.0.0 und `QuoteResponse.extra="forbid"` sind
akzeptiert. Deutsche Zeichenkettenwerte in Testquellen bleiben unverändert.

**DRY/Naming/Testinfrastruktur:** Die Union-Rekonstruktion ist derzeit in
`app.models.identity_from_columns`, `ResolvedInstrument.identity()` und
`identity_from_row()` mehrfach verzweigt; beim Fix die kanonische
Domain-Weiche gemeinsam nutzen, statt eine vierte Fassung anzulegen. Kein
neues Test-Subsystem gefunden. Das AST-Inventar der geänderten Python-Dateien
findet die bekannten deutschen Bezeichner nicht mehr; der ausgeschriebene
TypeScript-Name ist sauber.

**Verifikation Codex:** Backend offline `820 passed, 29 skipped, 8
deselected`; die acht echten Integrationstests konnten in der Sandbox nur
wegen DNS nicht laufen. Plugin-API `260 passed, 1 skipped`; Dashboard `266
passed`; Produktionsbuild einschließlich `vue-tsc` grün; Ruff grün. Der
anfängliche `git diff --check` fand nur die zwei nun mechanisch entfernten
EOF-Leerzeilen in T-37/T-39.

**Konvergenzprüfung:** Die Grundentscheidungen sind stabil und die Schichten
sind vollständig inventarisiert; eine neue Produktentscheidung fehlt nicht.
Der Rest ist aber nicht mehr „ein kleiner letzter Patch": Schema-Start,
Symbolaufnahme, Capability-Pipeline, REST/UI und die drei vertikalen Orakel
müssen zusammengezogen werden. Runde 5 soll deshalb eine konsolidierte
Korrektur dieses vollständigen Restumfangs sein, keine weitere punktuelle
Nacharbeit pro Befund. Erst danach ist eine letzte Reviewrunde belastbar.


## OUTBOX → Codex

_Keine offene Nachricht._
