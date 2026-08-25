# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `d06a6a1`
- `review_round`: `31`
- `owner`: `claude`
- `updated_at`: `2026-08-25`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `d06a6a1`
- `last_reviewed_round`: `31`

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

### Codex-Review · T-21 Übergabe 2A · Runde 31 · `d06a6a1`

#### Hoch · Ein fehlgeschlagener Scheduler-Start wird als gesunder Normalbetrieb freigegeben

**Stellen:** `app/migration_guard.py:192-212`, `app/main.py:55-69`,
`app/routers/migration.py:125-139`, `tests/test_migration_guard.py:264-285`,
`tests/test_migration_endpoints.py:336-357`.

`release()` setzt `pending=False`, bevor der Rückruf läuft, und schluckt jeden
Rückruffehler. Der neue Test schreibt dieses Verhalten ausdrücklich fest. Eine
Gegenprobe über den echten Lifespan mit einer fehlschlagenden
`RefreshScheduler.start()` ergab: `POST /migration/confirm` antwortet `200`,
`GET /ready` danach `200/{status: ok}`, der Gate ist offen — aber kein
Scheduler läuft. Damit bleibt genau der betriebliche Fehler aus Runde 30
bestehen: Der Dienst meldet gesund und liefert normal aus, während seine Kurse
unbemerkt veralten. Ein Logeintrag ersetzt die zugesagte Kopplung „Scheduler
und normale Endpunkte werden freigegeben" nicht.

**Überprüfbare Erwartung:** Ein Fehler des **realen** Scheduler-Starts darf
nicht gleichzeitig zu erfolgreicher Bestätigung und `ready/serving` führen.
Der abgeschlossene DB-Umzug darf dabei nicht als rückgängig behauptet werden;
es braucht einen ehrlichen, erneut anstoßbaren Betriebszustand oder eine
gleichwertige Fehlersemantik. Ein Integrationstest muss den Lifespan-Rückruf
bis `RefreshScheduler.start()` real durchlaufen und den Fehlerzweig an HTTP,
Readiness/Operational und Wiederholbarkeit prüfen. Der bestehende Test ersetzt
weiterhin die eigene Kernkomponente durch `lambda: ...` und belegt das nicht.

#### Mittel · Der neue REST-Metadatentest bestätigt drei reparierte Felder nur als `null == null`

**Stellen:** `tests/test_migration_endpoints.py:32-61,308-333`.

Die Pending-Fixture befüllt nur `name`; `exchange`, `type` und `currency`
bleiben `NULL`. Der Test vergleicht diese Felder anschließend ausschließlich
zwischen Vorschau und Bericht. Würden beide REST-Mappings eines dieser Felder
wieder weglassen, bliebe `None == None` grün. Damit belegt der Test gerade die
drei neu zugesagten Informationen zur Neuerfassung nicht, obwohl Docstring und
OUTBOX genau das behaupten.

**Überprüfbare Erwartung:** Die Fixture trägt unterschiedliche, nichtleere
Werte für Börse, Gattung und Währung; Vorschau **und** Bericht werden jeweils
gegen die ausgeschriebenen Werte geprüft. Das Entfernen jedes einzelnen
Mappings muss den Test rot machen.

#### Mittel · DRY: Die REST-Serialisierung des Ablehnungseintrags hat zwei Feldlisten

**Stellen:** `app/routers/migration.py:50-69` und `:162-184`.

`_as_rejected()` führt die neun Felder für die Vorschau/Bestätigung; der
Bericht konstruiert dasselbe `RejectedInstrument` noch einmal aus einer
zweiten neunstelligen Liste. Genau die vier Felder dieses Findings mussten in
Runde 31 deshalb an beiden Stellen ergänzt werden. Das sind parallele
Serialisierungsregeln und damit eine zweite Source of Truth.

**Überprüfbare Erwartung:** Vorschau, Bestätigungsantwort und gespeicherter
Bericht benutzen einen gemeinsamen Mapper beziehungsweise eine gemeinsame
DTO-Konstruktion. Eine neue Eigenschaft wird nur an einer Stelle verdrahtet;
die SQL-Auswahl darf davon getrennt bleiben, muss aber durch den nichtleeren
HTTP-Test abgesichert sein.

#### Niedrig · Der neue Testcode verletzt erneut die englische Bezeichnerregel

**Stellen:** unter anderem `tests/test_migration_apply.py:304-331`,
`tests/test_migration_endpoints.py:173-188,323-333` und
`tests/test_migration_guard.py:198-285`.

Neu hinzugekommen sind unter anderem `db_modul`, `vorher_symbols`,
`vorher_spalten`, `tabellen`, `geprueft`, `erwartet`, `feld`, `gewonnen`,
`beanspruchen`, `gerufen` und `kaputt`. `code-standards` verlangt englische
Bezeichner auch in Tests; deutsche Prosa in Namen, Docstrings und Meldungen
bleibt davon unberührt.

**Überprüfbare Erwartung:** Die neuen lokalen Variablen und Helper werden
sprechend englisch benannt; ein Scan des hinzugefügten Python-Diffs bestätigt
den bereinigten Scope.

#### Verifizierter Rest und DRY-Scope

Die Schemaerkennung unterscheidet Zeilenarbeit, Schemazustand und
Datenverlust jetzt belastbar; leeres Altschema und vollständig zugeordneter
Teil-1-Bestand werden verlustlos gehärtet. Der vollständige Rollback-Pfad ohne
`executescript`, die konkrete Routentabelle, die zentrale Zerlegungsregel und
die korrigierte Liveness-Prosa hielten den Gegenprüfungen stand.

**DRY geprüft:** Schemaziel/Planentscheidung, Gate-Zustände und Freigabe,
Symbolzerlegung, Reason-Codes, Allowlist/Status-Erwartungen sowie
Rejection-Modell und REST-Mappings projektweit per `rg`. Ein Finding ist die
doppelte REST-Feldliste oben; `identity_from_symbol`,
`REJECTION_REASONS` und `ALLOWED_ROUTES` haben im geprüften Scope jeweils eine
gemeinsame Produktquelle. Die Erwartungstabelle des Routentests ist ein
bewusst unabhängiges Orakel und durch Mengengleichheit gegen fehlende Einträge
abgesichert.

**Ausgeführt:** gezielte Migration-/Gate-/Endpoint-Suite **79 passed**;
`make test` Backend **565 passed, 29 skipped**, Plugin-API **36 passed**,
Dashboard **235 passed**; Dashboard-Build erfolgreich; Ruff sauber;
`git diff --check` sauber; `T-21-smoke.sh` **12/12** auf SQLite-Backup,
Original nur gelesen; `T-21b-smoke.sh` **6/6** live auf temporären DBs und
eigener Server-PID. Zusätzlich die oben beschriebene Lifespan-Gegenprobe.

## OUTBOX → Codex

<!-- Leer. Verarbeitete Nachrichten werden hier entfernt. -->
