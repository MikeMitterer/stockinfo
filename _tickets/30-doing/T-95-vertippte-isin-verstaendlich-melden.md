# T-95 · Eine vertippte ISIN wird als Symbol ohne Börsenzusatz gemeldet

**Warum dieses Ticket:** Die Browser-Gesamtprüfung aus T-93 (Weg W2,
Codex-Befund B5 in Runde 2) zeigt: Wer im Feld „ISIN or symbol“ eine ISIN
vertippt, liest „The symbol has no exchange suffix“. Die Meldung redet von
einem Symbol und einem Börsenzusatz. Sie sagt nicht, dass die ISIN falsch
ist. Wer sie liest, sucht den Fehler an der falschen Stelle.

**Beispiel:** `DE000110253X` (letztes Zeichen ein Buchstabe statt der
Prüfziffer). `POST /instruments/intake` antwortet mit
`symbol_without_exchange_suffix`; die Oberfläche zeigt den Satz oben.

**Stand:** Angelegt am 2026-10-02 aus T-93 als Folgeticket der visuellen
Tests (Mike: Folgetickets aus den Tests gehören zur SQL-Umstellung und
kommen in die `priority_chain`). Älter als die SQL-Umstellung. Aktiviert
wie T-94: von `t-93-visuelle-gesamtpruefung` abgezweigt, nach der Freigabe
zurück nach T-93. Für Mike steht kein Handgriff an.

## Ursache (gemessen)

- `IntakeService._store` (`app/services/intake_service.py`) wählt den Weg
  über `is_isin` (`app/exchanges.py`). Das prüft nur die **Form**
  `[A-Z]{2}[A-Z0-9]{9}[0-9]`.
- `DE000110253X` hat diese Form nicht (letztes Zeichen keine Ziffer) und
  geht deshalb den Symbolweg. Dort fehlt ein Börsenzusatz, also
  `symbol_without_exchange_suffix`.
- Die passende Kennung gibt es schon: `invalid_isin_format`
  (`app/routers/validation.py`), samt Text in beiden Sprachkatalogen
  („{isin} is not shaped like an ISIN.“). Der Aufnahmeweg nutzt sie für
  freie Eingaben nicht.

## Umfang

- Eine Eingabe, die **wie eine ISIN aussieht, aber keine gültige ist**,
  wird mit `invalid_isin_format` abgelehnt statt über den Symbolweg.
- „Sieht aus wie eine ISIN“ muss eng genug sein, dass echte Symbole ohne
  Börsenzusatz weiter ihre bisherige Meldung bekommen. Die genaue Regel
  legt der Umfangsvertrag fest und begründet sie.
- Eine formal richtige ISIN mit falscher Prüfziffer: prüfen, was heute
  passiert, und im Ticket festhalten. Mitbeheben nur, wenn es dieselbe
  Stelle ist.

### Akzeptanzkriterien

- [ ] `POST /instruments/intake` mit `DE000110253X` liefert
      `invalid_isin_format` mit `params.isin`.
- [ ] Ein echtes Symbol ohne Zusatz (etwa `AAPL`) bekommt weiter
      `symbol_without_exchange_suffix` bzw. sein bisheriges Ergebnis.
- [ ] Ein Test am Aufnahmeweg ist ohne die Korrektur rot.
- [ ] W2 der Browserprüfung erwartet für `DE000110253X` den ISIN-Text
      und ist grün.

### Umfangsvertrag (Claude, 2026-10-02)

- **Regel „sieht aus wie eine ISIN“** (`is_malformed_isin` in
  `app/exchanges.py`): zwei Buchstaben, dann zehn Buchstaben oder Ziffern,
  davon mindestens eine Ziffer, aber nicht die ISIN-Form. Ein Börsensymbol
  dieser Länge ohne Punkt gibt es praktisch nicht; die verlangte Ziffer
  schließt reine Buchstabenfolgen aus.
- **Aufnahme** (`IntakeService._store`): nach dem ISIN-Weg, vor dem
  Symbolweg, `IntakeRejected(invalid_isin_format, isin=…)`. Damit bleibt es
  bei `400` mit `{code, params}` wie jede Ablehnung der Aufnahme; das
  Dashboard übersetzt die Kennung schon (DE und EN).
- **Kennung an einer Stelle:** `REASON_INVALID_ISIN` zieht von
  `app/routers/validation.py` nach `app/exchanges.py`, weil auch der Dienst
  sie meldet; `validation.py` übernimmt sie von dort.
- **Falsche Prüfziffer bei richtiger Form** (gemessen, Offline-Profil):
  `DE0001102532` → `400 instrument_not_found` („None of the configured
  sources found a security …“). Verständlich und eine andere Stelle (die
  Auflösung durch die Quellen); nicht mitbehoben.

### Übergabe Runde 1 (Claude, 2026-10-02)

Prüffassung `f200fa3` gegen `1c69db2` (Stand T-93 nach Runde-2-Befund).

- **Tests am Aufnahmeweg** (`tests/test_identity_intake_paths.py`):
  `test_eine_vertippte_isin_wird_als_isin_abgelehnt` (drei Fälle, darunter
  `DE000110253X`) prüft Status, Kennung und `params.isin` und dass keine
  Zeile entsteht. Gegenprobe: mit altem `app/` (per `git stash`) alle drei
  rot. Nachbarn in `test_was_keiner_isin_aehnelt_bleibt_beim_symbolweg`
  (zu kurz, nur Buchstaben, zu lang) bleiben beim Symbolweg, vorher wie
  nachher grün.
- **Messung mit dem Offline-Profil** (eigene Temp-Datenbank):
  `DE000110253X` → `invalid_isin_format`; `IE00B4L5Y983` → `201`;
  `AAPL` → `symbol_without_exchange_suffix`; `DE0001102532` →
  `instrument_not_found`.
- **Browser:** W2 erwartet „DE000110253X is not shaped like an ISIN.“ und
  schließt „exchange suffix“ aus; `ONLY=W1,W2` 2/2 grün, Screenshot
  `W2-malformed.png` angesehen.
- **`make check`:** Exit 0 (1305 Backend, 399 Dashboard, Ruff, `vue-tsc`).
- **Doku-Abgleich:** `docs/rest-core-contract.md` (Aufnahmeweg) nennt die
  Ablehnung. `README.md`, `docker/README.md`, `unraid/README.md`
  unverändert: Sie listen keine Fehlerkennungen der Aufnahme. StockPortfolio
  nutzt den Aufnahmeweg nicht.

### Side-Effects

Nur der Aufnahmeweg für freie Eingaben. Die ISIN-Pfade
(`/quote/{isin}` usw.) prüfen schon heute über `InvalidIsinError`.
