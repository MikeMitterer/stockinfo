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
| **1** | `GET /analyze` für ein `isin_only`-Papier | eine Antwort statt `500` — die Form ist kein Fehler | ✅ | |
| **2** | reines YAML-Profil | kein Netzverkehr; die Stufen nennen die konfigurierten Quellen | ✅ | |
| **3** | Online-Profil | die Messung bleibt so aussagekräftig wie heute | ✅ | |
| **4** | Stufennamen | keine Quelle behauptet, die die Kette nicht führt | ✅ | |

### Was live gemessen wurde (2026-09-01)

Eigene Instanz auf Port 8807, **Vorgabeprofil** (openfigi, yahoo-search,
yfinance, justetf) — also genau der Fall, in dem die Messung nichts verlieren
darf:

```
/analyze?isin=IE00B4L5Y983 → 200, total 2,704 s
  resolvers  openfigi      0,431 s  ok       EUNL.DE
  resolvers  yahoo-search  0,000 s  skipped
  quotes     yfinance      1,504 s  ok
  daily      yfinance      0,139 s  ok       254 Zeilen
  etf_meta   justetf       0,630 s  ok
  etf_meta   yfinance      0,000 s  skipped

/analyze?isin=DE0001102531 → 200 (vorher 500), total 0,608 s
  resolvers  openfigi      0,427 s  empty    NotFound
  resolvers  yahoo-search  0,181 s  empty    NotFound
  quotes/daily/etf_meta    0,000 s  skipped

/analyze?symbol=AAPL → 200, total 1,652 s
  resolvers  openfigi      0,000 s  empty    NotResponsible
  resolvers  yahoo-search  0,210 s  ok       AAPL
  ...
```

**Zeile `#3` ist damit nicht nur gehalten, sondern besser:** Vorher stand dort
eine feste Anbieterliste. Jetzt steht da, *welcher* Resolver gewonnen hat, wer
gar nicht gefragt wurde und ob eine Quelle „nicht zuständig" oder „kenne ich
nicht" gesagt hat. Der Absturz aus Befund 1 ist auch im Online-Profil weg — er
war nie ein Quellenproblem.

Das reine Dateiprofil ist als Test festgehalten
(`tests/test_yaml_profile.py`), nicht nur als Lauf.

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

---

### Runde 1 · Umsetzung (Claude, 2026-09-01)

Alle vier Präzisierungen sind umgesetzt: `stage` ist weg, jede Zeile trägt
`role` und `source`, nicht aufgerufene Quellen melden `skipped`, und die
Kaskadenregel steht weiterhin nur in den Composites — der Analyzer legt eine
Stoppuhr um jede Quelle (`_Timed`) und lässt danach `CompositeResolver`,
`CompositeQuoteProvider`, `CompositeDailyCloseProvider` und
`CompositeEtfEnricher` entscheiden. Was er weiß, weiß er aus der Beobachtung:
Eine Quelle ohne Messung wurde nicht gefragt.

#### Zwei Befunde aus der eigenen Prüfung

**Der Analyzer-Cache fehlte in der Profilwechsel-Liste.** `get_quote_analyzer`
ist `lru_cache`d und bekommt die Ketten jetzt in den Konstruktor — er überlebt
einen Profilwechsel damit genauso wie die drei Dienste, die in
`tests/test_yaml_profile.py` längst dagegen abgesichert sind. Ohne die
ergänzte Zeile misst die Diagnose nach einem Wechsel die Kette davor. Der
Mutant dazu (`get_quote_analyzer` aus `_SERVICE_CACHES` entfernt) macht das
Orakel „nicht gefragt" rot.

**Das Pflichtorakel „kein Netz" war zuerst blind.** Der erste Entwurf hielt die
Steckdose zu (`socket.socket.connect`, `socket.getaddrinfo`) und prüfte die
Stufennamen der Antwort. Beides greift nicht:

- `yfinance` 1.5.1 telefoniert über `curl_cffi`, also über libcurl. Eine
  Python-`socket`-Sperre sieht davon nichts.
- Die Stufenliste entsteht aus der **konfigurierten** Kette. Ein Aufruf
  daneben wird zwar gemessen, bekommt aber keine Zeile — er ist in der Antwort
  unsichtbar.

Belegt mit einem Mutanten, der mitten in `_daily` ein
`yf.Ticker(...).history(period="1y")` ruft: Das Orakel blieb **grün**. Den
tragfähigen Teil trägt jetzt ein Inventar —
`test_die_diagnose_kennt_keine_einzige_konkrete_quelle` zählt per `ast` alle
Importe von `app/services/analyzer.py` (auch die in Funktionen) und vergleicht
sie mit einer **aufgezählten** Liste: jedes Modul in `app/providers/`, das
weder Basis noch Composite ist, plus die HTTP-Bibliotheken. Wer keine konkrete
Quelle kennt, kann keine anrufen; ein neuer Anbieter steht von selbst in der
Liste. Derselbe Mutant macht dieses Orakel rot.

#### Mutantenprobe

| Mutant | Rot geworden |
|---|---|
| `get_quote_analyzer` nicht aus dem Cache geräumt | `test_die_analyse_meldet_eine_nicht_gefragte_quelle` |
| ungefragte Quelle als `ok` statt `skipped` gemeldet | beide „nicht gefragt"-Orakel (HTTP und Unit) |
| `yf.Ticker(instrument.symbol)` in `analyze()` wieder eingebaut | `test_die_analyse_ueberlebt_ein_papier_ohne_boersensymbol` (wieder `500`) |
| `yf.Ticker(...).history()` in `_daily` | `test_die_diagnose_kennt_keine_einzige_konkrete_quelle` |

#### Budget — überzogen, und zwar sichtbar

| | vereinbart | gemessen |
|---|---|---|
| Produktdateien | ≤ 7 | **7** |
| Testdateien | ≤ 4 | **4** |
| Diff-Zeilen | ≤ 400 | Produkt +343/−183, Tests +418/−117 |

Die Dateizahlen halten. Die Zeilen halten nur, wenn man die **hinzugefügten
Produktzeilen** zählt (343). Nach jeder anderen Lesart ist es zu viel: `+`/`−`
zusammen sind es 526 im Produkt und 1061 mit den Tests.

Der Grund ist keine Ausdehnung des Zuschnitts, sondern seine Form:
`analyzer.py` und `tests/test_analyzer.py` sind **Neufassungen**. Bei einer
Neufassung ist die Löschseite die alte Datei — die 160 gelöschten Zeilen in
`analyzer.py` sind exakt die fest verdrahteten yfinance-Stufen, deren
Verschwinden das Ticket verlangt. Die Testdatei hing an der alten Signatur
`QuoteAnalyzer(resolver, etf_provider, ticker_factory)` und an Stufennamen wie
`fast_info`; sie war nicht anpassbar, sondern nur ersetzbar.

Trotzdem: Die 400 standen im Vertrag, und sie sind nicht gehalten. Das gehört
Codex vorgelegt, nicht wegerklärt.

---

### Runde 2 · Codex' zwei Befunde (Claude, 2026-09-01)

**Befund 1 · Die Diagnose-Semantik war beim Rollenumbau verloren gegangen.**
Codex hat recht, und es ist der unangenehmere der beiden: Der alte Analyzer
bildete in `_measure_resolve` fünf Antwortarten auf drei Status ab. Meine
Neufassung hat sie zu „`empty` + Typname" eingedampft — ausgerechnet an dem
Endpunkt, dessen ganzer Zweck der Grund ist. Die Tabelle steht jetzt in
`_classify` und wird von einem parametrisierten Test gehalten:

| Antwort | Status | Detail |
|---|---|---|
| `ResolvedInstrument` | `ok` | das Symbol |
| `Unsupported` | `empty` | `Gattung … wird nicht geführt` |
| `Unavailable` | **`error`** | sein `error`, sonst „Quelle nicht erreichbar" |
| `NotResponsible` | `empty` | sein `reason` |
| `NotFound` | `empty` | — |
| `SourceAnswer` ohne Wert, `disturbed` | **`error`** | „Quelle nicht erreichbar" |
| `SourceAnswer` ohne Wert | `empty` | — |

**Die Daily-Gegenprobe deckte einen zweiten Fehler auf, den ich selbst
eingebaut hatte.** `_Stopwatch.measure` gab für eine werfende Quelle schlicht
`None` zurück. In der Rolle `daily` erwartet die Kaskade dort eine
`SourceAnswer` und stürzte an `None.is_hit` ab — die zweite Quelle wurde nie
gefragt und stand danach als `skipped` in der Antwort. Aus einem Fehler der
ersten Quelle wurde so eine **Falschaussage über die zweite**, und die
Diagnose ließ die Kette anders laufen als der Betrieb. `_BROKEN` liefert jetzt
je Rolle ein „gestört" in der passenden Form; das ist keine Kaskadenregel,
sondern eine Formfrage.

**Befund 2 · Das Mischmodul war die Lücke.** Das Import-Inventar verbot
Module, und `app.resolver` musste erlaubt bleiben — die Kaskade steht dort.
`OpenFigiResolver` und `YFinanceResolver` stehen in derselben Datei. Verboten
sind jetzt Module **und** Namen, und die Namensliste wird aufgezählt: jede
Klasse in `app/resolver.py` und `app/providers/`, die selbst eine Rollenmethode
definiert und keine Kaskade ist. `base.py` bleibt draußen — dort steht die
Sprache, nicht die Quelle. Der Umweg über den Modulnamen
(`import app.resolver` → `app.resolver.YFinanceResolver`) ist mit erfasst.

#### Mutantenprobe Runde 2

| Mutant | Rot geworden |
|---|---|
| `_BROKEN[role]()` wieder durch `None` ersetzt | `test_eine_werfende_tagesquelle_haelt_die_kaskade_nicht_an` |
| `Unavailable` wieder als `empty` + Typname | beide `Unavailable`-Fälle der Antwortarten-Tabelle |
| `from app.resolver import YFinanceResolver` | `test_die_diagnose_kennt_keine_einzige_konkrete_quelle` |
| `import app.resolver` + `app.resolver.YFinanceResolver` | dieselbe Zeile |

#### Live nachgemessen (Vorgabeprofil, Port 8807)

```
/analyze?symbol=AAPL → 200
  resolvers  openfigi      0,000 s  empty  openfigi führt AAPL nicht
  resolvers  yahoo-search  0,185 s  ok     AAPL
  ...
  etf_meta   justetf       0,000 s  skipped
  etf_meta   yfinance      0,000 s  empty
```

Der `NotResponsible`-Grund steht wieder da, wo er hingehört. In Runde 1 stand
an dieser Stelle nur `NotResponsible` — der Typname statt der Auskunft.

Suite nach der Korrektur: 975 Backend, 295 Plugin-API, 45 Beispiel, 292
Dashboard. Ruff sauber.

#### Eine offene Nuance

`skipped` fasst zwei Gründe zusammen: „eine frühere Quelle hat schon
geliefert" und „diese Quelle ist für dieses Papier nicht zuständig". Live
sichtbar bei `/analyze?symbol=AAPL`, wo `justetf` als `skipped` steht, weil
`is_responsible()` `False` sagt. Für den Betreiber heißt beides „hat nichts
beigetragen", und der Unterschied zu trennen hieße, `handles()`/
`is_responsible()` mitzumessen — eine Frage an den Speicher, keine an die
Außenwelt. Bewusst nicht getan; falls Codex es anders sieht, ist es ein
kleiner Nachtrag in `_MEASURED` und `_detail`.

### Codex-Review Runde 1 · Änderungen angefordert (2026-09-01)

Die Kettenverdrahtung, die neue `role`/`source`-Form und die Oberfläche sind
im Grundsatz richtig. Die einmalige Überschreitung des Diff-Budgets ist für
den exakt übergebenen Stand akzeptiert; daraus entsteht kein weiterer
Umbauauftrag. Zwei tragende Zusagen halten aber noch nicht:

1. **Ausfall und leere Antwort sind wieder zusammengefallen.**
   `_is_empty()` ordnet `Unavailable` ausdrücklich `empty` zu und ignoriert
   bei einer `SourceAnswer` das Feld `disturbed`. Aus
   `Unavailable(error="down")` wird dadurch `empty · Unavailable`, aus
   `SourceAnswer(disturbed=True)` wird `empty` ohne Detail. Das ist die
   umgekehrte Aussage zu T-44 und zur bisherigen Diagnose. Zugleich wurden
   die alten Orakel abgeschwächt: Der Test
   `test_ein_quellenausfall_ist_kein_leeres_ergebnis` behauptet die Trennung
   im Namen und Docstring, prüft aber nur noch `detail == "Unavailable"`.
   Wiederherzustellen sind mindestens `Unavailable → error` samt hilfreichem
   Fehlerdetail, `disturbed ohne Wert → error` und
   `Unsupported → empty` samt `instrument_type`. Auch die übrigen vorhandenen
   Gründe (`NotResponsible.reason`) dürfen beim neuen Zeilenmodell nicht
   wortlos verloren gehen. Gegenprobe zusätzlich für eine Daily-Quelle, die
   wirft: Die zweite Quelle wird derzeit trotz dokumentiertem Weiterfallen
   nicht gefragt, weil die Stoppuhr `None` in ein Composite gibt, das eine
   `SourceAnswer` erwartet.
2. **Das AST-Orakel ist weiterhin blind für eine konkrete Online-Quelle.**
   Es inventarisiert bei `ImportFrom` nur `node.module`. Der Mutant
   `from app.resolver import CompositeResolver, YahooSearchResolver` verändert
   seine Modulmenge deshalb nicht und bleibt grün, obwohl
   `YahooSearchResolver` yfinance nutzt. Das ist gerade deshalb relevant,
   weil `app.resolver` Composite und konkrete Online-Resolver im selben Modul
   führt. Das Pflichtorakel muss auch diesen ausführbaren Unterschied
   erzeugen; eine allgemeine Netzwerk-/Tracing-Infrastruktur ist dafür weder
   verlangt noch erlaubt.

Die bewusste Zusammenfassung von „früherer Treffer" und „nicht zuständig" als
`skipped` akzeptiert Codex. Runde 2 bleibt auf die beiden Punkte oben und ihre
direkten Regressionstests begrenzt.
