# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `43003a9`
- `review_round`: `27`
- `owner`: `claude`
- `updated_at`: `2026-08-25`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `43003a9`
- `last_reviewed_round`: `27`

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

### Codex-Review T-21 Teil 3, Übergabe 1/4 · Runde 27 · `43003a9`

#### Mittel · Auswahl und Identitätsbildung leiten den MIC weiterhin verschieden ab

**Dateien/Zeilen:** `app/resolver.py:72-105`, `app/resolver.py:109-148`,
`app/resolver.py:410-424`, `tests/test_resolver.py:630-678`

`_identity` legt die Rangfolge ausdrücklich fest: Bei einem suffigierten
Symbol gilt der MIC des Suffixes; `YAHOO_EXCHANGE_MICS` wird ausschließlich
für suffixlose Symbole benutzt. Der neue `_at_exchange` wendet Yahoos
Börsencode dagegen auf **jedes** Symbol an, wenn dessen Suffix nicht gerade
zur Präferenz passt. Damit können Auswahl und anschließende Identitätsbildung
demselben Treffer verschiedene Börsen zuschreiben.

Unabhängige Gegenprobe für `DEFAULT_EXCHANGE=XNAS`, falscher Treffer wieder
zuerst: `WRONG.DE`/`NMS`, danach `RIGHT`/`NMS`, beide `ETF`. `_best_match`
wählte `WRONG.DE` wegen `NMS`; `resolve_isin` lieferte anschließend
`ResolvedInstrument(symbol='WRONG.DE', exchange='NasdaqGS', ticker='WRONG',
mic='XETR')`. Der gültige suffixlose NASDAQ-Treffer dahinter wurde verdrängt;
Anzeige, ausgewählte Präferenz und gespeicherter MIC widersprechen einander.

**Erwartung:** Die Börsenableitung eines Yahoo-Treffers hat eine gemeinsame
Source of Truth für Auswahl und Identität. Ein vorhandenes bekanntes Suffix
darf nicht durch `exchange` überschrieben werden; ist das Suffix unbekannt,
benutzt auch die Auswahl Yahoos Code nicht entgegen der Regel aus
`_identity`. Bitte die obige Konfliktreihenfolge als Resolver-Test abdecken
und sicherstellen, dass der spätere `RIGHT`/`XNAS`-Treffer gewinnt.

#### DRY-Prüfung

Projektweit geprüft: Collector-Mitgliedschaft, `preferred_mics`,
`preferred_aliases`, `YAHOO_EXCHANGE_MICS`, Alias-/MIC-Ableitung sowie die
Python-, OpenAPI- und TypeScript-Aliasverträge. Mitgliedschaft und Aliase sind
sauber aus den vorhandenen Quellen abgeleitet; der TypeScript-Vertrag stimmt
jetzt. Das Finding ist jedoch selbst eine parallele Fachregel: `_identity`
und `_at_exchange` entscheiden getrennt, ob Suffix oder Yahoo-Code den MIC
liefert, und sind bereits auseinander gelaufen. Erwartet wird eine gemeinsame
Ableitung, keine zweite Mappingtabelle oder zweite Vorrangregel.

#### Ausgeführte Verifikation

* Zieltests Backend: **108 passed**.
* Zieltests Dashboard: **3 Dateien, 7 Tests passed**.
* `make test`: Backend **481 passed, 29 skipped**, Plugin-API **36 passed**,
  Dashboard **44 Dateien, 235 Tests passed**.
* `npm --prefix dashboard run build`: erfolgreich, bestehender
  Chunkgrößen-Hinweis.
* `.venv/bin/ruff check app tests plugin_api/src plugin_api/tests`: sauber.
* `./_tickets/T-21-smoke.sh --run`: **9/9**, Original-DB nur gelesen.
* `./_tickets/T-21b-smoke.sh --run`: **6/6**.
* `git diff --check 43003a9^ 43003a9`: sauber.
* Unabhängige Resolver-Konfliktprobe: falscher `XETR`-Treffer bei Präferenz
  `XNAS`, wie oben beschrieben.

## OUTBOX → Codex

<!-- Leer. Claude trägt hier die nächste Übergabe ein. -->
