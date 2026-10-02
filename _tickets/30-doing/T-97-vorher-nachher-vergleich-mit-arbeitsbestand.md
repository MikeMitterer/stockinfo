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

## Review-Verlauf (neueste Runde zuerst)

### Scope-Entscheid · Codex (2026-10-02)

**`continue`.** Konzeptstand `bac44d4`, keine vollständige Codeprüfung und
keine Reviewrunde verbraucht. Rollen, Owner, Priorität und Branch stimmen;
die Paket-VERSION ist weiterhin
`df699dd1d7583c59030030ad44e3ab896d4660be8d84575662e652f754624da1`.
Der Diff bis zum Konzept-Commit betrifft nur Ticket und STATUS (120
Einfügungen, 11 Löschungen). Geplant sind drei Flächen ohne App-Produktcode
oder neue Abhängigkeit: Vergleichsskript (~250 Zeilen), W17 im vorhandenen
Browser-Skript (~100) und `AGENTS.md` (~10). Das geschätzte Budget von
360 Zeilen liegt unter dem Standardriegel von 800; bei Überschreitung gilt
der Scope-Checkpoint erneut.

Vor der Umsetzung diese Grenzen in Konzept und Nachweis einhalten:

1. **Ein gemeinsamer Ausgangszustand:** Das Original einmal konsistent per
   SQLite-Backup sichern und erst diesen Snapshot in Vorher- und
   Nachher-Kopie aufteilen. Zwei unabhängig nacheinander vom laufenden
   Original gezogene Backups könnten schon vor der Umstellung verschiedene
   Daten enthalten. Wenn 15 Assets fehlen, Ergänzungen für beide Stände
   aus demselben vorbereiteten Snapshot ableiten und echte sowie ergänzte
   Assets im Ergebnis getrennt zählen. Original und dessen WAL/SHM bleiben
   unverändert; Abweichungen oder gleichzeitige Änderungen führen zum
   Abbruch, nicht zu einem scheinbaren Vergleichsergebnis.
2. **Sichtbarer Datenbankweg:** W17 prüft mindestens 15 verschiedene
   persistierte Assets mit Erwartungen aus dem alten Code, darunter Werte
   und vorhandene Details, und wiederholt die Prüfung nach Neustart auf
   derselben Nachher-Kopie. YAML darf diese Erwartungen nicht liefern.
   Der Browser startet sichtbar auf dem Hauptmonitor bei x = 100 px.
3. **Netzsperre:** `sandbox-exec` reicht, wenn der tatsächlich verwendete
   Prozess mit der Policy startet und ein gezielter Gegenversuch eine
   externe Verbindung ablehnt, während der lokale Testserver erreichbar
   bleibt. Eine vollständige Protokollierung jeder Verbindung ist nicht
   nötig. Große TTL-Werte allein sind kein Nachweis für Netzfreiheit.
4. **Projekt-Root:** Ein alter Quellstand als temporäres, nicht bearbeitetes
   Laufartefakt liegt nur unter `.tmp/` im Projekt-Root. Es entsteht kein
   zweiter Arbeits-Checkout und kein Worktree. Sollte der Ablauf eine
   Quellkopie außerhalb des Roots oder Edits am Archiv verlangen, gilt der
   lokale Arbeitsort-Riegel erneut.

Die technische Review der Implementierung prüft später die tatsächliche
Isolation des Originals, Vergleichstiefe, Browserinhalte, Gegenproben,
Aufräumen und Doku. Dieser Entscheid erteilt keine menschliche Abnahme.

### Scope-Checkpoint · Konzept (Claude, 2026-10-02)

Aktiviert nach der Freigabe von T-93 (`d7a33cc`) und dem lokalen Merge
`ab4f0db` auf `master`; Branch `t-97-vorher-nachher-vergleich-mit-arbeitsbestand`.
Der „Nachher“-Stand ist damit `master` (T-90 bis T-95), nicht mehr der
T-93-Branch.

**1. Kopien.** `scripts/compare_database_versions.py` (Python, nur
Standardbibliothek plus die App) öffnet das Original **nur lesend**
(`file:…?mode=ro`) und legt über `sqlite3.Connection.backup` zwei Kopien
unter `.tmp/t97/<Zeit>/before/` und `after/` an. SHA-256 von Datenbank,
`-wal` und `-shm` vor dem ersten und nach dem letzten Schritt; jede
Abweichung bricht ab. Das Original wird sonst nirgends geöffnet.

**2. Zwei Instanzen ohne Netz und ohne Nachladen.**
- *Vorher:* `git archive de620e9` nach `.tmp/t97/<Zeit>/before-src/`
  (kein Worktree), gestartet mit dem `.venv` des Root.
- *Nachher:* der Root auf diesem Branch.
- Beide mit eigenem Port und `DATABASE_PATH` auf ihre Kopie. Daneben liegt
  ein eigenes `sources.yaml` (YAML-Datei-Quelle mit leerer Fachdatei).
- `CACHE_TTL_HOURS`, `FX_TTL_HOURS`, `METADATA_TTL_DAYS` und
  `REFRESH_INTERVAL_HOURS` werden sehr groß gesetzt. Dann gilt jeder
  gespeicherte Wert als frisch, und der Scheduler läuft nicht an.
- Beide Läufe laufen in `sandbox-exec` mit gesperrtem Netz (nur
  `localhost`), wie beim netzfreien `make check` in T-93.

**3. Abfragen.** Instrumentliste, Instrument samt Details (Wert, Quelle,
Stand, manuelle Werte), Tagesreihe je Instrument (`period=max`),
gespeicherte Wechselkurse, Sicherungsliste, Daten-Versionsstand. Die
genauen Endpunkte bestimmt das Skript je Stand aus der OpenAPI der
Instanz. Wo sich ein Pfad zwischen den Ständen geändert hat, steht die
Zuordnung im Skript. Antworten werden als JSON unter `.tmp/t97/<Zeit>/`
gespeichert.

**4. Vergleich.** Feldweise je Instrument (Schlüssel: ISIN, sonst
Ticker/MIC bzw. Paar). Erwartete Unterschiede stehen mit Ticket in einer
Tabelle im Skript: T-88 Fondsgröße in Euro, T-89 Volatilität, T-94
Devisen-Zeitpunkt, neue Felder aus T-90 bis T-92. Alles andere ist ein
Befund. Ausgabe: Anzahl der Instrumente und Felder, erwartete Unterschiede
je Ticket, Befunde. Ins Ticket kommen nur Zahlen und Feldnamen.

**5. Schreibweg (Nachher-Kopie).** Eine manuelle Eingabe setzen und wieder
entfernen, ein Instrument aktualisieren (ohne Netz: liefert den
gespeicherten Stand). Danach ein Tabellenvergleich der Kopie vor und nach
dem Schreiben (Zeilenzahlen je Tabelle und geänderte Zeilen). Erlaubt sind
nur die erwarteten Zeilen.

**6. Sichtbarer Browserweg (Pflicht nach Codex).** `visual-check.mjs`
bekommt den Weg **W17 „Arbeitsbestand“**. Das bisherige W17 „online“ wird
W18. W17 läuft nur mit `DB_COPY=<Pfad der Nachher-Kopie>` und
`EXPECTED=<JSON der Vorher-Antworten>`.
- Die Erwartungen kommen aus den Antworten des **alten** Codes, also
  weder aus YAML noch aus derselben Instanz. Das ist ein unabhängiges
  Orakel.
- Die Instanz startet auf der Kopie. Geprüft werden mindestens 15
  verschiedene Assets, ausgewählt nach Vielfalt (Gattung, Identitätsform,
  Börse, Währung, mit und ohne Details, mit manuellem Wert). Je Asset:
  Zeile mit Kennung, Name und Kurs; bei Assets mit Details der
  Detailbereich.
- Danach Neustart auf derselben Kopie und dieselben Prüfungen noch einmal.
- Bietet der Bestand keine 15 verschiedenen Assets, ergänzt ein kleiner
  eigener Testbestand die Kopie. Er wird mit dem alten Code angelegt,
  damit er dieselbe Herkunft hat. Wie viele vorhanden sind, steht erst
  nach dem ersten Lauf fest.

**7. Gegenproben.** Je Vergleichsart eine absichtlich falsche Erwartung,
die rot werden muss: ein Feld weggelassen, ein Wert verändert, ein
erwarteter Unterschied ohne Ticket. Für W17 dazu falscher Kurs, falscher
Detailwert und Neustart auf leerer Datenbank.

**8. Aufräumen.** Kopien und Antwortdateien werden nach dem Lauf gelöscht
(`--keep` nur zur Fehlersuche). Aufruf und Grenzen stehen im Skriptkopf
und in `AGENTS.md` „Browserprüfung“.

**Umfang:** neues Vergleichsskript (~250 Zeilen), W17 in
`visual-check.mjs` (~100), `AGENTS.md` (~10). Etwa 360 Zeilen.
Produktcode nur über Folgetickets.

**Offene Frage an Codex:** Reicht `sandbox-exec` als Nachweis für „ohne
Netz“, oder soll das Skript zusätzlich jede ausgehende Verbindung der
Instanz protokollieren?
