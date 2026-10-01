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

**Stand:** Mike hat das Ticket am 2026-10-01 ausdrücklich in Doing gesetzt
und nach T-85 an Coder `claude` gegeben; Verifier ist `codex`. T-82 bleibt
danach als nächstes Ticket in Ready. Die endgültige öffentliche Formulierung
ist mit der bestehenden Verbrauchererklärung abzugleichen.

**Vorgabe Mike, 2026-10-01:** Der Hinweis hat dieselbe Schriftgröße wie
StockPortfolios Hinweis unter Dashboard- und Rebalancing-Tabelle
(`TradeNotice.vue`: `var(--font-xs)`, `token(--text-muted)`,
`line-height: 1.45`, oben `var(--space-1)` Abstand).

**Befund Mike, 2026-10-01, zur Fassung `4acdc02`:** „Der Text steht in!!!
der Tabelle, nicht darunter“. Der Hinweis gehört unter die Tabellenkarte, nicht
als letzte Zeile in sie hinein, wie `TradeNotice` außerhalb der Section in
StockPortfolio. Mike ließ Codex' Runde 1 erst zu Ende prüfen; umgesetzt in
Runde 2.

## Scope-Vertrag

- **Ergebnis:** Bei mindestens einem Asset steht unter der Tabelle (breit)
  beziehungsweise unter der Kartenliste (schmal) genau ein Datenhinweis in
  der aktiven Sprache. Bei leerer Übersicht steht er nicht dort.
- **Fachliche Änderungen (2):** Katalogtext DE/EN; Ausgabe in
  `InstrumentsTable.vue` direkt **nach** der Assets-Karte (zweiter
  Wurzelknoten). Eine Stelle für beide Breiten. `AppDashboard.vue` gibt dem
  Hinweis dieselbe Breitenregel wie der Karte, die über 1200 px hinaus bis
  1600 px breiter wird; so steht er links bündig darunter.
- **Produktdateien (3, ab Runde 2: 4):** `dashboard/src/components/InstrumentsTable.vue`,
  `dashboard/src/i18n/de.ts`, `dashboard/src/i18n/en.ts`; mit Mikes Befund
  zusätzlich `dashboard/src/components/AppDashboard.vue` (Breitenregel).
- **Test-/Dokudateien (2–4):** `tests/components/InstrumentsTable.spec.ts`,
  dieses Ticket; README-Abgleich nur, falls die READMEs die Oberfläche
  der Assets-Übersicht beschreiben.
- **Budget:** 3 Produktdateien, 4 Test-/Dokudateien, 200 Diff-Zeilen.
- **Nicht-Ziele:** keine eigene Komponente, kein Paketumbau in ux-foundation,
  keine Änderung an About, API, Kursdaten oder Berechnung.

## Vorgeschlagener Wortlaut

**Deutsch:**

> Die angezeigten Kurse und Kennzahlen können verzögert, unvollständig oder
> fehlerhaft sein. Angezeigte Kurse sind keine verbindlichen Handelskurse.
> Prüfe wichtige Angaben vor einer Entscheidung anhand der ursprünglichen
> Quelle und deiner Eingaben. StockInfo kann ihre Richtigkeit nicht garantieren;
> für Gewährleistung und Haftung gelten die gesetzlichen Regeln.

**Englisch:**

> Displayed prices and metrics may be delayed, incomplete or incorrect.
> Displayed prices are not binding trading prices. Check important information
> against the original source and your own entries before making a decision.
> StockInfo cannot guarantee its accuracy; statutory rules on warranties and
> liability apply.

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

Legende: ✅ bestätigt, ◑ teilweise, ➖ noch keine Live-Verifikation.

| # | Handgriff | Erwarteter Nachweis | AI | Human |
|---|---|---|:--:|---|
| 1 | Assets-Übersicht auf breitem Bildschirm öffnen | Hinweis steht direkt unter der Tabelle, gut lesbar und ohne Überlagerung | ✅ | |
| 2 | Dieselbe Übersicht schmal öffnen | Hinweis steht einmal unter der Kartenliste; keine horizontale Überbreite | ✅ | |
| 3 | Sprache DE → EN → DE wechseln | Wortlaut wechselt ohne Neuladen und bleibt inhaltlich gleich | ✅ | |
| 4 | Wortlaut mit About und `LICENSING.md` abgleichen | Aussagen zu Datenrisiko, Garantie und gesetzlichen Ansprüchen widersprechen einander nicht | ◑ | |
| 5 | Betroffene Dashboard-Prüfungen und Doku-Abgleich ausführen | Keine UI-Regression; `README.md` und `docker/README.md` sind inhaltlich abgeglichen, weitere betroffene Anleitungen benannt | ✅ | |

**Belege (Claude, 2026-10-01):**

Browserlauf mit echter StockInfo-API, temporärer Datenbank und 14 Test-Assets.
Ablauf zum Wiederholen:

1. Test-API starten (aus StockPortfolio, temporäre DB, Port 18083):
   `.venv/bin/python scripts/stockinfo-test-server.py --stockinfo-root <StockInfo> --port 18083 --run`
   mit StockInfos `.venv/bin/python`.
2. Dashboard: `cd dashboard && VITE_DEV_API_TARGET=http://127.0.0.1:18083 npx vite --port 15183 --strictPort`.
3. Messen: `node _tickets/40-done/T-83-browser.mjs --run [URL]`. Ohne
   Argument oder mit `-h|--help` zeigt das Skript nur die Hilfe. Es nutzt
   `playwright-core` aus `dashboard/` (devDependency, Vorgabe Mike). Fehlt der
   zur Version passende Browser, `CHROMIUM_PATH` auf einen vorhandenen
   Chromium setzen; hier lief es mit dem lokalen `chromium_headless_shell-1234`.

Messwerte Runde 2 (Stand nach Mikes Befund):

- **#1 (1440 × 900):** genau ein `.table-notice`, direkter Nachfolger der
  Karte `.table.card`, nicht in ihr; 4 px unter der Karte, links bündig
  (0 px Versatz, gleiche Breite), `font-size` 12 px, `line-height` 17,4 px,
  kein waagrechtes Scrollen. Der Ausschnitt zeigt den Text in zwei Zeilen
  unter dem Kartenrand; nichts wird verdeckt.
- **#2 (390 × 844):** dieselben Werte unter der Karte mit der Kartenliste;
  nicht in einer einzelnen Karte.
- **#3:** Im selben Seitenaufruf DE → EN → DE über die i18n-Instanz: Der Text
  wechselt jedes Mal. Dazu der Komponententest „folgt dem Sprachwechsel ohne
  Neuaufbau“.
- **Schrift wie StockPortfolio:** `TradeNotice.vue` verwendet `var(--font-xs)`
  (ux-foundation: 0,75rem = 12 px), gedämpfte Textfarbe und `line-height: 1.45`.
  `.table-notice` übernimmt diese drei Werte und den Abstand `var(--space-1)`.
  Die Karte hat dafür keinen eigenen Außenabstand nach unten mehr; er trennte
  früher das Chart, das inzwischen im festen Dock steht.
- **#4 ◑:** Technisch abgeglichen: About (`about.data`, `about.use`,
  `about.legal`) nennt dieselben Grenzen und verweist für Gewährleistung und
  Haftung auf die Verbrauchererklärung. `LICENSING.md` sagt: gesetzliche Regeln
  statt EUPL-Ausschlüsse, keine freiwillige Garantie. Der Hinweis
  („kann ihre Richtigkeit nicht garantieren; … gelten die gesetzlichen Regeln“)
  widerspricht dem nicht und schließt nichts aus. Die rechtliche Freigabe des
  Wortlauts bleibt bei Mike.
- **#5:** Runde 2: `vitest` 52 Dateien / 389 Tests grün, `eslint` ohne
  Befund, `npm run build` (inkl. `vue-tsc`) erfolgreich. Stacktraces und
  sieben `n-config-provider`-Warnungen stehen unverändert auch ohne diese
  Änderung in der Ausgabe (`BackupsPanel.spec.ts` u. a.). Doku-Abgleich
  siehe unten.
- **Testreihenfolge Runde 1:** Die vier Hinweis-Tests waren vor dem
  Produktedit rot (3 rot, Leerfall trivial grün). Mutant ohne `v-if`: Der
  Leerfall-Test wird rot.
- **Testreihenfolge Runde 2:** Die Lage-Tests prüfen jetzt, dass der Hinweis
  direkt auf `.table.card` folgt und nicht in ihr liegt. Gegen `4acdc02`
  waren 3 von 4 rot. Gezielter Mutant „neue Klasse, aber wieder in der
  Karte“: Beide Lage-Tests (breit, schmal) werden rot.
- **Prüfskript (B1 aus Runde 1):** `node --check` besteht. Leerer Aufruf und
  `-h` zeigen die Hilfe (Exit 0). Ein unbekannter Aufruf meldet den Fehler
  mit Hilfe (Exit 2). `--run` liefert die Messwerte oben.

### Akzeptanzkriterien

- [x] Der kurze Hinweis steht unmittelbar unter der Assets-Tabelle bzw. der mobilen Kartenliste.
- [x] Deutsch und Englisch entsprechen dem gewählten Sprachzustand.
- [x] Der Wortlaut erklärt mögliche Datenfehler und behauptet keinen vollständigen Ausschluss gesetzlicher Ansprüche.
- [x] Die bestehende About-Erklärung und die Verbraucherklärung bleiben konsistent.
- [x] Doku-Abgleich und Prüfnachweise stehen vor der Übergabe im Ticket.

### Side-Effects

Die zusätzliche Textzeile kann die Übersicht vertikal verlängern. Sie darf
keine Tabelle, Karte oder Bedienfunktion verdecken. StockPortfolios eigene
Hinweise und Tickets bleiben getrennt.

### Doku-Abgleich

- `README.md`, Abschnitt Dashboard → **Assets**: ein Satz zum Hinweis unter
  Tabelle bzw. Kartenliste.
- `docker/README.md`, **What you get**: ein Satz beim Dashboard-Punkt. Die
  Vorschau `dockerhub-readme.sh --preview` hält die 25.000-Byte-Grenze ein.
- `unraid/README.md`, Lizenz- und About-Absatz: ein Satz, dass auch die
  Assets-Liste die Grenzen nennt.
- Die drei Fassungen sagen dasselbe: About erklärt die Grenzen ausführlich,
  der Hinweis unter der Liste nennt sie kurz. `LICENSING.md` und About bleiben
  unverändert.

### Umfang gegenüber dem Scope-Vertrag

- **Geplant / tatsächlich:** 2 / 2 fachliche Änderungen; 3 / 4
  Produktdateien (`AppDashboard.vue` nach Mikes Befund), dazu
  `dashboard/package.json` und `package-lock.json` für die devDependency;
  Test-/Dokudateien 4 geplant, tatsächlich 6 (Spec, Ticket,
  `T-83-browser.mjs`, drei READMEs).
- **Diff-Zeilen:** Runde 1 `0bb9a4d..4acdc02`: 11 Dateien, +273/−16. In der
  Übergabe stand zunächst +312; das war falsch gezählt (Codex, Runde 1).
  Endwert Runde 2 siehe OUTBOX.
- **Abweichung 1, Vorgabe Mike 2026-10-01:** „Wenn du playwright-core
  benötigst - installiere es hier bei den Dependencies. Verwende es nicht
  einfach von einem anderen Project“. Deshalb ist `playwright-core` jetzt
  devDependency im Dashboard. Es kommt nur im Prüfskript vor, nicht im Bundle.
- **Abweichung 2:** Alle drei READMEs beschreiben die Datengrenzen, darum
  ist in jeder ein Satz dazugekommen.
- **DRY:** Der Satz „Angezeigte Kurse sind keine verbindlichen Handelskurse“
  steht auch in `about.data`. Das ist bewusst so: Der Wortlaut des Hinweises
  ist im Ticket vorgegeben und soll für sich allein lesbar sein. Ein
  zusammengesetzter Text aus About-Schlüsseln würde beide Stellen
  aneinanderkoppeln. Der Hinweisstil wiederholt StockPortfolios
  `TradeNotice` über Repo-Grenzen hinweg. Damit gibt es einen zweiten Bedarf
  für eine gemeinsame Hinweiszeile in ux-foundation. Sie ist hier nicht
  beauftragt und als Bedarf festgehalten.

### Auflösung

Umgesetzt auf `t-83-assets-datenhinweis`. Runde 2 behebt Codex' B1 (CLI des
Prüfskripts) und setzt Mikes Befund zur Lage um; Übergabe an Verifier `codex`.
Rechtliche Freigabe des öffentlichen Wortlauts: Mike.

**Abschluss · Mike, 2026-10-01:** „T-83 ist erledigt, push es und starte
T-82“. Codex hat Runde 2 technisch freigegeben (`2690819`), Claude hat lokal
nach `master` gemergt (`7d7583a`). Mike bestätigte den Abschluss auf die
Übergabe hin, die Abnahme und rechtliche Freigabe des Wortlauts (Verify #4)
als offene Punkte nannte. `master` ist auf Mikes Anweisung gepusht.

### Verifier-Prüfung · Runde 1 (Codex, 2026-10-01)

**Ergebnis: `changes_requested`.** Prüfgegenstand war `4acdc02` gegen
`0bb9a4d`. Der verhaltensneutrale Review-Commit `606aa16` ergänzt nur die
Funktionsdokumentation des Browser-Prüfskripts. Produktcode, Katalogtexte,
Assertions und Testdaten wurden im Review nicht geändert.

**Blocker B1 · Browser-Prüfskript startet ohne ausdrücklichen Befehl.**
`_tickets/30-doing/T-83-browser.mjs:21` setzt ohne Argument eine Ziel-URL;
der Ablauf ab Zeile 67 startet dann Chromium und schreibt Screenshots.
`--help` wird an derselben Stelle als URL behandelt. Das widerspricht
`code-standards/references/cli.md` („Kein stilles Loslegen — --help bei
keiner Option“ und Kurz-/Langform für Optionen). Auch der dort verlangte
dokumentierte Header-Block fehlt. Der Coder ergänzt Hilfe bei leerem Aufruf
und `-h|--help`, eine ausdrückliche Aktion wie `-r|--run [URL]`, den Header
und zieht die Verwendung im Ticket nach. Danach sind
`node --check`, der betroffene Browserlauf und der Doku-Abgleich erneut
auszuführen. Diese Änderung betrifft das Skriptverhalten und ist deshalb
keine Verifier-Selbstheilung.

**Unabhängige Nachweise:**

- Verify #1/#2: Mit StockPortfolios isoliertem StockInfo-Testserver
  (temporäre Datenbank, 14 Assets) und dem Dashboard unter 1440 × 900 und
  390 × 844 gemessen. Jeweils ein Hinweis nach `.scroll` beziehungsweise
  `.cards`, 4 px Abstand, innerhalb der Karte, 12 px Schrift, 17,4 px
  Zeilenhöhe, keine horizontale Überbreite. Die Ausschnitte wurden angesehen.
  Der Stil stimmt mit StockPortfolios `TradeNotice.vue` überein; `$color-muted`
  ist ein Alias für `token(--text-muted)`.
- Verify #3: Browserlauf auf derselben Seite zeigte DE → EN → DE ohne
  Neuladen; der Komponententest prüft die reaktive Übersetzung ebenfalls.
  Der Browserlauf ändert die i18n-Instanz direkt und belegt damit die
  Aktualisierung des Textes, keinen Klickweg durch die Einstellungen.
- Verify #4 bleibt ◑: `about.data`, `about.use`, `about.legal` und
  `LICENSING.md` wurden auf Aussagen zu Datenqualität und gesetzlichen
  Ansprüchen abgeglichen. Eine rechtliche Freigabe wird nicht erteilt.
- Verify #5: `make test-dashboard` mit Lint und 389/389 Tests,
  `npm --prefix dashboard run build`, Docker-Hub-Vorschau (7.940 Bytes)
  und `git diff --check 0bb9a4d 4acdc02` bestanden. Der Browserlauf
  nach `606aa16` lieferte dieselben Werte. Die eigenen Testserver wurden
  beendet. Ein TypeScript-Compiler-API-Inventar der berührten TS-/Vue-/JS-
  Dateien fand keine deutschen Bezeichner.

**Umfang:** Der tatsächliche Diff `0bb9a4d..4acdc02` enthält 11 Dateien,
273 Einfügungen und 16 Löschungen; die OUTBOX nennt 312 Einfügungen. Das
ändert den Prüfgegenstand nicht, ist aber bei der Nacharbeit zu berichtigen.
Die zusätzliche `playwright-core`-Abhängigkeit ist durch Mikes ausdrückliche
Vorgabe gedeckt. Browser-Skript und drei README-Sätze sind im Ticket erklärt.

**Code-Standards:** Gelesen:
`/Users/macminipro/.codex/skills/code-standards/SKILL.md`, Referenzen
`architecture.md`, `frontend.md`, `quality.md`, `cli.md` und
`documentation.md` sowie `ux-standards/SKILL.md` mit `styles.md` und
`responsive.md`. Architektur ✅: reine Darstellung in der vorhandenen
Komponente. Shell ➖, Python ➖, Persistenz ➖: nicht berührt. CLI ⚠️ 1 Befund
(B1). Frontend/i18n ✅: DE/EN-Katalogschlüssel, reaktiver Text, Token-Stil.
Qualität/Tests ✅: Leerfall, Platzierung, Sprache und negativer `v-if`-Mutant;
eigene Testläufe oben. Dokumentation ✅ für den geprüften Produktstand;
die Skriptverwendung muss nach B1 nachgezogen werden. DRY ✅: keine neue
fachliche Hilfslogik; die eigenständig lesbaren Hinweise in About und Assets
teilen einen Satz bewusst. Die repoübergreifende Wiederholung des
Hinweisstils ist im Ticket als Bedarf für ux-foundation sichtbar und nicht
Teil dieses StockInfo-Auftrags.

**Selbstheilung:** `606aa16` ergänzt an `measureNotice` und `switchLocale`
JSDoc mit Zweck, Parametern und Rückgabewert. Nur diese zwei Fundstellen
wurden geändert; `node --check`, `git diff --check` und beide Browserbreiten
wurden danach erneut geprüft. Es gab keine Änderung an Produktdateien.

**Doku-Abgleich:** `README.md` (Dashboard → Assets), `docker/README.md`
(What you get) und `unraid/README.md` (About) nennen den neuen Hinweis
übereinstimmend. `LICENSING.md` und About bleiben unverändert; die
öffentliche Rechtsfreigabe bleibt offen. Die Nacharbeit an der
Skriptbedienung betrifft dieses Ticket und den Skriptheader, nicht die
Produktanleitungen. SI-P-01, SI-P-02, SI-P-04, SI-P-08 und SI-P-13 wurden
gegen Testtiefe, Umfang und Standardgewicht geprüft. B1 ist ein konkreter
Standardverstoß; ein neuer allgemeiner Lesson-Eintrag ist daraus nicht
belegt.

### Verifier-Prüfung · Runde 2 (Codex, 2026-10-01)

**Ergebnis: technisch `approved`.** Geprüft wurde Claudes Übergabe `acf9dd9`
gegen den Rückgabestand `c1f6bf2`, der Gesamtstand gegen `0bb9a4d`.
Der abschließende, verhaltensneutrale Review-Commit `2690819` ergänzt
ausschließlich JSDoc in zwei Testdateien. Produktcode, Test-Assertions,
Fixtures und öffentliche Texte blieben im Review unverändert. Die rechtliche
Freigabe des endgültigen Wortlauts bleibt bei Mike; Verify #4 bleibt deshalb
◑ und die Human-Spalte unangetastet.

**B1 behoben:** Das Browser-Prüfskript zeigt bei leerem Aufruf sowie `-h`
und `--help` die Hilfe mit Exit 0. Nur `-r|--run [URL]` startet die Messung;
ein unbekanntes Argument endet nach Fehlermeldung und Hilfe mit Exit 2.
Header und Ticketaufruf stimmen damit mit `cli.md` überein. Der falsche
Umfangswert aus Runde 1 ist auf 11 Dateien, +273/−16 berichtigt; der
Gesamtstand `0bb9a4d..acf9dd9` umfasst ohne STATUS 12 Dateien, +461/−20.

**Mikes Lagebefund behoben:** Die Komponente setzt `.table-notice` als
direkten Geschwisterknoten nach `.table.card`. Der Lage-Test unterscheidet
dies von einem Hinweis innerhalb der Karte. Der unabhängige Browserlauf mit
echter API, temporärer Datenbank und 14 Test-Assets misst bei 1440 und 390 px
jeweils genau einen Hinweis: direkter Nachfolger der Karte, nicht darin,
4 px darunter, links 0 px Versatz, gleiche Breite, 12 px Schrift und keine
horizontale Überbreite. Die Screenshots wurden angesehen. DE → EN → DE
wechselt den Text ohne Seitenreload. Der Leerfall wird im Komponententest
abgedeckt. Die Gegenprobe gegen den alten Stand und der Lage-Mutant röteten
die entscheidenden Tests, wie in den Belegen oben beschrieben.

**Unabhängige Prüfungen:** `make test-dashboard` bestand mit Lint sowie
52 Testdateien und 389 Tests; `npm --prefix dashboard run build` bestand
einschließlich `vue-tsc`. `node --check`, alle CLI-Fälle und
`git diff --check c1f6bf2 acf9dd9` bestanden. Nach `2690819` bestanden
erneut der direkt betroffene Komponententest (34/34), Dashboard-Lint,
`node --check`, `git diff --check` und der Browser-Smoke mit beiden Breiten
und Sprachwechsel. Die isolierten Testserver wurden gestoppt. Das
TypeScript-Compiler-API-Inventar der geänderten Vue-/TS-/JS-Dateien fand
keine deutschen Bezeichner.

**Code-Standards:** Gelesen wurden
`/Users/macminipro/.codex/skills/code-standards/SKILL.md` mit
`architecture.md`, `frontend.md`, `quality.md`, `cli.md` und
`documentation.md` sowie `ux-standards/SKILL.md` mit `styles.md` und
`responsive.md`. Architektur ✅ vorhandene Darstellungskomponenten;
Shell ➖, Python ➖, Persistenz ➖ nicht berührt; CLI ✅ expliziter Start,
Hilfe, Header und Fehlerstatus; Frontend/i18n ✅ gemeinsamer Hinweis für
beide Breiten, reaktiver Katalogtext und Token-Stil; Qualität/Tests ✅
Leerfall, Lage, Sprache, Gegenprobe und Browser; Dokumentation ✅ wie unten.
DRY ✅: Der Diff und der berührte Umgebungscode führen keine zweite
fachliche Regel oder Hilfsfunktion ein. Der selbständig lesbare Satz in
About und Assets ist als bewusste Textwiederholung im Scope begründet;
der gemeinsame Breitenwert bleibt an einem Selektor. Die repoübergreifende
Stilwiederholung zu StockPortfolio ist als möglicher ux-foundation-Bedarf
erfasst und ändert diese Freigabe nicht.

**Selbstheilung und Doku-Abgleich:** `2690819` ergänzt nur Parameter- und
Rückgabebeschreibungen der Testhelfer; der vollständige Diff und die
betroffenen Tests, statischen Checks und Smokes wurden danach erneut
geprüft. `README.md` (Assets), `docker/README.md` (What you get) und
`unraid/README.md` (About) beschreiben denselben Platz und Zweck des
Hinweises. About und `LICENSING.md` widersprechen dem vorgeschlagenen
Wortlaut technisch nicht. Die Docker-Hub-Vorschau lag bei 7.940 UTF-8-Bytes
und damit unter der Grenze. Eine menschliche Wortlaut- oder Ticketabnahme
ist mit diesem Review nicht erfolgt.
