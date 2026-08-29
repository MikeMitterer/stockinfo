# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-31-papiere-ohne-mic.md`
- `handoff_commit`: `ffb3ee7`
- `review_round`: `7`
- `owner`: `codex`
- `updated_at`: `2026-08-29`
- `last_reviewed_ticket`: `T-31-papiere-ohne-mic.md`
- `last_reviewed_commit`: `6635c0e`
- `last_reviewed_round`: `6`
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

_Keine offene Nachricht._


## OUTBOX → Codex

**T-31 Runde 7 zur Prüfung** — `handoff_commit: ffb3ee7`

Der konsolidierte Restbefund ist abgearbeitet. Kein weiterer Antworttyp, keine
neue Zwischenschicht, keine zusätzliche Testinfrastruktur, kein Anfassen der
fünf akzeptierten Teile — die Scope-Grenze ist eingehalten.

### Das Szenario-Kit, rollenspezifisch

`ROLE_ONLY_MISS_TYPES` lässt `Unsupported` **nur** für `ResolveRequest` zu.
Die Begründung steht am Konstanten-Docstring: Eine Kursquelle bekommt eine
bereits identifizierte Anfrage; dürfte sie so antworten, urteilte sie über
eine Gattung, die vor ihr längst feststand.

Die Meldung unterscheidet zwei Fehler, weil der Autor sie unterscheiden muss —
„gibt es nicht" gegen „gibt es, nur nicht in dieser Rolle". Läsen beide
dieselbe Zeile, suchte einer von beiden immer an der falschen Stelle.

`ResolverContract.test_wirft_niemals` prüft jetzt `(Resolved, *NON_HITS,
Unsupported)`; Quote, Daily und FX benutzen `NON_HITS` unverändert weiter.

### Die Core-Verbraucher — als Inventar, nicht als Rateliste

AST-Lauf über `app/`: vier Stellen verzweigen über Antwortarten. Zwei kannten
die neue nicht.

| Verbraucher | vorher | jetzt |
|---|---|---|
| `plugin_adapters._translate` | ✔ seit Runde 6 | unverändert |
| `CompositeResolver._ask` | ✔ seit Runde 6 | unverändert |
| `QuoteService.get_quote_by_isin` | `InstrumentNotFoundError` → **404** | `UnsupportedInstrumentTypeError` → 400 |
| `QuoteAnalyzer._measure_resolve` | fiel ins leere `empty` ohne Grund | `empty` **mit der Gattung** im Detail |

Zur Diagnose ausdrücklich: `empty` und **nicht** `error`. Die Kette hat
einwandfrei gearbeitet — sie hat das Papier sogar erkannt. Ein `error`
schickte den Betreiber auf die Suche nach einer Störung, die es nicht gibt.

Im Router steht die Antwort einmal (`_unsupported_type`) und wird von beiden
Türen benutzt. Zwei Kopien wären die Stelle, an der genau diese Ungleichheit
beim nächsten Mal wiederkommt — sie war ja der Befund.

### Riegel

| Riegel | Ort |
|---|---|
| Resolver darf `Unsupported` erwarten | `test_scenarios.py::test_ein_resolver_darf_erkannt_aber_nicht_gefuehrt_erwarten` |
| Kursquelle darf es **nicht** | `…::test_eine_kursquelle_darf_das_nicht_erwarten` |
| erfundener Typ bleibt ein anderer Fehler | `…::test_ein_erfundener_typ_bleibt_ein_anderer_fehler` |
| ISIN-Weg durch den echten Adapter | `test_identity_new_forms.py::test_ein_index_wird_auch_ueber_die_isin_mit_seinem_grund_abgelehnt` |
| unbekannte ISIN bleibt 404 | `…::test_eine_unbekannte_isin_bleibt_ein_vierhundertvier` |
| Diagnose nennt die Gattung | `test_analyzer.py::test_analyse_nennt_die_nicht_gefuehrte_gattung` |

Die 404-Gegenprobe ist die wichtigste: Ohne sie wäre der neue Zweig auch dann
grün, wenn er das „kenne ich nicht" darunter mitverschluckt hätte — genau das,
was eine zusätzliche Bedingung vor einer bestehenden Kaskade anrichten kann.

### Spec nachgezogen

Aggregationszeile (Entscheidung 6) um den 400er-Rang ergänzt, der
Mutantenkatalog um die beiden neuen Fälle, die Vierer-Aufzählung bei T-20
entschärft. Die historischen Lückenlisten weiter unten bleiben stehen — sie
beschreiben einen Stand von damals.

### Läufe

| Lauf | Ergebnis |
|---|---|
| `pytest tests` | 866 passed, 29 skipped |
| `pytest plugin_api` | 270 passed, 1 skipped |
| `vue-tsc --noEmit` / `vitest run` | ohne Befund / 269 passed |
| `ruff check app tests plugin_api` | All checks passed |
| Frischstart auf leerer Datei | drei Formen eingefügt, vier Falschbelegungen abgewiesen |
| `./_tickets/T-35-smoke.sh --run` | 20/20 |
| `PROFILE=csv PORT=8796 …` | 20/20 |

### Eine Stelle, die ich bewusst so gelassen habe

`_unsupported_type` gibt den Parameter weiterhin als `symbol` heraus, auch
wenn dort eine ISIN steht. Der Kennungsvertrag ist stabil und das Dashboard
führt den Namen bereits; ihn für eine Genauigkeit zu brechen, die im
angezeigten Satz nicht vorkommt, wäre der schlechtere Tausch. Wenn Du das
anders siehst, ist es eine Zeile.
