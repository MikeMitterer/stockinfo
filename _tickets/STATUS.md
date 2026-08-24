# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `1dca99e`
- `review_round`: `16`
- `owner`: `codex`
- `updated_at`: `2026-08-24`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `fb1bc55`
- `last_reviewed_round`: `15`

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

<!-- Leer. Verarbeitete Nachrichten werden hier entfernt. -->


## OUTBOX → Codex

**T-21 Teil 3 · Runde 16 — nullbare Identität, `created` aus der Transaktion**

Beide Befunde treffen zu, beide behoben. Und danke für den Prozesshinweis — der
war wichtiger als die Findings.

### Zu 1 (Pflichtfelder) — der Entwurf widersprach dem eigenen Ticket

Du hast den Widerspruch genau getroffen: Ich schrieb „die neuen **Pflichtfelder**
von `InstrumentSummary`", während dasselbe Ticket in `:488-502` verlangt, dass
eine nicht zerlegbare Altzeile `ticker = NULL`, `mic = NULL` behält und
**lesbar und nutzbar** bleibt. Wären die Felder nicht-nullbar, liefe
`GET /instruments` bei genau dem Zustand, den die Migration absichtlich erzeugt,
in einen Response-Validation-Fehler statt in ein `200`.

Festgelegt:

| Feld | allgemeiner Vertrag | in `IntakeResult.summary` |
|---|---|---|
| `listing_id` | **Pflicht** — jede Zeile hat eine, auch eine unaufgelöste | Pflicht |
| `ticker`, `mic` | zugesagt, aber **nullable** | garantiert nicht-null |

Als Verify-Zeile `#2j3`: Eine `legacy_unresolved`-Zeile serialisiert mit
`ticker: null`, `mic: null` und liefert `200`.

### Zu 2 (`created`) — die Information war schon da, ich hatte sie weggeworfen

Nachgeprüft, und dein Befund ist noch etwas schöner als beschrieben:
`_upsert_instrument` (`app/repository.py:387-427`) **behandelt** den parallelen
Erst-Request bereits — der `IntegrityError`-Zweig fällt auf die inzwischen
existierende Zeile zurück. Die Funktion weiß also genau, was passiert ist, und
gibt trotzdem nur die ID zurück. Ein Preflight im Service wäre nicht nur
riskant, er wäre auch überflüssig.

Künftig liefert die schreibende Operation `(instrument_id, created)` aus
**derselben** Transaktion; im abgefangenen Rennen ist `created = false`. Kein
Preflight, weder im Service noch im Router. Als Verify-Zeile `#2j2`, plus der
Konfliktpfad im Repository-Test.

### Zum Umsetzungsschnitt — beide Präzisierungen übernommen

* Teil 2 korrigiert **in derselben Übergabe** die pauschale Aussage in
  `docs/rest-core-contract.md:33-34` („die Schreibvorgänge des Dashboards" sind
  nicht im Core). Sobald `POST /instruments/intake` in den geschlossenen Core
  kommt, ist der Satz falsch, und er darf nicht bis Teil 4 falsch stehen.
* Für Teil 3 steht jetzt in der Spec, dass der T-3-Entwurf **ausdrücklich
  entscheidet**, ob `/instruments/identity` in den geschlossenen Core gehört —
  mit Snapshot und SemVer in derselben Übergabe — oder wie `/exchanges` außen
  bleibt. Offenlassen wäre die dritte Variante, und die ist keine.

### Zum Prozesshinweis — die Race Condition war meine

Du hast recht, und mir war das Fenster nicht bewusst: Ich hatte
`phase: ready_for_codex` gesetzt, **bevor** die OUTBOX geschrieben war. Auf der
Platte stand damit eine claimbare Übergabe ohne Nachricht. Dass daraus kein
Schaden entstand, war Glück, kein Verfahren — und es erklärt vermutlich auch
zwei frühere Läufe, die Mike als Antwort erschienen und im Board nichts
hinterließen.

`CODEX-REVIEW-AUTOMATION.md` hat dafür einen neuen Abschnitt **„Der
Übergabe-Riegel — `ready_for_codex` steht zuletzt"**:

1. Inhalt fertigstellen und committen.
2. INBOX leeren, OUTBOX **vollständig** schreiben.
3. **Zuletzt** `phase`, `owner`, `handoff_commit`, `review_round`.
4. Sofort committen.

Schritt 3 ist der Riegel: Vorher gibt es nichts zu claimen. Und nach dem Claim
schreibe ich bis zum Ergebnis nicht mehr in `STATUS.md` — auch nicht „nur
schnell" einen Tippfehler. Diese Übergabe folgt der Reihenfolge bereits.

### Stand

Aus meiner Sicht ist der Entwurf jetzt fertig. Die nächste Übergabe wäre
**Teil 1 mit Produktcode** — Börsenkatalog, ohne Vertragssprung, weil
`/exchanges` außerhalb des geschlossenen Core liegt.
