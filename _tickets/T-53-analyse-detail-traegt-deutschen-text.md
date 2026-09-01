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
