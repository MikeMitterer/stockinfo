# T-84 · Hinweise zum Internetbetrieb unabhängig prüfen

Die neuen StockInfo-Warnungen liegen in Anleitungen und Unraid-Vorlage vor,
wurden aber noch nicht unabhängig geprüft. StockInfo hat keine Anmeldung;
wer den Dienst erreichen kann, kann Daten ändern oder löschen. Vor einer
Veröffentlichung soll der zuständige Verifier prüfen, ob diese Grenze in
allen Texten zutreffend und gut sichtbar erklärt ist.

**Beispiel:** Ein Nutzer möchte den Unraid-Port 8000 am Router freigeben.
Die Vorlage soll schon bei der Installation warnen, und die Anleitungen
sollen einen geschützten Zugriffsweg nennen.

**Stand:** Mike hat am 2026-10-01 einen Reviewauftrag verlangt. Der
Dokumentations-Commit `396e8be` und der zentrale Template-Commit `ca7ae2d`
sind lokal vorbereitet; eine unabhängige Review-Übergabe oder Freigabe hat
noch nicht stattgefunden. Dieses Ticket liegt im Backlog. T-83 bleibt aktiv,
T-82 bleibt danach vorgesehen; Rollen, Phase und Priorität sind unverändert.

Für Mike steht jetzt kein Handgriff an. Abschluss und Veröffentlichung
bleiben nach der technischen Prüfung getrennt; Docker Hub und das
Unraid-Listing zeigen die neue Fassung derzeit nicht.

## Prüfgegenstand

| Repo | Time-box | Scope | GH-Issue |
|---|---|---|---|
| StockInfo | 0,5–1 h | `README.md`, `docker/README.md`, `unraid/README.md`; Commit `396e8bebc403144a8900bf45bf9c56644467499c` gegen `f821c2ab546ba7b47f3dc2828de3fc953490ea3d` | — |
| Unraid-Templates | 0,5 h | ausschließlich `templates/stockinfo.xml` aus Commit `ca7ae2d7b15331bf84a0fa344f436c37e3863e9c` gegen `c828e24671a81fd53824f67e3fea21b4e35b280b` | — |

Beide Commits liegen auf dem jeweiligen Branch `docs/internet-zugriff-hinweis`.
In StockInfo wird dieser Branch im Projekt-Root ausgecheckt; die frühere
Arbeitskopie unter `/private/tmp/stockinfo-internet-hinweis` entfällt mit
T-85. Das Unraid-Templates-Repository hat weiterhin seine Arbeitskopie
`/private/tmp/unraid-internet-hinweis`; T-85 ändert dort nichts. Das Gegenstück für StockPortfolio
wird im dortigen T-67 mit dessen Rollen geprüft. Der gemeinsame Template-
Commit wird pro Ticket nur für die eigene XML-Datei bewertet.
Eine Freigabe des gesamten Template-Commits braucht auch das StockPortfolio-
Prüfergebnis aus T-67.

Vor einer formellen Übergabe stellt der zuständige Coder `codex` die
Dokumentationsfassung auf dem dann aktuellen StockInfo-Stand bereit und
schreibt die OUTBOX mit den endgültigen Commit-IDs. Der unabhängige Review
gehört `claude`. Der bisherige Branch baut auf der T-83-Aktivierung auf;
spätere T-83-Änderungen sind darin noch nicht enthalten. Keine Reviewphase
allein aus den vorbereiteten Commits ableiten.

### Verify

Legende: ➖ unabhängige Prüfung steht aus. Die Autorprüfung ist unten genannt
und ersetzt kein Verifier-Urteil.

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | StockInfo-Diff gegen tatsächliche API-Routen und das Authentifizierungsmodell lesen | Hinweis erklärt fehlende Anmeldung und ändernde/löschende Zugriffe ohne unzutreffende Sicherheitszusage | ➖ |
| 2 | `README.md`, `docker/README.md` und `unraid/README.md` inhaltlich abgleichen | Direkte Internetfreigabe wird konsistent abgeraten; LAN, VPN und HTTPS-Proxy mit Anmeldung sind verständlich beschrieben | ➖ |
| 3 | `templates/stockinfo.xml` gegen die Anleitungen und Containerkonfiguration prüfen | Englischer Hinweis steht sichtbar in Overview, Description und Portfeld; keine andere Template-Funktion geändert | ➖ |
| 4 | Docker-Hub-Vorschau und XML erneut am endgültigen Prüfstand erzeugen | Vorschau unter 25.000 UTF-8-Bytes, Links korrekt; XML gültig | ➖ |
| 5 | Git-Fassung und Veröffentlichungsstand trennen | Review benennt geprüfte Commit-IDs und hält fest, dass kein Merge, Push oder Hub-/Unraid-Update belegt ist | ➖ |

**Autorbelege vom 2026-10-01:** `git diff --check` ohne Befund;
`xmllint --noout` für beide Templates erfolgreich. Die Docker-Hub-Vorschau
von StockInfo wurde erzeugt und hatte 8.006 UTF-8-Bytes. Das sind
Vorprüfungen, keine unabhängige Freigabe.

### Akzeptanzkriterien

- [ ] `claude` prüft die eindeutig benannte Endfassung unabhängig und hält Befunde oder Freigabe im Ticket fest.
- [ ] Der Doku-Abgleich umfasst beide READMEs, die Unraid-Anleitung und den StockInfo-Teil der zentralen Vorlage.
- [ ] Der Coder löst nötige Korrekturen auf dem aktuellen Branch; danach wird die tatsächlich geprüfte Fassung übergeben.
- [ ] Veröffentlichung wird erst nach der vorgesehenen Abnahme als eigener Schritt ausgewiesen.

### Side-Effects

Nur Dokumentation und Template-Beschreibung. Die aktive T-83-Umsetzung,
StockPortfolios eigener Review und die Containerkonfiguration bleiben
außerhalb dieses Reviewauftrags. Kein Produktcode wird durch das Ticket
geändert.

### Auflösung

Offen. Erst nach Aktivierung darf der Coder die formelle Übergabe vorbereiten;
ein Prüfurteil oder Ticketabschluss liegt noch nicht vor.
