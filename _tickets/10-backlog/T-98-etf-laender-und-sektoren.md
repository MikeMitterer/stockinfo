# T-98 · Länder- und Sektorgewichtung von ETFs anzeigen

StockInfo soll für europäische ETFs zeigen, **in welche Länder und Sektoren
der Fonds investiert**, jeweils mit Anteil in Prozent. Die Daten liefert
justETF schon heute; StockInfo verwirft sie bisher.

**Beispiel:** iShares Core MSCI World (`IE00B4L5Y983`), gemessen am
2026-10-03:

| Länder | Anteil | Sektoren | Anteil |
|---|---|---|---|
| United States | 70,32 % | Technology | 35,71 % |
| Japan | 5,79 % | Finance | 18,01 % |
| United Kingdom | 3,68 % | … | … |

**Stand:** Angelegt am 2026-10-03 auf Mikes Auftrag. Noch nicht eingeplant.
Für Mike ist aktuell kein Handgriff nötig.

## Ausgangslage

`JustEtfProvider.fetch_etf` ruft `justetf_scraping.get_etf_overview(isin,
include_gettex=False)` auf und übernimmt nur Stammdaten wie TER, Anbieter und
Fondsgröße. Die Antwort enthält außerdem `countries` und `sectors` als Liste
von `{"name": …, "percentage": …}` sowie `holdings_date`.

Die Bibliothek holt die Listen auf zwei Wegen (Messung vom 2026-10-03,
`IE00B4L5Y983`):

| Aufruf | Abrufe bei justETF | Länder | Sektoren |
|---|---|---|---|
| `expand_allocations=False` | 1 (nur die Profilseite) | 5 | 5 |
| `expand_allocations=True` (heutiger Standard) | 3 (Profilseite und je ein AJAX-Abruf) | 11 | 14 |

StockInfo nutzt heute den Standard. Es macht also schon jetzt drei Abrufe pro
ETF und verwirft zwei davon.

## Offene Entscheidungen vor der Umsetzung

1. **Top 5 oder vollständige Liste?** Die vollständige Liste kostet zwei
   zusätzliche Abrufe pro ETF. Das berührt die justETF-AGB (Ziffer 3.1,
   „übermäßige Belastung“) und eine mögliche Anfrage bei justETF. Die
   Top 5 kommen ohne Zusatzabruf. Entscheidet Mike.
2. **Form im Plugin-Vertrag.** `FieldKind` kennt nur `number`, `text` und
   `boolean` (`plugin_api/src/stockinfo_plugin/types.py`). Eine Liste aus
   Name und Anteil passt in keinen davon. Der Coder schlägt im
   Scope-Checkpoint eine Form vor, etwa eine neue Feldart für Gewichtungen
   oder je Eintrag ein eigenes Feld. Eine Vertragserweiterung braucht eine
   neue Vertragsversion, Fixtures und Doku.
3. **Anzeige.** Wo erscheinen die Listen: im Detailbereich der Zeile, als
   Tabelle oder Balken, in beiden Sprachen? Die Ländernamen kommen englisch
   von justETF; ob sie übersetzt werden, ist zu klären.
4. **Stand.** `holdings_date` nennt das Datum der Gewichtung. Es sollte wie
   bei der berechneten Volatilität (T-89) als Stand neben dem Wert stehen.

## Umsetzung und technische Nachweise

| Repo | Time-box | Scope | GH-Issue |
|---|---|---|---|
| StockInfo | 1–2 Tage | justETF-Anbindung, Plugin-Vertrag, Persistenz, REST, Dashboard, Doku | — |

Unabhängig von Entscheidung 1 gehört dazu: `expand_allocations` ausdrücklich
setzen, damit die Zahl der Abrufe im Code sichtbar ist und ein Test sie
festhält, wie heute `include_gettex=False`.

### Verify

Legende: ➖ noch keine Live-Verifikation.

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | Test für den Aufruf von `get_etf_overview` | `expand_allocations` hat den entschiedenen Wert; Zahl der Abrufe pro ETF ist belegt | ➖ |
| 2 | `GET /quote/IE00B4L5Y983` gegen eine temporäre Datenbank | Länder und Sektoren mit Anteil und Stand in der Antwort | ➖ |
| 3 | Nicht-europäischer ETF, etwa `US78462F1030` | Keine Gewichtung, kein Abruf bei justETF, kein Fehler | ➖ |
| 4 | Neustart der App | Gespeicherte Gewichtungen sind unverändert da | ➖ |
| 5 | Browserweg in `dashboard/e2e/visual-check.mjs` | Detailbereich zeigt beide Listen auf Deutsch und Englisch | ➖ |
| 6 | `make check` | Grün | ➖ |
| 7 | Vertragsprüfung (`contract/`) | Neue Form ist versioniert, Fixtures und Snapshot sind nachgezogen | ➖ |

### Akzeptanzkriterien

- [ ] Mike hat Entscheidung 1 getroffen; die Zahl der Abrufe pro ETF entspricht ihr.
- [ ] Länder und Sektoren erscheinen mit Anteil und Stand in API und Dashboard.
- [ ] Die Form im Plugin-Vertrag ist im Scope-Checkpoint bestätigt und dokumentiert.
- [ ] Sichtbare Texte laufen über die i18n-Kataloge.
- [ ] Doku-Abgleich: `README.md`, `docker/README.md`, `docs/plugin-authors.md`, `docs/rest-core-contract.md`.

### Side-Effects

StockPortfolio liest die Details über den generischen `details`-Eintrag. Eine
neue Feldart kann dort anders oder gar nicht erscheinen; das ist vor der
Übergabe mit StockPortfolios Code zu prüfen. Kein Push, kein Docker-Hub- oder
Unraid-Update.

### Auflösung

Offen. Noch keine Umsetzung oder Verifikation.
