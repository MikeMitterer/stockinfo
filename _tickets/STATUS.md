# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-41-role-kaskaden-fuer-yaml-fallback.md`
- `handoff_commit`: `115ac6c`
- `review_round`: `1`
- `owner`: `codex`
- `updated_at`: `2026-08-30`
- `last_reviewed_ticket`: `T-37-yaml-fallback-ein-datei.md`
- `last_reviewed_commit`: `d4e01b3`
- `last_reviewed_round`: `6`
- `workstream`: `ui_live_acceptance`
- `priority_chain`: `T-36-befunde-aus-dem-ui-lauf.md` → `T-31-papiere-ohne-mic.md` → `T-38-pflichtfelder-im-vertrag.md` → `T-37-yaml-fallback-ein-datei.md` → `T-41-role-kaskaden-fuer-yaml-fallback.md` → `T-35-ui-abnahme-am-laufenden-stack.md` → `T-39-english-plugin-developer-guide.md` → `T-40-universelles-agenten-review-regelwerk.md`
- `priority_ticket`: `T-41-role-kaskaden-fuer-yaml-fallback.md`

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

**T-41 Runde 1 — die drei Rollen-Kaskaden sind verdrahtet.** `115ac6c`,
Branch `t-41-role-kaskaden`, Worktree sauber.

**Zuerst der Befund gegen mich selbst: das Scope-Budget ist überschritten.**
Der Vertrag im Ticket nennt 5 Test-/Dokudateien und 650 Diff-Zeilen gesamt.
Tatsächlich sind es 8 und 1131 (605 committed in Task 1–2, 526 in Task 3).
Die Produktseite hält ihre Grenze: 4 Dateien, 230 Zeilen.

Ich habe das erst nach dem letzten Commit gemessen, statt beim Auslöser. Das
ist die Regelverletzung, nicht die Zahl — der Riegel verlangt den Checkpoint
**vor** dem Überschreiten. Der Aufwuchs steckt in Tests und Docstrings
(`test_composite_market.py` 234, `test_yaml_profile.py` 245); keine neue
Abstraktion, kein neuer Endpunkt, keine neue Konfiguration. Ob das so bleibt
oder zurückgeschnitten wird, entscheidest du: `continue`, `reduce`, `split`
oder `mike`.

Was in den drei Commits steht:

- `35979d8` — `CompositeQuoteProvider` und `CompositeDailyCloseProvider`. Der
  Unterschied, an dem alles hängt: `[]` ist bei `daily` eine Antwort und
  beendet die Kette, `None` fällt weiter. Der Adapter übersetzt `NotFound`
  jetzt zu `None` statt zu `[]`.
- `6b734cb` — `CachedFxService` nimmt eine Folge und merkt sich den
  **tatsächlichen** Lieferanten in einer lokalen Variablen; kein
  „letzte Quelle"-Zustand.
- `115ac6c` — `_first` weicht `_market_chain`; die vollständige Kette geht an
  beide Composites und an den FX-Dienst. Die leere Kette bleibt Startfehler.

Geprüft wurde nicht am grünen Lauf: Mit `return sources[:1]` fallen genau die
vier neuen Kaskadenorakel um und sonst keines. Der Browserlauf im
Online-Profil steht mit Werten im Ticket — `BTC-EUR` 68.095,81 aus yfinance
gegen 94.500,00 in der Datei, die Anleihe 99,42 aus der Datei, `/fx` 0,6204
aus yfinance gegen 0,6412 in der Datei.

Zwei Dinge, die ich beim Bauen gefunden habe und die nicht im Plan standen:

1. Die Testfixture leerte nur `get_cached_quote_service`. `get_fx_service`
   und `get_daily_history_service` trugen die Quellen des vorigen Tests
   weiter — mein `/fx`-Orakel war grün, weil es zufällig das erste seiner Art
   im Lauf war.
2. Mit `yaml-file` nur in den Marktrollen scheitert die Anleihe schon an der
   **Aufnahme**. Die Kaskade hilft beim Kurs erst, wenn das Papier aufgelöst
   wird; die Datei gehört also auch in `resolvers`. Steht jetzt in
   `docs/plugins.md` und `docs/sources.yaml.example`.

`make test` 944 + 295 + 269 grün, Ruff sauber, `PROFILE=yaml
./_tickets/T-35-smoke.sh --run` 20/20, `git diff --check` sauber.
