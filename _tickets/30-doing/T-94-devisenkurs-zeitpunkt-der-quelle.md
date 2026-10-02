# T-94 · Devisenkurs zeigt den Abruf statt des Zeitpunkts der Quelle

**Warum dieses Ticket:** Die Browser-Gesamtprüfung aus T-93 (Weg W11) hat
gezeigt, dass ein Wechselkurs immer mit dem Zeitpunkt des Abrufs erscheint,
nicht mit dem Zeitpunkt, den die Quelle nennt. Ein Kurs, der in einer Datei
am 27. August gepflegt wurde, steht in der Oberfläche als „frisch“ mit
heutiger Uhrzeit. Wer danach rechnet, hält einen alten Kurs für aktuell.

**Beispiel:** Die Offline-Vorlage `examples/assets-standalone.yaml` führt
`CAD → EUR` mit `rate: 0.6412` und `as_of: "2026-08-27T17:30:00+02:00"`.
`GET /fx?base=CAD&quote=EUR` liefert `quote_time` = Zeitpunkt des Abrufs
(etwa `2026-10-02T15:12:18+00:00`), und die Devisenansicht zeigt
„Oct 2, 2026“ statt „Aug 27, 2026“.

**Stand:** Angelegt am 2026-10-02 aus T-93 als Folgeticket der visuellen
Tests (Mike: Folgetickets aus den Tests gehören zur SQL-Umstellung und
kommen in die `priority_chain`). Älter als die SQL-Umstellung: Das Verhalten
besteht seit der FX-Kaskade (August 2026), T-90 bis T-92 haben es nicht
verursacht. Für Mike steht kein Handgriff an.

## Ursache (gemessen)

- Das YAML-Plugin liefert `FxRate(rate, as_of)` (`plugin_api/examples/yaml_file.py`,
  `fetch_rate`).
- Die Schnittstelle zwischen Dienst und Quellen (`provider.fetch_fx_rate`)
  gibt nur den Kurs als Zahl weiter (`answer.value`); `as_of` geht dort
  verloren.
- `CachedFxService._fetch_or_fallback` (`app/services/fx_service.py`) setzt
  `quote_time` deshalb auf „jetzt“ und speichert es so in `fx_rates`.

## Umfang

- Der Quellenzeitpunkt (`as_of`) reicht vom Plugin bis `quote_time` in
  Antwort und Cache. Fehlt er bei einer Quelle, bleibt „jetzt“ der Ersatz.
- `fetched_at` bleibt der Abrufzeitpunkt (Cache-Frische).
- Prüfen, ob Kursabrufe (`quotes`) denselben Verlust haben; falls ja, im
  Ticket nennen, nicht stillschweigend mit beheben.

### Akzeptanzkriterien

- [ ] `GET /fx?base=CAD&quote=EUR` liefert mit dem Offline-Profil
      `quote_time` aus `as_of` der Datei; `fetched_at` bleibt der Abruf.
- [ ] Ein Test belegt das am echten Weg vom Plugin bis zur Antwort und wird
      rot, wenn `as_of` wieder verloren geht.
- [ ] `make visual-check` W11 ist grün.

### Umfangsvertrag (Claude, 2026-10-02)

- `app/providers/base.py`: neuer Wert `FxQuote(rate, quote_time)`;
  `FxRateProvider.fetch_fx_rate` liefert `SourceAnswer[FxQuote]`.
- `app/plugin_adapters.py` (`FxAdapter`): `quote_time = as_of.isoformat()`,
  genau wie `QuoteAdapter` bei Kursen.
- `app/services/fx_service.py`: speichert und liefert `quote_time` der
  Quelle; `fetched_at` bleibt „jetzt“.
- Der Ersatz „jetzt“ für einen fehlenden Zeitpunkt entfällt: `FxRate.as_of`
  ist im Plugin-Vertrag Pflicht, eine Quelle ohne Zeitpunkt gibt es nicht.
- Unverändert: `YfinanceProvider.fetch_fx_rate` und das yfinance-Plugin.
  Yahoo nennt für Devisen keinen Zeitpunkt; das Plugin setzt `as_of` dort
  ehrlich auf den Abruf.
- Kurse (`quotes`) haben den Verlust nicht: `QuoteAdapter` reicht `as_of`
  bereits als `quote_time` weiter (`app/plugin_adapters.py`).
- Tests: Weg vom YAML-Plugin über `FxAdapter` und Dienst bis `GET /fx`;
  Doubles in `tests/test_fx_service.py` auf `FxQuote`.

### Übergabe Runde 1 (Claude, 2026-10-02)

Prüffassung `8991a55` gegen `ee5d856` (Stand T-93 nach Nacharbeit B1–B4).

- **Umsetzung** wie im Umfangsvertrag: `FxQuote` in `app/providers/base.py`,
  `FxAdapter.fetch_fx_rate` und `CachedFxService._fetch_or_fallback`.
- **Test am echten Weg:** `tests/test_yaml_profile.py::
  test_der_devisenkurs_traegt_den_zeitpunkt_der_datei` (YAML-Plugin →
  Adapter → Dienst → `GET /fx`, frisch und aus dem Cache). Gegenprobe: Mit
  dem alten `app/` (per `git stash`) ist er rot. Dazu Zusicherungen in
  `tests/test_fx_service.py::test_miss_holt_live_und_speichert`.
- **`make check`:** grün (1299 Backend, 399 Dashboard, ruff, vue-tsc).
- **Browser:** `ONLY=W1,W2,W11` 3/3 grün; W11 vorher rot.
- **Kurse:** kein Verlust, `QuoteAdapter` reicht `as_of` bereits weiter.
- **StockPortfolio:** zeigt `quoteTime` nur an (`FxNotice.vue`,
  `PortfolioManager.vue`), rechnet nicht damit. Dort steht künftig der
  Stand der Quelle; kein Handgriff nötig.
- **Doku-Abgleich:** `docs/rest-core-contract.md` („`quote_time` gegen
  `fetched_at`“) um `/fx` ergänzt. `README.md`, `docker/README.md` und
  `unraid/README.md` unverändert: Das Beispiel in `README.md` zeigt eine
  Kursantwort, und an Konfiguration und Betrieb ändert sich nichts.

### Side-Effects

`quote_time` eines Wechselkurses kann älter sein als bisher; die
Frischeanzeige („fresh“/„stale“) richtet sich weiter nach `fetched_at`.
Prüfen, ob StockPortfolio `quote_time` von `/fx` anzeigt oder auswertet.
