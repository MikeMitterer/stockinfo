# T-22 · Quellen konfigurieren statt verdrahten

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend) | aktiv · Plugin-MVP 1/4 | 4 h | Konfigurationsdatei, `is_configured()`, Protokolle | — |

**Löst:** Welche Quelle wann greift, steht heute als `if`-Kaskade in der
Composition-Root (`app/container.py:24-34`), und jeder API-Key ist ein eigenes
Feld in `Settings`. Mit zwei Quellen tragbar, mit vier nicht.

**Hängt an:** T-20 (ohne differenzierte Antworten ist eine konfigurierbare Kette
nicht sinnvoll steuerbar). **Blockiert:** T-23.

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

> **Verbindliche MVP-Reihenfolge, Mike 2026-08-27:** **T-22 → T-27a →
> T-27b → T-23.** Dieses Ticket baut auf dem freigegebenen T-21-Stand bis
> Übergabe 3 auf; die eingefrorenen T-21-Übergaben 4A/4B sind keine
> Voraussetzung.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 0 | **Profilpaket** eintragen (eine Zeile + Schlüssel), Neustart | `GET /sources` zeigt **alle** Rollen besetzt — keine Kette von Hand geschrieben | | |
| 1 | `data/sources.yaml` mit vertauschter Resolver-Reihenfolge, Neustart | `GET /sources` zeigt die neue Reihenfolge | | |
| 2 | OpenFIGI-Key entfernen, Neustart | Quelle bleibt **aktiv** — der Key ist optional und hebt nur das Limit an | | |
| 2b | Quelle mit **pflichtigem** Key ohne Key, Neustart | meldet `configured: false` und fällt aus der Kette — **kein Fehler** | | |
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

Eine Quelle, der etwas **Pflichtiges** fehlt, meldet `False` und wird gar nicht
erst aufgenommen.

**Nicht jeder Schlüssel ist pflichtig.** OpenFIGI arbeitet anonym mit
niedrigerem Limit und sendet den Key nur, wenn er da ist
(`app/providers/openfigi_provider.py:24-50`). Eine Quelle deshalb abzuschalten
wäre falsch — `is_configured()` fragt „kann ich arbeiten", nicht „ist alles
gesetzt".

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

### Der Normalfall ist eine Profilreferenz, nicht eine handgebaute Kette

Die Datei oben ist ein guter **Expertenmodus** — sie verlangt aber Paketliste,
Resolver-, Metadaten- und Kursketten sowie Provider-Abschnitte. Für den Zweck des
Vorhabens ist das zu viel: Wenn die Einrichtung kompliziert bleibt, wird das
Plugin-System nicht benutzt.

Regionale Profile (Kanada, Russland, Österreich/Deutschland) sollen deshalb als
**fertiges Paket mit getesteten Standardketten** eintragbar sein:

```yaml
# data/sources.yaml — der einfache Weg
profile: stockinfo-profile-canada==1.0.2

providers:
  eodhd:
    api_key: ${EODHD_API_KEY}
```

Eine Zeile plus Schlüssel. Einzelne Rollen zu überschreiben bleibt möglich, ist
aber die Ausnahme. Ohne diesen Weg ist „Quellenprofil" nur ein neuer Name für
eine weiterhin von Hand zusammengebaute Konfiguration.

**Verify dazu:** Profilpaket eintragen, Neustart, `GET /sources` zeigt **alle**
Rollen besetzt — ohne dass eine einzige Kette von Hand geschrieben wurde.

### Bei Gleichstand deterministisch sortieren

Sonst hängt das Ergebnis von der Ladereihenfolge des Dateisystems ab, und
Fehlerberichte lassen sich nicht nachstellen. Priorität aus der Konfiguration,
bei Gleichstand nach Name.

---

## Auflösung

_(offen)_
