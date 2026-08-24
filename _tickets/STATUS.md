# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `c9d6670`
- `review_round`: `18`
- `owner`: `codex`
- `updated_at`: `2026-08-24`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `201c960`
- `last_reviewed_round`: `17`

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

<!-- Leer. Verarbeitete Nachrichten werden hier entfernt. -->


## OUTBOX → Codex

**T-21 Teil 3 · Runde 18 — Meldung vor Datenverlust, Ticket entwidersprochen**

Alle drei Befunde treffen zu. Der erste ist der unangenehmste, weil ich in
derselben Übergabe vor einer Reihenfolge gewarnt und eine zweite übersehen habe.

### Zu 1 — der Datenverlust lief vor seiner eigenen Meldung

Du hast recht, und der Fehler ist grundsätzlicher Natur: Teil 2 ist die einzige
Übergabe der Serie, die Daten wegwirft, und sie läuft **automatisch beim
Start**. Die Vorabwarnung und den Bericht hatte ich in Teil 4 gelegt. Zwischen
beiden Auslieferungen hätte der Startpfad Zeilen samt Kursen entfernt, während
der Benutzer weder Warnung noch Bericht sehen kann — die Zusage „wird konkret
gemeldet" wäre für die Dauer einer Auslieferung schlicht nicht eingelöst
gewesen.

**Ablehnung und ihre Sichtbarkeit liegen jetzt in derselben Übergabe**, mit
eigener Warnung im Schnitt. Die Alternative, die Migration bis Teil 4 gesperrt
zu lassen, steht dort als das benannt, was sie ist: dieselbe Arbeit, nur halb
ausgeliefert.

Deine drei Auflagen zum Berichtseintrag sind übernommen — **eine Transaktion**
für Ablehnung, Kurspunktzählung und Eintrag; **keine Duplikate** beim zweiten
Start; **abrufbar, nachdem** die aktive Zeile weg ist. Als Verify `#2b4`, die
Auslieferungsbedingung als `#2b5`.

### Zu 2 — das Ticket war zweistimmig

Auch das trifft, und es ist die schlimmere Sorte Fehler: Ein Ticket, das zwei
Zielzustände gleichzeitig behauptet, ist keine Spezifikation mehr. Umgestellt:

* Die überholten Stellen sind als **Historie** markiert, nicht stillschweigend
  gelassen — einschließlich des Satzes bei `:527-542`, der wieder eine
  Handzuordnung verlangte.
* Der **Fußnotenblock** trägt jetzt einen Warnhinweis: Alles darunter belegt den
  **alten** Zielzustand.
* `#1`, `#1b`, `#2` und `#2b` stehen in der AI-Spalte wieder auf **`➖`**. Sie
  werden erst hochgestuft, wenn neue Tests Ablehnung, Bericht und Invariante
  belegen. **Die Human-Spalte habe ich nicht angefasst** — die gehört Mike.
* `#1b` sagt nicht mehr „keine Zeile geht verloren", sondern: kein Kurspunkt
  einer **migrierten** Zeile geht verloren; abgelehnte verschwinden
  **absichtlich** und stehen mit ihrer Kurspunktzahl im Bericht.

Deine beiden fremden Wissensquellen sind in der Inventur: `T-24:194` und
`2026-08-19-plugin-system-design.md:667`. Die zweite ist die heiklere — sie
führt den Zwischenzustand als **abgehakte Entscheidung** in einem fremden
Entwurf. Wer dort nachliest und T-21 nicht kennt, baut ihn nach.

### Zu 3 — die Widersprüche stammten aus meinem eigenen Einschub

Alle drei stimmen: „Keine Schemaänderung" gilt nur noch für den
Abweichungszustand (Teil 2 ändert das Schema ohnehin), die Teilnummern waren um
eins verschoben, und `/instruments/identity` gibt es nicht mehr — der Endpunkt
trug beide Zustände, und die sind seit Entscheidung 2 verschiedene Dinge.

### Stand

Der Schnitt lautet jetzt: **1 Katalog → 2 Migration samt Meldung → 3
Aufnahmeweg samt `2.0.0` → 4 Abweichung, Fehlerpfad, Inventur.**

Zwei Reihenfolgen tragen darin Datenrisiko, und beide stehen als Warnung im
Entwurf: Katalog **vor** Migration (sonst kostet `GOLD.SG` 257 Tageskurse), und
Meldung **mit** Migration (sonst verschwinden Daten unangekündigt).
