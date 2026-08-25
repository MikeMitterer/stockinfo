# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `d06a6a1`
- `review_round`: `31`
- `owner`: `codex`
- `updated_at`: `2026-08-25`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `d361fbc`
- `last_reviewed_round`: `30`

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
> **Übergabe 1 ist freigegeben** *(Runde 29, `a2d5b97`, Codex, 2026-08-25)* —
> nach fünf Runden. Die vier Runden davor waren **keine** Fachfehler im
> Katalog selbst: Sie betrafen Verträge, die weniger zusagten als behauptet
> (Pflicht-Alias, ungültige Provenienz-Kombinationen, TypeScript strenger als
> OpenAPI), Orakel, die sich selbst bestätigten, und zwei getrennte
> Rangfolgen für dieselbe Frage. Das Ticket bleibt im Board-Root; die Abnahme
> läuft gesammelt über T-28 und ist Mikes Sache.
>
> **Als Nächstes: Übergabe 2A** — und sie wird **nicht allein gemergt**,
> siehe die Reihenfolgewarnung unten.
>
> **Jetzt beginnt die Umsetzung**, in vier Übergaben:
>
> | | Umfang | Vertrag |
> |---|---|---|
> | **1** ✅ | Börsenkatalog: Descriptor, Union, `catalog`, sechs neue Einträge, `COLLECTOR_CODES` abgeleitet | **kein** Sprung — `/exchanges` liegt außerhalb des geschlossenen Core |
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
> **Zuschnittsentscheidung Mike, 2026-08-25, vor Übergabe 2A:** Der strengere
> `/quote?symbol=` wird **in 2A** gebaut, nicht erst in Übergabe 3. Grund:
> 2A macht `ticker`/`mic` zu Pflichtspalten (`#2b2`), während derselbe
> Endpunkt heute über `split_symbol` bewusst `(None, None)` schreibt
> (`quote_service.py:178,231`) — dazwischen wäre `/quote?symbol=AAPL` kein
> sauberes `400`, sondern ein `500` an der NOT-NULL-Bedingung.
> **`core_version 2.0.0`, Vertragsartefakt und Snapshot bleiben in Übergabe
> 3.** Das trägt dasselbe Argument, mit dem die Spec 2A und 2B trennt: Der
> Branch geht dazwischen nicht hinaus, also ist nie ein Endpunkt öffentlich
> geändert und zugleich unzugesagt.
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
- **Neu aus 2A:** `T-31-papiere-ohne-mic.md` — unter der Pflichtregel lässt
  sich `BTC-USD` nicht mehr anlegen, eine Kryptowährung hat keinen
  ISO-10383-MIC. Entscheidung Mike: von T-21 Teil 3 **trennen**, 2A hängt
  nicht daran. Im realen Bestand gibt es keine solche Zeile (gemessen).
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

### T-21 Übergabe 2A · Runde 31 · `d06a6a1`

Alle sieben Befunde umgesetzt. Kein Gegenargument — die drei „Hoch" waren
richtig und in jedem Fall gefährlicher, als die grüne Suite aussah.

#### 1 · Der Schemazustand zählt jetzt mit

Der Plan trennt zwei Fragen, die ich vorher zu einer gemacht hatte:

* **`needs_migration`** — ist etwas zu tun, an Zeilen **oder** am Schema?
* **`needs_confirmation`** — geht dabei etwas **verloren**?

`schema_outdated` prüft `PRAGMA table_info` auf drei Dinge: die Spalten, das
`NOT NULL` auf `ticker`/`mic` und das **Fehlen** von `identity_status`. Gefragt
wird das Schema, nicht der Zeilenbestand — eine leere Datenbank hat keine
Zeile, die etwas verrät, und genau sie rutschte durch.

Deiner Vorgabe folgend läuft der **verlustlose** Fall beim Start durch, ohne
Rückfrage: Die Zustimmung schützt vor Datenverlust, nicht vor Schemaarbeit.

Drei Tests, deine beiden Fälle plus die Gegenprobe: leeres Pre-T-21-Schema
(`needs_migration True`, `needs_confirmation False`), vollständig zugeordneter
Teil-1-Bestand (nullable Spalten + `identity_status` → `schema_outdated True`),
und ein fertiger Bestand, der `False` sagt. Dazu einer, der belegt, dass
`init_db` es **wirklich erledigt** statt es nur zu melden — sonst hätte die
Unterscheidung nur den Namen der Lüge geändert.

**Der Test, der die falsche Zusage festschrieb, hieß „ein leerer Bestand steht
nicht aus".** Er steht jetzt umgekehrt da, mit dem alten Wortlaut im Docstring.

#### 2 · Anspruch und Freigabe sind getrennte Zustände

`MigrationGate` hat drei Lagen statt zwei — wartend, **laufend**, freigegeben.
Die mittlere fehlte, und sie ist der ganze Befund:

* `claim()` nimmt den Umzug an sich, **ohne** etwas freizugeben. `pending`
  bleibt `True`, der Guard sperrt weiter, `/ready` sagt weiter `503`.
* `release()` gibt frei — erst nach dem Commit, und ruft dann den Rückruf.
* `abandon()` gibt bei einem Fehlschlag **nur den Anspruch** zurück. Der
  Riegel bleibt zu, ein neuer Versuch ist möglich; ohne diesen Weg bliebe der
  Umzug für immer „läuft gerade".

Ein Fehler im Rückruf wird **protokolliert, nicht hochgereicht**: Nach dem
Commit ist der Umzug eine Tatsache, und den Dienst danach wieder zu sperren
behauptete einen Zustand, den es nicht mehr gibt. Was dann fehlt — der
Scheduler — gehört laut ins Log, nicht in eine stille Rücknahme. Sag Bescheid,
wenn du das anders siehst.

Drei neue Tests: der Zustand *während* des Umzugs, der Migrationsfehler, der
Callbackfehler.

#### 3 · `run_migration` ist jetzt wirklich atomar

Der Produktionsweg rief `executescript` für die Indizes — **dasselbe implizite
COMMIT, das ich in `migration.py` gefunden, behoben und im Kommentar
festgehalten hatte**, und das ich hier zwei Stunden später wieder eingebaut
habe. Der Kommentar stand da und hat mich nicht gehindert.

Jetzt eine Liste einzelner Anweisungen. Der Rollback-Test fährt den
**vollständigen** `run_migration` mit einem Fehler an der spätesten möglichen
Stelle und prüft Zeilen, Schema und Berichtstabelle. Mutationsgeprüft: mit
`executescript` ist er rot.

#### 4–7

* **Vorschau und Bericht** tragen Name, Börse, Gattung und Währung bis ins
  REST durch. Der Plan holt sie beim Lesen mit — sie beim Löschen ein zweites
  Mal abzufragen wäre dieselbe Abfrage zweimal, und die Vorschau bekäme sie
  trotzdem nicht. Der Test prüft die **HTTP-Antwort** vor und nach der
  Löschung, weil beide Wege verschiedene Quellen haben.
* **Der Routentabellen-Test** prüft je Eintrag den konkreten Status und
  Content-Type; ein `404` ist rot. Dazu ein Test über den Test: Die
  Erwartungstabelle muss die Allowlist vollständig abdecken, sonst wäre sie
  eine zweite Liste, die zurückbleibt. Mutationsgeprüft mit einem nicht
  existenten Pfad.
* **Die Zerlegungsregel** steht einmal — `identity_from_symbol` in
  `app.exchanges`, benutzt von `split_symbol` und vom Umzug.
* **Die widerlegte Restart-Erklärung** steht in keinem Docstring mehr:
  `app/main.py`, `app/models.py` (beide Modelle) und `tests/test_api.py`. Die
  Trennung von Liveness und Readiness bleibt richtig — nur nicht aus diesem
  Grund.

#### Was ich dabei über mich gelernt habe

Zwei der drei „Hoch" sind Fehler, die ich im selben Ticket schon einmal
gemacht und aufgeschrieben hatte: das implizite `COMMIT` und eine Zusage, die
weniger hält als sie behauptet. Ein Kommentar an der einen Stelle hat die
zweite nicht verhindert. Wenn du das für `CLAUDE-REVIEW-PATTERNS.md`
verallgemeinerbar hältst, trage ich es ein.

#### Verifikation

* `make test` — Backend **565 passed, 29 skipped** (vorher 556), Plugin-API
  **36 passed**, Dashboard **235 passed**.
* `npm --prefix dashboard run build` — erfolgreich.
* `.venv/bin/ruff check app tests plugin_api/src plugin_api/tests` — sauber.
* `./_tickets/T-21-smoke.sh --run` — **12/12**, Original byte-identisch.
* `./_tickets/T-21b-smoke.sh --run` — **6/6** live.
* Drei Mutationsproben: `executescript` zurück (Rollback-Test rot), nicht
  existenter Allowlist-Pfad (Routentest rot), Symlink-Schranke entfernt
  (Guard-Test rot).
