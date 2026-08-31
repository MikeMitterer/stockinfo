# T-46 · Die Analyse geht an der Quellenkette vorbei

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend) | offen, **nicht** eingeplant | 2–4 h | `/analyze` misst die konfigurierte Kette statt fest verdrahteter Quellen | — |

- **Angelegt:** 2026-08-31, aus Mikes Frage „funktioniert die Analyse noch?"
- **Reihenfolge:** ausdrücklich **nicht** in die `priority_chain`. Wann es an
  die Reihe kommt, entscheidet Mike
- **Hängt ab von:** nichts. Berührt weder Vertrag noch Schema

**Löst:** Das Analysefenster verspricht zu zeigen, wie lange die App für ihre
Daten braucht. Es misst aber **nicht die App**, sondern yfinance und justETF —
unabhängig davon, was in `sources.yaml` steht. In einem Profil ohne Online-
Quelle geht es trotzdem ins Netz.

---

## Befund 1 · Ein Papier ohne Börsensymbol lässt die Route abstürzen

```
GET /analyze?isin=DE0001102531  →  HTTP 500  Internal Server Error
```

```
app/services/analyzer.py:73   ticker = self._ticker_factory(resolved_symbol)
yfinance/base.py:110          raise ValueError(f"Invalid ISIN number: {isin}")
```

Ein Papier der Form `isin_only` hat kein Börsensymbol. Die Auflösung liefert
deshalb die ISIN als `symbol`, und `yf.Ticker("DE0001102531")` wirft. Der
Zweig darüber fängt nur `resolved_symbol is None` ab — den Fall „aufgelöst,
aber nicht handelbar" gibt es dort nicht.

**Gemessen in beiden Profilen**, online wie rein YAML: derselbe `500`. Es ist
also kein Quellenproblem, sondern die Identitätsform aus T-31, die an dieser
Stelle nie ankam — dasselbe Muster wie beim Migrationswächter.

## Befund 2 · Im reinen YAML-Profil misst die Analyse trotzdem Yahoo

Gemessen an einer Instanz, deren Kette in **allen fünf Rollen** `yaml-file`
führt, ohne jede Online-Quelle:

```
GET /sources   →  resolvers, etf_meta, quotes, daily, fx: yaml-file
GET /analyze?isin=IE00B4L5Y983  →  200, total 2,444 s
   openfigi   0,000 s  ok  EUNL.DE
   fast_info  0,660 s  ok
   get_info   0,444 s  ok
   isin       0,589 s  ok
   history    0,171 s  ok   254 rows
   justetf    0,573 s  ok
```

**254 Zeilen Historie und ein justETF-Treffer in einem Profil, das keine
Online-Quelle hat.** Der `Analyzer` bekommt `yf.Ticker` als Vorgabe in den
Konstruktor (`app/services/analyzer.py:28`) und ruft justETF direkt; nur die
erste Stufe — die Auflösung — läuft über die konfigurierte Kette.

Drei Folgen, und die dritte ist die unangenehmste:

1. Die Zahlen beantworten nicht die Frage, die der Betreiber stellt. Er sieht,
   wie schnell Yahoo ist, nicht wie schnell **seine** Kette ist.
2. Die Stufen tragen Quellennamen (`openfigi`, `justetf`), die im YAML-Profil
   niemand konfiguriert hat. Die erste Stufe heißt `openfigi` und wurde von
   `yaml-file` beantwortet.
3. **Eine Instanz, die bewusst offline läuft, geht hier ins Netz.** Wer ein
   reines Dateiprofil wählt, tut das meist mit Absicht.

---

## Richtung — noch nicht entschieden

Der Kern ist nicht der Absturz, sondern die Frage, was die Analyse **ist**:
ein yfinance-Profiler oder eine Kettendiagnose. Die zweite Lesart würde die
Stufen aus den Rollen bilden (`resolvers`, `quotes`, `daily`, `etf_meta`, `fx`)
und je Rolle die Quelle nennen, die geantwortet hat — dieselbe Auskunft, die
`RawQuote.source` seit T-41 schon trägt.

Das ist mehr als eine Fehlerbehebung und gehört deshalb vor den Beginn
entschieden, nicht während der Umsetzung.

---

## Verify

Legende: ✅ live bestätigt · ➖ nicht geprüft.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | `GET /analyze` für ein `isin_only`-Papier | eine Antwort statt `500` — die Form ist kein Fehler | ➖ | |
| **2** | reines YAML-Profil | kein Netzverkehr; die Stufen nennen die konfigurierten Quellen | ➖ | |
| **3** | Online-Profil | die Messung bleibt so aussagekräftig wie heute | ➖ | |
| **4** | Stufennamen | keine Quelle behauptet, die die Kette nicht führt | ➖ | |

## Nicht-Ziele

- Keine neue Diagnoseansicht, keine Historie der Messungen.
- Keine Änderung an der Kaskade selbst.

## Auflösung

_(offen)_
