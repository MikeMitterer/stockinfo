# T-88 · Fondsgröße in Euro statt in Millionen

Die Detailansicht eines ETFs zeigt die Fondsgröße um den Faktor eine Million
zu klein. Beim iShares Core MSCI World (`EUNL.DE`) steht „129,791 EUR“; der
Fonds verwaltet rund 129,8 Milliarden Euro.

**Beispiel:** justETF schreibt „EUR 129,791 m“. Die Bibliothek
`justetf_scraping` liefert daraus `fund_size_eur = 129791.0` — laut ihrer
Doku „Fund size in EUR millions“. StockInfo gibt diesen Wert als absoluten
Betrag weiter, obwohl der Vertrag absolute Beträge verlangt (Fixture:
`fund_size: 89123000000.0`).

**Stand:** Gefunden am 2026-10-01 beim Erneuern der Screenshots. Mike:
„Erst Fehler beheben“ und „Das Ticket kannst du gleich bei doing ablegen“.
Coder `claude`, Verifier `codex`; maßgeblich ist `STATUS.md`. Danach entsteht
das neue `unraid/screenshots/detail-area.png`.

## Scope-Vertrag (Claude, 2026-10-01)

- **Ergebnis:** Die Detailansicht zeigt die Fondsgröße eines ETFs als
  richtigen Betrag in kurzer, lesbarer Form („129.79B EUR“, deutsch
  „129,79 Mrd. EUR“). Die API liefert den absoluten Euro-Betrag, wie der
  Vertrag es vorsieht. Die Replikation steht mit Leerzeichen da:
  „Physical (Optimized sampling)“.
- **Fachliche Änderungen (3):**
  1. `app/providers/justetf_provider.py`: `fund_size_eur` mal 1.000.000;
     `app/details.py`: Obergrenze für `fund_size` von 2.000.000 auf
     5.000.000.000.000 (5 Billionen), weil sie auch Quellenwerte prüft.
  2. `app/providers/justetf_provider.py`: fehlendes Leerzeichen vor „(“ in
     der Replikation ergänzen.
  3. `dashboard/src/components/DetailEditor.vue`: absolute Beträge kompakt
     formatieren (`Intl`-Notation `compact`).
- **Tests:** Provider-Test für Umrechnung und Leerzeichen, Grenzwert-Test
  in den Details, Dashboard-Test für die kompakte Anzeige.
- **Doku:** README-Abgleich (Abschnitte zu justETF und Fondsgröße), beide
  READMEs; Vertrag `contract/` beschreibt bereits absolute Beträge.
- **Budget:** 3 Produktdateien, 4 Test-/Dokudateien, 200 Diff-Zeilen.
- **Nicht-Ziele:** keine Migration gespeicherter Werte (Entwicklungsstand,
  nur Mikes Daten; justETF-Werte werden beim nächsten Metadatenabruf neu
  geschrieben), keine Änderung an StockPortfolio, keine andere Quelle.

**Hinweis für bestehende Daten:** Bereits gespeicherte justETF-Werte stehen
noch in Millionen, bis justETF erneut abgefragt wird. Eine Einzel-
Aktualisierung (↻ in der Zeile) erzwingt den Abruf; sonst geschieht es nach
`METADATA_TTL_DAYS`. Manuell eingetragene Fondsgrößen bleiben unverändert.

### Akzeptanzkriterien

- [ ] Die API liefert für einen justETF-ETF die Fondsgröße in Euro (Faktor
      1.000.000 gegenüber justETF).
- [ ] Werte bis 5 Billionen Euro werden angenommen, aus Quelle wie manuell.
- [ ] Die Detailansicht zeigt große Beträge kompakt und mit Währung.
- [ ] Die Replikation enthält das Leerzeichen vor der Klammer.
- [ ] Doku-Abgleich für `README.md` und `docker/README.md`.

### Side-Effects

StockPortfolio liest `fund_size` (`frontend/src/api/types.ts`) und erhält
danach Euro statt Millionen. Der Vertrag sagt bereits „absolut“; ob
StockPortfolio den Wert anzeigt, wird im Übergabebericht genannt.
