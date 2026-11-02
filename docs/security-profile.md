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

- **Zugangsdaten:** der optionale OpenFIGI-Schlüssel (`openfigi_api_key` in
  `app/config.py`) und jeder Wert, den ein Abschnitt unter `providers` in
  `sources.yaml` einer Quelle mitgibt, etwa der Schlüssel eines Plugins, ob
  im Klartext oder als `${NAME}` aus der Umgebung (siehe
  [Geheimnisse](#geheimnisse)).
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
- **Quellenkonfiguration:** `sources.yaml` im Daten-Volume, mit Ketten,
  Reihenfolgen und je Quelle einem Abschnitt unter `providers`. Ein Wert dort
  wird im Klartext angenommen: `_resolve` ersetzt nur einen Wert der Form
  `${NAME}` und gibt jeden anderen Text unverändert weiter
  (`app/sources_config.py:146-161`). Dass Schlüssel nur als Verweis wie
  `${OPENFIGI_API_KEY}` dort stehen, damit man die Datei weitergeben kann, ist
  eine Konvention aus dem Modulkopf (`app/sources_config.py:12-15`), keine
  Prüfung.
- **Offen:** ob ein Schlüssel im Klartext in `sources.yaml` abgewiesen werden
  soll.
- **Plugin-Pakete:** `data/plugin-env/<hash>/` (`app/plugin_env.py`).
- **Browser:** drei Einträge im `localStorage`, alle über `safeStorage` aus
  ux-foundation: `stockinfo-theme` mit der Themenwahl
  (`dashboard/src/composables/useTheme.ts:22`), `stockinfo-sort` mit Spalte
  und Richtung der Tabellensortierung
  (`dashboard/src/composables/useTableSort.ts:22`) und `stockinfo-lang` mit
  der Sprache (`dashboard/src/i18n/index.ts:21`, geschrieben über
  `persistLocale`). Keine Cookies, weder im Dashboard noch vom Backend; kein
  `sessionStorage`, kein IndexedDB, kein Cache-Speicher, kein Service Worker.
  ux-foundation selbst greift nur über `safeStorage` auf den Speicher zu.
- **Repository:** `.env` und `data/` stehen in `.gitignore`.
- **API-Antworten:** Kein Endpunkt gibt einen Schlüssel oder einen
  `providers`-Abschnitt aus. `GET /env` meldet nur, ob der OpenFIGI-Schlüssel
  gesetzt ist (`openfigi_key_set`); `GET /sources` nennt je Quelle Name,
  Rolle, Rang, Datenversion, ob sie arbeiten kann, einen Grund und die
  Kostenart, nicht
  ihren Abschnitt (`app/routers/dashboard.py`, `SourceEntry` in
  `app/models.py:785`).
- **Logs:** Kein Log-Aufruf der App übergibt Header, Schlüssel oder den
  Inhalt eines `providers`-Abschnitts. Belegt ist das mit einem
  `ast`-Inventar aller Argumente der 104 Log-Aufrufe in `app/`. Aus der
  Konfiguration erscheinen nur `database_path`, `strict_exchange` und die
  Namen von Rollen und Abschnitten (`sources_config_loaded`,
  `app/sources_config.py:265`). Der OpenFIGI-Schlüssel geht im Header
  `X-OPENFIGI-APIKEY` hinaus, nicht in der URL
  (`app/providers/openfigi_provider.py:148-150`). Tracebacks enthalten keine
  lokalen Variablen: structlog läuft unkonfiguriert, `rich` ist nicht
  installiert.
- **Lücke bei den Logs:** 22 Aufrufe übernehmen den Text einer Ausnahme
  wörtlich (`error=str(exc)` und ähnliche), darunter `source_raised` im
  Plugin-Guard (`app/plugin_guard.py:240-244`). Schreibt eine Quelle oder ein
  Plugin seinen Schlüssel in eine Ausnahme, steht er im Log.
- **Offen:** ob Logs Schlüssel aktiv herausfiltern sollen, statt sich darauf
  zu verlassen, dass keiner hineingeschrieben wird.

## Geheimnisse

- Der OpenFIGI-Schlüssel kommt über die Umgebungsvariable
  `OPENFIGI_API_KEY` oder `.env`, gelesen von `pydantic-settings`
  (`app/config.py`). Ohne Schlüssel läuft die App mit niedrigerem
  Rate-Limit.
- **Welcher Wert welche Quelle erreicht:** Jede Quelle bekommt nur ihren
  eigenen Abschnitt unter `providers`, nicht die Einstellungen der App und
  nicht die Abschnitte der anderen (`config_for`,
  `app/sources_config.py:93-111`). Ein `${NAME}` darin löst gegen alle
  Text-Einstellungen aus `Settings` und gegen die gesamte Prozessumgebung auf;
  ein echter Umgebungseintrag gewinnt (`environment_from`,
  `app/sources_config.py:114-143`). Die eingebaute OpenFIGI-Quelle nimmt
  ohne eigenen `api_key` den Schlüssel aus den Einstellungen
  (`app/sources_registry.py:144-147`).
- **Folge:** Eine `sources.yaml`, die jemand übernimmt, etwa aus einem Issue,
  kann über `${NAME}` jede Umgebungsvariable des Prozesses in den Abschnitt
  einer Quelle oder eines Plugins leiten.
- **Offen:** ob `${NAME}` auf eine erlaubte Liste von Namen beschränkt werden
  soll.
- Lesen kann den Schlüssel der Prozess der App und damit auch jedes geladene
  Plugin: Es läuft im selben Prozess und erreicht `os.environ` ohnehin.
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
- **`sources.yaml`:** vom Betreiber geschrieben oder von ihm übernommen; die
  App vertraut dem Inhalt. `${NAME}` ist die einzige Ersetzung, keine
  Vorlagensprache, darf aber jede Umgebungsvariable nennen (siehe
  [Geheimnisse](#geheimnisse)). Paketnamen unter `plugins.packages` müssen die
  Form `name==version` haben (`_PIN`, `app/sources_config.py:190`), sonst
  werden sie abgewiesen.

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
