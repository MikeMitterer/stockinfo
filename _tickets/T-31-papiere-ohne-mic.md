# T-31 · Papiere ohne echten MIC — Krypto, Index, Anleihe

- **Status:** offen (Entscheidung ausstehend)
- **Angelegt:** 2026-08-25, beim Bau von T-21 Teil 3, Übergabe 2A
- **Repo:** StockInfo
- **Abhängt von:** T-21 Teil 3 (Entscheidung 2)

## Verify-Matrix

| # | Where | Look for | AI | Human |
|---|---|---|---|---|
| 1 | Entscheidung | Mike hat entschieden, ob StockInfo Papiere **ohne** Handelsplatz weiter führt — und wenn ja, wie ihre Identität aussieht | ➖ [^a] | |
| 2 | `app/repository.py` | der Aufnahmeweg behandelt die Gattung nach dieser Entscheidung, nicht nach dem Zufall der Symbolform | | |
| 3 | Migration | eine reale Krypto-Zeile wird nach derselben Regel behandelt wie beim Aufnahmeweg — nicht anders | | |
| 4 | `tests/test_repository.py` | der Testfall `BTC-USD` prüft das entschiedene Verhalten, nicht das zufällig entstandene | ➖ [^b] | |

[^a]: **Nicht entschieden.** Mike hat am 2026-08-25 ausdrücklich gewählt, die
    Frage von T-21 Teil 3 zu trennen, damit Übergabe 2A nicht daran hängt.
[^b]: Vorerst als **Negativfall** formuliert: Der Test hält fest, dass ein
    Symbol ohne Handelsplatz beim Anlegen abgelehnt wird — das ist der
    Zustand nach 2A, nicht die Zusage, dass es so bleiben soll.

## Worum es geht

T-21 Teil 3 verlangt seit Entscheidung 2 eine **vollständige kanonische
Identität**: kanonischer Ticker **und** echter MIC nach ISO 10383. Seit
Übergabe 2A steht das im Schema (`ticker`/`mic` als `NOT NULL`), und
`canonical_identity` lehnt alles andere ab.

Damit lässt sich **`BTC-USD` nicht mehr speichern**. Eine Kryptowährung wird
an keinem Handelsplatz im Sinne von ISO 10383 gehandelt; es gibt schlicht
keinen MIC, der wahr wäre. Dasselbe gilt für Indizes und einen Teil der
Anleihen.

**Das ist keine Nachlässigkeit im Entwurf, sondern eine Folge, die niemand
ausgesprochen hat.** Die gemessene Auswirkungstabelle in der Spec führt nur
Aktien und ETFs auf; die Gattungen ohne Handelsplatz kamen darin nicht vor.

## Woran es aufgefallen ist

`tests/test_repository.py` deckt den Weg ausdrücklich ab. Der Docstring des
Tests nennt die Gattungen beim Namen:

> Ausgelöst von jedem Papier, dessen Gattung yfinance nicht kennt (Krypto,
> Index, Anleihe) oder dessen justETF-Abruf beim ersten Kontakt scheitert.

Der Test legt `BTC-USD` an und liest es zurück. Unter der neuen Regel schlägt
das mit `IncompleteIdentityError` fehl.

## Was **nicht** dagegen spricht, 2A ohne diese Entscheidung zu übergeben

Im realen Bestand gibt es heute **keine** solche Zeile — nachgemessen am
2026-08-25: sechs Instrumente, fünf mit Börsensuffix, dazu `VTI`. Die
Migration entfernt also nichts, was existiert.

`QUOTE_TYPE_MAP` in `app/providers/base.py` kennt außerdem nur `ETF`,
`MUTUALFUND` und `EQUITY`; eine Kryptowährung käme heute ohnehin ohne Gattung
durch. Der Weg ist vorhanden und getestet, aber nicht in Benutzung.

## Die Auswege, wie sie beim Fund aussahen

1. **Streng bleiben.** Was keinen echten MIC hat, gehört nicht in den
   Bestand. Klarste Regel, aber StockInfo verliert eine Gattung, die es heute
   bedient.
2. **Ein Katalogeintrag für „kein Handelsplatz".** Die Identität bliebe
   vollständig — um den Preis eines MIC-Werts, der keine Börse bezeichnet.
   Das ist genau die Sorte magischer Wert, die T-21 gerade austreibt (`US` im
   `mic`-Feld), und der Vorschlag trägt dieselbe Schwäche.
3. **Eine eigene Identitätsform für Gattungen ohne Handelsplatz.** Nicht
   durchdacht, aber die einzige der drei, die weder Daten noch Ehrlichkeit
   kostet — sie bräuchte einen Entwurf.

Die Entscheidung gehört nicht in 2A und ist deshalb hier.
