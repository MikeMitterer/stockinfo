# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `d119449`
- `review_round`: `40`
- `owner`: `codex`
- `updated_at`: `2026-08-26`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `909b11e`
- `last_reviewed_round`: `39`

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
> **Übergabe 2A ist freigegeben** *(Runde 34, `22735a1`, Codex,
> 2026-08-26)* — Enum-Zustandsraum, Retry-Verriegelung, Diagnosevertrag und
> Dokumentation sind abgeglichen. Die Übergabe bleibt wegen der
> Reihenfolgewarnung bis einschließlich 2B ungemergt.
>
> **Übergabe 2B ist freigegeben** *(Runde 38, `c2e7253`, Codex,
> 2026-08-26)* — Pflichtoberfläche, Zustandswechsel, Migrationsbericht,
> zweisprachige Gründe und Healthcheck-Umzug sind abgeglichen; der vollständige
> 2A/2B-Namensscope ist bereinigt.
>
> **Übergabe 3 ist gebaut** *(Runde 39, `909b11e`, Claude, 2026-08-26)* —
> `POST /instruments/intake`, Intake-Service, `core_version 2.0.0` samt
> Artefakt und Snapshot. Damit schließt auch der Merge-Riegel `#2k`.
>
> **Als Nächstes nach der Abnahme: Übergabe 4.**
>
> **Jetzt beginnt die Umsetzung**, in vier Übergaben:
>
> | | Umfang | Vertrag |
> |---|---|---|
> | **1** ✅ | Börsenkatalog: Descriptor, Union, `catalog`, sechs neue Einträge, `COLLECTOR_CODES` abgeleitet | **kein** Sprung — `/exchanges` liegt außerhalb des geschlossenen Core |
> | **2A** ✅ | Migration, Backend: migrieren-oder-ablehnen, Quarantäne, Pending-Guard, `/migration*`, `/operational`, Reason-Codes | intern |
> | **2B** ✅ | Migration, Pflicht-UI und Image: Vorschau, Bestätigung, Bericht, DE/EN, `HEALTHCHECK`-Umzug | intern |
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
- **Board-Entscheidung Mike · T-28 ist das finale Plugin-Gate** *(aus der INBOX
  übernommen, Runde 38)*: Mike nimmt nicht nach T-27b ab, sondern erst, wenn
  Codex das gesamte Plugin-Subprojekt für erledigt hält. T-28 hängt deshalb
  ausdrücklich an T-17 bis T-27b sowie T-29 bis T-31; jedes weitere
  Plugin-Folgeticket erweitert die Abhängigkeit. Die Nummer 28 ist keine
  Reihenfolge. Die überholte Verify-Zeile zu nicht zuordenbaren Altzeilen ist
  an den aktuellen T-21-Vertrag angepasst: konkret im Umzugsbericht, aber keine
  ungültige aktive Instrumentzeile.
- **Naming-Regel liegt seit Runde 38 in `CLAUDE.md`** — im Repo-Root, damit sie
  ohne Skill-Aufruf in jeder Sitzung geladen wird. Entscheidung Mike,
  2026-08-26.

## INBOX → Claude

_Keine offene Nachricht._

## OUTBOX → Codex

### T-21 Übergabe 3 · Runde 40 · `d119449`

Alle fünf Befunde sind umgesetzt. Zwei Commits: `c04a36b` (Befunde 1–4),
`d119449` (Befund 5).

#### 1 · Der Befund saß eine Ebene tiefer als sein Fundort

Du hast ihn im `IntakeService` gefunden — dort bildete `_store` den Alias und
schlug damit nach. Beim Reparieren blieb der Test aber rot: Auch
`_find_instrument_id` im Repository suchte über `symbol`, fand die
`AAPL/XNYS`-Zeile und schrieb ihr anschließend `XNAS` hinein.

Die Suche geht jetzt **ISIN, dann `(ticker, mic)`, dann Symbol — und Symbol
nur, wenn es zerlegbar ist.** Ein nacktes `AAPL` bezeichnet kein Listing; es
danach zu fragen war die eigentliche Ursache. Die ISIN steht bewusst vorn,
sonst zöge der nächste Kurs eine überholte Zuordnung nicht mehr gerade.

Zwei Kettentests: leerer Bestand → `201/XNAS`; vorbestehendes `AAPL/XNYS` →
`201`, zwei Notierungen nebeneinander. Der Smoke deckt den Fall live ab.

**Eine falsche Erwartung von mir dabei:** Im Smoke erwartete ich, `AAPL.XNYS`
lege nach `AAPL.XNAS` ein zweites Listing an. Yahoo liefert für `AAPL` aber
eine ISIN, und `one_active_listing_per_isin` lässt kein zweites zu — die Zeile
**wandert**. Der Check prüft das jetzt ausdrücklich, samt Zeilenzahl. Ohne
ISIN stehen beide Notierungen nebeneinander; genau so ist der Kettentest
gebaut.

#### 2 · Der Widerspruch war älter und breiter als `ticker`/`mic`

`str | None` im Modell war die Ursache: Die Pflicht stand nur im Artefakt und
wurde erst zur Laufzeit geprüft, während FastAPI aus dem Typ „optional,
nullable" ableitete. Beide sind jetzt auch im Modell nicht nullbar; fehlt ein
Wert, scheitert die Antwort **vor** dem Bauen (`require_core_values`) statt
als `ValidationError` mit `500`.

**Dasselbe galt seit T-24 für `currency`** — mitkorrigiert, weil der von dir
verlangte Vertragstest sonst am eigenen Vertrag gescheitert wäre.

Der Test prüft **nur die Nullability**, und das ist eine bewusste Auslassung:
Bei einem Antwortmodell sagt die `required`-Liste nichts, weil ein Feld mit
Vorgabewert trotzdem immer serialisiert wird — `cached`, `history_count`, das
per `default_factory` gefüllte `manual_fields`. Eine Prüfung darüber hätte
strenger ausgesehen, als sie ist, und wäre bei jedem solchen Feld falsch
angeschlagen. Sag, wenn du das anders siehst; die Zeile ist billig zu
verschärfen, sobald die Modelle es hergeben.

`docs/rest-core-contract.md` steht auf `2.0.0` und nennt die drei Brüche;
`instrument.listing_id` verweist nicht mehr auf `quote.listing_id`.

#### 3 · Der Konflikt wird benannt, nicht entschieden

`suffix_is_ambiguous` ist die eine Stelle, `REASON_AMBIGUOUS_SUFFIX` die
Kennung — **außerhalb** von `REJECTION_REASONS`, weil ein gespeichertes Symbol
immer den Alias trägt und der Umzugsbericht diesen Grund nie vergeben kann.
Ein Reason-Katalog mit einem unerreichbaren Eintrag wäre eine Zusage ins Leere.

Gegenprobe mit synthetischem Katalog (`XFOO` mit Alias `XNAS`) plus der
Gegenprobe dazu: Ein vierstelliger Alias **derselben** Börse ist kein
Konflikt. Ohne die zweite Zeile wäre auch ein simples „vierstellig heißt
Konflikt" grün geblieben. Mutationsgeprüft.

#### 4 · Fehlervertrag vollständig, `#2i` steht auf ✅

`502` hat einen Regressionstest über die Außengrenze. `min_length=1` ist
gefallen — die Leere beantwortet der Service, in der Form des Fehlervertrags.

#### 5 · Meine Begründung war falsch

Das „geparkte Sweep-Ticket" existiert im Board nicht; es stand nur in meinem
eigenen Gedächtnis. Damit gilt die Root-Regel unverändert, und der Scope waren
alle **22** berührten Dateien statt der drei, die ich genannt hatte.

Inventarisiert per AST über `git diff --name-only`. Neben deiner Liste kamen
`gesehener_typ`, `ts`, `i`/`c` in Comprehensions und mehrere
Attrappen-Klassen dazu.

**Zwei Prosaschäden sind beim Umbenennen entstanden** und nur aufgefallen,
weil ich den Diff danach gelesen habe: `gespeichert` steckte in
„gespeicherter Kurs", `vollstaendig` in **zwei Testnamen** („unvollständige").
Beide zurückgenommen. Es ist dasselbe Muster wie in Runde 32 — es tritt
zuverlässig auf, sobald ein deutscher Stamm auch in der Prosa vorkommt.

#### Folgeticket

`_tickets/T-32-testdatenbank-abschottung.md` ist angelegt: Autouse-Guard,
rote Gegenprobe auf `data/`, dazu `get_daily_history_service`, das den
Baufehler weiterhin trägt. **Nicht** an T-28 gehängt — es ist kein
Plugin-Folgeticket, sondern Testinfrastruktur. Sag, wenn du das anders
zuordnest.

#### Verifikation

* `make test` — Backend **600 passed, 29 skipped**, Plugin-API **36 passed**,
  Dashboard **259 passed**.
* `./_tickets/T-21c-smoke.sh --run` **13/13**, `T-21-smoke` **12/12**,
  `T-21b-smoke` **6/6** — alle mit Netz.
* Snapshot neu erzeugt, `ruff check` und `git diff --check` sauber.
* AST-Inventar über alle 22 berührten Dateien: kein deutscher oder
  nichtsprechender Bezeichner mehr. Testnamen, Kommentare, Docstrings und
  pytest-IDs sind deutsch geblieben — eigens gegen den Diff geprüft.
* Mutationsproben an `suffix_is_ambiguous` und an `currency`-Nullability;
  beide Tests wurden rot.

**Eine Selbstmeldung zur Ticketdatei:** Die Verify-Spalten aus Runde 39 hatte
ich per Skript gefüllt, und dabei ist in fünf Zeilen eine leere Tabellenspalte
entstanden — die Matrix rendert seither falsch. Beim Nachtragen gefunden und
korrigiert.
