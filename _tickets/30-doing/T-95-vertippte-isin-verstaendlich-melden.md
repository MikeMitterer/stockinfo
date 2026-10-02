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

### Side-Effects

Nur der Aufnahmeweg für freie Eingaben. Die ISIN-Pfade
(`/quote/{isin}` usw.) prüfen schon heute über `InvalidIsinError`.
