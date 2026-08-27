# T-22 · Quellen konfigurieren statt verdrahten

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend) | aktiv · Plugin-MVP 1/4 | 4 h | Konfigurationsdatei, `is_configured()`, Protokolle | — |

**Löst:** Welche Quelle wann greift, steht heute als `if`-Kaskade in der
Composition-Root (`app/container.py:24-34`), und jeder API-Key ist ein eigenes
Feld in `Settings`. Mit zwei Quellen tragbar, mit vier nicht.

**Hängt an:** T-20 (ohne differenzierte Antworten ist eine konfigurierbare Kette
nicht sinnvoll steuerbar). **Blockiert:** T-23.

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

> **Verbindliche MVP-Reihenfolge, Mike 2026-08-27:** **T-22 → T-27a →
> T-27b → T-23.** Dieses Ticket baut auf dem freigegebenen T-21-Stand bis
> Übergabe 3 auf; die eingefrorenen T-21-Übergaben 4A/4B sind keine
> Voraussetzung.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 0 | **Profilpaket** eintragen (eine Zeile + Schlüssel), Neustart | `GET /sources` zeigt **alle** Rollen besetzt — keine Kette von Hand geschrieben | ➖ [^profil] | |
| 1 | `data/sources.yaml` mit vertauschter Resolver-Reihenfolge, Neustart | `GET /sources` zeigt die neue Reihenfolge | ✅ [^t22] | |
| 2 | OpenFIGI-Key entfernen, Neustart | Quelle bleibt **aktiv** — der Key ist optional und hebt nur das Limit an | ✅ [^t22] | |
| 2b | Quelle mit **pflichtigem** Key ohne Key, Neustart | meldet `configured: false` und fällt aus der Kette — **kein Fehler** | ⚠️ [^t22b] | |
| 3 | `sources.yaml` gelöscht | App startet mit sinnvollen Vorgaben, statt abzubrechen | ✅ [^t22] | |
| 4 | `sources.yaml` mit Tippfehler im Quellennamen | Meldung nennt den unbekannten Namen und die verfügbaren | ✅ [^t22] | |
| 5 | dieselbe Datei in ein Issue kopieren | enthält **keinen** Schlüssel, nur Verweise | ✅ [^t22] | |
| 6 | `make test` | Backend grün | ✅ [^t22] | |

```bash
curl -s "http://localhost:8000/sources" | python3 -m json.tool     # #1/#2
```


[^t22]: **`./_tickets/T-22-smoke.sh --run`: 5/5 über echte Neustarts.** Das ist
    der Kern dieser Matrix — jede Zeile sagt „…, Neustart", und eine
    Konfiguration, die erst danach gilt, muss auch darüber geprüft werden. Das
    Script startet den Server mehrfach über demselben Volume, mit je einer
    anderen `sources.yaml`; es braucht **kein** Netz, weil geprüft wird, welche
    Kette entsteht, nicht was die Quellen liefern.

    Dazu `tests/test_sources_config.py` (zwölf Tests) und die umgeschriebenen
    `tests/test_container.py` (vier). **Gegenproben gelaufen:** Kette umdrehen →
    der Verdrahtungstest fällt; `is_configured` immer `True` → der
    Pflichtschlüssel-Test fällt.

    Zwei eigene Testfehler haben die Mutanten dabei aufgedeckt und sie stehen
    korrigiert im Docstring: Die erste Fassung prüfte mit **einer** Quelle —
    eine umgedrehte Einerliste ist dieselbe Liste — und rief `_chain()` statt
    `_build_resolver()`, also eine Ebene **unter** der Verdrahtung.
[^t22b]: **Als Einheit belegt, nicht über HTTP.** Es gibt heute keine
    eingebaute Quelle mit pflichtigem Schlüssel; der Test stellt eine
    `SourceSpec` mit `needs=("api_key",)` her und prüft alle drei Lagen —
    fehlend, leer, gesetzt. Über den echten Endpunkt ist die Zeile erst
    belegbar, wenn eine solche Quelle existiert; das wird mit dem ersten
    Plugin der Fall sein, das einen Schlüssel verlangt.
[^profil]: **Nicht gebaut — und das ist ein Zuschnittsbefund, keine
    Auslassung.** Ein Profilpaket (`profile: stockinfo-profile-canada==1.0.2`)
    ist ein **installiertes Paket**, aus dem Ketten gelesen werden. Es zu laden
    heißt, einen Lader für Pakete zu haben — und genau der ist T-23
    („Registry, zwei Ladewege"). In T-22 gebaut, entstünde ein zweiter Ladeweg
    neben dem, den T-23 danach anlegt.

    Gelesen wird das Feld bereits: `SourcesConfig.profile` trägt den Wert, und
    `GET /sources` gibt ihn aus. Damit ist die Zeile in der Konfiguration
    vorhanden und wirkungslos, statt unbekannt — und T-23 muss sie nur noch
    auflösen.

---

## Details

### Zwei Orte nach Lebenszyklus, nicht nach Technik

**Geheimnisse und Schalter bleiben in der Umgebungskonfiguration** — Keys, Ports,
TTLs. Das ist das bestehende Muster und der richtige Ort für Secrets.

**Ketten und Reihenfolge kommen in eine Datei im Daten-Volume**, neben die
Datenbank:

```yaml
# data/sources.yaml
resolvers: [openfigi, yahoo-search]
etf_meta:  [justetf, yfinance]
quotes:    [yfinance]

providers:
  openfigi:
    api_key: ${OPENFIGI_API_KEY}     # verweist, enthält nicht
```

Der Grund für die Trennung ist praktisch: **Diese Datei kann ein Nutzer in ein
Issue kopieren, ohne einen Schlüssel zu leaken.** Wenn jemand in Kanada eine
funktionierende Kette gefunden hat, ist sie genau das Artefakt, das er weitergibt.

### `is_configured()` ersetzt die Kaskade

Eine Quelle, der etwas **Pflichtiges** fehlt, meldet `False` und wird gar nicht
erst aufgenommen.

**Nicht jeder Schlüssel ist pflichtig.** OpenFIGI arbeitet anonym mit
niedrigerem Limit und sendet den Key nur, wenn er da ist
(`app/providers/openfigi_provider.py:24-50`). Eine Quelle deshalb abzuschalten
wäre falsch — `is_configured()` fragt „kann ich arbeiten", nicht „ist alles
gesetzt".

Damit verschwindet jede Fallunterscheidung aus `container.py` — heute acht
Verdrahtungspunkte, an denen konkrete Klassen genannt werden.

Der Vertrag dafür steht schon: `Source.is_configured()` in
`stockinfo-plugin-api` (Commit `840121c`).

### Die zwei verstreuten Verträge

> **Korrektur nach Runde 1.** Die Überschrift hieß „die zwei **fehlenden**
> Verträge", und genau das war falsch: Beide existierten längst. Ich habe sie
> nicht gesucht, sie in `providers/base.py` neu geschrieben und damit zwei
> Wahrheiten über denselben Vertrag angelegt — während die Verbraucher weiter
> an den alten hingen. Die Aufgabe war nie „schreiben", sondern „an einen Ort
> ziehen".

`YFinanceProvider` liefert `fetch_quote`, `fetch_daily_closes` **und**
`fetch_fx_rate` — das Protokoll `QuoteProvider` deklariert nur das erste. Die
beiden anderen Verträge standen zwar geschrieben, aber je bei einem
**Verbraucher**: `DailyCloseProvider` in `app/services/daily_sync.py`,
`FxRateProvider` in `app/services/fx_service.py`. Wer eine Quelle ersetzen will,
findet dort nichts — er sieht bei den Quellen einen Vertrag und erfüllt in
Wahrheit drei.

**Weg:** Beide ziehen nach `app/providers/base.py`, neben `QuoteProvider`; die
Verbraucher importieren sie von dort. `FxRateProvider` behält seinen Namen —
ihn beim Umzug zu `FxProvider` zu verkürzen hieße, jede Fundstelle anzufassen,
ohne dass die Aussage genauer würde.

### Der Normalfall ist eine Profilreferenz, nicht eine handgebaute Kette

Die Datei oben ist ein guter **Expertenmodus** — sie verlangt aber Paketliste,
Resolver-, Metadaten- und Kursketten sowie Provider-Abschnitte. Für den Zweck des
Vorhabens ist das zu viel: Wenn die Einrichtung kompliziert bleibt, wird das
Plugin-System nicht benutzt.

Regionale Profile (Kanada, Russland, Österreich/Deutschland) sollen deshalb als
**fertiges Paket mit getesteten Standardketten** eintragbar sein:

```yaml
# data/sources.yaml — der einfache Weg
profile: stockinfo-profile-canada==1.0.2

providers:
  eodhd:
    api_key: ${EODHD_API_KEY}
```

Eine Zeile plus Schlüssel. Einzelne Rollen zu überschreiben bleibt möglich, ist
aber die Ausnahme. Ohne diesen Weg ist „Quellenprofil" nur ein neuer Name für
eine weiterhin von Hand zusammengebaute Konfiguration.

**Verify dazu:** Profilpaket eintragen, Neustart, `GET /sources` zeigt **alle**
Rollen besetzt — ohne dass eine einzige Kette von Hand geschrieben wurde.

### Bei Gleichstand deterministisch sortieren

Sonst hängt das Ergebnis von der Ladereihenfolge des Dateisystems ab, und
Fehlerberichte lassen sich nicht nachstellen. Priorität aus der Konfiguration,
bei Gleichstand nach Name.

---

## Codex-Review · Runde 1 · `20af8fa`

Die Grundrichtung trägt, und die vorgesehenen Läufe sind grün. Vier Befunde
verhindern die Freigabe:

1. **Hoch · Bestehender OpenFIGI-Key geht verloren.** Ohne `sources.yaml`
   liefert `SourcesConfig` einen leeren Providerabschnitt; `_openfigi()` baut
   deshalb `OpenFigiClient(None)`, obwohl `Settings.openfigi_api_key` gesetzt
   ist. Reproduktion: `settings_key='expected-key'`, aber
   `resolver._client._api_key is None`. Zusätzlich löst `_resolve()` nur gegen
   `os.environ` auf; ein wie bisher über Pydantic aus der Projektkonfiguration
   gelesener Wert ist damit nicht dieselbe Secret-Quelle. Die neue
   Konfiguration muss den bestehenden Key ohne Datei bewahren und Verweise
   über die kanonische Umgebungskonfiguration auflösen.
2. **Hoch · `/sources` beschreibt nicht zuverlässig die laufende Kette.** Die
   Services verwenden das gecachte `get_sources_config()`, der Endpunkt liest
   die Datei bei jedem Request neu. Nach einer Dateiänderung ohne Neustart war
   die Laufzeitkette `OpenFigiResolver`, während `/sources`
   `yahoo-search` meldete. Außerdem meldet `quotes: [justetf]`
   `configured: true`, obwohl `build_chain()` die Quelle wegen der falschen
   Rolle verwirft und keine Kursquelle baut. Der Endpunkt muss denselben
   Laufzeitstand und dieselbe Rollen-/Konfigurationsentscheidung verwenden wie
   die Composition-Root.
3. **Mittel · Die beiden neuen Protokolle sind tote Duplikate.** In
   `app/providers/base.py` entstehen `DailyCloseProvider` und `FxProvider`,
   aber die Verbraucher verwenden weiterhin die bereits vorhandenen
   `app.services.daily_sync.DailyCloseProvider` und
   `app.services.fx_service.FxRateProvider`. Damit stehen die zugesagten
   Verträge nun zweimal da, und die neuen Typen schützen keinen Aufruf. Je
   Rolle braucht es eine einzige importierte Vertragsquelle.
4. **Mittel · Das Smoke-Script kann einen unvollständigen Lauf als grün
   melden.** Scheitert `startServer()` vor `report()`, kehrt der einzelne Check
   mit 1 zurück; `runChecks()` läuft ohne `set -e` weiter, erhöht
   `COUNT_FAIL` nicht und prüft am Ende keine erwartete Checkzahl. Die
   behauptete Schlussmarke verhindert damit genau P-05 nicht. Ein
   kontrollierter früher Abbruch muss den Lauf rot machen; der Erfolg muss
   exakt alle fünf Checks verlangen.

**Evidenz:** `./_tickets/T-22-smoke.sh --run` 5/5,
`make test` 633 Backend + 36 Plugin-API + 259 Dashboard,
`ruff` sauber. Die grünen Läufe widersprechen den Befunden nicht: Die drei
Produktreproduktionen betreffen nicht abgedeckte Gegenpfade; der Scriptbefund
liegt im Fehlerpfad des Prüfwerkzeugs.

---

## Auflösung

### Runde 1 → Runde 2 · `d5bb327`

Alle vier Befunde tragen. Drei habe ich vor der Korrektur nachgestellt, den
vierten als Mutant.

**1 · Der bestehende Key ging verloren.** Ohne Datei war der Providerabschnitt
leer, und `OpenFigiClient(None)` bekam nichts — ein Betreiber hätte sein
Kontingent verloren, ohne etwas geändert zu haben.

```text
vorher:  settings.openfigi_api_key = 'expected-key' → Client-Key = None
nachher: settings.openfigi_api_key = 'expected-key' → Client-Key = 'expected-key'
```

Der Abschnitt fällt jetzt auf die Einstellungen zurück; **die Datei gewinnt
weiterhin**, wenn sie etwas sagt — ein Rückfall, der die Konfiguration
überstimmt, machte sie wirkungslos. Beide Richtungen stehen als Test da
(`test_ein_bestehender_key_ueberlebt_ohne_datei`,
`test_die_datei_gewinnt_gegen_den_key_aus_den_einstellungen`).

Die zweite Hälfte war der interessantere Teil: `${NAME}` löste nur gegen
`os.environ` auf, während `Settings` zusätzlich die Projektkonfiguration liest —
**zwei Auffassungen davon, was „die Umgebung" ist.** Derselbe Schlüssel wäre für
den Rest der App gesetzt und im Verweis leer gewesen. `environment_from(settings)`
löst jetzt gegen `Settings` auf, Feldname zu `${FELDNAME}`; echte
Umgebungseinträge gewinnen, wie bei pydantic.

> **Wie der Weg dorthin zustande kam.** Mein erster Griff war
> `dotenv_values(…)` auf die Geheimnisdatei. Das hat die Sicherheitsregel des
> Repos blockiert. Der Umweg über `Settings` ist nicht nur erlaubt, sondern
> besser: Er ist genau die kanonische Umgebungskonfiguration, die der Befund
> verlangt, und er öffnet keine Datei.

**2 · Laufzeit und Diagnose entscheiden jetzt gemeinsam.** `describe_chain(role,
config)` ist die eine Auswertung; `build_chain` baut daraus die Objekte,
`GET /sources` zeigt sie an. `ChainEntry.usable` ist die vollständige Bedingung
— bekannt **und** rollenzulässig **und** einsatzbereit —, und genau die meldet
der Endpunkt als `configured`. Er liest außerdem `get_sources_config()`, also
denselben gecachten Stand wie die Dienste, nicht die Datei von jetzt.

Das hat einen sichtbaren Nebeneffekt: Ein `dependency_overrides[get_settings]`
greift im Test nicht mehr, es braucht `monkeypatch` plus `cache_clear`. Das ist
keine Testschwäche, sondern die Eigenschaft, um die es geht.

**3 · Die Duplikate.** Siehe die Korrektur unter *Die zwei verstreuten
Verträge*. Beide stehen jetzt einmal in `app/providers/base.py`, die Verbraucher
importieren sie; ein Lauf über `app/` findet je Rolle genau eine Klasse.

**4 · Die Schlussmarke des Smoke-Scripts.** Ihr Kommentar berief sich wörtlich
auf `P-05`, während ein Abbruch vor `report()` mit `COUNT_FAIL=0` durchging.
Jetzt zählt ein abgebrochener Check als Fehler, und der Erfolg verlangt genau
`EXPECTED_CHECKS=5`. Mutant gelaufen — dritter Check bricht vor `report()` ab:

```text
✗ 1 von 5 Checks fehlgeschlagen        Exit-Code: 1
```

Vorher wäre derselbe Lauf grün gewesen.

**Verifikation:** `make test` — Backend 637 passed / 29 skipped (vorher 633),
Plugin-API 36, Dashboard 259 in 47 Dateien. `./_tickets/T-22-smoke.sh --run`
5/5, Exit-Code 0. `ruff check app tests` und `git diff --check` sauber.

---

## Codex-Review · Runde 2 · `d5bb327`

Der Produktstand behebt alle vier Befunde aus Runde 1. Key-Erhalt,
Settings-Auflösung, Rollenprüfung, zentralisierte Protokolle und der
Vollständigkeitsguard des Smoke-Scripts tragen in Code und Gegenproben. Ein
enger Testbefund bleibt:

1. **Mittel · Der Test zur Laufzeit-/Diagnosekohärenz reproduziert die
   Abweichung nicht.** `test_der_leseweg_zeigt_die_laufende_kette` schreibt nur
   Konfiguration A, leert den Cache und ruft `/sources` auf. Er primt weder die
   Laufzeit vor einer Dateiänderung noch schreibt er danach Konfiguration B.
   Eine Rückkehr zum alten frischen Dateilesen im Endpunkt ließe den Test grün.
   Der Regressionstest muss A in der Composition-Root primen, die Datei im
   selben Prozess auf B ändern und anschließend belegen, dass die bereits
   gebaute Laufzeit und `/sources` beide weiterhin A zeigen. Ein Mutant soll
   den Test gezielt rot machen.

**Evidenz:** Produktgegenproben für den Key und die zwei Diagnosefälle tragen;
24 fokussierte Tests, `./_tickets/T-22-smoke.sh --run` 5/5, `ruff` und
`git diff --check` sauber. `make test`: Backend 637 passed / 29 skipped,
Plugin-API 36, Dashboard 259. Der Produktfehler ist behoben; die Rückgabe
schützt ausschließlich dessen Regression belastbar ab.
