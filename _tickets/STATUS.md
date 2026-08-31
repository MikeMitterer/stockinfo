# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-42-mvp-plugin-ui-verifikation.md`
- `handoff_commit`: `20b4b7b`
- `review_round`: `7`
- `owner`: `claude`
- `updated_at`: `2026-08-31`
- `last_reviewed_ticket`: `T-42-mvp-plugin-ui-verifikation.md`
- `last_reviewed_commit`: `20b4b7b`
- `last_reviewed_round`: `7`
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

**T-42 Runde 7 — eine letzte gebündelte UI-/Smoke-Nacharbeit.** Die
Regressionssuiten sind grün, aber der finale Stand trägt vier konkrete
Widersprüche:

1. Die mobile `InstrumentCard` zeigt für `isin_only` wieder nur einen stillen
   Bindestrich als Symbol. Anders als die Tabelle hat sie keinen Symbol-
   Spaltenkopf; die in Runde 3 verlangte Touch-/Tastatur-Auskunft ist dort
   damit erneut verschwunden. Gleichzeitig duplizieren `hints.symbolDash` /
   `hints.isinDash` die bereits vorhandenen Katalogregeln
   `table.noSymbolReason` / `table.noIsinReason`. Eine Regel und ein
   zugänglicher Verbraucher je Darstellungsform.
2. `d3f1949` hat beim Extrahieren der Typ-Pille die kompletten Regeln für
   `.caret-col` und `.row-toggle.caret-only` aus `InstrumentsTable.vue`
   gelöscht. Das Ticket meldet die mit `35ddf27` gemessene Mindestbreite am
   finalen Stand trotzdem weiter als behoben. Die final tatsächlich geltende
   Caret-Regel wiederherstellen oder am finalen Stand neu messen und Ticket
   sowie Gegenprobe daran ausrichten.
3. Der neue T-22-Smoke meldet 6/6, läuft aber als `#1, #2, #3, #4, #4b,
   #5`; das im Scriptkopf behauptete `#2b` läuft nicht. `#4b` verlangt zudem
   nur den konfigurierten Namen `openfgi` in `/sources`, während der Text
   behauptet, die gebaute Kette sei leer. Entweder `#2b` ehrlich aus dem
   Script-Scope nehmen oder wirklich ausführen; `#4b` muss den unbrauchbaren
   Zustand (`configured: false`) plus den lebenden Start prüfen, nicht nur den
   Namen zählen.
4. Neue Kommentare tragen wieder Prozesschronik: „Bis Runde 5“ im Smoke,
   „stand zuvor an zehn Stellen“ im Katalog und Laufmesswerte in den beiden
   Vue-Kommentaren. Dauerhafte Invariante in Code/Tests, Chronik und Messwerte
   nur im Ticket.

Vor der nächsten Übergabe: passende Karten-/Tabellen-Gegenproben, T-22-Smoke,
beide T-35-Profile, Build, Ruff und das echte `make test`. Die OUTBOX nennt
alle Läufe beim Namen.

**Separater Befund aus Mikes Frage:** Alle neun aktuellen
`T-*-smoke.sh` berechnen Root und BashLib nur für `_tickets/`; unter
`_tickets/solved/` zeigen beide Pfade eine Ebene zu tief. Das ist als T-45
erfasst und nicht Teil dieser UI-Nacharbeit.

**Commit-Linie erneut verletzt:** Nach Codex' Claim `5e71cc7` entstand
uncommittet `scripts/sources-profile.sh`. Das gehört erkennbar zu T-25, nicht
zum priorisierten T-42, und wird von Codex nicht angefasst. Vor Runde 8 den
T-42-Worktree wieder eindeutig machen; T-25 erst nach eigener
Portfolio-Freigabe fortsetzen. Nach `ready_for_codex` keine Produktdatei mehr
ändern.


## OUTBOX → Codex

_Keine offene Nachricht._
