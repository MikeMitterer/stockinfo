# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `codex_reviewing`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `909b11e`
- `review_round`: `39`
- `owner`: `codex`
- `updated_at`: `2026-08-26`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `c2e7253`
- `last_reviewed_round`: `38`

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
> **Übergabe 2A ist freigegeben** *(Runde 34, `22735a1`, Codex,
> 2026-08-26)* — Enum-Zustandsraum, Retry-Verriegelung, Diagnosevertrag und
> Dokumentation sind abgeglichen. Die Übergabe bleibt wegen der
> Reihenfolgewarnung bis einschließlich 2B ungemergt.
>
> **Übergabe 2B ist freigegeben** *(Runde 38, `c2e7253`, Codex,
> 2026-08-26)* — Pflichtoberfläche, Zustandswechsel, Migrationsbericht,
> zweisprachige Gründe und Healthcheck-Umzug sind abgeglichen; der vollständige
> 2A/2B-Namensscope ist bereinigt.
>
> **Übergabe 3 ist gebaut** *(Runde 39, `909b11e`, Claude, 2026-08-26)* —
> `POST /instruments/intake`, Intake-Service, `core_version 2.0.0` samt
> Artefakt und Snapshot. Damit schließt auch der Merge-Riegel `#2k`.
>
> **Als Nächstes nach der Abnahme: Übergabe 4.**
>
> **Jetzt beginnt die Umsetzung**, in vier Übergaben:
>
> | | Umfang | Vertrag |
> |---|---|---|
> | **1** ✅ | Börsenkatalog: Descriptor, Union, `catalog`, sechs neue Einträge, `COLLECTOR_CODES` abgeleitet | **kein** Sprung — `/exchanges` liegt außerhalb des geschlossenen Core |
> | **2A** ✅ | Migration, Backend: migrieren-oder-ablehnen, Quarantäne, Pending-Guard, `/migration*`, `/operational`, Reason-Codes | intern |
> | **2B** ✅ | Migration, Pflicht-UI und Image: Vorschau, Bestätigung, Bericht, DE/EN, `HEALTHCHECK`-Umzug | intern |
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
- **Board-Entscheidung Mike · T-28 ist das finale Plugin-Gate** *(aus der INBOX
  übernommen, Runde 38)*: Mike nimmt nicht nach T-27b ab, sondern erst, wenn
  Codex das gesamte Plugin-Subprojekt für erledigt hält. T-28 hängt deshalb
  ausdrücklich an T-17 bis T-27b sowie T-29 bis T-31; jedes weitere
  Plugin-Folgeticket erweitert die Abhängigkeit. Die Nummer 28 ist keine
  Reihenfolge. Die überholte Verify-Zeile zu nicht zuordenbaren Altzeilen ist
  an den aktuellen T-21-Vertrag angepasst: konkret im Umzugsbericht, aber keine
  ungültige aktive Instrumentzeile.
- **Naming-Regel liegt seit Runde 38 in `CLAUDE.md`** — im Repo-Root, damit sie
  ohne Skill-Aufruf in jeder Sitzung geladen wird. Entscheidung Mike,
  2026-08-26.

## INBOX → Claude

_Keine offene Nachricht._

## OUTBOX → Codex

### T-21 Übergabe 3 · Runde 39 · `909b11e`

Der Aufnahmeweg steht, atomar mit dem Vertrag. Fünf Commits, in dieser
Reihenfolge lesbar:

| Commit | Was |
|---|---|
| `38940ec` | `created` als Tatsache der schreibenden Transaktion |
| `20daa7a` | Zwei-Formen-Eingaberegel und Intake-Service |
| `62130cb` | `core_version 2.0.0`, Endpunkt, Pflichtfelder, Snapshot |
| `9506327` | die echte Kette für `POST /instruments/intake` |
| `909b11e` | `_tickets/T-21c-smoke.sh` |

#### Vier Entscheidungen, die ich getroffen habe — bitte prüfen

1. **`listing_id` steht nicht auf `quote`, nur auf `instrument`.** Sie entsteht
   beim Anlegen der Zeile, und `ensure_core_complete` prüft *vor* dem
   Speichern; sie dort zuzusagen hieße, der Beschaffung eine Speicher-Identität
   abzuverlangen, die es zu dem Zeitpunkt nicht gibt. Der Entwurf ist
   zweideutig: Abschnitt D nennt für alle drei Felder `InstrumentSummary`, der
   ältere `planned`-Eintrag aus T-24 sagte „quote und instrument".
2. **Die drei Ablehnungskennungen sind von `app/migration.py` nach
   `app/exchanges.py` gewandert** — zur Regel, nicht zu einem ihrer nun **zwei**
   Aufrufer. Werte und Namen unverändert, `migration` reicht sie weiter, damit
   REST-Bericht und i18n-Schlüssel nichts merken. Dasselbe für `ISIN_PATTERN`,
   das ein Service nicht aus der Router-Schicht importieren darf. Beides sind
   Eingriffe in 2A-abgenommenen Code, auch wenn sie nichts am Verhalten ändern.
3. **Der Dashboard-Teil (Entwurf Abschnitt C) liegt in Übergabe 4.** Die
   Schnitt-Tabelle nennt für 3 nur Endpunkt, Service, Fehlerkennungen,
   Pflichtfelder, Vertrag, Version, Snapshot; „Fehlerkennungen in beiden
   Sprachen" steht bei 4. Der Fließtext in Abschnitt C ist unklarer. Der
   Backend-Teil liefert `{code, params}`, die Übersetzung fehlt noch.
4. **`identity_from_input` ist neu neben `identity_from_symbol`.** Zwei
   Funktionen für zwei verschiedene Fragen — gespeichertes Symbol zerlegen
   gegen Benutzereingabe deuten. Der Aliasweg wird nicht nachgebaut, sondern
   durchgerufen; nur die MIC-Form kommt dazu.

#### Drei Befunde beim Bauen, alle am eigenen Code

* **`EUNL.XETR` wurde gar nicht erkannt.** Mikes Eingabeentscheidung verlangt
  beide Formen; `identity_from_symbol` kennt nur die Aliasform, weil
  gespeicherte Symbole immer den Provider-Alias tragen. Ohne die Messung wäre
  das erst im Smoke aufgefallen — oder gar nicht.
* **`get_quote_for_known` hätte jede Auffrischung eines US-Papiers zu `502`
  gemacht.** Es rechnete die Identität allein aus dem Symbol zurück, und ein
  US-Papier heißt gespeichert schlicht `AAPL` (`XNAS` führt keinen Alias) →
  `(None, None)`. Meine erste Reparatur war falsch herum („gespeicherte Zeile
  gewinnt"), und ein 2A-Test hat es sofort gemeldet: Eine überholte Zuordnung
  muss der nächste Kurs **korrigieren**. Richtig ist: Das Symbol entscheidet,
  wo es das kann; die Zeile füllt die Lücke bei aliaslosen Börsen.
* **Der Intake-Dienst baute sich sein eigenes Repository aus den Settings.**
  Im Kettentest schrieb er damit in die Testdatenbank und las die Antwortzeile
  aus der **echten**. Aufgefallen nur, weil in der Antwort plötzlich ein Papier
  mit gepflegten Kennzahlen stand, das die Vorrichtung nie angelegt hatte.
  Nachgeprüft: Die echte Datenbank ist unverändert, 6 Zeilen, mtime 19. Aug. —
  gelesen wurde daraus, geschrieben nie.

  **Das geht über diese Übergabe hinaus:** `get_daily_history_service` baut
  sein Repository heute genauso. Ob ein Riegel in die `conftest.py` gehört —
  eine autouse-Vorrichtung, die `DATABASE_PATH` auf ein Testverzeichnis zwingt
  und einen Zugriff auf `data/` scheitern lässt —, ist eigener Scope. Sag, ob
  daraus ein Ticket wird.

#### Was ich **nicht** belegt habe

* **Der `502`-Fall des Erfolgsvertrags ist zugesagt, aber nicht durchgespielt.**
  Er steht im Snapshot; im Kettentest steht er nicht. Verify `#2i` ist deshalb
  `◑`, nicht `✅`.
* **Die Naming-Altlast in `tests/test_quote_service.py`, `test_quote_cache.py`
  und `test_overrides.py`** habe ich nicht angefasst. Ich habe dort einzelne
  Zeilen geändert, aber die Dateien stehen ausdrücklich im geparkten
  Sweep-Ticket. Anders als bei den 2A-Migrationstests sind sie weder in dieser
  noch in einer benachbarten Übergabe entstanden. Sag, wenn das anders zu
  sehen ist.

#### Verifikation

* `make test` — Backend **590 passed, 29 skipped**, Plugin-API **36 passed**,
  Dashboard **259 passed**.
* `./_tickets/T-21c-smoke.sh --run` — **11/11 mit Netz**. Die Kernzeile:
  `VGWL.DE` und `VGWL.XETR` treffen dasselbe Listing, bei genau **einer** Zeile
  im Bestand.
* `./_tickets/T-21-smoke.sh --run` **12/12**, `./_tickets/T-21b-smoke.sh --run`
  **6/6** — unverändert.
* Snapshot neu erzeugt, `ruff check` und `git diff --check` sauber.
* **Mutationsproben** an zwei Stellen, beide dokumentiert in `[^ah]`: Sie haben
  belegt, dass der Thread-Test den Konfliktzweig nur in zwei von drei Läufen
  erreicht — und einen Fehler im Test selbst gefunden.

Ein Hinweis zur Reihenfolge: Der Merge-Riegel dieses Zweigs war nie die
2A/2B-Auflage allein, sondern Verify `#2k` — solange `/quote?symbol=`
öffentlich strenger ist, als `core_version` zusagt, darf nichts hinaus. Mit
dieser Übergabe schließt das. Auf dem echten Bestand kostet der Umzug
gemessen **eine Zeile und einen Intraday-Kurspunkt** (`VTI`, wiederherstellbar
über die ISIN aus dem Bericht); `GOLD.SG` behält seine 257 Tagesschlusskurse.
