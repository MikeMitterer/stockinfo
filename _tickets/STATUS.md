# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `43003a9`
- `review_round`: `27`
- `owner`: `codex`
- `updated_at`: `2026-08-25`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `083414c`
- `last_reviewed_round`: `26`

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

### T-21 Teil 3, Übergabe 1/4 · Runde 27 · `43003a9`

Beide Befunde sind umgesetzt.

#### Die Auswahl unterscheidet Handelsplatz und Sammelcode

Neu: **`preferred_mics(code)`** — die eine Stelle, die sagt, welche
Handelsplätze ein Vorgabewert umfasst. `preferred_aliases` ist daraus
**abgeleitet** statt daneben gepflegt; die Frage „was umfasst der
Vorgabewert?" hat damit genau eine Antwort.

`_at_exchange(quote, aliases, mics)` prüft einen Treffer auf zwei Wegen:
Suffix, oder Yahoos Börsencode über **`YAHOO_EXCHANGE_MICS`** — dieselbe
Abbildung, die `_identity` benutzt, um demselben Treffer später seinen MIC zu
geben. Keine zweite Mappingtabelle, wie in der DRY-Prüfung verlangt. Ein
Treffer, dessen Börse sich auf keinem der beiden Wege bestimmen lässt, gehört
zu keiner Präferenz; er kann weiterhin über den **unveränderten**
Fremdbörsen-Fallback gewinnen.

Zwei Resolver-Tests, in beiden steht der **falsche** Treffer zuerst — sonst
bewiese die Reihenfolge nichts:

* `test_yahoo_unterscheidet_eine_us_boerse_vom_sammelcode` — `XNAS`, Treffer
  `SPY`/`PCX` vor `ONEQ`/`NMS` → `ONEQ`/`XNAS`.
* `test_yahoo_laesst_einen_unbekannten_punktlosen_treffer_nicht_gewinnen` —
  `US`, Treffer `FUND`/`ZZZ` vor `ONEQ`/`NMS` → `ONEQ`/`XNAS`.

**Mutationsgeprüft:** die alte Regel („kein Alias → jedes punktlose Symbol
zählt") wieder eingesetzt → beide Tests rot, der zweite mit genau dem
`resolve_isin_ambiguous`/`Unavailable`-Pfad aus dem Befund. Dazu
`test_eine_praeferenz_umfasst_ihre_handelsplaetze` an der Quelle.

**Zur Herkunft des Befunds** — nicht als Einwand, der Fix gehört hierher:
Der Zweig „aliaslos → jedes punktlose Symbol" stammt nicht aus Runde 25/26,
er stand vor Übergabe 1 wörtlich so da (`0f79eec^`, `if suffix: … else: …`).
Neu ist, dass er **erreichbar** wurde: Bis dahin war `US` der einzige
aliaslose Eintrag, und die fünf echten US-MICs wurden erst mit dieser
Übergabe zu gültigen `DEFAULT_EXCHANGE`-Werten. Die `US`-Hälfte des Befunds
trifft damit auch bestehende Installationen mit `DEFAULT_EXCHANGE=US`.

Falls das als Muster taugt — **neue Tabelleneinträge machen einen schlafenden
Zweig erreichbar**; ein Fallback, der für genau einen Wert geschrieben wurde,
bedient plötzlich sechs. Ein Beleg ist zu wenig für einen eigenen Eintrag, und
`P-02` trägt ihn bereits. Deine Entscheidung, ob er dort richtig liegt.

#### Der TypeScript-Vertrag lässt den fehlenden Alias zu

`alias?: string | null`. `alias: string | null` verlangte die Property
weiterhin und war damit **strenger als der ausgelieferte Vertrag** — `alias`
steht nicht in `required`, ein Erzeuger darf das Feld auslassen. Der Typ-Test
führt jetzt beide zulässigen Formen, `null` und weggelassen. **Live
gegengeprüft:** Typ auf die alte Form zurückgesetzt → `TS2741: Property
'alias' is missing`, Build rot. Dazu ein `@ts-expect-error` auf ein fehlendes
`mic`, damit der Test nicht nur Nachsicht belegt.

**Wo der verbotene Leerstring wirklich garantiert wird:** bei Pydantic
(`min_length=1`), sichtbar als `minLength: 1` im OpenAPI-Schema —
`{"anyOf": [{"type": "string", "minLength": 1}, {"type": "null"}]}`. Ein
Stringtyp in TypeScript kann „mindestens ein Zeichen" nicht ausdrücken. Die
Behauptung, TypeScript trage diese Zusage mit, war meine, nicht die des Typs;
Ticket `#2h2`, Fußnote `[^j]` und die Spec sagen jetzt, welche Schicht sie
hält.

#### Nachgezogen

* Ticket: `#2h3` für die Auswahlregel mit Fußnote `[^k]`; `#2h2` und `[^j]`
  auf die tatsächliche Schichtenverteilung korrigiert.
* Spec: derselbe Nachtrag — „optional" heißt fehlend **oder** `null` in allen
  drei Schichten, der Leerstring-Bann liegt im Backend.

#### Verifikation

* `make test` — Backend **481 passed, 29 skipped** (vorher 474), Plugin-API
  **36 passed**, Dashboard **235 passed** (vorher 234).
* `npm --prefix dashboard run build` — erfolgreich; nur der bestehende
  Chunkgrößen-Hinweis.
* `.venv/bin/ruff check app tests plugin_api/src plugin_api/tests` — sauber.
* `./_tickets/T-21-smoke.sh --run` — **9/9**, Original-DB nur gelesen.
* `./_tickets/T-21b-smoke.sh --run` — **6/6**, beide Läufe live gegen das Netz.
* Zwei Mutationsproben: Auswahlregel zurückgesetzt → 2 Tests rot;
  TS-Typ zurückgesetzt → `TS2741`, Build rot.

