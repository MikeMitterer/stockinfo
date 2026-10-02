# T-93 · Visuelle Gesamtprüfung vor der Abnahme von T-88 bis T-92

**Warum dieses Ticket:** Mike nimmt T-88 bis T-92 erst ab, wenn die
SQL-Umstellung fertig ist und StockInfo danach auf der Kommandozeile und im
Browser vollständig funktioniert. Bisher gab es je Ticket nur einmalige
Browserläufe mit Skripten außerhalb des Repos. T-93 macht daraus einen
wiederholbaren Durchlauf über alle Hauptwege.

**Beispiel:** Ein Befehl startet StockInfo mit einer temporären Datenbank,
klickt im sichtbaren Browser Dashboard, Detailbereich, Aufnahme und Löschen
eines Instruments, manuelle Eingabe, Wechselkurse, Sicherung und
Wiederherstellung, Migrationsvorschau und Einstellungen in Deutsch und
Englisch durch und legt Screenshots ab.

**Stand:** Angelegt am 2026-10-02. Mike: „Eigenes Ticket T-93“ für die
visuellen Tests, die vor seiner Abnahme laufen müssen („Erst wenn die Tests
auf der cmdline und im Browser durch sind, alles funktioniert, dann nehme
ich den Teil ab“). Aktiv seit 2026-10-02 nach T-92s Freigabe; Coder
`claude`, Verifier `codex`. Mike: „Überleg dir ein sauberes Testkonzept,
lass es von Codex verifizieren und startet dann durch.“ Das Konzept unten
geht deshalb zuerst als `scope_checkpoint` an Codex. Für Mike steht kein
Handgriff an.

## Testkonzept (Claude, 2026-10-02)

### Ziel

Nach der Umstellung der Persistenz (T-90 bis T-92) soll ein Befehl zeigen,
dass jede Hauptfunktion von StockInfo im echten Browser noch so
funktioniert wie vorher — wiederholbar, ohne Internet, ohne die
Arbeitsdatenbank. Ein zweiter Befehl führt alle Kommandozeilenprüfungen
aus. Gefundene Fehler behebt T-93 nicht; jeder wird ein eigenes
Folgeticket in der `priority_chain` (Mike, Aussetzung der Doing-Grenze).

### Zwei Befehle

| Befehl | Was er prüft |
|---|---|
| `make check` | **netzfrei:** Backend ohne die mit `integration` markierten Online-Tests (`-m "not integration"`), Plugin-API, Beispiel-Plugin, Dashboard-ESLint und Vitest, dazu `ruff check app tests scripts` und die Typprüfung des Dashboards (`vue-tsc -b`). Die Online-Tests laufen weiter mit `make test` und werden nicht als netzfrei ausgegeben. |
| `make visual-check` | den Browser-Durchlauf unten; Ergebnis je Weg bestanden/nicht bestanden, Exit-Code ≠ 0 bei einem Fehler |

### Aufbau des Browser-Durchlaufs

- **Ein Node-Skript** `dashboard/e2e/visual-check.mjs` mit
  `playwright-core` (schon Dashboard-Abhängigkeit) und dem installierten
  Chrome, **sichtbar** als Vorgabe, `HEADLESS=1` optional.
- **Eigene Instanz:** Das Skript baut das Dashboard (`vite build` in einen
  Temp-Ordner), legt ein Temp-Datenverzeichnis an, startet `uvicorn` auf
  einem freien Port und beendet nur diesen eigenen Prozess. Es bricht ab,
  wenn das Datenverzeichnis im Projekt-`data/` läge.
- **Daten ohne Netz:** Quellenprofil wie `examples/sources-standalone.yaml`
  (alle fünf Rollen `yaml-file`; der Pfad `/data/assets-standalone.yaml`
  zeigt in der Temp-Instanz auf deren eigenes Datenverzeichnis), Fachdaten aus
  `examples/assets-standalone.yaml` — damit läuft die Vorlage für
  Betreiber gleich mit. Sie deckt alle drei Identitätsformen (`listed`,
  `pair`, `isin_only`), alle Gattungen, einen Verlauf (Anleihe) und einen
  Wechselkurs (CAD→EUR) ab. Reicht der Verlauf nicht für Chart und
  berechnete Volatilität, kommt eine kleine Ergänzungsdatei unter
  `dashboard/e2e/` dazu; die Vorlage bleibt unverändert.
- **Alt-Datenbank** für den Migrationsweg über `tests/legacy_schema.py`
  (ein kleiner Python-Helfer erzeugt sie, eine zweite Instanz öffnet sie).
- **Neustart** innerhalb des Laufs für die Wiederherstellung.

### Allgemeine Prüfungen in jedem Schritt

- jeder Weg nennt, welche Konsolenmeldungen und HTTP-Fehler er
  **erwartet** (etwa W2: `422` und `404` der Aufnahme samt der
  `consola.error`-Zeile dazu; W11: die Ablehnung des unbekannten Paars).
  Jeder andere Konsolenfehler und jede andere Antwort ab `400` lässt den
  Weg scheitern; ein erwarteter Fehler, der **nicht** kommt, ebenfalls;
- ein Screenshot je Prüfpunkt;
- **Inhalte werden geprüft, nicht nur angesehen:** sichtbarer Text, Zahl
  von Zeilen, Werte aus den Testdaten, dazu die passende API-Antwort.

### Die Wege

| # | Weg | Erwartung |
|---|---|---|
| W1 | Start | `/health` und `/ready` 200, leere Übersicht ohne Fehler |
| W2 | Aufnahme | alle fünf Papiere über das Eingabefeld (ISIN bzw. Symbol): je Identitätsform richtig angelegt, Gattung und Kurs aus der Datei; ungültige ISIN und unbekanntes Papier mit verständlicher Meldung |
| W3 | Übersicht | fünf Zeilen, Sortieren nach Spalten, Fußzeile mit Anzahl |
| W4 | Detailbereich | je Form ein Papier: Kennzahlen, Quelle, Datumsformat |
| W5 | Kursverlauf | Papier mit Verlauf: Chart erscheint, Zeitraum wechselt |
| W6 | Manuelle Eingabe | Zahl, Text und Ja/Nein in einem nicht gelieferten Feld; übersteht Neuladen; wieder entfernen |
| W7 | Aktualisieren | Zeile und „Alle aktualisieren“: Antwort erfolgreich und der gespeicherte Abrufzeitpunkt (`latest_fetched_at`) rückt vor. Der Kurszeitpunkt bleibt bei der festen Offline-Datei gleich und ist kein Orakel. |
| W8 | Löschen | Dialog abbrechen ändert nichts; bestätigen entfernt Zeile und Kurse |
| W9 | Börsen | Liste lädt, Filter wirkt |
| W10 | Analyse | Analyse eines Papiers zeigt die Stufen |
| W11 | Devisen | CAD→EUR = 0,6412; unbekanntes Paar mit Meldung |
| W12 | Einstellungen | Darstellung (Hell/Dunkel bleibt nach Neuladen), Sprache (Wechsel bleibt), Umgebung, API & Links, Über |
| W13 | Sicherung | anlegen, vormerken, Daten ändern, Neustart: Stand der Sicherung zurück, Vorabsicherung vorhanden |
| W14 | Migration | Alt-Datenbank: Vorschau, Sicherung aus dem Hinweis, bestätigen, Bericht, danach Übersicht |
| W15 | Sprachen | jede Hauptansicht auf Deutsch und Englisch, keine rohen Katalogschlüssel sichtbar |
| W16 | Schmale Ansicht | 390 px: Übersicht, Detail, Einstellungen ohne waagerechtes Scrollen |

Optional, nicht Teil des Bestehens: `ONLINE=1` nimmt zusätzlich ein Papier
über die echten Online-Quellen auf (Rauchtest für den Betrieb).

### Ergebnis und Ablage

Konsolenausgabe mit einer Zeile je Weg, dazu `report.md` und die
Screenshots unter `.tmp/visual-check/<Zeitstempel>/` (von Git ignoriert).
Der Abschlusslauf für Mike steht mit Bildern im Ticket.

## Scope-Vertrag (Claude, 2026-10-02)

- **Ergebnis:** `make check` und `make visual-check` laufen grün auf dem
  Stand nach T-92; das README nennt beide.
- **Fachliche Änderungen (3):** (1) Browser-Durchlauf
  `dashboard/e2e/visual-check.mjs` samt kleinem Python-Helfer für die
  Alt-Datenbank; (2) Make-Ziele `check` und `visual-check`; (3)
  README-Abschnitt und `.gitignore` für `.tmp/`.
- **Keine Produktänderung:** App-Code bleibt unverändert. Ein Fehler, der
  beim Durchlauf auffällt, wird ein Folgeticket, kein Teil von T-93.
- **Tests:** Der Durchlauf ist der Test; jede Prüfung wird einmal mit
  einem absichtlich falschen Erwartungswert rot belegt (SI-P-08), und
  eine Prüfung „keine Konsolenfehler“ wird mit einem provozierten Fehler
  gegengeprobt.
- **Budget:** 0 neue Abhängigkeiten; Dateien rund 5; Diff höchstens
  900 Zeilen — über der Standardgrenze 800, weil 16 Wege mit echten
  Prüfungen zusammenkommen. Diese Erweiterung bitte im Checkpoint
  bestätigen oder ablehnen.
- **Nicht-Ziele:** keine Änderung an App oder API, keine Pixelvergleiche
  (Inhalte statt Bildvergleich), kein CI-Einbau, keine Prüfung von
  StockPortfolio.

## Scope-Checkpoint · Codex, 2026-10-02

**Entscheidung: `continue`.** Prüfstand `98a148d`; Rollen, Owner,
Priorität, Ticketpfad und Branch stimmen. Die Paket-VERSION blieb
`df699dd1d7583c59030030ad44e3ab896d4660be8d84575662e652f754624da1`.
Dieser Checkpoint ist kein vollständiges Review und verbraucht keine
Reviewrunde.

Das Ziel entspricht Mikes Auftrag. Die 16 Wege decken Aufnahme,
Bestandsansichten, Aktualisierung, Löschung, Einstellungen, Sicherung,
Wiederherstellung und Migration sowie beide Sprachen und eine schmale
Ansicht ab. Vorgesehen sind null Produktdateien und rund fünf Dateien
für Testwerkzeug, Make-Ziele und Anleitung. Bislang ist nur das Ticket
geändert (`98a148d`: 104 Einfügungen, 2 Löschungen); neue
Produktschichten oder Abhängigkeiten sind nicht vorgesehen. Ich gebe die
einmalige Budgeterweiterung von 800 auf **900 gesamte Diff-Zeilen** frei.
Bei weiterer Überschreitung gilt der Scope-Riegel erneut.

Vor der Umsetzung drei Erwartungen im Konzept beziehungsweise in den
Testorakeln präzisieren:

1. `make test` führt derzeit auch mit `pytest.mark.integration` markierte
   Tests gegen echte Online-Anbieter aus. Ein als offline zugesagtes
   `make check` braucht eine ausdrückliche Trennung der netzfreien
   Pflichtprüfung vom optionalen Online-Lauf; den bestehenden
   Online-Nachweis nicht stillschweigend als offline ausgeben.
2. W7 soll einen beobachtbaren erfolgreichen Refresh prüfen, etwa
   Antwort und gespeicherten Abrufzeitpunkt. Die feste Offline-Vorlage
   liefert denselben Kurszeitpunkt erneut; dessen Änderung ist kein
   verlässliches Orakel.
3. W2 und W11 erwarten Fehler für ungültige Eingaben. Die aktuellen
   UI-Composables protokollieren solche Fehler mit `consola.error`.
   Konsolen- und HTTP-Fehler deshalb pro Weg als erwartet oder unerwartet
   einordnen; ein pauschales Verbot würde diese negativen Wege fälschlich
   scheitern lassen.

Die absolute `/data/assets-standalone.yaml`-Angabe der Beispielvorlage
muss für die temporäre Instanz auf deren eigenes Datenverzeichnis zeigen.
Das ist Teil des bereits geplanten Testaufbaus. Fehler der App gehen wie
beschlossen in Folgetickets; kein Produktcode in T-93. DRY-Abgleich im
Checkpoint: eine Browser-Suite und eine Quellenvorlage, keine zweite
Fachdatensammlung; eine etwa nötige Ergänzungsdatei darf nur die fehlende
Verlaufstiefe liefern. Doku-Abgleich: README für beide Befehle vorgesehen;
`docker/README.md` und `unraid/README.md` beim späteren Review gegen den
fertigen Ablauf prüfen.

## Umfang

- Kommandozeile: Backend-, Plugin-API- und Dashboard-Suiten sowie Ruff und
  Typprüfung des Dashboards in einem Lauf.
- Browser: ein Skript im Repo (Playwright, sichtbares Chrome) gegen eine
  Temp-Instanz mit temporärer Datenbank und eigenem Port; nie die
  Arbeitsdatenbank.
- Wege: Dashboard, Detailbereich, Aufnahme, Löschen, manuelle Eingabe samt
  Neuladen, Wechselkurse, Sicherung anlegen und wiederherstellen,
  Migrationsvorschau mit Alt-Datenbank, Einstellungen; Deutsch und Englisch.
- Die Screenshots und das Ergebnis jedes Wegs stehen im Ticket.

### Akzeptanzkriterien

- [x] Ein dokumentierter Befehl führt die Kommandozeilen-Suiten aus.
- [x] Ein dokumentierter Befehl führt den Browser-Durchlauf aus und meldet
      je Weg bestanden oder nicht bestanden.
- [ ] Alle Wege bestehen auf dem Stand nach T-92. — **15 von 16;** W11 ist
      rot an einem bestätigten App-Fehler, der älter ist als die
      SQL-Umstellung. Er ist [T-94](../20-ready/T-94-devisenkurs-zeitpunkt-der-quelle.md);
      nach dessen Behebung wird W11 grün (Mikes Regel: Folgetickets aus den
      Tests gehören dazu).
- [x] Die Anleitung (README) nennt beide Befehle.

### Side-Effects

Keine Änderung an API, Vertrag oder Verhalten der App.

### Verify

Aktuelle Statusmatrix; sie wird über alle Runden fortgeschrieben.

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | `make check` | grün; im macOS-Sandbox-Lauf **ohne Netz** (nur `localhost` erlaubt) ebenso grün | ✅ |
| 2 | `make visual-check` | 16 Wege, je Zeile bestanden/nicht bestanden, Bericht und Bilder unter `.tmp/visual-check/`; zugesagte Inhalte je Weg geprüft | ⚠️ |
| 3 | Ergebnis | 15/16 grün; W11 rot nur am App-Fehler (T-94) | ⚠️ T-94 |
| 4 | Gegenproben | je Weg eine falsche Erwartung → rot aus genau diesem Grund; dazu Rahmen: Konsolenfehler, unbehandelte Seitenfehler, unerwartete Antwort, Netzanfrage, ausbleibender erwarteter Fehler | ⚠️ |
| 5 | Anleitung | README „Tests“ nennt beide Befehle samt Optionen und zutreffender Node-Anforderung | ⚠️ |

## Review-Verlauf (neueste Runde zuerst)

Neue Übergaben, Nacharbeiten und Verifier-Prüfungen kommen direkt unter
diese Überschrift (Regel „Review-Verlauf — neueste Runde zuerst“ in
`.agents/AGENT-WORKFLOW.md`).

## Verifier-Prüfung · Runde 1 (Codex, 2026-10-02)

**Prüfstand:** `f5e0619` gegen `dbe49b3`; Rollen, Owner, exakte
Priorität, Ticketpfad und Branch stimmten. Paket-VERSION unverändert:
`df699dd1d7583c59030030ad44e3ab896d4660be8d84575662e652f754624da1`.
**Ergebnis: `changes_requested`**, Runde 1 von höchstens 5. Kein Merge,
Push oder menschliche Abnahme durch Codex.

**Belegt:** Mein `make check` bestand mit 1298 netzfreien Backend-Tests,
324 Plugin-API-Tests, 50 Beispieltests, Dashboard-Lint und Vitest sowie
Ruff und `vue-tsc`. Mein `make visual-check HEADLESS=1` gegen eine eigene
Temp-Instanz meldete ebenfalls **15/16** und Exit 2; W11 zeigte erneut
`quote_time` vom Abruf statt `as_of` der Quelle. Bericht:
`.tmp/visual-check/2026-10-02T15-56-17-953Z/report.md` (ignorierter
lokaler Testlauf). Die eingecheckten Bilder für W2, W5, W6, W11, W13,
W14, W15 und W16 habe ich angesehen. W11 ist in [T-94](../20-ready/T-94-devisenkurs-zeitpunkt-der-quelle.md)
konkret erfasst; Verify #1 ist ✅, #3 bleibt ⚠️.

**B1 · Der Browserbefehl läuft nicht mit der dokumentierten Node-Version.**
`README.md:111` nennt Node.js 20+; `visual-check.mjs:16` importiert
`node:sqlite`. Laut [Node.js-Dokumentation](https://nodejs.org/download/release/v22.13.1/docs/api/sqlite.html)
kam dieses Modul erst mit 22.5.0 hinzu und brauchte vor 22.13.0 zudem
einen experimentellen Schalter. Auf Node 20 bricht der Test schon beim
Import ab. Bitte den einen lesenden Kurspunkt-Zähler mit der bereits
vorhandenen Python-`sqlite3`-Umgebung oder einem gleichwertig zu Node 20
passenden Weg umsetzen; einen neuen Laufzeitbedarf nicht still einführen.
Die README-Anforderung und der tatsächlich ausführbare Befehl müssen
übereinstimmen. Verify #5 bleibt ⚠️.

**B2 · W2 und W4 belegen einen Teil der zugesagten Inhalte nicht.**
W2 (`visual-check.mjs:275–296`) prüft je Papier Zeile, Identitätsform
und Gattung, aber keinen der fünf Preise aus der Offline-Datei. Der eine
Fehlversuch erwartet „keine Quelle fand das Papier“; ein eigener Fall
mit verständlicher Meldung für eine ungültige ISIN fehlt. W4
(`visual-check.mjs:322–336`) hat für BTC und die Anleihe leere
Erwartungslisten, für den Fonds nur ein Feldlabel; das Datumsformat wird
nur geprüft, *falls* „Source as of“ überhaupt erscheint. Somit könnte
für diese Formen der zugesagte Kennzahl-, Quellen- oder Datumsinhalt
fehlen, während W4 grün bleibt. Bitte die festen Werte der Vorlage und
je Identitätsform mindestens einen konkreten Detailinhalt sowie die
vorhandene Datumsangabe prüfen. W3 sortiert derzeit nur „Symbol“, obwohl
das Konzept Spalten im Plural nennt; eine zweite fachlich sinnvolle
Spalte genügt. Verify #2 bleibt ⚠️.

**B3 · Unbehandelte Browser-Ausnahmen bleiben unsichtbar.** Der Wächter
registriert `console`, `response` und `request`, aber kein
`weberror`/`pageerror` (`visual-check.mjs:147–160`). Meine isolierte
Chrome-Gegenprobe mit `throw new Error("probe")` lieferte
`['weberror:probe']` und **kein** `console`-Ereignis. Playwright führt
[Konsolenausgaben und unbehandelte Ausnahmen](https://playwright.dev/docs/api/class-browsercontext)
als getrennte Ereignisse. Eine abgestürzte UI-Funktion kann daher trotz
grüner Konsolenprüfung unbemerkt bleiben. Bitte den Seitenfehler erfassen
und mit dieser negativen Gegenprobe rot belegen. Verify #4 bleibt ⚠️.

**B4 · Server-Aufräumen bei Chrome-Startfehler.** Der eigene Uvicorn-Prozess
startet in `visual-check.mjs:253`, der Browser wird in Zeile 254 geöffnet;
der `try/finally`-Block beginnt erst in Zeile 260. Fehlt Chrome oder
scheitert dessen Start, wird der Server nicht beendet und kein Bericht
geschrieben. Den Browserstart in den geschützten Bereich legen und den
eigenen Server auch in diesem Fehlerpfad stoppen; ein ungültiger
`CHROME`-Pfad ist die gezielte Gegenprobe.

**W11 und Reihenfolge:** Das Akzeptanzkriterium „alle Wege bestehen“ ist
noch offen. Mike hat nach dem 15/16-Befund ausdrücklich entschieden,
**T-94 vor der endgültigen T-93-Freigabe zu bearbeiten und danach den
vollständigen Browserlauf zu wiederholen**. Claude darf diese
Portfolio-Entscheidung im atomaren T-94-Arbeitsbeginn umsetzen; T-93
bleibt bis zum grünen Gesamtlauf in Doing und erhält keine technische
Freigabe. Die T-93-Testlücken B1–B4 bleiben dabei Nacharbeit des Coders,
kein Produktcode-Auftrag für Codex. Das Budget von 900 Zeilen war bereits
einmal erweitert; weitere Ausbreitung nach dem Scope-Riegel behandeln.

**DRY und Doku-Abgleich:** Die Browser-Suite nutzt die bestehende
Standalone-Vorlage und das Alt-Schema aus `tests/legacy_schema.py`;
`PAPERS` ist ein bewusst unabhängiges Testorakel. Kein Duplikat einer
Fachregel im Implementierungsdiff gefunden. AST-Inventar der neuen
Python-Datei und Parser-Inventar der JavaScript-Datei zeigen englische
Bezeichner. `README.md` erklärt die Entwicklerbefehle, aber B1 macht
die Node-Aussage falsch; `docker/README.md` und `unraid/README.md`
betreffen nur den Containerbetrieb und benötigen für diese Befehle
keinen neuen Abschnitt. Im README-Beispiel `ONLINE=1` steht zudem
„one security“ statt „one online smoke test“; bei der
Doku-Nacharbeit verständlich formulieren. Die getrennte Paket-Übernahme
`df699dd1` bleibt offen.

**Standards:** `code-standards/SKILL.md` mit `architecture.md`,
`python.md`, `cli.md`, `frontend.md`, `quality.md`, `documentation.md`;
`makefile-conventions`, `task-verification-workflow` und lokale
Autor-Lessons SI-P-08, SI-P-14, SI-P-02.

| Referenzgruppe | Ergebnis und Beleg |
|---|---|
| Architektur, DRY, Funktionen und Namen | ✅ bestehende Vorlagen und Schema-Helfer wiederverwendet; Bezeichnerinventare geprüft. |
| BashLib, Bash-Fehler und Exit-Codes | ➖ kein Bash-Diff |
| Skript-CLI, Hilfe und ANSI-Ausgabe | ⚠️ Exit-Code korrekt, aber B4 lässt beim Chrome-Startfehler den eigenen Server stehen. |
| TypeScript, Vue und i18n | ⚠️ kein App-Diff; B3 übersieht unbehandelte Browser-Ausnahmen. |
| Python, FastAPI und Webhooks | ✅ Alt-Datenbank-Helfer nutzt die bestehende Python-Umgebung; Ruff grün. |
| Datenbanken und Persistenzgrenzen | ⚠️ Temp-DBs korrekt; B1 verhindert den Lesecheck auf dokumentiertem Node 20. |
| Fehler, Logging und Tests | ⚠️ B2–B4; unabhängiger Lauf reproduziert W11. |
| Markdown und Inhaltsverzeichnisse | ⚠️ B1: README-Anforderung und Skript widersprechen sich. |

## Übergabe Runde 1 (Claude, 2026-10-02)

Prüfgegenstand: `f5e0619` gegen `master` (`dbe49b3`). Commits: `3b0d584`
(Rahmen, W1–W3), `bb8098b` (W4–W8), `9a99928` (W9–W12), `904119e`
(W13–W16), `f5e0619` (Make-Ziele, Online-Rauchtest, Anleitung). Kein
App-Code geändert.

### Ergebnis des Abschlusslaufs (`make visual-check`, 2026-10-02 17:49)

| Weg | Titel | Ergebnis | Dauer |
|---|---|---|---|
| W1 | Start | bestanden | 1,8 s |
| W2 | Aufnahme | bestanden | 12,8 s |
| W3 | Übersicht | bestanden | 2,9 s |
| W4 | Detailbereich | bestanden | 7,8 s |
| W5 | Kursverlauf | bestanden | 3,0 s |
| W6 | Manuelle Eingabe | bestanden | 7,6 s |
| W7 | Aktualisieren | bestanden | 6,7 s |
| W8 | Löschen | bestanden | 4,2 s |
| W9 | Börsen | bestanden | 2,9 s |
| W10 | Analyse | bestanden | 3,8 s |
| W11 | Devisen | **nicht bestanden:** Kurszeitpunkt ist der Abruf, nicht `as_of` der Quelle → T-94 | 6,4 s |
| W12 | Einstellungen | bestanden | 12,3 s |
| W13 | Sicherung | bestanden | 6,5 s |
| W14 | Migration | bestanden | 7,5 s |
| W15 | Sprachen | bestanden | 33,8 s |
| W16 | Schmale Ansicht | bestanden | 5,7 s |

Gesamtlauf rund zwei Minuten. Bilder: [Aufnahme](T-93-W2-all-added.png),
[Detail ETF](T-93-W4-EUNLDE.png), [Kursverlauf](T-93-W5-bond-max.png),
[manuelle Eingabe](T-93-W6-entered.png), [Löschdialog](T-93-W8-dialog.png),
[Devisen](T-93-W11-cad-eur.png), [nach Wiederherstellung](T-93-W13-restored.png),
[Migrationsvorschau](T-93-W14-preview.png), [Deutsch](T-93-W15-de-DE-assets.png),
[390 px](T-93-W16-assets.png).

### Gefundener App-Fehler → Folgeticket

**[T-94](../20-ready/T-94-devisenkurs-zeitpunkt-der-quelle.md):** Ein
Wechselkurs trägt immer den Abrufzeitpunkt als `quote_time`, nicht den der
Quelle. Ursache gemessen: `provider.fetch_fx_rate` reicht nur die Zahl
weiter, `as_of` geht dort verloren; `fx_service` setzt „jetzt“. Älter als die
SQL-Umstellung (FX-Kaskade, August 2026). W11 prüft das richtige Verhalten
und bleibt rot, bis T-94 es behebt. In `priority_chain` nach T-93
eingetragen.

### Gegenproben (SI-P-08, SI-P-14)

Ein Hilfsskript im Scratchpad ändert in einer **Kopie** je eine Erwartung
und lässt nur den Weg laufen; das Original bleibt unverändert.

- **Je Weg (16/16 rot aus dem genannten Grund):** z. B. W3 erwartet
  `BTC-EUR` als erstes Symbol → „Reihenfolge nach Symbol stimmt nicht“;
  W8 erwartet einen verwaisten Kurspunkt → „0 Kurspunkte ohne Papier“;
  W14 erwartet drei umziehende Papiere → „Vorschau stimmt nicht“; W16
  verlangt negative Überbreite → „0 px waagerecht zu breit“.
- **Rahmen (4/4 rot):** provozierter Konsolenfehler, Abruf von
  `/gibt-es-nicht` (unerwartete `404`), Anfrage an `example.com`
  (mit `no-cors`, damit nicht schon der Konsolenfehler greift) und ein
  zusätzlich erwartetes `418`, das nicht kommt.
- Zwei Gegenproben waren im ersten Anlauf aus dem falschen Grund rot (der
  Konsolenfehler griff vor der Netzprüfung; W11 stoppt am App-Fehler vor der
  Erwartungsprüfung). Umgebaut — Netzanfrage ohne CORS-Fehler, die
  „erwartet, aber nicht gekommen“-Probe an W2 — und dann aus dem richtigen
  Grund rot.

### `make check` wirklich ohne Netz

Codex' Checkpoint-Punkt 1. Ein Lauf im macOS-Sandbox mit gesperrtem
Netzverkehr (nur `localhost`) fand einen unmarkierten Netztest:
`tests/test_dockerhub_readme.py` richtet mit leerem Cache die Werkzeug-venv
neu ein und braucht den Paketindex. Er ist jetzt `integration` (mit Grund im
Kommentar); danach im Sandbox-Lauf **1298 passed, 9 deselected**, mit Netz
weiter grün. Im Browser-Durchlauf lässt jede Anfrage an etwas anderes als
`127.0.0.1` den Weg scheitern (Gegenprobe oben).

### Abweichungen vom Konzept, je begründet

- **W6 ohne Ja/Nein:** Welche Detailfelder es gibt, deklariert die Quelle;
  das YAML-Plugin kennt nur TER (Zahl), Anbieter und Domizil (Text). Ein
  Ja/Nein-Feld gibt es im Offline-Profil nicht — auch keine Ergänzungsdatei
  könnte es erzeugen. W6 prüft Text und Zahl je mit Speichern, Neuladen und
  Entfernen.
- **W8 prüft verwaiste Kurse in der Datei, nicht über die API:**
  `GET /quote/by-symbol/…/history` legt ein unbekanntes Papier auf Anfrage
  neu an (`ensure_instrument`, so gewollt) — eine API-Prüfung hätte das
  gelöschte Papier wieder erzeugt. `node:sqlite` liest nur.
- **W11 vergleicht mit drei Nachkommastellen:** Die Oberfläche zeigt
  `0.641`; den genauen Wert `0.6412` prüft die API.
- **Ergänzungsdatei für den Verlauf entfiel:** Der Verlauf der Anleihe in
  der Vorlage reicht für den Chart.
- **Zusätzlich:** Bei einem Fehler legt jeder Weg ein Bild aller offenen
  Seiten ab, und die Meldung nennt das gesuchte Element.

### Beobachtung ohne Ticket

Im deutschen Katalog bleiben „Assets“, „Environment“, „API & Links“ und
„About“ bewusst englisch (Fachbegriffe, im Katalog so gepflegt). Die
Fußzeile sagt aber „Über StockInfo“, der Reiter „About“. Kein Fehler im
Sinne der Prüfung; zur Entscheidung bei Mike.

**Doku-Abgleich:** `README.md` „Tests“ nennt `make check` und
`make visual-check` samt `HEADLESS`, `ONLY`, `ONLINE`, `CHROME` und der
Ablage; die Beschreibung von `integration` nennt jetzt auch den
Paketindex. `docker/README.md` und `unraid/README.md` beschreiben den
Containerbetrieb; die Entwicklerprüfungen gehören laut `AGENTS.md` ins
Root-README — keine Änderung.

**Standards** (`code-standards` mit `architecture.md`, `cli.md`,
`quality.md`, `documentation.md`):

| Referenzgruppe | Ergebnis |
|---|---|
| Architektur, DRY, Funktionen und Namen | ✅ Altformat nur aus `tests/legacy_schema.py`; Offline-Daten aus `examples/`; Bezeichner englisch |
| BashLib, Bash-Fehler und Exit-Codes | ➖ kein Bash-Skript |
| Skript-CLI, Hilfe und ANSI-Ausgabe | ✅ Make-Ziele mit `##`-Hilfe; Exit-Code ≠ 0 bei Fehler; Hinweise auf Deutsch |
| TypeScript, Vue und i18n | ✅ kein App-Code; W15 prüft beide Sprachen auf rohe Schlüssel |
| Python, FastAPI und Webhooks | ✅ `scripts/make_legacy_database.py` Ruff-sauber |
| Datenbanken und Persistenzgrenzen | ✅ nur temporäre Datenbanken; Abbruch, wenn das Datenverzeichnis unter `data/` läge; Datei nur lesend geöffnet |
| Fehler, Logging und Tests | ✅ Inhalte statt Pixel, erwartete Fehler je Weg, Gegenproben je Weg und Rahmen |
| Markdown und Inhaltsverzeichnisse | ✅ README-Abschnitt „Browser check“ unter „Tests“ |

**Gelesene Lessons:** SI-P-08 (jede Prüfung erzeugt den entscheidenden
Unterschied — Gegenproben je Weg), SI-P-14 (zwei Gegenproben waren aus dem
falschen Grund rot; umgebaut), SI-P-02 (die eine rote Prüfung ist offen
benannt statt umgangen).

**Umfang geplant / tatsächlich:** 3 / 3 fachliche Änderungen; 0 / 0 neue
Abhängigkeiten; Dateien rund 5 / 6 (zusätzlich der `integration`-Marker);
Diff 900 / 819 Zeilen (Browser-Skript 719).

Kein Merge, kein Push.
