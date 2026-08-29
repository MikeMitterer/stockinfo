# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-31-papiere-ohne-mic.md`
- `handoff_commit`: `2c6f512`
- `review_round`: `4`
- `owner`: `codex`
- `updated_at`: `2026-08-29`
- `last_reviewed_ticket`: `T-31-papiere-ohne-mic.md`
- `last_reviewed_commit`: `fb0de21`
- `last_reviewed_round`: `3`
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

### T-31 · Runde 4 · die Umsetzung, Vertrag bis Oberfläche

Commit `2c6f512`. Der freigegebene Schnitt ist gebaut — zwölf Commits, vom
Contract-Kit bis ins Dashboard.

**Zahlen.** Backend 828 grün / 29 skipped, Plugin-Vertrag 260 grün / 1
skipped, Dashboard 266 grün, `vue-tsc` ohne Befund, `ruff check app tests
plugin_api` sauber, `git diff --check` sauber. **`PROFILE=online` 20/20 und
`PROFILE=csv` 20/20**, beide frisch am laufenden Stack.

---

#### Zwei Abweichungen vom freigegebenen Entwurf

Beide sind Entscheidungen, keine Versehen, und beide gehören vor allem
anderen auf den Tisch.

**1 · `core_version` steigt hier, nicht in T-38.** Der Entwurf sagte „hier
wird sie vorbereitet, nicht gesetzt". Das ließ sich nicht halten:
`test_contract_openapi` erneuert den Schnappschuss nur, wenn die Nummer
steigt — genau dafür ist er gebaut. Ihn zu erneuern und `2.1.0`
stehenzulassen wäre die stille Variante gewesen, gegen die er existiert.

Der Denkfehler im Entwurf war einfach: **T-31 *ist* der Bruch.** Die
Identität wechselt hier ihre Form, `ticker`/`mic`/`isin` verschwinden aus
der Wurzel. T-38 macht danach `name` und `type` zur Pflicht — ebenfalls
breaking, aber unter derselben Major, weil dazwischen kein Release liegt.
Es bleibt bei **einem** Sprung, was T-31 verlangt; er fällt nur früher.
`core_version` steht auf `3.0.0`.

**2 · `QuoteResponse` bekam `extra="forbid"`, was im Entwurf nicht stand.**
Der Anlass ist gemessen: Beim Umbau blieb an fünf Stellen ein `isin=` neben
dem neuen `identity=` stehen. Pydantic verwarf es **kommentarlos** — die
Zeile ging ohne ISIN in die Datenbank, und der Fehler tauchte zwei
Schichten später als `TypeError: 'NoneType' object is not subscriptable`
auf, an einer Stelle ohne jeden Bezug zur Ursache.

Das ist wörtlich das Muster, gegen das T-38 geschrieben wird: Ein Wert
fehlte, und nichts hat gefragt. Wenn du den Schalter für Scope-Ausweitung
hältst, nehme ich ihn heraus — aber dann bitte mit einer Notiz in T-38,
denn er gehört dorthin.

---

#### Was gebaut ist

* **Vertrag.** Union aus `ListedIdentity`/`PairIdentity`/`IsinOnlyIdentity`,
  `identity` als Feld an `Resolved`, `QuoteRequest` und `DailyRequest`,
  `API_VERSION = 2`. `isin_of()` gibt es, `ticker`/`mic`-Properties nicht —
  ein `None` für eine ISIN erfindet nichts, ein Ticker für ein Paar schon.
* **Versionsschranke.** Der Loader liest `source_class.__dict__`, wie in
  Runde 2 festgelegt. Sie beißt: `LocalFileResolver` in
  `test_plugin_vertical` erbte von `CanadaFileResolver` und wurde abgewiesen
  — genau die Konstellation, auf die du gedrungen hast, jetzt an einem
  echten Ladeweg belegt.
* **Fähigkeiten.** `_serves()` sitzt bei Quote und Daily, also **nach** der
  Auflösung. Beim Resolver gibt es keinen Vorfilter; stattdessen prüft
  `ResolverAdapter` die Antwort gegen die Deklaration und meldet einen
  Verstoß als Befund.
* **Schema.** `CHECK` je Form, verlangend **und** ausschließend; drei
  partielle Indizes; `isin` und `listing_id` unverändert global eindeutig.
* **REST.** Ein Feld `identity`, keine parallelen Felder. Artefakt,
  OpenAPI-Snapshot und drei Fixtures ziehen nach.
* **Dashboard.** `isinOf()` und `refOf()` als die zwei Stellen der
  Fallunterscheidung. Der Typprüfer hat alle 16 Fundstellen selbst genannt.

#### Naming — gemessen, nicht geraten

Das AST-Inventar über die **53 berührten `.py`-Dateien** fand statt der vier
vorhergesagten (`feld`, `vertrag`, `herkunft`, `taugliche`) **34** deutsche
Bezeichner; die übrigen in Testdateien, die dieser Umbau ohnehin angefasst
hat. Dazu das TypeScript-Inventar über zehn `.ts`/`.vue`-Dateien, das den
Einbuchstabennamen `i` in `AnalysisPanel.vue` zeigte.

Ersetzt über `tokenize`, nicht über `replace_all`: `kaputt`, `quelle` und
`antwort` stehen in denselben Dateien auch in deutscher Prosa, und dort
bleiben sie. Ein `NAME`-Token ist ein Bezeichner, ein `STRING`-Token ist
Text.

**Zwei Stellen sieht auch der Tokenizer nicht**, und beide sind aufgefallen:
Python 3.11 gibt einen f-String als *ein* STRING-Token (Ruff meldete
`F821`), und `parametrize` nennt seine Parameter als Zeichenketten (pytest
meldete „function uses no argument"). Die Gegenprobe trägt nur, weil sie aus
mehr als einem Werkzeug besteht.

#### Woran ich dich besonders bitte zu sehen

* Die beiden Abweichungen oben.
* `_serves()` filtert **nicht**, wenn die Gattung unbekannt ist. Gedacht als
  „eine Nichtangabe ist keine Grundlage zum Überspringen" — oder ist das
  eine Lücke?
* Die `CHECK`-Klausel verbietet `isin` bei `kind='pair'`. Ein Krypto-ETP hat
  eine ISIN, ist aber `listed`; ich halte das für richtig. Zweitmeinung?
* `_instrument_from()` bildet für `isin_only` das Symbol **aus der ISIN**.
  Sie ist dort die ganze Identität, aber ein Symbol ist sie eigentlich nicht.

Ein Punkt, den ich **nicht** angefasst habe: Die Testquellen führen deutsche
Namen als Zeichenketten (`name = "kandidat"`, `"meins"`, `"heil"`). Das sind
Werte, keine Bezeichner — ich wollte den Scope nicht stillschweigend
ausweiten. Sag, ob sie mitziehen sollen.
