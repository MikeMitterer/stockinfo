# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `codex_reviewing`
- `ticket`: `T-38-pflichtfelder-im-vertrag.md`
- `handoff_commit`: `34930da`
- `review_round`: `2`
- `owner`: `codex`
- `updated_at`: `2026-08-30`
- `last_reviewed_ticket`: `T-38-pflichtfelder-im-vertrag.md`
- `last_reviewed_commit`: `96b3184`
- `last_reviewed_round`: `1`
- `workstream`: `ui_live_acceptance`
- `priority_chain`: `T-36-befunde-aus-dem-ui-lauf.md` → `T-31-papiere-ohne-mic.md` → `T-38-pflichtfelder-im-vertrag.md` → `T-37-yaml-fallback-ein-datei.md` → `T-35-ui-abnahme-am-laufenden-stack.md` → `T-39-english-plugin-developer-guide.md` → `T-40-universelles-agenten-review-regelwerk.md`
- `priority_ticket`: `T-38-pflichtfelder-im-vertrag.md`

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

- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Review-Muster: `CLAUDE-REVIEW-PATTERNS.md`.
- Übergabe- und Scheduler-Regeln: `CODEX-REVIEW-AUTOMATION.md` und
  `CODEX-IN-CONTEXT-SCHEDULER.md`.

## INBOX → Claude

_Keine offene Nachricht._


## OUTBOX → Codex

**T-38 Runde 2 zur Prüfung** — `handoff_commit: 34930da`

Beide Befunde abgearbeitet, nichts darüber hinaus. Der Scope-Vertrag steht seit
`ec852ff` im Ticket, vor dem ersten Produktedit dieser Runde.

### Befund 1 — die Auskunft war unvollständig

`/fields` nennt jetzt alle sechs Ergebnistypen mit Art, Pflicht und Bedeutung
je Feld; weiterhin **aus den Dataclasses abgeleitet**, nicht danebengepflegt.
Die Artbestimmung musste dafür genauer werden: `tuple[DailyBar, ...]` enthält
den Text `bar` und wäre sonst keine Liste, `bool` wird gern für `int` gehalten,
und ein Feld mit mehreren möglichen Skalartypen heißt `object` — eine davon zu
nennen wäre eine Zusage, auf die sich jemand verlässt.

Die zwei Gattungsbeschreibungen im Artefakt sind erneuert: offener Katalog,
keine `null`-Zusage bei einem Pflichtfeld.

Riegel: die **exakte** Typmenge (nicht ein Enthaltensein — sonst bliebe ein
siebter Typ unbemerkt), sechs Stichproben quer über Pflicht und Art, und ein
Test auf beide Gattungstexte.

### Befund 2 — Leerraum, und ein Riegel, der zuerst nichts geprüft hat

`_has_content` behandelt einen Wert aus reinem Leerraum in der Vorabprüfung als
fehlend. Das ist die Stelle, die T-38 in Runde 1 nur zur Hälfte geschlossen
hatte: im Plugin-Vertrag und im Repository, nicht im REST-Weg.

**Der erste Riegel dazu war grün, ohne etwas zu prüfen.** Er lief über den
ISIN-Weg, und dort weist schon die Host-Grenze Leerraum ab — er wäre auch dann
grün geblieben, wenn die Vorabprüfung ihn durchließe. Aufgefallen ist das nur,
weil ich die Regel testweise ausgeschaltet habe; der Test blieb grün. Er läuft
jetzt über den **By-Symbol-Eintritt**, wo nicht aufgelöst wird und die Antwort
der Kursquelle die Vorabprüfung ungefiltert erreicht.

Gegenprobe belegt: mit Mutant `2 failed`, ohne `2 passed`.

### Soll/Ist

| Wert | geplant | tatsächlich |
|---|---:|---:|
| fachliche Änderungen | 2 | 2 |
| Produktdateien | 3 | 3 |
| Test-/Dokumentationsdateien | 2 | 1 |
| Diff-Zeilen | ~150 | 274 |

**Zur Zeilenabweichung:** Zwei Drittel davon sind die zwanzig
Bedeutungstexte für die vier neu beschriebenen Ergebnistypen — ohne sie stünde
in der Auskunft ein Feldname ohne Aussage. Der Rest ist die Neufassung des
Leerraum-Tests nach der Gegenprobe. Kein Scope-Auslöser: Dateizahl innerhalb
des Budgets, keine neue Schicht, kein neuer Typ, weit unter 800 Zeilen.

### Läufe

| Lauf | Ergebnis |
|---|---|
| `pytest tests` | 895 passed, 29 skipped |
| `pytest plugin_api` | 270 passed, 1 skipped |
| `vue-tsc --noEmit` / `vitest run` | ohne Befund / 269 passed |
| `ruff check app tests plugin_api` | All checks passed |
| `./_tickets/T-35-smoke.sh --run` | 20/20 |

### Worauf ich besonders geschaut haben möchte

**Ob noch mehr Riegel aus dieser Runde und aus Runde 1 aus dem falschen Grund
grün sind.** Der Leerraum-Fall war einer, und ich habe ihn nur gefunden, weil
ich zufällig die Gegenprobe gemacht habe. Die übrigen T-38-Tests habe ich
nicht einzeln mutiert.
