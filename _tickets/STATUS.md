# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-42-mvp-plugin-ui-verifikation.md`
- `handoff_commit`: `20b4b7b`
- `review_round`: `7`
- `owner`: `codex`
- `updated_at`: `2026-08-31`
- `last_reviewed_ticket`: `T-42-mvp-plugin-ui-verifikation.md`
- `last_reviewed_commit`: `f75df2d`
- `last_reviewed_round`: `3`
- `workstream`: `ui_live_acceptance`
- `priority_chain`: `T-36-befunde-aus-dem-ui-lauf.md` → `T-31-papiere-ohne-mic.md` → `T-38-pflichtfelder-im-vertrag.md` → `T-37-yaml-fallback-ein-datei.md` → `T-41-role-kaskaden-fuer-yaml-fallback.md` → `T-35-ui-abnahme-am-laufenden-stack.md` → `T-39-english-plugin-developer-guide.md` → `T-42-mvp-plugin-ui-verifikation.md`
- `priority_ticket`: `T-42-mvp-plugin-ui-verifikation.md`

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

**T-42 Runde 7 — der Anzeigeteil ist zu Ende, und der Regressionslauf hat
etwas Älteres aufgedeckt.** `20b4b7b`, Branch `t-42-mvp-ui-verifikation`,
Worktree sauber.

**Der Hinweis sitzt jetzt im Spaltenkopf**, einmal je Spalte statt in jeder
Zeile — Mikes Einwand war, dass ein Tooltip, den man zum zwanzigsten Mal
wegklickt, keine Hilfe mehr ist. Damit ist auch der Naive-UI-Fall vom Tisch:
Kein Tooltip liegt mehr um einen Umschalter, also verschluckt auch keiner mehr
einen Klick. Dazu drei Nachzüge aus demselben Blick: **ein** Platzhalter aus
`common.noValue` statt zehn fester Zeichen in vier Dateien, ein Bindestrich
statt eines Geviertstrichs (auch im Legendentext), und der Platzhalter in
derselben Schrift wie seine Nachbarn — gemessen 6,3 gegen 8,2 px, jetzt
viermal 8,2.

**Der Befund, auf den ich dich eigentlich stoßen will:** Der T-22-Smoke war
rot, Check `#4`. Nicht durch meine UI-Arbeit — der Diff seit `be8f10d` fasst
nur `dashboard/` und `_tickets/` an. Der Check las die Tippfehler-Meldung aus
dem **Server-Log**, und dort steht sie seit Runde 5 nicht mehr: Ein unbekannter
Name bricht den Kettenbau nicht mehr ab, sondern kostet nur seine eigene
Quelle. Der Grund samt den bekannten Namen steht seither in `/sources` — die
Zusage ist gehalten, nur an anderer Stelle. Der Check liest sie jetzt von dort,
`#4b` hält die neue Zusage fest (der Start überlebt den Tippfehler). 6/6.

**Zwei Kommentare in `app/sources_registry.py`** beschrieben weiter das alte
Verhalten. Sie waren die letzte Stelle, an der die abgelöste Regel noch stand.

**Was ich davon selbst mitnehme:** Ein Smoke, den man nicht laufen lässt,
altert lautlos mit. Rot wurde er nicht durch eine Regression, sondern durch
eine bewusste Änderung — und in der Zwischenzeit hätte er eine echte
Regression an derselben Stelle nicht mehr gemeldet. Die Übergaben der letzten
Runden nannten „beide Smokes"; gemeint war T-35 in zwei Profilen. Wenn du eine
Zeile in CLAUDE-REVIEW-PATTERNS.md dafür für richtig hältst, schreib sie —
mein eigener Vorschlag wäre: *Der Regressionsblock nennt die Smokes beim
Namen, nicht ihre Anzahl.*

Regression am Stand `20b4b7b`: `make test` 947 + 295 + 45 + 278, `vue-tsc`
sauber, Build ✓, Ruff sauber, T-35-Smoke Profil O 20/20, T-22-Smoke 6/6,
`git diff --check` sauber.

Ab jetzt keine weitere Produktdatei.
