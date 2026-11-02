# Sicherheitsprofil

Was in diesem Projekt schutzwürdig ist und welche Grundsatzentscheidungen
gelten. Ein Konzeptticket, das den Aufbau der App berührt, prüft und ergänzt
es. Bei jedem Code-Ticket prüfen Implementer und Reviewer den Diff dagegen
(Guard `security`, Bericht ist Pflicht).
Leere Abschnitte heißen „noch nicht entschieden“; „keine“ ist eine Entscheidung.

Die Abschnitte beschreiben den Stand des Codes mit Fundstelle. Was als
**Offen** markiert ist, hat Mike noch nicht entschieden; der Ist-Stand ist
dort keine Zusage.

## Sensible Daten

- **Zugangsdaten:** nur der optionale OpenFIGI-Schlüssel
  (`openfigi_api_key` in `app/config.py`). Weitere Zugangsdaten hat die App
  nicht.
- **Persönliche Daten:** keine Benutzerkonten, keine Namen oder Adressen.
- **Geschäftsdaten:** die Liste der beobachteten Wertpapiere (ISINs, Symbole,
  Börsen) samt eigenen Detailwerten. Sie verrät, wofür sich der Betreiber
  interessiert, und gilt deshalb als privat. Kurse, Stammdaten und
  Devisenkurse stammen aus öffentlichen Quellen und sind nicht schutzwürdig.
- **Fremder Code:** Plugins aus `data/plugins/*.py` und aus dem Entry-Point
  `stockinfo.sources` laufen im Prozess der App (`app/plugin_loader.py`).

## Speicherorte

- **Datenbank:** SQLite unter `DATABASE_PATH`, Vorgabe `data/stockinfo.db`;
  im Container das Volume `/data`. Der Entrypoint übergibt `/data` an
  PUID/PGID (Vorgabe 99/100) und startet die App ohne Root-Rechte
  (`docker/entrypoint.sh`, `docker/Dockerfile`).
- **Sicherungen:** Kopien der Datenbank neben ihr, höchstens zehn; die elfte
  verdrängt die älteste (`app/services/backup.py`, `app/routers/backups.py`).
- **Quellenkonfiguration:** `sources.yaml` im Daten-Volume. Sie enthält
  Ketten und Reihenfolgen, Schlüssel nur als Verweis `${OPENFIGI_API_KEY}`,
  damit man die Datei weitergeben kann (`app/sources_config.py`).
- **Plugin-Pakete:** `data/plugin-env/<hash>/` (`app/plugin_env.py`).
- **Browser:** im `localStorage` liegt nur die Themenwahl
  (`dashboard/src/composables/useTheme.ts`); keine Cookies.
- **Nie** ins Repository: `.env` und `data/`. **Nie** im Klartext in
  `sources.yaml`, in API-Antworten oder im Browser: der OpenFIGI-Schlüssel.
  Die API meldet nur, ob er gesetzt ist (`openfigi_key_set` in
  `app/routers/dashboard.py`).
- **Offen:** ob der Schlüssel in Logs auftauchen darf, ist nicht festgelegt
  und nicht geprüft.

## Geheimnisse

- Der OpenFIGI-Schlüssel kommt über die Umgebungsvariable
  `OPENFIGI_API_KEY` oder `.env`, gelesen von `pydantic-settings`
  (`app/config.py`). Ohne Schlüssel läuft die App mit niedrigerem
  Rate-Limit.
- Lesen darf ihn der Prozess der App und damit jedes geladene Plugin.
- Agenten lesen `.env` nicht (Regel `sensible-dateien`).

## Anmeldung

- **Keine.** Es gibt keine Benutzer, Sitzungen oder Tokens. Die API lauscht
  per Vorgabe auf `0.0.0.0:8000` (`app/config.py`); auch die schreibenden
  Endpunkte sind offen, darunter Instrumente anlegen, ändern und löschen,
  Aktualisieren, Sicherung anlegen, Sicherung einspielen und
  Migration bestätigen (`app/routers/`).
- CORS erlaubt per Vorgabe nur `http://localhost:5173` (`cors_origins`).
- **Offen:** Die App setzt heute ein vertrauenswürdiges Heimnetz mit einem
  Betreiber voraus. Ob das die Grundsatzentscheidung ist oder eine Anmeldung
  kommen soll, ist nicht entschieden.

## Zugriffe von außen

- **HTTP-API:** ISINs, Symbole, Listing-IDs, Detailwerte und
  Sicherungsnamen. Pydantic-Modelle prüfen die Form. Ein Sicherungsname ist
  ein Name, kein Pfad: `_NAME_PATTERN` in `app/services/backup.py` weist
  Schrägstriche, `..` und absolute Pfade ab.
- **Datenquellen:** Antworten von Yahoo (yfinance), OpenFIGI und weiteren
  Quellen gelten als unzuverlässig, nicht als feindlich. Sie bilden keine
  Pfade oder Befehle.
- **Plugins:** Wer ein Plugin einträgt, vertraut ihm; es läuft mit den
  Rechten der App. `app/plugin_guard.py` fängt Fehler ab und öffnet nach
  drei Fehlschlägen in Folge einen Schutzschalter. Einen hängenden Aufruf
  bricht er nicht ab; das ist eine dokumentierte Grenze.
- **`sources.yaml`:** vom Betreiber geschrieben; `${NAME}` ist die einzige
  Ersetzung, keine Vorlagensprache.

## Ausführung

- **`pip install`** für die in `sources.yaml` genannten Plugin-Pakete
  (`_pip_install` in `app/plugin_env.py`): als Argumentliste ohne Shell,
  Pakete vorher auf `name==version` geprüft (`_PIN` in
  `app/sources_config.py`), nur Wheels (`--only-binary=:all:`), Constraint
  auf die installierte `stockinfo-plugin-api`, mit Zeitgrenze und
  `check=True`.
- **Plugin-Import** beim Start; ein fehlerhaftes Modul wird gemeldet und
  übersprungen (`app/plugin_loader.py`).
- **Entrypoint:** startet als root, prüft PUID/PGID und gibt die Rechte per
  `setpriv` ab, bevor die App startet (`docker/entrypoint.sh`).
- Weitere fremde Befehle startet die App nicht.
