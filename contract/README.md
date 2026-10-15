# `contract/` — der REST-Core als prüfbares Artefakt

Was StockInfo seinen Konsumenten zusagt, in einer Form, die eine Maschine lesen
kann. Erklärt wird der Vertrag in
[`docs/rest-core-contract.md`](../docs/rest-core-contract.md); **verbindlich ist
das, was hier liegt.**

```
contract/
├── core-contract.json           # der Vertrag: Felder, Nullability, Bedeutung, Regeln
└── openapi-core-snapshot.json   # gespeicherte OpenAPI-Form der erfassten Endpunkte
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
Plugin-Konfiguration. Semantik und Statuswerte:
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

[↑ Übersicht](#übersicht)

## Für dieses Repo

`tests/test_contract_openapi.py` prüft die laufende **App** auf zwei Arten:

- Sie muss `openapi-core-snapshot.json` entsprechen. Der Test schlägt an,
  sobald sich ein Core-Modell, ein Core-Pfad, `/fields` oder
  `/instrument-types` ändert.
- Jedes Pflichtfeld im Artefakt muss im Schema der App Pflicht sein, und kein
  optionales Feld darf dort heimlich Pflicht sein. Jeder Pfad unter
  `endpoints` muss in der App existieren.

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

Wer ein Feld ergänzt, ergänzt **beides**: das App-Modell und den Eintrag im
Artefakt. Fehlt der Eintrag, sagt `/fields` das Feld nicht zu, auch wenn die
App es liefert.

[↑ Übersicht](#übersicht)
