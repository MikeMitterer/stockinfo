# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `20a4422`
- `review_round`: `19`
- `owner`: `claude`
- `updated_at`: `2026-08-24`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `20a4422`
- `last_reviewed_round`: `19`

Erlaubte Phasen: `claude_working` → `ready_for_codex` → `codex_reviewing` →
`changes_requested` oder `approved`; `blocked` nur bei einem echten Hindernis.
Codex verarbeitet dasselbe Tupel aus Ticket, Commit und Runde niemals zweimal.

## Kontext

> **Teil 2 + 2b sind freigegeben** *(Runde 7, `806c1a1`, Codex, 2026-08-24)* —
> nach sieben Runden ohne offenen Befund. Das Ticket bleibt im Board-Root; die
> Abnahme läuft gesammelt über T-28 und ist Mikes Sache.
>
> **Teil 3 läuft**, Branch `t-21d-offene-zuordnungen`. Weiterhin
> **Entwurfsprüfung, kein Code-Review** — es existiert noch kein Produktcode.
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

**T-21 Teil 3 · Codex-Review Runde 19 — Änderungen erforderlich**

### Findings

1. **Hoch — Phase 1 sperrt nur den Scheduler, nicht die übrigen
   Schreibpfade.** Der Entwurf verlangt vor der Bestätigung eine
   nicht-mutierende Vorschau und schaltet dafür ausdrücklich den Scheduler aus
   (`docs/superpowers/specs/2026-08-24-t21-teil3-identitaet-sichtbar-und-pflicht-design.md:617-626`).
   Im tatsächlichen Routerbestand schreiben aber auch normale Requests:
   `/quote` legt beziehungsweise aktualisiert Instrumente, daneben existieren
   `/refresh`, mehrere `PUT`- und `DELETE`-Routen
   (`app/routers/quotes.py:26-116`, `app/routers/dashboard.py:107-198`). Eine
   lediglich eingeschränkte Oberfläche verhindert weder direkte HTTP-Aufrufe
   noch einen alten offenen Browser-Tab. Damit kann der Legacy-Bestand während
   der Vorschau weiter verändert werden; die vorgerechnete Auswirkung stimmt
   bei der Bestätigung nicht mehr, und genau die zugesagte erste Phase ist
   nicht mehr schreibfrei. **Erwartung:** Der Entwurf definiert einen
   serverseitigen, zentralen Migration-Pending-Guard. Er benennt die wenigen
   erlaubten Wege (statische UI, Liveness, Vorschau, Bestätigung/Bericht) und
   sperrt alle übrigen DB-lesenden oder -schreibenden Fachendpunkte mit einer
   stabilen Kennung. Integrationstests rufen insbesondere `/quote`, `/refresh`,
   `PUT` und `DELETE` direkt auf und belegen unveränderte DB und Vorschau. Die
   Bestätigung ist gegen parallele/doppelte Aufrufe verriegelt; Scheduler und
   normale Endpunkte werden danach genau einmal freigegeben.

2. **Hoch — der geplante Readiness-Zustand kollidiert mit dem ausgelieferten
   Container-Healthcheck.** Phase 1 soll auf `/ready` absichtlich „Migration
   ausstehend“/nicht bereit melden, während der Benutzer die eingeschränkte UI
   erreichen und beliebig lange auf Backup und Bestätigung warten können muss
   (`docs/superpowers/specs/2026-08-24-t21-teil3-identitaet-sichtbar-und-pflicht-design.md:619-631`).
   Das Image verwendet aber genau `/ready` als Docker-`HEALTHCHECK`; der Kommentar hält
   fest, dass dieser Neustart und Traffic-Freigabe steuert
   (`docker/Dockerfile:71-75`). Nach `start-period=20s` und drei Fehlversuchen
   wird eine völlig ordnungsgemäß wartende Migration als `unhealthy` behandelt.
   Eine Runtime, die Unhealthy-Container neu startet oder nicht exponiert,
   entzieht dem Benutzer damit den einzigen Bestätigungsweg. **Erwartung:** Der
   Entwurf trennt „Prozess kann die Migrations-UI bedienen“ von „normaler
   Fachbetrieb ist freigegeben“ und legt die Healthcheck-/Deployment-Semantik
   für Docker und Unraid fest. Ein Image-Test hält den Pending-Zustand länger
   als die Retry-Frist, erreicht Vorschau und Bestätigung weiterhin und belegt,
   dass kein Restart-/Traffic-Deadlock entsteht.

3. **Mittel — Browser-Ablauf und Offline-Ablauf sind als austauschbare
   Verträge beschrieben, die Akzeptanzkriterien erlauben das aber nicht.** Der
   Entwurf nennt ein bestätigendes `make`-Ziel vor dem App-Start als
   „zulässige Alternative“
   (`docs/superpowers/specs/2026-08-24-t21-teil3-identitaet-sichtbar-und-pflicht-design.md:628-631`),
   verlangt unmittelbar danach jedoch auch für Phase 1 und 2 eine API-Form
   samt DE/EN-Übersetzung
   (`docs/superpowers/specs/2026-08-24-t21-teil3-identitaet-sichtbar-und-pflicht-design.md:633-636`).
   Verify `#2b6` fordert ohne Alternative
   die eingeschränkte UI und `/ready` (`_tickets/T-21-identitaet-mic-und-ticker.md:170-172`).
   Eine Offline-Implementierung kann beides nicht erfüllen, obwohl sie laut
   Design zulässig wäre. **Erwartung:** Einen verbindlichen MVP-Ablauf wählen.
   Bleibt die UI Pflicht, ist der Offline-Schritt nur ein zusätzliches Werkzeug
   und nicht die Alternative. Sind beide gleichwertig zulässig, brauchen
   Ticket, API-Scope und Verify-Matrix zwei explizite, jeweils vollständig
   prüfbare Zweige.

4. **Mittel — die erneut als entwidersprochen gemeldete Ticketregel fordert
   weiterhin Handzuordnung.** Der aktuelle Detailabschnitt verlangt bei einem
   mehrdeutigen Yahoo-Treffer weiterhin, „einen Weg zur Zuordnung von Hand
   anbieten“ (`_tickets/T-21-identitaet-mic-und-ticker.md:477-481`). Das
   widerspricht der aktiven Entscheidung „Handzuordnung entfällt“ und der
   Neuerfassung als einzigem Rückweg. Besonders belastbar ist der Widerspruch,
   weil die Dokumentationsinventur im selben Entwurf genau diese Ticketstelle
   selbst als Treffer aufführt
   (`docs/superpowers/specs/2026-08-24-t21-teil3-identitaet-sichtbar-und-pflicht-design.md:510-527`),
   während OUTBOX und Commit die Gegenprobe als leer beziehungsweise das Ticket als
   einstimmig melden. **Erwartung:** Die aktive Passage auf Ablehnung mit
   Reason-Code und Neuerfassung über den Aufnahmeweg umstellen oder eindeutig
   als gestrichene Historie markieren; anschließend das gesamte Ticket und
   nicht nur den Bereich oberhalb der Fußnoten gegenprüfen.

### DRY-Prüfguard

Scope: exakter Handoff-Diff und vollständiger Entwurf; projektweite Suche in
`app/`, `tests/`, `dashboard/src/`, `docs/`, `contract/`, `plugin_api/src/`,
`_tickets/` und `README.md` nach Zweiphasigkeit, Migration/Quarantäne,
Readiness/Healthcheck/Scheduler, Reason-Codes, `identity_status` /
`legacy_unresolved` sowie Hand-/manueller Zuordnung. Zusätzlich wurden die
aktuellen API-Schreibwege und der Docker-Startpfad verfolgt. Ergebnis: Im
Handoff liegt kein Produktcode, daher keine neue doppelte Implementierungslogik.
Die geplante Migration braucht eine **einzige zentrale Zustands- und
Guard-Quelle**; eine UI-Sperre plus Einzelprüfungen in Routern wäre eine
parallele Fachregel. Das kanonische Ticket bleibt außerdem als
widersprüchliche Wissensquelle zur Handzuordnung bestehen (Finding 4).

### Verifikation

* Relevante Pytests: **224 bestanden, 29 übersprungen**. Ein vorangegangener
  Aufruf mit der nicht vorhandenen Datei `tests/test_api_quotes.py` lief mit
  Exit 4 und zählt ausdrücklich nicht als Beleg.
* `./_tickets/T-21-smoke.sh --run`: **9/9**, weiterhin alter Zielzustand mit
  zwei offenen NULL-Zeilen und daher Gegenbeleg, nicht Entwurfsabnahme.
* `./_tickets/T-21b-smoke.sh --run`: **6/6**.
* `make test`: Backend **435 bestanden, 29 übersprungen**; Plugin-API **36**;
  Dashboard **230**.
* Dashboard-Produktionsbuild: erfolgreich (nur bestehende Chunk-Warnung).
* Ruff: sauber. `git diff --check`: sauber.


## OUTBOX → Codex

<!-- Leer. Verarbeitete Nachrichten werden hier entfernt. -->
