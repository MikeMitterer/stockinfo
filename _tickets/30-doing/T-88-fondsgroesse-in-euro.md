# T-88 · Fondsgröße einheitlich in Millionen

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
zur Einheit „Mio. EUR überall“. In Runde 2 präzisierte Mike die Währung:
„Eingabewährung behalten“. Gültig ist damit: **Millionen überall; die
Währung ist EUR bei justETF-Werten und die Eingabewährung bei manuellen
Werten.** Codex' Praxisprüfung in Runde 2 empfiehlt, dabei zu bleiben.
Coder `claude`, Verifier `codex`; maßgeblich ist `STATUS.md`. Der Dateiname
`…-in-euro` stammt aus dem ersten Entwurf vor Mikes Entscheidungen.

## Scope-Vertrag (Claude, 2026-10-01, nach Mikes Entscheidung)

Der erste Entwurf wollte absolute Euro. Beim Inventar zeigte sich der
Widerspruch oben; Mike entschied „Mio. EUR überall“. Damit wurde der
Vertrag berührt (Plugin-Einheit, Fixtures, Feldbeschreibung). Das ist ein
Scope-Checkpoint-Auslöser; die nötige Produktentscheidung hat Mike direkt
getroffen, deshalb ging die Arbeit ohne Verifier-Zwischenstopp weiter.

- **Ergebnis:** Die Fondsgröße steht überall in Millionen, mit ihrer
  Währung: EUR bei justETF, die Eingabewährung bei manuellen Werten. Die
  Detailansicht zeigt „129,791 million EUR“ bzw. „129.791 Mio. EUR“, eine
  manuelle Angabe etwa „30 Mio. USD“. Die Replikation steht als
  „Physical (Optimized sampling)“ da.
- **Fachliche Änderungen (3):**
  1. Einheit: Katalog (`app/details.py`) `millions`; justETF-Plugin und
     Adapter `Unit.MILLIONS`. Der Plugin-Vertrag erhält `MONEY_UNITS`
     (`ABSOLUTE`, `MILLIONS`); beide verlangen eine Währung. App, Plugin und
     Vertragsprüfsuite nutzen diese eine Menge.
  2. Anzeige: ein Katalogtext `details.amountMillions` für alle drei
     Anzeigewege (`DetailEditor`, `MetricValue`, `MetricEditor`); die
     flachen Felder lesen die Währung über `utils/fundSize.ts` aus dem
     `details`-Eintrag (wirksam bzw. manuell), EUR nur ohne `details`.
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
      dieselbe Einheit: Millionen. Die Währung ist EUR bei justETF und die
      Eingabewährung bei manuellen Werten, in allen Anzeigewegen.
- [ ] Ein Betrag in Millionen verlangt eine Währung (App und Vertragsprüfsuite).
- [ ] Die Detailansicht zeigt „129,791 million EUR“ / „129.791 Mio. EUR“;
      eine manuelle Angabe erscheint in ihrer Währung, etwa „30 Mio. USD“.
- [ ] Die Replikation enthält das Leerzeichen vor der Klammer.
- [ ] Doku-Abgleich für `README.md`, `docker/README.md` und `contract/`.

### Side-Effects

StockPortfolio zeigt die Fondsgröße in den Zusatzinformationen einer
Position über den generischen `details`-Eintrag (`projectDetailFields`);
das flache Feld `fund_size` nutzt es nicht. Mit StockPortfolios Code
geprüft: Vor T-88 erschien dort „129.791,00 €“ (falsche Größenordnung),
nach T-88 „129.791,00 € Mio.“, eine manuelle USD-Angabe als „30,00 $ Mio.“.
StockPortfolio braucht dafür keine Codeänderung. Nachzuziehen dort: die
Fixture-Kopie unter `frontend/tests/fixtures/stockinfo/` auf `89123.0`
(StockPortfolio T-78) sowie Darstellung und kurzzeitiges „—“ aus dem
IndexedDB-Cache (StockPortfolio T-79).

### Verify

Aktuelle Statusmatrix; sie stand bis Runde 3 unter „Übergabe Runde 1“ und
wird über alle Runden fortgeschrieben.

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | Einheit über alle Stellen verfolgen (`git grep fund_size`, `ABSOLUTE`, `2_000_000`) | Katalog, Plugin, Adapter und Anzeige nutzen Millionen; Quelle und manuelle Eingabe tragen ihre jeweilige Währung. Die Reststellen mit „Mio. EUR“ in aktueller Erklärung stehen unter #6/B5 | ✅ |
| 2 | `.venv/bin/python -m pytest -q` und `cd plugin_api && ../.venv/bin/python -m pytest -q` | grün | ✅ |
| 3 | `cd dashboard && npx vitest run && npx vue-tsc -b && npx eslint src tests` | grün | ✅ |
| 4 | Detailansicht im Browser (Temp-Datenbank, ETF aufklappen, deutsch und englisch) | EN-Beleg aus Runde 1, DE-Belege für EUNL und manuelle USD-Größe aus Runde 2; alle unabhängig visuell angesehen. Runde 3 ändert kein Anzeigeverhalten | ✅ |
| 5 | Bezeichner-Inventar (Python `ast`, TS-Compiler-API) über die geänderten Dateien | elf Python- und neun TS-/Vue-Dateien vollständig inventarisiert; keine deutschen Nicht-Testbezeichner oder `UPPER_SNAKE_CASE`-Variablen im TS-Scope | ✅ |
| 6 | Doku- und Vertragsabgleich | Vertrag und Docker-README korrekt; Root-README und aktuelle API-Beschreibung widersprechen manuellen USD-Werten (B5) | ⚠️ B5 |

## Review-Verlauf (neueste Runde zuerst)

Neue Übergaben, Nacharbeiten und Verifier-Prüfungen kommen direkt unter
diese Überschrift (Regel „Review-Verlauf — neueste Runde zuerst“ in
`.agents/AGENT-WORKFLOW.md`). Die Abschnittsüberschriften sind unverändert;
Links auf einzelne Runden gelten weiter.

## Verifier-Prüfung · Runde 3 (Codex, 2026-10-02)

**Prüfstand:** `8a3ae95` gegen `12fac6c`, Gesamtstand gegen `f268ced`.
Nach dem Handoff-Commit betrafen alle Commits nur `_tickets/`; der
Arbeitsbaum war sauber. Ergebnis: **`changes_requested`** wegen B5.
Mike hat während dieser Prüfung das Limit ausdrücklich von drei auf fünf
Review-Runden erhöht (`STATUS.md`). Keine technische oder menschliche
Abnahme.

### Befunde und offener Rest

1. **B3 behoben.** Die fünf lokalen TS-Konstanten sind `camelCase`.
   Compiler-API-Inventar über alle neun im Gesamtstand berührten
   TS-/Vue-Dateien: keine lokale `UPPER_SNAKE_CASE`-Deklaration und keine
   nichtenglischen Identifikatoren. Das Python-`ast`-Inventar über elf
   berührte Dateien umfasst Namen, Parameter, Funktionen, Klassen,
   Attribute und Keyword-Namen; die zwei weiteren deutschen Attribute
   sind englisch. Ruff mit `I` besteht im Root und separat im
   `plugin_api`-Paket; dessen Importkontext ist eigenständig. `Q000`
   begründet keinen Verstoß gegen die geltenden Projektstandards.
2. **B4 behoben.** Der aktive Tickettext nennt Millionen mit EUR für
   justETF und mit Eingabewährung für manuelle Werte. Die Nebenwirkung
   in StockPortfolio beschreibt den sichtbaren `details`-Eintrag und
   verweist auf T-78/T-79. Die alte EUR-Entscheidung ist als Historie
   gekennzeichnet.
3. **B5 blockierend · aktuelle Währungsbeschreibung.** Das Root-README
   behauptet unter „ETFs outside Europe“ in `README.md:88-91`, die App
   speichere Fondsgrößen in Millionen EUR. Der aktuelle Vertrag und die
   USD-Tests erlauben aber manuelle Millionen in der Eingabewährung.
   Die öffentliche Override-API dokumentiert das Feld ebenfalls falsch:
   `app/models.py:526-528` hat für `InstrumentOverrides.fund_size` die
   Beschreibung „Fondsvolumen in Mio. EUR“; die Modell-Schema-Gegenprobe
   liefert genau diesen Text. Der generische Katalog in
   `app/details.py:18-19` nennt EUR, obwohl er nur die Einheit
   `millions` festlegt. Bitte diese drei aktuellen Aussagen präzisieren
   und die beiden READMEs sowie den API-/Vertragsabgleich danach nochmals
   durchführen. `docker/README.md:71` bezieht sich konkret auf
   quellengelieferte ETF-Metadaten und ist zutreffend. Der Yahoo-Docstring
   in `app/providers/yfinance_etf_provider.py:32-34` beschreibt den
   gesonderten alten `QuoteResponse`-Pfad; daraus leite ich keinen
   zusätzlichen Änderungsauftrag ab.

**Restanalyse:** B5 ist der einzige offene Befund. Die drei Fundstellen
sind inhaltlich eng verwandt und ohne Produktentscheidung korrigierbar;
zuerst die öffentliche API-Beschreibung, dann Root-README und Katalogkommentar,
anschließend Schema-Gegenprobe, Doku-Abgleich und betroffene Tests. Claude
bearbeitet die Korrektur, Codex prüft sie in Runde 4 gezielt. Sie blieb
offen, weil Runde 1 die Einheitenumstellung und Runde 2 den Tickettext
prüften und beide Rollen die pauschalen EUR-Aussagen im Gesamtstand
übersahen. Mein eigener Runde-2-Doku-Befund war insoweit unvollständig.
Der Schaden ist eine falsche Anweisung an API- und README-Leser für den
bereits unterstützten manuellen USD-Fall. Es gibt keinen Hinweis auf einen
weiteren Funktionsfehler. Der ausdrückliche Nutzerauftrag erlaubt Codex
keine Produktdatei-Änderung; daher keine Verifier-Selbstheilung.

### Verify und Standards

- **#1:** ✅ Millionen als Einheit in Katalog, Plugin, Adapter und Anzeige;
  Währungen im Verhalten getrennt. Falsche Beschreibung unter #6/B5.
- **#2:** ✅ Backend **1252 passed, 35 skipped, 1 warning**; Plugin-API
  **324 passed, 1 skipped**.
- **#3:** ✅ Dashboard **52 Testdateien, 395 passed**; `vue-tsc -b` und
  `eslint src tests` ohne Befund.
- **#4:** ✅ Die unveränderten englischen und deutschen Browserbelege aus
  Runde 1/2 einschließlich manuellem USD-Fall sind visuell geprüft;
  Runde 3 ist verhaltensneutral. Kein eigener Browserlauf behauptet.
- **#5:** ✅ Python-`ast` für elf Dateien und TS-Compiler-API für neun
  Dateien; normaler Ruff-Lauf und `ruff --select I` in beiden
  Paketkontexten bestehen.
- **#6 / Doku-Abgleich:** ⚠️ B5. `README.md` ist zur manuellen Währung
  missverständlich, die Override-API-Beschreibung falsch;
  `docker/README.md` und `contract/core-contract.json` sind für ihren
  jeweiligen Gegenstand zutreffend. `unraid/README.md` enthält keine
  Fondsgrößenaussage. Docker-README blieb seit der Vorschau aus Runde 1
  unverändert (8.784 UTF-8-Bytes). `git diff --check` für Nacharbeit und
  Gesamtstand besteht.

**Standard-Riegel:** `code-standards/SKILL.md` und die passenden
Referenzen zu Architektur, Frontend, Python, Qualität und Dokumentation
wurden berücksichtigt. DRY, Zuständigkeit und i18n im Nacharbeitsdiff
ohne neuen Befund; TS/Python-Namensschema sowie Importsortierung bestehen
die vollständigen Inventare und Checks. Bash, Datenbanken, Konfiguration
und Persistenzverhalten wurden in Runde 3 nicht verändert. Die aktuelle
Dokumentation bleibt wegen B5 offen.

**Offene Board-Übernahme:** Activity-/Observer-/Lessons-Abgleich aus
Paketfassung `df699dd1` bleibt getrennt sichtbar. Codex änderte keinen
Produktcode und erteilte keine menschliche Abnahme; kein Merge oder Push.

## Nacharbeit Runde 3 (Claude, 2026-10-02)

Prüfgegenstand: `8a3ae95` gegen `12fac6c` (Nacharbeit) und gegen `f268ced`
(Gesamtstand). Vor der Übergabe habe ich den **gesamten** T-88-Stand nach
Standard und Doku geprüft, nicht nur die Befunde.

- **B3 · TS-Namen:** `DEFAULT_FUND_SIZE_CURRENCY` → `defaultFundSizeCurrency`,
  `DIGITS` → `twoDecimals` (MetricValue, MetricEditor), `FIELD_KIND` →
  `fieldKinds`, `NUMBER_MAX` → `numberMaxByField`. TS-Compiler-Inventar
  über alle neun berührten TS-/Vue-Dateien (Quellen und Tests): keine
  `UPPER_SNAKE_CASE`-Variablen mehr, keine deutschen Namen.
- **B3 · Importblöcke:** `I001` in allen berührten Python-Dateien behoben,
  nicht nur in den zwei genannten: `tests/test_providers.py`,
  `tests/test_app_plugins_contract.py`, `tests/test_open_details.py`,
  `tests/test_plugin_justetf_integration.py`,
  `plugin_api/src/stockinfo_plugin/testing/contracts.py`. Wichtig:
  `plugin_api/` ist ein eigenes Paket. Vom Projekt-Root aus hält Ruff
  `stockinfo_plugin` für fremd und verlangt in
  `plugin_api/tests/test_contract_mutants.py` das Entfernen der Leerzeile;
  aus `plugin_api/` heraus verlangt es sie. Die Datei gehört zum Paket,
  geprüft wird sie deshalb dort; dort ist sie sauber.
- **Vollständigkeit über B2 hinaus:** Das AST-Inventar über alle elf
  berührten Python-Dateien (Namen, Parameter, Klassen, Attribute) fand noch
  `_quelle` und `_europaeisch` in `tests/test_app_plugins_contract.py`;
  jetzt `_source` und `_european`.
- **Nicht geändert, `Q000`:** Ruff `Q` meldet einfache Anführungszeichen in
  `app/details.py` und `tests/test_open_details.py`. Beide Dateien sind
  durchgehend so geschrieben; weder `code-standards` noch die
  Ruff-Konfiguration des Projekts legen einen Anführungsstil fest. Kein
  Verstoß, daher kein Umbau ganzer Dateien.
- **Keine Prozesshistorie im Code:** Suche über alle hinzugefügten Zeilen
  außerhalb von `_tickets/` nach Ticketnummern, „Runde“, „Codex“, „Mike“,
  „Befund“: kein Treffer.
- **B4 · Tickettext:** Titel, Stand, Ergebnis, Änderung 2, Akzeptanzkriterien
  und Side-Effects beschreiben jetzt den gültigen Stand: Millionen überall,
  Währung EUR bei justETF und Eingabewährung bei manuellen Werten.
  StockPortfolios Nebenwirkung steht mit dem geprüften Befund aus
  StockPortfolios Code da (Zusatzinformationen über `details`, T-78 und
  T-79). „Mio. EUR überall“ bleibt nur als Historie stehen.
- **Doku-Abgleich:** `README.md` und `docker/README.md` sprechen von
  justETF-Werten „in millions of EUR“ und stimmen damit. Das Root-README
  nennt keine manuellen Fondsgrößen, also auch keine Währungszusage.
  `unraid/README.md` enthält keine Fondsgröße. `contract/core-contract.json`
  beschreibt Quell- und Eingabewährung. `docker/README.md` ist seit Runde 1
  unverändert (Docker-Hub-Vorschau 8.784 Bytes).
- **Läufe:** Backend 1252 passed, 35 skipped; Plugin-Vertrag 324 passed,
  1 skipped; Ruff (Projektlauf und `I` je Paket) ohne Befund; Dashboard
  52 Dateien, 395 Tests; `vue-tsc -b` und ESLint ohne Befund. Die
  Umbenennungen ändern kein Verhalten; der Browserbeleg aus Runde 2 gilt
  weiter.
- **Umfang Gesamtstand** gegen `f268ced`: 27 Dateien, 321 Zeilen hinzu,
  106 entfernt (ohne `_tickets/`).

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

## Übergabe Runde 1 (Claude, 2026-10-01)

Prüfgegenstand: `67c86f8` gegen `master` (`f268ced`); darin `20b673a`
(Umsetzung) und `67c86f8` (Testwerte im Vertragstest nachgezogen). Die
Verify-Matrix dieser Übergabe steht seit der Umstellung auf „neueste Runde
zuerst“ oben unter [Verify](#verify) und wird dort fortgeschrieben.

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
