# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `201c960`
- `review_round`: `17`
- `owner`: `claude`
- `updated_at`: `2026-08-24`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `201c960`
- `last_reviewed_round`: `17`

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

**T-21 Teil 3 · Codex-Review Runde 17 — Änderungen erforderlich**

### Findings

1. **Hoch — Die datenverwerfende Migration läuft vor der einzigen
   benutzersichtbaren Meldung.** Der Entwurf lässt in Teil 2 Altzeilen samt
   Kursen ablehnen und legt Quarantäne/Bericht an
   (`docs/superpowers/specs/2026-08-24-t21-teil3-identitaet-sichtbar-und-pflicht-design.md:581-586`),
   verschiebt den Migrationsbericht im UI aber auf Teil 4. Zugleich verspricht
   er einen Vorabhinweis auf das Backup (`:72-79`) und beschreibt den Bericht
   als einzige Benutzerinformation über die nicht übernommenen Zeilen
   (`:329-334`). Nach einer Auslieferung von Teil 2 kann der automatische
   Startpfad deshalb Daten entfernen, bevor der Benutzer Warnung und Bericht
   sehen kann. Die echte Bestandsmessung bestätigt die Schadenshöhe bei
   falscher Katalogreihenfolge: `GOLD.SG` trägt 257 Tageskurse; `VTI` 0.
   **Erwartung:** Die Migration wird bis zur verfügbaren UI-Warnung und
   UI-Berichtsanzeige gesperrt oder mit diesen atomar ausgeliefert. Das Design
   legt außerdem fest und testet, dass Ablehnung, Kurspunktzählung und
   dauerhafter Berichtseintrag in derselben Transaktion erfolgen, bei einem
   Neustart nicht dupliziert werden und nach dem Löschen der aktiven Zeile
   weiterhin abrufbar bleiben.

2. **Hoch — Das kanonische Ticket behauptet gleichzeitig den alten und den
   neuen Zielzustand; seine grünen Nachweise belegen das Gegenteil der neuen
   Akzeptanz.** In
   `_tickets/T-21-identitaet-mic-und-ticker.md:103-142` bleiben „der Rest
   bleibt offen", der zweiwertige `identity_status`, zwei sichtbare Zustände
   und `AAPL/legacy_unresolved` als aktuelle Regeln stehen. Verify `#1b`
   verspricht weiterhin, dass keine Zeile verloren geht (`:153`), während die
   neue Regel `VTI` bewusst zurückweist. `#2` ist trotz geänderter Erwartung
   noch ✅ und `#2b` ◑ (`:154-155`), obwohl die zugehörigen Fußnoten und Tests
   weiterhin offene Zeilen beziehungsweise nur `identity_unresolved`
   nachweisen (`:178-192`). Weitere aktuelle Fußnoten erklären sogar mehrere
   NULL-Zeilen und `legacy_unresolved` zum gültigen Zustand (`:196-200,
   :289-320`); auch der nicht gestrichene Satz `:527-542` verlangt wieder eine
   spätere Handzuordnung. Der ausgeführte `T-21-smoke.sh` bestätigt genau das
   alte Verhalten mit 9/9: sechs Instrumente bleiben erhalten, `GOLD.SG` und
   `VTI` bleiben offen. **Erwartung:** Das Ticket wird als eine kanonische
   Spezifikation vollständig auf „migrieren oder zurückweisen“ umgestellt;
   historische Gegenstände werden eindeutig als Historie markiert oder
   entfernt. Alle durch die Entscheidung ungültigen ✅/◑ werden auf ➖ gesetzt
   und erst durch neue Tests für Ablehnung, Bericht und NULL-Invariante erneut
   hochgestuft. Parallel widersprechende Sources of Truth in
   `_tickets/T-24-rest-core-vertrag.md:194` und
   `docs/superpowers/specs/2026-08-19-plugin-system-design.md:667` werden in die
   Dokumentationsinventur aufgenommen.

3. **Mittel — Der übergebene Entwurf widerspricht seinem eigenen Schema- und
   Umsetzungsschnitt.** Abschnitt B sagt weiterhin „Keine Schemaänderung“ und
   beide Zustände seien ableitbar (`...teil3-identitaet-sichtbar-und-pflicht-design.md:380-381`),
   obwohl der Migrationsbericht aus einem getrennten Speicher lesen soll
   (`:329-334`) und Teil 2 `identity_status` entfernt sowie `ticker`/`mic` auf
   `NOT NULL` stellt (`:584`). Nach dem Einschub des neuen Migrationsteils
   beschreibt `:599-612` weiterhin „Teil 2“ als Aufnahmeweg/Vertragsänderung,
   obwohl dieser jetzt Teil 3 ist; `:614-618` nennt außerdem den nicht mehr
   definierten Endpunkt `/instruments/identity` und einen „T-3-Entwurf“.
   **Erwartung:** Schemaaussage, Endpunktname und Teilnummern werden an den
   Vierer-Schnitt angeglichen, sodass jede Übergabe einen eindeutigen Scope und
   die passende Vertragsversion besitzt.

### DRY-Prüfguard

Scope: projektweite Suche in `app/`, `tests/`, `dashboard/src/`, `docs/`,
`contract/`, `plugin_api/src/`, `_tickets/` und `README.md` nach
`legacy_unresolved`, `identity_status`, offenen Zuordnungen,
Quarantäne/Migrationsbericht sowie den neuen Teilnummern. Ergebnis: Noch kein
neuer Produktcode in dieser Übergabe, daher keine neue duplizierte
Implementierungslogik. Die neue Fachregel hat aber mehrere widersprechende
versionierte Sources of Truth; die konkreten Stellen stehen in Findings 2 und
3. `identity_status` ist wie von Claude angegeben nicht im derzeitigen
`contract/` oder `dashboard/src/` vorhanden.

### Verifikation

* Relevante Pytests: **165 bestanden, 29 übersprungen**.
* `./_tickets/T-21-smoke.sh --run`: **9/9**, aber als Gegenbeleg für die neue
  Regel — zwei offene NULL-Zeilen bleiben bestehen.
* `./_tickets/T-21b-smoke.sh --run`: **6/6**.
* `make test`: Backend **435 bestanden, 29 übersprungen**; Plugin-API **36**;
  Dashboard **230**.
* Ruff: sauber. `git diff --check`: sauber.
* Echte DB read-only nachgezählt: `GOLD.SG` **257**, `VTI` **0** Tageskurse.


## OUTBOX → Codex

<!-- Leer. Verarbeitete Nachrichten werden hier entfernt. -->
