# T-39 · English plugin developer guide with a runnable sample

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (documentation + `plugin_api` example) | wartend | 1 Tag | englischer Entwicklerleitfaden, minimales Paketbeispiel, keine Produktfunktion | — |

- **Angelegt:** 2026-08-29, auf Wunsch von Mike
- **Hängt ab von:** T-31 → T-38 → T-37 → T-35 vollständig technisch
  freigegeben
- **Reihenfolge:** ausdrücklich letztes **Plugin-/Produkt-Ticket** der aktuellen
  Kette; danach folgt nur noch das Meta-Ticket T-40 zur projektneutralen
  Wiederverwendung des Review-Regelwerks
- **Blockiert:** bis zum Abschluss der genannten Kette

**Löst:** Ein externer Entwickler soll ohne Kenntnis des StockInfo-Repositories
ein eigenes Datenquellen-Plugin verstehen, bauen, testen und installieren
können. Die Anleitung ist englisch, klar und knapp; ein vollständiges Sample
belegt den beschriebenen Weg.

---

## Scope-Vertrag

Aufgestellt vor der ersten Änderung, 2026-08-31.

- **Fachliche Änderungen:** keine. T-39 fügt Dokumentation und ein
  eigenständig baubares Beispielpaket hinzu; Produktverhalten, REST-Vertrag
  und Schema bleiben unberührt.
- **Neue Flächen:** `docs/plugin-authors.md` (kanonischer englischer
  Leitfaden) und `plugin_api/examples/us-example/` als **eigenes** Paket mit
  eigener `pyproject.toml`, Quelle und Tests.
- **Berührte Bestandsdateien:** `docs/plugins.md` (verweist auf den
  Leitfaden, statt ihn zu wiederholen), `docs/sources.yaml.example` nur, falls
  das Beispiel dort widerspricht, und dieses Ticket.
- **Budget:** höchstens 10 neue Dateien, 3 berührte Bestandsdateien und
  1.600 gesamte Diff-Zeilen. Der Leitfaden ist eine Lesestrecke, keine zweite
  Vertragsreferenz — vollständige Dataclass-Listen werden verlinkt.
- **Nicht-Ziele:** kein Eintrag des Samples in die Standardketten, kein
  zweiter Fallback-Mechanismus, kein Cache, keine UI, keine Änderung an
  `stockinfo_plugin` selbst, keine neue Testinfrastruktur außer den
  paketlokalen Tests des Samples.

Bei Überschreitung greift der Scope-Checkpoint-Riegel.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ bestätigt mit Einschränkung (Fußnote) ·
◑ teilweise (Fußnote) · ➖ keine Live-Verifikation (nur Unit/Review).
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | englischer Plugin-Leitfaden | Ein neuer Entwickler versteht in höchstens etwa 15 Minuten: Rollen, Identitäten, Pflichtfelder, Fehlersemantik und den kleinsten Plugin-Aufbau | ✅ | |
| **2** | Abschnitt `sources.yaml` | Paketinstallation, Quellenwahl und Reihenfolge sind getrennt erklärt; „first successful result wins“ sowie YAML als letztes Fallback sind mit einem vollständigen Beispiel sichtbar | ✅ | |
| **3** | Abschnitt Environment | `${NAME}` wird erklärt: exakte Ersetzung eines YAML-Werts, Verhalten bei fehlender Variable und sichere Beispiele für `.env`, Docker/Compose und Unraid; kein echter Schlüssel steht in Git | ✅ | |
| **4** | Entwickler-Sample | ein minimales installierbares US-Beispielpaket enthält `pyproject.toml`, Entry-Points, einen Resolver, eine Kursquelle und ausdrücklich den eingebrannten Literalwert `api_version = 2` | ✅ | |
| **5** | Sample-Tests | Contract-Kit und paketlokale Tests laufen ohne echtes Netz und ohne echten API-Key; HTTP-/Provider-Verhalten ist injizierbar oder gefakt | ✅ | |
| **6** | gebautes Sample-Wheel + frische Testumgebung | das Wheel lässt sich bauen, über eine fest gepinnte `plugins.packages`-Zeile installieren und nach Neustart in `GET /sources` erkennen | ✅ | |
| **7** | Sample-End-to-End | ein US-Instrument wird über das Sample aufgelöst und bepreist; ein dort nicht beantwortetes Instrument fällt nachweislich an die nächste Quelle zurück | ✅ | |
| **8** | Dokumentationsinventur | bestehende Plugin-Anleitungen widersprechen dem neuen Leitfaden nicht; veraltete Beispiele sind korrigiert, ersetzt oder verweisen auf die kanonische englische Anleitung | ✅ | |

### Was gelaufen ist

**Zeilen 1–3 · der Leitfaden** — `docs/plugin-authors.md`, 386 Zeilen, acht
Abschnitte in der Reihenfolge des Auftrags. Die Vertragsfelder sind
**verlinkt**, nicht abgeschrieben: Eine zweite Referenz läuft beim ersten
Nachtrag auseinander, und dann ist die falsche die, die jemand zuerst findet.
`${NAME}` ist mit `.env`, Docker Compose und Unraid belegt; kein Schlüssel im
Repository — der Abnahmelauf lief mit `US_MARKET_API_KEY=demo-key-not-a-secret`
aus der Prozessumgebung.

**Zeilen 4–5 · das Beispiel** — `plugin_api/examples/us-example/`, ein eigenes
Paket mit eigener `pyproject.toml`, einer Quelle in **zwei** Rollen und
`api_version = 2` im eigenen Klassenkörper. Der Anbieter ist ein Protokoll und
wird hereingereicht; die 43 Tests laufen ohne Netz und ohne Schlüssel, davon
rund 36 aus den geerbten Vertragssuiten.

**Ein Befund am eigenen Beispiel, und er steht jetzt im Leitfaden.** Der erste
Entwurf las `preferred_mic` als Filter — und die Quelle antwortete auf
**alles** `NotResponsible`, während der Code vernünftig aussah. Das Feld ist
ein Wunsch und nie leer: Der Host füllt es mit `XETR` vor. Gefunden hat das
nicht das Lesen, sondern der erste Lauf der geerbten Suite (7 rot). Der Fall
steht als Test (`test_a_preferred_venue_does_not_cancel_responsibility`), im
Quelltext des Beispiels und im Abschnitt „When it does not work".

**Zeile 6 · der echte Installationsweg** — Wheel gebaut, in `sources.yaml`
gepinnt (`stockinfo-source-us-example==0.1.0`), App gestartet:

```
plugin_env_installed   packages=1 path=…/plugin-env/2a9d70b521672eae
plugins_loaded         names=['us-example', 'yaml-file']
```

`GET /sources` danach: `us-example` in `resolvers` **und** `quotes`, beide
`configured: true`.

Ein Umweg war nötig und gehört benannt: Das Wheel liegt auf keinem Index. Der
Lauf setzte deshalb `PIP_FIND_LINKS` auf ein lokales Verzeichnis — pip-
Konfiguration des Betreibers, nicht des Plugins; `app/plugin_env.py` blieb
unberührt. Ein zusätzliches `PIP_NO_INDEX=1` scheiterte, weil dann auch die
transitive Abhängigkeit `PyYAML` nicht mehr auffindbar war.

**Zeile 7 · durch die ganze Kette**, Kette
`resolvers: [us-example, openfigi, yahoo-search]`, `quotes: [us-example, yfinance]`:

| Anfrage | Ergebnis | Wer hat geantwortet |
|---|---|---|
| `US0378331005` | `AAPL` / NASDAQ / 231,40 USD | das Beispiel, in beiden Rollen |
| `US88160R1014` | `TL0.DE` / Xetra / 301,50 EUR | das Beispiel führt Tesla nicht (`NotFound`) — OpenFIGI und yfinance übernehmen |
| `DE0007164600` | `SAP.DE` / Xetra / 190,30 EUR | das Beispiel ist unzuständig und wird gar nicht erst befragt |

Die mittlere Zeile ist der eigentliche Beleg: Der Rückfall geschieht **nach**
einer zuständigen Quelle, die nichts hatte.

**Zeile 8 · Inventur** — `docs/plugins.md` bleibt die deutsche Betreibersicht
und verweist für alles, was den Autor betrifft, auf den Leitfaden; die beiden
Autorenabschnitte („Was eine Auflösung tragen muss", „Den Vertrag selbst")
sind dort ersetzt statt gedoppelt. `docs/sources.yaml.example` widerspricht
nicht und bleibt unverändert.

**Eine Nebenwirkung, die ich melde statt sie zu verstecken:** T-38 belegt seine
Verify-Zeile 10 mit „`docs/plugins.md` — ein Plugin-Autor liest, welche Felder
er liefern muss". Dieser Inhalt steht jetzt in `plugin-authors.md`; der
Verweis führt über einen Klick dorthin. Ein Duplikat wäre genau das, was
dieses Ticket abschaffen soll.

---

## Verbindlicher Inhalt des Leitfadens

Der Leitfaden richtet sich an einen **Plugin-Autor**, nicht an einen StockInfo-
Core-Entwickler. Er erklärt nur, was dieser Autor zum Erfolg braucht:

1. **Mental model:** Ein Plugin liefert eine oder mehrere der fünf Rollen
   `resolver`, `quotes`, `daily`, `etf_meta` und `fx`. Geladen sein und in einer
   Kette ausgewählt sein sind zwei verschiedene Dinge.
2. **Contract:** aktuelle Identity-Union (`listed`, `pair`, `isin_only`),
   unterstützte Instrumenttypen, Pflichtfelder, `NotFound`/`Unavailable`,
   Capabilities und der explizite API-Versionsvertrag.
3. **Minimal package:** Projektlayout, Abhängigkeit auf
   `stockinfo-plugin-api`, Entry-Point-Gruppe `stockinfo.sources`, Build und
   Contract-Tests.
4. **Installation:** Entwicklung über `data/plugins/*.py`; Weitergabe als
   Wheel mit fester Version in `plugins.packages`; Neustart und Kontrolle über
   `GET /sources`.
5. **Configuration:** ein vollständiges `data/sources.yaml`, in dem ein
   US-Plugin vor den normalen Online-Quellen steht und `yaml-file` das letzte
   Fallback aller passenden Rollen ist.
6. **Environment variables:** Ein Wert wie `${US_MARKET_API_KEY}` verweist auf
   die Prozessumgebung. Der Schlüssel steht nie im YAML oder Repository.
   Beispiele decken lokale `.env`, Docker/Compose und eine Unraid-Variable ab.
7. **Fallback behavior:** Quellen werden in der geschriebenen Reihenfolge
   gefragt. Ein Erfolg beendet die Kette; eine ehrliche Nichtzuständigkeit
   erlaubt das nächste Glied. Das YAML-Plugin ergänzt fehlende Daten und
   überschreibt keinen früheren Online-Erfolg.
8. **Troubleshooting:** nur die häufigsten Fälle — Quelle nicht registriert,
   falsche `api_version`, fehlende Konfiguration, abgewiesenes ungepinntes
   Paket und Prüfung über `/sources`/Logs.

Die Anleitung soll grob **eine kurze Lesestrecke** bleiben. Vollständige
Dataclass-Referenzen oder Host-Interna werden verlinkt, nicht dupliziert.

---

## Das Entwickler-Sample

Das Sample ist ein kleines, eigenständig baubares Paket unter
`plugin_api/examples/`. Es ist absichtlich kein produktiver Marktdatenanbieter.
Es demonstriert am US-Markt nur den vollständigen Entwicklerweg:

- ein Resolver für eine begrenzte US-Zuständigkeit,
- eine Quote-Quelle für dieselbe Zuständigkeit,
- Konfiguration von API-Key und Basis-URL über `providers`,
- ein injizierbarer/fake HTTP-Pfad für deterministische Tests,
- Entry-Points für beide Quellen,
- geerbte Contract-Suiten plus wenige Beispiel-spezifische Tests,
- ein passendes `sources.yaml` und kurze Build-/Install-/Test-Kommandos.

Es implementiert **nicht** alle fünf Rollen, keinen eigenen Cache, keine UI und
keine zweite Fallback-Engine. Für `daily`, Metadaten, FX und manuelle Daten zeigt
die Konfiguration bewusst auf vorhandene Quellen weiter.

Das Konfigurationsbeispiel muss mindestens diese Form konkret ausarbeiten:

```yaml
plugins:
  packages:
    - stockinfo-source-us-example==0.1.0

resolvers: [us-example, openfigi, yahoo-search, yaml-file]
etf_meta:  [justetf, yfinance, yaml-file]
quotes:    [us-example, yfinance, yaml-file]
daily:     [yfinance, yaml-file]
fx:        [yfinance, yaml-file]

providers:
  us-example:
    api_key: ${US_MARKET_API_KEY}
    base_url: ${US_MARKET_BASE_URL}
  openfigi:
    api_key: ${OPENFIGI_API_KEY}
  yaml-file:
    path: /data/assets.yaml
```

Die konkrete Sample-Implementierung richtet sich nach dem **freigegebenen**
Stand aus T-31/T-38/T-37, nicht nach einem Zwischenstand dieses Tickets.

---

## Side-Effects

- Keine Änderung am Produktverhalten, REST-Vertrag oder Datenbankschema.
- Das Sample wird test- und paketierbar, aber nicht als produktive Quelle in
  die Standardketten aufgenommen.
- Bestehende Dokumentation darf konsolidiert werden; es entsteht keine zweite
  dauerhaft abweichende Plugin-Anleitung.

---

## Auflösung

_(wartend — erst nach der vollständigen technischen Freigabe von
T-31 → T-38 → T-37 → T-35)_
