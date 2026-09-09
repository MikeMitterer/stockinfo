# StockPortfolio · Brauchen wir eine flache Quote-Antwort?

Stand: 8. September 2026. Prüfung der lokalen Arbeitsstände; keine Änderung
an Produktcode, API-Vertrag oder aktiver Ticketkette.

Eine **vereinfachte Leseansicht** ist für Konsumenten plausibel. Für die
heutige StockPortfolio-Integration ist sie aber keine Voraussetzung: Die
bereits verwendeten Kennzahlen liefert StockInfo weiterhin als normale Felder.
Neue Plugin-Felder würden in StockPortfolio auch nach dem Abflachen verloren
gehen, solange dessen Mapper und Cache nur ihre feste Feldliste übernehmen.

## Was Mike entscheiden müsste

Aktuell ist keine Umsetzung beauftragt. Die fachliche Frage für einen späteren
Zuschnitt lautet: Soll StockPortfolio bestimmte zusätzliche Kennzahlen nutzen,
oder beliebige neue Plugin-Felder automatisch darstellen? Eine flache Route
ersetzt diese Entscheidung nicht. Für beliebige Felder werden weiterhin
Definitionen für Bedeutung, Typ, Beschriftung und Einheit benötigt.

## Tatsächliche Nutzung in StockPortfolio

| Weg | Verbraucher | Bedeutung für eine neue Ansicht |
|---|---|---|
| `GET /quote/{isin}` und `GET /quote?symbol=…` | `StockInfoClient` → Quote-Store → `toQuoteCacheEntry` | Normale Kursabfrage verwendet eine feste Zuordnung in den Cache |
| `POST /refresh/{isin}` und `POST /refresh/by-symbol/{symbol}` | Derselbe Quote-Store und Mapper | Ein manueller Refresh muss dieselben Daten liefern; nur den GET-Weg umzustellen wäre unvollständig |
| `GET /instruments` | Instruments-Store, InstrumentsView, Hinzufügen-Dialog und Dashboard | Metadaten werden zusätzlich über den Katalog verwendet |
| Tages-/Intraday-Historie und `/health` | History- und Status-Store | Eigenständige Antwortverträge, keine dynamische Quote-Projektion erforderlich |

[Client](/Volumes/DevLocal/DevWeb/Production/StockPortfolio/src/api/client.ts),
[Mapper](/Volumes/DevLocal/DevWeb/Production/StockPortfolio/src/api/mappers.ts),
[Quote-Store](/Volumes/DevLocal/DevWeb/Production/StockPortfolio/src/stores/quotes.ts),
[API-Typen](/Volumes/DevLocal/DevWeb/Production/StockPortfolio/src/api/types.ts).

Der Quote-Mapper übernimmt Identifikator, Symbol, Preis, Währung, Typ, Name,
`ter`, `volatility`, `accumulating` sowie Zeit- und Cacheangaben. Weitere
Felder werden nicht generisch übernommen. TER und Volatilität erscheinen
beispielsweise im Positionsdetail und in der Instrumentliste. Eine
Auswertung beliebiger Plugin-Felder oder ein Abruf von `/fields` ist im
untersuchten API-Client nicht vorhanden.

## Was StockInfo schon auflöst

[QuoteResponse](../app/models.py) führt die bekannten Kennzahlen weiterhin
auf oberster Ebene. [CachedQuoteService](../app/services/quote_cache.py)
übernimmt wirksame Werte und die dynamischen `details` aus dem Speicher.
[merge_value](../app/details.py) entscheidet bereits: Quellenwert vor manueller
Eingabe; `0` und `false` sind echte Werte, keine Lücken.

Ein Detail enthält mit `value` deshalb bereits den ausgewählten Wert.
Zusätzlich transportiert es Einheit, Währung, Herkunft und gegebenenfalls
verdeckte manuelle Eingaben. „Auflösen“ wäre hier vor allem eine Änderung der
Darstellung, keine neue fachliche Berechnung.

Schematischer Ausschnitt, kein abgerufener Live-Kurs:

```json
{
  "ter": 0.2,
  "details": {
    "risk-demo.score": { "value": 7, "origin": "provider" }
  }
}
```

Die gewünschte vereinfachte Darstellung könnte daraus machen:

```json
{
  "ter": 0.2,
  "risk-demo.score": 7
}
```

Der bestehende Portfolio-Mapper verwirft `risk-demo.score` in beiden Formen.
Flache Ausgabe macht ein unbekanntes Feld noch nicht zu einem bekannten
Domain-Feld in StockPortfolio.

## Unabhängige Integrationslücke: Identität

StockPortfolios Typen beziehen sich laut Dateikopf auf OpenAPI 0.5.0 und
lesen `response.isin` beziehungsweise `instrument.isin`. StockInfo liefert
inzwischen eine `identity`-Union (`listed`, `pair`, `isin_only`), in der eine
ISIN je nach Form enthalten sein kann.

Eine isolierte Gegenprobe mit dem echten, transpilierten Portfolio-Mapper
und einer synthetischen Antwort im aktuellen Identitätsformat ergibt
`isin === undefined`. Bekannte Kennzahlen werden übernommen, unbekannte
Details bleiben sowohl verschachtelt als auch flach unberücksichtigt.
Das belegt die Mapper-Lücke, nicht einen durchgeführten Browserfehler im
produktiven Portfolio. Eine zusätzliche Detailroute allein behebt sie nicht.

## Vorschlag für eine zusätzliche Route

Eine additive, dokumentierte Projektionsroute ist sinnvoll, wenn mehrere
Konsumenten eine kompakte Werteansicht brauchen. Ihr endgültiger Pfad bleibt
im API-Entwurf festzulegen. Der bisherige `/quote`-Vertrag bleibt erhalten.

- **Dieselbe fachliche Antwort verwenden.**<br>
  Vorhandenen Quote-/Cache-Service wiederverwenden und erst danach projizieren.
  Keine zweite Beschaffungs-, Vorrang- oder Cachelogik. ISIN- und Symbolabruf,
  Refresh und Instrumentkatalog bei der Konsumentenumstellung gemeinsam prüfen.

- **Namen und Datentypen erhalten.**<br>
  Qualifizierte Plugin-Schlüssel wie `risk-demo.score` beibehalten. Nicht
  pauschal auf `score` kürzen. Dynamische Felder dürfen Core-Felder nicht
  überschreiben; bekannte doppelt dargestellte Felder brauchen eine explizite
  Projektionsregel. `null`, `false` und `0` bleiben unterscheidbar.

- **Einheiten und Bedeutung bleiben Teil des Vertrags.**<br>
  Eine Zahl allein erklärt weder Prozentmaßstab noch Betragswährung.
  Für eine reine Werteansicht Definitionen über `/fields` bereitstellen und
  wertabhängige Währungen nicht still verwerfen. Herkunft und manuelle Eingaben
  bleiben über die vollständige Antwort erreichbar. Eine konkrete Form für
  nötige Zusatzmetadaten wird vor Umsetzung festgelegt.

- **Dynamik in OpenAPI ehrlich darstellen.**<br>
  Laufzeitabhängige Plugin-Felder werden durch Verschieben auf die oberste
  Ebene nicht zu statisch garantierten Feldern. Schema und Portfolio-Typen
  müssen diese Erweiterbarkeit ausdrücken; reine TypeScript-Typecasts
  validieren eine Serverantwort nicht.

Meine Empfehlung: Zuerst den StockPortfolio-Vertrag und seine Mapper an die
aktuelle Identität anpassen und die tatsächlich gewünschten Zusatzfelder
benennen. Danach entscheiden, ob eine gemeinsame serverseitige Projektion
mehreren Konsumenten hilft oder eine kleine Normalisierung im vorhandenen
Portfolio-Mapper genügt. Die Projektionsroute ist ein Komfortvertrag, kein
Ersatz für die Anpassung des Konsumenten.

## Prüfumfang

69 TypeScript-/Vue-Quelldateien in StockPortfolio mit TypeScript-Compiler-API
und Vue-SFC-Parser inventarisiert; Client, Mapper, Cachetypen, Stores und
sichtbare Kennzahlen-Verbraucher geprüft. Auf StockInfo-Seite Antwortmodelle,
Quote-Router, Cache-/Merge-Pfad und vorhandene Detailtests gelesen.

Den echten Portfolio-Mapper isoliert mit synthetischen Daten ausgeführt.
Keine Online-Abfragen, keine Änderung von Arbeitsdaten, kein Browserlauf und
kein vollständiger Integrations- oder Testlauf. StockPortfolio enthält bereits
fremde uncommittete Änderungen; diese wurden ausschließlich gelesen.
