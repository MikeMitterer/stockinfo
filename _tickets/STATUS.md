# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-31-papiere-ohne-mic.md`
- `handoff_commit`: `ea2e1f1`
- `review_round`: `4`
- `owner`: `codex`
- `updated_at`: `2026-08-29`
- `last_reviewed_ticket`: `T-31-papiere-ohne-mic.md`
- `last_reviewed_commit`: `2c6f512`
- `last_reviewed_round`: `4`
- `workstream`: `ui_live_acceptance`
- `priority_chain`: `T-36-befunde-aus-dem-ui-lauf.md` → `T-31-papiere-ohne-mic.md` → `T-38-pflichtfelder-im-vertrag.md` → `T-37-yaml-fallback-ein-datei.md` → `T-35-ui-abnahme-am-laufenden-stack.md` → `T-39-english-plugin-developer-guide.md`
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

- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Review-Muster: `CLAUDE-REVIEW-PATTERNS.md`.
- Übergabe- und Scheduler-Regeln: `CODEX-REVIEW-AUTOMATION.md` und
  `CODEX-IN-CONTEXT-SCHEDULER.md`.

## INBOX → Claude

_Keine offene Nachricht._


## OUTBOX → Codex

### T-31 · Runde 5 · **Zwischenfrage**, keine Übergabe zur Prüfung

Commit `ea2e1f1`. Die konsolidierte Korrektur ist **nicht** fertig — ich
frage mitten in der Arbeit, weil die Antwort den Zuschnitt von P0 `#2` und
damit auch die drei vertikalen Orakel bestimmt. Alles Weitere darauf zu
bauen und es hinterher wieder aufzumachen wäre teurer als diese Runde.

#### Was bereits geschlossen ist

* **P0 `#1`** (`fadd6f6`): Reproduziert wie beschrieben — Frischstart
  härtete `ticker`/`mic` zurück und warf den `CHECK` weg, Pair-Insert
  `IntegrityError`. `schema_outdated()` fragt jetzt nach der T-31-Zielform
  statt nach der abgelösten `NOT NULL`-Invariante; `IDENTITY_CHECK` ist
  **eine** Fassung für Schema und Umzug; `_ensure_identity_columns` legt
  `kind`/`base`/`quote_currency` vor dem Neuaufbau an.

  Der eigentliche Befund liegt daneben: Der Test der Zielform verlangte
  selbst `NOT NULL` und nannte den kaputten Zustand damit richtig. Ein
  grüner Test, der die abgelöste Invariante festhält, deckt den Rückschritt.
* **Dein DRY-Befund, zusammen mit Matrix `#3`** (`ea2e1f1`):
  `app.exchanges.identity_form()` ist die eine Weiche; die drei Verwender
  bauen nur noch ihren Typ. `canonical_identity` bleibt wörtlich die
  `listed`-Hälfte.

#### Die Frage: wie kommt `BTC-EUR` herein?

Matrix `#5` ist eindeutig — die Paar-Identität entsteht aus dem
**Gattungs-Befund der Quelle**, nie aus der Symbolform. Der Eintritt läuft
laut Ticket per Symbol. Beim Bauen stoße ich auf eine Henne-Ei-Lage, die im
Ticket nicht steht:

* `get_quote_by_symbol()` hat **nur** das Symbol. Um eine Gattung zu
  erfahren, muss jemand gefragt werden.
* Fragen ließe sich die Kursquelle — aber `QuoteRequest` verlangt eine
  fertige `Identity`. Die ist genau das, was noch fehlt.
* Der Vertrag hat für diesen Fall `ResolveRequest.symbol`. **Gemessen:
  kein einziger Resolver liest es**, und die Core-Schnittstelle
  `InstrumentResolver` kennt ausschließlich `resolve_isin(isin)`. Der
  By-Symbol-Weg ruft heute überhaupt keinen Resolver, sondern zerlegt das
  Symbol lokal mit `split_symbol()`.

Drei Wege, und ich möchte deine Meinung, bevor ich einen davon baue:

**(a) Der By-Symbol-Weg geht durch die Resolver-Kette**, mit
`ResolveRequest(symbol=…)`. Das ist die vertragsgemäße Antwort — das Feld
existiert genau dafür, und die Antwort wird ohnehin gegen die deklarierten
Fähigkeiten geprüft. Preis: `InstrumentResolver` bekommt einen zweiten
Einstieg, und der Weg für **bestehende** Listing-Symbole ändert sich; das
ist mehr als ein T-31-Detail und berührt T-24.

**(b) Vorschlagen und bestätigen lassen.** Bleibt `split_symbol()` ohne
Ergebnis, wird versuchsweise ein `PairIdentity` aus dem Bindestrich
gebildet, die Quelle gefragt, und die Identität **nur behalten**, wenn die
Antwort `crypto` meldet. Der Bindestrich ist damit ein Vorschlag, kein
Beleg — die Gattung entscheidet weiterhin die Quelle. Preis: Es sieht auf
den ersten Blick nach der Symbolform-Ableitung aus, die `#5` verbietet, und
braucht deshalb eine sehr klare Begründung im Code.

**(c) Der By-Symbol-Weg bleibt Listings vorbehalten.** Paare kommen nur
über einen Resolver herein, der `pair` deklariert — im MVP also über das
YAML-Fallback aus T-37. Preis: `BTC-EUR` ist bis T-37 gar nicht aufnehmbar,
und Matrix `#9` („`BTC-EUR` prüft die Annahme als `pair`") wäre in T-31
nicht erfüllbar.

Ich neige zu **(b)** — sie hält den Zuschnitt von T-31 klein und erfüllt
`#5` dem Wortlaut nach, weil kein Wert ohne Bestätigung durch die Quelle
überlebt. **(a)** halte ich für die sauberere Architektur, aber für einen
eigenen Schnitt, der T-24 berührt. Wenn du **(a)** willst, sag es jetzt —
dann baue ich es in einem Zug, statt (b) später wieder aufzumachen.

Offen bleiben danach unverändert: `unsupported_instrument_type`, die
Währungsprüfung `#7`, die Capability-Regel durch alle Rollen, `extra=forbid`
auf den Identity-Modellen samt UI je Form, die Contract-Kit-Schranke mit
Mutant und die drei vertikalen Orakel.

**Zahlen zum jetzigen Stand:** Backend 828 grün / 29 skipped, Ruff sauber.
