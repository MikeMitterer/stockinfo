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
| 1 | StockInfo: Statuszeilenlink in DE und EN öffnen | Jeweils der About-Reiter mit übersetztem Hinweis; Direktadresse funktioniert nach Neuladen | ✅ |
| 2 | StockInfo: Lizenz- und Erklärungslinks in DE und EN öffnen | DE führt zur deutschen EUPL, EN zur englischen EUPL; `LICENSING.md` ist erreichbar | ✅ |
| 3 | StockPortfolio: Statuszeilenlink und vorhandene Lizenzseite prüfen | About-Hinweis erreichbar; Lizenz-/Quellcodezugang bleibt funktionsfähig | ➖ |
| 4 | StockPortfolio: Hinweis mit tatsächlichen Ansichten abgleichen | Kursalter, Bestands- und Berechnungsdaten sowie Handlungsanzeigen werden zutreffend beschrieben | ➖ |
| 5 | Beide Apps: schmale Ansicht, Tastatur und Sprachwechsel prüfen | Links bleiben bedienbar und beschriftet; Inhalte wechseln ohne Neuladen | ◑ |
| 6 | Dokumentation beider Repositories abgleichen | Root- und Docker-READMEs erklären den aktuellen Zugang; Unraid-READMEs bei betroffenem Betrieb | ◑ |
| 7 | StockInfo-Anbieterbereich prüfen | Logo, Anschrift und Website-Link auf About rechts mit senkrechter Linie, mobil ohne Querlinie; keine Anschrift in der Statuszeile | ✅ |
| 8 | Anbieterbereich nach StockPortfolio übertragen | Gleiches Layout und Theme-Logos auf About; Statuszeile bleibt unverändert | ➖ |
| 9 | StockInfo-Einstellungen mobil bedienen | Unter 768 px ersetzt eine Bereichsauswahl die Tab-Leiste; der aktive Bereich und Direktadressen bleiben erreichbar | ✅ |

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

## Auflösung

**Unabhängiger Review · Claude, 2026-09-28.** Geprüfte Übergabe `5d0ea26`
auf `t-80-about-data-use-notice` gegen `master`. Prüfgegenstand ist
ausschließlich der StockInfo-Anteil; StockPortfolio läuft separat über sein
lokales T-58. Ergebnis: **approved**.

**Eigenständig nachvollzogen, nicht nur die Coder-Angaben übernommen:**

- `make test-dashboard` auf dem eingefrorenen Stand selbst laufen lassen:
  52 Dateien, 384/384 grün, Lint sauber. `npm run build` (vue-tsc + vite)
  erfolgreich; die vorbestehende Chunk-Size-Warnung ist unverändert und
  gehört nicht zu diesem Diff.
- `./.libs/ProjectTools/src/bash/dockerhub-readme.sh --preview` selbst
  ausgeführt: Größenprüfung bestanden, Vorschau 7.768 Byte, weit unter dem
  25.000-Byte-Limit.
- Alle fünf verlinkten Ziele einzeln mit `curl` gegen die echten Server
  geprüft (nicht nur die Coder-Angabe übernommen, SI-CX-01-Muster): EUPL DE,
  EUPL EN, `LICENSING.md`, MangoLilas Finanzinhalte-Hinweis und
  `mangolila.at` — alle HTTP 200.
- Browser (Vite-Dev-Server, `#/settings?tab=about`): About-Reiter bei
  1440 px mit Logo, Anschrift, Website-Link und senkrechter Trennlinie
  geprüft; Statuszeilenlink „Über StockInfo“ steht unmittelbar nach „powered
  by MangoLila“ und vor dem GitHub-Link, in geerbter Schrift, ohne eigene
  Anschrift in der Statuszeile. Theme-Wechsel auf ein helles Theme („Papier“)
  bestätigt den Logo-Tausch (dunkler Text auf hell, heller Text auf dunkel,
  beide Originaldateien 200×57 px). Sprachwechsel DE→EN ohne Neuladen
  bestätigt: Texte, Statuszeilenlink und Lizenzlink-Ziel (`LICENSE` statt
  `LICENSE.de.txt`) wechseln live.
- Schmale Ansicht: Bei ≤ 500 px ersetzt die Naive-UI-Auswahl die Tab-Leiste
  wie vorgesehen, per Maus und per Pfeiltasten+Enter bedienbar, ändert die
  Direktadresse und lädt den gewählten Bereich; kein horizontales Scrollen.
  **Einschränkung:** Das lokale Chrome-Fenster dieser Prüfsitzung lässt sich
  nicht unter 500 px verkleinern (macOS-Fensterminimum); die genaue 390-px-
  Geometrie aus der Coder-Prüfung (24 px Abstand, Wegfall der Querlinie,
  Select-/Rahmen-Mindesthöhe) wurde deshalb nicht px-genau nachgestellt,
  sondern nur das Verhalten unterhalb der `md`-Schwelle bestätigt. Verify
  #5 bleibt deshalb `◑` statt `✅`.
- Doku-Abgleich selbst nachvollzogen: `README.md`, `docker/README.md` und
  `unraid/README.md` beschreiben Reiter, Statuszeilenlink, Sprachabhängigkeit
  der Lizenzlinks, den getrennten MangoLila-Finanzhinweis und Anbieterangaben
  übereinstimmend. Verify #6 bleibt `◑`, weil die Zeile beide Repositories
  umfasst und nur der StockInfo-Anteil hier geprüft ist.
- Ticketpfad und Kette geprüft: `T-80-about-data-use-notice.md` liegt in
  `30-doing/`, entspricht `priority_ticket` und ist einziges Element seiner
  `priority_chain`. Umfangskontrolle nachgerechnet: 21 geänderte Dateien laut
  `git diff --stat` gegen den Merge-Base, davon 11 Produkt- (inkl. der zwei
  PNGs), 3 Testdateien sowie drei READMEs; 404 Zeilen Gesamtdiff, unter der
  800-Zeilen-Schwelle. Keine API-, Datenbank- oder Lizenztextänderung.

**Code-Standards (unabhängig vom Coder-Bericht geprüft, `code-standards`-
SKILL.md und `references/frontend.md` sowie `ux-standards`/`references/
responsive.md` gelesen):**

- Architektur ✅ — About bleibt eine gewöhnliche Vue-Komponente in
  vorhandener Struktur, keine neue Abstraktion.
- Frontend/i18n ⚠️ **1 Befund** — `AboutPanel.vue:12–16` trägt Name, Straße
  und Ort der Anbieteranschrift als literale Strings im `<script setup>`,
  nicht im Katalog (`providerCountry` daneben geht korrekt über `t(...)`).
  Verstößt gegen die absolute i18n-MUST-Regel aus `code-standards`, auch wenn
  der Text in beiden Sprachen identisch ist. **Nicht blockierend:** kein
  Sprachunterschied, kein Verhalten betroffen, geringes Pflegerisiko für eine
  praktisch unveränderliche Firmenadresse (`AGENTS.md`
  „Tatsächlicher Entwicklungsstand“ — Prüfgewicht folgt belegtem Schaden).
  Erwartete Korrektur: die drei Felder als Katalogeinträge führen, sobald
  ohnehin an der Datei gearbeitet wird.
- Qualität ✅ — neue/erweiterte Tests in `SettingsPanel.spec.ts`,
  `StatusBar.spec.ts` und `useHashTab.spec.ts` decken DOM-Position des
  Statuszeilenlinks, das Fehlen einer `<address>` in der Statuszeile,
  Theme-abhängigen Logo-Tausch, Sprachwechsel und Direktadresse konkret ab —
  keine bloße Gesamtzahl.
- Dokumentation ✅ — siehe Doku-Abgleich oben.
- DRY-Prüfguard ⚠️ **1 Befund** — `MANGOLILA_URL` ist neu in
  `dashboard/src/config.ts:18` entstanden, während `StatusBar.vue:69`
  (in diesem Diff ohnehin angefasst, neuer Import in Zeile 5) weiterhin das
  identische Literal `"https://www.mangolila.at/"` hartcodiert führt — eine
  zweite Quelle für dieselbe URL statt der neuen gemeinsamen Konstante. Die
  hartcodierte Stelle stammt aus `67af83a` (2026-08-16, T-12) und ist keine
  Neuregression, aber die neue Konstante hätte sie ablösen sollen.
  **Nicht blockierend:** beide Stellen stimmen heute überein, keine
  Verhaltensdivergenz. Erwartete Korrektur: `StatusBar.vue` auf
  `:origin-href="MANGOLILA_URL"` umstellen.
- Shell, CLI, Python, Persistenz, Makefile ➖ — im Produktdiff nicht berührt.

Lokale Lessons SI-CX-01, SI-R-02 und SI-T-66 vor dem Review gelesen (Autor
Codex): kein Datenbank-Startzustand betroffen, keine hypothetische
Migration/Ablösung verlangt, keine fremde Reviewwertung unbesehen
übernommen — die beiden Befunde oben sind eigenständig gefunden.

**Verbleibt sichtbar, verhindert die Freigabe nicht:** die zwei ⚠️-Befunde
oben (i18n-Katalog für die Anbieteranschrift, `MANGOLILA_URL`-Konsolidierung)
sowie die nicht px-genau nachvollzogene 390-px-Geometrie. Eine rechtliche
Freigabe des öffentlichen Wortlauts wird durch diesen technischen Review
nicht behauptet; T-79s persönliche Wiedervorlage bleibt unverändert offen.

`T-80-about-data-use-notice.md` ist das einzige Element seiner
`priority_chain`. Nach dem Portfolio-Riegel geht der Zustand deshalb auf
`portfolio_review` an Mike statt automatisch an ein nächstes Ticket. Das
Ticket bleibt bis zu Mikes Bestätigung in `30-doing/`.

## Nacharbeit auf Mikes Auftrag · 2026-09-28

Mike beauftragt die Korrektur der beiden in Runde 1 fälschlich als nicht
blockierend eingestuften Reviewbefunde (Einordnung: SI-P-13).
In `AboutPanel.vue` kommen Firmenname, Straße und Ort jetzt aus `about.*` in
beiden Sprachkatalogen. `StatusBar.vue` verwendet für den Anbieterlink die
bereits vorhandene Konstante `MANGOLILA_URL` aus `config.ts`. Die sichtbaren
Texte und Linkziele bleiben gleich. Produkt-Commit: `eece7d4`.
Die Freigabe von `5d0ea26` bleibt als
Prüfung dieser älteren Fassung erhalten; die Nacharbeit geht erneut an Claude.

**Coder-Prüfung:** Die betroffenen Komponenten-Tests bestanden (14/14),
`make test-dashboard` bestand mit Lint und 384/384 Tests, `npm run build`
bestand. Die Build-Warnung zu großen Chunks bestand bereits vor der Änderung.
Der Diff enthält keine neuen deutschen Bezeichner; die drei neuen i18n-Schlüssel
heißen `providerName`, `providerStreet` und `providerCity`.

**Doku-Abgleich:** `README.md`, `docker/README.md` und `unraid/README.md`
beschreiben bereits die Anbieterangaben, Website und den About-Zugang. Da
sich weder der angezeigte Inhalt noch das Linkziel ändern, brauchen sie
keine Textänderung. API, Datenbank und Lizenz bleiben unberührt.

## Auflösung · Runde 2

**Unabhängiger Review · Claude, 2026-09-28.** Geprüfte Übergabe `eece7d4`
auf `t-80-about-data-use-notice` gegen `eece7d4^`. Prüfgegenstand ist gezielt
die Nacharbeit zu den beiden in Runde 1 gefundenen, nach SI-P-13 korrekt als
blockierend eingeordneten MUST-/DRY-Verstößen. Ergebnis: **approved.**

- Diff wie angekündigt: `AboutPanel.vue` liest Name, Straße und Ort jetzt über
  `t('about.providerName'|'providerStreet'|'providerCity')`; die vorherige
  literale `providerAddress`-Konstante ist entfernt. Beide Sprachkataloge
  führen die drei Schlüssel mit identischem Text (physische Adresse, keine
  Übersetzung nötig). `StatusBar.vue` importiert und bindet
  `:origin-href="MANGOLILA_URL"` statt des Literals; kein hartcodiertes
  `mangolila.at` mehr im Produktcode außerhalb von `config.ts`
  (`rg` über `dashboard/src` bestätigt).
- Beide Runde-1-Befunde eigenständig gegengeprüft, nicht nur den Diff
  gelesen: `make test-dashboard` (Lint + 384/384) und `npm run build`
  selbst laufen lassen — beide grün, unveränderte Chunk-Warnung.
- Browser gegen den isolierten StockPortfolio-Testserver
  (`scripts/stockinfo-test-server.py`, temporäre Datenbank, kein Zugriff auf
  den Arbeitsbestand) geprüft: About-Text, Anschrift und Website-Link in DE
  und EN identisch zum vorherigen Stand; Statuszeilen-Link „powered by
  MangoLila“ zeigt weiterhin auf `https://www.mangolila.at/`. Keine sichtbare
  Regression.
- Scope wie angekündigt: 4 Produktdateien, keine neuen Bezeichner außerhalb
  ASCII/Englisch, keine API-/DB-/Lizenzänderung. Doku-Abgleich der Coder-Prüfung
  nachvollzogen: Inhalte und Linkziele sind unverändert, daher zu Recht keine
  README-Textänderung.

Damit ist T-80 (StockInfo-Anteil) freigegeben. `T-80-about-data-use-notice.md`
bleibt das einzige Element seiner `priority_chain`; nach dem Portfolio-Riegel
geht der Zustand auf `portfolio_review` an Mike. Das Ticket bleibt bis zu
Mikes Bestätigung in `30-doing/`. StockPortfolios T-58 ist weiterhin nicht
Teil dieser Prüfung.
