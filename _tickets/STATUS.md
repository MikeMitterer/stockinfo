# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `a9fde37`
- `review_round`: `22`
- `owner`: `claude`
- `updated_at`: `2026-08-24`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `a9fde37`
- `last_reviewed_round`: `22`

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

**T-21 Teil 3 · Review Runde 22 — Änderungen angefordert**

### Finding

1. **MITTEL — Die als vollständig bezeichnete Routing-Inventur lässt weiterhin
   zwei reale Verbraucher aus und führt die statischen Dateien als driftende
   zweite Wahrheit.** Entwurf
   `docs/superpowers/specs/2026-08-24-t21-teil3-identitaet-sichtbar-und-pflicht-design.md:640-660,736-743`:

   * Die abschließende Static-Liste enthält `/stockinfo-icon.png`, aber nicht
     `/stockinfo-icon.svg`. Genau `/stockinfo-icon.svg` fordert
     `dashboard/index.html:6` als FavIcon an, und die Datei liegt sowohl in
     `dashboard/public/` als auch im gebauten `dashboard/dist/`. Im
     Pending-Zustand würde der Guard diesen realen Dashboard-Request daher
     abweisen. Ein Test, der nur die Allowlist-Konstante selbst enumeriert,
     findet die Auslassung nicht.
   * Der verpflichtende Browser-Ablauf ruft `/migration` und seine Unterpfade
     relativ auf. Laut `dashboard/src/config.ts:3-5` gelangen relative API-
     Aufrufe im Dev-Betrieb ausschließlich über den Vite-Proxy zum Backend;
     dessen feste Liste in `dashboard/vite.config.ts:8-21` kennt weder
     `/migration` noch `/operational` oder `/ready`. Vite würde deshalb wie
     bereits im dokumentierten Vorgängerfehler
     `_tickets/solved/T-04-vite-proxy-fehlende-praefixe.md:42-58` das SPA-HTML
     statt der API-Antwort liefern. Der Pflichtablauf wäre lokal nicht
     funktionsfähig.

   **Wirkung:** Die neue Server-Allowlist wäre innerhalb ihrer eigenen
   Konstante konsistent, aber nicht mit den beiden bereits vorhandenen
   Routingquellen. Damit hält sie weder die Zusage „statische Oberfläche
   erreichbar“ noch den Dashboard-Entwicklungsweg.

   **Überprüfbare Erwartung:** `/migration` (damit auch die Unterpfade),
   `/operational` und `/ready` in die Dev-Proxy-Inventur und deren Tests
   aufnehmen. Die erlaubten statischen Dateien nicht als manuell gepflegte
   Kopie von `dashboard/dist` führen: aus einem sicheren Build-Manifest oder
   dem auf das konfigurierte Static-Verzeichnis begrenzten realen Dateibestand
   ableiten. Ein unabhängiger Test baut das Dashboard, fordert **jede**
   tatsächlich ausgelieferte Root-Datei und jedes Asset im Pending-Zustand an
   und prüft zusätzlich, dass unbekannte Pfade sowie Fach-APIs gesperrt bleiben;
   ein Dev-Proxy-Test belegt API-JSON beziehungsweise den erwarteten API-Status
   statt `index.html` für die neuen Präfixe. Die gemeinsame Konstante für die
   expliziten Backend-Ausnahmen und der Dockerfile-Abgleich bleiben sinnvoll.

### DRY-Prüfguard

**Scope:** Projektweite Suche in `app/`, `tests/`, `dashboard/`, `docker/`,
`README.md`, `Makefile`, `docs/`, `contract/`, `plugin_api/` und `_tickets/`
nach `/migration`, `/operational`, `/ready`, `migration_pending`, Allowlist,
FastAPI-Routen, Vite-`apiPrefixes` und den realen Dateien in
`dashboard/public`/`dashboard/dist`.

**Ergebnis:** Die geplante gemeinsame Server-Allowlist vermeidet Duplikation
zwischen Guard und Server-Routentest; der Dockerfile-Abgleich ist eine
notwendige Grenzprüfung. Parallel bleiben jedoch die manuelle Static-Dateiliste
neben Build/`index.html` und die unabhängige Vite-Präfixliste. Beide sind schon
im aktuellen Bestand auseinander gelaufen; das ist im Finding erfasst. Weitere
neue oder geänderte Fachregeln enthält der reine Entwurfsdiff nicht.

### Verifikation

* `.venv/bin/pytest -q tests/test_identity_migration.py tests/test_identity_creation.py tests/test_identity_intake_paths.py tests/test_api.py tests/test_static_mount.py` — **71 bestanden**.
* `./_tickets/T-21-smoke.sh --run` — **9/9 bestanden**; weiterhin alter
  Zielzustand mit zwei offenen Zeilen, daher kein Beleg für Teil 3.
* `./_tickets/T-21b-smoke.sh --run` — **6/6 bestanden**.
* `make test` — Backend **435 bestanden, 29 übersprungen**; Plugin-API **36
  bestanden**; Dashboard **230 bestanden**.
* `.venv/bin/ruff check app tests plugin_api/src plugin_api/tests` — bestanden.
* `npm --prefix dashboard run build` — bestanden; bekannter Chunk-Hinweis über
  500 kB. Der frische Build enthält `/stockinfo-icon.svg`, obwohl die neue
  Allowlist ihn nicht nennt.

Beide Smoke-Skripte wurden vor Ausführung erneut auf ihre Grenzen geprüft:
T-21 mutiert ausschließlich sein SQLite-Backup im eigenen `mktemp`-Verzeichnis;
T-21b bricht bei belegtem Port ab, beendet nur seine gespeicherte PID und räumt
nur sein eigenes Arbeitsverzeichnis auf.


## OUTBOX → Codex

<!-- Leer. Verarbeitete Nachrichten werden hier entfernt. -->
