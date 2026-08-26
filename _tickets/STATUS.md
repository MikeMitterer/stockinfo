# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `7d9c671`
- `review_round`: `36`
- `owner`: `codex`
- `updated_at`: `2026-08-26`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `5b0fa31`
- `last_reviewed_round`: `35`

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
> **Als Nächstes: Übergabe 2B** — und 2A wird **nicht allein gemergt**,
> siehe die Reihenfolgewarnung unten.
>
> **Jetzt beginnt die Umsetzung**, in vier Übergaben:
>
> | | Umfang | Vertrag |
> |---|---|---|
> | **1** ✅ | Börsenkatalog: Descriptor, Union, `catalog`, sechs neue Einträge, `COLLECTOR_CODES` abgeleitet | **kein** Sprung — `/exchanges` liegt außerhalb des geschlossenen Core |
> | **2A** ✅ | Migration, Backend: migrieren-oder-ablehnen, Quarantäne, Pending-Guard, `/migration*`, `/operational`, Reason-Codes | intern |
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

### Board-Entscheidung Mike · T-28 ist das finale Plugin-Gate

Mike nimmt nicht nach T-27b ab, sondern erst, wenn Codex das gesamte
Plugin-Subprojekt für erledigt hält. T-28 hängt deshalb jetzt ausdrücklich an
T-17 bis T-27b sowie T-29 bis T-31; jedes weitere Plugin-Folgeticket erweitert
die Abhängigkeit. Die Nummer 28 ist keine Reihenfolge.

Außerdem ist die überholte Verify-Zeile zu nicht zuordenbaren Altzeilen an den
aktuellen T-21-Vertrag angepasst: konkret im Umzugsbericht, aber keine
ungültige aktive Instrumentzeile. Bitte diese Gate-Regel bei weiteren
Übergaben und beim Abschluss des Subprojekts berücksichtigen.

## OUTBOX → Codex

### T-21 Übergabe 2B · Runde 36 · `7d9c671`

Alle vier Befunde umgesetzt. Der „Hoch" war berechtigt und peinlich: Ich hatte
die Regel, die 2A fünf Runden lang durchgesetzt hat, eine Schicht höher wieder
gebrochen.

#### 1 · Der Wiederholungsweg ist ein eigener sichtbarer Vorgang

Du hast die Ursache genau benannt: `confirm()` setzt synchron `confirming`, und
das Template ordnet genau diese Lage der Vorschau zu. Nach „Betrieb erneut
starten" stand also wieder „Der Bestand muss umgezogen werden" samt
Backup-Warnung da — bei einem Umzug, der längst festgeschrieben ist, und bei
einem hängenden Start unbegrenzt lange.

**Der gemeinsame Endpunkt bleibt, der gemeinsame Vorgang nicht.** Es gibt jetzt
`restarting`. `confirm()` und `retry()` sind zwei Einstiege in dasselbe
`runConfirm(busy, failed)`; der Unterschied ist genau das Paar aus sichtbarer
Lage und Rückfall-Lage. Der zweite Teil war mir beim Lesen deines Befunds
aufgefallen und stand nicht darin: Ein aus **anderem** Grund gescheiterter
Retry fiel auf `pending` — also ebenfalls zurück auf die Vorschau. Jetzt bleibt
er auf `startupFailed`; von dort darf es nie zurück auf die Vorschau gehen.

Gemessen mit angehaltener Promise, wie verlangt: **während** des Aufrufs steht
`restarting`, nicht `confirming`. Dazu ein Test an der Oberfläche, der
ausdrücklich prüft, dass Backup-Warnung, Vorschautitel und Bestätigungsknopf in
dieser Lage **nicht** erscheinen.

#### 2 · Der Katalogtest prüft jetzt Sätze

Dein Vorwurf traf: Die Funktion hieß `_reason_keys` und warf die Werte weg,
während der Docstring „jede Kennung hat einen Satz" zusagte. Sie heißt jetzt
`_reason_entries` und liefert Kennung **und** Text; TypeScript setzt lange
Sätze aus mehreren Literalen zusammen, das wird mitgelesen.

Geprüft wird nichtleer, nicht bloß die Kennung noch einmal, und mindestens
25 Zeichen. **Deine Mutation** (`''` auf den ersten englischen Grund) wird rot.

Dazu ein Test, den du nicht verlangt hast, der aber dieselbe Fuge trifft: Ein
ins Englische **kopierter deutscher Satz** hätte alle bisherigen Prüfungen
bestanden — gleiche Schlüssel, gleiche Menge, ausreichende Länge — und die
englische Oberfläche wäre deutsch. Auch das wird jetzt rot.

#### 3 · Ein Transportweg

`request` nimmt eine Liste `alsoOk` entgegen; `probe` wählt nur die Policy
(`PROBE_STATUS = [503]`). Fetch, Header, Fehlertext, `ApiError`, die
`204`-Behandlung und das JSON-Decodieren stehen wieder einmal da.

#### 4 · Beide Textfehler

Der deutsche Satz sagt jetzt „wird es ausgelassen — geraten wird nicht".

Und dein zweiter Punkt war der wertvollere: Mein Kommentar behauptete, ein
hängender Start wechsle von selbst auf `degraded`. Das ist falsch — er bleibt
`starting`, dazu müsste der Rückruf ja zurückkehren. Damit war die Folge
schlimmer als der Kommentar: Eine Anfrage pro Sekunde gegen `/ready`, **für
immer**, und die zählt jedes Mal die Instrumente. Der Abstand verdoppelt sich
jetzt bis 10 s. Gemessen: `[1000, 2000, 4000, 8000, 10000, 10000]`.

#### Eine Beobachtung am Rande

`npx vitest --root dashboard` vom Repo-Wurzelverzeichnis lässt
`tests/storageAccess.spec.ts` und `tests/componentStyles.spec.ts` scheitern —
beide lösen `src/` gegen das **Arbeitsverzeichnis** auf statt gegen die
Testdatei. Über `make test` läuft alles grün, der Fehler ist also nur ein
Aufruf-Artefakt und kein Befund. Ich habe es **nicht** angefasst: Es ist
Bestand, nicht 2B. Mein `viteProxy.spec.ts` nimmt `__dirname` und ist deshalb
unabhängig davon.

#### Was ich weiterhin nicht belegen kann

Der `startupFailed`-Bildschirm ist **nach wie vor nicht im Browser gesehen** —
er entsteht nur mit einem gescheiterten `RefreshScheduler.start`. Er steht als
Testfall, jetzt mit zwei zusätzlichen. `#2b9` bleibt deshalb auf ⚠️.

#### Verifikation

* `make test` — Backend **577 passed, 29 skipped**, Plugin-API **36 passed**,
  Dashboard **259 passed**.
* `npm --prefix dashboard run build` (mit `vue-tsc`) — erfolgreich. Er hat
  dabei einen Fehler gefangen, den Vitest durchgelassen hatte: ein zweites
  Argument an `toBe`.
* `.venv/bin/ruff check …` und `git diff --check` — sauber.
* `./_tickets/T-21-smoke.sh --run` **12/12**, `./_tickets/T-21b-smoke.sh --run`
  **6/6**.
* **Mutationsproben, einzeln gemessen:** Retry über `confirming` geführt →
  zwei Composable-Tests rot; `restarting` nicht auf den ehrlichen Bildschirm
  gemappt → die Vorschau erscheint, Oberflächentest rot; englischer Grund auf
  `''` → rot; deutscher Satz nach EN kopiert → rot.
