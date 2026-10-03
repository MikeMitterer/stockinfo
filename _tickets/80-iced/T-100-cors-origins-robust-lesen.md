# T-100 · CORS_ORIGINS robust lesen

StockInfo soll `CORS_ORIGINS` auch als einfache Adresse oder als
kommagetrennte Liste annehmen. Ein leerer Wert soll die Vorgabe ergeben, statt
den Start abzubrechen.

**Beispiel:** Ein Unraid-Nutzer trägt im Template-Feld „CORS origins“ die
Adresse seiner StockPortfolio-Instanz ein: `http://tower:8088`. Heute bricht
StockInfo damit beim Start ab. Gültig ist nur `["http://tower:8088"]`.

**Stand:** Angelegt am 2026-10-03 auf Mikes Auftrag („leg das Ticket für die
CORS-Codeänderung an - in doing“). Am 2026-10-03 nach `80-iced/`
zurückgestellt (Mike: „ja, verschieb T-100 nach iced“). Grund:
[StockPortfolio T-82](/Volumes/DevLocal/DevWeb/Production/StockPortfolio/_tickets/10-backlog/T-82-stockinfo-ueber-eigenen-server.md)
leitet StockInfo-Abfragen über den eigenen Server; dann braucht StockPortfolio
kein `CORS_ORIGINS` mehr, und dieses Ticket wird voraussichtlich
überflüssig. Wiederaufnahme nur, wenn T-82 nicht kommt. Keine Umsetzung.

## Ausgangslage

`Settings.cors_origins` ist `list[str]` (`app/config.py`). `pydantic-settings`
(2.14.2) liest eine Liste aus der Umgebung nur als JSON. Gemessen am
2026-10-03 mit `Settings(_env_file=None)`:

| `CORS_ORIGINS` | Ergebnis heute |
|---|---|
| `["http://unraid:8088"]` | `['http://unraid:8088']` |
| `["http://unraid:8088","http://192.168.1.10:8088"]` | beide Adressen |
| `http://unraid:8088` | `SettingsError`, Start bricht ab |
| leer | `SettingsError`, Start bricht ab |

Unraid übergibt ein leer gelassenes Template-Feld als leere Variable. Die
Anleitungen und das Template warnen deshalb seit `c4fedf0` und `acb2fef`
(Templates-Repo) ausdrücklich vor beiden Fällen.

Hintergrund: StockPortfolio ruft StockInfo direkt aus dem Browser auf. Ohne
die Adresse von StockPortfolio in `CORS_ORIGINS` blockiert der Browser die
Antworten. `*` ist keine Lösung: Dann könnten fremde Webseiten im Browser
StockInfo auslesen und Daten löschen.

## Umsetzung und technische Nachweise

| Repo | Time-box | Scope | GH-Issue |
|---|---|---|---|
| StockInfo | 2 h | `app/config.py`, Tests, Anleitungen; Templates-Repo: Feldbeschreibung | — |

Erlaubte Formen: JSON-Liste wie bisher, eine einzelne Adresse, mehrere
Adressen mit Komma getrennt. Leerzeichen um Einträge werden entfernt. Ein
leerer Wert ergibt die Vorgabe `["http://localhost:5173"]`. `*` bleibt
unverändert erlaubt, wird aber nicht empfohlen. Technischer Ansatz nach
Prüfung der Bibliothek, etwa `NoDecode` mit einem Validator im Modus
`before`; kein eigener Parser für die übrigen Felder.

Nach der Umsetzung entfallen die Warnungen „an empty value or a plain address
stops the container“ in `README.md`, `docker/README.md`, `unraid/README.md`
und im Template-Feld; Beispiele dürfen dann die einfache Form zeigen.

### Verify

Legende: ➖ noch keine Live-Verifikation.

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | Tests für alle Formen der Tabelle oben plus Komma-Liste mit Leerzeichen | Jede Form ergibt die erwartete Liste; kein `SettingsError` | ➖ |
| 2 | Container mit `CORS_ORIGINS=http://localhost:8088` starten, Preflight von dieser Origin und von einer fremden Origin senden | Erlaubte Origin bekommt `access-control-allow-origin`, fremde nicht | ➖ |
| 3 | Container mit leerem `CORS_ORIGINS` starten | Start gelingt, Vorgabe aktiv | ➖ |
| 4 | `make check` | Grün | ➖ |
| 5 | Doku-Abgleich der drei READMEs und des Templates | Warnungen entfernt, Beispiele stimmen mit dem Verhalten überein | ➖ |

### Akzeptanzkriterien

- [ ] Einzelne Adresse, Komma-Liste und JSON-Liste werden angenommen.
- [ ] Ein leerer Wert startet mit der Vorgabe.
- [ ] Fremde Origins bleiben ausgeschlossen.
- [ ] Doku-Abgleich: `README.md`, `docker/README.md`, `unraid/README.md`, Template `stockinfo.xml`.

### Side-Effects

Bestehende Installationen mit JSON-Liste verhalten sich unverändert.
StockPortfolio ist nicht betroffen. Kein Push, kein Docker-Hub- oder
Unraid-Update ohne eigenen Auftrag.

### Auflösung

Offen. Noch keine Umsetzung oder Verifikation.
