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
  YAML-Plugin. Die versionierten **Fachdaten**-Vorlagen kommen aus
  `examples/`. Die beiden Varianten laufen nacheinander auf denselben
  isolierten Ports; ein Profilwechsel gilt nicht als T-48-Neustarttest.
- **Die Ketten-Konfiguration hat nur eine Vorlage, und die liegt falsch.**
  Der Lauf kopiert `_tickets/T-37-sources-online-with-yaml-fallback.yaml` als
  `online/data/sources.yaml` und ändert in **dieser Scratch-Kopie** den
  Provider-Pfad von `/data/assets.yaml` auf
  `/data/assets-fallback.yaml`. Für das reine Dateiprofil existiert keine
  Vorlage im Repo; der Lauf schreibt `yaml/data/sources.yaml` im Scratchpad
  (fünf Rollen, überall nur `yaml-file`, Provider-Pfad
  `/data/assets-standalone.yaml`) und legt sie nicht ins Repo — siehe V-3.
- **Zwei Dateien sind fachlich notwendig.** Die Fallback-Datei enthält nur,
  was online keinen Kurs bekommt; die Standalone-Datei ist der vollständige
  Bestand. Eine gemeinsame Datei würde bei einem Online-Ausfall plausible
  alte Werte als Fallback zulassen und genau die Trennung aus T-49 aufheben.
  Mikes echtes `data/` wird nicht angefasst — der Lauf enthält
  Wiederherstellungen und Dateiänderungen, und die dürfen seinen Bestand
  nicht berühren.
- **Drei verbindliche Gattungen im isolierten Bestand:** `BTC-EUR` als
  `crypto`, `DE0001102531` als `bond` und `DE0009848119` als `fund`. Fehlen
  sie in der Datenbankkopie — und in der Kopie fehlen alle drei —, werden sie
  vor dem Browserlauf über das Feld „ISIN oder Symbol" über der Assets-Liste
  angelegt. **Das Feld ruft nicht `POST /instruments/intake`**, sondern
  `GET /quote/{isin}` bzw. `GET /quote?symbol={symbol}`
  (`useInstrumentActions.add` → `quotePath`); das Papier entsteht dabei
  nebenbei. Der Lauf nimmt bewusst diesen Weg, weil T-50 die **Oberfläche**
  abnimmt und ein Benutzer den Intake-Endpunkt nicht bedient. Keine direkte
  SQL-Präparation; wo das Feld ein Papier nicht annimmt, ist **das** der
  Befund und wird nicht umgangen.
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

**V-3 · Die Ketten-Konfiguration hat T-49 nicht mitgemacht.** Ein Inventar
aller YAML-Dateien im Repo — jede Datei mit einem Rollenschlüssel, nicht eine
Namenssuche — findet **genau ein** Quellenprofil, und es liegt in
`_tickets/T-37-sources-online-with-yaml-fallback.yaml`. Für das reine
Dateiprofil gibt es keines.

T-49 hat die **Fachdaten** aus dem Ticketverzeichnis geholt und zwei Vorlagen
unter `examples/` abgelegt. Die `sources.yaml` daneben ist genau dieselbe
Sorte Datei — versionierte Betriebsvorlage, kein Prüfmittel — und blieb
liegen. Zieht T-37 nach `solved/`, zieht die einzige Ketten-Vorlage mit; das
ist der Mechanismus, für den T-45 und T-49 zusammen angelegt wurden.

**Nicht Teil von T-50**, aus demselben Grund wie V-1: Er wird belegt und nach
Phase B gedrainiert. Der Lauf selbst schreibt seine beiden Profile im
Scratchpad.

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
| **1** | Konzept-Handoff an Codex | höchstens 9 Fälle; jeder nennt Fläche, Eingabe, Erwartung und den unterschiedenen Fehler; nichts, was die Suite schon belegt | ✅ | |
| **2** | Isolation des Laufs | eigene Ports, eigene DB-Kopie, eigene Konfiguration; `data/` des Benutzers vor und nach dem Lauf unverändert | ⚠️ [^rueckstand] | |
| **3** | T-46 im Browser | Fälle 1–4 gemessen, jeder mit Gegenprobe an Netzwerk oder Konfiguration | ✅ | |
| **4** | T-47 im Browser | Fälle 5–8 gemessen, einschließlich Neustart und englischer Oberfläche | ✅ | |
| **5** | T-48 im Browser | Fall 9 in beiden Profilen, mit Dateiinhalt und Netzwerkantwort als Gegenprobe | ✅ | |
| **6** | Befunde | jeder Befund nennt Messung, Fundort und ob er in diesem Ticket behoben wurde oder checkpoint-pflichtig ist | ✅ | |
| **7** | Konsole und Netzwerk | keine unerklärte Fehlermeldung, kein fehlgeschlagener Request, der dem Angezeigten widerspricht | ✅ | |
| **8** | Regression nach etwaigen Korrekturen | `make test` und Ruff grün; ohne Korrektur entfällt die Zeile nicht, sondern wird als „keine Änderung" belegt | ✅ | |
| **9** | Mike-Handoff | die Fälle sind ohne Entwicklungswissen nachvollziehbar; Human-Spalte leer | ✅ | |

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

## Runde 2 · Konzept nachgezogen (Claude, 2026-09-01)

Alle drei Korrekturen übernommen; die Fallzahl bleibt bei neun. Zwei Stellen
waren noch nicht ausführbar, und beide fielen erst auf, weil ich das Konzept
gegen die **tatsächlichen Dateien** gehalten habe statt gegen seine eigene
Beschreibung:

1. **Der Aufnahmeweg ist jetzt benannt und der Bedarf gemessen.** Die
   Datenbankkopie enthält fünf Papiere — `APC.DE`, `BRYN.DE`, `EUNL.DE`,
   `GOLD.SG`, `VGWL.DE`. **Keine** der drei verbindlichen Gattungen ist
   darunter; alle drei werden über das Feld „ISIN oder Symbol", also
   `POST /instruments`, angelegt. Nimmt der Weg ein Papier nicht an, ist das
   der Befund und wird nicht per SQL umgangen.
2. **„Die Vorlagen kommen aus `examples/`" stimmt nur für die Fachdaten.**
   Für die Rollenketten gibt es dort nichts. Das Inventar findet genau ein
   Quellenprofil im ganzen Repo, und es liegt im Ticketverzeichnis — V-3. Der
   Lauf schreibt das Standalone-Profil deshalb im Scratchpad.

**Gegenprobe zu den Gattungen, damit die Fälle nicht ins Leere zeigen:**
`assets-standalone.yaml` führt `bitcoin-eur` (`crypto`, `kind: pair`),
`german-bond` (`bond`, `isin_only`) und `active-fund` `DE0009848119` (`fund`,
mit `price`) — Fall 9 Standalone ist damit gedeckt.
`assets-fallback.yaml` führt **nur** `german-bond`, und zwar ohne `price`,
mit `history`. Genau darauf zielt Fall 9 Online; die Datei ist also passend
und muss für diesen Lauf nicht erweitert werden.

Kein Browserlauf, kein Produkt-Edit. V-1 und V-3 bleiben undrainiert bis nach
Phase B.

## Codex-Review Runde 2 · `changes_requested` (2026-09-01)

Die neun Fälle und die beiden Plugin-Varianten sind inhaltlich vollständig;
zwei konkrete Pfade waren noch nicht ausführbar:

1. Der öffentliche Aufnahmeweg ist `POST /instruments/intake`, nicht
   `POST /instruments` (`app/routers/instruments.py`).
2. Die einzige Online-Vorlage zeigt weiterhin auf `/data/assets.yaml`. Ihre
   Scratch-Kopie muss auf `/data/assets-fallback.yaml` zeigen; das neu
   geschriebene reine YAML-Profil auf `/data/assets-standalone.yaml`. Erst
   damit sind Mikes zwei Laufzeitdateien wirklich verdrahtet.

Keine neue Fallzeile, kein Produktedit und kein Browserlauf. Nach dieser
Pfadkorrektur ist Phase A freigabefähig; V-1 und V-3 bleiben dokumentierte
separate Drains nach Phase B.

## Runde 3 · Der Aufnahmeweg heißt anders, als beide ihn genannt haben (Claude, 2026-09-01)

Pfadkorrektur 2 übernommen — die Scratch-Kopien zeigen auf ihre jeweilige
Fachdatei; das Startskript setzt beide Pfade beim Kopieren.

**Pfadkorrektur 1 stimmt als Routenname und trifft trotzdem nicht.**
`POST /instruments/intake` existiert (`app/routers/instruments.py:42`) — mein
`POST /instruments` war falsch. Aber **das Feld ruft ihn nicht auf.** Der Weg
hinter „Hinzufügen" ist

```
useInstrumentActions.add → quotePath → GET /quote/{isin}
                                     bzw. GET /quote?symbol={symbol}
```

Das Papier entsteht dabei nebenbei; `intake` erscheint im ganzen
`dashboard/src/` **kein einziges Mal**. Für T-50 ist das nicht bloß eine
Formalie: Das Ticket nimmt die **Oberfläche** ab, und ein Benutzer bedient den
Intake-Endpunkt nicht. Wäre die Zeile so stehen geblieben, hätte der Lauf
einen Weg vorbereitet, den die geprüfte Fläche gar nicht geht — die
Vorbereitung wäre grün gewesen und hätte nichts über das Feld ausgesagt.

Nachgesehen habe ich das, weil derselbe Satz zwei Dinge gleichsetzte: die
sichtbare Fläche und eine Route. Solche Gleichsetzungen sind die Stelle, an
der eine der beiden Hälften ungeprüft mitläuft.

**Nebenbei geprüft, weil Fall 9 darauf steht:** Die sichtbare
Einzel-Aktualisierung ist `refreshOne` → `POST /refresh/{isin}` bzw.
`POST /refresh/by-symbol/{symbol}`. Sie existiert und ist vom bloßen Neuladen
unterscheidbar — Fall 9 ist ausführbar.

## Codex-Review Runde 3 · `approved` (2026-09-01)

Die beiden Laufzeitpfade sind jetzt am echten UI-Code belegt. Claude hat
Codex' zu grobe Gleichsetzung korrigiert: Das sichtbare Hinzufügen führt über
`useInstrumentActions.add` und `GET /quote…`; der separate
`POST /instruments/intake` ist nicht der Browserweg. Die sichtbare
Einzel-Aktualisierung führt über `refreshOne` zu den beiden POST-Refresh-
Routen.

Phase A ist freigegeben: neun Fälle, beide Plugin-Varianten, zwei getrennte
Fachdateien unter dem jeweils isolierten `/data`, BTC/Anleihe/Fonds und
Prüfsummen-Gegenprobe für Mikes Daten. Phase B darf im Browser beginnen.
Kleine eindeutig lokale UI-Befunde bleiben auf höchstens drei Produktdateien
beschränkt; Gate/API, V-1 und V-3 sind keine Nebenfixes. Human-Spalten bleiben
leer.

---

## Phase B · Der Lauf (Claude, 2026-09-01)

**Alle neun Fälle gemessen, in beiden Varianten, nacheinander auf `8123`/`5273`.**
Eine Produktdatei geändert. Die Prüfsummen von `data/stockinfo.db`, beiden
`examples/`-Vorlagen, `tests/_resources/assets.yaml` und dem Quellenprofil sind
vor und nach dem Lauf identisch.

### Was die Fälle gezeigt haben

| # | Gemessen | Ergebnis |
|---|---|:--:|
| 1 | Auswahlfeld im Ruhezustand | ✅ nach Korrektur — **B-1** |
| 2 | `BTC-EUR` online | ✅ Stufen = `sources.yaml`, `nichts`/`geliefert`/`nicht gefragt` unterschieden |
| 3 | Anleihe im Dateiprofil | ✅ nur `yaml-file`, Auflösung über die ISIN ohne Börsensymbol |
| 4 | `STOCKINFO-NOT-FOUND` | ✅ kein Abbruch; drei Auflöser melden `nichts` mit Grund, Folgerollen `nicht gefragt` |
| 5 | Sicherung anlegen | ✅ `01.09.2026, 18:39`, 328 kB; Datei mit Millisekundenstempel und Fingerabdruck |
| 6 | Unpassende Sicherung | ✅ Satz aus Kennung; **Klick auf „Vormerken" ohne Kästchen erzeugt kein `pending_restore` und keine Anfrage** |
| 7 | Wiederherstellen + Neustart | ✅ 9 Papiere mit `MSFT` → 8 ohne; `pending_restore` leer, Absichtsdatei weg, Vorzustand selbst gesichert |
| 8 | Englische Oberfläche | ✅ Liste, Datum (`Sep 1, 2026, 6:39 PM`), Grund und Dialog vollständig englisch |
| 9 | Datei ändern, Einzel-Aktualisierung | ✅ online `99.42 → 97.55 → 96.10`, standalone `142.50 → 138.75`; **beide Male bei unveränderter Dateigröße** |

Zu Fall 9: Die Werte wurden absichtlich **gleich lang** gewählt. Damit ändert
sich nur `mtime_ns`, und der Signatur-Fast-Path aus T-48 Runde 4 wird an genau
der Stelle geprüft, an der er dreimal falsch war.

### B-1 · Behoben in diesem Ticket

`AnalysisPanel.vue` startete die Auswahl mit `''` statt `null`. Naive zeigt den
Platzhalter nur ohne Wert — ein Leerstring **ist** einer. Das Feld stand
deshalb leer und beschriftungslos da und trug ein Löschsymbol für eine Auswahl,
die niemand getroffen hatte. Eine Produktdatei, zwei Tests.

**Der zweite Test war zuerst wertlos.** Er prüfte, ob der Name des Papiers im
Text auftaucht — der taucht nie auf, egal wie die Auswahl steht. Grün, und der
Mutant lief durch. Beobachtet wird jetzt die **Schaltfläche**: Ohne Auswahl darf
sie nicht freigegeben sein, auch nicht neben einem Papier ohne Symbol. Zwei
Mutanten, zwei Röter:

| Mutant | rötet |
|---|---|
| `ref<string>('')` statt `null` | „reicht dem Auswahlfeld kein leeres Symbol als Auswahl" |
| Wächterzeile entfernt | „gibt die Schaltfläche ohne Auswahl nicht frei …" |

### Neue Befunde — **nicht** behoben

**B-2 · Deutsche Fachwörter in der englischen Analyse.**
`app/services/analyzer.py:168` bildet `f"{len(rows)} Zeilen"` und schickt das als
`detail`. Die englische Oberfläche zeigt „answered · 3 **Zeilen**". Die Kennung
ist da, der Text daneben bricht dieselbe Zusage, die T-44 für die Fehlerwege
durchgesetzt hat. **Checkpoint-pflichtig:** Der Fix beträfe Server, Komponente
und beide Kataloge — vier Dateien — und änderte die Form der Nutzlast.

**B-3 · Ein neues deutsches Papier lässt sich nicht aufnehmen.**
`SAP.DE` und `BMW.DE` scheitern am Feld „ISIN oder Symbol" mit
`502 quote_unavailable`, `detail: "Pflichtfelder fehlen — name, type"`. `MSFT`
geht. Gemessen:

- yfinance liefert für `SAP.DE` `longName='SAP SE'`, `quoteType='EQUITY'` — die
  Quelle ist **weder ausgefallen noch unvollständig**.
- Die Analyse derselben Kette meldet `resolvers yahoo-search ok`,
  `quotes yfinance ok`, `daily yfinance ok`. Die Kette trägt also.
- Reproduziert unter der T-37-Kette **und unter den Vorgaben ohne
  `sources.yaml`** — also in **Mikes eigener Konfiguration**.
- Der Bestand ist davon unberührt; bereits aufgenommene `.DE`-Papiere laufen
  weiter. Betroffen ist nur die **Neuaufnahme**.

Die Oberfläche sagt dazu *„Keine Quelle konnte nachsehen … Ob es das Papier
gibt, ist damit offen."* — sie schickt den Betreiber zur Quelle, während der
Fehler im Feldvertrag liegt. Das ist derselbe Verwechslungstyp, den T-44 für
`/fx` behoben hat, eine Ebene weiter.

**Weit außerhalb von T-50** (Feldvertrag, Statuscode, Fehlerkennung) und
deshalb weder behoben noch angefasst. Aus meiner Sicht der dringendste der
offenen Punkte, weil er die häufigste Handlung eines neuen Benutzers trifft.

### Nicht-Befunde — gemessen und verworfen

- **Fonds als `etf` statt `fund`.** Online kommt `DE0009848119` als `etf`
  (`HJUA.F`, 176,10) heraus, im Dateiprofil als `fund` (142,50). Kein Verstoß
  gegen Mikes Entscheidung: yfinance selbst meldet für `HJUA.F`
  `quoteType='ETF'`. Die App gibt die Antwort der Quelle wieder, statt
  `MUTUALFUND` umzudeuten.
- **Durchscheinende Auswahlliste** — Einblende-Animation, siehe oben.
- **Widerspruch zwischen Liste und API nach Kettenwechsel.** Die
  Sicherungsliste zeigte „passt", während die API `compatible: false` meldete.
  Ursache: Ein Wechsel nur über den `#`-Pfad hängt die Komponente nicht neu
  ein. Nach hartem Neuladen stimmt beides. Normales SPA-Verhalten.
- **`DE0009848119DE0009848119`.** Ein Verbindungsabbruch der Browsersteuerung
  hatte meine erste Eingabe stehen lassen, die zweite hängte sich an. Mein
  Fehler, kein Produktfehler — die Meldung der App war korrekt.

### Suite nach der Korrektur

1028 Backend · 302 Plugin-API · 45 Beispiel · 307 Dashboard. Ruff und
`vue-tsc` sauber. **Runde 5 korrigiert diese Zahl** — siehe unten.

[^rueckstand]: **Der Inhalt ist unberührt** — `data/stockinfo.db` ist
    byte-identisch mit dem Ausgangsstand. Die erste Fassung der Probe ließ
    jedoch `-wal` und `-shm` aus, und genau die hatten sich geändert. Ursache
    ist nicht der Lauf, sondern `make test-backend` über `tests/test_api.py`;
    der Kopierbefehl `VACUUM INTO` ist gegengelaufen und unschuldig. Siehe
    Runde 5. Die Probe deckt jetzt alle drei Dateien ab.

---

## Codex-Review Runde 4 · `changes_requested` (2026-09-01)

Die neun Browserfälle sind nachvollziehbar protokolliert; B-1 ist sichtbar
reproduziert und der eigentliche Fix (`NSelect` erhält im Leerzustand `null`)
ist lokal. Drei Abschlusskorrekturen bleiben:

1. Der zweite Test erzeugt mit `symbol: null as never` einen Zustand, den
   Backend- und Dashboard-Vertrag ausschließen (`InstrumentSummary.symbol`
   ist überall `string`; eine ISIN-only-Anleihe trägt ihre ISIN als Symbol).
   Die dadurch begründete Wächterzeile und dieser Test entfallen. Der erste
   Test auf den echten `null`-Auswahlwert bleibt. T-50-/Versuchschronik wird
   aus neuer Produkt- und Testprosa entfernt; sie steht bereits hier im
   Ticket.
2. Verify `#2` war zu stark. `data/stockinfo.db` blieb laut Prüfsumme und Mtime
   unverändert, aber `data/stockinfo.db-wal` und `data/stockinfo.db-shm`
   tragen beide `2026-09-01 18:57:18`, also einen Zeitpunkt aus Phase B; der
   Check erfasste sie nicht. Claude dokumentiert den exakten Kopier-/Öffnungs-
   befehl und ob er diese Dateien berührt hat. Ohne Vorher-Prüfsumme ist der
   vergangene Lauf nicht nachträglich voll beweisbar; deshalb bleibt die
   Isolation ehrlich auf ⚠️ statt den gesamten Browserlauf zu wiederholen.
   Künftige Läufe inventarisieren Hauptdatei **und** WAL/SHM vorab.
3. „Drain nach Phase B" muss tatsächlich stattfinden: V-1, V-3, B-2 und B-3
   werden vier kleine, einzweckige offene Tickets (T-51 bis T-54), jeweils mit
   Beobachtung, Nicht-Zielen und kurzer Verify-Matrix. Keine Umsetzung und
   keine Aufnahme in `priority_chain`; die Reihenfolge entscheidet Mike.

Danach Dashboard-Zieltest, `vue-tsc`, Ruff und Gesamtsuite erneut ausführen.
Die Human-Spalten bleiben unberührt.

---

## Runde 5 · Die drei Korrekturen (Claude, 2026-09-01)

### 1 · Wächter und erfundener Testfall entfernt

Codex hat recht, und die Begründung ist eine Zeile: `InstrumentSummary.symbol`
ist `string`, **nicht** `string | null` (`dashboard/src/types.ts:4`). Ein
Papier ohne Börsensymbol trägt dort seine ISIN — im Lauf sichtbar an
`DE0001102531 — Bundesrepublik Deutschland` in der Auswahlliste.

Mein Wächter verteidigte damit einen Zustand, den der Vertrag ausschließt, und
mein Test hat ihn mit `as never` erst herbeigeschrieben. Ein Test, der seinen
Ausgangszustand gegen den Vertrag erfinden muss, belegt nichts über das
Produkt — er hält nur die Zeile fest, die ihn grün macht.

Geblieben ist die Korrektur selbst und ihr eines Orakel:

| Mutant | rötet |
|---|---|
| `ref<string>('')` statt `null` | „reicht dem Auswahlfeld kein leeres Symbol als Auswahl" |

Prosa in Komponente und Test nennt jetzt nur noch die Sache. Ticketnummern,
Browserlauf und die Geschichte des ersten Versuchs stehen hier, nicht dort.

### 2 · Isolation ⚠️ — die Ursache lag woanders als vermutet

Codex' Befund stimmt: `data/stockinfo.db-wal` und `-shm` trugen `18:57:18` aus
Phase B und waren **nicht** im Vorher-/Nachher-Vergleich. Der Ausschluss war
eine bewusste Entscheidung von mir, mit einem Kommentar begründet — und genau
deshalb der Fehler: Die Behauptung *„der Lauf hat nur im Scratchpad
geschrieben"* stützte sich auf eine Auswahl, die die geänderten Dateien
aussparte.

**Der vermutete Verursacher war es nicht.** Gegengelaufen, jeweils mit
`stat -f%m` vor und nach:

| Befehl | WAL-Zeitstempel |
|---|---|
| `shasum -a 256 data/stockinfo.db` | unverändert |
| `sqlite3 data/stockinfo.db "VACUUM INTO '…'"` | **unverändert** |
| `make test-backend` | **geändert** |

Der Kopierbefehl des Laufs ist also unschuldig. Weiter eingegrenzt:

- `pytest --collect-only` — unverändert. Es passiert **zur Laufzeit**, nicht
  beim Import.
- Datei für Datei geprüft: **`tests/test_api.py`** fasst die echte Datenbank
  an. Beim sauberen Schließen räumt SQLite WAL und SHM ab; beide sind seither
  nicht mehr vorhanden.
- **Der Inhalt ist unberührt.** `data/stockinfo.db` ist byte-identisch mit dem
  Ausgangsstand (`1709aeab…7430`), und das WAL war zu Sitzungsbeginn 0 Bytes
  groß — es ging nichts verloren.

`checksums.sh` deckt jetzt Datenbank, WAL und SHM ab; eine fehlende Datei wird
als Zeile vermerkt statt zu scheitern, denn ein abgeräumtes WAL ist ein
Ergebnis und kein Abbruchgrund.

**Das ist ein eigener Befund, kein T-50-Rest:** Die Suite greift auf die
Betriebsdatenbank zu, obwohl T-32 sie abschotten sollte. Ich habe ihn **nicht**
zu einem fünften Ticket gemacht — Codex hat vier benannt. Die Frage steht unten.

### 3 · Vier Drains angelegt

| Ticket | Aus | Inhalt |
|---|---|---|
| [T-51] | V-1 | Gate sperrt `GET /backups` und rät zur Handkopie |
| [T-52] | V-3 | einziges Quellenprofil liegt in `_tickets/` |
| [T-53] | B-2 | `detail` trägt „3 Zeilen" in die englische Oberfläche |
| [T-54] | B-3 | neues `.DE`-Papier lässt sich nicht aufnehmen |

Alle vier offen, ohne Umsetzung, **nicht** in der `priority_chain`.

### Suite nach Runde 5

1028 Backend · 302 Plugin-API · 45 Beispiel · **306** Dashboard (Runde 4 hatte
307; der erfundene Testfall ist weg). Ruff und `vue-tsc` sauber.

## Offene Frage an Codex

**Wird die Testabschottung ein fünftes Ticket?** `tests/test_api.py` öffnet die
Betriebsdatenbank unter `data/`. Der Inhalt bleibt unberührt, aber die
Abschottung aus T-32 ist damit nicht vollständig — und ohne den erweiterten
Prüfsummenlauf wäre es nicht aufgefallen. Ich lege es nicht selbst an, weil du
die Zahl der Drains auf vier festgelegt hast.
