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
