# T-26 · Offene Detailfelder tatsächlich durchreichen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | offen | 1 Tag | generische Persistenz, `details` in der API, generische Darstellung | — |

**Löst:** Entschieden ist, dass der Core geschlossen und die Details **offen und
additiv** sind. Umgesetzt ist davon nichts. Ohne dieses Ticket kann T-23 ein
Plugin laden, dessen korrekt deklarierte neue Felder in Backend, Datenbank,
Override-Modell und Dashboard **verloren gehen** — der Vertrag verspräche eine
Erweiterbarkeit, die eine Schicht später endet.

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

**Hängt an:** T-24 (die `details`-Hülle gehört zum REST-Vertrag), **T-21**
(generische Override-Endpunkte brauchen die eindeutige Adressierung) und
**T-23** (die `FieldSpec`-Deklarationen kommen von der Registry, dort sitzt auch
die Kollisionsprüfung).
**Muss vor** dem ersten Plugin liegen, das neue Felder mitbringt — solange es
fehlt, darf der Vertrag unbekannte Felder nicht *behaupten*.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Plugin mit einem unbekannten, korrekt deklarierten Feld | Wert wird gespeichert, nicht verworfen | | |
| 2 | `GET /quote/{isin}` | Feld erscheint im `details`-Container | | |
| 3 | `GET /instruments` | dito | | |
| 4 | **`GET /fields`** | nennt alle bekannten Felder samt Typ, Einheit, Beschriftung, `overridable` — **und eine Versionsnummer** | | |
| 5 | Plugin nachinstallieren, das ein Feld ergänzt | Feld-Version erhöht sich; ein Konsument kann daran erkennen, dass er neu laden muss | | |
| 6 | Dashboard, Detailbereich | stellt ein unbekanntes Feld generisch dar, ohne Codeänderung | | |
| 7 | Feld mit `overridable=False` | lässt sich **nicht** von Hand überschreiben | | |
| 8 | Feld mit `overridable=True` | manueller Wert füllt nur die Lücke; ein Quellenwert gewinnt | | |
| 9 | zwei Quellen, verschiedene Felder | Herkunft steht **je Feld**, nicht je Zeile | | |
| 9b | **Harness-Stufe 3** (Fortsetzung des Laufs aus T-23/T-25) | unbekanntes Detailfeld, Herkunft, Persistenz und Override überstehen den ganzen Weg bis zur REST-Antwort | | |
| 10 | älterer Konsument (Fixture ohne `details`) | ignoriert unbekannte Einträge, bricht nicht | | |
| 11 | `make test` | grün | | |

---

## Details

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

## Auflösung

_(offen)_
