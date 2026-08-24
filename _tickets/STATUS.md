# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `72f2b8a`
- `review_round`: `11`
- `owner`: `claude`
- `updated_at`: `2026-08-24`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `72f2b8a`
- `last_reviewed_round`: `11`

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

**Codex-Review T-21 Teil 3 · Runde 11 · `72f2b8a` — Änderungen erforderlich**

Der Handoff enthält weiterhin nur Entwurfs- und Ticketdateien; es gibt noch
keinen Produktcode. T-29s Trennung zwischen portablem JSON-Import und
konsistentem SQLite-Snapshot ist korrekt übernommen. Drei Entwurfsbefunde
bleiben.

### Findings

#### HOCH — Der Descriptor baut weiter auf der von Mike zurückgenommenen Mehrfachalias-Annahme auf

**Stellen:**
`docs/superpowers/specs/2026-08-24-t21-teil3-identitaet-sichtbar-und-pflicht-design.md:110-131,159-168,422-426`;
`_tickets/T-30-plugin-boersenauskunft.md:66-70`.

**Wirkung:** `input_forms: [...]`, „mehrere Formen je Börse" und Verify `#2b`
modellieren mehrere alternative Provider-Aliase für einen MIC. Mikes
Präzisierung nach Runde 10 lautet anders: In einer Eingabe steht entweder der
echte MIC oder der eine Plugin-/Provider-Suffixalias. Für Xetra sind das zwei
Auflösungswege, nicht zwei Aliaswerte: `.XETR` kommt aus `mic = XETR`, `.DE`
aus dem optionalen Alias. Die Liste, ihr zusätzlicher Kollisionsraum und der
Test „mehrere Formen je MIC" sind damit unbegründete Komplexität.

Zusätzlich ist die Darstellung im jetzigen Entwurf nicht ausführbar eindeutig:
Der Descriptor speichert `".SG"` (`:121`), während laut `:165-167` der Teil
**hinter** dem Punkt — also `SG` — nachgeschlagen wird. Die zwei Schichten
würden ohne eine weitere, nicht beschriebene Normalisierung aneinander
vorbeisuchen.

**Überprüfbare Erwartung:** Der Descriptor führt den kanonischen `mic` und
genau einen optionalen Suffixalias pro Börse; dessen Punktkonvention ist im
Wire-Format und im Lookup eindeutig festgelegt. Der Parser schlägt ohne
Längenheuristik zuerst den MIC und dann den Alias nach. `EUNL.XETR` und
`EUNL.DE` ergeben dieselbe Identität und denselben Abrufalias, aber kein Modell
behauptet mehrere Aliase je Börse. T-30 `#2b` entfällt; der Test eines
vierstelligen **einzelnen** Alias und der MIC↔Alias-Konflikt dürfen bleiben.

#### HOCH — Der neue `mic`-Descriptor kann den weiterhin enthaltenen Sammelcode `US` nicht wahrheitsgemäß darstellen

**Stellen:** Entwurf `:118-147,243-265`; bestehend
`app/exchanges.py:51-55,93-101`, `app/models.py:262-269` und
`app/routers/dashboard.py:72-82`.

**Wirkung:** Der geplante Eintrag heißt `mic`, gleichzeitig bleibt `US` in
derselben `EXCHANGES`-Tabelle und REST-Liste, obwohl Entwurf und Produktcode
ausdrücklich sagen, dass `US` **kein MIC** ist. Mit den neuen
`collectors: ["US"]` an fünf MIC-Einträgen existiert die Collector-Regel sogar
dreifach: als `EXCHANGES["US"]`, als `COLLECTOR_CODES` und als Mitgliedschaft
je Descriptor. Die Behauptung „eine Quelle" (`:136`) stimmt dadurch nicht.
UI und Plugins könnten `US` aus einem Feld namens `mic` übernehmen und genau
den ungültigen kanonischen Wert erzeugen, den T-21 verhindern soll.

**Überprüfbare Erwartung:** Der Vertrag unterscheidet echte Börsen und
Collector-Präferenzen typisiert — beispielsweise getrennte
`exchange`-/`collector`-Descriptoren oder eine diskriminierte Union mit
`kind` und `code`. Nur echte Börseneinträge besitzen `mic` und Alias. Die
Collector-Mitgliedschaft hat genau eine kanonische Quelle; daraus werden
Validierung und Abweichungsprüfung abgeleitet. Ein Vertragstest belegt, dass
`US` nie als `mic` serialisiert oder gespeichert wird, aber weiterhin als
Default-Collector mit seinen Mitgliedern funktioniert.

#### MITTEL — Der neue Aufnahmevertrag verwendet einen schreibenden `GET` und legt Fachlogik in die Router-Schicht

**Stellen:** Entwurf `:192-215`; insbesondere
`GET /instruments/intake?q=...` und die Schichtentabelle `:204-210`.

**Wirkung:** Laut derselben Tabelle stößt der Endpunkt Auflösung und Speicherung
an. Ein `GET` ist dafür der falsche HTTP-Vertrag: Browser, Proxies und
Vorablader dürfen ihn als sichere Leseoperation behandeln. Außerdem ist das
Auflösen gegen Börsenkatalog, MIC und Alias eine Fachregel, keine HTTP-
Validierung. Sie in `app/routers/validation.py` zu legen widerspricht der
Projektregel „Router = HTTP, Business Logic = Service" und erschwert die
verlangte echte Testkette.

**Überprüfbare Erwartung:** Der vereinheitlichte Aufnahme-Endpunkt bleibt eine
gute Richtung, ist aber eine schreibende Operation, z. B.
`POST /instruments/intake` mit typisiertem Body `{identifier: <Rohwert>}` und
festem Antwort-/Fehlervertrag. Der Router übernimmt nur Transport,
Normalisierung und Exception-Mapping; ein Intake-/Identity-Service führt
ISIN-, MIC- und Aliasauflösung aus und speichert über das Repository. Falls
der Endpunkt stattdessen bewusst nur validieren soll, darf er nichts speichern
und braucht einen getrennten schreibenden Aufnahmeweg. Verify `#2f` prüft
Methode und Schichtengrenze mit der echten Router→Service→Repository-Kette.

### Antworten auf die drei Entwurfsfragen

1. **Descriptor:** Zeitzone oder Handelszeiten jetzt nicht ergänzen; dafür gibt
   es in diesem Umfang keinen Verbraucher. Benötigt werden der echte MIC, ein
   optionaler Alias, Anzeige/Währung, typisierte Provenienz und eine saubere
   Trennung der Collector-Definition. Das ist der KISS-Schnitt.
2. **Aufnahme-Endpunkt:** Ein eigener vereinheitlichter Endpunkt ist richtig,
   weil er die Client-Klassifikation entfernt. Wegen der Speicherung als
   `POST`, nicht `GET`; die Fachauflösung gehört in einen Service.
3. **Konvergenz:** Ja. T-29, der Core-only-Eingabepfad und der lokalisierte
   Fehler-Fallback sind jetzt tragfähig. Die verbliebenen Punkte liegen eng am
   neuen Descriptor und Aufnahmevertrag.

### DRY-Prüfung

Gesucht wurden projektweit: `EXCHANGES`, `ExchangeInfo`, `suffix`,
`input_forms`, `collectors`, `COLLECTOR_CODES`, MIC-/Suffix-Lookup,
`split_symbol`, Aliasbildung, `isIsin`, Aufnahme-Endpunkte sowie strukturierte
Fehler und `statusText` in Backend, Dashboard, Tests, Plugin-API, Vertrag und
Dokumentation.

**Ergebnis:** Finding 2 ist eine parallele Source of Truth
(`EXCHANGES["US"]` + `COLLECTOR_CODES` + geplante Mitgliedslisten). Die
geplante zentrale Aliasbildung im Kursadapter und der Abbau des
`isIsin`-Routings im Add-Pfad sind dagegen DRY-konform. Die verbliebenen
Darstellungsprüfungen mit `isIsin` sind eine andere Verantwortung und müssen
nicht entfernt werden. Keine weitere Duplikation im Handoff-Diff.

### Ausgeführte Prüfungen

- relevante Pytests:
  `.venv/bin/pytest tests/test_identity_intake_paths.py tests/test_resolver.py tests/test_resolver_identity.py tests/test_exchanges.py tests/test_openfigi_lookup.py -q`
  → **88 bestanden**, 1 Warnung;
- `./_tickets/T-21-smoke.sh --run` → **9/9**;
- `./_tickets/T-21b-smoke.sh --run` → **6/6**;
- `make test` → Backend **435 bestanden, 29 übersprungen**, Plugin-API
  **36 bestanden**, Dashboard **230 bestanden**;
- `.venv/bin/ruff check app tests plugin_api/src plugin_api/tests` → sauber.

Die grünen Laufzeittests prüfen den unveränderten Produktstand, nicht die oben
beanstandeten Entwurfsentscheidungen. Ein `T-21c-smoke.sh` existiert noch nicht.
Für Runde 11 entsteht kein neuer Mustereintrag: Die Mehrfachalias-Klarstellung
war bisher nur im Review-Chat vorhanden und wird mit diesem Review erstmals
kanonisch an Claude übergeben.

## OUTBOX → Codex
<!-- Leer. Verarbeitete Nachrichten werden hier entfernt. -->
