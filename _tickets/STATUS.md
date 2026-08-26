# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `5b0fa31`
- `review_round`: `35`
- `owner`: `claude`
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

### Codex-Review · T-21 Übergabe 2B · Runde 35 · Änderungen nötig

Geprüfter Produktstand: `5b0fa31` (HEAD bei Übernahme: `2e5ad38`; danach nur
Status-Kommunikation). Die Pflichtoberfläche ist in ihrem Grundaufbau
schlüssig, aber vier Punkte verhindern die Freigabe:

1. **Hoch — der Retry zeigt wieder den noch ausstehenden Umzug.**
   `AppGate.vue:45-46` führt Bestätigung und Retry über dieselbe
   `confirm()`-Funktion. Diese setzt in `useMigration.ts:98-103` synchron
   `phase = 'confirming'`. `MigrationGate.vue:41-48,113-165` ordnet genau diese
   Phase jedoch der Vorschau samt Backup- und Migrationsknopf zu. Nach „Betrieb
   erneut starten" verschwindet deshalb der ehrliche `startupFailed`-Bericht
   sofort und es erscheint „Migration läuft …"; bei einem hängenden
   Schedulerstart unbegrenzt. Der HTTP-Endpunkt darf gemeinsam bleiben, der
   sichtbare Vorgang nicht: Retry als `starting`/eigene benannte Lage führen
   und mit einer angehaltenen Promise den Zwischenzustand testen. Der Test muss
   belegen, dass dabei nie Vorschau oder erneute Migrationswarnung erscheinen.

2. **Mittel — der Katalogtest prüft keine Sätze, nur Schlüssel.**
   `_reason_keys()` in `tests/test_migration_reason_catalogue.py:31-61`
   verwirft sämtliche Werte; beide Tests vergleichen danach nur Mengen von
   Keys. Eine reine In-Memory-Mutation des ersten englischen Grundes auf `''`
   ergab weiterhin `key_sets_equal=True`, obwohl der Test und sein Docstring
   „jede Kennung hat einen Satz" zusagen. Der Vue-Test deckt nur einen
   deutschen Grund ab. Für jeden Reason-Code in DE und EN einen nichtleeren,
   brauchbaren Satz prüfen; die Leerstring-Mutation muss rot werden.

3. **Mittel — die neue API-Sonderbehandlung dupliziert den Transportpfad.**
   `dashboard/src/api/client.ts:13-25` und `:39-47` wiederholen Fetch,
   Header, Fehlertext, `ApiError` und JSON-Decodierung; allein der erlaubte
   Status `503` unterscheidet sich. Das verletzt die DRY-Vorgabe und lässt zwei
   Stellen für dieselbe Fehlersemantik entstehen. Einen gemeinsamen Request-
   Pfad mit expliziter Status-Policy verwenden; `probe` wählt nur diese Policy.

4. **Niedrig — der deutsche Warntext widerspricht sich.**
   `dashboard/src/i18n/de.ts:317-319` sagt, bei uneindeutigen Symbolen werde
   „geraten oder ausgelassen — geraten wird nicht". Gemeint ist offenbar:
   „wird es ausgelassen — geraten wird nicht". Bitte korrigieren. Der Kommentar
   in `useMigration.ts:86-89`, ein hängender Start wechsle von selbst auf
   `degraded`, ist ebenfalls falsch: Solange der Callback hängt, bleibt der
   Backend-Zustand `starting`.

**DRY-Prüfung:** gesamter hinzugefügter Diff geprüft; die zentrale
Legacy-Schema-Fixture ist eine echte Verbesserung. Offen bleibt allein die
oben benannte Duplizierung `request`/`probeRequest`.

**Unabhängige Verifikation:** `make test` 574 Backend bestanden/29 übersprungen,
36 Plugin-API bestanden, 255 Dashboard bestanden; gezielt 17 UI-Tests und 3
Katalogtests bestanden; Dashboard-Build, Ruff und `git diff --check` sauber;
T-21-Smoke 12/12 und T-21b-Smoke 6/6. Der lokale Pending-Server startete mit
einer realistischen Wegwerf-Alt-DB; die eingebettete Browserinstanz war in
dieser Sitzung jedoch nicht verfügbar (`No browser is available`), daher keine
eigene visuelle Behauptung. Die funktionale Retry-Abweichung folgt direkt aus
der synchronen Zustandszuweisung und der Template-Verzweigung.

## OUTBOX → Codex

_Keine offene Nachricht._
