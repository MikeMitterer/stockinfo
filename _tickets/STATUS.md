# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `scope_checkpoint`
- `ticket`: `T-37-yaml-fallback-ein-datei.md`
- `handoff_commit`: `cc688a8`
- `review_round`: `0`
- `owner`: `codex`
- `updated_at`: `2026-08-30`
- `last_reviewed_ticket`: `T-38-pflichtfelder-im-vertrag.md`
- `last_reviewed_commit`: `1a1466a`
- `last_reviewed_round`: `2`
- `workstream`: `ui_live_acceptance`
- `priority_chain`: `T-36-befunde-aus-dem-ui-lauf.md` → `T-31-papiere-ohne-mic.md` → `T-38-pflichtfelder-im-vertrag.md` → `T-37-yaml-fallback-ein-datei.md` → `T-35-ui-abnahme-am-laufenden-stack.md` → `T-39-english-plugin-developer-guide.md` → `T-40-universelles-agenten-review-regelwerk.md`
- `priority_ticket`: `T-37-yaml-fallback-ein-datei.md`

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

**T-37 · Scope-Checkpoint 2** — `handoff_commit: cc688a8`

Auslöser: **eine neue Abstraktion**, die nicht im Vertrag steht. Kein
Größenproblem — das Budget ist eingehalten.

### Der Befund

Der Browserlauf zu Verify `#7` zeigt: Im Online-Profil bleibt die Anleihe ohne
Kurs. `502 quote_unavailable`, obwohl `yaml-file` in `quotes` an zweiter Stelle
steht und die Datei einen gepflegten Schlusskurs führt.

Die Ursache steht als Absicht im Code (`app/container.py`):

> **Eine, nicht eine Kette:** Für Kurse, Tagesreihen und Wechselkurse gibt es
> keinen Composite, und einen zu erfinden hieße, eine Rangfolge zu bauen, die
> niemand angefordert hat.

`_first(role)` nimmt für `quotes`, `daily` und `fx` die **erste** einsatzbereite
Quelle. `quotes: [yfinance, yaml-file]` heißt damit: yfinance, Punkt.

**Inzwischen hat sie jemand angefordert.** T-37 verlangt sie viermal — Verify
`#3` („dasselbe `yaml-file` jeweils zuletzt"), `#4` („nur bei fehlendem
Ergebnis wird YAML gefragt"), `#7` („die Anleihe ohne Online-Kurs über YAML")
und Mikes Entscheidung 6 aus T-31 („hängt das YAML-Plugin ans **Ende** seiner
Kette").

Das ist eine Kaskade für drei Rollen — die vierte Abstraktion dieser Art neben
`CompositeResolver` und der Metadatenkaskade. Sie steht nicht im Scope-Vertrag,
und Deine `continue`-Entscheidung schloss weitere Produktflächen aus. Deshalb
halte ich an.

### Belegt, nicht behauptet

`tests/test_yaml_profile.py::test_die_datei_antwortet_wenn_die_quelle_davor_nichts_hat`
ist **absichtlich rot** und sagt dasselbe wie der Browser.

**Mein Orakel zu Matrix `#4` prüfte bisher nur die eine Hälfte** — dass eine
vorgelagerte Quelle gewinnt. Ein Rückfall, der nie gefragt wird, gewinnt
ebenfalls nie; beide Fälle waren grün. Gefunden hat die Lücke der Lauf mit
Augen, nicht die Suite. Das ist der dritte Fall dieser Art in diesem Ticket.

### Was fertig ist

| Verify | Stand |
|---|---|
| `#1` Beispieldatei + Vorabprüfung | ✅ |
| `#2` `PROFILE=yaml` | ✅ 20/20 |
| `#3` `PROFILE=online` | ✅ 20/20 — aber ohne Datei-Rückfall, siehe oben |
| `#4` Überschneidung | ◑ die eine Hälfte grün, die andere rot |
| `#5` Persistenz, Preis-Rückfall | ✅ |
| `#6` Browser, YAML-Profil | ✅ **live bestätigt**, siehe unten |
| `#7` Browser, Online-Profil | ⚠️ ETF und Überschneidung stimmen, Anleihe fällt durch |
| `#8` Inventur | ✅ |
| `#9` Fehlerfälle | ✅ |

### Verify `#6`, live beobachtet

Drei Formen über die Oberfläche angelegt, alle mit den Werten aus der Datei:

| Papier | Form | Typ | Kurs |
|---|---|---|---|
| `BTC-EUR` | `pair` | crypto | 94.500,00 EUR |
| `DE0001102531` | `isin_only` | bond | 99,42 EUR — **jüngster Schlusskurs**, `price` fehlt |
| `DE0009848119` | `isin_only` | fund | 142,50 EUR |

Die ISIN-Spalte des Paars zeigt „hat keine — Währungspaar" statt eines
Editors. Konsole leer, alle Requests 200.

### Ein zweiter, kleinerer Befund aus demselben Lauf

Der Drilldown der **Anleihe** sagt: *„Kennzahlen werden nur für ETFs geholt —
dieses Papier ist **eine Aktie**."* Sie ist eine `bond`. Der Text
(`dashboard/src/i18n/de.ts:350`) kennt nur ETF und Aktie und ist seit T-31/T-38
für `bond`, `crypto` und `fund` schlicht falsch. Eine Zeile, aber wieder eine
neue Fläche — deshalb hier gemeldet statt gefixt.

### Umfang gegen das erweiterte Budget

| Wert | erlaubt | tatsächlich |
|---|---:|---:|
| Produktdateien | 8 | 8 |
| Test-/Dokudateien | 13 | 14 |
| Diff-Zeilen | 2700 | ~2600 |

Die vierzehnte Datei ist `_tickets/T-37-browser.sh` — der Starter für die
Browser-Abnahme, den Verify `#6`/`#7` verlangen. Ohne ihn ließe sich der Lauf
nicht wiederholen.

### Die Frage an Dich

`continue` (Kaskade für die drei Rollen bauen), `split` (eigenes Ticket, T-37
schließt ohne Verify `#7`) oder `mike` (die Entscheidung von damals wird
umgestoßen — sie war ausdrücklich begründet)?
