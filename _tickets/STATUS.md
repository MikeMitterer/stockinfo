# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-38-pflichtfelder-im-vertrag.md`
- `handoff_commit`: `96b3184`
- `review_round`: `1`
- `owner`: `codex`
- `updated_at`: `2026-08-30`
- `last_reviewed_ticket`: `T-31-papiere-ohne-mic.md`
- `last_reviewed_commit`: `ffb3ee7`
- `last_reviewed_round`: `7`
- `workstream`: `ui_live_acceptance`
- `priority_chain`: `T-36-befunde-aus-dem-ui-lauf.md` → `T-31-papiere-ohne-mic.md` → `T-38-pflichtfelder-im-vertrag.md` → `T-37-yaml-fallback-ein-datei.md` → `T-35-ui-abnahme-am-laufenden-stack.md` → `T-39-english-plugin-developer-guide.md` → `T-40-universelles-agenten-review-regelwerk.md`
- `priority_ticket`: `T-38-pflichtfelder-im-vertrag.md`

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

**T-38 Runde 1 zur Prüfung** — `handoff_commit: 96b3184`

Umgesetzt im engen Rahmen Deiner Ansage: propagieren, `docs/plugins.md`,
Tests, übergeben. Keine neuen Modelle, Endpunkte oder Abstraktionen; ein
Endpunkt hat einen **Abschnitt** dazubekommen (`/fields` → `plugin_contract`),
weil Verify `#6` genau das verlangt.

### Die Orakel waren zuerst da

`20be6d6`, zehn von dreizehn rot, aus der Verify-Matrix des Tickets. Was
danach grün wurde, war vorher gefordert.

### Matrix → Test → Ergebnis

| # | Beleg | Ergebnis |
|---|---|---|
| 2 | `test_contract_required_fields.py::test_eine_aufloesung_ohne_pflichtfeld_ist_nicht_baubar` | ✅ |
| 3 | kein zweiter Sprung — siehe Fußnote `[^v]` im Ticket | ✅ |
| 4 | `ResolverContract.test_bekanntes_papier_wird_aufgeloest` prüft `resolution_problem` | ✅ |
| 5 | `…::test_eine_unvollstaendige_antwort_legt_keine_zeile_an` (4 Fälle), `…::test_das_fehlende_feld_steht_im_protokoll` | ✅ |
| 6 / 6b | `…::test_die_feldauskunft_kennt_den_plugin_vertrag`, `…::test_name_und_gattung_stehen_dort_als_pflicht` | ✅ |
| 7 | `…::test_der_rest_vertrag_sagt_name_und_gattung_zu` (4 Fälle), `…::test_der_versionssprung_ist_ehrlich_gemacht` | ✅ |
| 8 | `…::test_openfigi_sagt_lieber_nichts_als_die_haelfte` (2 Fälle) | ✅ |
| 9 | T-37 vorbehalten, bewusst nicht vorweggenommen | ➖ |
| 10 | der Codeblock aus `docs/plugins.md` wird **ausgeführt** und gegen beide Invarianten geprüft | ✅ |

### Was der Bau gefunden hat, das nicht im Ticket stand

Ein Pflichtfeld verhindert das *Weglassen*, nicht das *Füllen mit nichts*.
`name=""` bleibt baubar, und für jede Prüfung auf `None` sieht das aus wie eine
Auskunft. Daraus drei Befunde:

1. **`require_core_values` kannte die neuen Pflichtfelder nicht.** Der Fehlfall
   wäre ein `500` ohne Auskunft gewesen — an vierzehn Stellen zugleich.
2. **`get_quote_for_known` reichte die Gattung durch, den Namen nicht.** Dieser
   Weg löst bewusst nicht auf; **jeder Refresh** wäre ein `502` geworden. Das
   ist der Befund, den sonst erst der Browserlauf gezeigt hätte.
3. **Das Repository schützte gegen `None`, nicht gegen `""`.** Ein leerer Name
   überschrieb den gespeicherten — derselbe Befund wie im UI-Lauf, eine Schicht
   tiefer.

Befund 3 kam von einem Test, dessen alte Fassung sich nicht mehr bauen ließ
(`QuoteResponse(name=None)` gibt es nicht mehr). Statt ihn zu streichen, prüft
er jetzt den leeren String.

### Zum Fixture-Sweep, weil die Zahl groß ist

38 Stellen in 10 Dateien haben `name`/`type` bekommen — **AST-geführt**, nicht
per Textsuche. Die Gegenprobe war ein Vorher/Nachher-Vergleich der roten Menge:
**kein einziger vorher grüner Test ist umgekippt.** Drei Tests, deren
Gegenstand die Abwesenheit eines Werts ist, wurden dabei rot und einzeln
nachgezogen; zwei davon beiläufig (geprüft wurden Platzhalterzahl bzw.
Sammelcode), einer inhaltlich.

Zwei Tests haben ihre Aussage **umgedreht** — eine Tabelle ohne Gattungsspalte
war gültig und ist es nicht mehr, eine Antwort ohne Gattung war unvollständig
und entsteht jetzt gar nicht. Beide Docstrings halten die alte Seite fest: Das
alte Argument war gut und hat gegen eine Messung verloren.

### Läufe

| Lauf | Ergebnis |
|---|---|
| `pytest tests` | 885 passed, 29 skipped |
| `pytest plugin_api` | 270 passed, 1 skipped |
| `vue-tsc --noEmit` / `vitest run` | ohne Befund / 269 passed |
| `ruff check app tests plugin_api` | All checks passed |
| Frischstart auf leerer Datei | drei Formen eingefügt, drei Falschbelegungen abgewiesen |
| `./_tickets/T-35-smoke.sh --run` | 20/20 |
| `PROFILE=csv PORT=8796 …` | 20/20 |

Die beiden Smoke-Läufe sind hier der wichtigste Beleg: Der schärfere Vertrag
hält am echten Netz, nicht nur gegen Doubles.

### Worauf ich besonders geschaut haben möchte

1. **Ob `resolution_problem` wirklich an allen drei Stellen dieselbe Regel
   ist.** Ihr Docstring behauptet drei Verwender; seit dieser Runde sind es
   auch drei.
2. **Der Fixture-Sweep.** Die Gegenprobe zeigt keine Umkehrung — aber sie zeigt
   nur, was ein Test *behauptet*. Ein Test, der `name` gar nicht prüft, hätte
   auch mit einem falschen Wert geschwiegen.
