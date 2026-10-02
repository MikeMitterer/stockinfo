# T-89 · Volatilität für alle Instrumenttypen anzeigen

Die Tabelle zeigt in der Spalte „Vola 1Y“ nur bei ETFs und ETCs einen Wert.
Bei Aktien und Fonds steht „–“, obwohl StockInfo die Volatilität auch dort
berechnet und die API sie liefert.

**Beispiel:** `APC.DE` (Apple) liefert in `GET /instruments`
`"volatility": 26.11`. In der Tabelle und im Detailbereich steht „–“.
Ebenso bei `BRYN.DE` (15,53 %) und `GOLD.SG` (EUWAX Gold, Typ `fund`, 27,0 %).

**Stand:** Gefunden am 2026-10-01 beim Erneuern der Screenshots. Mike: „Ja,
leg T-89 mit Lösung 1 an“ und „Starte nach dem OK von Codex auch gleich mit
T-89“. Aktiv seit 2026-10-02 nach Codex' Freigabe und Merge von T-88
(`eca7413`); Coder `claude`, Verifier `codex`, maßgeblich ist `STATUS.md`.
Für Mike steht kein Handgriff an.

## Scope-Vertrag (Claude, 2026-10-02)

**Befund aus dem Code:** Die berechnete Volatilität wird schon als
Detailwert gespeichert (`repository.set_volatility`, Quelle `calculated`).
`detail_store.read` zeigt einen Detailwert aber nur, wenn eine Deklaration
ihn für Gattung und Identitätsart freigibt. Bei mehreren Quellenwerten
gewinnt die Quelle, die in `definition.sources` zuerst steht; `calculated`
steht heute in keiner Deklaration.

- **Ergebnis:** `details.volatility` ist für alle Gattungen deklariert. Aktien,
  Fonds und andere Instrumente mit Tageskursen zeigen die berechnete
  Volatilität in Tabelle und Detailbereich. Bei ETFs mit justETF-Wert
  gilt weiter justETF; ohne justETF-Wert der berechnete. Das entspricht der
  bestehenden README-Aussage („from justETF for ETFs, otherwise computed“).
- **Fachliche Änderungen (2):**
  1. Neue Core-Deklaration (`app/calculated_metrics.py`): Quelle
     `calculated`, Feld `volatility` (Prozent, überschreibbar wie bei
     justETF), alle Gattungen aus `INSTRUMENT_TYPES`, Identitätsarten
     `listed` und `pair`. `sources_registry.detail_definitions` hängt sie
     **nach** den Plugins an; dadurch steht `calculated` in
     `sources` hinter `justetf`. Der Quellname kommt als Konstante aus dem
     neuen Modul; `repository.set_volatility` nutzt sie statt des Literals.
  2. Neues Dashboard-Bild `unraid/screenshots/dashboard.png`, auf dem die
     Aktien ihre Volatilität zeigen.
- **Tests:** Katalog deklariert `volatility` für `stock` und `fund` mit
  Quellenfolge `justetf`, `calculated`; Service mit temporärer Datenbank:
  Aktie zeigt den berechneten Wert in `details`, ETF mit beiden Werten zeigt
  justETF.
- **Sichtbare Prüfung:** Temp-Instanz mit Aktie, ETF und Fonds, Tabelle und
  Detailbereich auf Deutsch und Englisch, Screenshots als Beleg.
  StockPortfolios `projectDetailFields` erneut mit den echten Antworten.
- **Doku:** README („`volatility` … from justETF for ETFs, otherwise
  computed“) stimmt schon; Abgleich mit `docker/README.md` und
  `docs/plugin-authors.md` (Detailfelder).
- **Budget:** 3 Produktdateien, 3 Test-/Doku-/Bilddateien, 200 Diff-Zeilen.
- **Nicht-Ziele:** keine neue Berechnung, keine Änderung der Rangfolge
  zwischen justETF und Berechnung, keine Änderung an StockPortfolio.

## Ursache

- StockInfo berechnet die Volatilität selbst, für jedes Instrument mit
  Tagesschlusskursen (`app/services/quote_cache.py`,
  `_save_fresh_with_volatility` → `annualized_volatility`).
- Die Tabelle zeigt eine Kennzahl nur, wenn sie im `details`-Container des
  Instruments deklariert ist (`dashboard/src/components/MetricValue.vue`,
  `Object.hasOwn(item.details, field)`). Eingeführt mit `aa680cc`
  (2026-09-07, T-56), um alte TER- und Thesaurierungswerte bei Aktien
  auszublenden.
- `volatility` deklariert nur das justETF-Plugin, und dessen
  `SUPPORTED_TYPES` sind `etf` und `etc`. Aktien und Fonds bekommen den
  Eintrag nie.

T-56 hielt die Volatilität bei Aktien für einen Altwert („Das betrifft auch
eine alte Volatilität ohne aktuelle Deklaration“). Sie wird aber bei jeder
Aktualisierung neu berechnet.

## Lösung (Mike: Lösung 1)

StockInfo deklariert `volatility` selbst als Kennzahl für alle
Instrumenttypen, für die Kurse vorliegen. Der Wert stammt aus StockInfos
eigener Berechnung, nicht aus justETF; die Deklaration gehört deshalb zur
Quelle der Berechnung. Die Regel aus T-56 bleibt unverändert und blendet TER
und Thesaurierung bei Aktien weiter aus.

Nicht gewählt: eine Ausnahme für `volatility` in `MetricValue.vue`. Sie
umginge die Regel für eine Kennzahl, und der Detailbereich zeigte die
Volatilität bei Aktien weiter nicht.

Den genauen Weg (eigene Core-Deklaration oder Erweiterung des Katalogs) legt
der Coder im Scope-Vertrag fest.

### Akzeptanzkriterien

- [ ] `details` enthält `volatility` für Aktien, ETFs, ETCs und Fonds mit
      berechneter Volatilität.
- [ ] Tabelle und Detailbereich zeigen die Volatilität bei `APC.DE`,
      `BRYN.DE` und `GOLD.SG`.
- [ ] TER und Thesaurierung bleiben bei Aktien ausgeblendet (Regel aus T-56).
- [ ] Wenn justETF ebenfalls eine Volatilität liefert, ist festgelegt und
      getestet, welcher Wert gilt.
- [ ] **Sichtbare Prüfung im Browser** (nicht headless, Mike: „Vergiss auch
      die visuellen Tests pro Ticket nicht“): Temp-Instanz mit Aktie, ETF und
      Fonds; Tabelle und Detailbereich auf Deutsch und Englisch ansehen;
      Screenshots als Beleg im Ticket.
- [ ] `unraid/screenshots/dashboard.png` wird danach neu aufgenommen.
- [ ] Doku-Abgleich für `README.md` und `docker/README.md`.

### Side-Effects

StockPortfolio liest `volatility` aus der API; der Wert selbst ändert sich
nicht, nur seine Deklaration im `details`-Container. Geprüft mit
StockPortfolios Code (siehe StockPortfolio T-79): Dessen
Zusatzinformationen blenden die Volatilität bei Aktien und Fonds heute aus,
weil `GET /fields` sie nur für `etf` und `etc` deklariert. Nach T-89 muss die
Deklaration in `scopes` deshalb `stock` und `fund` samt passender
Identitätsarten nennen. Dann zeigt StockPortfolio den Wert ohne eigene
Änderung.

### Verify

Aktuelle Statusmatrix; sie wird über alle Runden fortgeschrieben.

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | `GET /fields`, Feld `volatility` | `sources` = `justetf`, `calculated`; Scope `calculated` mit allen Gattungen, `listed` und `pair` | ✅ |
| 2 | `GET /instruments` mit Aktie, Fonds, ETF | Aktie und Fonds: `details.volatility` mit Quelle `calculated`; ETF mit justETF-Wert: Quelle `justetf` | ✅ |
| 3 | `.venv/bin/python -m pytest -q`, `tests/test_calculated_metrics.py` | grün; ein Rot-Grün-Orakel am öffentlichen Eintrittspunkt mit negativem Gegenfall fehlt noch (B1) | ⚠️ B1 |
| 4 | Sichtbare Prüfung im Browser (Temp-Datenbank), deutsch und englisch | Tabelle zeigt „Vola 1Y“ bei Aktie und Fonds; Detailbereich zeigt „Volatilität (1 Jahr)“ | ✅ |
| 5 | StockPortfolios `projectDetailFields` mit den echten Antworten | Zusatzinformationen zeigen die Volatilität bei Aktie und Fonds; Coder-Lauf belegt die Ausgaben, API-Scopes wurden unabhängig geprüft | ✅ |
| 6 | Standard und Doku | Doku und Namensinventar passen; Typangaben im neuen Testmodul sind unvollständig beziehungsweise falsch (B2) | ⚠️ B2 |

## Review-Verlauf (neueste Runde zuerst)

Neue Übergaben, Nacharbeiten und Verifier-Prüfungen kommen direkt unter
diese Überschrift (Regel „Review-Verlauf — neueste Runde zuerst“ in
`.agents/AGENT-WORKFLOW.md`).

## Nacharbeit Runde 1 (Claude, 2026-10-02)

Prüfgegenstand: `5684a68` gegen `fecdad0` (Nacharbeit) und gegen `eca7413`
(Gesamtstand). Geändert ist nur `tests/test_calculated_metrics.py`.

- **B1 · öffentlicher Akzeptanzpfad:** Zwei API-Tests mit der echten App
  (Lifespan) auf der temporären Datenbank aus `tests/conftest.py`:
  `test_fields_deklariert_die_berechnete_volatilitaet_fuer_aktien_und_fonds`
  prüft in `GET /fields` die Quellenfolge `justetf`, `calculated` und den
  `calculated`-Scope mit `stock`, `fund` sowie `listed`, `pair`.
  `test_instruments_liefert_berechnete_und_justetf_volatilitaet` legt eine
  Aktie (APC.DE, berechnet 26,11) und einen ETF (EUNL.DE, berechnet 11,09,
  justETF 10,67) an; `GET /instruments` liefert 26,11 mit Quelle
  `calculated` und 10,67 mit Quelle `justetf`.
- **Negativer Mutant:** `detail_definitions` vorübergehend ohne
  `CalculatedMetrics` (`merge_definitions(_DETAIL_SCHEMAS.values())`).
  Ergebnis: beide API-Tests **rot**, `/fields` mit `StopIteration` (kein
  `calculated`-Scope), `/instruments` mit `KeyError: 'volatility'` (Aktie
  ohne Detailwert). Mutant zurückgenommen, `git diff -- app` leer, beide
  Tests **grün**.
- **B2 · Typen:** Alle Fixtures, Helfer und Testfunktionen sind annotiert.
  `_summary()` mit falschem `tuple[dict, int]` ist ersetzt durch
  `_save() -> int`, `_service() -> CachedQuoteService` und
  `_put_justetf() -> None`. `ruff --select ANN,I` ohne Befund.
- **Läufe:** Testmodul 11 passed; Backend 1263 passed, 35 skipped (die
  eine Warnung ist die bekannte Starlette-Deprecation); `ruff check app
  tests` ohne Befund. Bezeichner-Inventar des Testmoduls (`ast`): nur
  englische Nicht-Testnamen. Kein Produktcode und kein Anzeigeverhalten
  geändert; die Browserbelege aus Runde 1 gelten weiter.

## Verifier-Prüfung · Runde 1 (Codex, 2026-10-02)

**Prüfstand:** `fecdad0` gegen `eca7413`. Nach dem Produktcommit betraf
der Übergabecommit nur `_tickets/`; der Arbeitsbaum war beim Claim sauber.
Ergebnis: **`changes_requested`** wegen B1 und B2. Die fachliche
Deklaration, der Vorrang und die Browseranzeige stimmen; keine technische
oder menschliche Abnahme.

### Befunde

1. **B1 blockierend · Vertical-Acceptance-Riegel.** Die neuen roten Tests
   prüfen `detail_definitions()` und
   `CachedQuoteService.get_instrument_summary()` direkt. Sie erreichen
   weder `GET /fields` noch `GET /instruments`; der spätere Browserlauf
   belegt den grünen Nutzerweg, aber kein rotes Orakel am öffentlichen
   Eintrittspunkt. Der lokale Workflow verlangt für die neue Regel einen
   solchen Akzeptanztest und einen negativen Gegenfall, der bei einer
   minimal falschen Deklaration rot wird. Bitte einen schmalen API-Test
   mit temporärer Datenbank ergänzen: `GET /fields` zeigt den
   `calculated`-Scope für `stock` und `fund` (`listed` und `pair`), und
   `GET /instruments` liefert den berechneten Detailwert für eine Aktie
   und den justETF-Vorrang für einen ETF. Den Test mit entfernter
   Core-Deklaration als negativen Mutanten rot und mit der Endfassung grün
   ausführen und das Ergebnis dokumentieren. Normale Fixtures reichen;
   kein neues Test-Subsystem.
2. **B2 blockierend · Python-Typangaben im neuen Testmodul.** Die
   Python-Referenz von `code-standards` verlangt Type Hints überall.
   `tests/test_calculated_metrics.py:50` annotiert `_summary()` als
   `tuple[dict, int]`, gibt aber `CachedQuoteService` und `int` zurück.
   Das AST-Inventar aller acht Funktionen meldet zudem fehlende
   Parameter- beziehungsweise Rückgabetypen; `ruff --select ANN`
   weist acht Stellen aus (`:28,36,41,45,57,67`). Bitte die Typen
   vollständig und zutreffend setzen und die Gegenprobe wiederholen.
   Die neue API-Testfunktion aus B1 gehört in denselben Abgleich.

### Prüfung und Doku-Abgleich

- **#1:** ✅ `CalculatedMetrics` deklariert `volatility` in Prozent für
  alle sechs `INSTRUMENT_TYPES` und `listed`/`pair`. Eigene
  `definitions_for()`-Gegenprobe: alle sechs Typen gelten für beide
  Identitätsarten, `isin_only` nicht. Die gemergte Quelle steht nach
  justETF; Coder-API-Beleg zeigt `sources` in dieser Reihenfolge.
- **#2:** ✅ Reale Repository- und Service-Tests mit temporärer DB
  zeigen `calculated` bei der Aktie und justETF beim ETF. Die
  visuell geprüften Belege zeigen APC.DE, BRYN.DE und GOLD.SG in der
  Tabelle; APC.DE deutsch und GOLD.SG englisch auch im Detail.
- **#3:** ⚠️ B1, obwohl Backend **1261 passed, 35 skipped, 1 warning**,
  Plugin-API **324 passed, 1 skipped**, Dashboard **395 passed**.
- **#4:** ✅ Alle drei neuen Bilder wurden unabhängig angesehen:
  [APC deutsch](T-89-browser-de-apc.png),
  [GOLD englisch](T-89-browser-en-gold.png),
  `unraid/screenshots/dashboard.png`. Der Browserlauf selbst stammt
  von Claude; ich behaupte keinen eigenen.
- **#5:** ✅ Die StockInfo-Antwortfelder und Scopes passen zum
  dokumentierten `projectDetailFields`-Lauf mit APC.DE, GOLD.SG und
  EUNL.DE. Der Konsumentenlauf stammt von Claude, nicht von Codex.
- **#6 / Doku-Abgleich:** ⚠️ B2. `README.md:285-286` beschreibt
  justETF-Vorrang und sonst berechnete Volatilität bereits; das
  unveränderte `docker/README.md` trifft keine Herkunftsaussage,
  ebenso `unraid/README.md`. `docs/plugin-authors.md` erklärt jetzt
  `calculated` und die Quellenfolge; der Core-Vertrag bleibt
  quellenunabhängig. Ruff und Ruff-`I` für die vier geänderten
  Python-Dateien sowie `git diff --check` bestehen. Das AST-Inventar
  dieser vier Dateien ergab nur englische Nicht-Testbezeichner.

**Standard-Riegel:** Gelesen wurden
`/Users/macminipro/.codex/skills/code-standards/SKILL.md` und die
passenden Referenzen `architecture.md`, `python.md`, `persistence.md`,
`quality.md` und `documentation.md`.

| Referenzgruppe | Ergebnis und Beleg |
|---|---|
| Architektur, DRY, Funktionen und Namen | ✅ eine `CALCULATED_SOURCE` für Deklaration und Speicherung; keine zweite Berechnung. AST-Inventar der vier berührten Python-Dateien ohne deutsche Nicht-Testnamen. |
| BashLib, Bash-Fehler und Exit-Codes | ➖ nicht berührt |
| Skript-CLI, Hilfe und ANSI-Ausgabe | ➖ nicht berührt |
| TypeScript, Vue und i18n | ✅ kein Frontend-Code geändert; visuelle DE-/EN-Belege für die neuen Daten geprüft. Rohe Quellkennung `calculated` ist ein dokumentierter Nebenbefund, kein neuer fest verdrahteter UI-Satz. |
| Python, FastAPI und Webhooks | ⚠️ B2; Ruff und Importsortierung grün, aber fehlende und falsche Typangaben im neuen Testmodul. |
| Datenbanken und Persistenzgrenzen | ✅ vorhandener Repository-Schreibweg nutzt nur die gemeinsame Quellkonstante; keine neue SQL-Abfrage oder Verbindung. Tests bleiben durch `tmp_path` isoliert. |
| Fehler, Logging und Tests | ⚠️ B1; bestehende Suite grün, öffentliches rotes Orakel und negativer Mutant fehlen. Neue Fixtures/Helper sind klein, kein Test-Subsystem. |
| Markdown und Inhaltsverzeichnisse | ✅ `docs/plugin-authors.md` fügt die Erklärung im vorhandenen Abschnitt ein; beide READMEs und Vertrag inhaltlich abgeglichen. |

**Offene Board-Übernahme:** Activity-/Observer-/Lessons-Abgleich aus
Paketfassung `df699dd1` bleibt getrennt offen. Die sichtbare Quelle
`calculated` ohne lokalisierten Anzeigenamen und das Info-Symbol ohne
Datum sind als Nebenbefund dokumentiert. Sie ändern den Umfang von T-89
nicht und begründen hier keinen Blocker. Codex änderte keinen Produktcode
und erteilte keine menschliche Abnahme.

## Übergabe Runde 1 (Claude, 2026-10-02)

Prüfgegenstand: `fecdad0` gegen `master` (`eca7413`).

**Coder-Belege:**

- **#1:** Temp-Instanz mit dem Branchstand: `volatility` hat `sources`
  `["justetf", "calculated"]` und die Scopes `justetf` (etc, etf; listed)
  sowie `calculated` (bond, crypto, etc, etf, fund, stock; listed, pair).
- **#2:** `APC.DE` 26,11 und `BRYN.DE` 15,53 (stock), `GOLD.SG` 27,0 (fund)
  mit Quelle `calculated`; `EUNL.DE` 10,67 und `VGWL.DE` 10,29 mit Quelle
  `justetf`.
- **#3:** Neue Tests in `tests/test_calculated_metrics.py`, zuerst rot
  (Deklaration für stock, fund, crypto, bond und Quellenfolge fehlten; Aktie
  ohne `details.volatility`), danach grün. Die Fälle für etf, etc und den
  justETF-Vorrang waren schon vorher grün und sichern das bestehende
  Verhalten ab. Backend 1261 passed, 35 skipped.
- **#4:** Chrome sichtbar, 1512×801. Neues
  `unraid/screenshots/dashboard.png` (englisch): Vola-Spalte bei allen fünf
  Instrumenten gefüllt. Belege neben dem Ticket:
  [APC.DE deutsch](T-89-browser-de-apc.png) („Volatilität (1 Jahr)
  26,11 %“) und [GOLD.SG englisch](T-89-browser-en-gold.png)
  („Volatility (1y) 27 %“). Der Testfall VTI aus T-88 wurde vorher aus der
  Temp-Datenbank entfernt, damit das Dashboard-Bild nur die fünf
  verständlichen Instrumente zeigt.
- **#5:** `projectDetailFields` (StockPortfolio-Code via `vite-node`, Skript
  im Scratchpad): APC.DE „26,11 %“, GOLD.SG „27,0 %“, EUNL.DE „10,67 %“.
  Vorher fehlten APC.DE und GOLD.SG.
- **#6:** Ruff (Projektlauf und `I` für die berührten Dateien) ohne
  Befund. Neue Bezeichner englisch (`CalculatedMetrics`,
  `CALCULATED_SOURCE`, Testhelfer `_volatility`, `_summary`). Keine
  Ticketnummern oder Rundenhinweise im Code.

**Doku-Abgleich:** `README.md` sagt schon „from justETF for ETFs, otherwise
computed“ und bleibt unverändert; `docker/README.md` und `unraid/README.md`
machen keine Aussage zur Herkunft der Volatilität. `docs/plugin-authors.md`
(„Open detail fields“) erklärt jetzt die Core-Deklaration `calculated` und
die Rangfolge Plugin vor Berechnung. `contract/core-contract.json`
beschreibt `volatility` unabhängig von der Quelle und bleibt.

**Umfang geplant / tatsächlich:** 2 / 2 fachliche Änderungen,
3 / 3 Produktdateien, 3 / 3 Test-/Doku-/Bilddateien, 200 / 129 Diff-Zeilen.

**Nebenbefund, nicht im Scope:** Der Detailbereich zeigt die Quelle als
Rohname „calculated“, und das Info-Symbol erscheint ohne Datum, weil
berechnete Werte kein `as_of` tragen (`repository.set_volatility` setzt
keines). Ein lesbarer Quellname und ein Zeitstempel wären ein eigenes
Ticket.

Kein Merge, kein Push, kein Docker-Hub- oder Unraid-Update.
