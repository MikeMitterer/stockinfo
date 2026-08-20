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

**Hängt an:** T-24 (die `details`-Hülle gehört zum REST-Vertrag).
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

### Die Feldliste ist abfragbar — mit Version

*(Mikes Anforderung, 2026-08-20: verbindliche Felder samt Versionsnummer müssen
per API abfragbar sein, und dieselbe Logik gilt für die offenen Felder.)*

```
GET /fields
{
  "core_version": "1.0",              ← Vertragsversion aus T-24
  "details_version": 7,               ← erhöht sich, wenn Felder dazukommen
  "core":    [ … Pflichtfelder mit Typ und Nullability … ],
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

Die Versionsnummer ist dabei das eigentliche Werkzeug: Sie ändert sich, wenn ein
Plugin dazukommt, das Felder mitbringt. Ein Konsument mit gecachter Feldliste
merkt daran, dass er sie neu holen muss.

**Nicht zu verwechseln mit `generation_id` aus T-25:** Die Feldmenge kann sich
ändern, ohne dass das Quellenprofil wechselt — etwa wenn innerhalb desselben
Profils eine Quelle nachinstalliert wird.

---

## Auflösung

_(offen)_
