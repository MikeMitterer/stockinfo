# T-25 · Plugin-Datenkompatibilität und Migration

**Der Plugin-Autor erklärt die Datenkompatibilität und liefert die Migration.**
StockInfo leitet sie weder aus Paketversionen noch aus einem Hash der
Quellenkonfiguration ab. StockInfo sichert den Bestand und kontrolliert den
Migrationsaufruf. Diese Richtung ist von Mike am 2026-09-07 bestätigt;
die erste Umsetzung (`data_version` und Backup-Prüfung) steht im Abschnitt unten.

## Umgesetzt · data_version, 2026-09-07

Mike: „T-21 Fehlertext klären wir gleich, T-25 - führe zumindest die angesprochene data_version ein. Das ist die einzige Zahl das ein Backup inkompatibel machen kann.“

Der beauftragte Teil ist implementiert: `Source.data_version` ist eine positive
Ganzzahl mit Standard `1`; der Loader und das Plugin-Testharness prüfen die
Deklaration. `GET /sources` liefert sie je Quelle. Plugin-Namen ordnen die
Werte zu; Rollenreihenfolge, Paketpins und Profilname sind keine fachlichen
Ablehnungsgründe mehr. Nur unterschiedliche Datenversionen aktiver Quellen
führen zu `backup_data_version_differ`. Entfernte Quellen werden nicht
verglichen. Neue Quellen mit Stand 1 passen; bei einem anderen Stand greift
der Vergleich gegen die bisherige implizite 1.

Der verwendete Stand liegt in `meta.plugin_data_versions` in der DB und ihrer
Sicherung sowie informativ im Manifest. Alte Backups ohne Marker gelten als
Stand 1. Neue Datenbanken übernehmen die Deklaration; vorhandene Werte werden
bei einem Plugin-Update nicht überschrieben. Ein Backup ohne Manifest bleibt
prüfbar. Der Quellen-Fingerprint bleibt Herkunftsinformation; beim Sichern
wird die tatsächliche DB-Herkunft ins Manifest übernommen.

Technische Lesbarkeit (`backup_schema_too_new`) und die Integritätsprüfung
zwischen Manifest und Datenbank bleiben getrennte Fehlerfälle. `force` ist
weiter der bestehende ausdrückliche Restore-Override. Kein Plugin-Update führt
allein zur Rotation oder Migration. Die neue Zahl sperrt **Backups**, noch
nicht automatisch den Betrieb einer aktualisierten Quelle auf dem vorhandenen
Bestand: Migrationsausführung und Betriebssperre bleiben im Folgeumfang.

### Verifikation des beauftragten Teils

- 13 gezielte Tests: Paket-/Kettenwechsel, Datenversionswechsel, fehlendes
  Manifest, Altbackup, unveränderter DB-Stempel, frische DB, ungültige Werte
  sowie Datei-Plugin → Loader → REST → Restore-Anforderung → echter zweiter
  App-Lifespan mit geänderter Deklaration. Der zweite Start prüft neu und
  lehnt den vorgemerkten Restore ab. Keine Online- oder Docker-Verifikation.
- Frischer Backendlauf: **1087 bestanden, 29 übersprungen, 8 Online-Tests
  abgewählt**. Plugin-API und Beispielplugin: **356 bestanden, 1 übersprungen**.
- Backup-UI: **14 Tests bestanden**, einschließlich DE/EN mit Plugin-Namen und
  beiden Datenständen. `vue-tsc` und Ruff bestanden.
- Dashboard-Gesamtlauf vor den zwei neuen UI-Tests: **334 bestanden, 1 Fehler**.
  Vorbestehender CSS-Befund: `tests/componentStyles.spec.ts` beanstandet
  `DetailEditor.vue`, `.detail-editor__text { min-width: ... }`.
  Beide Dateien sind gegenüber dem Ausgangscommit unverändert. Kein grüner
  Gesamtlauf behauptet; der Befund gehört nicht zur Datenkompatibilität.

```bash
# M1 und Datenversionsvergleich; noch keine Migrationsabnahme M2–M5
.venv/bin/pytest -q tests/test_backup_data_version.py tests/test_backup.py
# Backend: frischer Datenpfad, keine echte externe API
TASK_DATA_DIR=$(mktemp -d /tmp/stockinfo-t25-verify.XXXXXX)
env DATABASE_PATH="$TASK_DATA_DIR/stockinfo.db" .venv/bin/pytest -q -m 'not integration'
# Plugin-Vertrag und Beispielplugin
PYTHONPATH=plugin_api/src:plugin_api/examples/us-example/src .venv/bin/pytest -q plugin_api/tests plugin_api/examples/us-example/tests
# Datenversionsgrund im UI
npm --prefix dashboard test -- tests/components/BackupsPanel.spec.ts
./dashboard/node_modules/.bin/vue-tsc -b dashboard/tsconfig.json
```

Die bisherige Richtung unten bleibt der Folgeumfang. Der aktuelle Teil ist
keine Implementierung des gesamten Migrationssystems und keine unabhängige
Agentenfreigabe. T-25 bleibt für diese Restarbeit offen.

## Für dich

Aktuell kein Handgriff nötig. Der beauftragte Teil ist implementiert und
geprüft. Für den Folgeumfang sind Migrationseinstieg und Fehlerverhalten
noch zu entwerfen; keine unabhängige Abnahme läuft.

### Bisherige Antworten und Rückmeldungen

Mike, 2026-09-07:

> Wenn wir diese Automatismen, die sehr komplex sind, einfach dem Plugin-Autor überlassen? Er soll ein Flag setzen, das die DB inkompatibel zum Vorgänger macht. Der Plugin-Author muss für die DB-Migration sorgen in dem ein von ihm bereitgestelltest Script oder so läuft

Auf den Vorschlag einer Datenkompatibilitäts-Version (`data_version`) statt
eines booleschen Flags, einer vom Plugin bereitgestellten Migration und eines
gesicherten Aufrufs durch StockInfo antwortete Mike: **„Passt“**.

Damit ist die Richtung entschieden; die genaue Schnittstelle ist noch nicht
implementiert. Die früher diskutierte Major-Versionsregel wird nicht verfolgt.

## Umsetzung und technische Nachweise

### Beschlossener Ablauf

1. Jedes Plugin deklariert seine Datenkompatibilitäts-Version; StockInfo
   speichert den verwendeten Stand je Plugin. `data_version` ist jetzt als
   additive Deklaration implementiert.
2. Bei unverändertem Stand braucht ein Paketupdate keine Datenmigration.
3. Bei verändertem Stand muss das Plugin einen passenden Migrationsweg vom
   gespeicherten zum neuen Stand bereitstellen. Übersprungene Paketversionen
   müssen berücksichtigt werden; ein Flag „zum Vorgänger inkompatibel“ genügt
   deshalb nicht.
4. StockInfo sichert vor der Migration und ruft einen einheitlichen
   Migrationseinstieg des Plugins auf.
5. Erst nach erfolgreicher Migration darf der neue Plugin-Stand den Bestand
   verwenden. Fehlt ein passender Weg oder scheitert die Migration, bleibt
   diese Verwendung gesperrt. Der Bestand muss wiederherstellbar bleiben.

Das Plugin verantwortet seine Datenumwandlung. Das gemeinsame StockInfo-Schema
bleibt Verantwortung des Hosts; eine Migration darf nicht beliebig die von
anderen Plugins verwendeten Tabellen verändern. Wie diese Grenze technisch
durchgesetzt wird, gehört zum Schnittstellenentwurf.

### Was dadurch entfällt und was noch zu klären ist

Die bisherige automatische Entscheidung über Dateninkompatibilität anhand von
Paketpins, Rollenketten oder Major-Versionen entfällt. Es wird auch keine
frische Datenbank allein wegen eines solchen Vergleichs angelegt. Der
bestehende Konfigurations-Fingerprint kann Herkunft dokumentieren, ist aber
kein Ersatz für die deklarierte Datenkompatibilität.

Der alte Rotationsentwurf samt Last-known-good-Plugin-Umgebung und siebenstufiger
Crash-Matrix wird nicht unverändert als Implementierungsauftrag übernommen.
Backup und Schutz vor einer halbfertigen Migration bleiben erforderlich.
T-23 liefert keinen Preflight: Dieser wurde dort ausdrücklich gestrichen.

Vor Umsetzung sind Plugin-Identifikation, Speicherung der Versionsstände,
Migrationsparameter und erlaubte Schreibzugriffe sowie das atomare Abschließen
oder Wiederherstellen bei einem Fehler festzulegen. Auch die Behandlung alter
Datenbanken ohne gespeicherten Plugin-Stand benötigt eine ausdrückliche Regel;
sie darf weder Kompatibilität raten noch Daten verwerfen.

Die Erkennung einer neuen Datenbankgeneration durch StockPortfolio ist davon
fachlich unabhängig. `generation_id` ist weiterhin nicht implementiert und im
aktuellen Core-Artefakt unter `planned.generation_runtime` als noch nicht
zugesagt gekennzeichnet. Die heutige Zustimmung erledigt oder verwirft diese
Restanforderung nicht. Ihre Einplanung sowie die alte Forderung nach
fortlaufenden Backupnummern sind bei der weiteren Eingrenzung separat zu klären.

### Befund vor der Umsetzung · Historie

`app/services/backup.py`, `fingerprint_of`, berücksichtigt momentan Rollenketten
und exakte Paketpins. Beim geprüften Wechsel `example-source==1.0.0` auf
`example-source==1.0.1` änderte sich die Kennung von `daf2bd492e20` auf
`9ae973ee1a4c`. `BackupService._judge` meldet bei abweichender Kennung
`backup_sources_differ`. Ein Profilname allein geht dagegen nicht in den Hash
ein. Die gewünschte Datenkompatibilitäts-Erklärung ist noch nicht vorhanden.

### Verify · neuer Umfang

Neue Kennungen M1–M5 unterscheiden diese Kriterien von der alten Matrix.
Legende: ➖ keine Live-Verifikation. Prüfläufe müssen eigene temporäre Daten
und kontrollierte Testplugins verwenden; keine Produktionsmigration zum Testen.

| # | Aktion | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| M1 | Paketversion ändern, Datenkompatibilitäts-Version beibehalten | Keine Migration und keine Ablehnung allein wegen des Paket-Bumps | ➖ |
| M2 | Datenkompatibilitäts-Version mit passender Migration ändern | Sicherung vor erstem Schreibzugriff; neue Daten und Versionsstand erst nach Erfolg verwendbar | ➖ |
| M3 | Mehrere Paketstände überspringen oder passende Migration weglassen | Passender Weg vom tatsächlich gespeicherten Stand; andernfalls keine Nutzung durch den neuen Plugin-Stand | ➖ |
| M4 | Migration mit Fehler oder Prozessabbruch beenden | Kein als erfolgreich markierter Teilstand; Bestand konsistent wiederherstellbar | ➖ |
| M5 | Migration mit Daten anderer Plugins und gemeinsamem Schema prüfen | Nur erlaubte Daten betroffen; gemeinsames Schema und fremde Daten geschützt | ➖ |

Dies ist eine beschlossene Richtung mit prüfbaren Kernanforderungen, noch kein
vollständiger Implementierungsplan. Alte AI-Nachweise und leere Human-Felder
bleiben unverändert in der Historie; sie bestätigen die neue Migration nicht.

### Side-Effects

Heute nur Ticketänderung. Keine Plugin-Installation, Migration, Sicherung oder
Datenbankrotation ausgeführt. Der spätere Vertrag betrifft Plugin-API und Host;
eine Paketversionsänderung allein soll keine Datenumwandlung auslösen.

### Auflösung

Teilweise umgesetzt: `data_version` und Backup-Kompatibilitätsprüfung sind
auf Mikes Auftrag implementiert. Der Migrationseinstieg und seine sichere
Ausführung fehlen weiterhin. STATUS-Rollen und Prioritätskette bleiben unverändert.

## Frühere Anforderungen und Prüfungen · Historie

Die folgende Fassung bleibt als vollständiger Nachweis der früheren Kriterien,
Antworten und Prüfungen erhalten. Ihr Rotationsauftrag, die T-23-Abhängigkeit
und die Behauptung eines bereits zugesagten Generation-Vertrags sind durch
die aktuelle Einordnung oben überholt; sie sind keine neuen Arbeitsaufträge.

<details>
<summary>Bisheriger Rotationsentwurf und Claudes Prüfstand vom 2026-09-07</summary>

# T-25 · Quellenprofil wechseln — Sicherung und frische Datenbank

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | offen — Sicherung steht, `generation_id` fehlt | 1 Tag | Profilbegriff, Sicherung, Rotation, Wiederherstellung | — |

**Löst:** Ein **Quellenprofil** ist die Gesamtheit der aktiven Quellen einer
Instanz. Profil A durch B zu ersetzen ist etwas anderes, als innerhalb von A
eine Quelle zu ergänzen — und dieser Unterschied fehlt im Entwurf bisher ganz.

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

> **Von Mike bestätigt (2026-08-20)**, im Wortlaut über Codex' Kanal:
> „Plugin B ersetzt Plugin A. Die Datenbank von A wird nach einem normalen,
> fortlaufend nummerierten Backup-Schema gesichert; B verwendet eine frische
> Datenbank. Kanada kann Profil B, Russland C und Österreich/Deutschland A
> verwenden." Der frühere Vorbehalt „nur aus zweiter Hand" ist damit erledigt.

**Hängt an:** T-22 (ohne Profil gibt es nichts zu wechseln), **T-24**
(`generation_id` gehört zum REST-Vertrag) **und T-23** (liefert den
programmatischen Preflight, den die Rotation wiederverwendet).
**Nicht zu verwechseln mit T-19**, das ein einzelnes Papier neu auflöst.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise ·
➖ ausschließlich automatisierte Tests/Review, keine Live-Verifikation ·
❌ gemessen und **nicht** erfüllt.

Die `AI`-Spalte trägt den von Claude am 2026-09-07 gemessenen Stand; die
Messungen stehen unter [Prüfstand 2026-09-07](#prüfstand-2026-09-07).
Die `Human`-Spalte bleibt leer — dieses Ticket hatte noch keine Abnahme.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Quelle **innerhalb** desselben Profils ergänzen, **Kompatibilitäts-ID unverändert** | bestehende Instrumente unverändert, **dieselbe** Datenbank | ❌ | |
| 2 | Paketversion anheben, **Kompatibilitäts-ID unverändert** | dito — kein Datenbankwechsel | ❌ | |
| 2b | Profilname gleich, aber **Kompatibilitäts-ID erhöht** (z.B. adjusted → unadjusted) | gilt als neue Generation, **frische** Datenbank | ❌ | |
| 3 | Profil A durch B ersetzen | **erst B vollständig validieren**, dann A sichern, dann wechseln | ❌ | |
| 3b | B mit fehlendem Wheel / Syntaxfehler / fehlendem Pflicht-Key | Rotation findet **nicht** statt; A bleibt aktiv, keine leere neue DB | ❌ | |
| 4 | nach #3 | B läuft auf einer **frischen** Datenbank | ❌ | |
| 4b | Sicherung läuft, gleichzeitig ein API-Schreibzugriff | Sicherung ist trotzdem konsistent | ➖ | |
| 5 | Sicherungsverzeichnis | fortlaufend nummeriert, mit Manifest: Profil, Stand, Zeitpunkt | ⚠️ | |
| 5b | **Crash-Matrix**: **sieben** injizierbare Fehlerpunkte, je Punkt Neustart und Recovery | nach jedem: genau **eine** vollständige Generation aktiv, keine Nummer überschrieben, nie B mit As Datenbank, A vollständig startbar | ❌ | |
| 5d | derselbe Preflight wie T-23 vor jeder Rotation | identische Logik, keine zweite Validierung — **Abnahme hier**, bereitgestellt in T-23 | ❌ | |
| 5c | B ungültig, Neustart | A läuft wieder **vollständig** — Konfiguration *und* Plugin-Umgebung, nicht nur die alte Datenbank | ❌ | |
| 6 | Wiederherstellung | ordnet Sicherung und Profil einander zu; ein unpassendes Paar wird abgelehnt | ➖ | |
| 6b | dieselbe Sicherung zweimal einspielen | jede Aktivierung bekommt eine **neue** `generation_id` | ❌ | |
| 7 | **Route** `GET /generation` läuft | liefert die aktive `generation_id` mit `Cache-Control: no-store` | ❌ | |
| 7b | Prozessneustart **ohne** Profilwechsel | dieselbe `generation_id` | ❌ | |
| 7c | verträgliche Konfigurationsänderung (Schlüssel, Zeitgrenze) | dieselbe `generation_id` | ❌ | |
| 7d | Profilwechsel **und** jede Restore-Aktivierung | **neue** `generation_id` | ❌ | |
| 7e | Harness-Stufe 2 | `/generation` und der Antwort-Header laufen im Integrationslauf mit — Erfolgs- **und** Fehlerantworten | ❌ | |
| 7g | **Middleware** | setzt `StockInfo-Generation` auf **jeder** Antwort, auch `404`/`409`/`422`/`502` | ❌ | |
| 7h | `app/main.py` CORS | `expose_headers` enthält `StockInfo-Generation` — cross-origin im Browser lesbar | ❌ | |
| 7i | Profilwechsel **während** eines laufenden Requests | Header und Rumpf stammen aus **derselben** Generation — Kontext am Requestanfang gebunden | ❌ | |
| 7j | **Live-OpenAPI der laufenden App** gegen das statische Vertragsartefakt aus T-24 | Route, Headername und Schema stimmen überein — hier die Konformität, in T-24 nur die Definition | ❌ | |

**Nicht abschlussrelevant — Cross-Repo-Nachweis:** Die folgenden Zeilen werden
**in StockPortfolio T-35 abgenommen** und blockieren den Abschluss von T-25
nicht. Sie stehen hier nur, damit der Zusammenhang sichtbar bleibt.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 8 | **StockPortfolio** nach Profilwechsel → **T-35 `#4`** | schaltet den sichtbaren Quote-/History-**Namespace** um; keine Werte der alten Generation sichtbar; Portfolio, Stückzahlen und Ziele bleiben | ➖ | — |
| 8b | dasselbe ohne Profilwechsel → **T-35 `#7`** | Cache bleibt — die Generation ändert sich nicht bei jeder Konfigänderung | ➖ | — |

---

<a id="prüfstand-2026-09-07"></a>

## Prüfstand 2026-09-07 · gemessen von Claude

Auftrag von Mike: „T-25 sollte erledigt sein. Das Script gibt es — check das
aber nochmal." Ergebnis: **T-25 ist nicht erledigt.** Das Ticket zerfällt in
zwei Hälften, von denen nur die erste gebaut ist. Keine Zeile wurde dabei
geändert oder abgeschwächt; die Messungen stehen unten mit ihrem Kommando.

### Das vorhandene Script ist ein Umschalter, keine Rotation

`scripts/sources-profile.sh` tauscht `sources.yaml` zwischen der Online-Kette
und dem YAML-Plugin und sichert die vorige Fassung. Das ist nützlich, aber es
ist nicht die Rotation aus `#3`: Es validiert B nicht vorab und legt keine
frische Datenbank an. Deshalb bleiben `#3`, `#3b` und `#4` offen. In `app/`
gibt es keinen Rotationsweg — auch keinen Preflight vor einer Rotation
(`#5d`) und keine Crash-Matrix (`#5b`, `#5c`).

### Sicherung und Wiederherstellung sind weitgehend gebaut

`app/services/backup.py`, `app/routers/backups.py` und `apply_pending` beim
Start decken Anlegen, Listen, Wiederherstellen, Manifest, Aufbewahrung von zehn
Ständen und die Ablehnung fremder Sicherungen ab. `VACUUM INTO` sichert gegen
laufende Schreiber, und `test_eine_sicherung_entsteht_waehrend_geschrieben_wird`
belegt `#4b`. 55 Tests in `tests/test_backup.py` und
`tests/test_sources_profile_script.py` sind grün.

`#5` bleibt trotzdem `⚠️`: Das Manifest ist da, die geforderte **fortlaufende
Nummer** nicht. Die Sicherung heißt `stockinfo-<Zeitstempel>-<Kennung>.db`.
Der Zeitstempel ist kollisionsfrei und monoton und damit praktisch gleichwertig
— aber er ist keine fortlaufende Nummer. Hier gehen Ticket und Umsetzung
auseinander; eines von beidem muss nachziehen.

### Die Kompatibilitäts-ID ist ein Hash und trifft die drei Fälle nicht

`fingerprint_of` bildet SHA-256 über Rollenketten und Paketliste. Das Ticket
schließt genau das aus („kein Hash über die Datei"); der deklarierte
`profile`-Name geht überhaupt nicht ein. Gemessen:

```
Referenz                    cb3dcfb403a8
#1  Quelle ergänzt          73f4e800eb41   → verändert, verlangt: unverändert
#2  Paketversion 1.0.0→1.0.1 04a885533e50  → verändert, verlangt: unverändert
#2b anderer Profilname a→b  cb3dcfb403a8   → unverändert, verlangt: neue Generation
    Zeitgrenze 10→30        cb3dcfb403a8   → unverändert, wie verlangt
```

Nur der Konfigurationsfall trifft zu. Die praktische Folge von `#2`: Nach einem
Patch-Bump meldet `BackupService._judge` für **alle** vorhandenen Sicherungen
`backup_sources_differ`, und `request_restore` lehnt sie ohne `force` ab. Der
Bestand wird dabei nicht gelöscht — die Datenbank wird nie von selbst getauscht
—, aber die Sicherungen sind ohne Zwang nicht mehr einspielbar.

### `generation_id` ist gar nicht gebaut — und der Vertrag verspricht sie

Neun Zeilen (`#7` bis `#7j`) und `#6b` hängen daran. Gemessen an einer frisch
gestarteten Instanz:

```
GET /generation               -> 404
StockInfo-Generation (/health) -> Header fehlt
expose_headers in app/main.py  -> nicht vorhanden
```

Das ist keine bloße Lücke, sondern eine **Abweichung vom veröffentlichten
Vertrag**. `contract/core-contract.json` deklariert bereits:

```json
"endpoint": "/generation", "header": "StockInfo-Generation",
"cache_control": "no-store", "required_on_every_response": true,
"expose_headers_required": true
```

Dazu liegen zwei Fixtures: `generation-200.json` als konformes Beispiel und
`generation-200-header-widerspricht-rumpf.json` als absichtlich vertragswidriges
— Header und Rumpf nennen verschiedene Generationen. Das Negativbeispiel prüft
nicht StockInfo, sondern die Erkennungslogik des Konsumenten StockPortfolio.
Beide beschreiben einen Endpunkt, den es nicht gibt. Genau diese Konformität
sollte `#7j` abnehmen.

T-26 hat den Punkt ausdrücklich stehen lassen: „T-25s allgemeine
Generation-/Header-Laufzeit bleibt offen."

### Nicht geprüft

`#5b` (Crash-Matrix mit sieben Fehlerpunkten) und `#5d` (Preflight aus T-23)
habe ich nicht ausgeführt — es gibt keine Rotation, gegen die sie liefen. Sie
stehen auf `❌`, weil das Geforderte fehlt, nicht weil ein Lauf fehlgeschlagen
wäre. Alle Browser- und Human-Zeilen bleiben unberührt.

```bash
# Route und Header an einer frischen Instanz
FRESH=$(mktemp -d); env DATABASE_PATH="$FRESH/stockinfo.db" .venv/bin/python -c "
from fastapi.testclient import TestClient; from app.main import app
with TestClient(app) as client:
    print(client.get('/health').headers.get('StockInfo-Generation', 'FEHLT'))
    print(client.get('/generation').status_code)"
# Sicherung und Wiederherstellung
.venv/bin/pytest -q tests/test_backup.py tests/test_sources_profile_script.py
```

---

## Details

### Zwei Vorgänge, die man nicht verwechseln darf

| Vorgang | Bestehende Instrumente | Datenbank |
|---|---|---|
| Quelle ergänzen/aktualisieren (in A) | unverändert | bleibt |
| Profil A → B | — | **frisch**, A wird gesichert |

Erst diese Trennung bringt zwei Invarianten widerspruchsfrei zusammen:

- „Eine Installation verändert nichts von selbst" (Voraussetzung dafür, dass
  T-19 nachrangig sein darf)
- „B ersetzt A mit frischer Datenbank"

### Erst validieren, dann rotieren

Die Reihenfolge ist nicht beliebig:

1. B installieren
2. **alles prüfen** — Plugin-Importe, Vertragsversionen, Pflichtkonfiguration,
   sind alle Rollen besetzt
3. erst dann A sichern und die aktive Datenbank wechseln

Ein nicht verfügbares Wheel, ein Syntaxfehler oder ein fehlender Pflichtschlüssel
darf weder eine leere neue Datenbank erzeugen noch die laufende A-Generation
ablösen. Dafür gibt es den Negativtest `#3b`.

### Was ein belastbares Backup braucht

Nicht nur die Datei kopieren:

- **Fortlaufende Nummer**, atomar vergeben — sonst kollidieren zwei gleichzeitig
  startende Läufe
- **Temporäre Datei, dann atomar veröffentlichen** — eine abgebrochene Sicherung
  darf nie wie eine gültige aussehen
- **Niemals überschreiben.** Eine vorhandene Nummer ist vergeben, Punkt
- **Konsistenz gegen *alle* Schreiber.** „Der Scheduler steht" genügt nicht —
  API-Requests schreiben auch. Es braucht die SQLite-Backup-API oder eine
  Wartungssperre, die Scheduler **und** Requests umfasst
- **Manifest**: Profil-ID, **Profil-Kompatibilitäts-ID**, Plugin-Pakete samt
  Versionen, StockInfo-Version, DB-Schema-Version. „Stand" allein ist zu
  unbestimmt, um eine Wiederherstellung zuzuordnen
- **Zuordnung beim Zurückholen**: Eine Sicherung aus Profil A in Profil B
  einzuspielen ist ein Fehler, kein Sonderfall

### Die Profil-Kompatibilitäts-ID — kein Hash über die Datei

Verify `#2` verlangt, dass eine neue Paketversion **keine** neue Datenbank
erzeugt. Daraus folgt zwingend eine ausdrückliche Kennung statt eines Hashes
über die ganze Konfiguration:

| Änderung | Kompatibilitäts-ID |
|---|---|
| API-Schlüssel, Zeitgrenze, Patch-Version | **unverändert** |
| fachlich inkompatibler Profilstand | erhöht sich — bewusst |
| `a/1` → `b/1` | anderes Profil, neue Datenbank |
| `a/1` → `a/2` | entscheidet der Profilautor, nicht ein Hash |

Ohne diese Regel kann der Launcher „Quelle aktualisieren" und „Profil ersetzen"
nicht zuverlässig unterscheiden — und würde bei jeder Schlüsseländerung die
Datenbank wegwerfen.

### Der Konsument, auf den es ankommt, ist StockPortfolio

Ein Cache über den Profilwechsel hinweg zeigt Werte aus einer Datenbank, die es
nicht mehr gibt. Deshalb gehört eine **`generation_id`** in die API — sie
gehört zum Vertrag aus T-24.

**Das StockInfo-Dashboard ist dafür der falsche Prüffall:** Es hält keinen
persistenten Cache über getrennte Deployments hinweg. StockPortfolio tut das —
dort liegt der eigentliche Fall. Nötig ist dort:

- die letzte `generation_id` speichern
- bei Änderung den sichtbaren Quote-/History-**Namespace** umschalten
- Portfolio, Stückzahlen, Ziele und Benutzerdaten behalten

**Umschalten, nicht löschen** *(Codex, 2026-08-21)*: Ich hatte hier zweimal
„leeren" geschrieben, während T-35 längst die robustere Semantik trägt. Der
Unterschied ist keine Wortwahl — physisches Löschen mehrerer Object-Stores ist
ein mehrschrittiger Vorgang, der mittendrin abbrechen kann; genau davor schützt
der Namespace. Verbindlich ist deshalb:

- **atomarer Wechsel** des sichtbaren Quote-/History-Namespace
- keine Werte der alten Generation sichtbar
- spätere Löschung alter Namespaces ist **Hausputz**, nicht Vertrag
- alle benutzereigenen Speicher bleiben unverändert

Sonst optimiert eine Umsetzung auf genau die riskante Mehrfach-Löschung, die
T-35 bewusst vermieden hat.

**Angelegt am 2026-08-21: `StockPortfolio/_tickets/T-35-stockinfo-generation-und-waehrung.md`.**
Verify `#8` kann in einem Ticket mit Scope „StockInfo (Backend + Dashboard)"
nicht grün werden — es wird **dort** abgenommen. Das Ticket hält fest:

> **`#8`/`#8b` blockieren den Abschluss von T-25 nicht** *(Codex, 2026-08-21)*.
> Sie standen in der abschlussrelevanten Tabelle, während T-35 zugleich von T-25
> abhängt — bei strenger Auslegung („alle Verify-Zeilen grün") wäre das dieselbe
> Schleife wie eben zwischen T-24 und T-25. Die fachliche Reihenfolge ist
> eindeutig: **T-25 schließt zuerst**, T-35 arbeitet währenddessen gegen die
> veröffentlichten T-24-Fixtures und macht den echten Integrationslauf danach.
> Das Consumer-Verhalten gehört **allein** T-35.

- letzte `generation_id` speichern, bei Änderung reagieren
- **nur** den Kurs-/History-Namespace umschalten — nie Portfolio, Stückzahlen, Ziele
- **keine EUR-Ersatzwährung**, wenn die Kurswährung fehlt (heute wird geraten)
- mittelfristig `listing_id` als bevorzugten Maschinen-/Cache-Schlüssel
- Rückfall auf ISIN/Symbol für alte gespeicherte Positionen bleibt

Ein Befund aus der Prüfung dort ist unabhängig von diesem Vorhaben ernst:
`mappers.ts:17` setzt `currency: response.currency ?? 'EUR'` — eine fehlende
Kurswährung wird geraten. Die App erklärt an anderer Stelle selbst, dass
„10.000 USD plus 10.000 EUR keine 20.000 von irgendetwas" ergeben; der Rückfall
unterläuft genau diese Regel. Der Cache liegt in **IndexedDB** und überlebt jedes
Deployment — Codex' Einschätzung, dass hier der eigentliche Konsument sitzt, ist
damit bestätigt.

### Header und Rumpf müssen aus derselben Generation stammen

*(Codex, 2026-08-21)* T-24 schreibt die Regel fest — hier steht, woran sie
scheitern kann. Den Header **am Ende** der Antwort aus einem veränderlichen
globalen Zustand zu lesen, erzeugt genau die verbotene Mischung: Der Rumpf
stammt noch aus A, der Header schon aus B. Ein Konsument sieht dann einen
gültigen Wert unter einer Generation, in der er nie gegolten hat — und cacht ihn
guten Gewissens.

Zwei Wege sind zulässig, ein dritter nicht:

| Weg | |
|---|---|
| Generation **und** Datenbank-Handle einmal am Requestanfang binden | tragfähig |
| Profilwechsel blockiert laufende Requests bis zu deren Ende | tragfähig |
| Header am Responseende aus dem globalen Zustand lesen | **verboten** |

Der erste Weg ist der einfachere: Was der Request am Anfang bekommen hat, gilt
für ihn bis zum Schluss — auch wenn zwischendurch rotiert wird.

### Absturzfester Übergang

Die Sicherungsdatei atomar zu schreiben genügt nicht; auch der Übergang
`A aktiv → A gesichert → B aktiv` muss es sein. Ein Abbruch dazwischen darf
beim nächsten Start weder A erneut rotieren noch B mit As Datenbank öffnen.

Dafür ein kleiner, dauerhafter Zustandsmarker mit:

- bisher aktiver Profil- und Kompatibilitäts-ID
- gewünschtem, **validiertem** Zielprofil
- Sicherungsnummer und deren Status
- Pfad der aktiven Datenbank
- Ziel-`generation_id`

Jeder Zwischenzustand muss beim Neustart deterministisch fortgesetzt **oder**
auf A zurückgerollt werden können.

**Die Crash-Matrix, konkret** *(Codex, 2026-08-21 — eine frühere Fassung dieses
Tickets hatte nur einen allgemeinen Absturztest, und die Spec behauptete
fälschlich, die Matrix sei schon enthalten).* **Sieben** Fehlerpunkte — „vor und
nach Aktivierung" sind zwei verschiedene persistierte Zustände, nicht einer —,
einzeln injizierbar, jeder mit Neustart und Recovery-Lauf:

| # | Abbruch nach/während | |
|---|---|---|
| 1 | erfolgreicher Validierung von B | |
| 2 | dem temporären Backup | |
| 3 | atomarer Veröffentlichung des Backups | |
| 4 | Schreiben des Übergangsmarkers | |
| 5 | Anlegen der frischen B-Datenbank | |
| 6 | unmittelbar **vor** Aktivierung von B | |
| 7 | unmittelbar **nach** Aktivierung von B | |

Für **jeden** Punkt gelten dieselben Invarianten: genau eine vollständige
Generation aktiv, keine Backupnummer überschrieben, niemals B mit der Datenbank
von A, und A einschließlich Konfiguration und Plugin-Umgebung wieder startbar.

Das braucht eine einspeisbare Uhr und kontrollierte UUID-Erzeugung — echte
Wartezeiten oder Manipulation der Systemuhr gehören nicht in die Suite.

**Und „A bleibt aktiv" braucht mehr als die alte Datenbank:** Die geänderte
`sources.yaml` zeigt ja weiterhin auf B. Es braucht eine gespeicherte
*last-known-good*-Konfiguration **samt Plugin-Umgebung**, sonst startet A nach
einem gescheiterten Wechsel gar nicht mehr.

### Wiederherstellung vergibt eine neue Generation

Beim Zurückholen einer Sicherung bekommt **jede Aktivierung** eine neue
`generation_id` — auch wenn im Backup eine alte gespeichert ist. Sonst sieht ein
Konsument bei zweimaliger Wiederherstellung dieselbe Kennung und behält seinen
Cache, obwohl sich der Inhalt geändert hat.

Die fachlichen `listing_id`s im Backup bleiben dabei erhalten. Das trennt
**Datenidentität** von **Betriebsereignis**.

---

## Auflösung

_(offen)_ — Stand vom 2026-09-07, gemessen in
[Prüfstand 2026-09-07](#prüfstand-2026-09-07).

Zum Abschluss fehlen drei Dinge, in dieser Reihenfolge:

1. **`generation_id` bauen.** Route `/generation`, Middleware für den Header auf
   jeder Antwort, `expose_headers` in der CORS-Einstellung, Bindung von
   Generation und Datenbank-Handle am Requestanfang. Der Vertrag samt beider
   Fixtures liegt aus T-24 bereits vor; hier entsteht nur die Umsetzung und mit
   `#7j` ihre Konformitätsprüfung. Zehn Verify-Zeilen hängen daran.
2. **Kompatibilitäts-ID vom Hash trennen.** Eine ausdrückliche, vom Profilautor
   vergebene Kennung statt SHA-256 über Ketten und Pakete — sonst sind `#1`,
   `#2` und `#2b` nicht gleichzeitig erfüllbar.
3. **Rotation mit Preflight.** Erst B validieren, dann A sichern, dann auf eine
   frische Datenbank wechseln, dazu die Crash-Matrix. `scripts/sources-profile.sh`
   deckt davon nur das Umschalten der Datei ab.

Punkt 1 ist der einzige, der einen veröffentlichten Vertrag unerfüllt lässt, und
zugleich der, an dem StockPortfolio hängt. Ob das Ticket so bleibt oder in
`generation_id` und Rotation geteilt wird, ist eine Portfolio-Entscheidung.

</details>
