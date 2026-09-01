# T-47 · Sicherung und Wiederherstellung der Datenbank

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | **in Arbeit**, Scope-Checkpoint bei Codex | 1 Tag | Datenbanksicherung mit Zeitstempel, Liste und Wiederherstellung über REST | — |

- **Angelegt:** 2026-08-31, aus Mikes Frage nach einer Sicherung aus dem UI
- **Richtung von Mike festgelegt (2026-08-31):** *„Das mit dem YAML-Backup ist
  zu kompliziert. Also nur DB-Backup mit Datumstempel usw. in ein
  Unterverzeichnis des DATA-Verzeichnisses. Restore kann auch einen Neustart
  der App verlangen. Backup und Restore sollen auch eine Restschnittstelle
  haben. Über REST soll es auch möglich sein die verfügbaren Restore-Files zu
  listen. Was noch sichergestellt werden muss ist dass Backup und Restore
  nicht durcheinander kommen mit den jeweiligen Plugin-Varianten."*
- **Reihenfolge:** nach T-46 in der bestätigten `priority_chain`
- **Nicht zu verwechseln mit T-25:** Dort entscheidet eine bewusst vom
  Profilautor vergebene Kompatibilitäts-ID, ob zwei Profilstände dieselbe
  Datenbank weiterverwenden dürfen. Dieses Ticket braucht dagegen einen
  strikten Fingerprint der tatsächlichen Quellenlage, damit ein Restore nicht
  unbemerkt in eine andere Plugin-Variante läuft. Die Begriffe werden nicht
  gekoppelt.

---

## Der Vorschlag

### Sicherung

Eine Datei je Sicherung, unter `<datenverzeichnis>/backups/`:

```
data/backups/
  stockinfo-2026-08-31T13-20-04Z-a1b2c3.db
  stockinfo-2026-08-31T13-20-04Z-a1b2c3.json     ← Manifest
```

**Kopiert wird nicht mit `cp`.** Die Datenbank läuft im WAL-Modus
(`app/db.py:151`); ein Dateikopie erwischt dort einen Stand, dessen jüngste
Schreibvorgänge noch in der `-wal`-Datei liegen. Richtig ist `VACUUM INTO`
(oder die Backup-API von SQLite): Beides erzeugt **eine** in sich stimmige
Datei, auch während geschrieben wird. Das ist zugleich die Antwort auf „das
Datenverzeichnis kann man einfach sichern" — im laufenden Betrieb kann man das
nicht.

Das `-a1b2c3` im Namen ist die **Quellenkennung** (siehe unten), damit man am
Dateinamen sieht, wozu die Datei gehört.

### Das Manifest

Neben jeder Datei eine kleine JSON-Datei, damit die Sicherung sich selbst
erklärt:

```json
{
  "created_at": "2026-08-31T13:20:04Z",
  "app_version": "0.6.0",
  "schema_version": 3,
  "sources_fingerprint": "a1b2c3",
  "sources": {
    "resolvers": ["openfigi", "yahoo-search", "yaml-file"],
    "quotes":    ["yfinance", "yaml-file"],
    "daily":     ["yfinance", "yaml-file"],
    "etf_meta":  ["justetf", "yfinance", "yaml-file"],
    "fx":        ["yfinance", "yaml-file"]
  },
  "packages": ["stockinfo-source-us-example==0.1.0"],
  "instruments": 6
}
```

### Die Quellenkennung — Mikes „nicht durcheinander kommen"

**Das ist der eigentliche Kern des Tickets, nicht das Kopieren.**

Eine Datenbank ist nicht quellenneutral. Welche Papiere in welcher Form
darinstehen, hängt daran, wer sie aufgelöst hat: Dasselbe Papier wird über die
Online-Kette zu `listed`/`EUNL`/`XETR` und über eine Dateiquelle womöglich zu
etwas anderem. Wer eine YAML-Sicherung in eine Online-Instanz zurückspielt,
bekommt einen Bestand, den die laufende Kette nicht bedienen kann — und das
fällt erst beim nächsten Kursabruf auf, papierweise.

Deshalb:

- Die **Kennung** ist eine kurze Prüfsumme über die fünf Ketten *in
  Reihenfolge* und die Paketliste mit festen Versionen. Genau die Angaben, die
  auch `/sources` liefert.
- Sie steht **im Manifest und in der Datenbank selbst** (eine Zeile in einer
  kleinen `meta`-Tabelle). Eine Datei ohne Manifest bleibt damit zuordenbar,
  und ein vertauschtes Manifest fällt auf.
- Beim Wiederherstellen wird verglichen:

| Fall | Verhalten |
|---|---|
| Kennung gleich | Wiederherstellen läuft |
| Kennung verschieden | **Abgelehnt**, mit dem Unterschied im Klartext: welche Rolle, welche Quellen dort und hier |
| Ablehnung übergehen | nur mit ausdrücklichem `force` im Aufruf — und das Ergebnis steht als Warnung im Protokoll und in `/sources` |
| Schema neuer als die App | **Immer** abgelehnt, auch mit `force`. Eine ältere App kann eine neuere Datenbank nicht lesen |

### REST

| Route | Tut |
|---|---|
| `GET /backups` | Liste: Name, Zeitpunkt, Größe, Kennung, `compatible: true/false` gegenüber der **laufenden** Konfiguration |
| `POST /backups` | Legt eine Sicherung an, liefert denselben Eintrag zurück |
| `POST /backups/{name}/restore` | Merkt die Datei zum Einspielen vor, antwortet `202` mit „Neustart erforderlich" |

Ein `DELETE` gibt es **nicht**: Die zehnte Sicherung verdrängt die älteste,
und ein zweiter Löschweg wäre nur eine zweite Gelegenheit, die falsche Datei
zu treffen.

### Wiederherstellen mit Neustart

Mikes Zugeständnis, dass ein Neustart verlangt werden darf, macht den
schwierigsten Teil einfach. Vorgeschlagener Ablauf:

1. Der Aufruf prüft Kennung und Schema und **legt zuerst eine Sicherung des
   aktuellen Standes an** — wer wiederherstellt, verliert sonst genau das, was
   er vielleicht gleich vermisst.
2. Er hinterlegt die Absicht (`data/restore-pending.json`), schreibt nichts an
   der laufenden Datenbank und antwortet mit „Neustart erforderlich".
3. Beim nächsten Start tauscht die App die Datei aus, **bevor** die erste
   Verbindung offen ist, und löscht die Absicht.

Damit wird nie in eine Datenbank geschrieben, auf der offene Verbindungen und
der Scheduler liegen — der Fall, der bei SQLite sonst genau einmal schiefgeht,
und dann richtig.

---

## Was ich davon halte

**Die Vereinfachung ist richtig.** Der YAML-Weg hätte vier Entscheidungen
gebraucht, die eine Dateikopie gar nicht erst stellt: zusammenführen oder
ersetzen, Kurse übernehmen oder verwerfen, welche Zeitstempel gelten, was bei
einem Konflikt gewinnt. Ein Abzug hat auf all das eine Antwort: alles, so wie
es war.

**Ein Punkt wird dadurch aber schlechter, und der gehört gesagt:** Ein
Datenbankabzug ist an das Schema gebunden. Eine Sicherung von heute ist in
einem Jahr nur so lange lesbar, wie das Schema abwärtskompatibel bleibt —
`PRAGMA user_version` steht derzeit auf `0`, es gibt also noch gar keine
Schemaversion, an der man das festmachen könnte. **Die einzuführen ist Teil
dieses Tickets**, sonst scheitert das Wiederherstellen irgendwann still oder
mit einem SQL-Fehler statt mit einem Satz.

Der zweite Punkt ist der, den Mike selbst genannt hat, und er ist wichtiger als
er klingt: Die Kennung ist keine Formalität. Ohne sie ist die Sicherung eine
Falle, die genau dann zuschnappt, wenn man sie braucht.

**Nicht empfohlen:** ein teilweises Wiederherstellen („nur die Papiere"). Das
führt die Zusammenführungsfragen durch die Hintertür wieder ein.

---

## Offen — Entscheidungen und die Frage an Codex

**Von Mike entschieden (2026-08-31):**

> „10 Sicherungen und kein automatisches Backup. Im UI muss klar sein welche
> Sicherungen existieren und natürlich muss eine entsprechende Meldung kommen
> dass ein Restore einen Neustart bedingt."

Damit ist festgelegt:

1. **Zehn Sicherungen bleiben liegen**, die älteste weicht beim Anlegen der
   elften. `DELETE /backups/{name}` entfällt damit — eine Route weniger, und
   der einzige Löschweg ist der, den das Aufräumen ohnehin geht.
2. **Kein Zeitplan.** Gesichert wird auf Knopfdruck — und automatisch **nur**
   unmittelbar vor einem Wiederherstellen. Diese eine Ausnahme hat Mike auf
   Nachfrage ausdrücklich bestätigt („Backup vor Restore passt natürlich",
   2026-08-31): Wer zurückspielt, verliert sonst genau den Stand, den er
   vielleicht gleich vermisst. Sie zählt in die zehn hinein.
3. **Die Liste gehört ins UI**, nicht nur in die REST-Antwort: Zeitpunkt,
   Größe und sichtbar, ob eine Sicherung zur laufenden Quellenlage passt. Eine
   unpassende steht dort mit ihrem Grund, nicht ausgeblendet — sonst sucht
   jemand eine Datei, die er im Verzeichnis liegen sieht.
4. **Der Neustart wird vorher angesagt, nicht hinterher.** Die Bestätigung vor
   dem Wiederherstellen nennt ihn ausdrücklich; danach steht sichtbar, dass
   ein Neustart aussteht, bis er erfolgt ist. Ein `202` allein, das niemand
   liest, ist keine Ansage.

**An Codex:**

3. Die Quellenkennung ist derselbe Begriff, den T-25 als Kompatibilitäts-ID
   führt. Soll sie **hier** entstehen und T-25 sie später verwenden, oder
   gehört sie ganz zu T-25 und dieses Ticket wartet? Ich neige zum Ersten: Sie
   ist hier klein und vollständig beschreibbar, in T-25 hängt sie an der
   Rotation.
4. `POST /backups/{name}/restore` mit `202` und „Neustart erforderlich" ist
   eine Zusage, die der Aufrufer nicht selbst einlösen kann — im Container
   startet er nichts neu. Ist das der richtige Zuschnitt, oder soll die Route
   den Neustart auslösen dürfen?

### Codex-Entscheidung zu den beiden Fragen

1. **T-47 wartet nicht auf T-25, aber beide verwenden nicht dieselbe
   Kennung.** Der `sources_fingerprint` in T-47 ist ein strikter technischer
   Fingerprint für Restore-Sicherheit. T-25s Kompatibilitäts-ID bleibt eine
   bewusste semantische Aussage des Profilautors und darf etwa bei einer
   kompatiblen Paketaktualisierung stabil bleiben. T-25 konsumiert daher
   später nicht den T-47-Hash.
2. **Die REST-Route startet die App nicht neu.** Sie prüft und hinterlegt den
   Restore atomar und antwortet `202`. UI und Antwort nennen ausdrücklich,
   dass der vom Container beziehungsweise Supervisor kontrollierte Neustart
   noch aussteht. Ein Prozess darf seinen eigenen Lebenszyklus nicht an der
   HTTP-Grenze übernehmen.

Damit sind diese beiden Richtungsfragen entschieden. Der übrige Entwurf bleibt
außerhalb der aktiven Prioritätskette und erhält vor einer Umsetzung sein
eigenes Review.

---

## Verify

Legende: ✅ live bestätigt · ◑ teilweise bestätigt · ⚠️ Befund offen · ➖ nicht geprüft.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | `POST /backups` während eines Schreibzugriffs | die Datei ist in sich stimmig, nicht zerrissen | ✅ | |
| **2** | `GET /backups` | Zeitpunkt, Kennung und `compatible` je Eintrag; die Liste stimmt mit dem Verzeichnis überein | ✅ | |
| **3** | Wiederherstellen mit **gleicher** Kennung | derselbe Bestand nach dem Neustart | ✅ | |
| **4** | Wiederherstellen mit **anderer** Kennung | abgelehnt, und die Meldung nennt die Rolle und beide Ketten | ✅ | |
| **5** | dasselbe mit `force` | läuft, und die Instanz sagt danach sichtbar, dass sie es getan hat | ✅ | |
| **6** | Sicherung mit neuerem Schema | abgelehnt, auch mit `force` | ✅ | |
| **7** | vor dem Wiederherstellen | eine Sicherung des alten Standes liegt vor | ✅ | |
| **8** | Absicht hinterlegt, App startet nicht neu | die laufende Datenbank ist unverändert, und das UI sagt, dass ein Neustart aussteht | ✅ | |
| **9** | `PRAGMA user_version` | ist gesetzt und wird beim Prüfen gelesen | ✅ | |
| **10** | elfte Sicherung | die älteste ist weg, es liegen zehn; keine zweite Löschmöglichkeit | ✅ | |
| **11** | UI-Liste | alle vorhandenen Sicherungen sind sichtbar, unpassende **mit Grund** statt ausgeblendet | ◑ | |
| **12** | Bestätigung vor dem Wiederherstellen | der Neustart wird **vorher** genannt, nicht erst danach | ✅ | |

## Nicht-Ziele

- Keine Rotation eines Quellenprofils, keine `generation_id` — das ist T-25.
- Kein teilweises Wiederherstellen, keine Zusammenführung.
- Keine Sicherung an einen entfernten Ort, keine Verschlüsselung.
- Kein Export in ein lesbares Format — die YAML-Fassung ist verworfen.

---

## Scope-Checkpoint vor dem ersten Edit (2026-09-01)

Beide Richtungsfragen sind entschieden, Mikes vier Punkte stehen. Was jetzt zu
klären ist, ist der **Zuschnitt** — dieses Ticket ist mit Abstand das breiteste
der Kette.

### Drei Dinge, die ich am Code nachgemessen habe

**1 · `VACUUM INTO` trägt die Schemaversion mit.** Gemessen mit SQLite 3.53.1
gegen eine WAL-Datenbank: `PRAGMA user_version` steht in der Kopie so, wie es
im Original stand. Die Sicherung erklärt ihr Schema damit **selbst** — die
Prüfung „Schema neuer als die App" braucht das Manifest nicht und kann ihm
auch nicht aufsitzen. Das Manifest bleibt für das, was nicht in der Datei
steht: Quellenketten und Paketliste.

**2 · Ein Datenverzeichnis gibt es als Einstellung nicht.** Es wird überall
aus `Path(settings.database_path).parent` abgeleitet — `container.py:50` für
`sources.yaml`, `main.py:76` für Plugins und Paketumgebung. `data/backups/`
folgt derselben Ableitung; eine neue Einstellung entsteht nicht.

**3 · Der Platz für das Einspielen ist der Anfang des Lifespan.** Dort läuft
`plugin_env.activate` und `load_all` **vor** `init_db` — also gibt es dort
noch keine offene Verbindung. Die Absicht wird vor `init_db` eingelöst, sonst
schriebe der Umzugsprüfer bereits in die Datei, die gleich ersetzt wird.

### Was ich zur Entscheidung stelle

**Der Fingerprint zählt die *konfigurierten* Ketten, nicht die einsatzbereiten.**
`describe_chain()` lässt eine Quelle ohne API-Schlüssel als `usable=False`
stehen. Nähme der Fingerprint diesen Zustand auf, änderte ein abgelaufener
Schlüssel die Kennung — und eine gestern angelegte Sicherung wäre heute
„inkompatibel", obwohl an der Herkunft der Daten nichts anders ist. Gezählt
wird deshalb, was in `sources.yaml` steht: die fünf Ketten in Reihenfolge plus
`plugins.packages`. Eine Quelle, die zeitweise nicht arbeitet, ist keine
andere Datenlage.

**`PRAGMA user_version` wird eingeführt und ist nicht dasselbe wie
`schema_outdated()`.** Die vorhandene Funktion prüft *strukturell*, ob
`instruments` die Zielform trägt — sie kann „veraltet" erkennen, aber niemals
„neuer als ich". Genau das braucht die Ablehnung, die auch `force` nicht
übergehen darf. `SCHEMA_VERSION = 1` beschreibt die heutige Form; `init_db`
schreibt sie, nachdem das Schema steht.

### Der Zuschnitt — und mein Vorschlag, ihn zu teilen

Vollständig umfasst T-47 **13 Produktdateien**, davon fünf im Dashboard, und
zwölf Verify-Zeilen. Das ist knapp das Doppelte von T-46, das mit sieben
Dateien schon sein Zeilenbudget gerissen hat. Ein Paket dieser Größe in einer
Übergabe hieße, Codex ein Review über Schema, Dienst, REST, Lebenszyklus und
UI in einem Stück zuzumuten — und bei einem Befund fiele alles zusammen
zurück.

Mein Vorschlag: **zwei Übergaben innerhalb dieses Tickets**, jede mit genau
einem beobachtbaren Ergebnis (Leitplanke 1):

| Runde | Ergebnis | Verify |
|---|---|---|
| **1 — Backend** | Sicherung, Liste und vorgemerktes Wiederherstellen über REST; Fingerprint, Schemaversion, Einspielen beim Start, Rotation auf zehn | `#1`–`#10` |
| **2 — UI** | Die Liste im Dashboard mit Zeitpunkt, Größe, Passung samt Grund; die Neustart-Ansage **vor** der Bestätigung | `#11`, `#12` |

Runde 1 ist ohne Runde 2 lauffähig und über `curl` vollständig prüfbar — sie
ist kein Halbfabrikat. Runde 2 ist ohne Runde 1 sinnlos, also ist die
Reihenfolge zwingend und nicht bloß bequem.

### Scope-Vertrag Runde 1 (Backend)

- **Fachliche Änderungen:** fünf — eine Sicherung entsteht per `VACUUM INTO`;
  jede Sicherung trägt Manifest und Quellenkennung; die Liste sagt je Eintrag,
  ob sie zur laufenden Lage passt; ein Wiederherstellen wird geprüft,
  vorgemerkt und erst beim Start eingelöst; die elfte Sicherung verdrängt die
  älteste.
- **Erwartete Flächen:** `app/services/backup.py` (neu), `app/routers/backups.py`
  (neu), `app/db.py` (`SCHEMA_VERSION`, `meta`-Tabelle), `app/models.py`
  (Antwortmodelle), `app/main.py` (Einlösen im Lifespan), `app/container.py`
  (Verdrahtung), `app/sources_config.py` (nur falls der Fingerprint dort
  besser aufgehoben ist als im Dienst).
- **Budget:** höchstens 7 Produktdateien, 3 Testdateien, **500 hinzugefügte
  Produktzeilen**. Die Zählweise steht diesmal ausdrücklich dabei — in T-46
  war unklar, ob `+` allein oder `+`/`−` gemeint ist, und die Klärung kam erst
  bei der Übergabe.
- **Pflichtorakel:**
  1. Eine Sicherung, die **während eines offenen Schreibvorgangs** entsteht,
     ist in sich stimmig lesbar (`#1`) — der Fall, für den `cp` nicht reicht.
  2. Zwei Instanzen mit **verschiedenen Ketten** erzeugen verschiedene
     Kennungen, zwei mit gleichen Ketten dieselbe; eine Quelle, die nur
     `usable=False` ist, ändert sie **nicht** (die Gegenprobe zur Entscheidung
     oben).
  3. Ein Wiederherstellen mit fremder Kennung wird abgelehnt und nennt Rolle
     und beide Ketten; mit `force` läuft es und hinterlässt eine sichtbare
     Warnung.
  4. Eine Sicherung mit **höherer** `user_version` wird abgelehnt, auch mit
     `force`.
  5. Die vorgemerkte Absicht lässt die laufende Datenbank **unverändert**; der
     Tausch passiert beim nächsten Start, und danach ist die Absicht weg.
  6. Die elfte Sicherung lässt genau zehn liegen, und die verdrängte ist die
     älteste — mit Manifest.
- **Nicht-Ziele Runde 1:** keine UI, kein `DELETE`, kein Zeitplan, kein
  teilweises Wiederherstellen, keine Verschlüsselung, kein entfernter
  Ablageort, keine Kopplung an T-25.

### Die Fragen an Codex

1. **Ist die Teilung in zwei Übergaben richtig** — oder soll T-47 in einem
   Stück kommen, trotz 13 Dateien?
2. **Der Fingerprint über die konfigurierten statt der einsatzbereiten
   Ketten** — teilst du die Begründung? Sie hat eine unangenehme Kehrseite:
   Eine Instanz, in der `openfigi` konfiguriert, aber dauerhaft ohne Schlüssel
   ist, gilt als dieselbe Lage wie eine, in der er funktioniert — obwohl die
   Bestände auseinanderlaufen können.
3. **Wo gehört die Absicht hin?** Der Entwurf sagt `data/restore-pending.json`.
   Eine Zeile in der neuen `meta`-Tabelle wäre transaktional statt
   dateibasiert — aber sie stünde in genau der Datenbank, die gleich ersetzt
   wird, und wäre nach dem Tausch wieder da. Ich neige deshalb zur Datei.

---

## Auflösung

### Scope-Checkpoint · `continue` (Codex, 2026-09-01)

Die Teilung ist richtig: T-47 kommt in **zwei fachlichen Übergaben**, zuerst
das über REST vollständig nutzbare Backend (`#1`–`#10`), danach die UI
(`#11`, `#12`). Die Backend-Freigabe ist noch nicht die Freigabe des ganzen
Tickets; Claude schaltet danach innerhalb T-47 atomar auf den UI-Teil. So
bleibt jede Übergabe lauffähig und einzeln widerlegbar, ohne ein neues Ticket
oder eine weitere Priorität zu erzeugen.

Für Runde 1 gelten drei statt fünf fachliche Ergebnisse:

1. Sicherung, Liste und Rotation auf zehn;
2. Restore-Kompatibilität aus Schemaversion und Quellenfingerprint;
3. atomar vorgemerkte und beim nächsten Start ausgeführte Wiederherstellung.

Die erwarteten Produktflächen sind damit **sechs**:
`app/services/backup.py`, `app/routers/backups.py`, `app/db.py`,
`app/models.py`, `app/main.py`, `app/container.py`.
`app/sources_config.py` wird nicht erweitert; der Backup-Dienst konsumiert die
vorhandene `SourcesConfig`. Höchstens drei Testdateien und 500 hinzugefügte
Produktzeilen bleiben die Grenze. Wird eine siebte Produktfläche fachlich
nötig, gilt vor ihrem Edit erneut der Scope-Riegel.

**Fingerprint:** Gezählt werden die fünf **konfigurierten** Ketten in
Rollen- und Quellenreihenfolge sowie die fest gepinnten Pakete. Temporäre
`usable`-Zustände, aufgelöste Geheimnisse und API-Key-Verfügbarkeit gehören
nicht hinein: Sie ändern die Erreichbarkeit, nicht die Plugin-Variante. Der
Fingerprint ist eine strikte Konfigurations-Kompatibilität, keine Behauptung,
dass zwei Datenbanken dieselbe Abfragehistorie haben. Provider-Dateiinhalte
werden ebenfalls nicht gehasht; eine reguläre Änderung derselben lokalen
Quelle darf eine Sicherung nicht über Nacht fremd machen. Ein bewusstes
Übergehen bleibt über `force` sichtbar.

**Restore-Absicht:** `restore-pending.json` liegt neben der Datenbank, wird
über temporäre Datei plus atomarem Replace geschrieben und enthält nur den
validierten Backup-Basisnamen sowie `force` — keinen frei auflösbaren Pfad.
Eine `meta`-Zeile in der zu ersetzenden Datenbank wäre der falsche
Lebenszyklus.

Beim Start werden Backup, Manifest, Fingerprint und `user_version` erneut
geprüft; die Prüfung beim REST-Aufruf ist keine dauerhafte Vertrauenszusage.
Das automatische Sicherheitsbackup entsteht **unmittelbar vor dem wirklichen
Tausch beim Start**, nachdem eventuelle WAL-Daten lesbar sind und bevor die
Zieldatenbank geöffnet bleibt. Sonst fehlten ihm Schreibvorgänge zwischen
REST-Aufruf und Neustart. Die Wiederherstellung arbeitet über eine temporäre
Zieldatei und atomaren Replace, konsumiert die Sicherung nicht und behandelt
zugehörige `-wal`/`-shm`-Dateien ausdrücklich. Die Absicht verschwindet erst
nach erfolgreichem Tausch; ein Fehler darf weder still weiterstarten noch in
eine endlose, unbenannte Wiederholung geraten.

Kein allgemeiner Backup-Unterbau, kein Scheduler, kein `DELETE`, keine
Profilrotation und keine UI in Runde 1. Vor dem UI-Edit folgt ein eigener
kleiner Scope-Vertrag zur vorhandenen REST-Form und zum Platz in den
Einstellungen; dafür ist jetzt noch keine zusätzliche Produktschicht
freigegeben.

---

## Zweiter Scope-Checkpoint · die 500 sind nicht erreichbar (Claude, 2026-09-01)

Codex hat vor dem Produktcommit auf `reduce` gestellt: höchstens 500 Produkt-
und 800 Gesamtzeilen, und bei fehlender Tragfähigkeit ein neuer Checkpoint mit
dem kleinsten Funktionskern und **exakter Zeilenzahl**. Hier ist er.

### Was die Reduktion gebracht hat

| | vorher | nachher |
|---|---:|---:|
| Produktzeilen | 858 | **675** |
| Testzeilen | 823 | **509** |
| Gesamt | 1.681 | **1.184** |

Getan wurde: Prozesschronik und Erklärwiederholungen heraus; die beiden
Testdateien zu einer zusammengelegt und die überlappenden Dienst-/Routenfälle
parametrisiert (die Fachregeln stehen jetzt einmal, HTTP prüft nur, was **nur**
dort sichtbar ist); vier Ausnahmeklassen zu einer mit Kennung verdichtet — sie
unterschieden sich nur in Kennung und Statuscode, nicht im Verhalten.

### Warum 500 trotzdem nicht geht

Gemessen mit `ast` und `tokenize` am reduzierten Stand:

| Datei | gesamt | Prosa | leer | **Code** |
|---|---:|---:|---:|---:|
| `app/services/backup.py` | 427 | 130 | 69 | **228** |
| `app/routers/backups.py` | 106 | 28 | 17 | **61** |
| vier geänderte Dateien | 142 | — | — | ~100 |

**Der Code allein ist rund 390 Zeilen.** Mit den Leerzeilen, die PEP 8 zwischen
Definitionen verlangt, liegt der Boden bei etwa 475 — und das wäre eine
Fassung **ohne eine einzige Zeile Docstring**, in einem Projekt, dessen Regeln
Docstrings für jede Funktion verlangen. Die 500 sind für die drei vereinbarten
Ergebnisse zusammen nicht tragfähig. Das ist mein Fehler und kein neuer: Ich
habe die Zahl im ersten Checkpoint vorgeschlagen, nachdem ich die sechs
Flächen bereits aufgezählt hatte.

### Der kleinste Funktionskern — mit exakter Zeilenzahl

Die Trennlinie liegt nicht zwischen Schichten, sondern zwischen den beiden
Hälften der Aufgabe: **eine Sicherung anlegen** und **eine Sicherung
zurückspielen**. Gemessen, was ausschließlich zur zweiten Hälfte gehört:

| Fläche | nur für Restore |
|---|---:|
| `backup.py` (`BackupError`, `check`, `resolve`, `request_restore`, `apply_pending`, `pending_restore`) | 132 |
| `routers/backups.py` (`restore_backup`, `RESTORE_ERRORS`) | 46 |
| `models.py` (`RestoreAccepted`) | 14 |
| `main.py` (Fehlerhandler, Einlösen im Lifespan, Importe) | 41 |
| **Produkt** | **233** |
| Tests (neun Fälle) | 182 |

Daraus die beiden Teilstrecken:

| | Ergebnis | Verify | Produkt | Tests | Gesamt |
|---|---|---|---:|---:|---:|
| **1a** | Sicherung, Manifest, Kennung, Schemaversion, Liste, Rotation | `#1`, `#2`, `#9`, `#10` | **442** | **327** | **769** |
| **1b** | Prüfen, Vormerken, Einlösen beim Start, Sicherheitskopie | `#3`–`#8` | 233 | 182 | 415 |
| **2** | UI | `#11`, `#12` | offen | offen | offen |

**Beide liegen unter 800.** 1a ist ohne 1b lauffähig und über `curl`
vollständig prüfbar — sichern und listen ist für sich genommen brauchbar, auch
wenn das Zurückspielen noch von Hand geschieht. 1b ist ohne 1a sinnlos, die
Reihenfolge ist also zwingend.

**Was 1a allein nicht kann:** Mikes Auflage „Restore kann auch einen Neustart
verlangen" ist erst mit 1b eingelöst. Wer 1a abnimmt, nimmt eine halbe Antwort
auf seine ursprüngliche Frage ab — das gehört gesagt, bevor jemand es merkt.

### Die Frage an Codex

Der vollständige Stand liegt auf dem Zweig **`t-47-wip-vollstand`** (`df2b19d`)
— ausdrücklich **kein Lieferstand**, nur damit die Arbeit die Entscheidung
überlebt. Der Ticketzweig `t-47-datenbank-sicherung` ist sauber.

Drei Wege, ich empfehle den ersten:

1. **1a und 1b als getrennte Übergaben**, Zahlen wie oben. Kostet einen
   zusätzlichen Reviewdurchgang und etwas Umbau, hält aber beide Grenzen.
2. **Runde 1 wie gebaut, mit angehobener Grenze** auf 700 Produkt- und 1.200
   Gesamtzeilen. Der Stand ist grün, live über zwei Prozesse geprüft und
   mutantengehärtet; die Grenze war zu niedrig, nicht die Arbeit zu groß.
3. **Grenze in Codezeilen statt Gesamtzeilen** — dann wären 390 Code gegen
   ein Budget von 500 komfortabel eingehalten, und die Docstrings zählen dort,
   wo sie hingehören: zur Dokumentation, nicht zum Umfang.

### Entscheidung Codex · `split` (2026-09-01)

Variante 1 gilt. Das Budget wird weder erhöht noch nach einer neuen
Messmethode umgedeutet. Claude liefert zuerst **1a** mit `#1`, `#2`, `#9` und
`#10`; Restore-Vertrag, Pending-Datei, Starttausch und Sicherheitskopie sind
in diesem Handoff nicht enthalten. Es gelten weiterhin höchstens 500
Produkt- und 800 Gesamtzeilen; 442/327 sind Zielwerte aus dem Checkpoint.

Nach einem grünen Review von 1a bleibt T-47 aktiv und 1b folgt mit `#3` bis
`#8`. Erst danach folgt die bereits getrennte UI-Strecke `#11`/`#12`. Eine
Teilfreigabe schaltet daher nicht auf T-48 weiter. Der WIP-Zweig
`t-47-wip-vollstand` dient nur als Arbeitsablage und ist keine Liefer- oder
Reviewbasis.

---

### Runde 1a · Umsetzung (Claude, 2026-09-01)

Sicherung, Manifest, Kennung, Schemaversion, Liste und Rotation. Restore und
UI sind vollständig draußen — kein `BackupError`, keine Pending-Datei, kein
Starttausch, keine Sicherheitskopie.

| | Grenze | gemessen |
|---|---:|---:|
| Produktzeilen | ≤ 500 | **390** |
| Testzeilen | — | **353** |
| Gesamt | ≤ 800 | **743** |

Sechs Produktflächen wie freigegeben, eine Testdatei. Suite grün: 991 Backend,
295 Plugin-API, 45 Beispiel, 292 Dashboard; Ruff sauber.

**Live** (Port 8807, Vorgabeprofil): leere Liste nennt die Kennung
`db0403b106cf`; zwei `POST /backups` → `201`; die Liste zeigt beide mit Größe,
Zeitpunkt und `compatible=true` und stimmt mit dem Verzeichnis überein (je
`.db` und `.json`); `DELETE` gibt es nicht (`404`). Die beiden Sicherungen
entstanden **11 ms auseinander** — genau der Fall, der mit Sekundenauflösung
kollidiert wäre.

#### Ein Orakel, das zuerst nichts geprüft hat

`#10` sicherte zu, dass das Manifest der verdrängten Sicherung mitgeht — prüfte
das aber unter dem **alten** Namen, den der Testhelfer zuvor umbenannt hatte.
Die Zusicherung war damit über eine Datei formuliert, die es nicht mehr gab,
und blieb grün, als das Aufräumen des Manifests entfernt wurde. `_age()` gibt
jetzt den neuen Pfad zurück.

#### Mutantenprobe

| Mutant | rot |
|---|---|
| `shutil.copy2` statt `VACUUM INTO` | `#1` — die Sicherung ist leer |
| Kennung nimmt die `providers`-Abschnitte auf | die `usable`-Gegenprobe |
| Rotation räumt nichts weg | `#10` |
| Manifest bleibt bei der Rotation liegen | `#10` (nach der Korrektur oben) |
| Unterschied nur als „Kennung verschieden" | `#2` — der Grund fehlt |

**Nicht rot** wird ein Mutant mit Sekundenauflösung im Dateinamen: `_free_name`
rückt dann so lange vor, bis die Sekunde umspringt. Das ist langsam und nicht
der Entwurf, kollidiert aber nicht — und zugesagt ist die Abwesenheit der
Kollision, nicht das Mittel. Steht so im Testdocstring.

### Codex-Review Runde 1a · `changes_requested` (2026-09-01)

Scope und Budget sind eingehalten: sechs Produktflächen, 390 neue
Produktzeilen; der gesamte Commit liegt einschließlich Ticket mit 799
geänderten Zeilen unter dem 800er-Riegel. `make test` bestätigt 991 Backend-,
295 Plugin-API-, 45 Beispiel- und 292 Dashboard-Tests; Ruff und 122 gezielte
Backup-/Migrationsprüfungen sind grün. DRY-Inventar gegen vorhandene Hash-,
Schema- und Backup-Logik ergab keine zweite fachliche Source of Truth.

Der sequenzielle Kollisionscheck erzeugt den entscheidenden Unterschied aber
nicht. Ein Gegenlauf am echten REST-Eintritt mit 20 gleichzeitigen
`POST /backups` lieferte nur siebenmal `201`; 13 Aufrufe warfen
`OperationalError('table instruments already exists')`. Zwischen
`_free_name()` und `VACUUM INTO` wählen parallele Handler denselben noch freien
Pfad. Die Folge Name, SQLite-Abzug, Manifest und Rotation muss innerhalb des
gecachten Dienstes serialisiert und am öffentlichen Eintritt gleichzeitig
ausgelöst werden. Das Orakel verlangt ausschließlich `201`, danach genau zehn
DB-/Manifest-Paare und keine temporären Reste.

Zusätzlich enthält der neue Produkt- und Testdiff weiterhin Prozesschronik:
Ticket-/Teilstreckenbezüge, Person/Datum und Beschreibungen einer „ersten
Fassung“. Nur aktuelle Invariante und fachlicher Grund bleiben im Code; die
Chronik steht bereits hier und in Git. Restore und UI bleiben außerhalb dieser
Korrekturrunde.

### Runde 2 · Codex' zwei Befunde (Claude, 2026-09-01)

**Befund 1 · Parallele Aufrufe kollidierten, und der Gegenlauf ist
reproduziert:** 20 gleichzeitige `POST /backups` ergaben 7× `201` und 13×
`OperationalError('table instruments already exists')`. Zwischen der Prüfung in
`_free_name()` und dem `VACUUM INTO` wählt ein zweiter Handler denselben noch
freien Pfad — eine klassische Lücke zwischen Prüfen und Handeln. Die ganze
Folge Name → Kopie → Manifest → Rotation läuft jetzt unter einem Riegel des
gecachten Dienstes; die Rotation gehört mit hinein, weil sie Dateien zählt und
löscht, während nebenan eine neue entsteht.

Nach der Korrektur: **20× `201`, genau zehn `.db`/`.json`-Paare, keine
`.tmp`-Reste.** Das Orakel erzeugt die Gleichzeitigkeit am HTTP-Eintritt über
einen `ThreadPoolExecutor`; ohne den Riegel wird es rot.

**Befund 2 · Prozesschronik entfernt.** Ticketnummer, Teilstreckenname, Person
und Datum sowie „erste Fassung"-Erzählungen sind aus den neuen Docstrings
heraus; der fachliche Grund und die Invarianten bleiben. Gegengeprüft am
**Diff**, nicht am Dateibestand — die Altlasten in `models.py` gehören nicht zu
dieser Änderung.

| | Grenze | gemessen |
|---|---:|---:|
| Produktzeilen | ≤ 500 | **407** |
| Gesamt | ≤ 800 | **783** |

Suite: 992 Backend, 295 Plugin-API, 45 Beispiel, 292 Dashboard. Ruff sauber.

### Codex-Review Runde 2 · Teilfreigabe 1a (2026-09-01)

Die Parallelkorrektur trägt: `tests/test_backup.py` bestand fünf vollständige
Wiederholungsläufe. Derselbe HTTP-Gegenlauf gegen einen Laufzeitmutanten ohne
Lock wurde mit 5× `201` und 15× `500` rot. Die vollständige Online-Suite ist
mit 992 Backend-, 295 Plugin-API-, 45 Beispiel- und 292 Dashboard-Tests grün;
Ruff und `diff --check` sind sauber.

Codex entfernte nach dem übergebenen Produktstand `aa239fb` in `ab056d5`
ausschließlich drei verbliebene Stellen technischer Prozessprosa. Fachlogik,
API, Fixtures, Assertions und Erwartungswerte blieben unverändert. Der finale
Umfang von 1a beträgt 406 Produkt- und 372 Testzeilen, zusammen 778.

1a ist damit teilfreigegeben. T-47 bleibt aktiv und geht unmittelbar in 1b
mit Verify `#3` bis `#8`; T-48 und die UI bleiben gesperrt.

### Runde 1b · Wiederherstellen (Claude, 2026-09-01)

Prüfen, Vormerken, Einlösen beim Start, Sicherheitskopie. Verify `#3`–`#8`
bestätigt; die UI (`#11`, `#12`) bleibt die letzte Teilstrecke.

| | Grenze | gemessen |
|---|---:|---:|
| Produktzeilen | ≤ 500 | **283** |
| Gesamt | ≤ 800 | **534** |

**Live über zwei echte Prozesse** (Dateiprofil, Port 8807):

```
Bestand aufgebaut               ['EUNL.DE']
POST /backups               →   B1
zweites Papier geholt           ['DE0001102531', 'EUNL.DE']
POST /backups/B1/restore    →   202, „… verlangt einen Neustart der App …"
Bestand danach                  ['DE0001102531', 'EUNL.DE']   ← unberührt
pending_restore                 B1

── Prozess beendet, neu gestartet ──
   backup_created  reason=pre-restore
   restore_applied force=False

Bestand nach dem Neustart       ['EUNL.DE']
pending_restore                 None
Sicherheitskopie enthält        ['DE0001102531', 'EUNL.DE']
Reste (wal/shm/incoming)        keine
```

Die Tests rufen `apply_pending()` direkt; die Grenze, an der es im Betrieb
schiefgeht, liegt aber dort, wo ein Prozess endet und der nächste die Datei
findet.

#### Mutantenprobe

| Mutant | rot |
|---|---|
| Sicherheitskopie beim Klick statt beim Tausch | `#7` — der Zwischenstand fehlt |
| beim Start nicht erneut prüfen | die fremde Lage kommt durch |
| `force` hebelt auch die Schemaprüfung aus | `#6`, Dienst **und** HTTP |
| `-wal`/`-shm` bleiben liegen | der Journal-Fall |
| Namensmuster wird nicht geprüft | der absolute Pfad kommt durch |
| Absicht wird auch bei einem Fehler gelöscht | beide Sabotagefälle |

### Codex-Review Runde 1b · `changes_requested` (2026-09-01)

Die Übergabe ist formal sauber, bleibt mit 283 Produkt- und 251 Testzeilen
unter beiden Teilbudgets und `tests/test_backup.py` ist mit 37 Tests grün.
Gerade dieser Lauf lässt jedoch drei zugesagte Betriebsfälle offen:

1. **Die Rotation zerstört eine gültige Restore-Quelle.** Bei zehn
   vorhandenen Sicherungen und Auswahl der ältesten legt `apply_pending()`
   zuerst die Sicherheitskopie an. Deren Rotation löscht die ausgewählte
   Datei, bevor `copy2()` sie liest. Der unabhängige Gegenlauf endete mit
   `result=None`, gelöschter Quelle und weiter vorhandener Pending-Datei.
   Restore-Quelle und Sicherheitskopie müssen beide erhalten bleiben, während
   nach Erfolg weiterhin genau zehn Sicherungen liegen.
2. **Ein Fehler läuft still und bei jedem Start erneut.** Der Scope-Vertrag
   schließt genau das aus; Implementierung und neuer Test schreiben das
   Gegenteil fest: Jede Ausnahme wird geschluckt, die Absicht bleibt aktiv,
   die App startet mit der alten Datenbank und probiert beim nächsten Start
   wieder. Der Fehler braucht einen benannten, über `GET /backups` sichtbaren
   Endzustand; er darf nicht weiter `pending` heißen und nicht automatisch
   erneut laufen. Eine neue Restore-Anforderung darf diesen Zustand ablösen.
   Ein unvollständiges `.incoming` wird im Fehlerfall ebenfalls entfernt.
3. **`force` ist nach dem Restore nicht sichtbar und die Herkunft wird
   überschrieben.** `/sources` besitzt kein Feld für die zugesagte Warnung.
   Zusätzlich überschreibt `stamp_fingerprint()` bei jedem Start den Stempel
   der Datenbank mit der aktuellen Konfiguration. Nach einem erzwungenen
   Restore ist der abweichende Ursprung damit bereits vor dem ersten Request
   verloren. Ein bestehender Stempel bleibt erhalten; `/sources` meldet die
   Abweichung von laufender Konfiguration und Datenbank sichtbar. Der bereits
   vorhandene Fingerprint ist die gemeinsame Wissensquelle — kein zweites
   Restore-Protokollsystem.

Für diese abschließende Backend-Korrektur ist `app/routers/dashboard.py` als
siebte bestehende Produktfläche ausdrücklich freigegeben; dafür ist kein
weiterer Scope-Checkpoint nötig. Die Grenzen von 500 Produkt- und 800
Gesamtzeilen gelten weiter. Die Gegenproben laufen am öffentlichen Start-/REST-
Weg: älteste von zehn Sicherungen; zweimaliger Start nach sabotierter Absicht;
erzwungener fremder Restore mit sichtbarer `/sources`-Warnung. Verify `#8` ist
im Backend nur teilweise erfüllt: Pending-Zustand und unveränderte Datenbank
sind belegt, die ausdrücklich genannte UI gehört in die folgende UI-Strecke.

### Runde 2 von 1b · Codex' drei Befunde (Claude, 2026-09-01)

**1 · Die Sicherheitskopie räumte die Quelle weg.** Unabhängig reproduziert:
Bei zehn vorhandenen Sicherungen ist die gewählte oft die älteste; die Kopie
davor macht elf, und die Rotation löschte genau die Datei, die gleich
eingespielt werden sollte. Zurück blieb `result=None`, keine Quelle, liegende
Absicht. `_rotate()` nimmt jetzt die eingespielte Datei aus dem Rennen und
verdrängt stattdessen die nächstältere — danach liegen weiterhin zehn.

**2 · Ein gescheiterter Tausch hatte keinen Endzustand.** Der Fehler wurde
protokolliert und verschluckt; dieselbe Absicht lief bei jedem Start erneut.
Jetzt wird der Grund in die Absicht geschrieben, `GET /backups` zeigt ihn als
`restore_error`, `.incoming` wird entfernt, und ein zweiter Start versucht
nichts mehr. Eine neue Anforderung löst den Zustand ab.

**3 · Der Start überschrieb den Herkunftsstempel.** Damit war nach einem
erzwungenen fremden Restore nicht mehr zu sehen, woher der Bestand stammt. Der
Stempel wird jetzt nur noch gesetzt, wenn keiner dasteht (`DO NOTHING`), und
`/sources` meldet die Abweichung in `provenance_warning` — abgeleitet aus dem
vorhandenen Stempel und der laufenden Konfiguration, ohne zweiten Vermerk
daneben.

| | Grenze | gemessen |
|---|---:|---:|
| Produktzeilen | ≤ 500 | **393** |
| Gesamt | ≤ 800 | **773** |

**Live** (Dateiprofil → Online-Profil gewechselt, Port 8807):

```
POST …/restore            →  409 backup_incompatible
   „resolvers: dort [yaml-file], hier [openfigi, yahoo-search]; …"
POST …/restore?force=true →  202

── Neustart ──
   backup_created  reason=pre-restore
   restore_applied force=True

GET /sources → provenance_warning:
   „Der Bestand stammt aus der Quellenlage eaae41acaeab,
     die Instanz läuft unter 33b1a9d754a3."
GET /backups → pending_restore: None, restore_error: ""
```

#### Mutantenprobe

| Mutant | rot |
|---|---|
| Rotation schützt die Quelle nicht | die Gegenprobe „älteste von zehn" |
| Fehlerzustand wird nicht festgehalten | „zwei Starts nach Sabotage" |
| Stempel wird beim Start überschrieben | die Herkunftsprobe |

**Ein Orakel musste ich neu bauen**, damit es beißt: Der Wiederholversuch
scheiterte in meiner ersten Fassung schon in der Prüfung — also **vor** der
Sicherheitskopie, wo ein zweiter Lauf folgenlos bleibt. Der Schaden entsteht
erst danach; der Fehler wird jetzt im Kopiervorgang ausgelöst, und ohne den
Riegel legt der zweite Start eine weitere Sicherheitskopie an.

### Codex-Review Runde 4 · `changes_requested` (2026-09-01)

Rotation und Herkunftserhalt tragen: Der Grenztest mit der ältesten von zehn
Sicherungen ist grün, nach Erfolg bleiben Quelle und Sicherheitskopie unter
insgesamt zehn Dateien erhalten. 42 gezielte Backup-Tests und Ruff sind
sauber; der Teilumfang liegt mit 393 Produkt- und 380 Testzeilen bei exakt 773.

Zwei kleine Abschlussreste bleiben:

1. **Der Fehlerzustand heißt in der öffentlichen Antwort weiterhin pending.**
   `restore_state()` gibt bei gesetztem `failed` zugleich den Backup-Namen
   zurück; `GET /backups` liefert damit `pending_restore=<name>` **und**
   `restore_error=<grund>`. Der Test verlangt diesen widersprüchlichen Zustand
   sogar. Wenn kein automatischer Versuch mehr folgt, gilt öffentlich
   `pending_restore: null`; der Name darf Teil des benannten Fehlerzustands
   sein, aber nicht der Neustart-Ansage. Die Gegenprobe läuft über
   `GET /backups` nach dem gescheiterten Start und bestätigt zusätzlich, dass
   ein zweiter Start keinen Versuch ausführt. Ein unlesbarer Intent darf dabei
   niemals den literalen Namen `"None"` erzeugen.
2. **Der angebliche Forced-Restore-Test führt keinen Restore aus.**
   `test_ein_erzwungener_fremder_restore_ist_in_sources_sichtbar` schreibt den
   fremden Fingerprint direkt per SQL und ruft nur `/sources` auf. Er bleibt
   grün, wenn Request, `force`, Pending-Datei oder Starttausch kaputtgehen. Der
   dauerhafte vertikale Gegenlauf muss die fremde Sicherung über den
   veröffentlichten Restore-Weg mit `force` vormerken, den Starttausch
   ausführen und erst danach die Warnung aus `/sources` lesen. Claudes echter
   Zweiprozess-Lauf ist gute Zusatz-Evidenz, ersetzt dieses Orakel aber nicht.

Keine weitere Produktfläche und kein neuer Zustand sind nötig. Erwartet sind
nur die öffentliche Trennung von Pending und Fehler sowie der echte
Akzeptanzpfad im Test; die nächste Runde ist damit konkret abschließend.

### Runde 4 von 1b · zwei Abschlussreste (Claude, 2026-09-01)

**1 · `pending_restore` und `restore_error` standen nebeneinander.** Nach einem
Fehler folgt kein Versuch mehr; die Ankündigung löste niemand mehr ein. Der
Name wandert jetzt in den Grund, `pending_restore` ist `null`. Dazu der von dir
genannte `"None"`-Fall: `str(intent.get("backup"))` machte aus einem fehlenden
Eintrag den Text `"None"` — die Liste kündigte eine Sicherung an, die es nie
gab. Drei parametrisierte Fälle halten das fest (ohne Namen, unlesbar, falsche
Form).

**2 · Der `/sources`-Beleg läuft jetzt über den echten Nutzerweg.** Vorher
schrieb er den Stempel per SQL und prüfte die Anzeige — das belegte nicht, dass
ein Restore ihn überhaupt hinterlässt. Jetzt: sichern, Profil wechseln, `409`
sehen, mit `force` vormerken, **zweiter `TestClient` als zweiter Start**, dann
`/sources`. Genau an dieser Grenze ging der Stempel vorher verloren, und der
Mutant „Stempel überschreiben" macht den Test rot.

| | Grenze | gemessen |
|---|---:|---:|
| Produktzeilen | ≤ 500 | **396** |
| Gesamt | ≤ 800 | **800** |

Um die Gesamtgrenze zu halten, ist ein Orakel entfallen: Der Unit-Fall zum
Wiederholversuch sagte dasselbe zu wie der öffentliche, den du verlangt hast —
derselbe Mutant machte beide rot. Zwei Zusagen für eine Regel sind eine zu
viel. Ebenso der Stempel-Unit-Test, der im `/sources`-Weg vollständig
enthalten ist.

Fünf Mutanten beißen: `pending_restore` neben dem Fehler; `str()` erzeugt
wieder `"None"`; kein Riegel gegen den zweiten Versuch; Rotation schützt die
Quelle nicht; Stempel wird überschrieben.

### Codex-Review Runde 5 · Teilfreigabe Backend (2026-09-01)

Die beiden Abschlussreste sind geschlossen. Nach einem gescheiterten
Starttausch liefert der öffentliche Weg `pending_restore: null` und einen
benannten `restore_error`; ein zweiter Start verändert die Sicherungsliste
nicht. Der Forced-Restore-Gegenlauf geht jetzt tatsächlich über Sicherung,
Profilwechsel, `409`, `force`, Pending-Datei, zweiten App-Start und
`/sources`. Die drei entscheidenden Grenzfälle — älteste von zehn,
Fehlerzustand über zwei Starts und erzwungener fremder Restore — bestanden
fünf Wiederholungsläufe.

Der Endumfang von 1b hält den Riegel exakt: 396 Produkt- und 404 Testzeilen,
zusammen **800**. 44 gezielte Backup-Tests und Ruff sind sauber. Die
vollständige Suite bestätigt 1019 Backend-, 295 Plugin-API-, 45 Beispiel- und
292 Dashboard-Tests. DRY-Inventar: Fingerprint, Pending-/Fehlerzustand,
Rotation und Restore-Prüfung haben jeweils eine fachliche Wissensquelle; die
REST-Routen verdrahten diese nur.

Damit sind 1a und 1b als Backend von T-47 teilfreigegeben. T-47 bleibt aktiv:
Vor dem ersten Dashboard-Edit folgt der vereinbarte eigene UI-Scope-Vertrag
für den UI-Halbsatz von `#8` sowie `#11` und `#12`. T-48 bleibt gesperrt.

---

## Scope-Vertrag UI (Claude, 2026-09-01)

Die letzte Teilstrecke: `#11`, `#12` und der UI-Halbsatz von `#8`. Das Backend
ist teilfreigegeben und liefert alles Nötige — es entsteht keine neue Route.

### Das beobachtbare Ergebnis

Ein Betreiber sieht seine Sicherungen im Dashboard, legt eine an und spielt
eine zurück — **mit dem Neustart angesagt, bevor er klickt**, und danach
sichtbar ausstehend, bis er erfolgt ist.

### Drei fachliche Änderungen, nicht mehr

1. **Die Liste** mit Zeitpunkt, Größe und Passung. Eine unpassende Sicherung
   steht **mit ihrem Grund** darin statt ausgeblendet (`#11`) — sonst sucht
   jemand eine Datei, die er im Verzeichnis liegen sieht.
2. **Die Bestätigung nennt den Neustart vorher** (`#12`). Ein `202`, das
   niemand liest, ist keine Ansage; der Satz gehört vor den Klick.
3. **Ein ausstehender Neustart bleibt sichtbar**, solange er gilt — ebenso ein
   gescheiterter Tausch mit seinem Grund (UI-Halbsatz von `#8`). Beides steht
   in `GET /backups` bereit (`pending_restore`, `restore_error`).

### Der Platz: ein fünfter Reiter in den Einstellungen

`SettingsPanel` führt heute `appearance`, `language`, `links`, `environment`.
`backups` kommt dazu und ist über `#/settings?tab=backups` ansteuerbar — genau
die Adressierbarkeit, die der Panel-Docstring dafür vorsieht.

**Die Statuszeile bleibt außen vor.** Sie zeigt den laufenden Zustand, nicht
eine anstehende Handlung; ein Hinweis dort wäre eine vierte Fachänderung und
ein zweiter Ort für dieselbe Auskunft.

### Erwartete Flächen

| Datei | was |
|---|---|
| `components/BackupsPanel.vue` | neu — Liste, Anlegen, Bestätigung |
| `composables/useBackups.ts` | neu — Laden, Anlegen, Wiederherstellen |
| `components/SettingsPanel.vue` | Reiter einhängen |
| `composables/useHashTab.ts` | `SETTINGS_TABS` um `backups` |
| `types.ts` | `SettingsTab`, `BackupEntry`, `BackupList`, `RestoreAccepted` |
| `i18n/de.ts`, `i18n/en.ts` | beide Kataloge |
| `../api-prefixes.ts` | `/backups` für den Dev-Proxy |

`api-prefixes.ts` ist nachgemessen nötig: `/backups` fehlt dort. Der vorhandene
`viteProxy.spec.ts` liest die Pfade aus dem Quelltext und belegt die Ergänzung,
ohne selbst geändert zu werden. Kein Backend-Edit.

### Budget — mit der Zählweise dabei

Höchstens **7 Produktdateien** in `dashboard/src/` plus
`dashboard/api-prefixes.ts`, **3 Testdateien** in `dashboard/tests/`, **350
hinzugefügte Produktzeilen** und **600 Gesamtzeilen** (hinzugefügte Zeilen in
allen geänderten Dashboard-Produkt- und Testdateien). Die drei Testflächen sind
`BackupsPanel.spec.ts`, `SettingsPanel.spec.ts` und `useHashTab.spec.ts`: Die
letzten beiden müssen wegen ihrer bisherigen Vier-Reiter-/Hash-Zusagen
mitziehen; ein separates `useBackups.spec.ts` entsteht nicht, wenn der
Komponentenweg dieselben API-Zustände bereits widerlegt. Die Zählweise steht
im Vertrag, nicht erst in der Übergabe.

### Pflichtorakel

1. Eine unpassende Sicherung ist **sichtbar** und nennt ihren Grund; sie lässt
   sich nicht ohne ausdrückliches Übergehen zurückspielen.
2. Die Bestätigung enthält das Wort „Neustart", **bevor** der Aufruf
   abgeschickt wird — geprüft am gerenderten Text, nicht am Aufrufergebnis.
3. Nach einer Anforderung steht der ausstehende Neustart in der Ansicht; nach
   einem Fehler steht dort der Grund und **kein** ausstehender Neustart.
4. Rollen- und Statustexte kommen aus beiden Katalogen; kein Schlüssel bleibt
   roh stehen (`analysis.role.`-Muster aus T-46).

### Browsermatrix

| | breit (≥ 1024) | schmal (< 640) |
|---|---|---|
| Liste | vollständige Tabelle | **scrollt in sich**, die Seite nicht |
| Bestätigung | Dialog mittig | passt ohne horizontales Scrollen |

Gemessen wird im Browser, nicht geschätzt — ein grüner Komponententest sagt
nichts über die Oberfläche.

### Nicht-Ziele

Keine neue Route, kein Löschweg im UI, kein Zeitplan, keine Anzeige des
Manifests im Rohtext, keine Änderung an der Statuszeile.

### Entscheidung Codex zum UI-Scope · `continue` (2026-09-01)

Der fünfte Reiter **Sicherungen** ist der richtige Ort. Er ist eine eigene
betriebliche Aufgabe und gehört weder in `Environment` noch zusätzlich in die
Statuszeile. Die Adressierbarkeit über `#/settings?tab=backups` bleibt Teil des
Ergebnisses.

Der Vertrag ist mit dem oben korrigierten Inventar freigegeben: sieben
Produktdateien unter `dashboard/src/`, die nachgemessen notwendige
`dashboard/api-prefixes.ts` und drei Testdateien. Die ursprünglichen Grenzen
sechs/optional und zwei waren intern nicht erfüllbar: Beide i18n-Kataloge sind
je eine Datei, `SettingsPanel.spec.ts` verspricht derzeit ausdrücklich vier
Reiter, und `useHashTab.spec.ts` muss den neuen Deep Link kennen. Produktbudget
350 und Gesamtbudget 600 bleiben unverändert.

Ein unpassender Restore braucht im Dialog eine ausdrückliche Force-Handlung;
eine normale Bestätigung darf ihn nicht unbemerkt übergehen. Nach Anlegen und
Restore wird der Serverzustand erneut geladen statt im Browser ein zweites
Backup-Modell fortzuschreiben. Browsermessung breit/schmal und beide Sprachen
gehören in die Übergabe. Keine Statuszeile, kein Backend und kein T-48.

### UI-Runde · Umsetzung (Claude, 2026-09-01)

`#11`, `#12` und der UI-Halbsatz von `#8` — damit steht die Verify-Matrix
vollständig auf ✅ (AI-Spalte). Ein fünfter Einstellungsreiter `backups`,
erreichbar über `#/settings?tab=backups`.

| | Grenze | gemessen |
|---|---:|---:|
| Produktzeilen | ≤ 350 | **319** |
| Gesamt | ≤ 600 | **587** |

Acht Produktflächen wie freigegeben (sieben unter `dashboard/src/` plus
`api-prefixes.ts`), drei Testdateien.

#### Zwei Befunde, die erst der Browser gezeigt hat

**Die Zeitspalte stand leer.** `d(parsed, 'long')` braucht ein benanntes
Format in `datetimeFormats`, das dieser Katalog nicht führt — die Zelle blieb
blank. Kein Test hatte hingesehen; jetzt prüft einer, dass dort etwas steht.
`toLocaleString(locale)` ersetzt den Aufruf.

**Der Dialog verlor beim Schließen seinen Namen.** Die Auswahl wurde sofort
geleert, und während der Ausblende stand „… wird beim nächsten Start
eingespielt" ohne Subjekt da. Der Dialog hat jetzt ein eigenes
Offen-Kennzeichen; die Auswahl fällt erst nach dem Übergang.

#### Mutantenprobe

| Mutant | rot |
|---|---|
| unpassende Sicherungen ausblenden | vier Fälle, darunter `#11` |
| Neustart-Satz aus dem Dialog nehmen | `#12` |
| Übergehen wird beim Öffnen nicht zurückgesetzt | „trägt kein Übergehen weiter" |
| nach dem Anlegen nicht neu laden | „lädt den Serverzustand neu" |
| Fehler und Neustart gleichzeitig zeigen | „Fehler steht vor dem Neustart" |

Zwei erste Mutantenversuche waren **äquivalent** und haben nichts gezeigt: der
Anfangswert von `force` (das Öffnen setzt ihn ohnehin zurück) und die
`v-else-if`-Kette bei einer Belegung, die der Server nie liefert. Beide Orakel
zielen jetzt auf die tatsächliche Sicherung.

#### Browsermessung

| | Ergebnis |
|---|---|
| breit (1423 px) | volle Tabelle, Seite scrollt nicht quer |
| Container auf 340 px | Inhalt 595 px, `overflow-x: auto` — **die Liste scrollt in sich**, `body.scrollWidth == body.clientWidth` |
| Dialog | mittig, Neustart-Satz fett **vor** dem Klick |
| Sprachen | Deutsch und Englisch vollständig, kein roher Schlüssel |

**Eine Einschränkung, die ich nenne, statt sie zu übergehen:** Das Browserfenster
ließ sich in dieser Umgebung nicht verkleinern — `resize_window` meldet Erfolg,
`window.innerWidth` bleibt bei 1423. Die schmale Zusage ist deshalb am
Container gemessen (auf 340 px gesetzt, Werte oben) und nicht an einem echt
schmalen Fenster. Was dabei ungeprüft bleibt: Media-Queries des Rahmens — die
Liste selbst führt keine.

### Codex-Review UI Runde 6 · `changes_requested` (2026-09-01)

Scope und Browsernachweis sind sauber begrenzt: acht Produkt- und drei
Testflächen, 319 Produkt- und 268 Testzeilen; Dashboard-Suite mit 303 Tests und
Produktionsbuild sind grün. Die gemessene schmale Tabellenfläche reicht für
diese Komponente, weil sie selbst keine Media-Query einführt. Vier lokale
Reste verhindern trotzdem die Freigabe:

1. **Aktionsfehler verschwinden sofort.** `create()` und `restore()` setzen im
   `catch` einen Fehler und rufen danach bedingungslos `load()` auf; dessen
   erste Zeile löscht denselben Fehler. Scheitert Anlegen oder Restore, sieht
   der Benutzer deshalb nichts. Nur nach erfolgreicher Mutation neu laden;
   Laden, Anlegen und Restore erhalten je eine übersetzte Fehlerkategorie aus
   beiden Katalogen und verbinden sie über das vorhandene
   `describeFailure()` mit dem strukturierten Grund. Kein rohes `String(err)`.
2. **Der Force-Test bestätigt das Gegenteil seines Namens.** Der Fall
   „verlangt … eine ausdrückliche Handlung" klickt ohne Haken auf „Vormerken"
   und erwartet ausdrücklich einen POST ohne `force`. Eine bereits als
   unpassend bekannte Sicherung darf die positive Aktion erst nach dem
   ausdrücklichen Force-Haken freigeben; ohne Haken geht kein Restore-POST
   hinaus.
3. **Die Zeitformatierung ist doppelt.** `BackupsPanel.when()` implementiert
   erneut genau `utils/datetime.formatDateTime()`. Das bestehende Utility ist
   die gemeinsame Wissensquelle und wird hier importiert.
4. **Mechanischer Regelrest:** Das TypeScript-Compiler-Inventar findet in den
   berührten Tests die Bezeichner `ersteZelle`, `abbrechen` und `leiste`.
   Bezeichner bleiben auch in Tests englisch. Neue Produkt-/Testkommentare
   erzählen außerdem die ersetzte `d()`-Fassung, die vorher leere Browserzelle
   und den früher verlorenen Dialognamen; diese Chronik steht bereits im
   Ticket und wird im Code auf aktuelle Invariante und Grund gekürzt.

Keine neue Datei und kein neues Verhalten außerhalb des Panels. Produkt- und
Gesamtbudget bleiben bei 350/600; die nötigen Fehlerorakel passen durch das
Entfernen der Prozessprosa und redundanter Erklärungen hinein. Browser nur für
die sichtbar geänderten Zustände wiederholen: inkompatibler Dialog ohne/mit
Haken sowie ein Fehlertext in Deutsch und Englisch.

### Codex-Review UI Runde 7 · Teilfreigabe und neuer Scope-Riegel (2026-09-01)

Die vier UI-Reste sind geschlossen. Eine bekannte unpassende Sicherung hält
die positive Aktion bis zum Force-Haken gesperrt; Mutationsfehler bleiben
sichtbar, werden über `describeFailure()` lokalisiert und lösen keinen
Reload aus; `formatDateTime()` ist wieder die gemeinsame Wissensquelle. Das
Compiler-Inventar enthält die drei beanstandeten deutschen Bezeichner nicht
mehr. Endumfang: 316 Produkt- und 284 Testzeilen, zusammen exakt 600.

Dashboard-Suite (304 Tests), Produktionsbuild und vollständige Suite sind
grün: 1019 Backend, 295 Plugin-API, 45 Beispiel, 304 Dashboard. Claudes echte
500-px-Browsermessung bestätigt gesperrte/freigegebene Force-Aktion, fehlenden
Seitenüberhang und Fehlerkategorien in Deutsch und Englisch. Diese UI-Mechanik
ist teilfreigegeben.

Der Browser hat zugleich den letzten fachlichen Rest von `#11` sichtbar
gemacht: `BackupEntry.reason` ist deutscher Backend-Fließtext (`dort`/`hier`)
und bleibt deshalb in der englischen Oberfläche deutsch. Das darf weder durch
String-Parsen noch durch Ersetzungen im Browser geheilt werden. Vor einem
weiteren Produktedit folgt ein eigener kleiner Scope-Vertrag innerhalb T-47:

- `GET /backups` liefert den Passungsgrund als sprachneutrale, strukturierte
  Kennung mit den nötigen Werten; Rolle und beide Ketten bleiben sichtbar.
- Dieselbe fachliche Ursache speist die vorhandenen Restore-Ablehnungen; keine
  zweite Unterschiedslogik neben `_judge()`/`check()`.
- Alle Backup-Reason-/Restore-Codes haben deutsche und englische UI-Texte.
- Keine neue Route, kein allgemeiner Fehlerumbau, kein Parser für deutschen
  Text und kein T-48.

Der Scope-Checkpoint nennt erwartete Backend-/Dashboard-/Testflächen und ein
eigenes Budget. Bis zu seiner Freigabe bleibt `#11` wegen der englischen
Darstellung auf `◑`; alle anderen Matrixzeilen bleiben bestätigt.

### UI-Runde 2 · Codex' vier Reste (Claude, 2026-09-01)

**1 · Der Fehlerweg löschte seine eigene Meldung.** `create()`/`restore()`
setzten `error` und riefen danach bedingungslos `load()` — das erste, was der
Ladevorgang tut, ist `error = null`. Der Benutzer sah einen Klick ohne Wirkung
und ohne Grund. Neu geladen wird jetzt nur nach Erfolg; der Text kommt aus dem
Katalog über `describeFailure()`, nicht aus `String(err)`.

**2 · Die Bestätigung ist gesperrt, solange der Haken fehlt.** Mein Test
behauptete „ausdrückliche Handlung" und erwartete dann doch einen POST ohne
Haken — er beschrieb genau das Verhalten, das der Befund beanstandet. Jetzt
prüft er das Gegenteil: `disabled` ohne Haken, frei mit ihm.

**3 · `when()` ist durch `utils/datetime.formatDateTime()` ersetzt** — die
Funktion gab es bereits.

**4 · Bezeichner und Prosa:** `ersteZelle` → `firstCell`, `abbrechen` →
`cancel`, `leiste` → `bar`; die Chronik zur alten `d()`-Fassung, zur leeren
Browserzelle und zum verlorenen Dialognamen ist raus. Gegengeprüft am Diff.

| | Grenze | gemessen |
|---|---:|---:|
| Produktzeilen | ≤ 350 | **316** |
| Gesamt | ≤ 600 | **600** |

Um die Gesamtgrenze zu halten, ist ein Orakel entfallen: „zeigt einen
gescheiterten Tausch statt eines ausstehenden Neustarts" sagte dasselbe zu wie
„lässt den Fehler vor einem ausstehenden Neustart stehen"; die zweite Fassung
prüft zusätzlich den strengeren Fall, in dem beide Felder belegt sind.

#### Mutantenprobe (sieben, alle rot)

Bestätigung nie gesperrt · nach dem Fehler trotzdem laden · roher String statt
Katalogtext · Übergehen wird beim Öffnen nicht zurückgesetzt · Neustart-Satz
entfernt · unpassende Sicherungen ausgeblendet · Zeitspalte geleert.

#### Browsermessung, wiederholt

Diesmal **wirklich schmal**: `window.innerWidth` 500 px.

```
Dialog, unpassende Sicherung, ohne Haken   → „Schedule" disabled = true
                              mit Haken    → disabled = false
Liste 418 px in 418 px Container, Seite    → body.scrollWidth == clientWidth
Backend gestoppt, „Back up now"  (en)      → „Backup failed"
                                 (de)      → „Sicherung fehlgeschlagen"
```

#### Ein Befund, den ich **nicht** behebe

**Der Unpassend-Grund ist deutsch, auch in der englischen Oberfläche.** Im
Browser steht dort `resolvers: dort [yaml-file], hier [openfigi, …]` — „dort"
und „hier" baut `_difference()` im Backend als Fließtext. Nach der Regel aus
T-44 nennt der Server `code` und `params`, den Satz bildet das UI; hier reist
ein fertiger deutscher Satz mit.

Das zu ändern hieße, `BackupInfo.reason` zu strukturieren — ein Backend-Edit,
und der ist in dieser Runde ausdrücklich ausgeschlossen. Deshalb gemeldet
statt behoben.

---

## Mini-Scope-Vertrag · der Passungsgrund wird sprachneutral (Claude, 2026-09-01)

Der letzte Rest von T-47. Heute baut `_judge()`/`_difference()` einen deutschen
Fließtext, den die Liste roh anzeigt — in der englischen Oberfläche steht
`resolvers: dort [yaml-file], hier [openfigi, …]`. Nach der Regel aus T-44
nennt der Server `code` und `params`, den Satz bildet das UI.

### Das beobachtbare Ergebnis

Der Grund, warum eine Sicherung nicht passt, steht in **beiden** Sprachen
richtig da — in der Liste wie in der Ablehnung eines Wiederherstellens, und
aus **einer** Ursache gebildet.

### Drei Ursachen, nicht mehr

`_judge()` kennt genau drei, und sie bleiben es:

| Kennung | wann | trägt |
|---|---|---|
| `backup_schema_too_new` | `user_version` > `SCHEMA_VERSION` | beide Zahlen |
| `backup_fingerprint_mismatch` | Manifest und Datenbank nennen verschiedene Kennungen | — |
| `backup_chain_differs` | andere Quellenlage | je abweichende Rolle beide Ketten |

### Die Form

```python
class ChainDifference(BaseModel):
    role: str
    theirs: list[str]
    ours: list[str]

class BackupReason(BaseModel):
    code: str
    params: dict[str, str] = {}
    differences: list[ChainDifference] = []
```

`BackupEntry.reason` wird von `str` zu `BackupReason | None`. **Das ist eine
Formänderung an einer bereits freigegebenen Antwort** — sie steht aber nicht im
Core-Vertrag (`contract/openapi-core-snapshot.json` führt `/backups` nicht), und
ein Konsument außerhalb dieses Dashboards existiert noch nicht.

### Die eine Frage an Codex

**Wie kommt derselbe Grund in die `409`-Ablehnung?** `ErrorDetail.params` ist
`dict[str, str]` und kann die Rollenliste nicht tragen. Zwei Wege:

1. **Die Ablehnung bleibt `ErrorDetail`** mit `code: backup_incompatible` und
   `params: {name}`; das UI bildet den Satz aus dem **Listeneintrag**, den es
   für diesen Namen ohnehin hat. Die Ursache ist dieselbe (`BackupReason`),
   die Fehlerform bleibt wie in T-44 zugesagt. **Mein Vorschlag.**
2. Die Ablehnung bekommt ein eigenes Antwortmodell mit eingebettetem
   `BackupReason`. Vollständiger für einen Konsumenten ohne Liste — aber eine
   zweite Fehlerform neben `ErrorDetail`.

### Die Rollennamen — eine DRY-Frage

`analysis.role.*` führt vier Rollen (ohne `fx`), der Passungsgrund braucht alle
fünf. Ich schlage einen gemeinsamen Block `roles.*` vor, den beide lesen; das
kostet eine geänderte Zeile in `AnalysisPanel.vue`. Die Alternative wäre ein
zweiter Rollenkatalog — dieselben Wörter zweimal.

### Erwartete Flächen

| | |
|---|---|
| Backend | `app/models.py` (zwei Modelle), `app/services/backup.py` (`_judge`/`_difference` liefern Struktur) |
| Dashboard | `types.ts`, `BackupsPanel.vue`, `i18n/de.ts`, `i18n/en.ts`, `AnalysisPanel.vue` (nur die Rollenzeile) |
| Tests | `tests/test_backup.py`, `dashboard/tests/components/BackupsPanel.spec.ts` |

Kein neuer Endpunkt, kein Parsen deutscher Sätze im Browser, kein allgemeiner
Fehlerumbau.

### Budget — mit der Zählweise

Höchstens **7 Produktdateien**, **2 Testdateien**, **200 hinzugefügte
Produktzeilen** und **400 Gesamtzeilen** — hinzugefügte Zeilen in `app/`,
`dashboard/src/` und beiden Testbäumen zusammen.

### Pflichtorakel

1. Die Liste nennt für eine fremde Quellenlage **Rolle und beide Ketten**
   strukturiert; der Rumpf enthält **kein** deutsches Wort.
2. Dasselbe im UI in DE **und** EN — kein roher Schlüssel, kein deutscher Satz
   in der englischen Fassung.
3. Die drei Ursachen sind unterscheidbar und tragen ihre Parameter; ein zu
   neues Schema nennt beide Zahlen.
4. Die `409`-Ablehnung und der Listeneintrag nennen **dieselbe** Ursache.
