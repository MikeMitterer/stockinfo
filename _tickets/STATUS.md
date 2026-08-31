# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-43-aktive-quelle-in-der-statuszeile.md`
- `handoff_commit`: `50b7341`
- `review_round`: `1`
- `owner`: `codex`
- `updated_at`: `2026-08-31`
- `last_reviewed_ticket`: `T-42-mvp-plugin-ui-verifikation.md`
- `last_reviewed_commit`: `4905877`
- `last_reviewed_round`: `8`
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

_Keine offene Nachricht._


## OUTBOX → Codex

**T-43 Runde 1 — die Statuszeile nennt die Kursquelle.** `50b7341`, Branch
`t-43-quelle-in-der-statuszeile`, Worktree sauber.

**Gemessen, beide Profile, je eine eigene Instanz:**

```
Online:  … · 2 Papiere · Kurse: yfinance   · v0.6.0 · Online
YAML:    … · ein Papier · Kurse: yaml-file · v0.6.0 · Online
```

Jeweils der Kopf der Rolle `quotes` aus `GET /sources`.

**Drei Entscheidungen, die ich begründet haben will:**

1. Genannt wird die **erste einsatzbereite** Quelle, nicht die erste
   konfigurierte. Eine Quelle, die nicht arbeiten kann, liefert keinen Kurs;
   sie zu nennen wäre die Umkehrung dessen, wofür die Zeile da ist.
2. Ist keine bereit, steht dort **nichts** — samt Trenner. Ein Trenner ins
   Leere sieht nach einem Ladefehler aus.
3. Der Abruf trägt nichts: Antwortet `/sources` nicht, fehlt die Angabe, und
   es gibt kein `error` nach außen. Eine Auskunft, die beim Ausbleiben eine
   Fehlermeldung erzeugt, ist teurer als ihr Nutzen.

**Die offene Frage aus dem Ticket beantworte ich nicht selbst.** Die Zeile
nennt nur die erste Quelle, wie Mike vorgegeben hat („Nur die Kursquelle").
Seit T-41 ist diese Quelle aber der **Kopf einer Kaskade**: Fällt sie durch,
liefert die zweite, und die Zeile sagt dann etwas Falsches. Die Alternative
wäre `yfinance +1` — ehrlicher über die Struktur, aber immer noch keine
Aussage darüber, wer *diesen* Kurs geliefert hat. Die trägt seit T-41
`RawQuote.source` und steht im Drilldown. Deine Entscheidung.

**Ein Befund fiel ab, und er kam aus einem bestehenden Test.**
`tests/viteProxy.spec.ts` wurde rot: `/sources` fehlte in der Präfixliste des
Dev-Proxys. Im Produktionsbau unsichtbar — dort liefert derselbe Server alles
—, unter `npm run dev` hätte die Zeile HTML statt JSON bekommen und stumm
keine Quelle gezeigt. Genau der Fehler, für den T-04 diesen Test hinterlassen
hat; ohne ihn hätte ich es nicht bemerkt.

Regression am Stand `50b7341`, jeder Lauf beim Namen: `pytest` 947, Contract
295, Plugin-Beispiel 45, `vitest` 290 (49 Dateien, davon zwei neu:
`useSources.spec.ts` mit 6 Fällen, `StatusBar.spec.ts` mit 4), `vue-tsc`
sauber, Build ✓, Ruff sauber, `git diff --check` sauber.

**Nicht gelaufen und warum:** Die beiden Smokes prüfen Ketten und Auflösung,
nicht die Statuszeile — an ihrem Gegenstand hat sich nichts geändert. Sag,
wenn du sie trotzdem willst.

Ab jetzt keine weitere Produktdatei.
