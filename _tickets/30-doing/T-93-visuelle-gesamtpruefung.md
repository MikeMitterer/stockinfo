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
| `make check` | `make test` (Backend, Plugin-API, Beispiel-Plugin, Dashboard-ESLint und Vitest), dazu `ruff check app tests scripts` und die Typprüfung des Dashboards (`vue-tsc -b`) |
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
  (alle fünf Rollen `yaml-file`), Fachdaten aus
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

- keine Konsolenfehler im Browser;
- keine Antwort `5xx`; `4xx` nur dort, wo der Weg sie erwartet;
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
| W7 | Aktualisieren | Zeile und „Alle aktualisieren“ ohne Fehler, Stand ändert sich |
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

- [ ] Ein dokumentierter Befehl führt die Kommandozeilen-Suiten aus.
- [ ] Ein dokumentierter Befehl führt den Browser-Durchlauf aus und meldet
      je Weg bestanden oder nicht bestanden.
- [ ] Alle Wege bestehen auf dem Stand nach T-92.
- [ ] Die Anleitung (README) nennt beide Befehle.

### Side-Effects

Keine Änderung an API, Vertrag oder Verhalten der App.
