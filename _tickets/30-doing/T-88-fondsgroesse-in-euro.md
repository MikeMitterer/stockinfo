# T-88 · Fondsgröße einheitlich in Mio. EUR

Die Detailansicht eines ETFs zeigte die Fondsgröße ohne Einheit „Mio.“. Beim
iShares Core MSCI World (`EUNL.DE`) stand „129,791 EUR“; der Fonds verwaltet
rund 129,8 Milliarden Euro. Dazu stand die Replikation ohne Leerzeichen da:
„Physical(Optimized sampling)“.

**Beispiel:** justETF schreibt „EUR 129,791 m“. Die Bibliothek
`justetf_scraping` liefert daraus `fund_size_eur = 129791.0`, laut ihrer Doku
„Fund size in EUR millions“. StockInfo war uneins über die Einheit:

| Stelle vorher | Einheit |
|---|---|
| manuelles Feld `InstrumentOverrides.fund_size` (`app/models.py`) | Mio. EUR, Grenze 2.000.000 |
| Detailkatalog `app/details.py`, `MetricEditor.vue` | Grenze 2.000.000 (passt zu Mio.) |
| justETF-Plugin, Adapter (`Unit.ABSOLUTE`), Vertrags-Fixtures (`89123000000.0`) | absolut |
| Anzeige | Zahl plus „EUR“, ohne „Mio.“ |

**Stand:** Gefunden am 2026-10-01 beim Erneuern der Screenshots. Mike:
„Erst Fehler beheben“, „Das Ticket kannst du gleich bei doing ablegen“ und
zur Einheit „Mio. EUR überall“. Coder `claude`, Verifier `codex`;
maßgeblich ist `STATUS.md`. Der Dateiname `…-in-euro` stammt aus dem ersten
Entwurf vor Mikes Einheiten-Entscheidung.

## Scope-Vertrag (Claude, 2026-10-01, nach Mikes Entscheidung)

Der erste Entwurf wollte absolute Euro. Beim Inventar zeigte sich der
Widerspruch oben; Mike entschied „Mio. EUR überall“. Damit wurde der
Vertrag berührt (Plugin-Einheit, Fixtures, Feldbeschreibung). Das ist ein
Scope-Checkpoint-Auslöser; die nötige Produktentscheidung hat Mike direkt
getroffen, deshalb ging die Arbeit ohne Verifier-Zwischenstopp weiter.

- **Ergebnis:** Die Fondsgröße hat überall eine Einheit: Mio. EUR. Die
  Detailansicht zeigt „129,791 million EUR“ bzw. „129.791 Mio. EUR“. Die
  Replikation steht als „Physical (Optimized sampling)“ da.
- **Fachliche Änderungen (3):**
  1. Einheit: Katalog (`app/details.py`) `millions`; justETF-Plugin und
     Adapter `Unit.MILLIONS`. Der Plugin-Vertrag erhält `MONEY_UNITS`
     (`ABSOLUTE`, `MILLIONS`); beide verlangen eine Währung. App, Plugin und
     Vertragsprüfsuite nutzen diese eine Menge.
  2. Anzeige: ein Katalogtext `details.amountMillions` für alle drei
     Anzeigewege (`DetailEditor`, `MetricValue`, `MetricEditor`); die
     flachen Altfelder nutzen `utils/fundSize.ts` mit EUR.
  3. Replikation: `JustEtfProvider` setzt das fehlende Leerzeichen vor „(“.
- **Vertrag:** `contract/core-contract.json` beschreibt `fund_size` als
  Millionen; drei Fixtures von `89123000000.0` auf `89123.0`.
- **Budget geplant / tatsächlich:** Produktdateien 3 / 12 (app 4,
  plugin_api 2, dashboard 6); Test-/Doku-/Vertragsdateien 4 / 15 (Tests 8,
  READMEs 2, Vertrag 4, Screenshot 1); Diff-Zeilen 200 / 249. Grund: Mikes
  Einheiten-Entscheidung betrifft Vertrag, Plugin-Paket und alle drei
  Anzeigewege.
- **Nicht-Ziele:** keine Datenmigration (Entwicklungsstand; gespeicherte
  justETF-Werte stehen schon in Millionen), keine Änderung an StockPortfolio,
  keine andere Quelle.

### Akzeptanzkriterien

- [ ] Die Fondsgröße hat in Katalog, Plugin, Adapter, Vertrag und Anzeige
      dieselbe Einheit: Mio. EUR.
- [ ] Ein Betrag in Millionen verlangt eine Währung (App und Vertragsprüfsuite).
- [ ] Die Detailansicht zeigt „129,791 million EUR“ / „129.791 Mio. EUR“.
- [ ] Die Replikation enthält das Leerzeichen vor der Klammer.
- [ ] Doku-Abgleich für `README.md`, `docker/README.md` und `contract/`.

### Side-Effects

StockPortfolio liest `fund_size` (`frontend/src/api/types.ts`,
`normalizers.ts`) und zeigt es in keiner `.vue`-Datei an. Der Wert kam schon
immer in Millionen; nur StockInfos Vertrags-Fixtures sagten „absolut“.
StockPortfolio führt eine eigene Kopie der Fixtures unter
`frontend/tests/fixtures/stockinfo/`; der Abgleich auf `89123.0` gehört ins
StockPortfolio-Board.

## Übergabe Runde 1 (Claude, 2026-10-01)

Prüfgegenstand: `67c86f8` gegen `master` (`f268ced`); darin `20b673a`
(Umsetzung) und `67c86f8` (Testwerte im Vertragstest nachgezogen).

### Verify

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | Einheit über alle Stellen verfolgen (`git grep fund_size`, `ABSOLUTE`, `2_000_000`) | Nirgends mehr „absolut“ für die Fondsgröße; Grenzen passen zu Millionen. Coder-Suche nach `fund_size` neben `ABSOLUTE`/„absolut“ und nach `1_200_000_000` über `app`, `tests`, `plugin_api`, `dashboard`, `contract`: einziger Treffer ist der Docstring des Mutantentests, der bewusst beide Einheiten prüft | ⚠️ B1 |
| 2 | `.venv/bin/python -m pytest -q` und `cd plugin_api && ../.venv/bin/python -m pytest -q` | grün | ✅ |
| 3 | `cd dashboard && npx vitest run && npx vue-tsc -b && npx eslint src tests` | grün | ✅ |
| 4 | Detailansicht im Browser (Temp-Datenbank, ETF aufklappen, deutsch und englisch) | „129,791 million EUR“ / „129.791 Mio. EUR“, „Physical (Optimized sampling)“ | ◑ |
| 5 | Bezeichner-Inventar (Python `ast`, TS-Compiler-API) über die geänderten Dateien | nur englische Bezeichner | ⚠️ B2 |
| 6 | Doku- und Vertragsabgleich | README, Docker-README und `contract/` nennen Millionen; Docker-Hub-Vorschau unter 25.000 Bytes | ✅ |

**Coder-Belege:**

- **#2:** Backend 1252 passed, 35 skipped; Plugin-Vertrag 324 passed,
  1 skipped; Ruff ohne Befund.
- **#3:** Dashboard 52 Dateien, 393 Tests grün; `vue-tsc -b` und ESLint ohne
  Befund. Der Stacktrace „useBackups.create boom“ im Lauf ist ein gewollter
  Fehler aus einem vorhandenen Test.
- **#4:** Echte StockInfo-Instanz mit Temp-Datenbank im Scratchpad, Dashboard
  aus dem Branch in einen eigenen Ordner gebaut. API liefert für EUNL.DE
  `fund_size` 129791.0 mit `unit` `millions` und `currency` EUR. Screenshot
  `unraid/screenshots/detail-area.png` zeigt „129,791 million EUR“ und
  „Physical (Optimized sampling)“. Die deutsche Anzeige deckt der
  Komponententest ab.
- **#5:** `ast`-Inventar (66 Namen in den geänderten Python-Dateien) und
  TS-Compiler-Inventar der sieben geänderten TS-/Vue-Dateien: alle englisch.
- **#6:** Docker-Hub-Vorschau 8.784 UTF-8-Bytes.

**Doku-Abgleich:** `README.md` (Quellentabelle, justETF: „fund size (in
millions of EUR)“) und `docker/README.md` (Funktionsliste) sagen dasselbe.
`unraid/README.md` nennt die Fondsgröße nicht und bleibt unverändert.
`contract/core-contract.json` beschreibt beide `fund_size`-Felder als
Millionen; Quellenwerte in EUR, manuelle Werte in der eingegebenen Währung.

Kein Merge, kein Push, kein Docker-Hub- oder Unraid-Update.

## Verifier-Prüfung · Runde 1 (Codex, 2026-10-01)

**Prüfstand:** `67c86f8` gegen `f268ced`. Seit der Übergabe wurden nur
`_tickets/`-Dateien committet. Ergebnis: **`changes_requested`**; keine
technische oder menschliche Abnahme. Der Review verändert keinen Produktcode.

### Blockierende Befunde

1. **B1 · Falsche Währung bei manuell erfasster Fondsgröße.**
   `dashboard/src/utils/fundSize.ts:14` setzt für die flachen Anzeigen
   stets `EUR`; `MetricValue.vue:68` und `MetricEditor.vue:136` nutzen
   diesen Text. Der Vertrag in `contract/core-contract.json` erlaubt für
   manuelle `fund_size` die eingegebene Währung, und `DetailEditor.vue`
   zeigt diese Währung auch an. Gegenprobe mit echtem `CachedQuoteService`
   und temporärer Datenbank: Ein Instrument mit `fund_currency=USD` nimmt
   `set_overrides('EUNL.DE', {'fund_size': 30})` an. Der Summary-Wert ist
   `flat_fund_size=30`, das Detail hat `manual_currency=USD`; die flache
   Anzeige macht daraus „30 Mio. EUR“. Auch `validate_input` akzeptiert
   `DetailInput(value=30, currency='USD')` für `fund_size`. Bitte die
   Währung für alle Anzeigewege und den Vertrag mit Mikes Entscheidung
   „Mio. EUR überall“ in Einklang bringen und den manuellen USD-Pfad
   gezielt prüfen.
2. **B2 · Deutsche Bezeichner in berührten Testdateien.** Die
   Projektregel verlangt englische Bezeichner ausnahmslos auch in Tests;
   bereits vorhandene Namen ziehen beim Berühren der Datei mit. Das
   Python-`ast`-Inventar über alle elf geänderten Python-Dateien fand
   unter anderem `_StummeQuelle`, `_SchwaetzerischeQuelle` und
   `_HalbherzigeZone` in
   `plugin_api/tests/test_contract_mutants.py:96,115,373` sowie
   `_KontextabhaengigerEnricher`, `aufrufe`, `spion`, `politik`,
   `faelle`, `erwartet`, `kaputt`, `europaeisch`, `uebersee`,
   `ausgefallen` und `ersatz` in `tests/test_providers.py`. Bitte das
   vollständige Inventar dieser berührten Dateien bereinigen und erneut
   per AST prüfen. Deutsche Testfunktionsnamen bleiben nach Projektregel
   zulässig. Das TS-Compiler-Inventar der geänderten TS-/Vue-Dateien
   fand keine entsprechende Abweichung.

### Nachweise und Grenzen

- **Verify #1:** Katalog, justETF-Plugin, Adapter, `MONEY_UNITS`,
  Maximalwert und Vertrags-Fixtures nutzen Millionen; B1 durchbricht
  jedoch die geforderte einheitliche Anzeige.
- **Verify #2:** Backend vollständig **1252 passed, 35 skipped**;
  Plugin-API **324 passed, 1 skipped**. Der erste Backend-Lauf in der
  Sandbox scheiterte an DNS und Paketindex, der erneute vollständige Lauf
  mit freigegebenem Netzwerkzugang war grün.
- **Verify #3:** Dashboard **393 passed**; `vue-tsc -b` und
  `eslint src tests` bestanden.
- **Verify #4:** Das neue Bild `unraid/screenshots/detail-area.png`
  zeigt den englischen Betrag und „Physical (Optimized sampling)“.
  Der deutsche Betrag ist im Komponententest belegt, nicht in einem
  unabhängigen deutschen Browserlauf. Die manuelle USD-Konstellation
  bleibt durch B1 falsch.
- **Verify #5:** Python-`ast` und TS-Compiler-API über die berührten
  Dateien ausgeführt; B2 ist der Befund. Der normale Ruff-Lauf war grün.
- **Verify #6 / Doku-Abgleich:** `README.md` und `docker/README.md`
  beschreiben justETF-Werte in Millionen EUR übereinstimmend;
  `unraid/README.md` enthält keine Fondsgrößen-Zusage. Der Vertrag
  beschreibt Quellenwerte in EUR und manuelle Werte in der Eingabewährung;
  B1 betrifft dessen Umsetzung. Die Docker-Hub-Vorschau bestand mit
  **8.784 UTF-8-Bytes**. `git diff --check` bestand.

**Standard-Riegel:** Gelesen wurde
`/Users/macminipro/.codex/skills/code-standards/SKILL.md` mit
`references/architecture.md`, `frontend.md`, `python.md`, `quality.md`
und `documentation.md`.

| Referenzgruppe | Ergebnis und Beleg |
|---|---|
| Architektur, DRY, Funktionen und Namen | ⚠️ B2; DRY-Suche über den Diff und berührten Umgebungscode: `MONEY_UNITS` ist die gemeinsame Geld-Einheitenmenge, `fundSizeText` bündelt die beiden flachen Anzeigewege. Keine weitere doppelte Fachregel gefunden. |
| BashLib, Bash-Fehler und Exit-Codes | ➖ nicht berührt |
| Skript-CLI, Hilfe und ANSI-Ausgabe | ➖ nicht berührt |
| TypeScript, Vue und i18n | ⚠️ B1; neuer Betragstext kommt aus den DE/EN-Katalogen, die flache Währung ist jedoch fest verdrahtet. Typprüfung und ESLint bestanden. |
| Python, FastAPI und Webhooks | ⚠️ B2 in zwei berührten Python-Testdateien; Backend-Suite und normaler Ruff-Lauf bestanden. |
| Datenbanken und Persistenzgrenzen | ➖ keine produktive DB-/Persistenzänderung im Diff |
| Fehler, Logging und Tests | ✅ volle Suiten und gezielte Service-Gegenprobe mit temporärer Datenbank; kein neuer stiller Fehlerpfad im Diff gefunden. |
| Markdown und Inhaltsverzeichnisse | ✅ beide README-Aussagen und Vertragsbeschreibung gegen den Diff geprüft; Docker-Hub-Vorschau bestanden. |

**Offene Board-Übernahme:** Die bereits in `STATUS.md` dokumentierte
Activity-/Observer-/Lessons-Übernahme aus Paketfassung `df699dd1`
bleibt ein getrennter Board-Schritt für die zuständige schreibberechtigte
Instanz. Sie ändert dieses Reviewurteil nicht.

## Nacharbeit Runde 2 (Claude, 2026-10-02)

Prüfgegenstand: `12fac6c` gegen `67c86f8` (Nacharbeit) und gegen `f268ced`
(Gesamtstand).

- **B1 · Währung:** Mike entschied auf Rückfrage „Eingabewährung
  behalten“: Die Fondsgröße steht immer in Millionen, die Währung folgt der
  Quelle (justETF: EUR) oder der manuellen Eingabe. `utils/fundSize.ts`
  liest sie über `fundSizeCurrency(item, 'effective' | 'manual')` aus dem
  `details`-Eintrag; EUR gilt nur ohne `details`. `MetricValue.vue` nutzt die
  wirksame Währung für den Wert und die manuelle für den Hinweistext,
  `MetricEditor.vue` die manuelle. Neue Tests: manuelle Fondsgröße in USD
  in beiden Komponenten. Der Vertragstext („a manual value uses the
  currency entered with it“) galt schon und bleibt.
- **B2 · Bezeichner:** In `tests/test_providers.py` und
  `plugin_api/tests/test_contract_mutants.py` sind alle deutschen Klassen,
  Variablen, Parameter und Attribute englisch: `_SilentSource`,
  `_ChattySource`, `_HalfheartedZone`, `_ContextDependentEnricher`,
  `invocations`, `spy_overview`, `policy`, `cases`,
  `expected_accumulating`, `broken`, `european`, `overseas`, `failed`,
  `fallback`, Attribute `asked` und `fetch_context`. Erneutes
  `ast`-Inventar beider Dateien einschließlich `self`-Attributen und
  Keyword-Argumenten: nur englische Namen. Verbliebene Treffer für
  „gefragt“ sind Prosa (Kommentar, Meldungstext).
- **Verify #4, deutscher Browserlauf:** Temp-Instanz mit dem Stand
  `12fac6c`, Dashboard aus dem Branch gebaut, Chrome sichtbar mit
  `de-DE`. Belege neben dem Ticket:
  [EUNL.DE](T-88-browser-de-eunl.png) zeigt „129.791 Mio. EUR“ und
  „Physical (Optimized sampling)“;
  [VTI](T-88-browser-de-vti-usd.png) (US-ETF ohne justETF, Fondsgröße von
  Hand per `PATCH …/details` mit 30 USD) zeigt „30 Mio.“ mit Währungsauswahl
  USD. API dazu: flach `fund_size` 30, Detail `unit` `millions`,
  `currency` USD, `origin` manual.
- **Läufe:** Backend 1252 passed, 35 skipped; Plugin-Vertrag 324 passed,
  1 skipped; Ruff ohne Befund; Dashboard 52 Dateien, 395 Tests;
  `vue-tsc -b` und ESLint ohne Befund.
- **Umfang:** Gesamtstand gegen `f268ced` 27 Dateien, 304 Zeilen hinzu,
  88 entfernt (ohne `_tickets/`). Mehr als in Runde 1, weil B2 vorhandene
  deutsche Bezeichner in zwei berührten Testdateien umbenennt.

### Bitte an Codex: Praxisprüfung der Währungsentscheidung

Mike: „Die Frage bezüglich Eintragung der Fondsgröße in Euro oder USD oder
der Basiswährung – lass meine Entscheidung auch nochmal von Codex
verifizieren, ob das in der Praxis standhalten kann.“ Bitte bewerten, ob
„Millionen, Währung = Eingabewährung“ im Alltag trägt, verglichen mit
„nur EUR“ und „Basiswährung des Fonds (`fund_currency`)“. Prüfpunkte etwa:
Vergleichbarkeit zwischen Instrumenten, Sortierung und Filter in
StockInfo und StockPortfolio, was Factsheets typischerweise angeben,
Verhalten, wenn justETF später einen EUR-Wert über einen manuellen
USD-Wert legt (Schatten-Hinweis), Aufwand für den Nutzer. Das Ergebnis
geht als Empfehlung an Mike; es ist kein Blocker dieser Runde, außer
Codex findet einen konkreten Fehler im umgesetzten Verhalten.

### Auswirkung auf StockPortfolio (geprüft mit dessen Code)

StockPortfolios `projectDetailFields` mit StockInfos echten Antworten
aufgerufen (`vite-node`, Skript im Scratchpad, StockPortfolio unverändert):

| | vor T-88 (`absolute`) | nach T-88 (`millions`) |
|---|---|---|
| EUNL.DE Fondsgröße | 129.791,00 € (falsch) | 129.791,00 € million |
| VTI manuell 30 USD | 30,00 $ | 30,00 $ million |

Der Fehler schlug also auf StockPortfolio durch; T-88 behebt ihn dort ohne
Codeänderung, weil StockPortfolio die Einheit `millions` schon kennt.
Nachzuziehen in StockPortfolio: Fixture-Kopie (T-78), kurzzeitiges „—“ für
in IndexedDB gespeicherte Kurse mit alter Einheit bis zum nächsten Abruf,
Formatierung „129.791,00 € Mio.“. Erfasst in StockPortfolio T-79.

## Verifier-Prüfung · Runde 2 (Codex, 2026-10-02)

**Prüfstand:** `12fac6c` gegen `67c86f8`, Gesamtstand gegen `f268ced`.
Seit dem Produktcommit wurden nur `_tickets/`-Dateien committet; der
Arbeitsbaum war zu Beginn der Prüfung nach dem Übergabecommit `1c87ab1`
sauber. Ergebnis: **`changes_requested`** wegen B3 und B4. B1 und B2 aus
Runde 1 sind behoben. Keine technische oder menschliche Abnahme.

### Befunde

1. **B1 behoben · Währung der Anzeige.** `fundSizeCurrency()` liest
   `details.fund_size.currency` für den wirksamen Wert und
   `manual_currency` für den verdeckten oder bearbeiteten manuellen Wert.
   Gegenprobe mit demselben Instrument: wirksam EUR, manuell USD; der
   Helfer liefert getrennt EUR und USD. Die beiden Komponenten verwenden
   die passende Variante. Die neuen USD-Komponententests, der deutsche
   VTI-Beleg mit 30 Mio. und USD-Auswahl sowie der EUNL-Beleg mit
   „129.791 Mio. EUR“ stimmen damit überein. Die Bilder wurden unabhängig
   angesehen; einen eigenen Browserlauf habe ich nicht behauptet.
2. **B2 behoben · Python-Bezeichner.** Das vollständige `ast`-Inventar der
   beiden betroffenen Dateien einschließlich Klassen, Funktionen,
   Parametern, lokalen Namen, Attributen und Keyword-Namen umfasst 135
   beziehungsweise 156 eindeutige Bezeichner. Die deutschen Namen aus
   Runde 1 sind ersetzt; deutsche Testfunktionsnamen sind ausdrücklich
   erlaubt. Die gezielten Tests dazu bestehen.
3. **B3 blockierend · TypeScript-Namensschema.** Die Projektregel erhält
   das Namensschema je Sprache; `code-standards` verlangt `camelCase` für
   TypeScript-Variablen. Das Compiler-API-Inventar der fünf in Runde 2
   geänderten TS-/Vue-Dateien fand in
   `dashboard/src/utils/fundSize.ts:12` den neu benannten
   `DEFAULT_FUND_SIZE_CURRENCY` sowie in den berührten Komponenten
   `FIELD_KIND`, `NUMBER_MAX` und zweimal `DIGITS`
   (`MetricEditor.vue:74,119,122`, `MetricValue.vue:63`). Bitte diese
   lokalen Konstanten einheitlich in `camelCase` umbenennen und die fünf
   Dateien erneut vollständig inventarisieren. Der zusätzliche Ruff-Lauf
   mit `I,Q` meldet in den beiden berührten Python-Testdateien je einen
   schon vor Runde 2 vorhandenen `I001`-Importblock; diese mechanische
   Importsortierung bitte im selben Standardschritt mitziehen. Der normale
   Ruff-Lauf erfasst `I,Q` nicht.
4. **B4 blockierend · aktiver Scope widerspricht Mikes neuer
   Entscheidung.** Titel, Ergebnis, Anzeigeweg 2 und Akzeptanzkriterium 1
   am Anfang dieses Tickets sagen weiter „Mio. EUR überall“ beziehungsweise
   flache Felder mit EUR. Die Nacharbeit und die aktuelle Entscheidung
   erlauben ausdrücklich eine manuelle Fondsgröße in USD. Auch der
   Side-Effects-Abschnitt legt nahe, StockPortfolio zeige die Größe nicht,
   während die Nacharbeit die sichtbare Ausgabe über
   `projectDetailFields` belegt. Bitte die aktuellen Ergebnis- und
   Abnahmeaussagen auf **Millionen mit Quell- oder Eingabewährung** ziehen;
   die ursprüngliche Entscheidung und Runde 1 dürfen als Historie
   erkennbar bleiben. `README.md` und `docker/README.md` beschreiben
   justETF-Quellwerte weiterhin zutreffend in EUR; der Plugin-Vertrag
   nennt für manuelle Werte bereits die Eingabewährung.

### Praxisempfehlung an Mike zur Währungsentscheidung

**Eingabewährung beibehalten.** Ein manueller Wert bleibt dadurch in der
Währung seiner Quelle, ohne stillschweigende Umrechnung. Ein nur auf EUR
beschränktes Feld würde bei einem USD-Factsheet eine Umrechnung samt
Wechselkurs und Stichtag vom Nutzer verlangen. Die Fondsbasiswährung ist
keine zuverlässige Anzeigewährung für die Größe: iShares nennt für
IE00B4L5Y983 USD als Fondswährung und berichtet Fondsvermögen in USD,
während justETF für denselben Fonds die Größe in EUR ausweist.
Vanguard weist VTI-Fondsvermögen ebenfalls in USD aus.
Belege: [iShares-Produktdaten](https://www.ishares.com/uk/individual/en/products/251882/ishares-core-msci-world-ucits-etf),
[justETF-Profil](https://www.justetf.com/de/etf-profile.html?isin=IE00B4L5Y983),
[Vanguard-Factsheet](https://workplace.vanguard.com/assets/corp/fund_communications/pdf_publish/us-products/fact-sheet/F0970.pdf).

Die Kehrseite ist fehlende direkte Vergleichbarkeit: 30 Mio. USD und
30 Mio. EUR dürfen ohne Umrechnung weder als gleicher Betrag behandelt
noch roh nach Größe sortiert werden. StockInfos Dashboard verwendet
`fund_size` derzeit nur für Anzeige und Bearbeitung, nicht zum Sortieren
oder Filtern (`rg fund_size dashboard/src`). Eine künftige
größenbasierte Rangliste braucht eine ausdrücklich festgelegte
Vergleichswährung mit Kurs und Stichtag. Bei einem EUR-Quellenwert, der
eine manuelle USD-Eingabe verdeckt, sollen wirksamer Wert und Hinweis
jeweils ihre eigene Währung zeigen; die Runde-2-Logik trennt diese
Währungen. Diese Empfehlung ist eine technische Bewertung und keine
menschliche Abnahme.

### Verify und Standards

- **#1:** ✅ Katalog, Plugin, Adapter und Vertrag führen Millionen; B1
  ist korrigiert. Der aktuelle Scope-Text muss mit B4 nachziehen.
- **#2:** ✅ Backend **1252 passed, 35 skipped**; Plugin-API
  **324 passed, 1 skipped**. Gezielt: 61 Backend- und 24
  Plugin-Mutantentests bestanden.
- **#3:** ✅ Dashboard **395 passed**; gezielt 37 Komponententests,
  `vue-tsc -b` und `eslint src tests` bestanden.
- **#4:** ✅ Die deutschen EUNL- und VTI-Belegbilder wurden visuell
  geprüft; der frühere englische Beleg steht in Runde 1. Kein eigener
  Browserlauf in dieser Runde.
- **#5:** ⚠️ B3; Python-`ast` über die beiden Testdateien ohne deutsche
  Nicht-Testbezeichner, TypeScript-Compiler-API über alle fünf geänderten
  TS-/Vue-Dateien mit den genannten Schemaabweichungen.
- **#6 / Doku-Abgleich:** ⚠️ B4 im aktuellen Tickettext. Die beiden
  READMEs und `contract/core-contract.json` widersprechen der
  Quellen-/Eingabewährung nicht; `unraid/README.md` enthält weiterhin
  keine Fondsgrößenaussage. Die Docker-Hub-Vorschau war in Runde 1 mit
  8.784 UTF-8-Bytes unter der Grenze; `docker/README.md` blieb seither
  unverändert. `git diff --check` für Nacharbeit und Gesamtstand bestand.

**Standard-Riegel:** Gelesen wurde
`/Users/macminipro/.codex/skills/code-standards/SKILL.md` mit
`references/architecture.md`, `frontend.md`, `python.md`, `quality.md`
und `documentation.md`.

| Referenzgruppe | Ergebnis und Beleg |
|---|---|
| Architektur, DRY, Funktionen und Namen | ⚠️ B3; `fundSizeCurrency` bündelt die Währungswahl, keine neue doppelte Fachregel im Nacharbeitsdiff gefunden. |
| BashLib, Bash-Fehler und Exit-Codes | ➖ nicht berührt |
| Skript-CLI, Hilfe und ANSI-Ausgabe | ➖ nicht berührt |
| TypeScript, Vue und i18n | ⚠️ B3; Komponenten nutzen den gemeinsamen i18n-Text mit getrennten Währungen, Typprüfung und ESLint bestehen. |
| Python, FastAPI und Webhooks | ⚠️ zwei bereits vorhandene `I001`-Importblöcke in den berührten Tests; B2 ist per AST und Tests behoben. |
| Datenbanken und Persistenzgrenzen | ➖ keine produktive Persistenzänderung im Nacharbeitsdiff |
| Fehler, Logging und Tests | ✅ vollständige Suiten, gezielte USD-Tests und kontrastierende EUR/USD-Helfer-Gegenprobe. |
| Markdown und Inhaltsverzeichnisse | ⚠️ B4; aktueller Scope und Akzeptanztext müssen die neue Entscheidung wiedergeben. |

**Offene Board-Übernahme:** Activity-/Observer-/Lessons-Abgleich aus der
lokalen Paketfassung `df699dd1` bleibt getrennt offen. Er erweitert das
T-88-Review nicht. Kein Produktcode, keine menschliche Abnahme und kein
Merge oder Push durch Codex.
