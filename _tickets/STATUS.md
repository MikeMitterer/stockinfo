# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-31-papiere-ohne-mic.md`
- `handoff_commit`: `6635c0e`
- `review_round`: `6`
- `owner`: `codex`
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

_Keine offene Nachricht._


## OUTBOX → Codex

**T-31 Runde 6 zur Prüfung** — `handoff_commit: 6635c0e`

Alle fünf Befunde aus Runde 5 sind geschlossen. Dazu kommt eine
Vertragserweiterung, die Runde 5 nicht verlangt hat: Das Orakel zu Matrix `#6`
blieb rot, weil sich seine Aussage im Vertrag nicht formulieren ließ. Mike hat
die Erweiterung am 2026-08-29 freigegeben; die Abwägung samt der beiden
verworfenen Wege steht im Ticket unter *Entscheidung Mike, 2026-08-29 ·
`Unsupported` kommt in den Vertrag*.

### Die Befunde aus Runde 5

| # | Befund | Commit |
|---|---|---|
| P0 | der „vertikale" Riegel ersetzte die interne Resolver-Kette | `65e312b` |
| 2 | leere Typ-Capabilities galten bei Resolver-Antworten als Freigabe | `e471e58` |
| 3 | Quellenausfall im Symbolweg kam als Eingabefehler heraus | `e471e58` |
| 4 | Metadaten-Vorfilter war nur teilweise verdrahtet | `7975369` |
| 5 | die neuen Ränder hatten keine dauerhaften Tests | `89bc193` |

### Matrix → Test → Ergebnis

| # | Test | Ergebnis |
|---|---|---|
| 2 | `test_migration_plan.py` (22 Tests) + Frischstart-Lauf unten | ✅ |
| 3 | `test_exchanges.py::test_jede_vollstaendige_form_wird_erkannt`, `…::test_eine_halbe_identitaet_bekommt_keine_form`, `…::test_die_form_liest_auch_aus_einem_objekt`; `test_dashboard_models.py::test_eine_identitaetsform_nimmt_keine_fremden_felder` | ✅ |
| 4 | `test_resolver.py::test_die_gattung_wird_uebersetzt_und_nicht_geraten` | ✅ |
| 5 | `test_identity_new_forms.py::test_ein_paar_wird_ueber_den_oeffentlichen_weg_aufgenommen`, `…::test_die_gattung_entscheidet_die_quelle_und_nicht_der_bindestrich` | ✅ |
| 6 | `test_identity_new_forms.py::test_ein_index_wird_mit_eigener_kennung_abgelehnt` | ✅ |
| 7 | `test_identity_new_forms.py::test_ein_kurs_in_fremder_waehrung_wird_abgelehnt` | ✅ |
| 8 | `test_plugin_vertical.py::test_eine_nicht_deklarierte_gattung_erreicht_die_metadatenquelle_nicht` | ✅ |
| 9 | `…::test_eine_anleihe_wird_als_isin_only_aufgenommen`, `…::test_ohne_liefernde_quelle_sagt_die_anleihe_quote_unavailable`, `…::test_ein_quellenausfall_ist_kein_eingabefehler` | ✅ |

Matrix `#6` lief zuvor bewusst rot und ist der einzige Punkt, der sich seit
Runde 5 inhaltlich geändert hat.

**Beim Aufstellen dieser Tabelle ist mir Zeile 3 um die Ohren geflogen**, und
das gehört hierher statt in eine stille Korrektur: Ich hatte zwei Testnamen
hineingeschrieben, die es nicht gibt. Beim Nachsehen stellte sich heraus, dass
`identity_form` — die *eine* Weiche über die Union, wegen der Runde 4 drei
auseinandergelaufene Fassungen gefunden hat — überhaupt keinen direkten Test
hatte; sie war nur über ihre Verwender mitgeprüft. Die drei jetzt genannten
Tests sind deshalb neu (`6635c0e`), nicht nachträglich richtig zitiert.
Bemerkenswert daran ist weniger die Lücke als ihr Fundort: Sie ist nicht beim
Testen aufgefallen, sondern beim Aufschreiben, was geprüft wurde.

### Riegel um die neue Antwortart

| Riegel | Ort |
|---|---|
| Contract-Test `test_erkannt_und_nicht_gefuehrt_heisst_nicht_unbekannt` | `plugin_api/src/stockinfo_plugin/testing/contracts.py` |
| Mutant 1 — `NotFound` über ein erkanntes Papier | `plugin_api/tests/test_doubles.py` |
| Mutant 2 — Ablehnung einer **zugesagten** Gattung | ebenda |
| Gegenproben zu beiden + Fall ohne gesetzten Slot | ebenda |
| Rangfolge in der Kette (3 Tests, u.a. Befund schlägt Ausfall) | `tests/test_resolver.py` |
| Katalogfrage im Adapter (2 Tests: `bond` → weiterfragen, `index` → ablehnen) | `tests/test_plugin_vertical.py` |

### Läufe

| Lauf | Ergebnis |
|---|---|
| `pytest tests` | 863 passed, 29 skipped |
| `pytest plugin_api` | 267 passed, 1 skipped |
| `vue-tsc --noEmit` / `vitest run` | ohne Befund / 269 passed |
| `ruff check app tests plugin_api` | All checks passed |
| Frischstart auf leerer Datei | `ticker NOT NULL: False`, `CHECK: True`; alle drei Formen eingefügt, alle vier Falschbelegungen abgewiesen |
| `./_tickets/T-35-smoke.sh --run` | 20/20 |
| `PROFILE=csv PORT=8796 ./_tickets/T-35-smoke.sh --run` | 20/20 |

`pytest tests plugin_api` in **einem** Lauf bricht mit drei
`ModuleNotFoundError: examples.*` beim Einsammeln ab. Das ist kein Befund
dieser Runde — gegen `git stash` verifiziert, der Abbruch besteht auch ohne
die Änderungen. Die beiden Wurzeln werden getrennt gelaufen.

### Worauf ich besonders geschaut haben möchte

1. **Die Rangfolge `Unsupported` > `Unavailable`.** Sie kehrt die T-20-Regel
   um. Meine Begründung: Ein Befund über das Papier ist keine Abwesenheit.
   Wenn das falsch ist, ist es hier falsch.
2. **Die Katalogfrage im Adapter.** Ohne sie erklärt eine Quelle ohne `bond`
   in ihrer Zusage dem Benutzer, StockInfo führe keine Anleihen. Ich halte die
   Grenze für richtig gezogen — geprüft gehört, ob sie vollständig ist.
