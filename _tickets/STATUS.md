# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `codex_reviewing`
- `ticket`: `T-42-mvp-plugin-ui-verifikation.md`
- `handoff_commit`: `f75df2d`
- `review_round`: `3`
- `owner`: `codex`
- `updated_at`: `2026-08-31`
- `last_reviewed_ticket`: `T-42-mvp-plugin-ui-verifikation.md`
- `last_reviewed_commit`: `fab3540`
- `last_reviewed_round`: `1`
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

**T-42 Phase B ist gelaufen — alle zwölf Fälle.** `f75df2d`, Branch
`t-42-mvp-ui-verifikation`, Worktree sauber. Werte, Gegenwerte und Belege
stehen im Ticket; `data/stockinfo.db` blieb unberührt (19. August).

Drei Profile: reines YAML, Online mit `yaml-file` zuletzt, und ein drittes
mit dem gepinnten `us-example`-Wheel. Der FX-Non-Hit kam wie von dir verlangt
deterministisch aus einem temporären lokalen `fx-miss`.

**Was der Lauf belegt** — je Kaskadenfall mit dem Gegenwert, ohne den nichts
bewiesen wäre:

* Überlappung: **127,49** online gegen **128,21** in der Datei — online
  gewinnt, und auch der Name ist der von OpenFIGI.
* Lücke: die Anleihe kommt mit 99,42 aus der Datei, weil online kein Kurs
  existiert.
* FX-Herkunft: `fx-miss` steht **vor** `yaml-file` und liefert `NotFound`;
  die Anzeige nennt `yaml-file`.
* Neustart: `pending: false`, `unchanged: 4` — kein Migrationszustand durch
  das Krypto-Papier.
* Fremdes Plugin: geladen und in beiden Rollen brauchbar; ohne Schlüssel
  `configured: false` **mit** lesbarem Grund, während die Kette weiterarbeitet.

**Sechs Anzeigebefunde** hat Mike im Lauf gesehen, alle behoben und gemessen
(`288c527`, `13d4652`, `35ddf27`): abgeschnittene Zeile (Überlauf 0 statt
122 px), ISIN-Platzhalter (214 → 116 px), Symbol = ISIN bei `isin_only`,
Typ-Auszeichnung für alle sechs Gattungen, Caret in eigener Spalte, und
zuletzt ein Caret, das unter ~1150 px auf 5×15 gestaucht wurde — `width` ist
in einer Tabelle ein Wunsch, `min-width` ist die Untergrenze.

Der Typ-Befund ist die **dritte Ausprägung desselben Musters an einem Tag**:
eine zweite Stelle, die eine getroffene Entscheidung nicht nachgezogen hat —
nach `_FIGI_TYPES` und dem Migrationswächter.

**Zwei Befunde habe ich gemessen und ausdrücklich nicht angefasst.** Mike
fragte, warum ein Kurs nicht geladen werden konnte:

```
GET /fx?base=CAD&quote=USD  →  502  {"detail":"Kein Wechselkurs für CAD/USD"}
```

Der Statuscode ist falsch — die Quelle wurde gefragt und hat geantwortet, dass
sie das Paar nicht führt; das ist `404`, nicht `502`. Und die Meldung ist
deutscher Fließtext statt einer Kennung, weshalb das Dashboard nur seine
eigene Kategorie zeigen kann. Ein Statuscode ist REST-Vertrag, also
checkpoint-pflichtig; derselbe Befund steht seit T-35 für `normalize_isin`
offen. Beide gehören in ein gemeinsames kleines Ticket — sag, ob du es
anlegst oder ich.

**Auf Mikes Nachfrage geprüft statt zugesichert:** null feste Texte in den
Vue-Templates, alle 44 Attributtexte über den Katalog, die Suche selbst
gegengeprüft.

Regression: Ruff sauber, 939 Backend (`-m "not integration"`), 295
plugin_api, 45 Beispiel, 274 Dashboard, beide Smokes 20/20, `git diff --check`
sauber.

**Die Human-Spalte ist unangetastet.** Nach deiner Freigabe geht dieselbe
Matrix an Mike.
