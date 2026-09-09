# T-16 · Review-Fixes und die zweite ETF-Quelle am laufenden System prüfen

Abgeschlossen auf Mikes Auftrag vom 2026-09-07. Die UI-Abnahme wurde durch
T-56 abgelöst; der alte Befund #5c ist in T-17 behoben und verifiziert.
Die unbestätigten Docker-Tests stehen jetzt in
[T-63](../T-63-docker-start-und-betrieb-pruefen.md).

## Für dich

Keine weitere Aufgabe in T-16. Mike: „Kennzeichne es als erledigt - erstelle ein eigenes Ticket für die Docker-Tests“.

## Abschluss und technische Einordnung · 2026-09-07

Die erneute Prüfung von `tests/test_quote_cache.py` ergab 35 bestandene Tests.
Der genaue alte US-ETF-UI-Ablauf „TER setzen und danach Refresh“ wurde dabei
nicht erneut live ausgeführt. Der Abschluss ist Mikes Entscheidung und keine
nachträgliche Bestätigung aller alten Prüfzellen. Die bisherigen Antworten
und Belege bleiben unten unverändert erhalten.

Das Smoke-Skript wird mit dem Ticket unter `solved/` archiviert. Seine alten
Provider-Erwartungen sind historisch; es wurde nicht erneut als aktueller
Gesamtnachweis ausgeführt. Docker #9 bleibt ohne Live-Nachweis.

## Ursprünglicher Prüfstand · Historie

Die folgenden Statusangaben, offenen Punkte und Befehle beschreiben den
früheren Stand; sie sind kein aktueller Auftrag.

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | in-review | 15 min (nur noch UI) | Verifikation am laufenden System, kein Code | — |

**Löst:** Vier Commits (`6ee6bbe`…`809c48a`) haben sechs Review-Befunde behoben
und ETF-Metadaten auf zwei Quellen aufgeteilt. Die Unit-Tests decken die Logik
ab, aber die Hälfte der Befunde lebt an Stellen, die kein Test erreicht — genau
dort saßen die Fehler.

**Stand:** Die maschinell prüfbaren Zeilen sind durch (`./_tickets/T-16-smoke.sh --run`,
11 von 12 grün). Offen sind die vier UI-Zeilen und ein neuer Befund (#5c).

<!--
  Status: in-review — Code ist in master, die Mensch-Spalte fehlt.
  Das Prüf-Script startet einen eigenen Server auf Port 8765 mit temporärer DB;
  die Arbeits-Datenbank bleibt unberührt.
-->

---

## Verify

Legende: ✅ live bestätigt · ⚠️ bestätigt mit Einschränkung (Fußnote) ·
◑ teilweise (Fußnote) · ➖ keine Live-Verifikation (nur Unit/Review).
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

**Voraussetzung für die UI-Zeilen:** Stack läuft (`make dev-up`) — Backend `:8000`,
Dashboard `:5173`. Die Script-Zeilen brauchen nur `./_tickets/T-16-smoke.sh --run`.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Script `#1` | Krypto-Papier auf frischer DB legt an statt mit 500 abzustürzen | ✅ [^1] | |
| 2 | Script `#2a–c` | US-ETF: Anbieter da, Quelle `yfinance`, **kein** geratenes TER | ✅ [^2] | |
| 3 | Assets → US-ETF → Detailbereich → TER eintragen, dann Refresh | der eingetragene Wert bleibt stehen und wird nicht verdeckt | ➖ [^3] | |
| 4 | Script `#4a/b` | kanadisches Papier: per Symbol ja, per ISIN nicht auflösbar | ⚠️ [^4] | |
| 5 | Script `#5a/b` | EU-ETF unverändert: TER da, `yfinance+justetf` gespeichert | ✅ [^5] | |
| 5c | Script `#5c` | **Live-Antwort zeigt `ter: null`, obwohl die DB 0.2 hält** | ❌ [^6] | |
| 6 | Refresh-Knopf an einer ETF-Zeile, danach Detailbereich | TER/Anbieter werden tatsächlich aktualisiert | ◑ [^7] | |
| 7 | Script `#7` | Börse und Währung bleiben über zwei Live-Abrufe gleich | ✅ [^8] | |
| 8 | „Alles aktualisieren" in der Kopfzeile drücken | Balken läuft an der **Oberkante der Seite**, über der Kopfzeile | ◑ [^9] | |
| 9 | `make up`, danach `docker logs stockinfo` | Container startet; **kein** `ValidationError` zu `strict_exchange` | ➖ [^10] | |
| 10 | ETF mit gepflegten Kennzahlen, bis `METADATA_TTL_DAYS` greift | justETF wird erneut gefragt statt zu verstummen | ➖ [^11] | |
| 11 | Script `#11` | Backend 244 grün | ✅ [^12] | |

```bash
# Zeilen #1, #2, #4, #5, #6, #7, #11 in einem Lauf
./_tickets/T-16-smoke.sh --run

# #9 — Container (nicht im Script: baut ein Image und greift auf Docker zu)
make build && make up && sleep 3 && docker logs stockinfo 2>&1 | tail -20
```

---

## Details

**Was die vier Commits geändert haben**

| Commit | Inhalt |
|---|---|
| `6ee6bbe` | `make test` neu; pauschales `export` im Makefile entfernt; Hilfe zu `PLATFORM=all` korrigiert |
| `5c094f8` | Fortschrittsbalken an die Seitenoberkante; totes `$header-h` entfernt |
| `5ec9c37` | Fünf Review-Befunde: Insert-Absturz, wandernde Börse im Lesepfad, Metadaten-Zeitstempel, Symbol-Refresh, Gattungswahl im Resolver |
| `809c48a` | `is_responsible` trennt Zuständigkeit vom Ergebnis; `YFinanceEtfEnricher` + `CompositeEtfEnricher`; `EtfDetails.source` |

### Neuer Befund #5c — die Antwort hält den Stand nicht

Kurs-TTL abgelaufen, Metadaten-TTL noch frisch: `_build` fragt justETF dann
nicht — richtig, der Stand ist jung. Die frische Antwort hat deshalb keine
ETF-Felder, und `_save_fresh` reicht **genau diese Antwort** an den Client
durch, statt den gespeicherten Stand zu liefern. Gemessen: `ter` in der Antwort
`null`, in der Datenbank `0.2`.

Die Daten sind nicht verloren, nur unsichtbar — beim nächsten Cache-Treffer sind
sie wieder da. Der Weg wäre, in `_save_fresh` den gespeicherten Stand über die
frische Antwort zu legen, so wie `_with_overrides` es für die manuellen Werte
tut. **Vorbestehend**, nicht durch die vier Commits verursacht; die zweite
ETF-Quelle macht ihn nur sichtbarer.

### Grenzfall #4 — kanadische Papiere

Über die ISIN scheitert schon die Auflösung: OpenFIGI kennt kein Listing
(`openfigi_resolve_empty`), Yahoos ISIN-Suche liefert nichts
(`resolve_isin_empty`) — auch mit `DEFAULT_EXCHANGE=XTSE`. Über das Symbol
(`XIC.TO`) kommt das Papier herein, aber yfinance nennt dafür keine ISIN (`'-'`),
und ohne sie greift der konservative Pfad: kein Anbieter, `metadata_complete`
bleibt falsch.

Der Enricher bräuchte die ISIN gar nicht zum Holen — nur um die Zuständigkeit zu
bestimmen. Das ist der Punkt, an dem das Resolver-/Quellen-Konzept hakt.

### Offene Kante, bewusst so gelassen

Für nicht-europäische ETFs kostet die Anreicherung einen zusätzlichen
Yahoo-Aufruf (`.info`), zusätzlich zu dem aus `fetch_quote`. Er läuft nur nach
Ablauf von `METADATA_TTL_DAYS`. Vermeidbar, indem `RawQuote` den `fundFamily`
mitbringt — das vermischt aber Kurs- und Metadatenpfad.

[^1]: Live über die HTTP-Route auf frischer DB: `GET /quote?symbol=BTC-USD` → 200.
    Vorher `Incorrect number of bindings supplied. The current statement uses 17,
    and there are 8 supplied.`
[^2]: `GET /quote/US9229087690` → `provider=Vanguard`, `source=yfinance`,
    `ter=null`. Echte Yahoo-Antwort, kein Fake.
[^3]: Nur aus `apply_overrides` abgeleitet („füllt nur Lücken"), nicht in der
    Oberfläche durchgespielt. Der Grund, warum TER aus Yahoo bewusst nicht
    übernommen wird — ein gelieferter Wert verdeckt einen eingetragenen.
[^4]: Der Ist-Zustand ist geprüft, nicht der Wunschzustand: `#4a` bestätigt den
    Symbol-Weg (CAD), `#4b` friert die Lücke bei der ISIN-Auflösung als 404 ein.
    Siehe Abschnitt oben.
[^5]: `ter=0.2` in der Antwort und `source=yfinance+justetf` in der gespeicherten
    Zeile (`GET /instruments`).
[^6]: Neuer Befund, siehe Abschnitt oben. Das Script meldet ihn als Fehlschlag —
    der Lauf bleibt rot, bis er behoben ist.
[^7]: Der API-Pfad ist live geprüft (`POST /refresh/by-symbol/EUNL.DE` liefert
    `ter=0.2`), der Knopf in der Oberfläche nicht.
[^8]: Zwei Live-Abrufe hintereinander bei `CACHE_TTL_HOURS=0`, beide
    `EUNL.DE|EUR|Xetra`.
[^9]: Im Browser gemessen — Balken `y=0..3`, Kopfzeile `y=0..56`, z-index 25
    gegen 10. Die Klasse `active` war dabei von Hand gesetzt; ein echter Lauf
    von „Alles aktualisieren" stand nicht dahinter.
[^10]: Nur der Weg über Make ist geprüft. Der Container bekommt seine
    Konfiguration über `--env-file` und übergibt Werte wörtlich — der
    Trailing-Whitespace, der über Make stolperte, kann dort weiterhin zuschlagen.
[^11]: Die TTL lässt sich in der Zeit nicht abkürzen, ohne den Zeitstempel von
    Hand zu setzen. Logik ist unit-getestet.
[^12]: 244 passed. Dashboard (230) und `ruff` laufen über `make test` mit.

---

## Auflösung

_(offen — trägt der Mensch nach)_
