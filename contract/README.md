# `contract/` — der REST-Core als prüfbares Artefakt

Was StockInfo seinen Konsumenten zusagt, in einer Form, die eine Maschine lesen
kann. Erklärt wird der Vertrag in
[`docs/rest-core-contract.md`](../docs/rest-core-contract.md); **verbindlich ist
das, was hier liegt.**

```
contract/
├── core-contract.json           # der Vertrag: Felder, Nullability, Bedeutung, Regeln
├── openapi-core-snapshot.json   # gespeicherte OpenAPI-Form der erfassten Endpunkte
└── fixtures/                    # interne HTTP-Beispiele für die Vertragstests
```

Zur Laufzeit beantwortet **`GET /fields`** denselben Vertrag: Feldliste je
Antworttyp und `core_version`, ergänzt um das konfigurierte Detailschema,
`details_version` und `generation_id` aus der Datenbank. Ein Konsument speichert
seine Kopie unter `(generation_id, core_version, details_version)` zwischen und
erkennt an den Nummern, dass er neu holen muss — ohne den Inhalt zu
vergleichen. Dazu muss er `/fields` erneut abrufen.

`meaning` beschreibt die Felder von `core` und `plugin_contract` immer auf
Englisch. Die Sprache ist fest und unabhängig von `Accept-Language` oder der
Dashboard-Sprache.

`GET /instrument-types` ergänzt den Vertrag um die Asset-Typen der laufenden
Plugin-Konfiguration. Die drei `fixtures/instrument-types-*.json` zeigen
vollständige, leere und unvollständige HTTP-Auskünfte. Semantik und Statuswerte:
[Typkatalog](../docs/rest-core-contract.md#asset-typen-aus-der-plugin-konfiguration).

## Übersicht

- [Für Konsumenten](#für-konsumenten)
- [Für dieses Repo](#für-dieses-repo)
- [Wenn sich etwas ändert](#wenn-sich-etwas-ändert)

## Für Konsumenten

**Was die laufende App liefert, beschreiben drei Quellen:** `GET /fields`
(Felder, Detailschema, `generation_id`), `GET /instrument-types` (Typkatalog,
dieselbe UUID im Header `StockInfo-Generation`) und
[`openapi-core-snapshot.json`](openapi-core-snapshot.json), den
`tests/test_contract_openapi.py` laufend gegen die App prüft. Bekannte
Abweichungen bei Tageskursen und Pence-Währungen stehen in der
[REST-Referenz](../docs/rest-core-contract.md#die-begriffe-die-sich-sonst-niemand-erschließt).

**Unbekannte Felder werden ignoriert**, nicht als Fehler behandelt. Sonst
bricht die nächste additive Erweiterung den Konsumenten.

**Die Fixtures sind keine Beispielantworten der laufenden App.** Sie sind
interne Beispiele, mit denen `tests/test_contract.py` das Artefakt prüft, und
kein Laufzeitvertrag für Konsumenten.

[↑ Übersicht](#übersicht)

## Für dieses Repo

Die Fixtures sind kein reines JSON, sondern ein **HTTP-Umschlag** aus Status,
Headern und Rumpf. Gekürztes Strukturbeispiel; der Rumpf ist hier
ausgelassen:

```json
{
  "endpoint": "/quote/{isin}",
  "model": "quote",
  "contract_compliant": true,
  "violates": null,
  "note": "…",
  "request":  { "method": "GET", "path": "/quote/IE00B3RBWM25" },
  "response": {
    "status": 200,
    "headers": { "Content-Type": "application/json" },
    "body": {}
  }
}
```

Fixtures mit `contract_compliant: false` verletzen absichtlich die Regel, die
`violates` nennt; `note` erklärt sie.

Der `request` einer Fixture beschreibt einen konkreten Aufruf: Methode, Pfad
und Query-Namen werden gegen die Endpunktliste im Artefakt geprüft
(`endpoints`, dazu `query_notes` mit der Bedeutung je Parameter). Ein Beispiel
mit einem Parameter, den es nicht gibt, sieht sonst aus wie eine zugesagte
Funktion — FastAPI ignoriert Unbekanntes still.

`tests/test_contract.py` prüft beide Dateiarten gegeneinander: dieselben
Endpunktpfade, derselbe Headername, jede Erfolgsfixture erfüllt die
Pflichtfelder ihres Modells, und jede Fixture mit `violates` trägt die
genannte Verletzung wirklich.

Diese Prüfung läuft **ohne die App** und weist nur die Konsistenz der
Vertragsdateien nach. Sie bestätigt nicht die fachliche Übereinstimmung
jeder Fixture mit einer Live-Antwort.

```bash
.venv/bin/pytest tests/test_contract.py -q
```

`tests/test_contract_openapi.py` hält die andere Richtung: Es vergleicht die
**App** mit `openapi-core-snapshot.json` und schlägt an, sobald sich ein
Core-Modell, ein Core-Pfad, `/fields` oder `/instrument-types` ändert.
Eine beabsichtigte Vertragsänderung verlangt folgende Schritte:

```bash
# 1. core_version im Artefakt erhöhen (Major/Minor/Patch nach compatibility)
# 2. Schnappschuss erneuern:
UPDATE_CORE_SNAPSHOT=1 .venv/bin/pytest tests/test_contract_openapi.py -q
```

Der Schnappschuss deckt bewusst nur die zugesagten Pfade ab. Ein Abbild des
ganzen OpenAPI-Dokuments wäre bei jeder Änderung an einem Diagnoseendpunkt
rot, und einen Test, der ständig grundlos anschlägt, liest bald niemand mehr.

[↑ Übersicht](#übersicht)

## Wenn sich etwas ändert

`core_version` folgt SemVer — Major bei entferntem oder unverträglich
geändertem Pflichtfeld, Minor bei additiver Erweiterung, Patch bei einer
Klarstellung ohne Änderung am JSON. Die offene Detailmenge zählt getrennt über
`details_version`, die zur Laufzeit aus dem gespeicherten Detailschema stammt.

Wer ein Feld ergänzt, ergänzt **beides**: den Eintrag im Artefakt und mindestens
eine Fixture, die ihn zeigt. Der Test schlägt sonst nicht an — er prüft, was
dasteht, nicht was fehlt.

[↑ Übersicht](#übersicht)
