# `contract/` — der REST-Core als prüfbares Artefakt

Was StockInfo seinen Konsumenten zusagt, in einer Form, die eine Maschine lesen
kann. Erklärt wird der Vertrag in
[`docs/rest-core-contract.md`](../docs/rest-core-contract.md); **verbindlich ist
das, was hier liegt.**

```
contract/
├── core-contract.json   # der Vertrag: Felder, Nullability, Bedeutung, Regeln
└── fixtures/            # echte HTTP-Antworten dazu, positiv und negativ
```

## Für Konsumenten

Die Fixtures sind kein reines JSON, sondern ein **HTTP-Umschlag** aus Status,
Headern und Rumpf — anders ließe sich das Header-Verhalten der Generation gar
nicht prüfen:

```json
{
  "endpoint": "/quote/{isin}",
  "model": "quote",
  "contract_compliant": true,
  "violates": null,
  "note": "…",
  "request":  { "method": "GET", "path": "…" },
  "response": { "status": 200, "headers": { … }, "body": { … } }
}
```

Ein Konsument — etwa StockPortfolio — fährt seine Mapper gegen diese Dateien,
ohne StockInfo zu starten und ohne das Repository zu klonen. Zwei Regeln dabei:

- **`contract_compliant: false` ist Absicht.** Diese Fixtures zeigen, was ein
  Konsument **erkennen** können muss: eine generationenfähige Antwort ohne
  Header, ein `/generation`, dessen Header dem Rumpf widerspricht. Wer sie
  fehlerfrei durchlaufen lässt, hat einen blinden Fleck. `violates` nennt die
  verletzte Regel.
- **Unbekannte Felder werden ignoriert**, nicht als Fehler behandelt. Sonst
  bricht die nächste additive Erweiterung den Konsumenten.

## Für dieses Repo

`tests/test_contract.py` prüft beide Dateiarten gegeneinander: dieselben
Endpunktpfade, derselbe Headername, jede Erfolgsfixture erfüllt die
Pflichtfelder ihres Modells, jede `/generation`-Fixture hält Header und Rumpf
zusammen.

Bewusst **ohne die laufende App** (T-24 `#7i`): Der Vertrag muss prüfbar sein,
bevor die Routen existieren, die T-25 baut. Dass die laufende App diesem
Artefakt entspricht, nimmt T-25 `#7j` ab.

```bash
.venv/bin/pytest tests/test_contract.py -q
```

## Wenn sich etwas ändert

`core_version` folgt SemVer — Major bei entferntem oder unverträglich
geändertem Pflichtfeld, Minor bei additiver Erweiterung, Patch bei einer
Klarstellung ohne Änderung am JSON. Die offene Detailmenge zählt getrennt über
`details_version` (siehe T-26).

Wer ein Feld ergänzt, ergänzt **beides**: den Eintrag im Artefakt und mindestens
eine Fixture, die ihn zeigt. Der Test schlägt sonst nicht an — er prüft, was
dasteht, nicht was fehlt.
