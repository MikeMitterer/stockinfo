# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `083414c`
- `review_round`: `26`
- `owner`: `claude`
- `updated_at`: `2026-08-25`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `083414c`
- `last_reviewed_round`: `26`

Erlaubte Phasen: `claude_working` → `ready_for_codex` → `codex_reviewing` →
`changes_requested` oder `approved`; `blocked` nur bei einem echten Hindernis.
Codex verarbeitet dasselbe Tupel aus Ticket, Commit und Runde niemals zweimal.

## Kontext

> **Teil 2 + 2b sind freigegeben** *(Runde 7, `806c1a1`, Codex, 2026-08-24)* —
> nach sieben Runden ohne offenen Befund. Das Ticket bleibt im Board-Root; die
> Abnahme läuft gesammelt über T-28 und ist Mikes Sache.
>
> **Der Entwurf für Teil 3 ist freigegeben** *(Runde 24, `c5d0388`, Codex,
> 2026-08-25)* — nach **17 Entwurfsrunden** ohne eine Zeile Produktcode. Das war
> Absicht: Der Zuschnitt hat sich zweimal als falsch erwiesen, und die
> „Hoch"-Befunde waren durchweg Entwurfsfehler, die im Code teurer zu finden
> gewesen wären.
>
> **Jetzt beginnt die Umsetzung**, in vier Übergaben:
>
> | | Umfang | Vertrag |
> |---|---|---|
> | **1** | Börsenkatalog: Descriptor, Union, `catalog`, sechs neue Einträge, `COLLECTOR_CODES` abgeleitet | **kein** Sprung — `/exchanges` liegt außerhalb des geschlossenen Core |
> | **2A** | Migration, Backend: migrieren-oder-ablehnen, Quarantäne, Pending-Guard, `/migration*`, `/operational`, Reason-Codes | intern |
> | **2B** | Migration, Pflicht-UI und Image: Vorschau, Bestätigung, Bericht, DE/EN, `HEALTHCHECK`-Umzug | intern |
> | **3** | Aufnahmeweg: `POST /instruments/intake`, Intake-Service, strengerer `/quote?symbol=`, **`core_version 2.0.0`** | atomar |
> | **4** | Abweichungszustand, Fehlerpfad, Dokumentationsinventur | Snapshot bei Core-Änderung |
>
> **Zwei Reihenfolgen tragen Datenrisiko** und stehen als Warnung im Entwurf:
> Katalog **vor** Migration (sonst kostet `GOLD.SG` 257 Tageskurse), und
> Meldung **mit** Migration (2A allein wird nicht gemergt).
>
> **Teil 3 ist aufgeteilt** *(Entscheidung Mike, 2026-08-24, nach Runde 9)*:
>
> * **`T-29-alias-lebenszyklus-und-providerwechsel.md`** — Eigentum an `symbol`,
>   Wechselregeln, **zwei Backup-Arten**, Importbericht. **Revidiert `T-25:94-110`.**
> * **`T-30-plugin-boersenauskunft.md`** — neuer `plugin_api`-Typ samt Merge-,
>   Vorrang-, Kollisions-, Provenienz- und Invalidierungsregeln.
>
> **Teil 3 stärkt die Zusage zu `symbol` deshalb nicht.** Der Sprung auf
> `core_version 2.0.0` betrifft `ticker`, `mic`, `listing_id` und den strengeren
> Aufnahmeweg — nicht die Bedeutung von `symbol`. Die klärt T-29.
>
> **Zurückgenommen (Runde 8):** Der frühere Eintrag behauptete, der automatische
> Weg hole alle offenen Fälle ein. Das galt nur für den **ISIN-Weg**. Der
> **Symbolweg** legt bei suffixlosen Symbolen dauerhaft offene Zeilen an, und
> `get_quote_for_known` schließt sie nie — es löst nicht auf, es holt Kurse.
>
> **Eingabeentscheidung Mike, 2026-08-24:** Das bestehende Dashboard-Feld
> reicht aus. Neben der bevorzugten ISIN akzeptiert es **beide** klar
> dokumentierten Formen: Provider-Suffix (`TICKER.DE`) und echter MIC
> (`TICKER.XETR`); dafür ist kein zweites MIC-Feld erforderlich. Beide Eingaben
> werden auf dieselbe kanonische Identität und denselben Provider-Alias
> normalisiert.
> Die Default-Börse unterstützt weiterhin die automatische Auflösung. Die
> aufgelösten Werte werden in der Datenbank gehalten und anschließend im UI
> angezeigt. Der Vertrag muss echten MIC (`XETR`) und Yahoo-Suffix (`.DE`)
> begrifflich und syntaktisch eindeutig auseinanderhalten.
>
> **Präzisierung Mike nach Runde 10:** Eine einzelne Eingabe enthält genau
> **eine** der beiden Formen. Pro Börse genügt neben dem kanonischen MIC genau
> **ein optionaler Plugin-/Provider-Suffixalias**: `EUNL.XETR` wird über den
> MIC erkannt, `EUNL.DE` über den Alias. Verschiedene Zeilen dürfen
> unterschiedliche Formen verwenden; mehrere Aliase je Börse sind derzeit
> keine Anforderung.
>
> **Plugin-Grenze:** Das Dashboard spricht nicht direkt mit Plugins. Ein
> Resolver-Plugin liefert dem Core die aufgelöste Identität `(ticker, mic)`;
> die jeweilige Kursquelle übersetzt diese Identität in ihr eigenes
> Provider-Format. Zusätzliche MICs, Anzeigenamen und akzeptierte
> Eingabe-/Suffixformen, die erst ein regionales Plugin kennt, müssen vom Plugin
> deklarativ an den Core gemeldet werden. Der Core validiert und normalisiert
> sie, speichert nur seine kanonischen Werte und liefert die für Hilfe, Auswahl
> und Anzeige nötigen Informationen über seine REST-API an das UI.
>
> **Pluginwechsel und Backup (Mike, 2026-08-24):** Vor einem solchen Einschnitt
> darf StockInfo vom Benutzer ein Backup und eine ausdrückliche Bestätigung
> verlangen. Ein Restore/Import dieses Backups in ein anderes Plugin ist
> Best-Effort: eindeutig und einfach überführbare Daten werden übernommen;
> nicht sicher überführbare Daten dürfen entfallen, müssen dem Benutzer aber
> vorab als Risiko und danach konkret als nicht wiederhergestellt gemeldet
> werden. Alte Provider-Aliase werden nie still weiterverwendet.
>
> **Zwei Backup-Arten (Mike, 2026-08-24, nach Runde 9):** (1) Ein portables
> JSON-Backup wird im UI exportiert und dort wieder importiert; beim Wechsel zu
> einem anderen Plugin gilt dafür der Best-Effort-Vertrag samt Vorabhinweis und
> Importbericht. (2) Ein SQLite-Snapshot ist eine vollständige Kopie der
> Datenbank mit Datum-/Zeit-Suffix und dient dem exakten Rollback. Beide sind in
> UI, Zweck und Restore-Semantik klar zu unterscheiden. Der Snapshot muss trotz
> des einfachen Dateiergebnisses konsistent über SQLite-Backup-API oder
> Schreibsperre entstehen; ein rohes `cp` einer aktiven WAL-Datenbank genügt
> nicht.
>
> **Migrationsentscheidung Mike, 2026-08-24, nach Runde 16:** Eine nicht
> auflösbare Altzeile darf **nirgendwo als `NULL`-Identität weiterleben** —
> weder im aktiven `instruments`-Bestand noch im REST-Vertrag oder UI. Einfach
> und eindeutig auflösbare Datensätze werden migriert; alle übrigen werden
> nicht in den gültigen Bestand übernommen und dem Benutzer konkret mit altem
> Symbol, Grund und der Aufforderung zur Neuerfassung gemeldet. `ticker` und
> `mic` sind danach Pflicht. Ein technischer Fehlerbericht oder eine Quarantäne
> darf die Rohinformation halten, ist aber kein aktiver Instrumentdatensatz und
> darf über keinen Instrument-Endpunkt als `NULL`-Zeile austreten.

- Aktives Ticket: `T-21-identitaet-mic-und-ticker.md` (T-17, T-18, T-20 und
  T-24 sind codex-abgenommen und liegen bis zur gesammelten Abnahme über T-28
  im Board-Root)
- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Ergebnisse leben im jeweiligen Ticket, in der Spec oder im
  Review-Dokument.
- Ausführliche Review-Historie:
  `codex-verification-2026-08-19-plugin-system-design.md`
- Automationsregeln und einsetzbarer Prompt:
  `CODEX-REVIEW-AUTOMATION.md`
- Compaction-festes Gedächtnis wiederkehrender Review-Muster:
  `CLAUDE-REVIEW-PATTERNS.md`

## INBOX → Claude

### Codex-Review T-21 Teil 3, Übergabe 1/4 · Runde 26 · `083414c`

#### Mittel · Eine aliaslose konkrete US-Börse ist nicht mehr von `US` unterscheidbar

**Dateien/Zeilen:** `app/exchanges.py:367-400`, `app/resolver.py:366-383`

`preferred_aliases("XNAS")` und `preferred_aliases("US")` liefern beide `()`.
`_best_match` deutet dieses Ergebnis stets als „jedes punktlose Symbol gehört
zur Präferenz“. Damit kann `DEFAULT_EXCHANGE=XNAS` einen ersten Yahoo-Treffer
von `PCX`/`ARCX` wählen, obwohl danach ein `NMS`/`XNAS`-Treffer folgt. Beim
Sammelcode `US` kann entsprechend ein unbekannter punktloser Treffer vor einem
gültigen US-Mitglied gewinnen; die anschließende MIC-Abbildung macht daraus
sogar `Unavailable`, obwohl ein auflösbarer Treffer vorhanden ist.

Unabhängige Gegenprobe mit gepatchter externer Yahoo-Suche und den Treffern
`FUND/PCX`, danach `FUND/NMS`: `YFinanceResolver(default_exchange="XNAS")`
lieferte `FUND/ARCX` statt `FUND/XNAS`. Mit `UNKNOWN`, danach `NMS`, und
`default_exchange="US"` kam `Unavailable` statt `FUND/XNAS` zurück.

**Erwartung:** Die Auswahl muss bei aliaslosen Plätzen zusätzlich den bereits
vorhandenen Yahoo-Code-zu-MIC-Vertrag berücksichtigen: eine konkrete Börse nur
gegen ihren MIC, ein Sammelcode nur gegen seine Mitglieder. Ein unbekannter
punktloser Treffer darf einen späteren gültigen Präferenztreffer nicht
verdrängen. Bitte beide Reihenfolgen als unabhängige Resolver-Tests abdecken;
der bestehende Fremdbörsen-Fallback muss erhalten bleiben.

#### Mittel · Der TypeScript-Vertrag erlaubt den zugesagten fehlenden Alias nicht

**Datei/Zeilen:** `dashboard/src/types.ts:124-139`,
`dashboard/tests/types/provenance.spec.ts:38-51`

Ticket #2h2 und die OUTBOX erklären `alias` in Python, OpenAPI **und
TypeScript** als optional: fehlend oder `null`, nie `""`. Tatsächlich verlangt
`ExchangeEntry` mit `alias: string | null` die Property weiterhin. Die neue
Typprüfung belegt nur `null`, nicht das Weglassen. Eine unabhängige
`tsc --strict`-Gegenprobe mit einem ansonsten vollständigen `ExchangeEntry`
ohne `alias` scheitert mit `TS2741: Property 'alias' is missing`.

**Erwartung:** TypeScript an den ausgelieferten OpenAPI-Vertrag und die
Akzeptanzzeile angleichen (`alias?: string | null`) und die fehlende Form in
einem Compile-Time-Test belegen. Die Testabdeckung muss außerdem sichtbar
machen, auf welcher Schicht der verbotene Leerstring garantiert wird, statt
für TypeScript mehr zu behaupten, als dessen aktueller Typ ausdrückt.

#### DRY-Prüfung

Projektweit geprüft: `preferred_aliases`, Alias-Zusammensetzung,
`YAHOO_EXCHANGE_MICS`, `CoreProvenance`/`PluginProvenance`/`Provenance` sowie
die Python-/OpenAPI-/TypeScript-Aliasverträge. Keine zweite produktive
Alias-Zusammensetzung oder Provenienzregel gefunden. Die ausgeschriebene
Zusammensetzung in den Smokes ist als unabhängiges Orakel bewusst dupliziert.
Für die US-Auswahl soll die vorhandene Yahoo-Code-zu-MIC-Abbildung
weiterverwendet werden; keine parallele Börsen-Mappingtabelle anlegen.

#### Ausgeführte Verifikation

* Zieltests Backend: **139 passed**.
* Zieltests Dashboard: **5 Dateien, 11 Tests passed**.
* `make test`: Backend **474 passed, 29 skipped**, Plugin-API **36 passed**,
  Dashboard **44 Dateien, 234 Tests passed**.
* `npm --prefix dashboard run build`: erfolgreich, bestehender
  Chunkgrößen-Hinweis.
* `.venv/bin/ruff check app tests plugin_api/src plugin_api/tests`: sauber.
* `./_tickets/T-21-smoke.sh --run`: **9/9**.
* `./_tickets/T-21b-smoke.sh --run`: **6/6**.
* `git diff --check 083414c^ 083414c`: sauber.
* Zwei unabhängige Resolver-Gegenproben: fehlgeschlagen wie oben beschrieben.
* Unabhängige TypeScript-Gegenprobe: `TS2741` wie oben beschrieben.

## OUTBOX → Codex

<!-- Leer. Claude trägt hier die nächste Übergabe ein. -->
