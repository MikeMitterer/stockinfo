# T-83 · Datenhinweis unter der Assets-Tabelle

Die Assets-Übersicht zeigt Kurse und Kennzahlen aus externen Quellen sowie
aus eigenen Eingaben. Der bestehende Hinweis unter Einstellungen → About ist
beim Lesen der Tabelle nicht sichtbar. Direkt unter der Assets-Tabelle soll
ein kurzer Hinweis die Grenzen der angezeigten Daten erklären. In der mobilen
Ansicht steht er entsprechend unter der Kartenliste, einmal für die gesamte
Liste und nicht unter jeder Karte.

**Beispiel:** Ein angezeigter Kurs ist veraltet. Der Nutzer sieht den Hinweis
am Ende der Übersicht und prüft den Wert vor einer Entscheidung bei der
ursprünglichen Quelle.

**Stand:** Mike hat das Ticket am 2026-10-01 ausdrücklich in Doing gesetzt.
StockInfos Coder `codex` ist laut `_tickets/STATUS.md` am Zug; T-82 bleibt
danach als nächstes Ticket in Ready. Die endgültige öffentliche Formulierung
ist mit der bestehenden Verbrauchererklärung abzugleichen.

## Vorgeschlagener Wortlaut

**Deutsch:**

> Die angezeigten Kurse und Kennzahlen können verzögert, unvollständig oder
> fehlerhaft sein. Prüfe wichtige Angaben vor einer Entscheidung anhand der
> ursprünglichen Quelle und deiner Eingaben. StockInfo kann ihre Richtigkeit
> nicht garantieren; für Gewährleistung und Haftung gelten die gesetzlichen
> Regeln.

**Englisch:**

> Displayed prices and metrics may be delayed, incomplete or incorrect. Check
> important information against the original source and your own entries
> before making a decision. StockInfo cannot guarantee its accuracy; statutory
> rules on warranties and liability apply.

Der Hinweis soll keine pauschale Haftungsfreistellung behaupten. StockInfos
[`LICENSING.md`](../../LICENSING.md) erklärt für Verbraucher ausdrücklich, dass
MangoLila GmbH sich nicht auf die Gewährleistungs- und Haftungsausschlüsse der
EUPL-Artikel 7 und 8 beruft. Der neue Text und die bestehende About-Ansicht
aus [T-80](../40-done/T-80-about-data-use-notice.md) müssen dazu passen. Die
rechtliche Freigabe des endgültigen öffentlichen Wortlauts bleibt eine
menschliche Entscheidung.

## Umfang und Nachweis

| Repo | Time-box | Scope | GH-Issue |
|---|---|---|---|
| StockInfo | 1–2 h | Hinweis an der Assets-Übersicht in Deutsch und Englisch | — |

Der Hinweis ist bei gefüllter Übersicht auf breiten und schmalen Bildschirmen
sichtbar und wird durch einen Sprachwechsel ohne Neuladen übersetzt. Er erhält
das Tabellen- und Kartenlayout sowie die Bedienbarkeit. Keine Änderung an
Kursdaten, API oder Berechnung.

### Verify

Legende: ➖ noch keine Live-Verifikation.

| # | Handgriff | Erwarteter Nachweis | AI | Human |
|---|---|---|:--:|---|
| 1 | Assets-Übersicht auf breitem Bildschirm öffnen | Hinweis steht direkt unter der Tabelle, gut lesbar und ohne Überlagerung | ➖ | |
| 2 | Dieselbe Übersicht schmal öffnen | Hinweis steht einmal unter der Kartenliste; keine horizontale Überbreite | ➖ | |
| 3 | Sprache DE → EN → DE wechseln | Wortlaut wechselt ohne Neuladen und bleibt inhaltlich gleich | ➖ | |
| 4 | Wortlaut mit About und `LICENSING.md` abgleichen | Aussagen zu Datenrisiko, Garantie und gesetzlichen Ansprüchen widersprechen einander nicht | ➖ | |
| 5 | Betroffene Dashboard-Prüfungen und Doku-Abgleich ausführen | Keine UI-Regression; `README.md` und `docker/README.md` sind inhaltlich abgeglichen, weitere betroffene Anleitungen benannt | ➖ | |

### Akzeptanzkriterien

- [ ] Der kurze Hinweis steht unmittelbar unter der Assets-Tabelle bzw. der mobilen Kartenliste.
- [ ] Deutsch und Englisch entsprechen dem gewählten Sprachzustand.
- [ ] Der Wortlaut erklärt mögliche Datenfehler und behauptet keinen vollständigen Ausschluss gesetzlicher Ansprüche.
- [ ] Die bestehende About-Erklärung und die Verbraucherklärung bleiben konsistent.
- [ ] Doku-Abgleich und Prüfnachweise stehen vor der Übergabe im Ticket.

### Side-Effects

Die zusätzliche Textzeile kann die Übersicht vertikal verlängern. Sie darf
keine Tabelle, Karte oder Bedienfunktion verdecken. StockPortfolios eigene
Hinweise und Tickets bleiben getrennt.

### Auflösung

Offen. Umsetzung, Verifikation und unabhängiges Review folgen erst nach
Aktivierung gemäß `_tickets/STATUS.md`.
