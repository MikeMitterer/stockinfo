# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `codex_reviewing`
- `ticket`: `T-31-papiere-ohne-mic.md`
- `handoff_commit`: `07048d8`
- `review_round`: `1`
- `owner`: `codex`
- `updated_at`: `2026-08-29`
- `last_reviewed_ticket`: `T-36-befunde-aus-dem-ui-lauf.md`
- `last_reviewed_commit`: `f257ee1`
- `last_reviewed_round`: `6`
- `workstream`: `ui_live_acceptance`
- `priority_chain`: `T-36-befunde-aus-dem-ui-lauf.md` → `T-31-papiere-ohne-mic.md` → `T-38-pflichtfelder-im-vertrag.md` → `T-37-csv-profil-gleiche-tests.md` → `T-35-ui-abnahme-am-laufenden-stack.md`
- `priority_ticket`: `T-31-papiere-ohne-mic.md`

Erlaubte Phasen: `claude_working` → `ready_for_codex` → `codex_reviewing` →
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

- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Review-Muster: `CLAUDE-REVIEW-PATTERNS.md`.
- Übergabe- und Scheduler-Regeln: `CODEX-REVIEW-AUTOMATION.md` und
  `CODEX-IN-CONTEXT-SCHEDULER.md`.

## INBOX → Claude

_Keine offene Nachricht._


## OUTBOX → Codex

### T-31 · Runde 1 · der Umbauschnitt, **vor** der Umsetzung

Commit `07048d8`. **Kein Produktcode** — geprüft werden soll der Entwurf,
nicht das Ergebnis. Mike hat das ausdrücklich so angeordnet: erst der Plan
durch dein Review, dann die Umsetzung. Der neue Abschnitt heißt „Der
Umbauschnitt" und steht in `T-31-papiere-ohne-mic.md` vor „Worum es geht".

**Der Befund, um den es mir geht.** Dieses Ticket beschreibt die Union an
`Resolved`. `QuoteRequest` und `DailyRequest` tragen die Identität aber
ebenfalls, heute als Pflichtfelder `ticker: str` und `mic: str`. Ein
`BTC-EUR` ließe sich damit **auflösen, aber nicht bepreisen**, und die
`isin_only`-Anleihe ebensowenig — also genau die beiden Gattungen, für die
das Ticket existiert. Matrix `#7` („die Kurswährung muss `quote_currency`
entsprechen") setzt es bereits voraus, spricht es aber nirgends aus. Mein
Schluss: `Identity` ersetzt `ticker`/`mic` in allen drei Typen. Wenn du das
anders siehst, ist es besser jetzt strittig als nach dem Umbau.

**Was ich ausdrücklich nicht tue.** Pflichtfelder, `GET /fields` und der
`core_version`-Major bleiben T-38; der YAML-Fallback bleibt T-37. Sie landen
im selben `API_VERSION`, weil zwischen den Kettengliedern kein Release
liegt — nicht, weil die Tickets verschmelzen. Die Reihenfolge der Kette
bleibt unangetastet.

**Drei Entscheidungen Mikes, heute getroffen und eingetragen:**

1. Die bestehende `data/stockinfo.db` wird **verworfen**, kein Umzugspfad —
   sechs Zeilen, Projekt in Entwicklung. Der Tabellen-Neuaufbau entfällt
   damit als Umzugsschritt, die `CHECK`-Klauseln nicht.
2. Der Smoke-Profilname wird `yaml` statt `csv` (Umsetzung in T-37).
3. **Beide Versionssprünge werden gemacht.** Mike hat gefragt, ob
   `API_VERSION = 2` in der Entwicklungsphase übertrieben sei — ein
   berechtigter Einwand, `plugin_api` steht ohnehin auf `0.2.0`. Gegenprobe:
   `Source.api_version` hat `API_VERSION` als Vorgabewert, die eingebauten
   Plugins erben den neuen Wert also ohne eine einzige Änderung. Der Sprung
   kostet eine Zeile und ist das einzige, was T-38 `#3` und `#7` prüfbar
   macht. Entschieden: bleibt.

**Woran ich dich besonders bitte zu sehen:**

* Der Vorgabewert `SUPPORTED_KINDS = {"listed"}` an `Source` — sagt er die
  Wahrheit über einen Autor, der nichts erklärt, oder ist er eine stille
  Annahme in der Sorte, die dieses Projekt regelmäßig teuer bezahlt?
* Die drei partiellen Unique-Indizes: Decken sie die Eindeutigkeit je Form
  wirklich ab, oder bleibt eine Form ohne Schutz?
* Die `CHECK`-Klausel für `pair` verbietet `isin`. Ist das zu streng — gibt
  es ein Paar mit ISIN, das damit unspeicherbar würde?
* Der Zuschnitt gegen T-38: Ist wirklich nichts darin, was ohne die
  Pflichtfelder nicht funktioniert?

**Zahlen:** keine — es gibt nichts zu messen. `git diff --check` sauber, der
Stand ist unverändert der freigegebene `f257ee1` plus zwei Dokumentcommits.
