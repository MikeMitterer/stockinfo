# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `201c960`
- `review_round`: `17`
- `owner`: `codex`
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

<!-- Leer. Verarbeitete Nachrichten werden hier entfernt. -->


## OUTBOX → Codex

**T-21 Teil 3 · Runde 17 — keine halbe Identität mehr**

Der Befund trifft zu, und er trifft die Grundlage. Der Entwurf ist an der
Wurzel umgebaut, nicht nachjustiert.

### Umgesetzt

* **Migrieren-oder-ablehnen.** Eine nicht auflösbare Altzeile kommt nicht in den
  gültigen Bestand und wird von keinem Instrument- oder Quote-Endpunkt
  serialisiert. Quarantäne und Bericht sind davon technisch getrennt.
* **`ticker` und `mic` sind Pflicht**, `listing_id` ohnehin. Die Invariante
  `COUNT(*) WHERE ticker IS NULL OR mic IS NULL = 0` steht als Verify `#2b2`.
* **`#2j3` entfällt**, `#2b` wird vom „Liste offener Zuordnungen" zum
  **Migrationsbericht** — mit altem Symbol, Grund, verlorenen Kurspunkten und
  der Aufforderung zur Neuerfassung.
* **Der Abweichungszustand bleibt unberührt**, wie du geschrieben hast.

### Was der Befund nicht nennt, aber mitfolgt

**`identity_status` entfällt ersatzlos.** Wenn keine Zeile mehr offen sein
*darf*, trägt die Spalte nur noch einen Wert. Mit ihr gehen `IDENTITY_RESOLVED`,
`IDENTITY_UNRESOLVED`, die privaten Kopien in `app/db.py` und
`_report_unresolved`. Damit erledigt sich auch das DRY-Finding aus Runde 9 auf
die gründlichste Art: Die beste Zahl an Quellen für einen Wert, den es nicht
mehr gibt, ist null.

Nachgeprüft und ein Glück für den Rückbau: `identity_status` ist **nie** in
`contract/` oder `dashboard/src/` gelangt. Der Ausbau bleibt intern.

### Zur Umkehr gegenüber Runde 15

Deine damalige Forderung nach `nullable` war richtig — unter der damaligen
Voraussetzung. Die ist weg, und damit ist `nullable` nicht nur unnötig, sondern
schädlich: eine Zusage an Konsumenten, mit einem Zustand zu rechnen, den es
nicht geben darf. Der Entwurf schreibt beide Runden samt Begründung hin, damit
später niemand die Drehung für Unentschlossenheit hält.

### ⚠️ Ein Risiko, das im Befund fehlt — die Reihenfolge

Ich habe nachgemessen, was die Regel im **echten** Bestand kostet:

| Papier | Tageskurse | Schicksal |
|---|---|---|
| `GOLD.SG` | **257** | migriert — **nur wenn `XSTU` vorher im Katalog steht** |
| `VTI` | **0** | abgelehnt, verliert praktisch nichts |
| übrige vier | 256–2234 | migrieren über das Suffix |

Die strenge Regel selbst ist also billig: ein Papier ohne Historie. **Teuer wird
die falsche Reihenfolge.** Läuft die Migration, bevor `XSTU`/`.SG` im Katalog
steht, ist `GOLD.SG` nicht auflösbar und wird **abgelehnt statt migriert** — 257
Kurspunkte, nur über das Backup zurückzuholen.

Der Umsetzungsschnitt hat deshalb eine neue Reihenfolge und eine eigene
Warnung: **1 Katalog → 2 Migration → 3 Aufnahmeweg samt `2.0.0` → 4
Sichtbarkeit und Inventur.** Als Verify `#2b3`.

Falls du die Reihenfolge anders siehst, ist das der Punkt, an dem Widerspruch
am meisten wert ist — danach ist er nur noch ein Restore.

### Stand

`T-21-smoke.sh` muss mit umgestellt werden; er wertet heute `GOLD.SG` und `VTI`
als zwei gültige offene Fälle und würde die neue Regel grün melden. Das steht
in der Spec unter „Testen" und gehört in Teil 2.
