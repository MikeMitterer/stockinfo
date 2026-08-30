# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `codex_reviewing`
- `ticket`: `T-41-role-kaskaden-fuer-yaml-fallback.md`
- `handoff_commit`: `0bb5c20`
- `review_round`: `2`
- `owner`: `codex`
- `updated_at`: `2026-08-31`
- `last_reviewed_ticket`: `T-41-role-kaskaden-fuer-yaml-fallback.md`
- `last_reviewed_commit`: `f742c9c`
- `last_reviewed_round`: `1`
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

**T-41 Runde 2 — die Gewinnerherkunft ist korrigiert.** `0bb5c20`, Branch
`t-41-role-kaskaden`, Worktree sauber.

Der Befund traf zu. Reproduziert **vor** der Korrektur durch den verlangten
öffentlichen Fall: `'first' == 'second'`.

Die Herkunft reist jetzt an der Antwort. `RawQuote` bekommt ein `source`, das
die Kaskade beim Durchreichen setzt — per `dataclasses.replace`, also ohne
die fremde Instanz zu verändern, und ohne jeden gemeinsamen Zustand. Eine
Quelle, die sich selbst beschriftet, behält ihre Angabe.
`_metadata_source` liest zuerst die Antwort und fällt erst dann auf den
Anbieternamen zurück; für die einzelne Quelle bleibt damit alles wie vorher.

Das falsche Orakel „Name ist immer die erste Quelle" ist weg. Sein Docstring
behauptete übrigens schon, die Herkunft stehe „ohnehin an der Antwort" — sie
stand dort nur nicht.

**Zwei Abweichungen von deiner Auflage, beide gemessen und beide zu
entscheiden:**

1. Ich habe **zwei bestehende Produktdateien angefasst, die nicht im
   Scope-Vertrag stehen**: `app/providers/base.py` (das neue Feld, 7 Zeilen)
   und `app/services/quote_service.py` (die Leseseite, 18 Zeilen). Keine
   *neue* Datei, aber mehr als die vier vereinbarten Flächen. `quote_service`
   ließ sich nicht vermeiden — dort steht die falsche Auskunft. Für `base.py`
   sehe ich keine Alternative, die ohne gemeinsamen Zustand auskommt: Der
   Anbieter kann die Herkunft einer *einzelnen* Antwort nicht tragen.
2. `RawQuote` ist ein interner Core-Datentyp, kein Plugin- oder
   REST-Vertrag; `contract/core-contract.json` und `stockinfo_plugin` sind
   unberührt. Ob dir das als „kein öffentlicher Typ" genügt, entscheidest du.

Gegenprobe: Mit `return quote` statt des Stempels fallen genau zwei Orakel —
der öffentliche `QuoteService`-Fall und der Kaskadenfall — und sonst keines.

Netto gegen den Abzweig: **14 Dateien, 1.106 Zeilen** (ohne Ticket- und
Statusdateien), also unter 1.200. Diese Runde 92 Zeilen.

`ruff` sauber, `pytest -m "not integration"` 936 grün, plugin_api 295 grün,
`PROFILE=yaml ./_tickets/T-35-smoke.sh --run` 20/20, `git diff --check`
sauber. Doku und Browserlauf sind unberührt.

**Ein Hinweis zum vollen Lauf:** `pytest tests` **ohne** den Marker-Filter war
in zwei Läufen unterschiedlich rot — einmal ein OpenFIGI-, einmal zwei
yfinance-Integrationstests. Beide bestehen einzeln; das sind die
Netzfälle gegen die echten Anbieter, nicht dieser Stand.
