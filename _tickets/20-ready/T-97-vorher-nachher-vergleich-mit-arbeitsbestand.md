# T-97 · Vorher-nachher-Vergleich der SQL-Umstellung mit einer Kopie des Arbeitsbestands

**Warum dieses Ticket:** Die Browser-Gesamtprüfung aus T-93 startet mit einer
leeren Datenbank und fünf Beispielpapieren aus `examples/`. Sie zeigt, dass
die App mit neuen Daten funktioniert. Das eigentliche Risiko der
SQL-Umstellung (T-90 bis T-92) ist aber Mikes **vorhandener** Datenbestand:
über viele Versionen gewachsen, mit vielen Instrumenten, langen Verläufen,
manuellen Overrides und Sonderfällen, die keine Beispieldatei abbildet. Ob
diese Daten nach dem Umbau genauso gelesen und geschrieben werden, prüft
bisher kein Test.

**Beispiel:** Ein Instrument mit manuell überschriebener Fondsgröße liefert
vor T-90 `fund_size` = 1.234.000.000 EUR mit Quelle `manual`. Nach der
Umstellung muss dieselbe Abfrage auf derselben Datenbank denselben Wert und
dieselbe Quelle liefern.

**Stand:** Angelegt am 2026-10-02 auf Mikes Auftrag. Mike: „die visuellen
Tests werden mit dem YAML-File gemacht obwohl massive Änderungen bei dem
Datenbankzugriffen gemacht wurden … am aktuellen Grund vorbei“ und „Ja, leg
T-97 an und trag es ein“. Folgeticket der SQL-Umstellung in der
`priority_chain`; Mikes Abnahme von T-88 bis T-95 wartet auch auf T-97.

Für Mike steht vor der Umsetzung kein Handgriff an. Die Freigabe für die
Kopie des Arbeitsbestands ist erteilt (siehe Grenzen).

## Umsetzung und technische Nachweise

| Repo | Time-box | Scope | GH-Issue |
|---|---|---|---|
| StockInfo | 0,5–1 Tag | Vergleichsskript und Befundliste; Produktcode nur über Folgetickets | — |

### Kontext / Ziel

1. **Kopie:** Die Arbeitsdatenbank (`DATABASE_PATH`, im Entwicklerbetrieb
   `data/stockinfo.db`) wird zweimal in einen temporären Ordner kopiert —
   konsistent über die SQLite-Backup-Schnittstelle oder bei gestoppter App
   samt `-wal`/`-shm`. Das Original wird nie geöffnet, um darin zu schreiben.
2. **Vorher:** Den Stand vor der Umstellung starten, `master` vor T-90
   (`de620e9`, letzter Merge vor `21b5c84`), in einem temporären
   Arbeitsverzeichnis (kein Worktree im Root, siehe `AGENTS.md`), gegen die
   erste Kopie, eigener Port. Die wichtigsten API-Antworten speichern:
   Instrumentliste, Kurse, Details samt Quelle und Stand, Verläufe, manuelle
   Overrides, Wechselkurse, Sicherungsliste, Daten-Versionsstand.
3. **Nachher:** Den aktuellen Stand (T-93-Branch mit T-94/T-95) gegen die
   zweite Kopie starten und dieselben Abfragen stellen.
4. **Vergleich:** Antworten feldweise vergleichen. Unterschiede, die aus
   beauftragten Änderungen stammen (etwa Fondsgröße in Euro aus T-88,
   Volatilität aus T-89, Devisen-Zeitpunkt aus T-94), werden ausdrücklich
   als erwartet benannt; jeder andere Unterschied ist ein Befund.
5. **Schreibweg:** Auf der Nachher-Kopie zusätzlich einmal schreiben
   (manuelle Eingabe setzen und entfernen, Instrument aktualisieren) und
   prüfen, dass danach nur die erwarteten Zeilen geändert sind.
6. **Befunde:** Jeder echte Fehler wird ein eigenes Folgeticket in der
   `priority_chain`, wie bei T-93.

### Grenzen

- **Kopie ja, Original nie.** Mike erlaubt ausdrücklich eine Kopie des
  Arbeitsbestands in einem temporären Ordner für diesen Vergleich. Die
  Regel aus `AGENTS.md` („nie die Arbeitsdatenbank verwenden“) gilt für das
  Original unverändert; der Riegel in `tests/conftest.py` bleibt an.
- Die Kopien und gespeicherten Antworten enthalten Mikes echte Daten. Sie
  bleiben lokal unter `.tmp/` (von Git ignoriert) und werden nach dem
  Vergleich gelöscht. Ins Ticket kommen nur Zahlen und Feldnamen, keine
  vollständigen Datensätze.
- Keine Online-Quellen: Beide Läufe ohne Netzabruf, damit nur die
  Datenbank und nicht der Markt den Unterschied macht.

### Akzeptanzkriterien

- [ ] Vorher- und Nachher-Lauf laufen gegen je eine Kopie, das Original ist
      unverändert (Prüfsumme vor und nach dem Vergleich).
- [ ] Der Vergleich deckt die oben genannten Bereiche ab und nennt die Zahl
      der verglichenen Instrumente und Felder.
- [ ] Der sichtbare Datenbankweg prüft **mindestens 15 verschiedene
      Assets** (Mike, 2026-10-02: „Zwei Papiere sind mir zu wenig … ich denke
      da mindestens 15“): verschiedene Gattungen, Identitätsformen, Börsen
      und Währungen, mit und ohne Details. Reicht der Arbeitsbestand dafür
      nicht, wird er mit einem eigenen Testbestand ergänzt.
- [ ] Jeder Unterschied ist als erwartet (mit Ticket) oder als Befund
      eingeordnet; Befunde stehen als Folgetickets in der Kette.
- [ ] Der Schreibweg auf der Nachher-Kopie ändert nur die erwarteten Zeilen.
- [ ] Kopien und Antwortdateien sind nach dem Vergleich gelöscht.

### Side-Effects

Keine am Produkt. Ein Vergleichsskript im Repo, damit der Lauf vor späteren
Datenbank-Umbauten wiederholbar ist; Ablage und Aufruf in `AGENTS.md`,
Abschnitt „Browserprüfung“ oder einem eigenen Abschnitt, nicht im README.
