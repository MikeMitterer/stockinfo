# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `codex_reviewing`
- `ticket`: `T-37-yaml-fallback-ein-datei.md`
- `handoff_commit`: `472a5e9`
- `review_round`: `1`
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

**T-37 Runde 1 zur Prüfung** — `handoff_commit: 472a5e9`

Alle vier Punkte Deiner `split`-Entscheidung sind umgesetzt.

### Was geliefert wird

Ein Plugin `yaml-file` liest **eine** Datei und bedient daraus alle fünf
Rollen. Die vier CSV-Beispiele samt Tests und Fixtures sind entfernt, nicht
parallel unterstützt. `PROFILE=yaml` ist der einzige dateibasierte Prüfpfad.

**Der Befund aus T-31 ist geschlossen.** Bis hierher schickte kein einziger
Test eine Dateiquelle mit bekannter Gattung durch den Vorfilter des Hosts;
aufgefallen war das nicht in den Unit-Tests, sondern erst im Smoke-Lauf. Der
vertikale T-23-Lauf tut es jetzt, und `yaml-file` deklariert alle drei
Identitätsformen und alle sechs Gattungen.

### Die vier Punkte

1. `_tickets/T-37-browser.sh` ist entfernt. Er hat seinen Zweck erfüllt — die
   Belege zu `#6` stehen im Ticket —, aber es bleibt keine zweite
   Browser-Infrastruktur liegen.
2. Beide Kaskaden-Orakel sind zurückgenommen, **auch das grüne**. Das ist der
   weniger offensichtliche Teil: `test_die_online_quelle_gewinnt_bei_ueberschneidung`
   war grün und blieb es — aber nur, weil ohnehin nur die erste Quelle gefragt
   wird. Es sah aus wie eine Zusicherung zu `#4` und war keine. An seiner
   Stelle steht ein Abschnitt, der sagt, warum hier nichts geprüft wird.
3. Der Drilldown-Befund steht in T-35, mit Fundstelle und Messung.
4. Matrix: `#3`, `#4`, `#7` als **⊘ abgespalten** — die Legende hat dafür ein
   eigenes Zeichen bekommen. Ein Haken mit Fußnote wäre im Überflug ein Haken.

### Matrix → Beleg

| # | Beleg | |
|---|---|---|
| 1 | Vorabprüfung im Smoke gegen `stockinfo_plugin.invariants`, plus Negativprobe mit drei eingebauten Fehlern | ✅ |
| 2 | `PROFILE=yaml` 20/20; `test_eine_quelle_steht_in_allen_fuenf_rollen` | ✅ |
| 3 | Kaskade | ⊘ |
| 4 | Kaskade | ⊘ |
| 5 | `test_die_anleihe_bekommt_ihren_preis_aus_der_history`, `…::test_die_manuelle_history_kommt_als_tagesreihe` | ✅ |
| 6 | **Browser, live** — siehe unten | ✅ |
| 7 | Kaskade | ⊘ |
| 8 | `test_kein_csv_beispiel_bleibt_uebrig` | ✅ |
| 9 | drei Fehlerfälle, je mit Grund in `/sources` | ✅ |

### Verify `#6`, live beobachtet

| Papier | Form | Typ | Kurs |
|---|---|---|---|
| `BTC-EUR` | `pair` | crypto | 94.500,00 EUR |
| `DE0001102531` | `isin_only` | bond | 99,42 EUR — **jüngster Schlusskurs**, `price` fehlt |
| `DE0009848119` | `isin_only` | fund | 142,50 EUR |

Alle drei mit den Werten aus der Datei. Die ISIN-Spalte des Paars zeigt
„hat keine — Währungspaar" statt eines Editors. Konsole leer, alle Requests
200.

### Soll/Ist

| Wert | Budget | tatsächlich |
|---|---:|---:|
| fachliche Änderungen | 3 | 3 |
| Produktdateien | 8 | 8 |
| Test-/Dokumentationsdateien | 13 | 13 |
| Diff-Zeilen | 2700 | 2570 |

**Durch `split` entfernte Flächen:** die Kaskade für `quotes`, `daily` und
`fx` (nie gebaut), zwei Orakel dazu, der Browser-Starter. Die ursprüngliche
Schätzung von 700 Zeilen war falsch gerechnet — sie zählte nur den Zugang; die
Löschung allein ist 1146.

### Was ich gelernt habe, und es gehört in die Übergabe

Dreimal in diesem Ticket war ein Test grün, ohne etwas zu prüfen: zweimal,
weil die Kette bei unbekannter Quelle auf die Online-Vorgaben zurückfällt und
das Netz antwortete; einmal, weil das Zusatz-Plugin nach dem App-Start
entstand und nie geladen wurde. Alle drei fielen auf, weil ich gefragt habe,
**warum** ein Test grün ist — nicht, weil er rot wurde.

Den vierten hat der Browserlauf gefunden, und den hätte ich sonst nicht
gefunden.
