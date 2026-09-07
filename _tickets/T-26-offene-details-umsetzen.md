# T-26 · Offene Detailfelder tatsächlich durchreichen

Plugin-Felder werden jetzt gespeichert, über REST ausgeliefert und im Dashboard
anhand ihrer Deklaration angezeigt. Der erste UI-Test ist gelaufen; die
unabhängige Prüfung durch Claude steht noch aus. T-56/F bleibt bis dahin offen.

## Für dich

Aktuell ist keine weitere Entscheidung oder Wiederholung des Tests nötig.
Dein Auftrag vom 2026-09-07 gilt: **Codex implementiert einschließlich REST,
UI und erstem UI-Test; Claude verifiziert anschließend.** Die Rückmeldungen
zur Oberfläche bleiben unverändert in [T-56](T-56-was-mike-im-ui-pruefen-soll.md).
T-62 zum Anzeigenamen bleibt offen.

## Umsetzung und technische Nachweise

| Repo | Time-box | Scope | GH-Issue |
|---|---|---|---|
| StockInfo | ursprünglich 1 Tag | Plugin-Katalog → Persistenz → REST → Dashboard | — |

**Ergebnis:** Ein korrekt deklariertes neues Feld übersteht den Weg von einem
Datei-Plugin bis zum REST-Ergebnis und zur Bearbeitung im Browser, ohne eine
Feldliste im Dashboard zu ändern.

Die drei fachlichen Teile sind Feldschema samt Anwendbarkeit/Version,
generischer Speicher samt Migration/Quellenvorrang und REST/UI-Durchleitung.
Betroffen sind Plugin-API, Registry/Adapter, Repository/Service, REST-Vertrag
und Dashboard. Das entspricht dem ausdrücklich erweiterten Auftrag; ein
beziffertes Dateibudget wurde vor der Umsetzung allerdings nicht eingetragen.
Der Umfang muss deshalb bei der Übergabe ausdrücklich mitgeprüft werden.

Nicht-Ziele: T-25 vollständig umsetzen, Namen editierbar machen (T-62),
Börsenkatalog erweitern (T-30), neue Chart-Funktionen oder Plugin-Installation.
Der Umsetzungsplan steht in
[2026-09-07-t26-open-details.md](../docs/superpowers/plans/2026-09-07-t26-open-details.md).

### Verify

**B** = isolierter Browserlauf auf `http://127.0.0.1:5186/#/assets`,
Backend `http://127.0.0.1:8936`, eigenes temporäres Datenvolume,
Quellen `risk-demo` + `yaml-file`. **A** = automatisierter Test mit eigener DB.
Die Browserinstanz ist eine Testinstanz; ihre Laufzeit ist kein Betriebsversprechen.

| # | Lauf | Handgriff | Nachweis | woher | AI |
|---|---|---|---|---|:--:|
| 1 | B/A | ETF mit neuem `risk-demo.score` aufnehmen | Feld gespeichert und nach erneutem Lesen vorhanden | REST-Kette, Browser | ✅ |
| 2 | B/A | `GET /quote/IE00B4L5Y983` lesen | unbekanntes Feld unter `details`, TER identisch zur bisherigen Projektion | REST-Kette | ✅ |
| 3 | B/A | `GET /instruments` lesen | Werte und Herkunft unter `details` | REST-Kette, Browser | ✅ |
| 4 | B/A | `GET /fields` lesen | Typ, Einheit, Labels, Schreibrecht, Quellen, Anwendbarkeit und Version | REST-Kette | ✅ |
| 5 | A | Schema ändern und Quelle entfernen; Ausfall simulieren | Version steigt bei Änderung/Entfernung, bleibt bei Ausfall gleich | `test_open_details*.py`; kein separater Installationslauf | ➖ |
| 6 | B | BTC und ETF aufklappen, DE/EN und 390 px prüfen | unbekannte Felder generisch; BTC ohne Fondsfelder; kein horizontaler Überlauf | Chrome, sichtbare Bedienung | ✅ |
| 7 | B/A | `verified` zu überschreiben versuchen | kein Editor; PATCH 422, vorhandenes `false` bleibt | Browser und REST-Kette | ✅ |
| 8 | B/A | Score 0 eintragen, Quelle auf 17 ändern, aktualisieren, Eingabe entfernen | Quelle gewinnt; 0 als verdeckt sichtbar; Löschen lässt 17 bestehen | Browser-PATCH und Refresh | ✅ |
| 9 | B | ETF-Details öffnen | Score/Verified nennen risk-demo, Fondsfelder yaml-file | Chrome-Snapshot | ✅ |
| 9b | B/A | Datei-Plugin durch Registry, Beschaffung, DB und REST führen | unbekanntes Feld samt Herkunft, Persistenz und Override erhalten | `test_open_details_flow.py`, gleicher Plugin-Code im Browser | ✅ |
| 10 | A | Dashboard-Fixtures ohne `details` rendern | bisheriger Detailpfad bleibt kompatibel | bestehende Komponenten-Suite | ➖ |
| 11 | A | vollständige lokale Suite ausführen | 1065 Backend, 303 Plugin-API, 45 Beispiel, 329 Dashboard erfolgreich | `make test`, 2026-09-07 | ➖ |

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise ·
➖ ausschließlich automatisierte Tests/Review, keine Live-Verifikation.

**Prüflauf:** Backend 29 übersprungen, 8 Online-Integrationstests abgewählt;
Plugin-API 1 übersprungen. Ruff und `vue-tsc --noEmit` erfolgreich. AST- und
TypeScript-Compiler-Inventar der berührten Dateien geprüft. Keine unabhängige
Freigabe und kein erneuter vollständiger Zwei-Profil-Lauf von T-56 behauptet.

```bash
# #1–5, #7–9b: reproduzierbarer REST-/Persistenzlauf mit Testvolumes
.venv/bin/pytest -q tests/test_open_details.py tests/test_open_details_flow.py
# #11: vollständige lokale Suite, Betriebsdatenbank abgeschottet
env DATABASE_PATH=/tmp/stockinfo-t26-suite/stockinfo.db make test ARGS='-m "not integration"'
# #4: aktuelle Felddefinitionen der isolierten Browserinstanz
curl -sS http://127.0.0.1:8936/fields
# #2 und #3: Details der Testinstanz
curl -sS http://127.0.0.1:8936/quote/IE00B4L5Y983
curl -sS http://127.0.0.1:8936/instruments
```

**Nebenwirkungen:** Datenbankschema 2 übernimmt bisherige Detailspalten und
manuelle Werte in generische Tabellen. Die bisherigen Top-Level-REST-Felder
bleiben als Projektion erhalten. Neue Metadatenfelder müssen im Plugin
deklariert sein; der Core verwirft undeclared/ungültige Werte. `/fields` nennt
eine persistierte Detailgeneration und einen atomaren Schema-Zähler; T-25s
allgemeine Header-/Generation-Laufzeit bleibt offen. API_VERSION bleibt 2;
`FieldSpec.instrument_types` ist ein optionaler Zusatz.

**Browserbreite:** Nach dem mobilen Test blieb zunächst eine feste Emulation
aktiv; der Wechsel auf eine feste Desktopbreite behob das Resize-Problem noch
nicht. Auf Mikes zweiten Hinweis vollständig entfernt. Echter Fenster-Resize
geprüft: 1100 px Fenster → 1060 px Tabelle, 1505 px → 1465 px. Die Ansicht
reagiert wieder auf die Fensterbreite; keine CSS-Änderung erforderlich.

### Auflösung

Implementiert und erstgetestet. Claude soll insbesondere Migration,
Schema-Stabilität, Quellenpriorität und serverseitige Schreibrechte unabhängig
prüfen. Das Ticket bleibt bis zur Prüfung offen.

## Fachliche Anforderungen und Designentscheidungen

Die folgenden Anforderungen stammen aus dem ursprünglichen Ticket. Der aktuelle
Umsetzungs- und Prüfstand steht oben; diese Zielbeschreibung ist keine offene
Arbeitsliste und keine unabhängige Freigabe.


### Was zu bauen ist

- generische Felddefinitionen, gespeist aus `FieldSpec` der geladenen Quellen
- normalisierte Werte **und Herkunft je Instrument und Feld**
- generische manuelle Overrides — aber nur für Felder mit `overridable=True`
- die bestehende Merge-Regel gilt unverändert: Quelle gewinnt, manueller Wert
  füllt Lücken
- `details` in `/quote` und `/instruments`
- generische Darstellung im Dashboard
- Fixtures, an denen ein Konsument die Ignorierbarkeit prüfen kann

### Die Hülle eines Detailwerts

`GET /fields` sagt, **welche** Felder es gibt. `details` am Instrument sagt,
**welchen wirksamen Wert** dieses Papier dazu hat. Zwei Ebenen, die nicht
vermischt werden dürfen. Die Hülle trägt:

```
"details": {
  "ter": {
    "value":     0.2,
    "unit":      "percent",
    "currency":  null,              ← nur bei Beträgen
    "origin":    "provider",        ← provider | manual
    "source":    "justetf",
    "as_of":     "2026-08-19T…",
    "shadowed":  false              ← ein manueller Wert wird gerade verdeckt
  }
}
```

`shadowed` ist kein Beiwerk: Es ist dieselbe Aussage, die `apply_overrides`
heute schon über `shadowed_fields` macht — wer einen Wert eingetragen hat und
einen anderen sieht, muss erfahren, warum.

### Namespaces — sonst kollidieren zwei Plugins bei `yield`

Zwei Quellen können beide ein Feld `yield` deklarieren und Verschiedenes meinen.
Regeln dagegen *(Codex, 2026-08-20)*:

- bekannte Felder wie `ter` bedienen den **kanonischen Katalog**
- ein Plugin darf ein kanonisches Feld nur mit **verträglichem** Typ und
  verträglicher Zieldimension bedienen
- wirklich neue Felder bekommen einen stabilen Namespace: `plugin-name.feld`
- deklarieren zwei Quellen denselben Schlüssel mit widersprüchlichem Typ,
  widersprüchlicher Einheit oder Bedeutung, wird die Quelle **beim Laden
  abgelehnt** — kein „der letzte gewinnt"
- ein veröffentlichter Feldschlüssel wird nie umgedeutet; neue Bedeutung heißt
  neuer Schlüssel

Geprüft wird das an **zwei** Stellen: in der Registry beim Laden (T-23) und im
Contract-Test des Plugins.

### Eine einzige Wahrheit für die acht bekannten Kennzahlen

`ter`, `volatility` und die übrigen sechs erwarten bestehende Konsumenten
weiterhin auf oberster Ebene, während sie zugleich im generischen Katalog
stehen. Diese Doppelprojektion ist unvermeidlich — sie darf aber nicht zu zwei
Wahrheiten werden:

- Quellenwert, manueller Wert und Merge-Regel werden **einmal** generisch
  gespeichert und berechnet
- die Top-Level-Felder sind nur eine **Kompatibilitätsprojektion** desselben
  wirksamen Werts
- ein Test vergleicht beide Darstellungen, einschließlich `null`- und
  Override-Fällen

Zwei getrennte Speicher- oder Merge-Pfade erzeugen früher oder später
widersprüchliche Antworten.

### Die Feldliste ist abfragbar — mit Version

*(Mikes Anforderung, 2026-08-20: verbindliche Felder samt Versionsnummer müssen
per API abfragbar sein, und dieselbe Logik gilt für die offenen Felder.)*

```
GET /fields
{
  "core_version": "1.0",              ← Vertragsversion aus T-24
  "details_version": 7,               ← ändert sich bei **jeder** Schemaänderung
  "core": { "quote": [ … ], "instrument": [ … ], "daily": [ … ], "fx": [ … ] },
  "details": [
    { "name": "ter", "kind": "number", "unit": "percent",
      "label_en": "Total expense ratio", "overridable": true,
      "sources": ["justetf"] }
  ]
}
```

Der Grund ist praktisch: Ein Konsument, der Details generisch darstellen soll,
muss sie **erfragen** können — sonst müsste jedes neue Feld eine Codeänderung
auf beiden Seiten nach sich ziehen, und die Erweiterbarkeit wäre wieder keine.

Die Versionsnummer ist dabei das eigentliche Werkzeug. Sie ändert sich bei
**jeder** Änderung am öffentlichen Feldschema — nicht nur, wenn Felder
dazukommen:

| Ändert die Version | Ändert sie **nicht** |
|---|---|
| Feld kommt dazu oder fällt weg | eine Quelle ist gerade nicht erreichbar |
| Typ, Einheit, Währungspflicht oder `overridable` wechselt | ein Schutzschalter ist offen |
| ein Feldschlüssel wird ersetzt | Kurse ändern sich |
| Beschriftung oder ausgelieferte Quellenmenge ändert sich | |

Maßgeblich ist das **konfigurierte und validierte** Profilschema, nicht dessen
momentane Gesundheit. Ein Provider-Ausfall darf die Feldliste nicht verändern —
sonst verwerfen alle Konsumenten ihre Caches, weil eine Quelle kurz hakt.

**Der Typ ist festgelegt** *(Codex, 2026-08-20)*: eine nichtnegative Ganzzahl,
innerhalb einer `generation_id` monoton, atomar fortgeschrieben. Ein
Fingerabdruck wäre auch möglich gewesen — aber der REST-Vertrag muss **einen**
Typ nennen, sonst rät jeder Konsument. Zwischengespeichert wird immer unter
`(generation_id, details_version)`.

**Nicht zu verwechseln mit `generation_id` aus T-25:** Die Feldmenge kann sich
ändern, ohne dass das Quellenprofil wechselt — etwa wenn innerhalb desselben
Profils eine Quelle nachinstalliert wird.

---
