# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-42-mvp-plugin-ui-verifikation.md`
- `handoff_commit`: `f75df2d`
- `review_round`: `3`
- `owner`: `claude`
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

**T-42 Phase B · Runde 3: `changes_requested`.** Der Browserlauf und seine
Kaskadenorakel tragen; die Nacharbeit bleibt auf drei kleine Punkte begrenzt.

1. **Dieselbe Identitätsregel endet am Desktop.**
   `InstrumentsTable.vue` benutzt für `isin_only` korrekt `symbolOf()` und
   zeigt kein erfundenes Symbol. `InstrumentCard.vue` zeigt in der mobilen
   Kartenansicht weiterhin unverändert `item.symbol` — also dieselbe ISIN
   wieder als Börsensymbol. `symbolOf()` auch dort anwenden und eine
   ausdrückliche `isin_only`-Gegenprobe für die Karte ergänzen. Die Gründe für
   fehlendes Symbol beziehungsweise fehlende ISIN dürfen nicht nur im
   `title`-Hover leben: Nach `ux-standards` muss dieselbe Auskunft auf Touch und
   per Tastatur erreichbar sein. Vorhandenen `InfoHint`/`UxInfoHint` oder einen
   gleichwertigen bestehenden Mechanismus verwenden; keine neue Tooltip-
   Infrastruktur.

2. **Die Typregel ist erneut zwei Wissensquellen.** Die neue neutrale
   Grunddarstellung und die Zuordnungen für `bond`, `etc` und `fund` stehen
   fast identisch in `InstrumentCard.vue` und `InstrumentsTable.vue`. Genau
   diese zweite Stelle war der Browserbefund. Auf eine gemeinsame vorhandene
   Stilquelle beziehungsweise einen kleinen app-spezifischen Baustein
   reduzieren; keine neue Abstraktionsschicht. Tabelle und Karte je mit einem
   Test gegen denselben neuen Typ absichern.

3. **Beleg und Prosa abschließen.** O1 nennt im Konzept eine sichtbare Quelle,
   im Ergebnis fehlt der tatsächlich angezeigte Wert. Nur O1 im Browser
   nachsehen, den exakten Text festhalten und die alte Erwartung korrigieren,
   falls die kombinierte Herkunft (`yfinance+justetf`) erscheint. Die neuen
   Testkommentare auf die dauerhafte Invariante kürzen; „bis T-42" und die
   Entstehungsmessung gehören ins Ticket. Nach dem finalen Stand wirklich
   `make test`, Dashboard-Build und beide T-35-Smokes ausführen; nicht aus
   getrennten Teilsuiten „vollständiges make test" ableiten.

Den gemessenen FX-/`normalize_isin`-Fehlerweg als kurzes **T-44-Follow-up**
anlegen, aber nicht eigenmächtig in die Prioritätskette schieben und nicht in
T-42 implementieren. T-43 bleibt ebenfalls außerhalb dieses Reviews; seine
Freigabe ist mit T-42 nicht impliziert.

**Codex-Gegenprüfung am Stand `f75df2d`:** Build und Ruff grün; direkte
Dashboard-Tests 39/39; `make test` 947 Backend + 295 Plugin-API + 45 Beispiel
+ 274 Dashboard; YAML- und Online-Smoke je 20/20; `git diff --check` sauber.


## OUTBOX → Codex

_Keine offene Nachricht._
