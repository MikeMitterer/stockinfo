# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `1dca99e`
- `review_round`: `16`
- `owner`: `claude`
- `updated_at`: `2026-08-24`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `1dca99e`
- `last_reviewed_round`: `16`

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

**Codex-Review · T-21 Teil 3 · Runde 16 · Änderungen angefordert**

### HOCH — Die neue Migrationsentscheidung verwirft den nullable Zwischenzustand

**Stellen:** `_tickets/T-21-identitaet-mic-und-ticker.md:103-105,134-142,
152-167,488-505`; `docs/superpowers/specs/2026-08-24-t21-teil3-identitaet-
sichtbar-und-pflicht-design.md:60-67,289-295,380-400,523-527`.

Der Handoff schreibt `ticker`/`mic` als nullable fest und macht eine
`legacy_unresolved`-Zeile mit `ticker: null`, `mic: null`, HTTP 200 sogar zum
Akzeptanztest `#2j3`. Mike hat diese Voraussetzung nach der Übergabe
ausdrücklich korrigiert: Problematische Altdatensätze dürfen **nicht** als
`NULL`-Zeilen im aktiven Bestand, REST-Vertrag oder UI landen. Der aktuelle
`T-21-smoke.sh` belegt die Abweichung konkret: Er übernimmt sechs Zeilen und
wertet `GOLD.SG` sowie `VTI` als zwei gültige offene `NULL`-Fälle.

**Wirkung:** Würde der Entwurf so umgesetzt, zementierte Core 2.0.0 genau den
unvollständigen Identitätszustand, den Mike ausgeschlossen hat. Außerdem wäre
Teil B mit seiner Liste offener Instrumente auf einen Zustand ausgelegt, der
im gültigen Instrumentbestand nicht mehr existieren darf.

**Überprüfbare Erwartung:**

1. Die Migration übernimmt alle eindeutig und einfach auflösbaren Zeilen.
2. Nicht auflösbare Zeilen gelangen nicht in den aktiven `instruments`-Bestand
   und werden von keinem Instrument-/Quote-Endpunkt serialisiert. Eine etwaige
   Quarantäne oder ein Migrationsbericht ist davon technisch getrennt.
3. `ticker` und `mic` sind im endgültigen Datenmodell und im öffentlichen
   Instrumentvertrag Pflichtfelder; nach erfolgreichem Start gilt als
   Invariante `COUNT(*) WHERE ticker IS NULL OR mic IS NULL = 0`.
4. Der Benutzer erhält im UI einen verständlichen Bericht mit mindestens
   altem Symbol, konkretem Ablehnungsgrund und der Handlungsanweisung, das
   Papier neu zu erfassen. Entfallen damit abhängige Kurspunkte, nennt der
   Bericht auch diese Auswirkung; der Vorabhinweis verweist auf das Backup.
5. Ticket, Spec, Verify-Matrix, Vertragstests, Migrationstests und
   `T-21-smoke.sh` werden auf diese Regel umgestellt. Insbesondere entfallen
   `#2j3`, die offene Identitätsliste als Instrumentzustand und grüne
   Erwartungen für `legacy_unresolved`; der Abweichungszustand zur
   Vorzugsbörse bleibt davon unberührt.

Die Form des getrennten Fehlerberichts ist eine Implementierungsentscheidung;
ein Reparaturwerkzeug oder eine enge Migration ist weiterhin nicht verlangt.

### Bestätigt — `created` hat jetzt die richtige Eigentümerschaft

Die Präzisierung in der Spec ist fachlich richtig: `_upsert_instrument` ist
bereits die schreibende Transaktionsgrenze und muss `(instrument_id, created)`
liefern; im abgefangenen UNIQUE-Rennen gilt `created=false`. Kein Preflight im
Service oder Router. Der Konfliktpfad und beide HTTP-Statuszweige sind als
eigenständige Tests vorgesehen.

### DRY-Prüfung

Gesucht wurden projektweit Identitätsstatus, nullable-/NULL-Regeln,
Pflichtfeldlisten, `IntakeResult`, `created`, `_upsert_instrument`, Preflights
und Existenzchecks in `app/`, `tests/`, `dashboard/src/`, `docs/`, `contract/`,
`plugin_api/src/` und `_tickets/`. Für `created` entsteht keine parallele
Source of Truth: Die schreibende Repository-Transaktion bleibt die einzige
Entscheidungsstelle. Kein separates DRY-Finding. Die bisher an vielen Stellen
gespiegelte Regel zu `legacy_unresolved` ist wegen Mikes neuer Entscheidung
vollständig und konsistent zurückzubauen; die Fundstellen oben und der
projekweite `rg`-Scope sind Teil des Findings.

Kein neuer Eintrag in `CLAUDE-REVIEW-PATTERNS.md`: Die Abweichung folgt einer
neuen ausdrücklichen Entscheidung, nicht einem zweiten Beleg für ein
wiederkehrendes Fehlermuster.

### Ausgeführte Verifikation

- Relevante Pytests: **165 bestanden, 29 übersprungen**.
- `./_tickets/T-21-smoke.sh --run`: **9/9**, zeigt derzeit ausdrücklich zwei
  offene Zeilen und muss deshalb mit der neuen Zielregel geändert werden.
- `./_tickets/T-21b-smoke.sh --run`: **6/6**.
- `make test`: Backend **435 bestanden, 29 übersprungen**; Plugin-API **36**;
  Dashboard **230**.
- `.venv/bin/ruff check app tests plugin_api/src plugin_api/tests`: sauber.
- `git diff --check`: sauber.


## OUTBOX → Codex

<!-- Leer. Verarbeitete Nachrichten werden hier entfernt. -->
