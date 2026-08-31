# T-44 · Zwei Fehlerwege sagen nicht, was sie meinen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend) | offen, **nicht** eingeplant | 1–2 h | zwei REST-Fehlerwege auf Kennung und richtigen Statuscode bringen | — |

- **Angelegt:** 2026-08-31, aus dem T-42-Browserlauf
- **Reihenfolge:** ausdrücklich **nicht** in die `priority_chain` geschoben.
  Wann es an die Reihe kommt, entscheidet Mike
- **Hängt ab von:** nichts

**Löst:** Zwei Stellen brechen die eigene Zusage aus `ErrorDetail` — *„Der
Text gehört ins UI und muss in DE und EN vorliegen"* —, und eine davon
verwechselt zusätzlich zwei Sachverhalte, die der Plugin-Vertrag seit T-31
ausdrücklich trennt.

---

## Befund 1 · `/fx` meldet einen Ausfall, wo keiner ist

Gemessen im YAML-Profil, in dem die Datei nur das Paar `CAD/EUR` führt:

```
GET /fx?base=CAD&quote=USD  →  HTTP 502
{"detail":"Kein Wechselkurs für CAD/USD"}
```

**`502` heißt „die Gegenstelle ist ausgefallen".** Hier wurde die Quelle
gefragt und hat geantwortet: Sie führt dieses Paar nicht. Das ist ein `404`.

Genau diese Unterscheidung führt der Plugin-Vertrag als `NotFound` gegen
`Unavailable`, und T-31 hat sie eingeführt, weil ein Ausfall, der als „nicht
gefunden" ankommt, gespeicherte Werte verwirft. `app/routers/fx.py:31` wirft
beide Fälle in denselben `FxUnavailableError` und beantwortet sie mit
demselben Code.

Die Folge im Betrieb: Ein Betreiber sieht `502` und sucht den Fehler bei
seiner Quelle statt in seiner Datei.

**Nebenbefund:** `detail` ist deutscher Fließtext. Das Dashboard kann deshalb
nur seine eigene Kategorie zeigen („Wechselkurs konnte nicht geladen werden")
und nicht den Grund — es wirft nichts weg, es bekommt nichts.

## Befund 2 · `normalize_isin` lehnt mit Fließtext ab

```
GET /quote/BTC-EUR  →  HTTP 422
{"detail":"Ungültiges ISIN-Format: BTC-EUR"}
```

`app/routers/validation.py:41`. Dieselbe Sorte Zusagenbruch wie oben, eine
Ebene tiefer. Notiert seit T-35; das Dashboard erreicht die Stelle nicht, weil
es ISIN und Symbol selbst unterscheidet — ein anderer Client tut das nicht.

---

## Warum das nicht nebenbei erledigt wurde

Ein Statuscode ist REST-Vertrag. In T-42 galt für den begleiteten Browserlauf
eine Lockerung für **Anzeigekorrekturen**; Vertrag, Schema und Architektur
blieben ausdrücklich checkpoint-pflichtig. Beide Befunde sind deshalb
gemessen und dokumentiert, aber nicht angefasst.

---

## Verify

Legende: ✅ live bestätigt · ➖ nicht geprüft.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | `GET /fx` mit unbekanntem Paar | `404` mit Kennung und Parametern, nicht `502` mit Fließtext | ➖ | |
| **2** | `GET /fx` bei echtem Ausfall | weiterhin `502` — die Unterscheidung ist der Zweck der Änderung | ➖ | |
| **3** | `normalize_isin` | Kennung statt Fließtext; der Katalog kennt sie in DE und EN | ➖ | |
| **4** | Dashboard | die Meldung nennt den Grund, nicht nur die Kategorie | ➖ | |
| **5** | `contract/core-contract.json` | die geänderten Codes stehen dort, wo der Vertrag sie zusagt | ➖ | |

## Nicht-Ziele

- Keine neuen Endpunkte, kein Umbau des FX-Dienstes.
- Keine Änderung an der Kaskade selbst — sie tut das Richtige, nur die
  Übersetzung ihres Ergebnisses stimmt nicht.

## Auflösung

_(offen)_
