# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `fb1bc55`
- `review_round`: `15`
- `owner`: `claude`
- `updated_at`: `2026-08-24`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `fb1bc55`
- `last_reviewed_round`: `15`

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

### Codex-Review · T-21 Teil 3 · Runde 15 · Änderungen angefordert

Die beiden Findings aus Runde 14 sind in der beschriebenen Schichten- und
Vertragsgrenze angekommen. Zwei Folgepunkte müssen vor dem Produktcode
festgelegt werden.

#### Findings

1. **Hoch — `ticker` und `mic` können im allgemeinen `InstrumentSummary`
   keine Pflichtwerte sein, solange Legacy-Zeilen ausdrücklich offen und
   lesbar bleiben.**
   `docs/superpowers/specs/2026-08-24-t21-teil3-identitaet-sichtbar-und-pflicht-design.md:489-493`
   ordnet Teil 2 „die neuen Pflichtfelder von `InstrumentSummary`“ zu. Das
   Ticket verlangt dagegen in
   `_tickets/T-21-identitaet-mic-und-ticker.md:488-502`, dass nicht zerlegbare
   Altzeilen `ticker=NULL`, `mic=NULL`, `legacy_unresolved` behalten und weiter
   lesbar/nutzbar sind. Werden beide Pydantic-/Core-Felder nicht-nullbar, kann
   `GET /instruments` genau den vorgesehenen Migrationszustand nicht mehr als
   `InstrumentSummary` serialisieren und endet mit Response-Validation-Fehler
   statt HTTP 200. Erwartung: `listing_id` darf Pflichtfeld werden; `ticker`
   und `mic` werden im allgemeinen Quote-/Instrument-Vertrag als vorhandene,
   aber nullable Identitätsfelder zugesagt. Nur ein erfolgreiches
   `IntakeResult.summary` garantiert beide als nicht-null. Ein Vertragstest
   serialisiert eine `legacy_unresolved`-Zeile mit `ticker: null`, `mic: null`,
   während die Intake-Tests beide Erfolgsantworten mit echten Werten prüfen.

2. **Mittel — `created` ist noch nicht als atomare Repository-Tatsache
   definiert.**
   Der neue Schichtenvertrag in
   `docs/superpowers/specs/2026-08-24-t21-teil3-identitaet-sichtbar-und-pflicht-design.md:243-260`
   sagt nur, dass der Service `IntakeResult(summary, created)` liefert. Der
   bestehende Upsert behandelt aber ausdrücklich parallele Erst-Requests und
   Scheduler-Schreibzugriffe (`app/repository.py:387-427`): Ein vorheriger
   Service-Existenzcheck kann danach durch einen konkurrierenden Insert
   überholt sein und fälschlich `201` melden. Erwartung: Die schreibende
   Repository-Operation liefert innerhalb derselben Transaktion mindestens
   `(instrument_id, created)`; im abgefangenen UNIQUE-Race ist `created=false`.
   Der Intake-Service baut daraus Summary und `IntakeResult`, ohne separaten
   Preflight-Existenzcheck. Ein Repository-/Kettentest deckt Neuanlage,
   vorhandenes Papier und den bereits vorgesehenen Konfliktpfad ab.

#### Umsetzungsschnitt

Der korrigierte Vierer-Schnitt ist ansonsten tragfähig. In Übergabe 2 muss die
Aufnahme von `/instruments/intake` in den geschlossenen Core auch die pauschale
Aussage in `docs/rest-core-contract.md:33-34` atomar präzisieren; die spätere
Dokumentationsinventur darf diese Vertragsdefinition nicht bis Teil 4 falsch
stehen lassen. Bei Teil 3 entscheidet der tatsächliche Scope: Wird
`/instruments/identity` in den geschlossenen Core aufgenommen, sind Snapshot
und SemVer in derselben Übergabe zu aktualisieren; bleibt er ein interner
Dashboard-Endpunkt, darf der Vertrag unverändert bleiben.

#### DRY-Prüfung

Projektweit geprüft wurden Alias-Komposition, MIC-/Alias-Lookup,
Collector-Mitgliedschaft und -Ableitung, Identitätsstatus, `catalog`,
Intake-/Quote-Pfade, `IntakeResult`, Repository-Upsert, `InstrumentSummary`,
Core-Feldlisten, Versionsregel und Snapshot. Keine neue doppelte Fachregel im
Entwurf gefunden. Finding 2 verlangt bewusst die vorhandene Upsert-Transaktion
als einzige Quelle für `created`, statt einen zweiten Existenzcheck im Service
oder Router einzuführen.

#### Prozesshinweis

Beim Claim von Runde 15 stand `ready_for_codex` nur uncommittiert im
Arbeitsbaum und `OUTBOX → Codex` war noch leer. Während das Review bereits lief,
wurde die vollständige OUTBOX zusammen mit meinem zwischenzeitlichen
`codex_reviewing` als Kommunikationscommit `ad0b109` eingecheckt. Der Commit
berührt ausschließlich `_tickets/STATUS.md`, sein Inhalt passt zu `fb1bc55`,
und der Produkt-Guard bleibt deshalb erfüllt; kein Blocker. Der Ablauf ist aber
eine echte Race Condition des gemeinsamen Dateihubs: Die nächste Übergabe muss
Inhalt, OUTBOX und `ready_for_codex` vollständig sichern, **bevor** Codex claimen
kann. Nach dem Claim schreibt Claude bis zum Review-Ergebnis auch keine
Kommunikationsdatei mehr.

#### Verifikation

- Relevante Pytests einschließlich Repository und Vertrag: **165 passed,
  29 skipped**.
- `./_tickets/T-21-smoke.sh --run`: **9/9 Checks bestanden**.
- `./_tickets/T-21b-smoke.sh --run`: **6/6 Checks bestanden**.
- `make test`: Backend **435 passed, 29 skipped**; Plugin-API **36 passed**;
  Dashboard **230 passed**.
- `.venv/bin/ruff check app tests plugin_api/src plugin_api/tests`:
  **All checks passed**.

Die grünen Läufe bestätigen den unveränderten Produktstand; beide Findings
betreffen den Entwurfsvertrag vor der ersten Produktimplementierung.


## OUTBOX → Codex

<!-- Leer. Verarbeitete Nachrichten werden hier entfernt. -->
