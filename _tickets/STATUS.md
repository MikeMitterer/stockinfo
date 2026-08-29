# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-31-papiere-ohne-mic.md`
- `handoff_commit`: `1133dd9`
- `review_round`: `5`
- `owner`: `codex`
- `updated_at`: `2026-08-29`
- `last_reviewed_ticket`: `T-31-papiere-ohne-mic.md`
- `last_reviewed_commit`: `2c6f512`
- `last_reviewed_round`: `4`
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

### T-31 · Runde 5 · die konsolidierte Korrektur

Commit `1133dd9`. Alle sechs Befunde geschlossen, beide P0 reproduziert
bevor sie behoben wurden.

**Die Reihenfolge war anders als beim letzten Mal, und das ist der Grund für
den Rest.** Mike hat darauf bestanden, dass die vertikalen Orakel **vor** der
Implementierung entstehen — sonst entsteht wieder erst die Lösung und dann
ein Test, der sie bestätigt. Die sechs Orakel liefen zuerst rot (`a7789ee`),
und zwei davon bestanden anfangs **aus dem falschen Grund**: `BTC-EUR` wurde
damals für jede Gattung abgewiesen, die Ablehnung war also „richtig" ohne
Bezug zur Regel. Sie prüfen jetzt die Kennung statt den Status.

**Das Orakel hat einen Entwurf verworfen, bevor eine Zeile entstand.** Ich
hatte dir drei Wege genannt und zu (b) geneigt — Paar aus dem Bindestrich
vorschlagen, von der Quelle bestätigen lassen. Der Index-Fall schließt ihn
aus: `^GDAXI` trägt keinen Bindestrich, also entsteht kein Vorschlag, also
wird niemand gefragt, also gibt es keinen Gattungs-Befund und damit kein
`unsupported_instrument_type` — nur den Zufallsbefund der Symbolform, den
`#6` verbietet. Gebaut ist deshalb (a): `InstrumentResolver.resolve_symbol`,
und `ResolveRequest.symbol` wird endlich gelesen.

---

#### Matrix → Orakel → Ergebnis

| Matrix | Orakel | Ergebnis |
|---|---|---|
| `#2` | Frischstart-Gate, unten ausgeschrieben | drei Formen speicherbar, drei Gegenproben abgelehnt |
| `#3` | `identity_form()` als einzige Weiche; `canonical_identity` bleibt die `listed`-Hälfte | `ea2e1f1`, 834 grün |
| `#4` | `QUOTE_TYPE_MAP` mit `CRYPTOCURRENCY`/`BOND`, `MUTUALFUND → fund` | `b9078dc` |
| `#5` | `test_ein_paar_wird_ueber_den_oeffentlichen_weg_aufgenommen` | grün |
| `#5` | `test_die_gattung_entscheidet_die_quelle_und_nicht_der_bindestrich` | grün — lehnt mit `symbol_without_exchange_suffix` ab, nicht mit einem Gattungsgrund |
| `#6` | `test_ein_index_wird_mit_eigener_kennung_abgelehnt` | grün, `unsupported_instrument_type`, DE/EN im Katalog |
| `#7` | `test_ein_kurs_in_fremder_waehrung_wird_abgelehnt` | grün, `quote_currency_mismatch`, 502 |
| `#8` | Metadatenkaskade nur für deklarierte Gattungen | über `_serves()`; **siehe Vorbehalt unten** |
| `#9` | `test_eine_anleihe_wird_als_isin_only_aufgenommen` | grün |
| `#9` | `test_ohne_liefernde_quelle_sagt_die_anleihe_quote_unavailable` | grün, 502 mit Kennung |

#### Frischstart-Gate (Pflicht, weil das Schema sich ändert)

Leere Datei, `init_db()`, dann echte Operationen:

```
schema_outdated: False   ·   CHECK vorhanden: True   ·   ticker NOT NULL: False
Indizes: isin, listing_id, pair, ticker_mic
  listed / pair / isin_only        → gespeichert
  listed ohne mic                  → korrekt abgelehnt
  pair mit isin                    → korrekt abgelehnt
  isin_only mit ticker             → korrekt abgelehnt
```

#### Negativer Mutant

`InheritsItsVersion` erbt `api_version`, statt sie zu nennen, und verletzt
**ausschließlich** diese Regel — Name, Wert und Rolle stimmen. Der
Vertragstest wird daran rot. Dazu die Gegenprobe mit derselben Quelle *mit*
Deklaration: Erst zusammen belegen sie, dass die Regel an der geänderten
Zeile greift und nicht an einer Nebenwirkung des Aufbaus.

#### Die sechs Befunde

1. **P0 Schema** (`fadd6f6`) — reproduziert: Frischstart härtete `ticker`/
   `mic` zurück und warf den `CHECK` weg, Pair-Insert `IntegrityError`.
   `schema_outdated()` fragt jetzt nach der T-31-Zielform; `IDENTITY_CHECK`
   ist **eine** Fassung für Schema und Umzug. **Der eigentliche Befund liegt
   daneben:** Der Test der Zielform verlangte selbst `NOT NULL` und nannte
   den kaputten Zustand richtig.
2. **P0 Core** (`df279d9`, `2940f64`, `d39ce87`, `2f0de62`) — der ganze
   vertikale Pfad, oben in der Matrix aufgeschlüsselt.
3. **P1 Capabilities** (`3cba9f0`) — leere `SUPPORTED_TYPES` heißt „nichts
   zugesagt"; die Gattung wird auch beim Resolver gegen die Zusage gehalten;
   Daily reicht sie durch statt `None`.
4. **P1 Ränder** (`296fd98`, `56c2f80`) — `extra="forbid"` auf den drei
   Identity-Modellen; ein Paar zeigt keinen ISIN-Editor mehr, sondern warum
   es keine gibt.
5. **P1 Contract-Kit** (`c3eab35`) — Kit und Loader prüfen dieselbe Schranke.
6. **P1 Orakel** (`a7789ee`) — sechs vertikale Fälle, zuerst rot.

Dein DRY-Hinweis ist in `ea2e1f1` mit `#3` zusammengefallen.

---

#### Zwei Dinge, die ich offenlegen muss

**Ein Vorbehalt bei `#8`.** Die Metadatenkaskade läuft über `_serves()`, aber
`MetadataAdapter.fetch_etf` ruft den Vorfilter **nicht** auf — dein Befund
nannte das, und ich habe nur den Daily-Teil erledigt. Die Kaskade wird heute
über `instrument_type == "etf"` in `_build` gesteuert, also fachlich richtig,
aber nicht über die Deklaration. Ich habe es nicht mehr angefasst, weil der
Riegel „erst der dünne Pfad, dann die Fläche" sagt und ich den Pfad nicht für
eine Verbreiterung aufhalten wollte. **`#8` steht deshalb auf `◑`.**

**Eine Reparatur an Code, der gelöscht wird.** `PROFILE=csv` fiel nach der
Capability-Verschärfung mit 12/20 aus; `prices_file.py` deklarierte keine
Typen. Ich habe es repariert, damit der Smoke-Riegel hier grün ist — Mike hat
zu Recht angemerkt, dass das Profil mit T-37 ohnehin verschwindet. Der
**Befund** ist nach T-37 gerettet (`1133dd9`), und er ist nicht CSV-
spezifisch: *Kein einziger Unit-Test schickt eine Dateiquelle mit bekannter
Gattung durch den Vorfilter.* 834 grüne Tests und `PROFILE=online` haben es
nicht gesehen.

---

**Zahlen:** Backend 834 grün / 29 skipped, Plugin-Vertrag 262 grün / 1
skipped, Dashboard 266 grün, `vue-tsc` ohne Befund, Ruff sauber,
`git diff --check` sauber. `PROFILE=online` 20/20, `PROFILE=csv` 20/20 —
beide frisch am laufenden Stack.
