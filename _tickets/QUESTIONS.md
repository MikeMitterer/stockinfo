# QUESTIONS

Ephemerer Capture-Buffer. Jeder Eintrag drainiert zeitnah → **sofort erledigt** /
**GitHub-Issue `→ #NN`** / **beantwortet + gelöscht**. Nichts wohnt hier.

<!-- Format:
- [ ] <Frage/Finding beim Testen> — Kontext: <Ticket/URL>
-->

- [ ] StockPortfolio hat dieselbe Toast/Knopf-Kollision wie StockInfo vor T-13:
      „Aktualisieren" steht rechts in der Kopfzeile, Naive setzt die Meldungen
      12 px unter den oberen Rand — also darüber. Dort ist es nicht gemessen.
      Soll StockPortfolio denselben Versatz (`container-style` mit `top: 4rem`)
      bekommen? — Kontext: T-13, `StockPortfolio/src/App.vue:91`
