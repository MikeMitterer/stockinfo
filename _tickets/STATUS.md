# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `909b11e`
- `review_round`: `39`
- `owner`: `claude`
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

### Review T-21 Übergabe 3 · Runde 39 · `909b11e` — Änderungen nötig

Die Richtung stimmt, aber der Aufnahmeweg und sein Vertrag sind noch nicht
freigabefähig. Bitte die Befunde in dieser Reihenfolge abarbeiten.

#### 1 · Hoch — aliaslose MIC-Eingaben verlieren genau die genannte Börse

`identity_from_input("AAPL.XNAS")` liefert korrekt `("AAPL", "XNAS")`.
`IntakeService._store()` wirft diese Identität danach jedoch weg, bildet mit
`provider_alias()` nur `"AAPL"` und ruft `store_by_symbol()` auf
(`app/services/intake_service.py:140-144`). Damit entscheidet wieder der
mehrdeutige Symbolpfad:

* auf leerem Bestand antwortet `POST /instruments/intake` für `AAPL.XNAS` mit
  **500** und legt nichts an;
* liegt bereits `AAPL/XNYS` vor, antwortet dieselbe Eingabe mit **200 und
  `mic: XNYS`** — also mit einem anderen Handelsplatz als ausdrücklich
  eingegeben.

Das verletzt die verpflichtende Zeile `AAPL.XNAS → AAPL/XNAS` aus Entwurf und
Testplan. Die kanonische Eingabeidentität muss bis Cache, Quote-Service und
Repository erhalten bleiben; Nachschlagen und Konfliktauflösung dürfen hier
nicht wieder nur über `symbol` laufen. Ergänze echte Kettentests für
`AAPL.XNAS` auf leerem Bestand **und** bei einem vorbestehenden `AAPL/XNYS`
sowie den aliaslosen MIC-Fall im T-21c-Smoke.

#### 2 · Hoch — das 2.0-Vertragspaket widerspricht sich

`contract/core-contract.json` erklärt `quote.ticker` und `quote.mic` zu
nicht-nullbaren Pflichtfeldern. Das veröffentlichte OpenAPI-Schema führt beide
aber als optional und nullable; seine `required`-Liste enthält nur `symbol`,
`price`, `quote_time`, `fetched_at`. Ein generierter Client darf damit genau
den Zustand annehmen, den 2.0 abschafft.

Zusätzlich ist die ausdrücklich zu Übergabe 3 gehörende Vertragsprosa nicht
mitgezogen: `docs/rest-core-contract.md` steht weiter auf **1.0.0**, nennt nur
fünf Modelle/den alten Instrument-Endpunkt und schließt pauschal alle
Dashboard-Schreibvorgänge aus dem Core aus. Im Artefakt verweist die Bedeutung
von `instrument.listing_id` außerdem auf das nicht vorhandene
`quote.listing_id`.

Trenne nötigenfalls internes Beschaffungsmodell und öffentliches
Response-Modell, aber bring Artefakt, OpenAPI und Prosa auf **eine** Zusage.
Ein Vertragstest muss Pflicht/Nullability des Artefakts gegen OpenAPI halten;
ein bloß neu erzeugter Snapshot bestätigt sonst nur beide Seiten ihres eigenen
Widerspruchs.

Die Designentscheidung, `listing_id` nur auf `instrument` zuzusagen, ist
fachlich akzeptiert. Zu korrigieren sind die widersprechenden Verbraucher.

#### 3 · Mittel — Alias/MIC-Kollision wird still entschieden statt abgelehnt

Der freigegebene Entwurf verlangt bei einem Token, das MIC der einen und Alias
einer anderen Börse ist, einen benannten Konflikt. `identity_from_input()`
schreibt stattdessen ausdrücklich „Der Alias gewinnt“. Eine Gegenprobe mit
einem Katalogeintrag `XFOO(alias="XNAS")` deutet `AAPL.XNAS` still als
`AAPL/XFOO`.

`test_kein_token_ist_alias_und_mic_zugleich` misst nur den heutigen
Core-Katalog; er implementiert den zugesagten Konflikt für plugin-erweiterte
Kataloge nicht. Baue die Konfliktkennung samt Gegenprobe ein, einschließlich
eines vierstelligen Alias. Die Trennung `identity_from_input` gegen
`identity_from_symbol` ist grundsätzlich richtig; nur ihre Vorrangregel nicht.

#### 4 · Mittel — der zugesagte Fehlervertrag ist nicht vollständig belegt

Verify `#2i` verlangt 201, 200, 400 und 502 über die echte Kette. Der
eingecheckte Test deckt 502 nicht ab. Meine manuelle Außengrenzenprobe ergab
zwar korrekt `502 {"code":"quote_unavailable", ...}`, ersetzt aber keinen
Regressionstest.

Außerdem antwortet `identifier: ""` wegen `min_length=1` mit FastAPIs
untypisiertem **422**, während `identifier: " "` den vorgesehenen
`400/identifier_empty` liefert. Damit ist `REASON_EMPTY` gerade für die exakt
leere Eingabe unerreichbar. Lege fest und teste eine konsistente öffentliche
Fehlerform; danach darf `#2i` von `◑` auf ✅.

#### 5 · Mittel — das AST-Inventar widerlegt den geparkten Naming-Scope

Die Root-Regel sagt ausdrücklich: Was in einer Datei angefasst wird, zieht
mit. Ein AST-Inventar der **tatsächlich berührten** Python-Dateien findet
deutsche oder nichtsprechende Bezeichner nicht nur in den drei genannten
Tests, sondern mindestens in:

* `app/main.py` (`laufende`, `scheduler_sperre`, `scheduler_starten`),
  `app/services/quote_cache.py` (`feld`, `manuell`, `wirksam`, `zeile`);
* `tests/test_exchanges.py` (`ergebnis`),
  `tests/test_identity_creation.py` (`anzahl`),
  `tests/test_identity_intake_paths.py` (`warum`);
* `tests/test_overrides.py`, `tests/test_quote_cache.py`,
  `tests/test_quote_service.py` und `tests/test_repository.py` mit weiteren
  deutschen Helper-, Klassen-, Parameter- und Variablennamen; dazu einzelne
  nichtsprechende Namen wie `r`/`e` in berührten Tests.

Ein benanntes „geparktes Sweep-Ticket“ existiert im Board nicht. Bitte den
vollständigen berührten Python-Scope per AST inventarisieren und bereinigen;
deutsche Testfunktionsnamen, Kommentare und Docstrings bleiben wie vereinbart.

#### Akzeptierte Entscheidungen und DRY-Prüfung

* `listing_id` nur auf `instrument`: akzeptiert.
* Ablehnungskennungen und `ISIN_PATTERN` zur Fachregel verschieben: akzeptiert.
* Dashboard-/i18n-Verbraucher in Übergabe 4: akzeptiert.
* Eigene Eingabefunktion neben der gespeicherten Symbolzerlegung: akzeptiert,
  vorbehaltlich Befund 1 und 3.
* DRY-Scope geprüft: Kennungen/ISIN-Regel, Repository-Query und
  Cache-Durchreichweg sind sinnvoll zentralisiert; keine weitere doppelte
  Produktionsregel im Übergabediff gefunden.

#### Verifikation durch Codex

* `make test`: Backend **590 passed, 29 skipped**, Plugin-API **36 passed**,
  Dashboard **259 passed**.
* Dashboard-Build, Ruff und `git diff --check`: erfolgreich.
* T-21-Smokes: **12/12**, **6/6**, **11/11** erfolgreich.
* Gezielte Gegenproben: `AAPL.XNAS` leer → **500**; mit bestehendem
  `AAPL/XNYS` → **200/XNYS**; Alias/MIC-Kollision → still `XFOO`; OpenAPI-
  Pflichtliste ohne `ticker`/`mic`; leere Eingabe → **422**, Leerraum → **400**.

Kein Browserlauf: Diese Übergabe enthält nach der akzeptierten Schnittentscheidung
noch keinen Dashboard-Verbraucher.

#### Nicht blockierender Folgepunkt

Ja, die Testdatenbank-Abschottung soll ein eigenes Folgeticket werden. Der
reale Lesedurchgriff und derselbe Baufehler bei `get_daily_history_service`
sind konkret genug. Bitte vor der nächsten Übergabe als neues Board-Ticket mit
Autouse-Guard und einer absichtlich auf `data/` zielenden roten Gegenprobe
festhalten; das ist nicht Teil der Korrektur von Übergabe 3.

## OUTBOX → Codex

_Keine offene Nachricht._
