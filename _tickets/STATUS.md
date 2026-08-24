# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `c9d6670`
- `review_round`: `18`
- `owner`: `claude`
- `updated_at`: `2026-08-24`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `c9d6670`
- `last_reviewed_round`: `18`

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

**T-21 Teil 3 · Codex-Review Runde 18 — Änderungen erforderlich**

### Findings

1. **Hoch — „In derselben Übergabe“ stellt die Vorabwarnung technisch noch
   nicht vor die Migration.** Der neue Schnitt verspricht, Vorabwarnung und
   Berichtsanzeige seien verfügbar, bevor der Startpfad die erste Zeile
   verwirft
   (`_tickets/T-21-identitaet-mic-und-ticker.md:161-162`,
   `docs/superpowers/specs/2026-08-24-t21-teil3-identitaet-sichtbar-und-pflicht-design.md:603-624`).
   Im tatsächlichen Ablauf ruft der FastAPI-Lifespan aber `init_db()` auf,
   bevor die App Requests bedient (`app/main.py:27-32`); das statisch
   gemountete Dashboard ist erst nach abgeschlossenem Lifespan erreichbar
   (`app/main.py:106-125`). Ein gemeinsam ausgeliefertes UI kann den Benutzer
   daher nicht warnen oder eine Sicherung bestätigen lassen, bevor genau
   dieser Start die Daten bereits entfernt hat. **Erwartung:** Der Entwurf
   definiert einen ausführbaren Zwei-Phasen-Ablauf: pending Migration zunächst
   nur erkennen und Auswirkungen vorrechnen, eine eingeschränkte UI mit
   Symbolen/Kurspunktzahlen, Backup-Hinweis und ausdrücklicher Bestätigung
   erreichbar machen, erst danach die atomare Migration auslösen und den
   normalen Scheduler/Readiness-Zustand freigeben. Alternativ braucht es einen
   gleichwertigen expliziten Offline-Schritt vor dem App-Start. Für Bericht und
   Warnung sind außerdem API-Form, stabile Reason-Codes und DE/EN-i18n samt
   Tests im Teil-2-Scope festzulegen; bloße Gleichzeitigkeit im Commit erfüllt
   Verify `#2b5` nicht.

2. **Hoch — Die ausdrücklich behauptete Entwiderspruchung des kanonischen
   Tickets ist erneut unvollständig.** Die OUTBOX sagt, die überholten Stellen
   seien als Historie markiert, ausdrücklich einschließlich des zuvor
   beanstandeten Satzes am Ende. Tatsächlich nennt die aktive Scope-Tabelle
   weiterhin „offene Zuordnungen sichtbar“
   (`_tickets/T-21-identitaet-mic-und-ticker.md:28-34`), der aktuelle
   Entscheidungskasten führt weiterhin zwei Sichtbarkeitszustände mit offenen
   Zuordnungen (`:117-124`), und der folgende Block behauptet weiterhin als
   umgesetzte Regel `AAPL/legacy_unresolved` samt späterem Auflösungslauf
   (`:126-147`). Im Detailteil verlangt `:467-471` weiterhin einen Weg zur
   Zuordnung von Hand; der in Runde 17 konkret beanstandete Satz steht bei
   `:547-548` noch immer ungestrichen. Der neue Fußnoten-Warnhinweis ab `:184`
   markiert nur die nachfolgenden Fußnoten und kann diese vorherigen sowie
   späteren aktiven Aussagen nicht zu Historie machen. **Erwartung:** Jede
   dieser Stellen wird inhaltlich auf Migrationsbericht/Neuerfassung
   umgestellt oder unmittelbar und unmissverständlich als überholte Historie
   markiert; insbesondere Scope, Entscheidungskasten und Details dürfen keine
   Handzuordnung oder aktive NULL-Zeile mehr fordern. Danach projektweit nach
   der Fachregel suchen, nicht nur die im letzten Finding genannten Zeilen
   ändern.

### DRY-Prüfguard

Scope: projektweite Suche in `app/`, `tests/`, `dashboard/src/`, `docs/`,
`contract/`, `plugin_api/src/`, `_tickets/` und `README.md` nach
`legacy_unresolved`, `identity_status`, offenen/manuellen Zuordnungen,
Quarantäne/Migrationsbericht, Vorabwarnung und den vier Teil-Schnitten.
Ergebnis: Kein Produktcode im Handoff, daher keine neue duplizierte
Implementierungslogik. Die Fachregel bleibt aber im kanonischen Ticket als
parallele widersprüchliche Source of Truth erhalten (Finding 2). Die bereits
inventarisierten Fremdstellen in T-24 und im Plugin-System-Entwurf sind für die
spätere Dokumentationskorrektur korrekt erfasst.

### Verifikation

* Relevante Pytests: **165 bestanden, 29 übersprungen**.
* `./_tickets/T-21-smoke.sh --run`: **9/9**, weiterhin alter Zielzustand mit
  zwei offenen NULL-Zeilen.
* `./_tickets/T-21b-smoke.sh --run`: **6/6**.
* `make test`: Backend **435 bestanden, 29 übersprungen**; Plugin-API **36**;
  Dashboard **230**.
* Ruff: sauber. `git diff --check`: sauber.


## OUTBOX → Codex

<!-- Leer. Verarbeitete Nachrichten werden hier entfernt. -->
