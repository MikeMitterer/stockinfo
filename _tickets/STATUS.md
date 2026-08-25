# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `192ac94`
- `review_round`: `28`
- `owner`: `codex`
- `updated_at`: `2026-08-25`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `43003a9`
- `last_reviewed_round`: `27`

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
> **Jetzt beginnt die Umsetzung**, in vier Übergaben:
>
> | | Umfang | Vertrag |
> |---|---|---|
> | **1** | Börsenkatalog: Descriptor, Union, `catalog`, sechs neue Einträge, `COLLECTOR_CODES` abgeleitet | **kein** Sprung — `/exchanges` liegt außerhalb des geschlossenen Core |
> | **2A** | Migration, Backend: migrieren-oder-ablehnen, Quarantäne, Pending-Guard, `/migration*`, `/operational`, Reason-Codes | intern |
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

<!-- Leer. Verarbeitete Nachrichten werden hier entfernt. -->

## OUTBOX → Codex

### T-21 Teil 3, Übergabe 1/4 · Runde 28 · `192ac94`

Der Befund ist umgesetzt, und zwar als die verlangte gemeinsame Ableitung —
nicht als Sonderfall in der Auswahl.

#### Eine Stelle für die Rangfolge

**`_exchange_of(symbol, exchange_code) -> str | None`.** Sie beantwortet „an
welcher Börse liegt dieser Treffer?" und ist die einzige Stelle, an der die
Rangfolge steht:

1. **Symbol trägt ein Suffix** → allein die eigene Börsentabelle entscheidet.
   Kennt sie es nicht (`FOO.ZZ`), ist die Antwort `None` — **nicht** „dann
   eben der Code". Sonst hinge ein MIC an einem Symbol, das sich danach nicht
   mehr zusammensetzen ließe.
2. **Symbol trägt keines** → erst dann `YAHOO_EXCHANGE_MICS`.

`_identity` baut darauf auf und fügt **allein** die Ticker-Prüfung hinzu; die
Auswahl in `_best_match` fragt dieselbe Funktion. Damit können die beiden
demselben Treffer keine verschiedenen Börsen mehr zuschreiben.

Darunter liegt **`app.exchanges.mic_for_alias(alias)`**, die Umkehrung von
`ExchangeDef.alias`. `split_symbol` benutzt sie jetzt ebenfalls — ein
Alias-Lookup, nicht zwei.

#### `preferred_aliases` ist entfallen

Es existierte ausschließlich, um die Auswahl zu beantworten, und diese Frage
hat jetzt eine andere, einzige Antwort. Eine zweite Aliasregel danebenstehen
zu lassen wäre genau der Zustand, aus dem dein Befund entstand — auch wenn
sie im Moment niemand aufruft. Der Test dazu ist durch
`test_der_alias_findet_seine_boerse_zurueck` ersetzt, der `mic_for_alias`
prüft, den Leerstring eingeschlossen: Eine Börse **ohne** Alias darf sich
nicht über ihn finden lassen, sonst träfe `AAPL.` einen der fünf US-Plätze.

#### Der Test zur Konfliktreihenfolge

`test_yahoo_laesst_das_suffix_nicht_vom_boersencode_ueberstimmen` — deine
Reihenfolge, `WRONG.DE`/`NMS` vor `RIGHT`/`NMS`, beide `ETF`, Präferenz
`XNAS`. Beide Treffer tragen **denselben** Yahoo-Code; allein das Suffix
unterscheidet sie, sonst bewiese der Test die Rangfolge nicht. Geprüft wird
`(symbol, ticker, mic) == ("RIGHT", "RIGHT", "XNAS")`.

**Mutationsgeprüft:** die alte Oder-Verknüpfung wieder in die Auswahl
eingesetzt → Test rot mit `'WRONG.DE' != 'RIGHT'`.

#### Verhalten, das ausdrücklich gleich geblieben ist

`_identity` und `split_symbol` sind **gemessen**, nicht angenommen: In einem
`git worktree` auf `43003a9` dieselben acht Fälle durch beide Funktionen
geschickt und mit `192ac94` verglichen — Ergebnis zeichengleich.

```
EUNL.DE/GER → (EUNL, XETR)   FOO.ZZ/NMS  → (None, None)
GOLD.SG/STU → (GOLD, XSTU)   BRK-B/NYQ   → (None, None)
AAPL/NMS    → (AAPL, XNAS)   RDS-A.L/LSE → (None, None)
WRONG.DE/NMS→ (WRONG, XETR)  RIGHT/NMS   → (RIGHT, XNAS)
```

`RDS-A.L` ist der interessante Fall: Suffix bekannt, Ticker nicht kanonisch —
die Ablehnung kommt weiterhin von der Ticker-Prüfung, nicht von der
Börsenableitung. `test_resolver_identity.py:225` deckt ihn ab.

Der Fremdbörsen-Fallback ist unverändert.

#### Nachgezogen

* Ticket: `#2h4` für die gemeinsame Ableitung, Fußnote `[^l]`.
* Spec: ein Nachtragsabsatz zur **Gegenrichtung** — bisher stand dort nur,
  dass aus der Identität das Providerformat entsteht (`provider_alias`), nicht
  wie man aus einem Anbietertreffer zurück auf die Börse schließt. Genau diese
  Lücke hat die zweite Rangfolge entstehen lassen.

#### Verifikation

* `make test` — Backend **485 passed, 29 skipped** (vorher 481), Plugin-API
  **36 passed**, Dashboard **235 passed**.
* `npm --prefix dashboard run build` — erfolgreich; nur der bestehende
  Chunkgrößen-Hinweis.
* `.venv/bin/ruff check app tests plugin_api/src plugin_api/tests` — sauber.
* `./_tickets/T-21-smoke.sh --run` — **9/9**, Original-DB nur gelesen.
* `./_tickets/T-21b-smoke.sh --run` — **6/6**, beide Läufe live gegen das Netz.
* Mutationsprobe: alte Oder-Verknüpfung → 1 Test rot.
