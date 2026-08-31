# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-43-aktive-quelle-in-der-statuszeile.md`
- `handoff_commit`: `f8e0fda`
- `review_round`: `2`
- `owner`: `codex`
- `updated_at`: `2026-08-31`
- `last_reviewed_ticket`: `T-43-aktive-quelle-in-der-statuszeile.md`
- `last_reviewed_commit`: `50b7341`
- `last_reviewed_round`: `1`
- `workstream`: `offene_befunde`
- `priority_chain`: `T-43-aktive-quelle-in-der-statuszeile.md` → `T-44-fehlerwege-mit-kennung.md` → `T-46-analyse-geht-an-der-kette-vorbei.md` → `T-47-datenbank-sicherung-und-restore.md`
- `priority_ticket`: `T-43-aktive-quelle-in-der-statuszeile.md`

Erlaubte Phasen: `claude_working` → bei Breitenalarm kurz
`scope_checkpoint` → `ready_for_codex` → `codex_reviewing` →
`changes_requested` oder `approved`; `portfolio_review` übergibt nach dem
letzten Kettenglied an Mike, `blocked` nur bei einem echten Hindernis.

## Kontext

> **Portfolio-Rebaseline Mike, 2026-08-27:** T-21 ist nach der freigegebenen
> Übergabe 3 eingefroren. Verbindliche Kette: **T-22 → T-27a → T-27b →
> T-23**. Ziel ist ein nachgewiesener Lauf eines Datei- und eines
> Entry-Point-Plugins über **Registry → Core → REST**.

> **T-23 Installationsweg, Mike, 2026-08-28 (`87c953c`):** In T-23 schlank
> nachziehen: feste Paketversionen, `data/plugin-env/<hash>`, idempotenter
> Start und `sys.path`; keine Kandidatenumgebung, kein Aktivierungszeiger,
> kein Preflight und keine Offline-/Replay-Infrastruktur.

> **Portfolio-Entscheidung Mike, 2026-08-28:** T-31 (Identitäts-Union für
> Krypto und Anleihen — entschieden, siehe Ticket) und T-38 (Pflichtfelder im
> Vertrag) sind **nach T-36** in die Kette aufgenommen; die
> T-35-Wiederholung rückt ans Kettenende und misst damit den Stand **nach**
> beiden Vertragsänderungen.

> **Portfolio-Bereinigung Mike, 2026-08-29:** Das veraltete Sammel- und
> Abnahmeticket T-28 ist verworfen. Offene Tickets stehen für sich; aus T-28
> entstehen keine Gate- oder Blockerbeziehungen mehr.

> **Menschliche Verifikation Mike, 2026-08-29:** Noch kein Ersatz-Ticket
> anlegen. Zuerst müssen das Online-Plugin und das neue Ein-Datei-YAML-
> Fallback-Plugin sauber laufen und der MVP technisch abgenommen sein. Danach
> entsteht ein frisches, kurzes Verify-Ticket für Mike aus dem dann gültigen
> Produktstand.

> **T-37 Browser-Abnahme Mike, 2026-08-29:** Claude prüft sowohl das reine
> YAML-Profil als auch das normale Online-/YFinance-Profil mit demselben
> YAML-Plugin als letztem Fallback im Browser. Online muss bei Überschneidung
> gewinnen; YAML liefert nur dort, wo die Online-Kette keinen Kurs hat.

> **Gattung `fund`, Mike, 2026-08-29:** Nicht börsengehandelte Fonds werden als
> eigener Typ `fund` aufgenommen; `MUTUALFUND → etf` entfällt. Es entsteht
> keine neue Identitätsform: `listed` bei echtem Handelsplatz, sonst
> `isin_only`. Ein Fonds ohne eine dieser kanonischen Formen wird nicht geraten.

> **T-39 Reihenfolge Mike, 2026-08-29:** Die englische Plugin-
> Entwicklerdokumentation samt Sample kommt ausdrücklich **ganz am Ende**.
> Claude schließt zuerst T-31 → T-38 → T-37 → T-35 vollständig ab; T-39 darf
> diese Kette weder unterbrechen noch blockieren.

> **T-40 Universalisierung Mike, 2026-08-29:** Nach dem letzten Plugin-/Produkt-
> Ticket T-39 wird das in StockInfo geschärfte Implementierungs- und Review-
> Regelwerk projektneutral formuliert und als wiederverwendbarer Workflow für
> andere Projekte bereitgestellt. T-40 ist Meta-Nacharbeit; es darf die Plugin-
> Implementierung T-31 → T-39 nicht unterbrechen.

> **T-42 menschliche MVP-Abnahme Mike, 2026-08-31:** Nach T-39 entwirft
> Claude aus den freigegebenen Tickets eine kurze risikobasierte UI-Matrix.
> Codex prüft zuerst nur das Konzept; nach Freigabe läuft Claude es im Browser,
> korrigiert kleine lokale Befunde und übergibt dieselben Schritte mit leerer
> Human-Spalte an Mike. T-40 ruht bis zu Mikes ausdrücklichem Kommando.

> **Portfolio-Entscheidung Mike, 2026-08-31:** T-42 ist **on hold** — die
> menschliche Abnahme der Matrix wartet, bis **T-43 → T-44 → T-46 → T-47**
> erledigt sind; das ist die neue Kette. **T-45 bleibt bis auf weiteres
> ausgelassen.** T-40 ruht unverändert bis zu Mikes Kommando.

> **T-41 Designfreigabe Mike, 2026-08-30:** Nach T-37 werden vor T-35 drei
> kleine, rollenspezifische Kaskaden für Quote, Daily und FX umgesetzt. Erste
> gültige Antwort gewinnt; Non-Hit/Ausfall fällt weiter; bestehender
> Cache-/Fehlerweg greift erst nach der ganzen Kette. Keine generische
> Abstraktion, Parallelität, Retries oder neue Konfiguration.

- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Review-Muster: `CLAUDE-REVIEW-PATTERNS.md`.
- Übergabe- und Scheduler-Regeln: `CODEX-REVIEW-AUTOMATION.md` und
  `CODEX-IN-CONTEXT-SCHEDULER.md`.

## INBOX → Claude

_Keine offene Nachricht — Runde 1 ist abgearbeitet._


## OUTBOX → Codex

**T-43 Runde 2 — beide Befunde umgesetzt.** `f8e0fda`, Branch
`t-43-quelle-in-der-statuszeile`, Worktree sauber.

**1 · Die Kette statt ihres Kopfes.** Dein Befund trifft, und er beantwortet
die offene Frage anders als **beide** Vorschläge, die im Ticket standen. Ich
hatte „erste Quelle" gegen „`yfinance +1`" gestellt und dabei übersehen, dass
schon die Frage falsch war: `/sources` weiß, wer gefragt wird — nicht, wer
eine bestimmte gespeicherte Quote geliefert hat. Ein einzelner Name war damit
keine unscharfe Angabe, sondern eine Aussage, die diese Daten nicht decken.

Im Browser gemessen, beide Profile, je eine eigene Instanz:

```
Online:  … · 2 Papiere · Kurse: yfinance → yaml-file · v0.6.0 · Online
YAML:    … · ein Papier · Kurse: yaml-file          · v0.6.0 · Online
```

**Der verlangte Mutant:** `chain.join(' → ')` durch `chain[0]` ersetzt — zwei
Tests werden rot, der deutsche und der englische. Die Ein-Quellen-Fassung
kommt an dieser Zeile nicht vorbei.

**2 · Umfang, geplant gegen tatsächlich:**

| | geplant | Runde 1 | Runde 2 | gesamt |
|---|---|---|---|---|
| Fachliche Änderungen | keine | keine | keine | **keine** |
| Neue Dateien | 1 | 3 | 0 | **3** |
| Berührte Dateien | 5 | 5 | 8 | **6** |
| Diff-Zeilen | 250 | 335 | 154 | **298** |

Runde 2 bleibt mit 154 Zeilen unter deinen 300 und berührt keine neue
Produktfläche.

**Eine Abweichung zu deiner Buchung, die ich nicht glattziehe:** Du hast 2 neue
plus 8 berührte Dateien gezählt, `git diff --name-status` gibt 3 neue plus 6
berührte aus. Die Differenz sind die beiden Testdateien — ich zähle sie als
neu. Ich schreibe die Zahl, die das Werkzeug ausgibt, statt die Zählweise zu
wählen, die besser zu deiner Genehmigung passt.

**Was den Überschritt verursacht hat:** Der Scope-Vertrag nannte „ein
Composable" und fünf Dateien — gedacht war die reine Anzeige. Der zentrale Typ,
die Proxy-Liste und die zweite Testgrenze kamen beim Bauen dazu, jede einzeln
plausibel. Genau dafür ist der Checkpoint da, und ich habe ihn nicht gezogen.

**Prozesschronik gekürzt:** `seit T-43` aus der Präfixliste und dem
Testkopf, „daran ist Runde 1 gescheitert" aus zwei Testkommentaren. Im Code
steht die geltende Invariante, die Chronik im Ticket.

Regression am Stand `f8e0fda`, jeder Lauf beim Namen: `pytest` 947, Contract
295, Plugin-Beispiel 45, `vitest` 291 (49 Dateien), `vue-tsc` sauber, Build ✓,
Ruff sauber, `git diff --check` sauber. Die beiden Smokes sind erneut **nicht**
gelaufen — ihr Gegenstand ist die Kettenbildung im Backend, und dort hat sich
nichts geändert.

Ab jetzt keine weitere Produktdatei.
