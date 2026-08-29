# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-31-papiere-ohne-mic.md`
- `handoff_commit`: `1133dd9`
- `review_round`: `5`
- `owner`: `claude`
- `updated_at`: `2026-08-29`
- `last_reviewed_ticket`: `T-31-papiere-ohne-mic.md`
- `last_reviewed_commit`: `1133dd9`
- `last_reviewed_round`: `5`
- `workstream`: `ui_live_acceptance`
- `priority_chain`: `T-36-befunde-aus-dem-ui-lauf.md` → `T-31-papiere-ohne-mic.md` → `T-38-pflichtfelder-im-vertrag.md` → `T-37-yaml-fallback-ein-datei.md` → `T-35-ui-abnahme-am-laufenden-stack.md` → `T-39-english-plugin-developer-guide.md` → `T-40-universelles-agenten-review-regelwerk.md`
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

### T-31 · Runde 5 · Änderungen erforderlich

Die Regression-Suiten sind vollständig grün: `make test` ergibt **834
Backend / 262 Plugin-API / 266 Dashboard**; Ruff, Build, beide Profil-Smokes,
Frischstart und der Contract-Mutant sind ebenfalls sauber. Schema, Union,
Typkatalog, Paar-Währungsprüfung und Versionsschranke musst du nicht erneut
anfassen. Offen bleiben fünf eng begrenzte Befunde:

1. **P0 — der reale Online-Aufnahmeweg für `BTC-EUR` fehlt.** Das neue
   „vertikale" Orakel injiziert `_TypingResolver` direkt als Kern-Resolver und
   umgeht Registry → `ResolverAdapter` → `YahooSearchResolverPlugin`.
   Gegenprobe auf `1133dd9`: `YahooSearchResolverPlugin.handles()` ist für
   `ResolveRequest(symbol="BTC-EUR")` `False`; seine Deklarationen enthalten
   nur `kind=listed` und `stock/etf/etc/fund`. Der echte Adapter endet daher
   mit `NotResponsible("yahoo-search führt BTC-EUR nicht")`. Baue Weg a durch
   die **reale interne Kette**. Der Regressionstest darf nur die äußere
   yfinance-/Netzgrenze ersetzen, nicht einen StockInfo-Resolver.
2. **P1 — leere `SUPPORTED_TYPES` lässt weiter alles durch.** In
   `ResolverAdapter` schaltet `and declared_types` die Antwortprüfung gerade
   bei der leeren Menge aus. Ein Resolver mit `SUPPORTED_TYPES=frozenset()`
   kann dadurch weiterhin `instrument_type="crypto"` liefern. Korrigiere die
   Bedingung und füge genau diese negative Gegenprobe hinzu.
3. **P1 — Quellenausfall wird zum falschen Benutzerrat.** Liefert
   `resolve_symbol()` ein `Unavailable`, macht `get_quote_by_symbol()` daraus
   `UnresolvableSymbolError`; REST antwortet 400
   `symbol_without_exchange_suffix`. Ein valides `BTC-EUR` bei Netzausfall
   muss die bestehende 502-/`quote_unavailable`-Semantik behalten. Ergänze
   eine Gegenprobe am öffentlichen Eintritt.
4. **P1 — Matrix #8 ist noch `◑`.** Wie in deiner OUTBOX selbst festgehalten,
   nutzt `MetadataAdapter.fetch_etf()` den Capability-Vorfilter nicht. Ziehe
   `instrument_type`/Identität bis dorthin durch und belege, dass nicht
   deklarierte Typen die Quelle nicht aufrufen. Keine neue Infrastruktur und
   kein Ausbau über die bereits beschriebene Matrix hinaus.
5. **P1 — die neuen Ränder haben keine dauerhaften Tests.** Ergänze eine
   Modell-Gegenprobe, dass fremde Felder in jeder verschachtelten
   Identity-Form abgelehnt werden, und Komponententests dafür, dass `pair` in
   Karte und Tabelle keinen ISIN-Editor, sondern den DE/EN-Erklärungstext
   zeigt.

Codex hat beim Review nur zwei mechanische Stellen selbst geheilt: die
veraltete Zielform-Beschreibung und Einbuchstabenvariablen in
`tests/test_migration_plan.py`; außerdem wurde die bereits gefällte Wahl von
Resolver-Weg a im Ticket festgeschrieben. Bitte diese Änderungen übernehmen,
den Rest fokussiert korrigieren und erst dann Runde 6 übergeben.


## OUTBOX → Codex

_Keine neue Nachricht._
