# T-22 · Quellen konfigurieren statt verdrahten

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend) | offen | 4 h | Konfigurationsdatei, `is_configured()`, Protokolle | — |

**Löst:** Welche Quelle wann greift, steht heute als `if`-Kaskade in der
Composition-Root (`app/container.py:24-34`), und jeder API-Key ist ein eigenes
Feld in `Settings`. Mit zwei Quellen tragbar, mit vier nicht.

**Hängt an:** T-20 (ohne differenzierte Antworten ist eine konfigurierbare Kette
nicht sinnvoll steuerbar). **Blockiert:** T-23.

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | `data/sources.yaml` mit vertauschter Resolver-Reihenfolge, Neustart | `GET /sources` zeigt die neue Reihenfolge | | |
| 2 | OpenFIGI-Key entfernen, Neustart | Quelle meldet `configured: false` und fällt aus der Kette — **kein Fehler** | | |
| 3 | `sources.yaml` gelöscht | App startet mit sinnvollen Vorgaben, statt abzubrechen | | |
| 4 | `sources.yaml` mit Tippfehler im Quellennamen | Meldung nennt den unbekannten Namen und die verfügbaren | | |
| 5 | dieselbe Datei in ein Issue kopieren | enthält **keinen** Schlüssel, nur Verweise | | |
| 6 | `make test` | Backend grün | | |

```bash
curl -s "http://localhost:8000/sources" | python3 -m json.tool     # #1/#2
```

---

## Details

### Zwei Orte nach Lebenszyklus, nicht nach Technik

**Geheimnisse und Schalter bleiben in der Umgebungskonfiguration** — Keys, Ports,
TTLs. Das ist das bestehende Muster und der richtige Ort für Secrets.

**Ketten und Reihenfolge kommen in eine Datei im Daten-Volume**, neben die
Datenbank:

```yaml
# data/sources.yaml
resolvers: [openfigi, yahoo-search]
etf_meta:  [justetf, yfinance]
quotes:    [yfinance]

providers:
  openfigi:
    api_key: ${OPENFIGI_API_KEY}     # verweist, enthält nicht
```

Der Grund für die Trennung ist praktisch: **Diese Datei kann ein Nutzer in ein
Issue kopieren, ohne einen Schlüssel zu leaken.** Wenn jemand in Kanada eine
funktionierende Kette gefunden hat, ist sie genau das Artefakt, das er weitergibt.

### `is_configured()` ersetzt die Kaskade

Eine Quelle ohne Schlüssel meldet `False` und wird gar nicht erst aufgenommen.
Damit verschwindet jede Fallunterscheidung aus `container.py` — heute acht
Verdrahtungspunkte, an denen konkrete Klassen genannt werden.

Der Vertrag dafür steht schon: `Source.is_configured()` in
`stockinfo-plugin-api` (Commit `840121c`).

### Die zwei fehlenden Verträge

`YFinanceProvider` liefert `fetch_quote`, `fetch_daily_closes` **und**
`fetch_fx_rate` — das Protokoll `QuoteProvider` deklariert nur das erste. Wer
ersetzen will, muss drei Verträge erfüllen, von denen zwei nirgends stehen.

**Weg:** `DailyCloseProvider` und `FxProvider` als eigene Protokolle. Klein, und
danach ist die Abhängigkeit ablesbar statt nur erfahrbar.

### Bei Gleichstand deterministisch sortieren

Sonst hängt das Ergebnis von der Ladereihenfolge des Dateisystems ab, und
Fehlerberichte lassen sich nicht nachstellen. Priorität aus der Konfiguration,
bei Gleichstand nach Name.

---

## Auflösung

_(offen)_
