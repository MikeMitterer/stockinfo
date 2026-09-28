# T-80 · Hinweise zu Daten und Nutzung in beiden Apps

StockInfo und StockPortfolio zeigen Finanzdaten, ohne in der Oberfläche an
einem gut auffindbaren Ort deren Grenzen zu erklären. Nutzer sollen erkennen,
dass Angaben aus externen Quellen, dem lokalen Bestand und eigenen Eingaben
fehlen, veraltet oder fehlerhaft sein können. Sie sollen außerdem die
Lizenztexte und die bestehende Verbraucherklärung erreichen.

**Beispiel:** Ein angezeigter Kurs oder eine daraus berechnete Zahl ist kein
verbindlicher Handelskurs. Eine Entscheidung sollte anhand der maßgeblichen
Quelle geprüft werden. Die Oberfläche erklärt das in der gewählten Sprache;
ein Link in der Statuszeile führt direkt zur Erklärung.

**Stand:** Beide Oberflächen sind in den Ticket-Branches umgesetzt und vom
Coder geprüft; Claudes unabhängige Prüfung steht aus. StockPortfolio hat
weiterhin `legal.html` und den Statuszeilenlink
„Lizenz & Quellcode“. Beide Projekte enthalten `LICENSE`, `LICENSE.de.txt`
und `LICENSING.md`. StockInfos EUPL-Ticket T-79 nennt eine persönliche
Wiedervorlage zur rechtlichen Prüfung; sie ist hier nicht als erledigt erklärt.

**Nächster Schritt:** Die StockInfo-About-Seite ist mit Mikes zwei
Original-Logos für helle und dunkle Themes im Browser geprüft und wird Claude
zur unabhängigen Prüfung übergeben. Die zuständige StockPortfolio-Instanz
übernimmt das Layout anhand ihres lokalen T-58 und organisiert dort die eigene
Prüfung. Die rechtliche Prüfung des endgültigen Wortlauts bleibt als
gesonderte menschliche Wiedervorlage sichtbar.

## Umfang

Dieses Ticket hat einen Ort im StockInfo-Board und zwei betroffene Repositories:
StockInfo und StockPortfolio. Die UI und die Datenhinweise werden je App
angepasst. Es entsteht kein dritter, gemeinsam gepflegter Rechtstext.
StockPortfolios lokales T-58 regelt dort Umsetzung und Reviewübergabe.

### StockInfo

- Unter **Einstellungen** einen adressierbaren Reiter „About“ mit kurzen
  Hinweisen zu Datenherkunft, Aktualität, Fehlergrenzen
  und eigenverantwortlicher Prüfung ergänzen. Die fünf Punkte der
  Hauptnavigation bleiben wie bisher.
- Den Reiter aus der Statuszeile direkt erreichbar machen. Der Link steht
  unmittelbar nach „powered by MangoLila“ in der Schrift der Statuszeile.
  Beschriftung und Inhalt folgen der gewählten Sprache; ein Sprachwechsel
  wirkt ohne Neuladen.
- Auf die EUPL verlinken: Deutsch zu `LICENSE.de.txt`, Englisch zu `LICENSE`.
  Die tatsächlich ausgelieferte URL muss in der laufenden App funktionieren.
  Die bestehende Verbraucherklärung in `LICENSING.md` ist ebenfalls erreichbar;
  die Oberfläche widerspricht ihr nicht. Ein zusätzlicher Link führt zu
  MangoLilas Hinweis für Finanzinhalte auf Website und in Publikationen.
- Logo, Anschrift und Website-Link der MangoLila GmbH stehen rechts neben dem
  About-Text, durch eine senkrechte Linie getrennt. Auf schmalen Bildschirmen
  stehen sie darunter ohne Querlinie. Die Statuszeile enthält ausschließlich
  den About-Link, keine Anschrift.

### StockPortfolio

- Den gleichen **Nutzerweg** bereitstellen: einen auffindbaren Reiter „About“
  und einen direkten
  Statuszeilenlink. Den vorhandenen Link „Lizenz & Quellcode“ zu `legal.html`
  berücksichtigen; seine Lizenz- und Quellcode-Funktion erhalten.
- Die Aussagen an Bestandswerte, Kursalter, Berechnungen und die tatsächlich
  vorhandenen Handlungsanzeigen anpassen. Unter Dashboard- und Rebalancing-
  Tabelle steht ein kleiner Hinweis zu berechneten Kauf- und Verkaufswerten.
- Den vorhandenen Auslieferungsweg für die englische und deutsche EUPL sowie
  `LICENSING.md` benutzen. Der sprachabhängige Link zeigt auf den passenden
  Lizenztext und erreicht eine im Build enthaltene Datei. Der MangoLila-Hinweis
  für Website-Finanzinhalte wird ebenfalls verlinkt.
- Das StockInfo-Layout wird von der StockPortfolio-Instanz anhand ihres
  T-58 übertragen. Die neue Anschrift ist dort noch nicht umgesetzt.

### Wortlaut und Grenzen

Der Hinweis erklärt konkrete Grenzen und verweist auf die Originalquellen.
Ein pauschaler Satz wie „Für nichts haftbar“ ist kein Ziel. Die bestehende
Erklärung von MangoLila GmbH für Verbraucher in `LICENSING.md` bleibt
maßgeblich: Gegenüber Verbrauchern beruft sie sich nicht auf die Ausschlüsse
der EUPL-Artikel 7 und 8; stattdessen gelten die gesetzlichen Regeln.
Die offiziellen Lizenztexte bleiben unverändert. Eine rechtliche Prüfung des
endgültigen öffentlichen Texts ist weiterhin Mikes Entscheidung.

## Technische Prüfung

| # | Fall | Erwartetes Ergebnis | AI |
|---|---|---|:--:|
| 1 | StockInfo: Statuszeilenlink in DE und EN öffnen | Jeweils der About-Reiter mit übersetztem Hinweis; Direktadresse funktioniert nach Neuladen | ➖ |
| 2 | StockInfo: Lizenz- und Erklärungslinks in DE und EN öffnen | DE führt zur deutschen EUPL, EN zur englischen EUPL; `LICENSING.md` ist erreichbar | ➖ |
| 3 | StockPortfolio: Statuszeilenlink und vorhandene Lizenzseite prüfen | About-Hinweis erreichbar; Lizenz-/Quellcodezugang bleibt funktionsfähig | ➖ |
| 4 | StockPortfolio: Hinweis mit tatsächlichen Ansichten abgleichen | Kursalter, Bestands- und Berechnungsdaten sowie Handlungsanzeigen werden zutreffend beschrieben | ➖ |
| 5 | Beide Apps: schmale Ansicht, Tastatur und Sprachwechsel prüfen | Links bleiben bedienbar und beschriftet; Inhalte wechseln ohne Neuladen | ➖ |
| 6 | Dokumentation beider Repositories abgleichen | Root- und Docker-READMEs erklären den aktuellen Zugang; Unraid-READMEs bei betroffenem Betrieb | ➖ |
| 7 | StockInfo-Anbieterbereich prüfen | Logo, Anschrift und Website-Link auf About rechts mit senkrechter Linie, mobil ohne Querlinie; keine Anschrift in der Statuszeile | ➖ |
| 8 | Anbieterbereich nach StockPortfolio übertragen | Gleiches Layout und Theme-Logos auf About; Statuszeile bleibt unverändert | ➖ |
| 9 | StockInfo-Einstellungen mobil bedienen | Unter 768 px ersetzt eine Bereichsauswahl die Tab-Leiste; der aktive Bereich und Direktadressen bleiben erreichbar | ➖ |

Die Tabelle enthält die ursprünglichen Prüffälle. Die Coder-Nachweise stehen
darunter; menschliche Antworten und eine rechtliche Freigabe werden nicht von
der KI eingetragen.

## Coder-Prüfung · 2026-09-28

- StockInfo: `make test-dashboard` — 384 Tests in 52 Dateien bestanden;
  Production-Build bestanden. Browser: Direktadresse `#/settings?tab=about`,
  Position nach MangoLila und identische berechnete Schrift (11 px) geprüft.
  Die drei GitHub-Ziele für EUPL DE/EN und `LICENSING.md` antworten mit HTTP 200.
  Die MangoLila-Seite antwortet ebenfalls mit HTTP 200. Ihr Wortlaut nennt
  Website, Social-Media-Kanäle und Publikationen, nicht diese Software; die
  About-Ansicht stellt sie daher als ergänzenden Link dar.
- StockPortfolio: lokaler T-58-Branch mit `Settings → About`, Statuszeilenlink
  sowie Hinweisen unter beiden Tabellen. Details und der bekannte unabhängige
  Docker-Testfehler stehen im dortigen Ticket.
- **Doku-Abgleich:** `README.md`, `docker/README.md`, `unraid/README.md`
  erklären den Zugang und die sprachabhängigen Lizenzlinks übereinstimmend.
  Docker-Hub-Vorschau erfolgreich. `AGENTS.md` nennt den Testserver mit
  temporärer Datenbank.

## Coder-Prüfung · About-Anbieterbereich · 2026-09-28

- Die Anschrift steht nur auf `Settings → About`; die Statuszeile enthält
  weiterhin nur den Link zum Reiter. Das transparente Original-Logo mit
  weißer Schrift erscheint im dunklen Theme, das mit schwarzer Schrift im
  hellen Theme. Beide sind 200 × 57 px groß; die Bilddateien wurden unverändert
  übernommen. Der Website-Link führt zu `https://www.mangolila.at/`.
- Browserprüfung bei 1440 px sowie bei emulierten 390 px Breite: Der Abstand
  zwischen Text und senkrechter Linie beträgt 24 px; mobil stehen Logo,
  Anschrift und Website-Link unter dem Text ohne Querlinie. Keine horizontale
  Überbreite. Die zuvor verwendete, im Theme nicht definierte Variable
  `--space-5` wurde durch `--space-6` ersetzt.
- `make test-dashboard`: 384/384 bestanden; `npm run build` mit isoliertem
  Testserver bestanden; Docker-Hub-Vorschau bestanden. StockPortfolio bleibt
  im T-58-Worktree unverändert, bis das StockInfo-Layout übernommen wird.
- Die Reiterzeile passte bei 390 px nicht: `About` lag außerhalb des sichtbaren
  Bereichs. Unter 768 px zeigt jetzt eine Naive-UI-Auswahl den aktiven Bereich.
  Im Browser von `About` auf `Sprache` gewechselt; die Direktadresse änderte
  sich zu `#/settings?tab=language`. Ab 768 px bleibt die Tab-Leiste erhalten.
  Der zunächst unterhalb der Auswahl sitzende Rahmen kam von einer globalen
  Touch-Mindesthöhe am äußeren Naive-UI-Element: Das innere Label blieb 34 px
  hoch, der Rahmen wurde 44 px hoch. Beide erhalten nun dieselbe Mindesthöhe.
- **Doku-Abgleich:** `README.md`, `docker/README.md`, `unraid/README.md`
  nennen jetzt Logo, Anschrift und Website-Link auf About. Die Lizenzhinweise
  und die Trennung des MangoLila-Webhinweises von der Verbraucherklärung
  bleiben inhaltlich gleich.

## Dokumentation und Schnittstellen

Vor Umsetzung das Datei- und Überschrifteninventar der aktuellen Anleitungen
beider Repositories prüfen. In jedem Repo `README.md` und
`docker/README.md` inhaltlich abgleichen, bei Unraid-Auswirkungen auch
`unraid/README.md`. StockInfos Docker-Hub-Vorschau nach Änderungen an
`docker/README.md` ausführen. Die Lizenz- und Verbrauchertexte werden verlinkt,
nicht für die About-Ansicht kopiert.

Keine Änderung der REST-API, Datenbank oder Lizenzbedingungen vorgesehen.
StockPortfolio liegt in einem eigenen Repository; dessen Regeln, Rollen und
Schreibrechte sind vor dem Produktedit gesondert zu prüfen.
