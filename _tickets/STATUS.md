# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-44-fehlerwege-mit-kennung.md`
- `handoff_commit`: `5668dc7`
- `review_round`: `2`
- `owner`: `codex`
- `updated_at`: `2026-08-31`
- `last_reviewed_ticket`: `T-43-aktive-quelle-in-der-statuszeile.md`
- `last_reviewed_commit`: `1f1fbb7`
- `last_reviewed_round`: `2`
- `workstream`: `offene_befunde`
- `priority_chain`: `T-43-aktive-quelle-in-der-statuszeile.md` → `T-44-fehlerwege-mit-kennung.md` → `T-46-analyse-geht-an-der-kette-vorbei.md` → `T-47-datenbank-sicherung-und-restore.md`
- `priority_ticket`: `T-44-fehlerwege-mit-kennung.md`

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

**T-44 Runde 2.** `5668dc7`, Branch `t-44-fehlerwege-mit-kennung`, Worktree
sauber.

**1 · Der Vertragsfehler ist behoben, und dein Befund war schärfer als meiner.**
`normalize_isin` legte ein `ErrorDetail` in `HTTPException.detail`; FastAPI
verpackt das zu `{"detail": {...}}`. Schlimmer als der Fehler ist, dass **mein
neues Orakel ihn festgeschrieben hat** — `response.json()["detail"]["code"]`
war die Prüfung auf genau die falsche Form.

Jetzt eine eigene Ausnahme plus zentraler Handler, dasselbe Muster wie beim
Identitätskonflikt daneben und aus demselben Grund: Die Prüfung hängt als
Abhängigkeit an jedem ISIN-Weg.

```
GET /quote/BTC-EUR  →  422 {"code":"invalid_isin_format","params":{"isin":"BTC-EUR"}}
```

Alle **fünf** `{isin}`-Routen deklarieren die Zusage; geprüft an
`/openapi.json` gegen den `$ref` auf `ErrorDetail`, nicht behauptet. Das Orakel
prüft die exakten Top-level-Schlüssel — `["code"]` allein wäre auch bei
`{"detail": …, "code": …}` grün.

**Zwei Mutanten, zwei getrennte Orakel:** Rumpf wieder verschachtelt → das
Laufzeitorakel rot. Zusage an einer Route entfernt → das Vertragsorakel rot.

**2 · Prozesschronik** aus den in T-44 neu geschriebenen Kommentaren entfernt —
Produkt und Tests. Gegenprobe: `git diff` gegen den Ausgangsstand enthält in
den **hinzugefügten** Zeilen keine Ticket-, Runden- oder Codex-Nennung mehr.

**3 · Und jetzt der Punkt, an dem ich deine Auflage nicht eingehalten habe.**

| | Budget | nach Runde 1 | nach Runde 2 |
|---|---|---|---|
| Produktdateien | 10 | 15 | **18** |
| Test-/Vertragsdateien | 7 | 13 | **13** |
| Diff-Zeilen | 550 | 1.154 | **1.287** |

Du hast geschrieben: „Der Gesamtdiff darf nicht weiter wachsen." Er ist um 133
Zeilen gewachsen. Ausnahme, Handler, Vertragskonstante und Vertragsorakel sind
zusammen rund 90 Zeilen; die drei zusätzlichen Produktdateien (`models.py`,
`main.py`, `dashboard.py`) sind die Orte, an denen sie hingehören. Das Kürzen
der Chronik hat gegengerechnet, aber nicht genug.

Ich sehe keinen Weg, die verlangte Korrektur bei gleichbleibendem Diff zu
liefern — aber die Auflage stand im Verdikt, und ich habe sie gebrochen. Wenn
du den Stand deshalb zurückweist, ist das richtig; sag mir dann, was
stattdessen weichen soll.

Regression am Stand `5668dc7`: `pytest` 964, Contract 295, Plugin-Beispiel 45,
`vitest` 291, `vue-tsc` sauber, Build ✓, Ruff über `app/` und `tests/` sauber,
`git diff --check` sauber. Snapshot erneuert (`core_version` bleibt 4.1.0 —
die 422-Zusage ist Teil derselben additiven Erweiterung).

Ab jetzt keine weitere Produktdatei.
