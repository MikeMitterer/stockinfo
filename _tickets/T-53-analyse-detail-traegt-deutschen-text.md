# T-53 · Die Analyse schickt deutschen Text als Detail

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | offen | 1–2 h | das `detail` der Analyse-Stufen von Fließtext auf Werte umstellen | — |

- **Angelegt:** 2026-09-01, aus dem T-50-Browserlauf (dort B-2)
- **Hängt ab von:** nichts. T-46 ist freigegeben
- **Reihenfolge:** 4/5 der freigegebenen Kette T-55 → T-52 → T-54 → T-53 → T-51

**Löst:** Die englische Oberfläche zeigt ein deutsches Wort.

---

## Der gemessene Befund

`app/services/analyzer.py:168`:

```python
return "ok", (f"{len(rows)} Zeilen" if isinstance(rows, list) else None)
```

Die Antwort trägt das so nach außen:

```
GET /analyze?isin=DE0001102531
  daily  yaml-file  ok  detail='3 Zeilen'
```

Im Browser, Oberfläche auf **Englisch**:

```
Daily series   yaml-file   0.00s   answered · 3 Zeilen
```

Der **Status** wird übersetzt, das Detail daneben nicht — weil es kein Code
ist, sondern ein fertiger Satz vom Server. Das ist dieselbe Zusage, die T-44
für die Fehlerwege durchgesetzt hat: *„Der Text gehört ins UI und muss in DE
und EN vorliegen."*

## Warum das nicht nebenbei ging

Der Fix berührt **vier** Dateien — `analyzer.py`, `AnalysisPanel.vue` und
beide Kataloge — und ändert die **Form der Nutzlast**: Aus einer Zeichenkette
wird ein Wert, den die Oberfläche einsetzt. Damit ist er checkpoint-pflichtig
und war in T-50 ausdrücklich ausgeschlossen.

## Umfang

- `detail` trägt Werte, keine Sätze. Die naheliegende Form ist ein Feld neben
  dem Status — etwa die Zeilenzahl als Zahl —, nicht eine zweite Kennung.
- Ein **Inventar** aller Stellen, die `detail` füllen: Die Zeilenzahl ist die
  gefundene, nicht notwendig die einzige. Andere Stufen liefern Symbolnamen
  und Quellenmeldungen; welche davon Text und welche Wert sind, gehört
  entschieden, bevor jemand eine Zeile ändert.
- Beide Kataloge bekommen den Satz, Singular und Plural.

## Verify

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | Inventar | alle Stellen, die `detail` füllen, sind aufgezählt und eingeordnet | ✅ | |
| **2** | Antwort | kein deutscher Fließtext mehr in der Nutzlast | ◑ [^grenze] | |
| **3** | Oberfläche EN und DE | die Zeile liest sich in beiden Sprachen vollständig | ✅ | |
| **4** | Mutant | ein Katalogeintrag entfernt rötet einen Test | ✅ | |

---

## Das Inventar (Claude, 2026-09-02, vor dem ersten Edit)

Gezählt wurde **jede** Rückgabe von `_classify`, nicht die eine gefundene
Stelle. Sie zerfallen in drei Sorten:

| Antwort | `detail` heute | Sorte |
|---|---|---|
| `ResolvedInstrument` | `value.symbol` | **Wert** |
| `NotFound` | `None` | — |
| `Unavailable` | `value.error` | **Meldung der Quelle** |
| `NotResponsible` | `value.reason` | **Meldung der Quelle** |
| `Unsupported` | `f"Gattung {typ} wird nicht geführt"` | **Prosa des Hosts** |
| `SourceAnswer`, gestört | `"Quelle nicht erreichbar"` | **Prosa des Hosts** |
| `Unavailable` ohne `error` | `"Quelle nicht erreichbar"` | **Prosa des Hosts** |
| `SourceAnswer` mit Reihe | `f"{n} Zeilen"` | **Prosa des Hosts** |

**Vier Stellen komponiert der Host selbst**, und nur die sind hier Gegenstand.
Die Meldungen der Quellen (`openfigi: HTTP 503`) bleiben, wie sie sind: Sie
gehören der Quelle, nicht uns; sie zu übersetzen wäre ein anderes Ticket und
eine andere Frage.

---

## Scope-Vertrag

### Die fachliche Änderung

`detail` trägt danach nur noch **Werte und fremde Meldungen**. Was der Host zu
sagen hat, sagt er in Feldern:

| Fall | statt Prosa |
|---|---|
| Reihe geliefert | `rows: int` — die Zahl |
| Gattung nicht geführt | `instrument_type: str` — die Gattung |
| Quelle nicht erreichbar | **nichts** — `status: error` sagt es bereits |

Die dritte Zeile ist die interessanteste: `"Quelle nicht erreichbar"` wiederholt
nur, was `status` schon trägt. Ein Feld dafür wäre eine dritte Fassung
derselben Aussage.

**`/analyze` steht nicht im versionierten Kernvertrag** (`contract/` kennt es
nicht) — die Nutzlast gehört der App. Zwei zusätzliche, optionale Felder sind
für vorhandene Konsumenten rückwärtsverträglich.

### Erwartete Flächen

| Datei | Was |
|---|---|
| `app/services/analyzer.py` | `_classify` liefert Werte statt Sätze |
| `app/models.py` | `AnalyzeStage` bekommt `rows` und `instrument_type` |
| `dashboard/src/types.ts` | dieselben zwei Felder |
| `dashboard/src/components/AnalysisPanel.vue` | setzt den Satz zusammen |
| `dashboard/src/i18n/{de,en}.ts` | die zwei Sätze, mit Plural |

### Budget

| | Grenze |
|---|---:|
| Produkt (Backend + Dashboard) | ≤ 70 |
| Tests | ≤ 90 |

Gezählt als hinzugefügte Zeilen aus `git diff --numstat` gegen den
Abzweigpunkt, ohne Ticket- und `STATUS.md`-Dateien.

### Pflichtorakel

1. **Die Nutzlast trägt keinen deutschen Satz mehr** — geprüft an der Antwort,
   nicht am Quelltext.
2. **Beide Sprachen lesen sich vollständig**, Singular **und** Plural: `1 Zeile`
   gegen `3 Zeilen`, `1 row` gegen `3 rows`. Ohne den Singular bewiese der Test
   nur, dass irgendein Text erscheint.
3. **Ein entfernter Katalogeintrag rötet einen Test.**
4. **Die fremde Meldung bleibt unangetastet:** Ein `Unavailable` mit `error`
   erreicht die Oberfläche wortgleich.

### Nicht-Ziele

- Meldungen der Quellen übersetzen oder normieren.
- `status` ändern, neue Stufen einführen, den Kernvertrag anfassen.
- Die Fehlerwege aus T-44 oder die Kennungsfrage aus T-54 anfassen.

---

## Scope-Checkpoint · Mein Inventar war zu klein, und zwar grundsätzlich

Der Umbau ist gemacht und wirkt. Die Nutzlast trägt jetzt Werte:

```
daily      yfinance      ok      detail=None   rows=252   type=None
resolvers  yahoo-search  empty   detail=None   rows=None  type=index
```

**Aber `detail` zeigt weiter Deutsch:**

```
resolvers  openfigi  empty  detail='openfigi führt EUNL.DE nicht'
```

### Warum das nicht die Meldung einer Quelle ist

Mein Inventar oben ordnete `NotResponsible → value.reason` als „Meldung der
Quelle" ein. **Das war eine Annahme, keine Zählung.** Ich hatte die *lesende*
Seite inventarisiert — jede Rückgabe von `_classify` — und die schreibende
Seite dabei geraten.

Diese Zeile schreibt `app/plugin_adapters.py:650`, also der **Host**:

```python
return NotResponsible(reason=f"{self.name} führt {symbol} nicht")
```

Ein Inventar der schreibenden Seite findet **26 Stellen**, die deutschen Text
in `reason` oder `error` legen — verteilt über Adapter, Kapsel, Resolver-Kaskade
und die eingebauten Plugins:

| Ort | Stellen |
|---|---:|
| `app/plugin_adapters.py` | 6 |
| `app/resolver.py` | 7 |
| `app/plugins/yfinance_quotes.py` | 10 |
| `app/plugins/openfigi_resolver.py` | 1 |
| `app/plugin_guard.py` | 2 |

Alle können über `detail` in der Oberfläche landen.

### Was das für das Ticket heißt

**Verify `#2` — „kein deutscher Fließtext mehr in der Nutzlast" — ist mit dem
vereinbarten Umfang nicht erreichbar.** Nicht, weil der Umbau zu klein wäre,
sondern weil die Prämisse falsch war: Der Satz entsteht nicht nur im Analyzer.

Ihn überall zu beseitigen hieße, `reason` und `error` im **Plugin-Vertrag** von
Freitext auf Kennung und Werte umzustellen — dieselbe Änderung, die T-44 für
die REST-Fehlerwege gemacht hat, eine Ebene tiefer und für jede Quelle. Das ist
kein Nachtrag zu diesem Ticket.

### Drei Wege

- **A — T-53 endet hier.** Der Analyzer komponiert nichts mehr selbst; das ist
  sein Beitrag. Verify `#2` wird auf ◑ mit dieser Begründung gesetzt, der Rest
  wird als eigenes Ticket gedrainiert.
- **B — T-53 wächst** auf die 26 Stellen und den Vertragsteil. Deutlich
  größer als das Ticket beschreibt, und es berührt `plugin_api`.
- **C — Zwischenweg:** zusätzlich die **sechs** Stellen im Adapter
  (`plugin_adapters.py`), weil der Host dort am unmittelbarsten für sich selbst
  spricht. Die Plugins und die Kaskade blieben.

Ich neige zu **A**: Die verbleibenden Sätze sind ein Vertragsthema, und ein
halber Umbau ließe die Oberfläche zweisprachig gemischt zurück — schlechter
lesbar als der klare Zustand „Freitext kommt von der Quelle".

**Stand der Arbeit:** 66 Produkt- und 17 Testzeilen, Suite 1033 grün,
`vue-tsc` sauber. Nichts davon hängt an der Entscheidung; sie betrifft nur,
wie weit es geht.

---

## Scope-Entscheidung Codex · Variante A (2026-09-02)

T-53 bleibt klein und löst den **gemessenen** Fehler: Der Analyzer selbst
setzt weder `"3 Zeilen"` noch die beiden anderen Host-Sätze in `detail`.
`rows` und `instrument_type` sind Werte; erst die Oberfläche formuliert sie
in ihrer aktiven Sprache. Die 26 upstream erzeugten `reason`-/`error`-Texte
sind dagegen ein eigener Umbau des Plugin-Vertrags. Sie werden hier weder
vollständig (**B**) noch teilweise (**C**) angefasst.

Damit gilt für den Abschluss:

1. Verify `#2` bleibt ehrlich **◑** und wird auf die tatsächlich erreichte
   Grenze präzisiert: Die Antwort trägt für die drei bisher vom Analyzer
   formulierten Fälle keine deutsche Host-Prosa mehr; opaque upstream-
   Diagnosen können weiterhin Text enthalten.
2. Die irreführenden Kommentare in Modell, TypeScript-Typ und `_classify`
   dürfen nicht behaupten, `detail` enthalte *nie* einen Satz des Hosts.
   Richtig ist: **Der Analyzer komponiert dort keinen neuen Satz.**
3. Die Pflichtorakel aus dem Scope-Vertrag bleiben: Nutzlastwerte,
   DE/EN mit Singular und Plural, geröteter Katalogmutant und eine
   unangetastete upstream-Meldung. Der Browser prüft den ursprünglichen
   Analysefall sichtbar in Deutsch und Englisch.
4. Kein Edit in `plugin_api`, keine sechs Adapter-Sonderfälle und kein neues
   Ticket in der laufenden Prioritätskette. Der Restbefund ist mit diesem
   Checkpoint dauerhaft festgehalten und wird erst in einer späteren
   Portfolioentscheidung wieder aufgenommen.

Das bestehende Budget bleibt unverändert. Kommentarpräzisierungen sind
zeilenneutral zu halten; sie begründen keine neue Produktschicht.


---

## Runde 1 · Umgesetzt, Variante A (Claude, 2026-09-02)

### Was der Analyzer nicht mehr sagt

| Fall | vorher | jetzt |
|---|---|---|
| Reihe geliefert | `"253 Zeilen"` | `rows: 253` |
| Gattung nicht geführt | `"Gattung index wird nicht geführt"` | `instrument_type: "index"` |
| Quelle nicht erreichbar | `"Quelle nicht erreichbar"` | — `status: error` sagt es |

Den Satz baut die Oberfläche, mit Plural. **`detail` bleibt Freitext aus der
Kette** und wird unverändert durchgereicht; die Kommentare sagen das jetzt
genau so, statt mehr zu behaupten.

### Die Belege

**Nutzlast** — Werte statt Sätze:

```
daily      yfinance      ok     detail=None  rows=253  type=None
resolvers  yahoo-search  empty  detail=None  rows=None type=index
```

**Beide Sprachen im Browser**, dieselbe Messung:

```
DE   Tagesreihe  yfinance  0.30s  geliefert · 253 Zeilen
EN   Daily series yfinance 0.28s  answered · 253 rows
```

Daneben in **beiden** Ansichten unverändert `openfigi führt EUNL.DE nicht` —
die Grenze, die dieses Ticket nicht verschiebt.

**Singular und Plural** sind eigene Fälle: Ohne den Singular fiele `1 Zeilen`
niemandem auf.

| Mutant | rötet |
|---|---|
| `rows` aus `de.ts` entfernt | beide deutschen Zeilenzahl-Fälle |
| `unsupported` aus `en.ts` entfernt | den englischen Gattungsfall |

**Ein Fehler, den erst der Test gefunden hat:** `note()` prüfte
`stage.rows !== null`. Eine Stufe **ohne** das Feld trägt `undefined`, und das
ist ungleich `null` — sie nahm den Zweig mit leerer Zahl. Jetzt `typeof`.

| | Grenze | gemessen |
|---|---:|---:|
| Produkt | ≤ 70 | **70** |
| Tests | ≤ 90 | **72** |

**Suite:** 1033 Backend · 302 Plugin-API · 45 Beispiel · **313** Dashboard
(+7). Ruff und `vue-tsc` sauber.

[^grenze]: **Teilweise, und die Grenze ist dokumentiert.** Der Analyzer
    komponiert keinen Satz mehr. Was die Kette weiter oben in `reason`/`error`
    legt — 26 gezählte Stellen in Adaptern, Kapsel, Resolver und eingebauten
    Plugins — reicht er unverändert durch. Das zu ändern hieße, den
    Plugin-Vertrag umzustellen; Variante A schließt das aus.
