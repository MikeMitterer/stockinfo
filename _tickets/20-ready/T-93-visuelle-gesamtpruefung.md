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
ich den Teil ab“). Folgt nach T-92; Rollen und Aktivierung legt
`STATUS.md` fest. Für Mike steht kein Handgriff an.

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
