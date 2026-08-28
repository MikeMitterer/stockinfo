# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `codex_reviewing`
- `ticket`: `T-35-ui-abnahme-am-laufenden-stack.md`
- `handoff_commit`: `405d659`
- `review_round`: `1`
- `owner`: `codex`
- `updated_at`: `2026-08-28`
- `last_reviewed_ticket`: `T-23-plugin-registry.md`
- `last_reviewed_commit`: `a9e49f9`
- `last_reviewed_round`: `6`
- `workstream`: `ui_live_acceptance`
- `priority_chain`: `T-35-ui-abnahme-am-laufenden-stack.md`
- `priority_ticket`: `T-35-ui-abnahme-am-laufenden-stack.md`

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

- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Review-Muster: `CLAUDE-REVIEW-PATTERNS.md`.
- Übergabe- und Scheduler-Regeln: `CODEX-REVIEW-AUTOMATION.md` und
  `CODEX-IN-CONTEXT-SCHEDULER.md`.

## INBOX → Claude

_Keine offene Nachricht._


## OUTBOX → Codex

### T-35 · Runde 7 · fuenf Befunde aus dem ersten Browserlauf

Commit `405d659`. **Bitte diesmal Aenderungen pruefen, nicht Befunde
sammeln** — Mike hat waehrend des Laufs ausdruecklich Reparieren beauftragt
(„Name — leer, ist schon mal falsch", „Ja, Fehlermeldung ist zu generisch!").
Die Verify-Matrix und alle fuenf Befunde stehen vollstaendig in
`T-35-ui-abnahme-am-laufenden-stack.md` unter „Auflösung".

Der Lauf lief im Browser gegen den freigegebenen MVP, mit der von Mike
vorgegebenen Kette (openfigi → yahoo-search, justetf → yfinance) und einer
eigenen Datenbank; `data/stockinfo.db` wurde nicht angefasst.

**Was ich fuer die wichtigsten Pruefpunkte halte:**

1. **`yahoo-search` war kaputt, nicht nur unkonvertiert.** Sie trug die
   Core-Signaturen, bekam aber den `ResolverAdapter`. `handles()` sagte
   faelschlich `True`, dann flog `AttributeError`, und `CompositeResolver`
   faengt nichts ab: **jede von OpenFIGI nicht aufloesbare ISIN war ein 500**.
   Behoben mit einer Rollenhuelle; **der Adapter blieb unangetastet**. Prueft
   bitte, ob der neue strukturelle Waechter
   (`test_jede_eingebaute_quelle_spricht_in_jeder_rolle_den_vertrag`) die
   Klasse wirklich abdeckt oder nur diesen Fall.

2. **`FigiMatch` ist eine Signaturaenderung an `map_isin`.** Sie beruehrt
   `app/resolver.py` und fuenf Test-Doubles. Bitte gegenlesen, ob die
   Gattungs-Tabelle `_FIGI_TYPES` zu streng oder zu grosszuegig ist — sie
   laesst Unbekanntes bewusst auf `None`, weil ein geratenes `"stock"` die
   ETF-Anreicherung wieder still abschaltete.

3. **`KEEP_IF_UNKNOWN` in `app/repository.py`** gilt **nur beim
   Aktualisieren**. Mein erster Anlauf legte sie auch auf das Anlegen, und
   die beiden Plugin-Durchstiche sind sofort gefallen. Bitte pruefen, ob
   `exchange` und `currency` dieselbe Behandlung braeuchten — ich habe den
   Umfang bewusst auf `name` und `type` begrenzt, weil nur die gemessen
   kaputt waren.

4. **`quotes.py` antwortet jetzt typisiert** (`instrument_not_found` statt
   deutschem Fliesstext). Das aendert den Antwortkoerper von drei
   404-Faellen. Kein Test und keine Fixture hat den alten Text gepinnt —
   bitte gegenpruefen, ob eine Vertragszusage daran haengt, die ich uebersehen
   habe. Die `502`-Faelle tragen weiter Fliesstext; er nennt dort die
   ausgefallenen Quellen (T-20 `#3`), deshalb habe ich sie nicht angefasst.

5. **`test_migration_reason_catalogue.py` sucht jetzt gezielt** im Block
   unter `migration`. Vorher nahm er den ersten `reason:`-Block der Datei und
   haette den neuen `errors.reason` geprueft — also einen Katalog, den er
   nicht meint. Die Kennungen aus `ErrorDetail` haben damit **noch keinen**
   Waechter; das ist Waechter `#3` aus T-34.

**Eine offene Frage, die ich ausdruecklich nicht entschieden habe.** Mike:
„das Plugin muss ganz klar eine Feldliste von Pflichtfeldern und von
optionalen Feldern liefern … Wie kann es sein dass name kein Pflichtfeld ist
— auch Codex soll die Aussage pruefen."

Geprueft: `FieldSpec` hat kein `required`, die Resolver-Rolle deklariert gar
keine Feldliste, `Resolved.name` ist `= None`. Alle drei Hauptbefunde sind
Ausprägungen desselben Lochs — ein Wert fehlte, und nichts hat gefragt. Meine
Fixes fuellen Werte, sie machen daraus keine Regel. Der Vorschlag (required
in `FieldSpec`, Pflichtfelder je Rolle, geprueft **am Ende der Kette** statt
je Quelle, Durchsetzung im Contract-Kit) steht in T-35 unter „Offen: eine
Frage an den Vertrag". Bitte Stellung nehmen — Umsetzung gehoert in ein
eigenes Ticket, vermutlich neben T-27a und T-34.

**Nebenbefund ohne Fix:** Der Anlegeweg des Dashboards laeuft ueber
`GET /quote/…`, nicht ueber `POST /instruments/intake`. Die typisierte
Auskunft dort kam beim Benutzer nie an. Ich habe den genommenen Weg
korrigiert, aber nicht entschieden, welcher der richtige ist.

**Zahlen:** 802 Unit-Tests, 8 Integrationstests gegen Yahoo/justETF/OpenFIGI,
257 Vertragstests, 259 Dashboard-Tests, `vue-tsc` sauber,
`./_tickets/T-35-smoke.sh --run` 15/15 (braucht Netz).


## An Mike · Zwischenstand
