# T-26 · Offene Detailfelder tatsächlich durchreichen

Plugin-Felder werden jetzt gespeichert, über REST ausgeliefert und im Dashboard
anhand ihrer Deklaration angezeigt. Der erste UI-Test ist gelaufen; die
erste Prüfung durch Claude hat Korrekturen verlangt. Diese sind umgesetzt;
die zweite Prüfung steht aus. T-56/F bleibt bis dahin offen.

## Für dich

Aktuell ist keine weitere Entscheidung oder Wiederholung des Tests nötig.
Dein Auftrag vom 2026-09-07 gilt: **Codex implementiert einschließlich REST,
UI und erstem UI-Test; Claude verifiziert anschließend.** Die Rückmeldungen
zur Oberfläche bleiben unverändert in [T-56](T-56-was-mike-im-ui-pruefen-soll.md).
T-62 zum Anzeigenamen bleibt offen.

## Umsetzung und technische Nachweise

| Repo | Time-box | Scope | GH-Issue |
|---|---|---|---|
| StockInfo | ursprünglich 1 Tag | Plugin-Katalog → Persistenz → REST → Dashboard | — |

**Ergebnis:** Ein korrekt deklariertes neues Feld übersteht den Weg von einem
Datei-Plugin bis zum REST-Ergebnis und zur Bearbeitung im Browser, ohne eine
Feldliste im Dashboard zu ändern.

Die drei fachlichen Teile sind Feldschema samt Anwendbarkeit/Version,
generischer Speicher samt Migration/Quellenvorrang und REST/UI-Durchleitung.
Betroffen sind Plugin-API, Registry/Adapter, Repository/Service, REST-Vertrag
und Dashboard. Das entspricht dem ausdrücklich erweiterten Auftrag; ein
beziffertes Dateibudget wurde vor der Umsetzung allerdings nicht eingetragen.
Der Umfang muss deshalb bei der Übergabe ausdrücklich mitgeprüft werden.

Nicht-Ziele: T-25 vollständig umsetzen, Namen editierbar machen (T-62),
Börsenkatalog erweitern (T-30), neue Chart-Funktionen oder Plugin-Installation.
Der Umsetzungsplan steht in
[2026-09-07-t26-open-details.md](../docs/superpowers/plans/2026-09-07-t26-open-details.md).

### Verify

**B** = isolierter Browserlauf auf `http://127.0.0.1:5186/#/assets`,
Backend `http://127.0.0.1:8936`, eigenes temporäres Datenvolume,
Quellen `risk-demo` + `yaml-file`. **A** = automatisierter Test mit eigener DB.
Die Browserinstanz ist eine Testinstanz; ihre Laufzeit ist kein Betriebsversprechen.

| # | Lauf | Handgriff | Nachweis | woher | AI |
|---|---|---|---|---|:--:|
| 1 | B/A | ETF mit neuem `risk-demo.score` aufnehmen | Feld gespeichert und nach erneutem Lesen vorhanden | REST-Kette, Browser | ✅ |
| 2 | B/A | `GET /quote/IE00B4L5Y983` lesen | unbekanntes Feld unter `details`, TER identisch zur bisherigen Projektion | REST-Kette | ✅ |
| 3 | B/A | `GET /instruments` lesen | Werte und Herkunft unter `details` | REST-Kette, Browser | ✅ |
| 4 | B/A | `GET /fields` lesen | Typ, Einheit, Labels, Schreibrecht, Quellen, Anwendbarkeit und Version | REST-Kette | ✅ |
| 5 | A | Schema ändern und Quelle entfernen; Ausfall simulieren | Version steigt bei Änderung/Entfernung, bleibt bei Ausfall gleich | `test_open_details*.py`; kein separater Installationslauf | ➖ |
| 6 | B | BTC und ETF aufklappen, DE/EN und 390 px prüfen | unbekannte Felder generisch; BTC ohne Fondsfelder; kein horizontaler Überlauf | Chrome, sichtbare Bedienung | ✅ |
| 7 | B/A | `verified` zu überschreiben versuchen | kein Editor; PATCH 422, vorhandenes `false` bleibt | Browser und REST-Kette | ✅ |
| 8 | B/A | Score 0 eintragen, Quelle auf 17 ändern, aktualisieren, Eingabe entfernen | Quelle gewinnt; 0 als verdeckt sichtbar; Löschen lässt 17 bestehen | Browser-PATCH und Refresh | ✅ |
| 9 | B | ETF-Details öffnen | Score/Verified nennen risk-demo, Fondsfelder yaml-file | Chrome-Snapshot | ✅ |
| 9b | B/A | Datei-Plugin durch Registry, Beschaffung, DB und REST führen | unbekanntes Feld samt Herkunft, Persistenz und Override erhalten | `test_open_details_flow.py`, gleicher Plugin-Code im Browser | ✅ |
| 10 | A | Dashboard-Fixtures ohne `details` rendern | bisheriger Detailpfad bleibt kompatibel | bestehende Komponenten-Suite | ➖ |
| 11 | A | vollständige lokale Suite ausführen | 1069 Backend, 303 Plugin-API, 45 Beispiel, 331 Dashboard erfolgreich (frischer Datenpfad) | `make test`, 2026-09-07 | ➖ |

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise ·
➖ ausschließlich automatisierte Tests/Review, keine Live-Verifikation.

**Prüflauf:** Backend 29 übersprungen, 8 Online-Integrationstests abgewählt;
Plugin-API 1 übersprungen. Ruff und `vue-tsc --noEmit` erfolgreich. AST- und
TypeScript-Compiler-Inventar der berührten Dateien geprüft. Keine unabhängige
Freigabe und kein erneuter vollständiger Zwei-Profil-Lauf von T-56 behauptet.

```bash
# #1–5, #7–9b: reproduzierbarer REST-/Persistenzlauf mit Testvolumes
.venv/bin/pytest -q tests/test_open_details.py tests/test_open_details_flow.py
# #11: vollständige lokale Suite, Betriebsdatenbank abgeschottet
TASK_TEST_DIR=$(mktemp -d /tmp/stockinfo-t26-r2.XXXXXX)
DATABASE_PATH="$TASK_TEST_DIR/stockinfo.db" make test ARGS='-m "not integration"'
# #4: aktuelle Felddefinitionen der isolierten Browserinstanz
curl -sS http://127.0.0.1:8936/fields
# #2 und #3: Details der Testinstanz
curl -sS http://127.0.0.1:8936/quote/IE00B4L5Y983
curl -sS http://127.0.0.1:8936/instruments
```

**Nebenwirkungen:** Datenbankschema 2 übernimmt bisherige Detailspalten und
manuelle Werte in generische Tabellen. Die bisherigen Top-Level-REST-Felder
bleiben als Projektion erhalten. Neue Metadatenfelder müssen im Plugin
deklariert sein; der Core verwirft undeclared/ungültige Werte. `/fields` nennt
eine persistierte Detailgeneration und einen atomaren Schema-Zähler; T-25s
allgemeine Header-/Generation-Laufzeit bleibt offen. API_VERSION bleibt 2;
`FieldSpec.instrument_types` ist ein optionaler Zusatz.
Die Metadatenanreicherung wird jetzt für jede bekannte Instrumentgattung
angefragt, nicht nur für ETFs. Das Plugin entscheidet über Deklaration und
`is_responsible`, ob es zuständig ist. Dadurch können etwa Krypto-Felder
beigesteuert werden; Fondsfelder bleiben auf ihre deklarierten Gattungen
begrenzt. Der Feldkatalog wird beim Start nach der DB-Initialisierung
persistiert; `GET /fields` liest ihn ausschließlich.

**Browserbreite:** Nach dem mobilen Test blieb zunächst eine feste Emulation
aktiv; der Wechsel auf eine feste Desktopbreite behob das Resize-Problem noch
nicht. Auf Mikes zweiten Hinweis vollständig entfernt. Echter Fenster-Resize
geprüft: 1100 px Fenster → 1060 px Tabelle, 1505 px → 1465 px. Die Ansicht
reagiert wieder auf die Fensterbreite; keine CSS-Änderung erforderlich.

### Direkte UI-Nacharbeit auf Mikes Auftrag · 2026-09-07

Mike beanstandete die Zeitangaben pro Feld und die scheinbar vollständige
Sperre. Er beauftragte unmittelbare Korrektur und Tests editierbarer Felder,
ohne vorherige Claude-Prüfung. Sein weiterer Hinweis: Der Zeitpunkt steht
bereits unten bei „Source as of“; ein zusätzlicher Zeit-Tooltip ist unnötig.

Umgesetzt: keine Zeitangabe und kein Zeit-Tooltip pro Feld; die gemeinsame
Fußzeile bleibt. Auf Mikes weiteren Auftrag entfallen auch „Nur Lesen“/„Read only“ und
alle Info-Symbole samt Erklärungstexten an den Feldern. Die Bedienung allein
zeigt, ob ein Feld editierbar ist.
Bearbeiten-Schaltflächen nennen ihr Feld. Beim Test zusätzlich den fehlenden
Ladetext-Schlüssel des Feldkatalogs korrigiert.

| # | Lauf | Handgriff | Nachweis | woher | AI |
|---|---|---|---|---|:--:|
| 6a | B | ETF-Details öffnen | kein Datum im Feldbereich, gemeinsame Fußzeile bleibt; keine Read-only-Texte oder Info-Symbole pro Feld | Chrome-Snapshot und Screenshot | ✅ |
| 8a | B | leeren Score 0 und leeren Anbieter „Testanbieter“ per UI setzen, Browser neu laden | beide Werte sichtbar und per REST als manual gespeichert | echte Zahl-/Freitextbedienung, Reload, GET instruments | ✅ |
| 8b | B | beide manuellen Angaben per Clear/Entfernen löschen | beide null; readonly false bleibt erhalten | UI und REST-Rücklesen | ✅ |
| 8c | A | editierbaren Boolean über echten Komponentenbutton umschalten | true → false → null; false zeigt Nein | Komponententest, kein Live-Boolean-Lauf | ➖ |

Der isolierte Testbestand bleibt mit editierbaren Lücken vorbereitet:
Risikoscore bei BTC/ETF und Fondsanbieter beim ETF. Dafür ausschließlich die
Dateien im eigenen Testvolume geändert. Betriebsdaten bleiben unberührt.
Gezielt 6/6 Detail-Komponententests und vue-tsc erfolgreich; Compiler-Inventar
und `git diff --check` geprüft. Kein erneuter Backend-Volltest für diese
Frontend-Nacharbeit erforderlich.

### Herkunft im Tooltip und unterscheidbare Testinstrumente

Weiterer direkter Auftrag Mike: Herkunft nicht im normalen Feldbereich
anzeigen. Quellennamen und „Von Hand“ stehen jetzt nur im Tooltip am Feld,
ohne Info-Symbol. Live am ETF geprüft: Feldbereich ohne Herkunftstext,
Tastaturfokus auf TER zeigt „Source: yaml-file“. Bearbeitung bleibt erhalten.

Auf Mikes Hinweis zur Demo gelten Score und Verified im isolierten Plugin
jetzt ausschließlich für Krypto. Nach Neustart der eigenen Testinstanz per
REST bestätigt: BTC hat score/verified, EUNL provider/ter/fund_domicile.
Die Demo-Datei liegt ausschließlich im temporären Testvolume, nicht im
Betriebsprofil. Frühere ETF-Score-Nachweise oben beschreiben den damaligen
Teststand. Aktuell ist beim ETF der Anbieter, bei BTC der Score editierbar.

### Korrekturen nach Claudes Runde 1

Die ursprüngliche Volltest-Angabe „1065 Backend erfolgreich“ beruhte auf einer
bereits initialisierten temporären Datenbank und war kein Frischstartbeleg.
Claudes Gegenprobe mit sieben Fehlern ist bestätigt. Der oben dokumentierte
Lauf erzeugt jetzt mit `mktemp` vor jedem Start einen neuen leeren Datenpfad;
am 2026-09-07 bestanden 1069 Backend-, 303 Plugin-API-, 45 Beispiel- und
331 Dashboard-Tests. Backend: 29 übersprungen, 8 Online-Tests abgewählt;
Plugin-API: 1 übersprungen. Log: `/tmp/stockinfo-t26-r2-full.log`.

| Befund | Korrektur und Nachweis |
|---|---|
| Konstruktorfehler entfernt Schema und manuelle Werte | Deklaration der Plugin-Klasse vor Konstruktion validieren; echter werfender Konstruktor im REST-Flow, Katalog/Version identisch und manueller Wert 0 weiter sichtbar |
| `/fields` schreibt, Frischstarttests scheitern | Kataloginitialisierung in den Lifespan; GET verwendet ein Repository lesend. Betroffene Tests starten den Lifespan mit isoliertem Volume. Gegenprobe mit `PRAGMA query_only=ON` erfolgreich |
| Quellenfußzeile widerspricht Detailfeldern | Aus tatsächlichen Provider-Werten in `details` ableiten. Komponententest zuerst rot, dann grün; live EUNL nur TER/Anbieter/Domizil und Fußzeile `yaml-file`, kein `risk-demo` |
| Antwortreihenfolge schwankt | Vereinigte Feldmenge vor Projektion sortieren; damit auch `manual_fields` und `shadowed_fields` stabil |
| Migrierter manueller Betrag ohne Währung | Manuelle Fondswährung übernehmen, sonst gespeicherte Fondswährung; Migrationstest mit EUR vor USD und GBP als Rückfall |
| Bestehender Override-Weg weist Betrag ab | Explizite oder gespeicherte manuelle Betrags-/Fondswährung ergänzen; gespeicherte EUR bleibt bei Änderung von 20 auf 30 erhalten. Unbekannte Währung wird weiterhin nicht erfunden |
| Sammelquellen-SQL unverständlich | Austausch migrierter `yfinance+justetf`-Zeilen beim Einzelquellen-Refresh direkt kommentiert |
| Importe | `json` und `detail_store` in die jeweiligen Importgruppen verschoben |
| Ausweitung der Metadatenabfrage undokumentiert | Nebenwirkungen oben um alle bekannten Gattungen und Plugin-Zuständigkeit ergänzt |

Ruff und `vue-tsc --noEmit` erfolgreich. Vollständiges Python-AST-Inventar der
berührten Dateien und TS-Compiler-Inventar beider berührten Dashboard-Dateien
auf englische Bezeichner geprüft. Browser: 1194 px, kein horizontaler Überlauf.
Die UI-Nachprüfung dieser Runde betrifft die Quellenfußzeile; frühere
Eingabe-/Löschtests werden dadurch nicht als neu ausgeführt ausgegeben.

### Tooltip-Position auf Mikes Rückmeldung

Herkunfts-Tooltip links am Feld ausgerichtet (`top-start`); zuvor war er
über der Mitte der ganzen Spalte und damit weit rechts vom kurzen Wert.
Live bei TER gemessen: Feld links 42,59 px, Tooltip zuvor 151,64 px,
jetzt 43 px. 25 betroffene Komponententests und `vue-tsc` erfolgreich.
Dieser UI-Nachtrag folgt auf den grünen Gesamtlauf oben.

### Herkunfts-Tooltips entfernt

Auf Mikes anschließende Rückmeldung „Der ToolTip ist nervig“ sind die
Herkunfts-Tooltips samt zusätzlichem Tastaturfokus an den Feldern entfernt.
Die Quellenfußzeile und die Herkunftsdaten in REST bleiben erhalten.
Sechs Detail-Komponententests und vue-tsc erfolgreich.

### Auflösung

Implementiert und nach Claudes erster Prüfung korrigiert. Die zweite
unabhängige Prüfung ist offen; das Ticket bleibt offen.

## Fachliche Anforderungen und Designentscheidungen

Die folgenden Anforderungen stammen aus dem ursprünglichen Ticket. Der aktuelle
Umsetzungs- und Prüfstand steht oben; diese Zielbeschreibung ist keine offene
Arbeitsliste und keine unabhängige Freigabe.


### Was zu bauen ist

- generische Felddefinitionen, gespeist aus `FieldSpec` der geladenen Quellen
- normalisierte Werte **und Herkunft je Instrument und Feld**
- generische manuelle Overrides — aber nur für Felder mit `overridable=True`
- die bestehende Merge-Regel gilt unverändert: Quelle gewinnt, manueller Wert
  füllt Lücken
- `details` in `/quote` und `/instruments`
- generische Darstellung im Dashboard
- Fixtures, an denen ein Konsument die Ignorierbarkeit prüfen kann

### Die Hülle eines Detailwerts

`GET /fields` sagt, **welche** Felder es gibt. `details` am Instrument sagt,
**welchen wirksamen Wert** dieses Papier dazu hat. Zwei Ebenen, die nicht
vermischt werden dürfen. Die Hülle trägt:

```
"details": {
  "ter": {
    "value":     0.2,
    "unit":      "percent",
    "currency":  null,              ← nur bei Beträgen
    "origin":    "provider",        ← provider | manual
    "source":    "justetf",
    "as_of":     "2026-08-19T…",
    "shadowed":  false              ← ein manueller Wert wird gerade verdeckt
  }
}
```

`shadowed` ist kein Beiwerk: Es ist dieselbe Aussage, die `apply_overrides`
heute schon über `shadowed_fields` macht — wer einen Wert eingetragen hat und
einen anderen sieht, muss erfahren, warum.

### Namespaces — sonst kollidieren zwei Plugins bei `yield`

Zwei Quellen können beide ein Feld `yield` deklarieren und Verschiedenes meinen.
Regeln dagegen *(Codex, 2026-08-20)*:

- bekannte Felder wie `ter` bedienen den **kanonischen Katalog**
- ein Plugin darf ein kanonisches Feld nur mit **verträglichem** Typ und
  verträglicher Zieldimension bedienen
- wirklich neue Felder bekommen einen stabilen Namespace: `plugin-name.feld`
- deklarieren zwei Quellen denselben Schlüssel mit widersprüchlichem Typ,
  widersprüchlicher Einheit oder Bedeutung, wird die Quelle **beim Laden
  abgelehnt** — kein „der letzte gewinnt"
- ein veröffentlichter Feldschlüssel wird nie umgedeutet; neue Bedeutung heißt
  neuer Schlüssel

Geprüft wird das an **zwei** Stellen: in der Registry beim Laden (T-23) und im
Contract-Test des Plugins.

### Eine einzige Wahrheit für die acht bekannten Kennzahlen

`ter`, `volatility` und die übrigen sechs erwarten bestehende Konsumenten
weiterhin auf oberster Ebene, während sie zugleich im generischen Katalog
stehen. Diese Doppelprojektion ist unvermeidlich — sie darf aber nicht zu zwei
Wahrheiten werden:

- Quellenwert, manueller Wert und Merge-Regel werden **einmal** generisch
  gespeichert und berechnet
- die Top-Level-Felder sind nur eine **Kompatibilitätsprojektion** desselben
  wirksamen Werts
- ein Test vergleicht beide Darstellungen, einschließlich `null`- und
  Override-Fällen

Zwei getrennte Speicher- oder Merge-Pfade erzeugen früher oder später
widersprüchliche Antworten.

### Die Feldliste ist abfragbar — mit Version

*(Mikes Anforderung, 2026-08-20: verbindliche Felder samt Versionsnummer müssen
per API abfragbar sein, und dieselbe Logik gilt für die offenen Felder.)*

```
GET /fields
{
  "core_version": "1.0",              ← Vertragsversion aus T-24
  "details_version": 7,               ← ändert sich bei **jeder** Schemaänderung
  "core": { "quote": [ … ], "instrument": [ … ], "daily": [ … ], "fx": [ … ] },
  "details": [
    { "name": "ter", "kind": "number", "unit": "percent",
      "label_en": "Total expense ratio", "overridable": true,
      "sources": ["justetf"] }
  ]
}
```

Der Grund ist praktisch: Ein Konsument, der Details generisch darstellen soll,
muss sie **erfragen** können — sonst müsste jedes neue Feld eine Codeänderung
auf beiden Seiten nach sich ziehen, und die Erweiterbarkeit wäre wieder keine.

Die Versionsnummer ist dabei das eigentliche Werkzeug. Sie ändert sich bei
**jeder** Änderung am öffentlichen Feldschema — nicht nur, wenn Felder
dazukommen:

| Ändert die Version | Ändert sie **nicht** |
|---|---|
| Feld kommt dazu oder fällt weg | eine Quelle ist gerade nicht erreichbar |
| Typ, Einheit, Währungspflicht oder `overridable` wechselt | ein Schutzschalter ist offen |
| ein Feldschlüssel wird ersetzt | Kurse ändern sich |
| Beschriftung oder ausgelieferte Quellenmenge ändert sich | |

Maßgeblich ist das **konfigurierte und validierte** Profilschema, nicht dessen
momentane Gesundheit. Ein Provider-Ausfall darf die Feldliste nicht verändern —
sonst verwerfen alle Konsumenten ihre Caches, weil eine Quelle kurz hakt.

**Der Typ ist festgelegt** *(Codex, 2026-08-20)*: eine nichtnegative Ganzzahl,
innerhalb einer `generation_id` monoton, atomar fortgeschrieben. Ein
Fingerabdruck wäre auch möglich gewesen — aber der REST-Vertrag muss **einen**
Typ nennen, sonst rät jeder Konsument. Zwischengespeichert wird immer unter
`(generation_id, details_version)`.

**Nicht zu verwechseln mit `generation_id` aus T-25:** Die Feldmenge kann sich
ändern, ohne dass das Quellenprofil wechselt — etwa wenn innerhalb desselben
Profils eine Quelle nachinstalliert wird.

---

## Reviewhistorie

<details>
<summary>Claude · Runde 1 · changes_requested · Prüfstand 8bf2d53</summary>


Geprüft hat **Claude** als zugeordneter Verifier. Prüfstand: `fe323ff` für den
gesamten Diff, zusätzlich der UI-Nachtrag `fe323ff..8bf2d53`. Die verarbeitete
OUTBOX ist entfernt; der Rundenverbrauch bleibt bei 1.

### Zuschnitt zuerst: `continue`

Die Breite folgt Mikes ausdrücklich erweitertem Auftrag (Feldschema, generischer
Speicher, REST/UI), nicht einer unangekündigten Produktschicht. Die Nicht-Ziele
sind eingehalten: kein T-25, kein T-62, kein T-30. Tatsächlich in
`d7afe20..fe323ff`: **35 Produktdateien +1082/−177**, 11 Test-/Dokudateien
+428/−31, 4 Ticketdateien +503/−118. Das fehlende Vorabbudget bleibt eine
festgehaltene Prozessabweichung; sie wird durch dieses `continue` nicht
nachträglich zur Freigabe. Ein Zuschnitt-Rückbau wird **nicht** verlangt.

### Blocker 1 — ein Quellenausfall verändert Feldliste und `details_version`

Das Ticket ist hier verbindlich: „Maßgeblich ist das konfigurierte und
validierte Profilschema, nicht dessen momentane Gesundheit. Ein Provider-Ausfall
darf die Feldliste nicht verändern." Das gilt nur für **eine** von zwei
Ausfallformen.

In `app/sources_registry.py::_build_one` wird `_DETAIL_SCHEMAS[spec.name]` erst
**nach** erfolgreichem Konstruktor gesetzt. Wirft `spec.build(...)` — nicht
erreichbarer Dienst, fehlendes Credential, Importfehler im geladenen Plugin —,
kehrt die Funktion vorher mit `None` zurück. Die Quelle ist weiterhin
konfiguriert und war validiert, ihre Felder fallen trotzdem aus dem Katalog.

Gegenprobe, nicht abgeleitet: Sonde mit einem Demo-Plugin, dessen `__init__`
beim zweiten Profilaufbau wirft.

```
assert after['details_version'] == before['details_version']
E   assert 3 == 2
[warning] source_construction_failed error='RuntimeError: …' role=etf_meta source=risk-demo
```

Zweite Folge derselben Ursache: bereits gespeicherte Werte verschwinden aus der
Antwort, weil `detail_store.read` nur Felder ausliefert, die `applies(...)` über
die Katalog-Scopes bestätigt.

```
assert 'risk-demo.score' in during
E   AssertionError: assert 'risk-demo.score' in {'provider': …, 'ter': …, 'fund_domicile': …}
```

Das trifft auch **manuelle** Eingaben: Sie bleiben in `detail_overrides` stehen,
sind für den Konsumenten aber unsichtbar, solange die Quelle hakt.

Der ausgelieferte `test_quellenausfall_aendert_weder_schema_noch_version` setzt
`configuration_problem()` — ausgerechnet den einen Ausfallpfad, der **nach** dem
Schemablock ausgewertet wird. Der Test kann die beiden Zustände deshalb nicht
unterscheiden: Seine Assertion ist richtig, sein Aufbau erzeugt den
entscheidenden Unterschied nicht.

**Erwartet:** Die Deklaration hängt an der konfigurierten und zuletzt
validierten Quelle, nicht an einem gelungenen Konstruktor — Deklaration vor dem
Bau lesen oder das letzte validierte Schema einer konfigurierten Quelle halten.
Dazu ein Test, der genau die Konstruktorform des Ausfalls erzeugt.

### Blocker 2 — „1065 Backend erfolgreich" trägt nicht

Verify #11 und die OUTBOX melden eine grüne Gesamtsuite. Auf einem **frischen**
`DATABASE_PATH` scheitern mit dem im Ticket dokumentierten Kommando sieben
Tests:

```
5 × tests/test_api_fields.py, 2 × tests/test_contract_required_fields.py
sqlite3.OperationalError: no such table: meta
  app/routers/fields.py:47 → app/repository.py:620 → app/detail_store.py:69
7 failed, 1058 passed, 29 skipped, 8 deselected
```

Warum der Lauf grün aussah: `/tmp/stockinfo-t26-suite/stockinfo.db` existierte
schon **vollständig initialisiert** (mit `detail_values`/`detail_overrides`,
Zeitstempel 14:51) — der Beleg stammt aus Reststand, nicht aus einem
Frischstart. Genau das verlangt der Vertical-Acceptance-Riegel Punkt 4 für ein
Ticket, das Schema und Startzustand ändert. Gegenprobe: dieselben Tests laufen
mit einer initialisierten Datenbank grün (36/36).

Ursache ist eine neue Kopplung: `GET /fields` öffnet seit diesem Diff selbst ein
`QuoteRepository` und liest `meta`, ohne dass `init_db` gelaufen sein muss. Im
Betrieb deckt der Lifespan das ab, in der Suite nicht. Zwei Dinge gehören
zusammen korrigiert:

- Ein **GET schreibt**: `detail_catalog(definitions)` führt `sync_catalog` mit
  `BEGIN IMMEDIATE` aus und zählt die Version bei jedem Aufruf fort. Über diesen
  Weg wirkt sich Blocker 1 bei jedem `/fields` erneut aus.
- `QuoteRepository(settings.database_path)` wird im selben Handler **zweimal**
  gebaut.

### Weitere Korrekturen für dieselbe Runde

1. **Gemeinsame Quellenfußzeile widerspricht der feldweisen Herkunft.** Dein
   eigener Hinweis ist bestätigt: `InstrumentDrilldown.vue:136` zeigt
   `item.source` — den Instrumentstand der letzten vollständigen Anreicherung —
   während die sichtbaren Felder ihre Herkunft aus `details[].source` nehmen.
   EUNL nennt so `risk-demo`, obwohl kein sichtbares Feld von dort kommt. Das
   ist eine falsche Auskunft, kein Schönheitsfehler.
2. **Unbestimmte Reihenfolge in der Antwort.** `detail_store.read` iteriert über
   `set(CANONICAL) | applicable | set(providers) | set(manual)`. Schlüsselfolge
   in `details` sowie die Listen `manual_fields`/`shadowed_fields` wechseln
   damit zwischen Prozessen. Sortieren.
3. **Migrierter Betrag verliert seine Währung.** Auf echtem Altbestand geprüft:
   Instrument 4 hat manuell `fund_size=500000.0` mit `currency=NULL`, während
   `fund_currency='EUR'` als eigenes manuelles Feld danebensteht.
   `currency_required` ist für `fund_size` wahr — der generische `details`-Weg
   zeigt den Betrag ohne Währung. Die Top-Level-Projektion bleibt korrekt.
4. **Neue 422-Falle im alten Overrides-Formular.** `set_overrides` validiert
   jetzt mit `validate_input`; ein manueller `fund_size` ohne `fund_currency`
   wird abgewiesen. Vorher war das erlaubt. Entweder bewusst so festhalten und
   die Oberfläche darauf vorbereiten, oder die Währung aus dem gespeicherten
   Stand ergänzen.
5. **Unerklärte SQL-Bedingung.** In `save_quote` ist
   `instr('+' || source || '+', '+' || ? || '+') > 0` für einfache Quellennamen
   deckungsgleich mit `source = ?`; sie greift nur bei zusammengesetzten Namen
   wie `yfinance+justetf`. Wenn das die Absicht ist, gehört der Grund als Satz
   daneben — sonst zentralisiert der nächste Durchgang sie weg.
6. **Importe.** `app/repository.py`: `import json` steht in `get_overrides`
   statt im Kopf, und `from app import detail_store` steht zwischen
   `import sqlite3` und `import uuid`.
7. **Erweiterte Anreicherung dokumentieren.** `quote_service.py` ersetzt
   `if instrument_type == "etf"` durch `is not None`. Der entfernte Kommentar
   nannte das Risiko beim Namen („sonst bekäme eine Aktie ihre Metadaten nie
   wieder aktualisiert"); der `is_responsible`-Zweig fängt es weiterhin ab. Die
   Verhaltensausweitung gehört in die Nebenwirkungen von T-26.

### Was unabhängig bestätigt ist

- **Migration auf echtem gewachsenem Bestand, verlustfrei.** Nicht synthetisch:
  Kopie von `data/backups/stockinfo-20260907T085907625Z-*.db` im Scratchpad.
  Werte von fünf Instrumenten und **beide** Override-Zeilen sind vollständig in
  `detail_values`/`detail_overrides` angekommen, `accumulating` als echter
  Wahrheitswert, `fund_size` von EUNL mit `currency='USD'`, `source=NULL` als
  `legacy`; Altspalten genullt, `instrument_overrides` geleert, `details_migrated`
  gesetzt. Die Betriebsdatenbank wurde dabei nicht angefasst — vor und nach den
  Läufen bytegleich geprüft.
- **DRY.** `merge_value` ist die einzige Merge-Regel und wird sowohl vom
  generischen Weg als auch von `apply_overrides` benutzt; `CANONICAL` ist die
  einzige Tabelle für Zieleinheit und Grenzen. Kein zweiter Merge- oder
  Speicherpfad gefunden. Gesucht wurde projektweit nach Feldlisten, Einheiten,
  Grenzen und Overrides-Wissen.
- **Testinfrastruktur-Riegel eingehalten.** Kein Record/Replay, keine
  Transportschicht, keine Test-CLI, kein Framework-Plugin. Die neuen Tests
  benutzen `TestClient`, `tmp_path` und ein testlokales Datei-Plugin.
- **Bezeichner englisch, als Inventar gemessen.** Python-`ast` über die 22
  geänderten Dateien: 2481 Bezeichner, kein deutscher. TypeScript-Compiler über
  die 20 geänderten `.ts`/`.vue`: 3904 Bezeichner, kein deutscher.
- **Ruff** sauber; **Dashboard 330/330** grün; **vue-tsc** ohne Befund.
- **Schreibrecht serverseitig.** `overridable=False` wird in
  `set_detail_overrides` **und** in `set_overrides` geprüft; der Browserbefund
  „PATCH 422, vorhandenes `false` bleibt" ist im Flow-Test mit vier
  Negativfällen samt unverändertem `/instruments` abgesichert.

### Nicht selbst geprüft

Die Browserzeilen 1, 3, 6, 6a, 8a, 8b, 9 und der UI-Nachtrag aus `8bf2d53`
stehen als Codex-Belege; ich habe den zugehörigen Code gelesen, aber keinen
eigenen Browserlauf gemacht. Zeile 8c ist ein Komponententest, kein Live-Lauf —
so ist sie auch markiert.

### Selbstheilung

Nicht angewandt. Beide Blocker verlangen eine fachliche Entscheidung, und der
Worktree trug während der Prüfung parallele Produktedits — die Ausnahme greift
in diesem Zustand ausdrücklich nicht.


</details>
