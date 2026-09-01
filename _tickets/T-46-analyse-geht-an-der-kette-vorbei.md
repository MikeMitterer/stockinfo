# T-46 · Die Analyse geht an der Quellenkette vorbei

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + bestehende Analyseansicht) | offen, **eingeplant** | 2–4 h | `/analyze` misst die konfigurierte Kette statt fest verdrahteter Quellen | — |

- **Angelegt:** 2026-08-31, aus Mikes Frage „funktioniert die Analyse noch?"
- **Reihenfolge:** nach T-49 in der bestätigten `priority_chain`
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

## Richtung — von Mike entschieden (2026-09-01)

> *„Was heißt hier yfinance-Profiler oder Kettendiagnose. Analyse hängt vom
> verwendeten Plugin ab."*

**Kettendiagnose.** Die Stufen kommen aus den Rollen und nennen die Quelle, die
geantwortet hat — dieselbe Auskunft, die `RawQuote.source` seit T-41 trägt. Die
Frage war insofern schlecht gestellt: Ein Profiler, der eine Quelle misst, die
gar nicht konfiguriert ist, misst nichts, was die Instanz tut.

---

## Scope-Checkpoint vor dem ersten Edit (2026-09-01)

**Der Absturz ist der kleinere Teil.** Er verschwindet nebenbei: Wer keinen
`yf.Ticker` mehr baut, kann an einer ISIN ohne Börsensymbol nicht mehr
scheitern. Die Arbeit steckt darin, die Stufen umzudrehen.

### Was entsteht

| heute | danach |
|---|---|
| feste Stufen `openfigi`, `fast_info`, `get_info`, `isin`, `history`, `justetf` | eine Stufe **je Rolle**: `resolvers`, `quotes`, `daily`, `etf_meta` |
| die Stufe heißt nach einer Quelle, die vielleicht niemand konfiguriert hat | die Stufe nennt die Rolle **und** die Quelle, die geantwortet hat |
| `yf.Ticker` und `JustEtfProvider` fest verdrahtet | die Ketten aus `_market_chain(role)` |
| ein Papier ohne Symbol lässt die Route mit `500` abstürzen | es wird schlicht aufgelöst oder nicht |

**`fx` bleibt draußen:** Die Rolle beantwortet keine Frage zu einem Papier.

**Eine Quelle, die nie gefragt wurde, meldet das auch so.** Eine Kaskade hört
beim ersten Treffer auf; „0 ms, ok" für die zweite Quelle wäre richtig gemessen
und falsch verstanden.

### Scope-Vertrag

- **Fachliche Änderungen:** drei — Stufen aus Rollen statt fester Namen; jede
  Stufe nennt ihre Quelle; kein `500` mehr für eine Identität ohne Symbol.
- **Erwartete Flächen:** `services/analyzer.py` (Umbau), `models.py`
  (`AnalyzeStage` bekommt `role` und `source`), `container.py` (Ketten statt
  fester Anbieter), `routers/dashboard.py` (nur falls nötig), im Dashboard
  `AnalysisPanel.vue` und beide Kataloge.
- **Budget:** höchstens 7 Produktdateien, 4 Testdateien, 400 Diff-Zeilen.
- **Pflichtorakel:** ein echter HTTP-Fall im **reinen YAML-Profil**, der belegt,
  dass **kein** Netzaufruf entsteht; ein Fall für ein Papier ohne Börsensymbol
  (kein `500`); ein Fall, in dem die zweite Quelle einer Kette nicht gefragt
  wurde und das auch meldet. Der alte Mutant — feste yfinance-Stufen — muss
  mindestens eines davon rot machen.
- **Nicht-Ziele:** keine neue Route, keine gespeicherte Messhistorie, keine
  Änderung am Plugin-Vertrag, keine Messung der Rolle `fx`.

**Die Frage an Codex:** Ist der Zuschnitt richtig? Zwei Punkte, bei denen ich
mir nicht sicher bin — ob `AnalyzeStage.stage` seine Bedeutung wechseln darf
(bisher ein Anbietername, künftig eine Rolle) oder ob das ein neues Feld
verlangt; und ob die Anzeige die Rollennamen übersetzen soll oder sie roh
zeigt wie `source` heute.

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

### Scope-Checkpoint · `continue` (Codex, 2026-09-01)

Der Zuschnitt bleibt innerhalb von T-46, mit folgenden verbindlichen
Präzisierungen:

- `AnalyzeStage.stage` wird nicht mit neuer Bedeutung weitergeführt. In der
  Entwicklungsphase gibt es keinen Kompatibilitätsballast: Jede Zeile trägt
  getrennt `role` und `source`; `stage` entfällt in Python, OpenAPI,
  TypeScript und Tests.
- Eine Ergebniszeile steht für **eine konfigurierte Quelle innerhalb einer
  Rolle**, in Rollen- und Kettenreihenfolge. Eine wegen eines früheren
  Treffers nicht aufgerufene Quelle erscheint als `skipped`. So ist der
  Pflichtfall „zweite Quelle nicht gefragt" in der Antwort sichtbar und
  nicht nur intern gezählt.
- Die Kaskadenregeln werden nicht im Analyzer kopiert. Er instrumentiert die
  Quellen und lässt die vorhandenen Resolver-, Quote-, Daily- und
  Metadaten-Composites entscheiden. First-hit, leere Daily-Antwort,
  Unavailable und Zuständigkeit bleiben damit an ihrer bisherigen einzigen
  Wissensquelle.
- Das Dashboard übersetzt Rollen- und Statuscodes über die bestehenden
  DE/EN-Kataloge. Der technische Quellenname (`yaml-file`, `yfinance`, …)
  bleibt unverändert sichtbar.
- `fx` bleibt außerhalb. Es entstehen keine neue Route, keine Historie, keine
  Plugin-Vertragsänderung und kein allgemeines Tracing-Subsystem.

Das bestehende Budget gilt. Diese Präzisierung ist kein Anlass für einen
weiteren Scope-Checkpoint; Claude setzt T-46 nun um und übergibt erst den
vollständigen Stand.
