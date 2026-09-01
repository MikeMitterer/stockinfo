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

Legende: ✅ live bestätigt · ➖ nicht geprüft.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | `POST /backups` während eines Schreibzugriffs | die Datei ist in sich stimmig, nicht zerrissen | ➖ | |
| **2** | `GET /backups` | Zeitpunkt, Kennung und `compatible` je Eintrag; die Liste stimmt mit dem Verzeichnis überein | ➖ | |
| **3** | Wiederherstellen mit **gleicher** Kennung | derselbe Bestand nach dem Neustart | ➖ | |
| **4** | Wiederherstellen mit **anderer** Kennung | abgelehnt, und die Meldung nennt die Rolle und beide Ketten | ➖ | |
| **5** | dasselbe mit `force` | läuft, und die Instanz sagt danach sichtbar, dass sie es getan hat | ➖ | |
| **6** | Sicherung mit neuerem Schema | abgelehnt, auch mit `force` | ➖ | |
| **7** | vor dem Wiederherstellen | eine Sicherung des alten Standes liegt vor | ➖ | |
| **8** | Absicht hinterlegt, App startet nicht neu | die laufende Datenbank ist unverändert, und das UI sagt, dass ein Neustart aussteht | ➖ | |
| **9** | `PRAGMA user_version` | ist gesetzt und wird beim Prüfen gelesen | ➖ | |
| **10** | elfte Sicherung | die älteste ist weg, es liegen zehn; keine zweite Löschmöglichkeit | ➖ | |
| **11** | UI-Liste | alle vorhandenen Sicherungen sind sichtbar, unpassende **mit Grund** statt ausgeblendet | ➖ | |
| **12** | Bestätigung vor dem Wiederherstellen | der Neustart wird **vorher** genannt, nicht erst danach | ➖ | |

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

_(offen — Scope-Checkpoint liegt bei Codex)_
