# T-82 · Python-Paket für StockPortfolio-Tests einbinden

StockPortfolios lokales Skript `scripts/stockinfo-test-server.py` wird mit
StockInfos Python-Umgebung gestartet. Für die einheitliche CLI-Hilfe und
Farbausgabe soll es `projecttools.ui.colors` aus dem paketierbaren
ProjectTools-Python-Teil nutzen können. Diese Bibliothek ist derzeit nicht
als Abhängigkeit der StockInfo-Umgebung deklariert. Ein bloßer
`sys.path`-Eingriff oder ein absoluter Rechnerpfad würde den Aufruf an
eine lokale Verzeichnisstruktur binden.

**Auswirkung für den Konsumenten:** Ohne geklärten Installationsweg kann
StockPortfolio das Skript nicht zuverlässig auf anderen Rechnern mit der
gemeinsamen CLI-Darstellung starten. Der bestehende Teststack und StockInfos
Produkt-API sollen davon unberührt bleiben.

**Stand:** Für die Umsetzung bereit; noch nicht aktiviert. Dieses Ticket
klärt den für StockInfo passenden Weg. Die Paketstruktur entsteht getrennt
in ProjectTools. Keine vorweggenommene Entscheidung über StockInfos
Abhängigkeiten oder über die konkrete Implementierung.

## Klärung und technische Nachweise

| Repo | Time-box | Scope | GH-Issue |
|---|---|---|---|
| StockInfo | 1–2 h | Python-Umgebung für den lokalen StockPortfolio-Testaufruf | — |

Prüfen, ob StockInfos bestehende Projekt-venv die richtige Umgebung für
dieses Konsumentenwerkzeug ist und wie das ProjectTools-Paket dort
reproduzierbar verfügbar wird. Dabei den lokalen Entwicklungsweg, frische
Checkouts und den Aufruf aus StockPortfolio betrachten. Einen anderen
Installationsweg nur wählen, wenn er den gleichen maschinenunabhängigen
Aufruf ermöglicht. Die Entscheidung und ihre Grenze im Ticket begründen.

### Verify

Legende: ➖ noch keine Live-Verifikation.

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | In einer frischen StockInfo-Umgebung den dokumentierten Installationsweg ausführen | `projecttools.ui.colors` ist ohne absoluten Rechnerpfad und ohne `sys.path`-Änderung importierbar | ➖ |
| 2 | StockPortfolios Testskript mit der vorgesehenen Python-Umgebung und `--help` starten | Hilfe erscheint ohne laufenden Dienst und ohne Seiteneffekte | ➖ |
| 3 | Den Teststack nach der gewählten Einbindung starten, Status prüfen und stoppen | StockInfo und StockPortfolio bleiben über den dokumentierten Aufruf erreichbar; fremde Prozesse und Daten bleiben unangetastet | ➖ |
| 4 | StockInfos bestehende Tests und die betroffenen Entwickleranleitungen prüfen | Keine Regression; Installationsschritte und Zuständigkeit sind nachvollziehbar | ➖ |

### Akzeptanzkriterien

- [ ] Der für StockInfo gewählte Installationsweg ist begründet und reproduzierbar.
- [ ] StockPortfolios Skript kann die gemeinsame CLI-Darstellung über den Paketimport nutzen, ohne Rechnerpfad im Code.
- [ ] Hilfe und Teststack funktionieren auf dem dokumentierten Entwicklungsweg.
- [ ] Betroffene Anleitungen in beiden Repositories sind auf Konsistenz geprüft; nötige Anpassungen sind dokumentiert.

### Side-Effects

Kein Eingriff in StockInfos Kurs- oder API-Vertrag. Keine globale
Python-Installation und keine automatische Änderung fremder Projekt-venvs.
ProjectTools bleibt ein eigenes Repository mit eigenem Commit.

### Auflösung

Offen. Umsetzung, Verifikation und unabhängiges Review folgen nach
Aktivierung gemäß `_tickets/STATUS.md`.
