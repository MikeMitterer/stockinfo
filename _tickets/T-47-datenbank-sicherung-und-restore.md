# T-47 · Sicherung und Wiederherstellung der Datenbank

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | Vorschlag, **Codex-Freigabe offen** | 1 Tag | Datenbanksicherung mit Zeitstempel, Liste und Wiederherstellung über REST | — |

- **Angelegt:** 2026-08-31, aus Mikes Frage nach einer Sicherung aus dem UI
- **Richtung von Mike festgelegt (2026-08-31):** *„Das mit dem YAML-Backup ist
  zu kompliziert. Also nur DB-Backup mit Datumstempel usw. in ein
  Unterverzeichnis des DATA-Verzeichnisses. Restore kann auch einen Neustart
  der App verlangen. Backup und Restore sollen auch eine Restschnittstelle
  haben. Über REST soll es auch möglich sein die verfügbaren Restore-Files zu
  listen. Was noch sichergestellt werden muss ist dass Backup und Restore
  nicht durcheinander kommen mit den jeweiligen Plugin-Varianten."*
- **Reihenfolge:** nicht eingeplant. Erst nach Codex' Freigabe des Entwurfs
- **Nicht zu verwechseln mit T-25:** Dort geht es um die **Rotation** eines
  Quellenprofils. Die Kennung, die hier eine Sicherung ihrer Quellenlage
  zuordnet, ist aber **dieselbe**, die T-25 als Kompatibilitäts-ID braucht —
  sie sollte einmal entstehen, nicht zweimal

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
   unmittelbar vor einem Wiederherstellen. Diese eine Ausnahme bleibt: Wer
   zurückspielt, verliert sonst genau den Stand, den er vielleicht gleich
   vermisst. Sie zählt in die zehn hinein.
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

## Auflösung

_(offen — zuerst Codex' Antwort auf die beiden Fragen, dann Mikes zwei
Entscheidungen)_
