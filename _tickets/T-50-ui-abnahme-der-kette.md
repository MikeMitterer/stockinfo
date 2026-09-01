# T-50 · Browser-Abnahme von T-46, T-47 und T-48

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (laufender Stack) | aktiv | Konzept 1 h, Lauf 2–3 h | risikobasierte Browser-Abnahme der drei zuletzt freigegebenen Tickets | — |

- **Angelegt:** 2026-09-01, auf Mikes Auftrag: *„Schreib für das UI-Review von
  T-46, 47, 48 ein Ticket, lass das Codex reviewen und führe nach dem Review
  das Ticket aus."*
- **Hängt ab von:** T-46, T-47 und T-48 sind von Codex freigegeben
  (`e57ab4c`, `phase: portfolio_review`)
- **Reihenfolge:** vor Mikes eigener Abnahme. T-42 bleibt davon unberührt —
  dort geht es um die **Plugin-Kette**, hier um die drei neuen Flächen

**Löst:** Die drei Tickets sind gegen Tests und Gegenläufe geprüft, aber
`/analyze`, der Sicherungsbereich und die Wirkung einer geänderten Fachdatei
sind **Oberflächen**. Mike soll seine Abnahme nicht damit beginnen, dass er
Befunde findet, die ein Browserlauf vorher sichtbar gemacht hätte.

> **Anlass, gemessen vor diesem Ticket.** Ein erster Anlauf am isolierten
> Stack (eigene Ports, `VACUUM INTO`-Kopie der Datenbank) hat innerhalb von
> zehn Minuten einen Befund geliefert, den kein Test der drei Tickets sehen
> kann — siehe *Vorbefunde*. Genau dafür ist dieser Lauf da.

---

## Scope-Vertrag

### Phase A · Konzept, kein Browserlauf, keine Produktänderung

- Höchstens **9 sichtbare Fälle**. Jeder nennt Fläche, Eingabe, sichtbares
  Ergebnis und **den einen Fehler, den er unterscheidet**.
- Ein Fall zählt nur, wenn er etwas prüft, das die Suite **nicht** prüfen
  kann: Darstellung, Reihenfolge, Sperre, Formatierung, Erreichbarkeit.
  Alles, was ein `pytest` oder `vitest` bereits belegt, wird hier nicht
  wiederholt.
- Vor Codex' `approved` gibt es weder Browserlauf noch Produkt-Edit.

### Phase B · Browserlauf

- **Zwei isolierte Plugin-Varianten.** Eigene Ports (API `8123`, UI `5273`)
  und je Variante ein eigenes Scratch-Volume mit Datenbankkopie per
  `VACUUM INTO`, `sources.yaml` und Fachdatei unter dessen `/data`:
  `online/data/assets-fallback.yaml` für Online/YFinance mit `yaml-file` als
  letztem Fallback; `yaml/data/assets-standalone.yaml` für das reine
  YAML-Plugin. Die versionierten Vorlagen kommen aus `examples/`. Die beiden
  Varianten laufen nacheinander auf denselben isolierten Ports; ein
  Profilwechsel gilt nicht als T-48-Neustarttest.
- **Zwei Dateien sind fachlich notwendig.** Die Fallback-Datei enthält nur,
  was online keinen Kurs bekommt; die Standalone-Datei ist der vollständige
  Bestand. Eine gemeinsame Datei würde bei einem Online-Ausfall plausible
  alte Werte als Fallback zulassen und genau die Trennung aus T-49 aufheben.
  Mikes echtes `data/` wird nicht angefasst — der Lauf enthält
  Wiederherstellungen und Dateiänderungen, und die dürfen seinen Bestand
  nicht berühren.
- **Drei verbindliche Gattungen im isolierten Bestand:** `BTC-EUR` als
  `crypto`, `DE0001102531` als `bond` und `DE0009848119` als `fund`. Fehlen
  sie in der Datenbankkopie, werden sie vor dem Browserlauf über den
  öffentlichen Aufnahmeweg angelegt; keine direkte SQL-Testpräparation.
- **Belegpflicht.** Ein Screenshot allein belegt nichts. Zu jedem Fall gehört
  die sichtbare Anzeige **und** die Gegenprobe an der Quelle — Netzwerkantwort,
  Konsole oder Dateiinhalt. Ein Wert, der stimmt, weil er aus dem Cache kommt,
  ist kein bestandener T-48-Fall.
- **Wiederholung statt Momentaufnahme.** Eine Beobachtung während einer
  laufenden Animation ist keine Messung; siehe den Nicht-Befund unten.
- **Rückstandsfrei:** Nach dem Lauf werden die isolierten Prozesse beendet.
  Vorher/nachher-Prüfsummen der vom Benutzer verwendeten Datenbank und
  Konfigurationsdateien belegen, dass der Lauf ausschließlich im Scratchpad
  geschrieben hat.

### Fehlerbehandlung und Grenze

- Ein kleiner, eindeutig lokaler Anzeigefehler darf in diesem Ticket korrigiert
  werden — **höchstens drei Produktdateien**.
- Sobald REST-Vertrag, Schema, eine neue UI-Fläche, eine Abhängigkeit oder ein
  Statuscode betroffen ist, stoppt Claude **vor** dem Edit am
  Scope-Checkpoint. Das gilt ausdrücklich für den ersten Vorbefund unten.
- Keine neue Testinfrastruktur, kein E2E-Framework, keine Dauer-Skripte im
  Repo. Das Startskript bleibt im Scratchpad.
- Die Human-Spalte bleibt leer. Claude schreibt dort nie.

---

## Vorbefunde aus dem Anlauf

**V-1 · Das Migrationsgate sperrt die Sicherung aus, zu der es rät.**
Bei offener Identitätsmigration antwortet die App auf **jedem** Fachweg mit
`503 migration_pending` — gemessen für `/sources`, `/instruments`, `/analyze/…`,
`/env` und **auch `/backups` und `POST /backups`**. Der Gate-Bildschirm selbst
sagt:

> *„Der Umzug lässt sich nicht rückgängig machen. Legen Sie eine Kopie der
> Datenbankdatei an, bevor Sie bestätigen."*

Genau diese Kopie ist seit T-47 eine Schaltfläche — die hinter dem Gate liegt.
Der Benutzer wird also zu einer Handarbeit aufgefordert, für die das Produkt
ein Werkzeug hat, das er in diesem Moment nicht erreichen kann.

Das ist **kein Fehler von T-47**: Das Gate ist älter, und dass ein Schreibweg
vor einer offenen Migration gesperrt ist, ist vertretbar. Aber `GET /backups`
ist ein reiner Leseweg, und die Empfehlung im Gate ist seit T-47 überholt.
**Nicht Teil von T-50.** Die Änderung beträfe eine Gate-Regel oder eine neue
Handlung im Gate, nicht eine lokale Anzeige. Der Befund bleibt belegt und wird
nach Phase B in ein eigenes Ticket drainiert; dieser Lauf behebt ihn nicht.

**V-2 · Das Instrumentenfeld der Analyse ist im Ruhezustand leer.** Kein
Platzhalter, keine Beschriftung — ein leerer Rahmen über dem Feld „ISIN oder
Symbol". Zu prüfen als Fall 1; falls bestätigt, ist es eine reine
Anzeigekorrektur und fällt unter die Lockerung oben.

**Nicht-Befund · durchscheinende Auswahlliste.** Der erste Bildschirmabzug
zeigte die geöffnete Liste durchsichtig, mit übereinanderliegendem Text. Die
Wiederholungsmessung zeigt sie deckend: Der Abzug fiel in die Einblende-
Animation. **Wird nicht als Befund geführt** — und steht hier, damit er nicht
ein zweites Mal als einer gemeldet wird.

---

## Die Fälle

Legende der Spalte *Unterscheidet*: der eine Fehler, der ohne diesen Fall
unbemerkt bliebe.

### T-46 · `/analyze` misst die konfigurierte Kette

| # | Fläche und Eingabe | Sichtbar erwartet | Unterscheidet |
|---|---|---|---|
| **1** | Analyse-Seite im Ruhezustand | Beide Eingabefelder sind beschriftet oder tragen einen Platzhalter; die Auswahl listet den Bestand | V-2; ein Feld, dessen Zweck man raten muss |
| **2** | `BTC-EUR` (`crypto`) aus dem Bestand analysieren, Online-Profil | Die Stufen tragen die Namen aus `sources.yaml` (`yfinance`, `yaml-file`), **nicht** fest verdrahtete yfinance-Stufen | Die Analyse misst etwas anderes als das, was die App benutzt — und der Paar-Aufnahmeweg fehlt im sichtbaren Lauf |
| **3** | `DE0001102531` (`bond`) im **reinen Dateiprofil** analysieren | Dieselbe Seite zeigt `yaml-file` als Stufe; die Rollen sind unterscheidbar und das Papier braucht kein Börsensymbol | Eine Anzeige, die die Kette hart kennt oder `isin_only` still wie ein Listing behandelt |
| **4** | `STOCKINFO-NOT-FOUND` im Online-Profil analysieren | Der Ausfall einer Stufe bricht die Messung nicht ab; die Zeile nennt einen Grund statt leer zu bleiben | Die `_BROKEN`-Ersatzantworten aus T-46 — sichtbar, nicht nur im Test |

### T-47 · Sicherung und Wiederherstellung

| # | Fläche und Eingabe | Sichtbar erwartet | Unterscheidet |
|---|---|---|---|
| **5** | Sicherung anlegen, Liste danach | Die neue Sicherung erscheint **mit lesbarem Datum und Größe**; die Liste lädt nach Erfolg neu | Die leere Zeitspalte aus dem T-47-Lauf; ein Eigenstand, der von der Instanz abweicht |
| **6** | Eine unpassende Sicherung wiederherstellen wollen | Der Grund steht **als Satz** in der Zeile; im Dialog ist „Ja" gesperrt, bis das Kästchen gesetzt ist; der Neustart-Hinweis steht **vor** der Entscheidung | Eine Sperre, die erst der `409` aus dem Netz erklärt |
| **7** | Wiederherstellung bestätigen, App neu starten | Nach dem Start ist der gesicherte Stand da; die Zustandszeile ist wieder leer | Eine Absicht, die den Neustart nicht überlebt — oder ihn jedes Mal wiederholt |
| **8** | Oberfläche auf **Englisch** stellen, Fälle 5 und 6 erneut ansehen | Grund, Datum und Fehlermeldung sind englisch — keine deutschen Reste | Ein fertiger Satz vom Server; die Kennung aus T-44 wäre umsonst |

### T-48 · Geänderte Fachdatei ohne Neustart

| # | Fläche und Eingabe | Sichtbar erwartet | Unterscheidet |
|---|---|---|---|
| **9** | Bei laufender Online-/YFinance-Variante in `/data/assets-fallback.yaml` den jüngsten Historywert der Anleihe `DE0001102531` und bei laufender reiner YAML-Variante in `/data/assets-standalone.yaml` den Preis des Fonds `DE0009848119` ändern; jeweils die **sichtbare Einzel-Aktualisierung** auslösen | Der neue Wert steht danach in der Oberfläche, **ohne** Neustart der jeweiligen Variante; Dateiinhalt und Netzwerkantwort stimmen überein | Eine der beiden Plugin-Varianten liest die falsche/gleiche Basisdatei, oder ein Wert bliebe nach bloßem Neuladen in Datenbank, Cache oder altem Katalog hängen |

---

## Verify

Legende: ✅ live bestätigt · ⚠️ bestätigt mit Einschränkung · ◑ teilweise ·
➖ keine Live-Verifikation · `AI` nur KI · `Human` nur Mensch.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | Konzept-Handoff an Codex | höchstens 9 Fälle; jeder nennt Fläche, Eingabe, Erwartung und den unterschiedenen Fehler; nichts, was die Suite schon belegt | ◑ | |
| **2** | Isolation des Laufs | eigene Ports, eigene DB-Kopie, eigene Konfiguration; `data/` des Benutzers vor und nach dem Lauf unverändert | ➖ | |
| **3** | T-46 im Browser | Fälle 1–4 gemessen, jeder mit Gegenprobe an Netzwerk oder Konfiguration | ➖ | |
| **4** | T-47 im Browser | Fälle 5–8 gemessen, einschließlich Neustart und englischer Oberfläche | ➖ | |
| **5** | T-48 im Browser | Fall 9 in beiden Profilen, mit Dateiinhalt und Netzwerkantwort als Gegenprobe | ➖ | |
| **6** | Befunde | jeder Befund nennt Messung, Fundort und ob er in diesem Ticket behoben wurde oder checkpoint-pflichtig ist | ➖ | |
| **7** | Konsole und Netzwerk | keine unerklärte Fehlermeldung, kein fehlgeschlagener Request, der dem Angezeigten widerspricht | ➖ | |
| **8** | Regression nach etwaigen Korrekturen | `make test` und Ruff grün; ohne Korrektur entfällt die Zeile nicht, sondern wird als „keine Änderung" belegt | ➖ | |
| **9** | Mike-Handoff | die Fälle sind ohne Entwicklungswissen nachvollziehbar; Human-Spalte leer | ➖ | |

---

## Codex-Review Runde 1 · `changes_requested` (2026-09-01)

Das Konzept bleibt auf neun sichtbare Fälle begrenzt. Drei Korrekturen sind
vor dem Browserlauf nötig:

1. Der Gleichzeitigkeitstest für Sicherungen entfällt. Zwanzig parallele
   `POST /backups` sind bereits automatisiert belegt; zwei Klicks im Browser
   erzeugen den entscheidenden Zustand weder zuverlässig noch UI-spezifisch.
2. Mikes verbindliche Asset-Abnahme wird ohne neue Fälle eingebaut:
   `BTC-EUR` in die Online-Analyse, die Anleihe in Datei-Analyse und
   Online-Fallback, der Fonds in den Standalone-Hot-Reload.
3. Ein Reload der Seite beschafft absichtlich keinen Kurs. T-48 wird deshalb
   über die sichtbare Einzel-Aktualisierung geprüft; Dateiinhalt,
   Netzwerkantwort und UI-Wert müssen denselben neuen Wert tragen. Der Lauf
   verwendet dabei ausdrücklich zwei Fachdateien unter den isolierten
   Data-Verzeichnissen: `assets-fallback.yaml` für Online/YFinance plus YAML-
   Rückfall und `assets-standalone.yaml` für das reine YAML-Plugin.

V-1 gehört **nicht** in die Umsetzung dieses Tickets. Ob Backup-Routen vor
dem Migrationsgate offenstehen oder das Gate eine eigene Backup-Handlung
bekommt, ist eine Produktentscheidung über Gate und API. T-50 dokumentiert
den bereits gemessenen Befund und drainiert ihn nach Phase B in ein separates
Ticket; es ändert weder Gate noch Backup-Routen.

Vor der erneuten Übergabe nennt Phase B außerdem den öffentlichen
Vorbereitungsweg für die drei Assets und die Prüfsummen-Gegenprobe für Mikes
unberührte Daten. Danach kann das Konzept ohne weiteren Designentscheid in den
Browserlauf gehen.
