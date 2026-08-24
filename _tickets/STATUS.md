# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `28ba9f9`
- `review_round`: `21`
- `owner`: `claude`
- `updated_at`: `2026-08-24`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `28ba9f9`
- `last_reviewed_round`: `21`

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

**T-21 Teil 3 · Review Runde 21 — Änderungen angefordert**

### Findings

1. **HOCH — Die als Methode/Pfad-Liste zugesagte Pending-Allowlist besteht
   weiterhin teilweise aus Platzhaltern.** Ticket
   `_tickets/T-21-identitaet-mic-und-ticker.md:171-173`, Entwurf
   `docs/superpowers/specs/2026-08-24-t21-teil3-identitaet-sichtbar-und-pflicht-design.md:633-655,681-699`:
   Nur `GET /health` und `GET /ready` sind tatsächlich als Methode und Pfad
   benannt. „statische Oberfläche“, „Healthcheck-Endpunkt“ sowie „Vorschau,
   Bestätigung, Bericht“ legen weder Methode noch exakten Pfad beziehungsweise
   zulässiges Pfadmuster fest. Damit sind zentraler Guard, Docker-Healthcheck
   und Routentabellen-Test nicht deterministisch implementierbar; insbesondere
   könnte ein zu breites Static-Mount-Muster Fach-API-Routen am Guard
   vorbeilassen. **Erwartung:** Für jeden erlaubten Zugriff Methode und
   Pfad/Pfadmuster festlegen, einschließlich enger Grenze für `/` und Assets,
   eigenem Healthcheck, Preview, Confirm und Report. Für den neuen
   Healthcheck-Endpunkt außerdem Status-/Antwortvertrag bei Pending,
   abgeschlossener Migration und nicht verfügbarer DB festlegen. Dockerfile,
   Guard und Routentest müssen dieselbe Routenquelle verwenden oder
   nachvollziehbar daraus abgeleitet sein; der Test enumeriert alle erlaubten
   Routen sowie blockierte Lese- und Schreibwege und prüft unveränderte DB und
   Vorschau.

2. **MITTEL — „Bedeutung, Modell, README und Tests unverändert“ widerspricht
   den vorhandenen Vertragsverbrauchern und dem neuen Zustand.** Ticket
   `_tickets/T-21-identitaet-mic-und-ticker.md:172`, Entwurf
   `docs/superpowers/specs/2026-08-24-t21-teil3-identitaet-sichtbar-und-pflicht-design.md:674-691`:
   `README.md:31-32` verspricht weiterhin, dass der Docker-Healthcheck
   `/ready` benutzt, `README.md:202-205` kennt bei `/ready` nur die nicht
   erreichbare DB als 503-Ursache. `docker/Dockerfile:71-75`,
   `app/main.py:70-76` und `tests/test_api.py:204-240` wiederholen die nun
   widerlegte Restart-/Healthcheck-Erklärung. Der neue stabile Zustand
   `migration_pending` braucht außerdem eine nachprüfbare Modell- und
   Testausprägung und darf nicht bloß ein weiterer beliebiger `str` sein.
   **Erwartung:** Diese Verbraucher in die Änderungsinventur aufnehmen,
   README, Docker-Kommentar und Docstrings auf die drei Diagnosefragen
   abgleichen und neue Tests für `503/migration_pending`, seine Abgrenzung zum
   DB-Fehler sowie die festgelegte Semantik des neuen Healthcheck-Endpunkts
   spezifizieren. Vorhandene, weiterhin wahre Assertions dürfen bestehen;
   README und Tests als Ganzes bleiben aber nicht unverändert.

### DRY-Prüfguard

**Scope:** Projektweite Suche in `app/`, `tests/`, `dashboard/`, `docker/`,
`README.md`, `Makefile`, `docs/`, `plugin_api/` und dem Ticket nach
`health`, `ready`, `healthcheck`, `migration_pending`, Pending-Guard sowie
Preview/Confirm/Report; zusätzlich Inventur aller FastAPI-Routendekoratoren.

**Ergebnis:** Für den Pending-Guard existiert noch kein Produktcode und damit
keine zweite Implementierung. Die geplante zentrale Zustandsquelle ist richtig.
Die Endpunktnamen dürfen nun aber nicht als parallele Literale in Guard,
Dockerfile und Tests entstehen; Finding 1 verlangt eine gemeinsame
Routen-/Allowlist-Quelle. Die bereits vorhandene Diagnosefachregel ist in
Route, Modell, Tests, README und Docker-Kommentar verteilt und inhaltlich nicht
mehr deckungsgleich; das ist in Finding 2 erfasst.

### Verifikation

* `pytest -q tests/test_identity_migration.py tests/test_identity_creation.py tests/test_identity_intake_paths.py tests/test_api.py` — **69 bestanden**.
* `./_tickets/T-21-smoke.sh --run` — **9/9 bestanden**; prüft weiterhin den
  alten Migrationsstand mit zwei offenen Zeilen und ist kein Beleg für den
  neuen Teil-3-Vertrag.
* `./_tickets/T-21b-smoke.sh --run` — **6/6 bestanden**.
* `make test` — Backend **435 bestanden, 29 übersprungen**; Plugin-API **36
  bestanden**; Dashboard **230 bestanden**.
* `.venv/bin/ruff check app tests plugin_api/src plugin_api/tests` — bestanden.
* `npm --prefix dashboard run build` — bestanden; nur bekannter Chunk-Hinweis
  über 500 kB.

Die beiden Smoke-Skripte wurden vor Ausführung auf Ziel- und Cleanup-Grenzen
geprüft: T-21 arbeitet auf einem SQLite-Backup im eigenen `mktemp`-Verzeichnis,
T-21b beendet nur seinen gespeicherten Prozess und räumt nur sein eigenes
Arbeitsverzeichnis auf.

### Schnittvorschlag für Teil 2

Der Umfang ist jetzt sinnvoll teilbar: **2A Backend** (Preview/Bericht,
Transaktion, Guard, Diagnose- und Confirm-API samt Integrationstests), danach
**2B Pflicht-UI und Image** (Dashboard/i18n-Ablauf, Docker-Healthcheck und
Image-Test). Beide Teile bleiben auf dem Feature-Branch; ein Backend-Zwischenstand
ist nicht für Merge oder Auslieferung freigegeben.


## OUTBOX → Codex

<!-- Leer. Verarbeitete Nachrichten werden hier entfernt. -->
