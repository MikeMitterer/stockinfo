# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `scope_checkpoint`
- `ticket`: `T-42-mvp-plugin-ui-verifikation.md`
- `handoff_commit`: `13d4652`
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

**T-42 · Scope-Checkpoint, diesmal vor dem Edit.** `13d4652`, Worktree sauber.

`continue` ist umgesetzt: Das Caret hat eine eigene Spalte (es ist ein
Umschalter, keine Kennung), und die Entstehungs- sowie Messchroniken sind aus
den Produktkommentaren raus — dort steht jetzt die Invariante, die Zahlen und
Ticketnummern stehen im Ticket. 274 Dashboard-Tests grün, `vue-tsc` sauber.

**Und hier ist der nächste Wunsch, der die Grenze reißt.** Mike möchte in der
Statuszeile sehen, welche Quelle gerade liefert. Festgelegt hat er:

```
StockInfo powered by MangoLila · 4 Papiere · Kurse: yaml-file
```

Also die erste einsatzbereite Quelle der Rolle `quotes`.

**Das ist keine Anzeigekorrektur, sondern eine neue Funktion**, und deshalb
frage ich vorher statt hinterher: Das Dashboard ruft `GET /sources`
**überhaupt nicht** ab — nachgesehen, es gibt keinen Composable und keinen
Aufruf. Nötig wären:

| Datei | Art |
|---|---|
| `composables/useSources.ts` | **neu** — Abruf und Auswahl der Kursquelle |
| `components/StatusBar.vue` | Anzeige |
| `components/AppDashboard.vue` | Verdrahtung |
| `i18n/de.ts`, `i18n/en.ts` | Beschriftung |
| `tests/…` | Composable- und Statuszeilentest |

Nach deiner eigenen Abgrenzung fällt „eine eigenständige größere Funktion"
nicht unter die Lockerung. Ich halte das für den Fall — ein neuer Endpunkt im
Frontend, der bisher nirgends gelesen wird.

**Zwei Fragen:**

1. Darf ich es in T-42 bauen, oder wird es ein eigenes Ticket? Für T-42 spricht,
   dass es genau die Auskunft ist, die dieser Lauf die ganze Zeit über
   `curl /sources` von Hand geholt hat — ein Benutzer hat sie nicht.
2. Falls ja: Reicht die erste einsatzbereite `quotes`-Quelle, oder soll die
   Zeile kenntlich machen, dass dahinter eine Kaskade steht (`yfinance +1`)?
   Mike hat die kurze Form gewählt; ich frage, weil du die Kaskade
   mitentworfen hast.

Der Lauf steht bis dahin. Offen sind weiterhin FX, Y4, das Online-Profil und
P1/P2.
