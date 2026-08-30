# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-38-pflichtfelder-im-vertrag.md`
- `handoff_commit`: `96b3184`
- `review_round`: `1`
- `owner`: `claude`
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

**T-38 Runde 1 — zwei begrenzte Korrekturen gegen `96b3184`**

1. **Die Vertragsauskunft muss vollständig und widerspruchsfrei sein.**
   `/fields` liefert derzeit nur `resolved` und `quote`. Nenne dort alle sechs
   vorhandenen Plugin-Ergebnistypen (`Resolved`, `Quote`, `DailyBar`,
   `DailySeries`, `FxRate`, `Reading`) mit ihren Pflicht- und Optionalfeldern
   und sichere die exakte Menge plus repräsentative Felder im Test. Korrigiere
   außerdem die zwei veralteten Gattungsbeschreibungen in
   `contract/core-contract.json`: offener kanonischer Katalog `stock`, `etf`,
   `etc`, `fund`, `crypto`, `bond`; keine `null`-Zusage bei einem Pflichtfeld.
   Kein neuer Endpunkt, kein neues Modell, keine neue Abstraktion.
2. **Leerraum ist kein Pflichtwert.** Nur aus Leerzeichen bestehende Werte für
   `name` oder `type` dürfen den öffentlichen Quote-/REST-Weg nicht als
   erfolgreiche Antwort verlassen. Nutze einen vorhandenen gültigen
   Fallbackwert oder lehne strukturiert ab; ergänze einen direkten Test über
   den öffentlichen Eintrittspfad. Bleibe in den vorhandenen
   Precheck-/Modellgrenzen, ohne neuen Helper oder neue Abstraktion.

Akzeptierte Teile sind eingefroren; es gibt keine weiteren Befunde. Vor dem
nächsten Produkt-Edit den neuen Scope-Vertrag im Ticket ergänzen. T-38 wird
nicht rückwirkend um Kommentarbereinigung oder andere Architekturarbeit
erweitert.

Belege: 69 gezielte Tests bestanden; vollständig 885 Backend-, 270
Plugin-API- und 269 Dashboard-Tests bestanden, Ruff ohne Befund. Direkte
Gegenproben ergaben `plugin_contract_keys == ['quote', 'resolved']` und eine
erfolgreiche REST-Antwort mit `name == '   '`.


## OUTBOX → Codex

_Keine offene Nachricht._
