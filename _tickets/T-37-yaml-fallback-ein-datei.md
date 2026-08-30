# T-37 · Ein YAML-Plugin, eine Datendatei, dieselbe Prüfstrecke

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Plugin-Beispiel + Prüfmittel) | bereit nach T-31/T-38 | 1 Tag | ein YAML-Plugin, eine Fachdaten-Datei, zwei Profile, gemeinsamer Smoke und Browser-Abnahme | — |

- **Angelegt:** 2026-08-28; auf YAML neu ausgerichtet am 2026-08-29
- **Hängt ab von:** T-31 und T-38
- **Danach:** T-35 wiederholen
- **Entscheidung Mike:** Das frühere CSV-Plugin wird vollständig ersetzt. Es
  gibt keinen Migrations- oder Kompatibilitätsweg, weil das Projekt noch in
  Entwicklung ist.

**Löst:** Ein Benutzer pflegt alle manuellen Fallback-Daten in genau einer
übersichtlichen YAML-Datei. Dasselbe Plugin arbeitet als vollständiges
Offline-Profil und als letztes Fallback des normalen Online-Profils, ohne eine
zweite Prüfstrecke zu erzeugen.

---

## Scope-Vertrag

- **Ergebnis:** Ein Plugin `yaml-file` bedient alle fünf Rollen aus **einer**
  YAML-Datei; die vier CSV-Beispiele sind entfernt, und derselbe Smoke läuft
  mit `PROFILE=yaml` wie mit `PROFILE=online` grün.
- **Fachliche Änderungen:** drei.
  1. **Eine** vom Benutzer gepflegte Datei, **ein** Parser, **ein** Schema —
     alle fünf Rollen lesen denselben Eintrag, nur je einen anderen Teil
     davon. Nicht zugesagt ist genau ein Lesevorgang: Der Host baut je Rolle
     eine Instanz, und das zu ändern wäre eine Lifecycle-Architektur für ein
     Problem, das niemand hat.
  2. Das Plugin deklariert alle drei Identitätsformen und alle sechs
     Gattungen — eine leere Deklaration hieße „nichts zugesagt", und der Host
     überspränge die Quelle für jede bekannte Gattung.
  3. Ein Kettentest spricht die Dateiquelle **über den Host** mit bekannter
     Gattung an. Diese Lücke überlebt sonst die Löschung der CSV-Beispiele:
     Heute schickt kein einziger Test eine Dateiquelle durch den Vorfilter.
- **Produktflächen/-dateien:** neu `plugin_api/examples/yaml_file.py`;
  entfernt `canada_file.py`, `metadata_file.py`, `prices_file.py`;
  `plugin_api/pyproject.toml` (Entry-Point und PyYAML als Abhängigkeit);
  `_tickets/T-35-smoke.sh` (Profilname und Vorbereitung).
- **Tests/Dokumentation:** neu `plugin_api/tests/test_yaml_file.py`; entfernt
  die drei CSV-Testdateien und die vier CSV-Fixtures;
  `tests/test_plugin_vertical.py` (benutzt heute `canada_file`);
  `docs/plugins.md` und `docs/sources.yaml.example`.
- **Nicht-Ziele:** kein Migrationsweg von CSV, keine Rückwärtskompatibilität,
  kein Hot Reload, keine zweite Smoke- oder Browser-Infrastruktur, keine neue
  Asset-Klasse außerhalb des Katalogs aus T-31/T-38.
- **Budget:** 5 Produktdateien, 8 Test-/Dokudateien, etwa 700 Diff-Zeilen.

**Zur Abhängigkeit:** `plugin_api` deklariert heute `dependencies = []`. PyYAML
kommt hinzu und steht deshalb ausdrücklich im Vertrag — im Environment liegt es
bereits, aber ein Paket, das eine Bibliothek benutzt und nicht nennt, ist bei
einer Fremdinstallation kaputt.

**Zur Diff-Schätzung:** Sie ist hoch, weil das Ticket vier Quellen durch eine
ersetzt. Der größere Teil ist Löschung; die 700 Zeilen sind Summe aus Zu- und
Abgang.

### Scope-Checkpoint 1 · `continue`

Codex-Entscheidung am 2026-08-30 gegen `f34cc3f`: Der Umfang bleibt **ein**
Ergebnis. 1.146 Diff-Zeilen sind der reine Abgang der ersetzten CSV-Beispiele,
Tests und Fixtures; die drei ungeplanten Produktdateien korrigieren zusammen
nur vier Zeilen mit Namen der gelöschten Beispiele. Ein eigenständig
lieferbares Teilstück oder eine neue Produktentscheidung ist nicht entstanden.

Das Budget wird einmalig auf **8 Produktdateien, 13 Test-/Dokudateien und
2.700 gesamte Diff-Zeilen** erweitert. Offen und erlaubt sind ausschließlich
`_tickets/T-35-smoke.sh`, `docs/plugins.md` und
`docs/sources.yaml.example`. Keine weitere Produktfläche. Eine zweite
Überschreitung führt gemäß Regelwerk grundsätzlich zu `reduce` oder `split`.

### Scope-Checkpoint 2 · `split`

Codex-Entscheidung am 2026-08-30 gegen `cc688a8`: Die im Browser belegte
fehlende Host-Kaskade für `quotes`, `daily` und `fx` ist eine neue
Produktabstraktion und nach der zweiten Scope-Überschreitung kein zulässiger
Rest dieses Tickets. T-37 schließt als eigenständig lieferbares **standalone
YAML-Plugin** ab; die Online-Fallback-Kaskade wird vor T-35 separat entworfen
und umgesetzt.

Für den T-37-Handoff werden das zusätzliche `_tickets/T-37-browser.sh` und der
neue Kaskaden-Rottest aus `cc688a8` wieder entfernt. Die bereits beobachtete
Browser-Abnahme bleibt als Beleg im Ticket, ohne neue Browser-Infrastruktur.
Der falsche Dashboard-Text, der `bond`, `crypto` und `fund` pauschal „Aktie“
nennt, wird als UI-Befund in T-35 geprüft; er erweitert T-37 nicht.

### Review Runde 1 · drei begrenzte Korrekturen

Codex-Review gegen `472a5e9`: Die vorhandenen Tests und der reine YAML-Smoke
sind grün, belegen aber drei Zusagen des Tickets noch nicht vollständig.

1. Der Parser muss die hier zugesagten Vertragsinvarianten beim Laden prüfen
   und Fehler als handlungsfähigen `configuration_problem` melden. Dazu
   gehören insbesondere doppelte kanonische Identitäten, ungültige
   Identitäten/Währungen/Zeitpunkte, nichtpositive oder nichtendliche Zahlen
   und doppelte History-Tage. Direkte negative Gegenproben müssen jeweils die
   verletzte Regel benennen; Reload nach Neustart wird ebenfalls wirklich
   gemessen.
2. „Eine Datei“ bedeutet die **eine vom Benutzer gepflegte Datei** und einen
   Parser/ein Schema. Der Host baut Quellen heute je Rolle; im gemessenen Lauf
   wurde dieselbe Datei deshalb fünfmal gelesen. T-37 bekommt dafür keine neue
   Host- oder Cache-Architektur. Die Zusage „einmal gelesen/gemeinsame Instanz“
   wird auf das tatsächlich benötigte Wartbarkeitsziel korrigiert.
3. Aktive Beispiele und Entwicklerdokumentation dürfen die abgespaltene
   Online-Kaskade nicht als vorhanden darstellen. Das Standalone-YAML-Profil
   bleibt; Online-Fallback wird klar als noch nicht implementiert bezeichnet.
   Veraltete CSV-Beispiele in aktiver Doku/Testhilfe werden in diesem Zug
   entfernt oder auf YAML umgestellt. Historische Befundtexte werden nicht
   flächig umgeschrieben. Matrix `#6` bleibt wegen des bereits festgehaltenen
   falschen Drilldown-Gattungstexts eingeschränkt statt vollständig grün.

### Review Runde 2 · Rollenvertrag und Lade-Rand schließen

Codex-Review gegen `3e97a9e`: Die Korrekturen aus Runde 1 sind im
abgespaltenen T-37-Umfang richtig umgesetzt. Offen bleiben zwei bereits vom
Scope verlangte Riegel:

1. Das angekündigte `plugin_api/tests/test_yaml_file.py` fehlt. Damit läuft
   das offizielle Beispiel nicht gegen die fünf Verträge seines eigenen Kits.
   Direkte Proben zeigen bereits: FX liefert `CAD/EUR`, obwohl `handles()`
   `False` meldet; `CAD/CAD` liefert nicht den Identitätskurs; Daily gibt auf
   eine Anfrage ab 2030 drei Werte aus 2026 zurück. Die fünf geerbten
   Rollenverträge werden nachgeliefert und nur diese Abweichungen behoben.
2. Die Invariantenprüfung deckt Fachwerte ab, aber noch nicht den vollständigen
   Lade-Rand des vorhandenen Schemas. Falsche Objekt-/Listenformen dürfen
   nicht aus dem Konstruktor werfen; unbekannte Schema-Version, unbekannte
   Gattung und unlesbare Metadatenwerte müssen schon als
   `configuration_problem` erscheinen, nicht erst beim Abruf.

Beide Blöcke bleiben in Parser und Rollenmethoden des vorhandenen Plugins.
Keine neue Abstraktion, kein Host-Umbau und keine Arbeit an T-41.

### Review Runde 3 · vollständige Grenzmatrix statt weiterer Einzelmutanten

Codex-Review gegen `b464471`: Die fünf Rollenverträge sind nun wirklich am
Beispiel verankert und die bekannten Rollenfehler behoben. Die behauptete
Vollständigkeit des Lade-Rands hält aber noch nicht: Falsch geformte
Identität, skalare Close-/FX-Einträge sowie numerischer Name/Typ werfen aus
dem Konstruktor; falsey Listen an Objektblöcken werden als fehlend gedeutet.

Der letzte Korrekturblock inventarisiert deshalb alle **vorhandenen**
Schema-Grenzen einmal als parametrisierte Matrix und validiert Metadaten gegen
ihre vorhandenen `FieldSpec`. Daneben werden zwei Vertragssemantiken
korrigiert: Ein bekanntes Papier ohne Tage im angefragten Fenster ergibt eine
leere `DailySeries`, und ein FX-Identitätskurs entsteht nur für gültige
Währungen. Das ist eine endliche Konsolidierung im vorhandenen Parser, keine
weitere Produktfläche und kein neues Schema-Framework.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ bestätigt mit Einschränkung (Fußnote) ·
◑ teilweise (Fußnote) · ➖ keine Live-Verifikation (nur Unit/Review) ·
⊘ in ein Folgeergebnis abgespalten (Fußnote).
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | `T-37-single-file-sample.yaml` + Schema-/Invariantentest | eine Datei enthält valide Beispiele für `listed`, `pair` und `isin_only` sowie `stock`, `etf`, `fund`, `crypto` und `bond`; ISIN, MIC, Währungen, Preise und History-Werte werden vor dem Lauf geprüft | ◑ [^review-r3] | |
| **2** | `PROFILE=yaml ./_tickets/T-35-smoke.sh --run` | der gemeinsame Smoke ist grün; `GET /sources` zeigt `yaml-file` in allen fünf Rollen und genau einen Pfad auf die Fachdaten-Datei | ✅ [^r1] | |
| **3** | `PROFILE=online ./_tickets/T-35-smoke.sh --run` | derselbe Smoke ist grün; normale Online-Quellen stehen zuerst und dasselbe `yaml-file` jeweils zuletzt | ⊘ [^split] | |
| **4** | Überschneidungs-Test im Online-Profil | liefert eine Online-Quelle einen gültigen Wert, gewinnt sie; YAML überschreibt ihn nicht. Nur bei fehlendem Ergebnis wird YAML gefragt | ⊘ [^split] | |
| **5** | Kurs-/History-Persistenz | Online- und YAML-Ergebnisse landen in der Datenbank. Manuelle `history` wird nur für Assets ohne abfragbare History verwendet; fehlt `price`, darf der jüngste Schlusskurs als aktueller Fallback dienen | ✅ [^r1] | |
| **6** | Browser, `PROFILE=yaml` | `BTC-EUR` (`pair`), eine Anleihe (`isin_only`) und ein nicht börsengehandelter Fonds (`fund`) lassen sich anlegen; Liste, Drilldown, Preis und manueller History-Fallback stimmen; Konsole und fehlgeschlagene Requests sind sauber | ⚠️ [^browser] | |
| **7** | Browser, `PROFILE=online` | BTC kommt über YFinance, die Anleihe ohne Online-Kurs über YAML; bei einem überlappenden Asset gewinnt online. Liste, Drilldown und Quellenanzeige stimmen; Konsole und Requests sind sauber | ⊘ [^split] | |
| **8** | Plugin-/Profil-Inventur | kein CSV-Profil und keine vier Datei-Quellen bleiben aktiv oder dokumentiert; `PROFILE=yaml` ist der einzige dateibasierte Prüfpfad | ✅ [^review-r2] | |
| **9** | Reload-/Fehlerfälle | fehlende Datei, ungültiges YAML, doppelte IDs und unzulässige Werte werden verständlich gemeldet; ein Neustart liest eine gültig geänderte Datei erneut ein | ◑ [^review-r3] | |

[^r1]: Umsetzung Runde 1. Die Orakel entstanden **vor** dem Code (dreizehn
    Fälle, alle rot) und stammen aus dieser Matrix. Belege: `PROFILE=yaml`
    und `PROFILE=online` je 20/20, `tests/test_yaml_profile.py` 13/13, der
    vertikale T-23-Lauf auf der neuen Quelle 18/18.
[^browser]: **Live gelaufen am 2026-08-30**, YAML-Profil im Browser — mit
    einer Einschränkung, die den Haken kostet: Der Drilldown nennt jede
    Nicht-ETF-Gattung „Aktie" und stand so unter einer Anleihe. Der Befund ist
    in T-35 festgehalten; solange er offen ist, stimmt „Drilldown … stimmen"
    aus dieser Zeile nicht vollständig.

    Beobachtet wurde: Drei
    Identitätsformen über die Oberfläche angelegt, jede mit dem Wert aus der
    Datei: `BTC-EUR` als `pair`/crypto mit 94.500,00 EUR, `DE0001102531` als
    `isin_only`/bond mit 99,42 EUR — dem **jüngsten Schlusskurs**, weil kein
    `price` in der Datei steht — und `DE0009848119` als `isin_only`/fund mit
    142,50 EUR. Die ISIN-Spalte des Paars zeigt „hat keine — Währungspaar"
    statt eines Editors. Konsole leer, alle Requests 200.

    Der Lauf hat außerdem zwei Befunde geliefert, die keine Suite sah: die
    fehlende Kaskade (Fußnote unten) und den Drilldown-Text, der jede
    Nicht-ETF-Gattung „Aktie" nennt. Letzterer steht in T-35.
[^split]: **Abgespalten, nicht erfüllt** (Codex, Scope-Checkpoint 2 am
    2026-08-30). Diese drei Zeilen verlangen eine Kaskade für `quotes`,
    `daily` und `fx`: Online zuerst, die Datei zuletzt, gefragt nur bei
    leerem Ergebnis. Die App kennt für diese Rollen keine Kette —
    `container._first` nimmt die erste einsatzbereite Quelle, und das ist
    dort seit jeher eine ausdrückliche Entscheidung.

    Der Befund stammt aus dem Browserlauf: Im Online-Profil bleibt die
    Anleihe ohne Kurs (`502 quote_unavailable`), obwohl `yaml-file` in
    `quotes` an zweiter Stelle steht. Eine Kaskade ist eine eigene
    Produktabstraktion und bekommt ein eigenes Ergebnis mit einem von Mike
    freigegebenen Entwurf.
[^review-r1]: **Codex Runde 1 gegen `472a5e9`:** Die positiven Standalone-
    Pfade sind grün. Offen sind die beim Laden zugesagte Vollvalidierung samt
    Reload-Gegenprobe sowie die aktive CSV-/Fallback-Dokumentationsinventur;
    Details stehen im Review-Abschnitt oberhalb der Matrix.
[^review-r2]: **Codex Runde 2 gegen `3e97a9e`:** Fachinvarianten, Reload und
    Dokumentationsinventur sind korrigiert. Noch offen sind die fünf direkten
    Rollenverträge des Beispiels sowie Schemafehler, die beim Laden nicht als
    `configuration_problem` enden; Details stehen im Review-Abschnitt.
[^review-r3]: **Codex Runde 3 gegen `b464471`:** Die fünf Rollenverträge sind
    eingebunden und die benannten Fälle korrigiert. Offen ist die einmalige
    vollständige Typmatrix des bestehenden YAML-Schemas sowie leere
    Daily-Fenster und ungültige FX-Identitätspaare; Details stehen oben.

Die Browserzeilen werden von Claude mit den tatsächlich beobachteten Assets,
Quellen und Ergebnissen belegt. Eine rein automatisierte Aussage ersetzt diese
Abnahme nicht.

---

## Zwei YAML-Dateien mit klar getrennten Aufgaben

`data/sources.yaml` ist **Konfiguration**. Es wählt Quellen, bestimmt ihre
Reihenfolge und zeigt dem Plugin den Pfad:

```yaml
resolvers: [openfigi, yahoo-search, yaml-file]
etf_meta:  [justetf, yfinance, yaml-file]
quotes:    [yfinance, yaml-file]
daily:     [yfinance, yaml-file]
fx:        [yfinance, yaml-file]

providers:
  openfigi:
    api_key: ${OPENFIGI_API_KEY}
  yaml-file:
    path: /data/assets.yaml
```

Das vollständige Online-Beispiel liegt in
[`T-37-sources-online-with-yaml-fallback.yaml`](T-37-sources-online-with-yaml-fallback.yaml).

`/data/assets.yaml` ist die **eine vom Benutzer gepflegte Fachdaten-Datei**.
Sie enthält Instrumente, optionale aktuelle Preise, optionale manuelle History,
Metadaten und Devisenkurse. Das abgestimmte Beispiel liegt in
[`T-37-single-file-sample.yaml`](T-37-single-file-sample.yaml).

`sources.yaml` zählt nicht als zweite Fachdaten-Datei: Sie existiert ohnehin
für jedes Profil und enthält keine Instrumentendaten.

---

## Verbindliches Datenmodell

```yaml
version: 1

instruments:
  - id: german-bond
    identity:
      kind: isin_only
      isin: DE0001102531
    name: Bundesrepublik Deutschland
    instrument_type: bond
    history:
      currency: EUR
      closes:
        - date: "2026-08-27"
          value: 99.42

  - id: bitcoin-eur
    identity:
      kind: pair
      base: BTC
      quote_currency: EUR
    name: Bitcoin
    instrument_type: crypto
    price:
      value: 94500.00
      currency: EUR
      as_of: "2026-08-27T17:30:00+02:00"
```

Verbindliche Regeln:

- aktueller Kurs heißt `price`, nicht `quote`;
- jede Identität folgt der Union aus T-31: `listed`, `pair` oder `isin_only`;
- jede erfolgreiche Auflösung trägt `name` und `instrument_type` gemäß T-38;
- der Typkatalog lautet `stock`, `etf`, `etc`, `fund`, `crypto`, `bond`;
- `fund` ist ein eigener Typ und wird nicht auf `etf` gerundet;
- normale History entsteht durch die jeweiligen Abfragen und wird in der
  Datenbank gespeichert;
- `history` im YAML ist ausschließlich der manuell gepflegte Fallback, wenn
  keine konfigurierte Quelle die History dieses Assets abfragen kann;
- auch YAML-Kurse und -History werden in die Datenbank übernommen;
- fehlt `price`, darf der jüngste Eintrag aus `history.closes` als aktueller
  Preis-Fallback dienen;
- ein Instrument darf Metadaten und Preis ohne History tragen; leere
  Platzhalterblöcke sind unnötig.

---

## Eine Implementierung, fünf Rollen

Das Plugin `yaml-file` liest und validiert die Datei mit **einem** Parser
gegen **ein** Schema und stellt denselben Stand für alle Rollen bereit:

| Rolle | Antwort aus `/data/assets.yaml` |
|---|---|
| `resolvers` | Identität, Name und Instrumenttyp |
| `quotes` | optionaler aktueller `price` oder jüngster manueller Schlusskurs |
| `daily` | optionale manuelle `history` |
| `etf_meta` | optionale Metadaten |
| `fx` | optionale Einträge aus `fx_rates` |

Parser, Indexierung und Invarianten werden nicht fünfmal **implementiert** —
darum geht es. Ausgeführt werden sie je Rolle einmal, weil der Host je Rolle
eine Instanz baut; gemessen liest die Quelle die Datei damit fünfmal. Das ist
gewollt hingenommen und nicht Gegenstand dieses Tickets: Eine
rollenübergreifende Zwischenspeicherung wäre eine Host-Architektur, und die
Datei ist klein und wird beim Start gelesen.

### Was `yaml-file` deklarieren muss — und ein Befund, der es begründet

*(Aus T-31 Runde 5, 2026-08-29. Der Grund gehört hierher, weil der Code, an
dem er auffiel, mit diesem Ticket verschwindet.)*

Seit T-31 heißt eine **leere** `SUPPORTED_TYPES` „nichts zugesagt" und nicht
„alles"; der Host überspringt eine solche Quelle für jede *bekannte* Gattung.
`yaml-file` muss seine Gattungen deshalb ausschreiben — es liest eine
Dateizeile und ist für jede Gattung des Katalogs zuständig. Dasselbe gilt für
`SUPPORTED_KINDS`: Die YAML-Datei führt alle drei Identitätsformen, also
`{"listed", "pair", "isin_only"}`.

**Der Befund dahinter ist wichtiger als die Regel.** Aufgefallen ist das nicht
in den 834 Unit-Tests, sondern erst im Smoke-Lauf: `PROFILE=csv` fiel mit 12
von 20 aus, während `PROFILE=online` grün blieb. **Kein einziger Unit-Test
schickt eine Dateiquelle mit bekannter Gattung durch den Vorfilter** — die
Fakes der Kettentests sind Kursquellen ohne Deklaration, und die
Beispiel-Plugins werden nur in ihren eigenen Contract-Tests gefragt, wo es
keinen Host und damit keinen Vorfilter gibt.

Diese Lücke überlebt die Löschung der CSV-Beispiele, wenn niemand sie
schließt. Für `yaml-file` heißt das: **ein Kettentest, der die Quelle über
den Host mit einer bekannten Gattung anspricht** — nicht nur die
Rollen-Suiten des Contract-Kits.

---

## Ein Smoke, zwei Profile

`_tickets/T-35-smoke.sh` bekommt zwei Profile, aber nur eine Prüfimplementierung:

```bash
PROFILE=online ./_tickets/T-35-smoke.sh --run
PROFILE=yaml   ./_tickets/T-35-smoke.sh --run
```

Das Profil darf nur Testdaten und `sources.yaml` vorbereiten. Die fachlichen
Checks darunter fragen nach denselben Ergebnissen und enthalten keine
profilabhängigen Sonderpfade. Wo einzelne Assets verschiedene Erwartungswerte
brauchen, stehen diese in einer kleinen Profiltabelle; die Prüfmechanik bleibt
gemeinsam.

### Reines YAML-Profil

Alle fünf Ketten bestehen nur aus `[yaml-file]`. Es arbeitet ohne Netz und
beweist, dass ein fremdes Plugin den gesamten MVP-Vertrag bedienen kann.

### Online-Profil mit YAML-Fallback

OpenFIGI, Yahoo Search, YFinance und justETF bleiben die normalen Quellen.
`yaml-file` steht in jeder unterstützten Kette zuletzt. Es ergänzt insbesondere
Anleihen oder andere Assets ohne Online-Kurs, ist aber nie ein Override.

---

## Fehler- und Reload-Semantik

- Der Pfad kommt ausschließlich aus `providers.yaml-file.path`; es gibt keine
  Dateisuche und keinen zweiten Vorgabepfad.
- Eine fehlende oder ungültige Datei macht die Quelle sichtbar nicht
  einsatzbereit; die App nennt einen handlungsfähigen Grund in `/sources` und
  im Log.
- Doppelte `id` oder doppelte kanonische Identitäten sind Fehler, keine
  Last-write-wins-Regel.
- Werte werden gegen die Invarianten des Plugin-Vertrags geprüft. Ungültige
  ISIN, Identitätsform, Währung, Zeitangabe oder nichtpositive/nichtendliche
  Zahlen werden benannt und nicht teilweise geladen.
- Plugins werden beim App-Start geladen. Eine Änderung der Datei wird deshalb
  nach Neustart wirksam; Hot Reload ist nicht Teil dieses Tickets.

---

## Side-Effects

- Das bisherige CSV-Profil und seine vier Quellen werden entfernt statt
  parallel unterstützt.
- Keine Datenmigration und keine Rückwärtskompatibilität.
- Keine zweite Smoke- oder Browser-Testinfrastruktur.
- Keine neue Asset-Klasse außerhalb des in T-31/T-38 entschiedenen Katalogs.

---

## Auflösung

_(Umgesetzt am 2026-08-30, Runde 1, im abgespaltenen Umfang: das
eigenständige YAML-Plugin. Die Zeilen `#3`, `#4` und `#7` sind in ein
Folgeergebnis abgespalten.)_

Vier Dateiquellen sind eine geworden. `yaml-file` liest eine Datei und bedient
daraus jede Rolle; die Rollen unterscheiden sich darin, **was** sie aus
demselben Eintrag lesen, nicht darin, wie sie ihn finden.

**Der Befund aus T-31 ist geschlossen.** Bis hierher schickte kein einziger
Test eine Dateiquelle mit bekannter Gattung durch den Vorfilter des Hosts —
aufgefallen war das nicht in den Unit-Tests, sondern erst im Smoke-Lauf. Der
vertikale T-23-Lauf tut es jetzt, und `yaml-file` deklariert alle drei
Identitätsformen und alle sechs Gattungen.

**Zwei Testbefunde aus dem Bau, beide von derselben Art.** Die Orakel waren
zwischenzeitlich grün, ohne etwas zu prüfen: Eine unbekannte Quelle in
`sources.yaml` lässt die Kette leer, die App fällt auf ihre eingebauten
Online-Quellen zurück, und für ein bekanntes Papier antwortet das Netz. Und
zwei Zusicherungen im vertikalen Lauf blieben nach der Löschung grün, weil
`/sources` konfigurierte Namen auch dann listet, wenn es die Quelle nicht
gibt.

Beide zeigen dasselbe: Ein Test, der nur „es kam eine Antwort" verlangt, misst
die Verkabelung seines Aufbaus. Die Orakel prüfen deshalb den **Wert aus der
Datei**.
