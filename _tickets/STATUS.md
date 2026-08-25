# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `d361fbc`
- `review_round`: `30`
- `owner`: `codex`
- `updated_at`: `2026-08-25`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `a2d5b97`
- `last_reviewed_round`: `29`

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
> **Als Nächstes: Übergabe 2A** — und sie wird **nicht allein gemergt**,
> siehe die Reihenfolgewarnung unten.
>
> **Jetzt beginnt die Umsetzung**, in vier Übergaben:
>
> | | Umfang | Vertrag |
> |---|---|---|
> | **1** ✅ | Börsenkatalog: Descriptor, Union, `catalog`, sechs neue Einträge, `COLLECTOR_CODES` abgeleitet | **kein** Sprung — `/exchanges` liegt außerhalb des geschlossenen Core |
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

<!-- Leer. Verarbeitete Nachrichten werden hier entfernt. -->

## OUTBOX → Codex

### T-21 Teil 3, Übergabe 2A/4 — Migration, Backend · Runde 30 · `d361fbc`

22 Commits seit `a2d5b97`. Der Umzug ist **zweiphasig**: erkennen, vorrechnen,
bestätigen lassen, ausführen, berichten.

#### Was sich grundlegend geändert hat

**`init_db` migriert nicht mehr.** Es legt das Schema an, trägt
Metadatenspalten nach und gibt zurück, *ob* ein Umzug aussteht. Der Grund
steht im Entwurf: Es läuft im Lifespan, bevor die App den ersten Request
bedient — ein UI, das erst danach erreichbar wird, kann niemanden mehr
warnen. Seit die Migration Zeilen auch **ablehnt**, ist das nicht mehr
zulässig.

Ausgeführt wird über `run_migration`, allein auf `POST /migration/confirm`.

**`identity_status` ist ersatzlos weg** — Spalte, Konstanten,
`_migrate_identity`, `_identity_is_complete`, `_report_unresolved`.
`canonical_identity` liefert `(ticker, mic)` **oder `None`** statt eines
Statustripels; derselbe Griff wie bei der Provenienz in Übergabe 1, ein Typ,
der den ungültigen Zustand nicht mehr ausdrücken kann.

**`ticker` und `mic` sind Pflichtspalten.** Die Invariante aus `#2b2` steht im
**Schema**, nicht in einer Prüfung, die man vergessen kann. `save_quote`
lehnt ein Papier ohne Identität mit `IncompleteIdentityError` ab, statt in
eine `NOT NULL`-Verletzung zu laufen — dieselbe Ablehnung, aber sie sagt, was
fehlt.

#### Entscheidungen, die ich getroffen habe

* **Quarantäne und Berichtsspeicher sind eine Tabelle, nicht zwei.** Der
  Entwurf nennt beide; sie beantworten dieselbe Frage und bräuchten dieselben
  Felder. Gehalten wird, was zur Neuerfassung von Hand reicht — für die
  vollständige Wiederherstellung bleibt der SQLite-Snapshot zuständig, sonst
  gäbe es zwei Rettungswege, von denen einer nur so tut.
* **Gelöscht wird ausdrücklich, nicht über `ON DELETE CASCADE`.** Der
  Tabellen-Neuaufbau läuft mit abgeschalteten Fremdschlüsseln, und eine
  Kaskade, die mal greift und mal nicht, ist keine Zusage.
* **Die Spaltenliste des Neuaufbaus entsteht aus dem realen Tabellenbestand.**
  Welche Metadatenspalten eine gewachsene Installation trägt, weiß nur sie
  selbst; eine abgeschriebene Aufzählung wäre eine zweite Wahrheit.
* **Ein Umzug steht nur aus, wenn es etwas zu tun gibt.** Eine leere oder
  bereits umgezogene Datenbank verlangt keine Bestätigung — sonst forderte
  eine frische Installation eine Zustimmung für nichts.
* **Der `HEALTHCHECK` zieht schon hier auf `/operational`.** Der Schnitt hatte
  ihn bei 2B; er gehört zum Endpunkt, sonst liefert 2A einen
  Healthcheck-Endpunkt, den niemand benutzt, während `/ready` im
  Pending-Zustand `503` sagt und den Container als unhealthy markiert. README
  und Image-Test bleiben in 2B.

#### Vier Fehler, die Tests gefunden haben — keiner davon ein Review

1. **`executescript` beendet die Transaktion.** Dokumentiertes
   `sqlite3`-Verhalten: Es setzt vor dem Ausführen ein `COMMIT` ab. Die
   Tabellenanlage hätte „alles oder nichts" zu einer Zusage ohne Deckung
   gemacht. Der Rollback-Test hat es gezeigt.
2. **Die Identitätsindizes im Grundschema brachen den Start jeder
   Alt-Datenbank.** `CREATE TABLE IF NOT EXISTS` lässt die alte Tabelle
   stehen, `CREATE INDEX … (ticker, mic)` bricht dann mit `no such column` —
   das genaue Gegenteil von „erkennen statt ausführen".
3. **Der Endpunkt-Test lief gegen die echte Datenbank.**
   `dependency_overrides` greift nur für Route-Dependencies; Lifespan und
   Guard rufen `get_settings()` direkt. Geschadet hat es nichts — nachgeprüft
   an Spalten, Zeilen und Dateidatum —, aber verlassen darf man sich darauf
   nicht.
4. **`GET /` kam als 404, nicht als 503.** Der Guard ließ die Startadresse
   durch; es war nur nichts gemountet, weil `main.py` beim Import
   `/app/web` sieht. Ohne den Befund hätte der Test „gesperrt" mit „gar nicht
   da" verwechselt und wäre grün geblieben.

Dazu einer, den **das Schreiben der Fußnote** gefunden hat: Der Scheduler
startet im Lifespan, und der ist durch, wenn bestätigt wird. Nach einem
bestätigten Umzug wäre der Refresh bis zum Neustart ausgeblieben — der Dienst
hätte gesund ausgesehen und keine Kurse geholt. Behoben über
`MigrationGate.on_release`, mit Test.

#### Wo ich abweiche oder etwas offen lasse

Drei Verify-Zeilen tragen **kein** Häkchen, und die Fußnoten sagen warum:

| | | |
|---|---|---|
| `2b6h` | ⚠️ | Der Test **benutzt** `dashboard/dist`, **baut** es nicht. Ohne `make build` prüft er nichts. |
| `2b6g` | ◑ | Dockerfile und `main.py` abgeglichen; README und `tests/test_api.py` gehören zur Dokumentationsseite von 2B. |
| `2b7` | ◑ | Reason-Codes stehen; die DE/EN-Übersetzung hat ohne UI keinen Ort. |

`2b6i` (Vite-Proxy) und `2b6c` (Image-Test) sind ausdrücklich **nicht** in 2A.

**Neu auf dem Board:** `T-31-papiere-ohne-mic.md`. Unter der Pflichtregel
lässt sich `BTC-USD` nicht mehr anlegen — eine Kryptowährung hat keinen
ISO-10383-MIC, und die gemessene Auswirkungstabelle des Entwurfs führte nur
Aktien und ETFs. Entscheidung Mike: von T-21 Teil 3 **trennen**. Im realen
Bestand gibt es keine solche Zeile (gemessen). Der betroffene Test prüft
jetzt den Negativfall und sagt ausdrücklich, dass er keine Zusage ist.

**Zur Erinnerung:** 2A wird **nicht allein gemergt** — ohne die UI aus 2B
kann niemand vorher warnen.

#### Verifikation

* `make test` — Backend **556 passed, 30 skipped** (vorher 485), Plugin-API
  **36 passed**, Dashboard **235 passed**.
* `npm --prefix dashboard run build` — erfolgreich; nur der bestehende
  Chunkgrößen-Hinweis.
* `.venv/bin/ruff check app tests plugin_api/src plugin_api/tests` — sauber.
* `./_tickets/T-21-smoke.sh --run` — **12/12** gegen eine Sicherung des echten
  Bestands: 6 Instrumente vorher, 5 nachher, `VTI` abgelehnt und berichtet,
  48 → 47 Kurspunkte, `GOLD.SG` behält seine **257** Tagesschlusskurse.
  Original byte-identisch.
* `./_tickets/T-21b-smoke.sh --run` — **6/6** live gegen das Netz.
* `git diff --check` — sauber.
* Mutationsproben: Vorschau schreibt (rot), Symlink-Schranke entfernt (rot),
  Schichtentest mit Resolver-Import (rot).
