# T-101 · StockPortfolio braucht kein CORS mehr

StockPortfolio ruft StockInfo seit seinem Ticket T-82 nicht mehr aus dem
Browser auf. Der StockPortfolio-Server leitet die Abfragen an
`STOCKINFO_API_URL` weiter; der Browser spricht nur noch mit StockPortfolio.
Für StockPortfolio muss StockInfo deshalb keine fremde Browser-Herkunft mehr
zulassen, und die StockInfo-Adresse muss nur vom StockPortfolio-Container aus
erreichbar sein, nicht vom Browser.

**Beispiel:** Ein Unraid-Nutzer betreibt StockPortfolio unter
`http://tower:8088`. Bisher musste er diese Adresse in StockInfo als
`CORS_ORIGINS` eintragen. Jetzt genügt in StockPortfolio
`STOCKINFO_API_URL=http://stockinfo:8000` im gemeinsamen Docker-Netz; in
StockInfo trägt er nichts ein.

**Stand:** Angelegt am 2026-10-03 aus StockPortfolio heraus (claude-coder,
StockPortfolio T-82). Beschreibt die Lage aus Konsumentensicht; über Folgen in
StockInfo entscheidet, wer den Dienst kennt.

## Was sich für StockInfo ändert

- **T-100 (`80-iced/`, CORS_ORIGINS robust lesen):** Wurde zurückgestellt,
  bis T-82 kommt. T-82 ist umgesetzt; StockPortfolio braucht das Feld nicht
  mehr. Ob T-100 für andere Konsumenten noch Wert hat, entscheidet StockInfo.
- **T-99 (`10-backlog/`, Testmodus für Konsumenten):** Die Anforderung
  „CORS für die Browser-Herkunft des Teststacks (`http://127.0.0.1:5175`)“
  entfällt. StockPortfolios Teststack startet StockInfo inzwischen mit einer
  absichtlich fremden Herkunft und prüft, dass der Browser StockInfo nie
  direkt anfragt.
- **Unraid-Vorlage:** Das Feld „CORS origins“ in `templates/stockinfo.xml`
  ist bereits entfernt (Templates `4e910c4`).
- **Anleitungen:** Die CORS-Hinweise für StockPortfolio sind bereits entfernt
  (`ad10866`). `README.md` erklärt `CORS_ORIGINS` nur noch allgemein; aus
  StockPortfolio-Sicht ist keine Änderung nötig.

## Auswirkung, wenn nichts geschieht

Keine Störung. T-99 enthielte eine überholte Anforderung, und T-100 bliebe
ohne Anlass im Eis.
