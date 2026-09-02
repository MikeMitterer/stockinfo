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
| **1** | Inventar | alle Stellen, die `detail` füllen, sind aufgezählt und eingeordnet | ➖ | |
| **2** | Antwort | kein deutscher Fließtext mehr in der Nutzlast | ➖ | |
| **3** | Oberfläche EN und DE | die Zeile liest sich in beiden Sprachen vollständig | ➖ | |
| **4** | Mutant | ein Katalogeintrag entfernt rötet einen Test | ➖ | |

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
