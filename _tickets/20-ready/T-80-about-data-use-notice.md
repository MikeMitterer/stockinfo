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

**Stand:** Das Ticket ist aufgenommen; Produktcode wurde dafür noch nicht
geändert. StockPortfolio hat bereits `legal.html` und den Statuszeilenlink
„Lizenz & Quellcode“. Beide Projekte enthalten `LICENSE`, `LICENSE.de.txt`
und `LICENSING.md`. StockInfos EUPL-Ticket T-79 nennt eine persönliche
Wiedervorlage zur rechtlichen Prüfung; sie ist hier nicht als erledigt erklärt.

**Nächster Schritt:** Die Umsetzung im zuständigen Board einplanen. Die
rechtliche Prüfung des endgültigen Wortlauts bleibt als gesonderte menschliche
Wiedervorlage sichtbar.

## Umfang

Dieses Ticket hat einen Ort im StockInfo-Board und zwei betroffene Repositories:
StockInfo und StockPortfolio. Die UI und die Datenhinweise werden je App
angepasst. Es entsteht kein dritter, gemeinsam gepflegter Rechtstext und keine
zweite Ticketkopie im StockPortfolio-Board.

### StockInfo

- Unter **Einstellungen** einen adressierbaren Reiter „Über StockInfo“ / „About
  StockInfo“ mit kurzen Hinweisen zu Datenherkunft, Aktualität, Fehlergrenzen
  und eigenverantwortlicher Prüfung ergänzen. Die fünf Punkte der
  Hauptnavigation bleiben wie bisher.
- Den Reiter aus der Statuszeile direkt erreichbar machen. Beschriftung und
  Inhalt folgen der gewählten Sprache; ein Sprachwechsel wirkt ohne Neuladen.
- Auf die EUPL verlinken: Deutsch zu `LICENSE.de.txt`, Englisch zu `LICENSE`.
  Die tatsächlich ausgelieferte URL muss in der laufenden App funktionieren.
  Die bestehende Verbraucherklärung in `LICENSING.md` ist ebenfalls erreichbar;
  die Oberfläche widerspricht ihr nicht.

### StockPortfolio

- Den gleichen **Nutzerweg** bereitstellen: eine auffindbare „Über
  StockPortfolio“ / „About StockPortfolio“-Ansicht und einen direkten
  Statuszeilenlink. Den vorhandenen Link „Lizenz & Quellcode“ zu `legal.html`
  berücksichtigen; seine Lizenz- und Quellcode-Funktion erhalten.
- Die Aussagen an Bestandswerte, Kursalter, Berechnungen und die tatsächlich
  vorhandenen Handlungsanzeigen anpassen. Nicht pauschal behaupten, die App
  gebe keine Empfehlung, bevor ihre sichtbaren Funktionen geprüft wurden.
- Den vorhandenen Auslieferungsweg für die englische und deutsche EUPL sowie
  `LICENSING.md` benutzen. Der sprachabhängige Link zeigt auf den passenden
  Lizenztext und erreicht eine im Build enthaltene Datei.

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

`➖` bedeutet hier: noch nicht umgesetzt oder live geprüft. Technische Belege
werden beim jeweiligen Schritt unter derselben Prüfnummer ergänzt; menschliche
Antworten und eine rechtliche Freigabe werden nicht von der KI eingetragen.

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
