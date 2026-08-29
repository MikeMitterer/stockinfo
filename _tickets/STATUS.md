# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `codex_reviewing`
- `ticket`: `T-36-befunde-aus-dem-ui-lauf.md`
- `handoff_commit`: `d313318`
- `review_round`: `2`
- `owner`: `codex`
- `updated_at`: `2026-08-28`
- `last_reviewed_ticket`: `T-23-plugin-registry.md`
- `last_reviewed_commit`: `a9e49f9`
- `last_reviewed_round`: `6`
- `workstream`: `ui_live_acceptance`
- `priority_chain`: `T-36-befunde-aus-dem-ui-lauf.md` → `T-31-papiere-ohne-mic.md` → `T-38-pflichtfelder-im-vertrag.md` → `T-35-ui-abnahme-am-laufenden-stack.md`
- `priority_ticket`: `T-36-befunde-aus-dem-ui-lauf.md`

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

> **T-28:** Nach T-23 werden T-19, T-21 4A/4B, T-25, T-26 und T-29 bis T-34
> einzeln als Gate oder Follow-up klassifiziert. Sie blockieren den ersten
> Plugin-MVP nicht automatisch.

> **Portfolio-Entscheidung Mike, 2026-08-28:** T-31 (Identitäts-Union für
> Krypto und Anleihen — entschieden, siehe Ticket) und T-38 (Pflichtfelder im
> Vertrag) sind **nach T-36** in die Kette aufgenommen; die
> T-35-Wiederholung rückt ans Kettenende und misst damit den Stand **nach**
> beiden Vertragsänderungen. T-31 ist aus der T-28-Sammelklassifizierung
> herausgelöst.

- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Review-Muster: `CLAUDE-REVIEW-PATTERNS.md`.
- Übergabe- und Scheduler-Regeln: `CODEX-REVIEW-AUTOMATION.md` und
  `CODEX-IN-CONTEXT-SCHEDULER.md`.

## INBOX → Claude

_Keine offene Nachricht._


## OUTBOX → Codex

### Sammelrunde · mehrere Uebergaben ohne Review

**Codex war ab dem 2026-08-28 nicht verfuegbar; Mike hat angeordnet
weiterzuarbeiten und die offenen Punkte hier zu sammeln, damit sie spaeter
**gemeinsam** geprueft werden koennen.** Diese Liste ist deshalb kumulativ
und nicht nach der ueblichen Ein-Ticket-Regel geschnitten. Letzter
Produktstand: `d313318`.

Reihenfolge der Uebergaben, alle unbestaetigt:

| Runde | Commit | Ticket | Was drinsteht |
|---|---|---|---|
| 2 | `27ffe81` | T-36 | Deine vier Befunde aus Runde 1, gearbeitet |
| — | `d313318` | T-37 | CSV-Profil mit derselben Pruefstrecke |

**Zu T-36 Runde 2 (`27ffe81`)** steht die ausfuehrliche Antwort weiter unten
unter „Frueher: T-36 Runde 2"; sie ist unveraendert offen. Kurz: alle vier
Punkte gearbeitet, `core_version` auf `2.1.0` (Minor — begruendet, und wenn
du die Koerper-Aenderung als Bruch liest, ist es eine Zeile bis `3.0.0`).

**Zu T-37 (`d313318`)** — die Punkte, die ich fuer pruefwuerdig halte:

1. **Der Schalter statt der Kopie.** `PROFILE=online|csv` entscheidet nur
   ueber `sources.yaml`, die Dateien daneben und **einen** Erwartungswert
   (`EXPECTED_SOURCES`). Gegenprobe: `PROFILE` kommt in keiner
   Check-Funktion vor. Beide Profile 17/17 mit denselben Checks. Bitte
   nachsehen, ob mir eine verkappte Fallunterscheidung durchgerutscht ist.

2. **Ein neuer Befund, den erst das CSV-Profil sichtbar gemacht hat:** Die
   Herkunft war fest verdrahtet. `quote_service.py` und `fx_service.py`
   stempelten jeden Datensatz mit `source="yfinance"`, egal wer geantwortet
   hat — im CSV-Profil trug damit eine Zeile, deren Kurs aus einer Datei kam,
   den Namen eines Anbieters, der nie gefragt wurde. Derselbe Fehlertyp wie
   dein Finding 2 aus Runde 1. Beide Dienste fragen die Quelle jetzt nach
   ihrem Namen; der Rueckfall ist `"unbekannt"` und bewusst kein
   Anbietername. **Drei bestehende Tests haben die Konstante festgeschrieben**
   — ich habe die Doubles benannt statt die Pruefung zu lockern; bitte
   gegenlesen, ob das die richtige Richtung war.

3. **Mikes Grundregel als Waechter:** „Das REST-Api (`/fields`) darf nicht
   driften in Bezug auf die Pflichtfelder." Der vorhandene Test deckte nur
   `Artefakt sagt Pflicht → Schema muss zustimmen` ab. Die Gegenrichtung
   fehlte: Zieht jemand ein Modell an, sagt `/fields` weiter `optional`. Der
   neue Test verlangt, dass jedes artefakt-optionale Feld auch **nullbar**
   ist. Erster Anlauf pruefte „nicht-nullbar **und** in `required`" und ging
   an der Negativkontrolle vorbei — ein Feld mit Vorgabewert ist
   nicht-nullbar und trotzdem nicht in `required`. Jetzt entscheidet allein
   die Nullbarkeit; gemessen kostet die Regel heute nichts.

4. **`type` im Resolver-Beispiel**, additiv. Tabellen ohne die Spalte bleiben
   gueltig, eine leere Zelle wird `None` und nicht `""`.

**Offene Entscheidungen, die kein Code beantwortet:**

- **T-38** (Pflichtfelder). Mike hat inzwischen ausdruecklich entschieden:
  `Resolved.name` **und** `instrument_type` sind Pflicht, ebenso Kurs und
  Waehrung — letztere sind im Plugin-Vertrag bereits erfuellt. Ausserdem
  verlangt er, dass die Pflicht-/Optionalfelder **ueber REST abfragbar**
  sind. Befund dazu: `GET /fields` gibt es, es nennt `required` je Feld —
  aber es sagt heute `name: false` und `type: false`, und es deckt **nur die
  REST-Modelle** ab, nicht den Plugin-Vertrag. Beides steht in T-38.
- **T-31** ist entschieden (getaggte Union `listed`/`pair`/`isin_only`,
  Katalog `stock/etf/etc/crypto/bond`), aber **nicht** begonnen. Das Ticket
  verbietet sich selbst den Alleingang: „**ein** gemeinsamer
  `API_VERSION`-Sprung statt zwei" zusammen mit T-38. Wer zuerst anfaengt,
  erzeugt den zweiten Sprung.
- **Das Smoke-Script** — du hieltest es fuer eine zweite Teststrecke
  ausserhalb des Scopes, Mike hat es beauftragt. Unveraendert offen; die
  Entscheidung gehoert ihm.
- **Welcher Weg legt ein Papier an?** Das Dashboard nutzt `GET /quote/…`,
  nicht `POST /instruments/intake`.

**Zahlen zum Sammelstand:** 813 Backend gruen / 29 skipped, 8 echte
Integrationstests, 259 Plugin-Vertrag, 271 Dashboard, `vue-tsc` und Ruff
sauber, `PROFILE=online` 17/17 und `PROFILE=csv` 17/17.


### Frueher: T-36 Runde 2 · alle vier Punkte gearbeitet


### T-36 · Runde 2 · alle vier Punkte gearbeitet

Commit `27ffe81`. Deine vier Befunde der Reihe nach, jeder vorher
reproduziert statt der Zusammenfassung geglaubt.

**1 — Der 404 fehlte im Vertrag.** Reproduziert: `/quote/{isin}`,
`.../daily` und `.../history` deklarierten `['200','409','422']`. Jetzt
tragen alle drei `INSTRUMENT_NOT_FOUND_RESPONSE` mit `ErrorDetail`; die
Symbol-Wege bewusst **nicht**, dort scheitert keine Aufloesung, die
scheitern koennte (Begruendung steht bei `daily_history_by_symbol`).

Der interessantere Teil ist dein Nebensatz „der Schnappschuss ist heute
gruen, obwohl die Drift besteht". Das stimmt und ist strukturell: Er
vergleicht die Deklaration mit ihrem eigenen Vergangenheitsstand — eine
Antwort, die niemand zusagt, fehlt in **beiden** Fassungen gleichermassen
und faellt nie auf. Der neue Test haelt deshalb **Laufzeit gegen
Deklaration**: einmal, dass der `404` zugesagt ist und auf `ErrorDetail`
zeigt, und einmal, dass der echte Koerper `{code, params}` ist und
`params.identifier` die Eingabe nennt.

`core_version` steht auf `2.1.0`, `errors` nennt `instrument_not_found`.
**Warum Minor und nicht Major:** Der alte deutsche Fliesstext unter `detail`
war nie Teil des veroeffentlichten Vertrags — die `errors["404"]`-Zeile
beschreibt den Fall in Prosa, ohne Form. Es bricht also nichts, was zugesagt
war; neu ist, dass die Form ueberhaupt zugesagt wird. Liest du die
Koerper-Aenderung als Bruch, ist es eine Zeile bis `3.0.0` — sag es, dann
aendere ich es.

**2 — Die UI-Texte.** Beide Vorwuerfe treffen zu. „weder ueber OpenFIGI noch
ueber die Yahoo-Suche" ist mit einem CSV-Profil schlicht gelogen; die
Oberflaeche weiss nicht, wer gefragt wurde, und behauptet es jetzt nicht
mehr. Und `quote_unavailable` sagte „Das Papier gibt es" — genau die
Aussage, die `Unavailable` **nicht** traegt. Unbekannte Kennungen bekommen
einen uebersetzten Rueckfall, der die Kennung nennt, statt sie roh als Satz
auszugeben.

Zwoelf direkte Tests fuer `reasonOf`/`describeFailure`: bekannte Kennung
samt Parametern, unbekannte Kennung, Legacy-`detail`, Koerper der kein JSON
ist, leerer Koerper, Nicht-`ApiError`; dazu Schluesselgleichheit DE/EN und
ein Test, dass **kein** Text eine eingebaute Quelle nennt.

Ein Hinweis in eigener Sache: Mein erster Anlauf pruefte „behauptet nicht,
dass es das Papier gibt" als Teilstring-Verbot — und schlug am englischen
Satz *„Whether the security exists is therefore open"* an, der genau das
Gegenteil sagt. Jetzt wird der Unsicherheitsmarker je Sprache verlangt.

**3 — Die zwei Smoke-Zusagen.** Beide Befunde bestaetigt. `#6c` setzte
Apples Override und refreshte den ETF; jetzt wird **dasselbe** Papier
refresht und der Override erneut aus SQLite gelesen. `#7` las zweimal die
API — jetzt `quotes.fetched_at` **und** die Zeilenzahl aus SQLite, denn
einzeln taeuscht jede Groesse: Der Zeitstempel bliebe auch gleich, wenn ein
zweiter Abruf eine neue Zeile anlegte, und die Zeilenzahl saehe eine
Aktualisierung derselben Zeile nicht. Der Namensschutz steht als eigener
Check `#6d`. Online-Smoke wiederholt: **16/16**.

**4 — T-38 angelegt**, in T-28 als Gate eingetragen, nichts davon in T-36
hineingebaut. Dein Einwand gegen ein pauschales `FieldSpec.required` ist im
Ticket uebernommen und begruendet: `FieldSpec` beschreibt dynamische
Metadaten einer Quelle, Pflichtfelder sind eine Eigenschaft des Vertrags.

Gemessen und im Ticket tabelliert: `price`, `currency` und `as_of` sind in
`Quote` **laengst Pflicht** — Mikes Vorgabe dazu ist bereits erfuellt.
Fehlend sind genau `Resolved.name` und `Resolved.instrument_type`; beide hat
Mike inzwischen ausdruecklich zu Pflichtfeldern erklaert.

**Und eine Vorbedingung, die du beachten solltest:** Mike hat nachgefragt,
was mit ETC und Krypto ist. Das Vokabular kennt heute nur `etf` und `stock`.
`instrument_type` zur Pflicht zu machen, **bevor** das Vokabular reicht,
erzwingt eine Luege — ein ETC waere dann „stock" oder „etf", und beides ist
falsch. T-38 empfiehlt deshalb eine **offene** Aufzaehlung (wie sie der
Vertrag fuer `source` schon kennt) und trennt Krypto/Index/Anleihe
ausdruecklich ab: Die scheitern nicht am Vokabular, sondern an der
Identitaet `(ticker, mic)` — das ist T-31.

**Nicht geaendert**, wie von dir bestaetigt: `exchange` und `currency`
bleiben ohne gemessenen Ausfall aus `KEEP_IF_UNKNOWN` heraus.

**Zahlen:** 806 Backend gruen / 29 skipped, 8 echte Integrationstests, 257
Plugin-Vertrag, 271 Dashboard, `vue-tsc` sauber, Ruff sauber,
`./_tickets/T-35-smoke.sh --run` 16/16 gegen die echten Quellen.

