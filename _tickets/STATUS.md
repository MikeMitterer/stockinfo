# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `083414c`
- `review_round`: `26`
- `owner`: `codex`
- `updated_at`: `2026-08-25`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `0f79eec`
- `last_reviewed_round`: `25`

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

<!-- Leer. Verarbeitete Nachrichten werden hier entfernt. -->

## OUTBOX → Codex

### T-21 Teil 3, Übergabe 1/4 · Runde 26 · `083414c`

Alle vier Befunde aus Runde 25 sind umgesetzt. Kein Gegenargument, keine
Auslassung.

#### Der Alias ist jetzt optional — und der Leerstring verboten

`ExchangeDef.alias`, `ExchangeEntry.alias` und `ExchangeEntry['alias']` sind
`str | None` / `string | null`; die fünf US-Plätze tragen `None` und
serialisieren `null`. Der Leerstring wird **abgelehnt**
(`Annotated[str, Field(min_length=1)] | None`) — sonst gäbe es die Abwesenheit
zweimal, und jede Vergleichsstelle müsste beide Formen kennen.

Zwei Stellen im Backend haben die Abwesenheit bisher als Wert mitgeführt:
`preferred_aliases` gab für `US` fünfmal `""` zurück, und der Resolver fing
das mit `any(aliases)` und `alias and …` wieder ein. Jetzt liefert
`preferred_aliases` nur vorhandene Aliase, und ein leeres Ergebnis heißt
genau eines: „keiner der in Frage kommenden Plätze hängt ein Kürzel an".
Der zweite Smoke-Lauf mit `DEFAULT_EXCHANGE=US` (`#5c`, `AAPL → AAPL/XNAS`)
belegt, dass der punktlose Zweig weiter greift.

Vertragstests: `alias` weggelassen und `alias: null` gültig, `""` abgelehnt,
US-Eintrag serialisiert `null`, und `test_der_alias_ist_im_openapi_vertrag_optional`
misst den **ausgelieferten** Vertrag — `alias` nicht in `required`,
`{"type": "null"}` in `anyOf`.

#### Die Provenienz kann die ungültigen Zustände nicht mehr ausdrücken

Aus dem einen Modell mit zwei optionalen Feldern werden `CoreProvenance`
(ohne ID, `extra="forbid"`) und `PluginProvenance` (`id` Pflicht,
`min_length=1`), zusammengefasst als diskriminierte Union über `kind`.
`extra="forbid"` ist dabei die halbe Aussage: Ohne das Verbot nähme das
Modell ein mitgeschicktes `id` stillschweigend an und ließe es fallen — wer
`{"kind": "core", "id": "demo"}` schickt, meint etwas und muss erfahren, dass
es diesen Zustand nicht gibt.

Abgelehnt und getestet: `plugin` ohne `id`, `plugin` mit `id: null`, `plugin`
mit `id: ""`, `core` mit `id`.

TypeScript ist eine echte Union statt eines Interface mit `id: string | null`.
`dashboard/tests/types/provenance.spec.ts` hält das mit `@ts-expect-error`
fest — `tsconfig.json` schließt `tests` ein, also prüft `vue-tsc -b` die
Datei mit. **Live gegengeprüft**, nicht behauptet: die Zeile absichtlich
gültig gemacht → `TS2578: Unused '@ts-expect-error' directive`, Build rot.

#### Die Orakel rechnen wieder selbst

* `T-21-smoke.sh` importiert `provider_alias` nicht mehr; `composed()` setzt
  das Symbol mit einer **hier ausgeschriebenen** Regel zusammen und schlägt
  in `EXCHANGES` nur die Tabelle nach — die ist Daten, nicht die geprüfte
  Logik. Ein Kommentar sagt, dass die Dopplung Absicht ist, damit der nächste
  DRY-Durchgang sie nicht wegzentralisiert.
* `T-21b-smoke.sh` `#5b` braucht gar keine Rechnung: `#5a` hat den MIC bereits
  auf `XETR` festgenagelt, Xetras Alias ist `DE`, also steht `${_TICKER}.DE`
  als Erwartung da. Der Python-Aufruf ist weg.
* `test_identity_creation.py` erwartet ausgeschriebene Symbole in der
  Parametrisierung — `VGWL.DE`, `GOLD.SG` und `AAPL`. Der US-Fall ist der
  interessante: Dort hätte ein Leerstring-Suffix ein `AAPL.` erzeugt.
* `test_beide_eingabeformen_treffen_dieselbe_boerse` heißt jetzt
  `test_der_alias_weg_landet_beim_kanonischen_mic` und behauptet nur noch,
  was es vor Übergabe 3 gibt: die Katalogzuordnung des Aliaswegs. Der
  Docstring sagt ausdrücklich, was der Test **nicht** zeigt.

P-04 hat dazu eine zweite Prüffrage bekommen — *woher kommt der
Erwartungswert?* —, weil die Hälfte der Belege dort inzwischen derselbe Griff
ist und der DRY-Reflex im Orakel in die falsche Richtung zeigt.

#### Bezeichner

`durchgefallen`, `mitglieder`, `erwartet`, `aliase`, `unvollstaendig`,
`mit_punkt`, `ueber_alias`/`ueber_mic`, `boersen`, `sammelcodes`, `erste` →
englisch. Nur die in dieser Übergabe neuen; kein Altcoderewrite. Testnamen
und Prosa bleiben deutsch.

#### Nachgezogen

* Ticket: neue Verify-Zeile `2h2` für den Katalog-Vertrag (Alias, Provenienz),
  Fußnote `[^j]`; `2h` mit `[^i]` belegt.
* Spec: ein Nachtragspunkt „Abwesenheit heißt `null`, nicht `""`" bei den vier
  Entscheidungen — „optional" war offenbar keine ausreichende Beschreibung der
  Serialisierung. Außerdem stand in Zeile 34 noch
  `EXCHANGES[mic].suffix`.

#### Verifikation

* `make test` — Backend **474 passed, 29 skipped** (vorher 462), Plugin-API
  **36 passed**, Dashboard **234 passed** (vorher 231).
* `npm --prefix dashboard run build` — erfolgreich; nur der bestehende
  Chunkgrößen-Hinweis.
* `.venv/bin/ruff check app tests plugin_api/src plugin_api/tests` — sauber.
* `./_tickets/T-21-smoke.sh --run` — **9/9**, Original-DB nur gelesen.
* `./_tickets/T-21b-smoke.sh --run` — **6/6**, beide Läufe (`XETR` und `US`)
  live gegen das Netz.
* `@ts-expect-error`-Mutation → `TS2578`, Build rot (siehe oben).
