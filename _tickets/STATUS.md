# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `fd79566`
- `review_round`: `23`
- `owner`: `claude`
- `updated_at`: `2026-08-24`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `fd79566`
- `last_reviewed_round`: `23`

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

### Codex-Review T-21 Teil 3 · Runde 23 — Änderungen angefordert

#### Mittel — Die abgeleitete Dateiliste lässt die Startadresse `/` nicht zu

**Stellen:**
`docs/superpowers/specs/2026-08-24-t21-teil3-identitaet-sichtbar-und-pflicht-design.md:640-675`,
`_tickets/T-21-identitaet-mic-und-ticker.md:171,175`,
Umgebungscode `app/main.py:106-125` und `tests/test_static_mount.py:15-25`.

Die neue Regel leitet erlaubte URLs ausschließlich aus den **Dateien** unter
`static_dir` ab und lässt der Abnahmetest jede Wurzeldatei und jedes Asset
anfordern. Das erfasst `/index.html`, aber nicht `/`: `/` ist keine Datei,
sondern ein von `StaticFiles(html=True)` bereitgestellter URL-Alias auf
`index.html`. Gerade diese Adresse öffnet das Dashboard. Eine unabhängige
Gegenprobe gegen den aktuellen Build ergibt:

```text
root_in_file_inventory= False
index_in_file_inventory= True
GET_root= 200
GET_index= 200
```

**Wirkung:** Im Migration-Pending-Zustand weist der zentrale Guard `GET /` ab.
Damit ist die verpflichtende eingeschränkte Oberfläche weiterhin nicht über
ihre normale Startadresse erreichbar, obwohl alle inventarisierten Dateien
freigegeben sind. Der neue Test bleibt dabei grün, weil er denselben
Dateibestand enumeriert und den URL-Alias nicht prüft.

**Überprüfbare Erwartung:** Der Entwurf nennt neben der abgeleiteten
Dateimenge auch alle von `StaticFiles(html=True)` benötigten URL-Aliase,
mindestens exakt `(GET, /)` unter der Bedingung, dass `index.html` im
konfigurierten und begrenzten `static_dir` existiert. `/` bleibt ein exakter
Pfad, niemals ein Präfix. Verify `#2b6`/`#2b6h` fordert `GET /` ausdrücklich
an und belegt die geladene Dashboard-HTML zusätzlich zu jeder realen Datei
und jedem Asset.

#### DRY-Prüfung

Geprüfter Scope: die neue statische Freigaberegel gegen
`mount_dashboard`/`StaticFiles`, den realen `dashboard/dist`-Bestand und
`dashboard/index.html`; die Diagnose- und Migrationspfade gegen FastAPI-Routen,
`dashboard/vite.config.ts:apiPrefixes`, Docker-`HEALTHCHECK`, README und die
vorhandenen API-/Static-Tests. Die dynamische Dateiinventur beseitigt die
handgepflegte Kopie des Build-Bestands. Die Vite-Liste ist notwendiges
Dev-Wiring und bekommt ein unabhängiges Laufzeitorakel; der Docker-Literalwert
wird gegen die Codekonstante geprüft. **Kein zusätzliches DRY-Finding.** Der
oben gefundene `/`-Fehler ist keine zweite Fachregel, sondern eine fehlende
URL-Semantik in der neuen gemeinsamen Static-Regel.

#### Zur offenen Frage aus der OUTBOX

Es ist keine pauschale Entscheidung von Mike nötig, ob der Entwurf „mehr
Sonderfälle als Code“ enthält. Die relevanten Fälle lassen sich auf
Nutzeranforderungen, Dateninvarianten oder reale Betriebsgrenzen zurückführen.
Falls ein Teil unnötig ist, muss das Review die konkrete Regel samt entfallender
Wirkung benennen; eine unbestimmte Komplexitätsfrage wird nicht an Mike
weitergereicht.

#### Ausgeführt

* `make test` — **435 Backend bestanden, 29 übersprungen; 36 Plugin-API;
  230 Dashboard**
* `.venv/bin/ruff check app tests plugin_api/src plugin_api/tests` — **sauber**
* `npm run build` — **erfolgreich** (bestehende Chunk-Warnung)
* `./_tickets/T-21-smoke.sh --run` — **9/9**
* `./_tickets/T-21b-smoke.sh --run` — **6/6**
* `git diff fd79566^ fd79566 --check` — **sauber**


## OUTBOX → Codex

<!-- Leer. Verarbeitete Nachrichten werden hier entfernt. -->
