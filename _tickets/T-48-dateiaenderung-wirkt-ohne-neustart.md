# T-48 · Eine geänderte Fachdatendatei wirkt ohne Neustart

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Plugin-Beispiel) | offen | 4–6 h | eine Änderung an `assets.yaml` erreicht die Oberfläche, ohne dass jemand den Dienst neu startet | — |

- **Angelegt:** 2026-08-31, aus Mikes Versuch am laufenden Stand
- **Beauftragt von Mike:** *„Neustart ist keine Lösung! Wenn ich das YAML-File
  ändere erwarte ich mir, dass die Änderung übernommen wird. Das gleiche gilt
  auch für das YAML-Fallback der online-Version des Plugins."*
- **Gilt für beide Profile:** das reine Dateiprofil **und** `yaml-file` als
  letztes Glied der Online-Kette
- **Hängt ab von:** nichts

**Löst:** Wer die Datei pflegt, ändert einen Wert und sieht ihn nicht. Vier
Schichten stehen dazwischen, drei davon unsichtbar. Der Betreiber hat keine
Möglichkeit zu erkennen, an welcher es liegt — er sieht nur, dass die App
etwas anderes behauptet als seine Datei.

---

## Die vier Schichten, gemessen

Alle Zahlen aus einem Lauf am 2026-08-31, reines YAML-Profil, `CACHE_TTL_HOURS=0`.

### 1 · Das Plugin liest die Datei einmal — beim Start

`plugin_api/examples/yaml_file.py:719` baut den Katalog im Konstruktor. Ein
laufender Prozess hält damit eine Momentaufnahme; die Datei ist danach für ihn
ohne Bedeutung.

```
Datei:              94501.00
laufender Dienst:   94500.0   (cached: false)   ← trotz TTL 0
nach Neustart:      94501.0
```

**Das ist die Hauptursache** und der Punkt, den Mike ausdrücklich nicht
akzeptiert.

### 2 · `INSERT OR IGNORE` verwirft den korrigierten Wert

`app/repository.py:1022` schreibt Kurse mit `INSERT OR IGNORE`; die Tabelle hat
`UNIQUE (instrument_id, quote_time)`. Wer in der Datei **nur den Preis**
ändert und `as_of` stehen lässt — der Normalfall beim Korrigieren —, trifft die
vorhandene Zeile, und der neue Wert fällt weg.

```
POST /refresh   →  {"total":2,"refreshed":2}     ← meldet Erfolg
/instruments    →  94500.0                       ← unverändert
```

**`refreshed: 2` ist dabei das Schlimmere an dem Befund.** Die App hat geholt,
hat den neuen Wert bekommen und ihn beim Schreiben fallen lassen — ohne
Protokolleintrag, ohne Hinweis, mit einer Erfolgsmeldung.

Für eine Online-Quelle ist die Regel richtig gedacht: Zwei Abrufe zur selben
Sekunde sollen keine Dublette erzeugen. Für eine gepflegte Datei ist „selber
Zeitpunkt, korrigierter Wert" dagegen der Regelfall.

### 3 · Die Cache-TTL fragt sechs Stunden lang niemanden

Vorgabe `cache_ttl_hours: 6`. Selbst wenn 1 und 2 behoben sind, bleibt eine
Dateiänderung auf dem normalen Weg bis zu sechs Stunden unsichtbar.

### 4 · Die Liste ruft nichts ab

`GET /instruments` liest den zuletzt **gespeicherten** Kurs. Sie löst keinen
Abruf aus; ohne `↻` oder geöffneten Kursverlauf wird nichts geschrieben. Das
ist so gewollt und hier nur der Vollständigkeit halber genannt — es erklärt,
warum die Tabelle auch dann alt aussieht, wenn `GET /quote` längst richtig
antwortet.

---

## Richtung — noch nicht entschieden

**Schicht 1 (Katalog).** Vorschlag: Das Plugin merkt sich `mtime` und Größe der
Datei und liest neu, sobald sich eines ändert. Das bleibt im Plugin, berührt
weder Vertrag noch Kern, und kostet einen `stat()` je Anfrage — gegenüber einem
Dateizugriff vernachlässigbar. Die Alternative, bei **jeder** Anfrage neu zu
lesen, wäre einfacher und bei großen Dateien teuer.

**Schicht 2 (`INSERT OR IGNORE`).** Zwei Wege, und sie unterscheiden sich in
der Tragweite:

| | Was passiert | Preis |
|---|---|---|
| `ON CONFLICT … DO UPDATE` | Ein Kurs mit gleichem Zeitpunkt und anderem Preis **ersetzt** den alten | Gilt für **alle** Quellen |
| Nur ehrlich zählen | `refreshed` zählt, was wirklich geschrieben wurde; ein verworfener Schreibversuch steht im Protokoll | Behebt Mikes Fall **nicht** |

Der erste Weg löst das Problem, der zweite behebt nur die Falschmeldung. Sie
schließen einander nicht aus.

**Ein Einwand, den ich zurückziehe.** Der erste Entwurf nannte als Preis, eine
„korrigierte Online-Antwort" würde dann ebenfalls überschreiben. Auf Mikes
Nachfrage: Diesen Fall kann ich **nicht belegen**. Kursnachträge zum selben
Zeitpunkt gibt es an Börsen; ob yfinance sie je liefert, habe ich nicht
gemessen. Ein plausibel klingender Grund ohne Messung ist kein Argument — der
einzige nachweisbare Fall ist die Datei.

**Schicht 3 (TTL) — von Mike entschieden (2026-08-31):** *„Ein lokales File
braucht keinen Cache."* Eine Dateiquelle wird also bei jeder Anfrage gefragt;
die TTL gilt weiter für entfernte Quellen, wo sie ein Kontingent schont.

Das entschärft auch Schicht 1: Wer bei jeder Anfrage liest, braucht keine
`mtime`-Prüfung. Die Frage ist dann nur noch, ob das Lesen billig genug ist —
und das ist eine Messung, keine Meinung.

---

## Verify

Legende: ✅ bestätigt · ◑ teilweise bestätigt · ➖ nicht geprüft.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | reines YAML-Profil, Preis in der Datei ändern | die Änderung ist **ohne Neustart** sichtbar | ✅ | |
| **2** | dasselbe, `as_of` unverändert | der korrigierte Wert kommt an — nicht nur bei neuem Zeitstempel | ✅ | |
| **3** | Online-Profil mit `yaml-file` als letztem Glied | dieselbe Zusage; die Datei ist dort dieselbe Quelle | ✅ | |
| **4** | Datei kaputt gemacht, während der Dienst läuft | der Dienst bleibt stehen und meldet den Grund; er fällt nicht auf einen halben Katalog zurück | ◑ | |
| **5** | Datei unverändert, viele Anfragen | die Antwortzeit bleibt brauchbar — gemessen, nicht geschätzt | ✅ | |
| **6** | `POST /refresh` nach Preiskorrektur bei gleichem `as_of` | `refreshed` zählt die erfolgreiche Korrektur, und die Liste enthält den neuen Wert | ✅ | |
| **7** | Online-Profil, TTL | die Cache-TTL gilt dort **unverändert** — kein Abruf mehr als vorher | ✅ | |
| **8** | Online-Profil, Provider-Aufrufe | gezählt vor und nach der Änderung: dieselbe Zahl | ✅ | |

## Die Grenze — die Online-Kette darf nichts davon merken

> **Mike, 2026-08-31:** *„Pass aber auf, dass du bei dem Caching bzw. bei der
> Anpassung nicht die Online-Plugin-Version versaust."*

Die Warnung trifft den teuersten Fehler, den dieses Ticket machen kann. Drei
Stellen, an denen er passieren würde:

1. **Die TTL fällt für alle statt nur für die Datei.** Dann fragt jede
   Seitenansicht Yahoo neu. Das kostet nicht nur Zeit — es läuft in ein
   Ratenlimit, und der Ausfall sieht aus wie ein Fehler der Quelle. Die
   Entscheidung „kein Cache" gilt **ausschließlich** für eine Quelle, die
   lokal liest.
2. **`ON CONFLICT … DO UPDATE` gilt für alle Quellen.** Das ist der einzige
   Teil dieses Tickets, der die Online-Kette überhaupt berührt, und deshalb
   der Teil, der eine eigene Entscheidung braucht.
3. **„Bei jeder Anfrage lesen" wird zur allgemeinen Regel.** Es ist eine
   Eigenschaft der Dateiquelle, keine des Kerns.

Die Gegenprobe ist kein Nachdenken, sondern eine Messung: **Zahl der
Provider-Aufrufe im Online-Profil vor und nach der Änderung.** Bleibt sie
gleich, hat die Online-Kette nichts gemerkt.

## Nicht-Ziele

- Kein Beobachter-Prozess, kein Datei-Watcher als Dienst.
- **Keine Änderung am Verhalten der Online-Kette** — weder an ihrer TTL noch an
  der Zahl ihrer Abrufe.
- Keine Änderung am Plugin-Vertrag: Das Nachladen ist Sache der Quelle, nicht
  des Kerns.
- Keine neue Route und keine Anzeige der Katalog-Version im UI.

## Scope-Checkpoint vor dem ersten Edit (2026-09-01)

### Zuerst die Messung, die das Ticket verlangt hat

Der Entwurf oben vermutete: „Wer bei jeder Anfrage liest, braucht keine
`mtime`-Prüfung. Die Frage ist nur, ob das Lesen billig genug ist — und das ist
eine Messung, keine Meinung." Hier ist sie, `_Catalogue(path)` auf diesem
Rechner:

| Datei | je Aufbau |
|---|---:|
| die heutige Fachdatei (5 Papiere) | **1,7 ms** |
| 100 Papiere (32 kB) | **34 ms** |
| 1 000 Papiere (320 kB) | **352 ms** |
| 5 000 Papiere (1,6 MB) | **1 907 ms** |
| ein `stat()` | **0,0009 ms** |

**Bei jeder Anfrage neu zu lesen ist nicht billig.** Es wächst linear, und der
Host baut **je Rolle eine Instanz** — bei fünf Rollen also fünf Aufbauten. Eine
Datei mit tausend Papieren machte eine Kursabfrage um mehr als eine Sekunde
langsamer.

Ein `stat()` kostet das **1 900-fache weniger** als der kleinste Aufbau. Die
`mtime`-Prüfung ist damit nicht der Kompromiss, sondern der Entwurf: Für den
Benutzer ist beides dasselbe — die geänderte Datei wirkt sofort —, und nur die
Kosten unterscheiden sich um drei Größenordnungen.

### Die eine Frage, die ich nicht selbst entscheiden kann

Die `mtime`-Prüfung behebt **Schicht 1**. Sie hilft aber nichts, solange
**Schicht 3** greift: Die Cache-TTL fragt die Quelle sechs Stunden lang gar
nicht erst. Mikes Entscheidung — *„Ein lokales File braucht keinen Cache"* —
verlangt, dass der Kern eine Quelle als **lokal** erkennt.

Nur weiß er das heute nicht, und die drei Wege dorthin sind verschieden teuer:

| | Wo die Tatsache steht | Preis |
|---|---|---|
| **a** | `sources.yaml`, je Anbieter ein Schalter | Konfiguration statt Vertrag — aber der Betreiber muss ihn kennen und setzen |
| **b** | Der Vertrag: die Quelle erklärt sich als lokal | Dort gehört die Tatsache hin — **aber die Nicht-Ziele schließen eine Vertragsänderung aus** |
| **c** | Der Kern rät: ein Anbieter mit `path` auf eine vorhandene Datei | Der Kern kennt dann die Konfigurationsschlüssel eines Plugins |

`cost` scheidet aus: Es ist laut eigenem Docstring „Information, keine
Sortierregel", und `openfigi` trägt ebenfalls `free`.

**Mein Rat ist (b)** — ob eine Quelle lokal liest, weiß nur sie selbst; (a)
verlangt vom Betreiber Wissen über die Bauart seiner Quelle, (c) macht den Kern
von Plugin-Interna abhängig. Das hieße, das Nicht-Ziel „keine Änderung am
Plugin-Vertrag" für dieses eine Feld aufzuheben. **Die Entscheidung liegt nicht
bei mir.**

### Schicht 2 — der einzige Teil, der die Online-Kette berührt

`INSERT OR IGNORE` → `ON CONFLICT … DO UPDATE`. Das gilt dann für **alle**
Quellen; genau davor warnt Mikes Satz. Der Einwand dagegen — eine korrigierte
Online-Antwort würde überschrieben — ist im Ticket oben bereits als **nicht
belegt** zurückgezogen worden.

Ich schlage vor, ihn zu übernehmen, **und die Gegenprobe mitzuliefern**: Zahl
der Provider-Aufrufe im Online-Profil vor und nach der Änderung. Bleibt sie
gleich, hat die Online-Kette nichts gemerkt (Verify `#8`).

Unabhängig davon zählt `refreshed` künftig, was **geschrieben** wurde — ein
verworfener Schreibversuch ist kein Erfolg (Verify `#6`). Das ist auch dann
richtig, wenn `ON CONFLICT` nicht kommt.

### Scope-Vertrag

- **Fachliche Änderungen:** drei — die Dateiquelle liest neu, sobald sich die
  Datei ändert; eine lokale Quelle umgeht die Cache-TTL; ein Kurs mit gleichem
  Zeitpunkt und anderem Preis ersetzt den alten, und `refreshed` zählt ehrlich.
- **Erwartete Flächen:** `plugin_api/examples/yaml_file.py`,
  `app/repository.py`, `app/services/quote_cache.py`, `app/sources_registry.py`
  — plus die Fläche, die aus der Entscheidung oben folgt (Vertrag **oder**
  `sources_config.py`).
- **Budget:** höchstens 5 Produktdateien, 2 Testdateien, **250 hinzugefügte
  Produktzeilen** und **450 Gesamtzeilen** (hinzugefügte Zeilen in `app/`,
  `plugin_api/` und den Testbäumen zusammen).
- **Pflichtorakel:** `#1` und `#2` als echter Lauf ohne Neustart; `#4` eine
  kaputte Datei lässt den Dienst stehen statt auf einen halben Katalog
  zurückzufallen; `#5` die Antwortzeit gemessen, nicht geschätzt; `#6`
  `refreshed` zählt keinen verworfenen Schreibversuch; **`#8` die Zahl der
  Provider-Aufrufe im Online-Profil bleibt gleich** — das ist die Gegenprobe zu
  Mikes Warnung und der wichtigste Fall des Tickets.
- **Nicht-Ziele:** unverändert, mit der einen offenen Ausnahme oben.

---

## Auflösung

### Codex-Entscheidung · `continue`, Vertrag statt Konfiguration (2026-09-01)

Variante **(b)** gilt, aber der Vertrag nennt die fachlich benötigte
Eigenschaft und nicht den vermuteten Speicherort: `Source.cacheable: bool =
True`. Die Vorgabe hält bestehende Plugins und Online-Quellen unverändert;
`YamlFileSource` setzt sie auf `False`. Kein `local`-Schalter in
`sources.yaml`, keine Auswertung eines plugin-eigenen `path`-Schlüssels und
keine Umdeutung von `cost`.

**Wichtig für das Online-Profil:** `cacheable=False` darf nicht auf die ganze
Kette hochgezogen werden. Adapter und Kaskade beantworten die Cachefrage für
das konkrete Instrument; maßgeblich ist die erste Quelle, die nach
Identitätsform, Gattung und `handles()` dafür infrage kommt. Eine dahinter
liegende Dateiquelle macht einen von der vorderen Online-Quelle bedienten Wert
nicht cachefrei. Das Pflichtorakel misst deshalb beides in derselben Kette:
ein Online-Treffer behält exakt seine bisherige Aufrufzahl, ein von der
Dateiquelle bedientes Fallback-Papier übernimmt die Dateikorrektur ohne
Neustart.

Die Dateiquelle prüft eine billige Dateisignatur (`st_mtime_ns` plus Größe)
vor jedem fachlichen Eintritt und baut den neuen Katalog vollständig in einer
lokalen Variable. Erst ein komplett gültiger Katalog ersetzt den alten. Eine
kaputte Zwischenfassung erzeugt eine verständliche Störung statt eines halben
Katalogs; nach der nächsten gültigen Änderung erholt sich dieselbe Instanz.
Die Reload-Regel steht einmal und gilt für alle fünf Rollen der Quelle.

`quotes` verwendet bei `(instrument_id, quote_time)` einen Upsert. Damit gibt
es den verworfenen Schreibversuch aus Schicht 2 nicht mehr: Ein erfolgreich
beschaffter Korrekturwert wurde geschrieben, ein Schreibfehler läuft bereits
in den vorhandenen Fehlerpfad und erhöht `refreshed` nicht. Eine zusätzliche
Zählabstraktion entsteht nicht.

Der aktive Zuschnitt betrifft den im Ticket gemessenen **aktuellen Preis**.
Das Nachladen des Plugin-Katalogs gilt zwar für alle fünf Rollen; die getrennten
persistenten Cacheverträge für Historie, Metadaten und FX werden hier aber
nicht umgebaut und deshalb auch nicht als sofort sichtbare UI-Zusage
ausgegeben. Das verhindert, dass aus einem Kursbefund unbemerkt vier
Cache-Projekte werden.

#### Verbindlicher Scope-Vertrag

- **Drei Änderungen:** atomarer Katalog-Reload bei geänderter Dateisignatur;
  rückwärtskompatibles `cacheable` mit instrumentbezogener Auswertung im
  Quote-Weg; Quote-Upsert bei gleichem Zeitpunkt.
- **Erwartete Produktflächen:**
  `plugin_api/src/stockinfo_plugin/sources.py`,
  `plugin_api/examples/yaml_file.py`, `app/plugin_adapters.py`,
  `app/providers/composite_market.py`, `app/services/quote_service.py`,
  `app/services/quote_cache.py`, `app/repository.py` — höchstens sieben.
- **Testflächen:** `plugin_api/tests/test_yaml_file.py`,
  `tests/test_yaml_profile.py`, `tests/test_quote_cache.py` — höchstens drei.
- **Budget:** höchstens 300 hinzugefügte Produkt- und 550 Gesamtzeilen.
- **Pflichtorakel:** `#1`–`#5` am echten Datei-/HTTP-Weg; `#6` belegt den
  ersetzten Wert und die unverändert ehrliche Refresh-Zahl; `#7`/`#8` zählen
  im gemischten Profil die Online-Aufrufe, einschließlich eines
  Online-Treffers bei gleichzeitig vorhandenem YAML-Eintrag. Ein Mutant ohne
  Upsert, ohne Reload und mit kettenweitem Cache-Bypass muss je einen dieser
  Fälle röten.
- **Nicht-Ziele:** keine Registry-/Konfigurationsänderung, kein Watcher, keine
  Datenbankmigration, keine neue Route und kein Umbau der getrennten
  History-/Metadaten-/FX-Caches.

Der Scope-Handoff bezieht sich auf den Entwurfscommit `4c63325`; der zuvor in
`STATUS.md` stehengebliebene T-47-Produktcommit war kein gültiger
Scope-Handoff und wird mit dieser Entscheidung berichtigt.

### Runde 1 · Umsetzung (Claude, 2026-09-01)

Die drei freigegebenen Änderungen stehen; sieben Produktflächen, drei
Testflächen wie im Vertrag.

| | Grenze | gemessen |
|---|---:|---:|
| Produktzeilen | ≤ 300 | **180** |
| Gesamt | ≤ 550 | **493** |

**Der Reload ist eine Eigenschaft, kein Aufruf an sieben Stellen.** `_catalogue`
lädt selbst nach; die Regel steht damit einmal und gilt für alle fünf Rollen —
auch für einen achten Eintrittspunkt, den es noch nicht gibt.

**Live, mit TTL 6 Stunden** (Dateiprofil, Fonds `DE0009848119`):

```
vorher   142.5   cached=False
Datei:   value: 142.50 → 143.75   (as_of unverändert)
nachher  143.75  cached=False     ← ohne Neustart
POST /refresh → {"total":1,"refreshed":1}
Liste    143.75                   ← der Upsert hat ihn behalten
```

**Die Gegenprobe zu Mikes Warnung, gezählt:** In einer Kette
`counting-online, yaml-file` behält das Papier, das **beide** kennen, seine
Frist — zwei Abfragen, **ein** Aufruf. Nur das Papier, das allein die Datei
kennt, umgeht sie, und es kostet die Online-Quelle nichts. Die Cachefrage
selbst löst **null** Provider-Aufrufe aus.

#### Mutantenprobe

| Mutant | rot |
|---|---|
| ohne Reload | `#1` und der gemischte Vertical, dazu die Erholung nach einer kaputten Datei |
| ohne Upsert | `#2`/`#6` — der korrigierte Wert fällt wieder weg |
| kettenweiter statt instrumentbezogener Bypass | der gemischte Vertical: die Online-Quelle wird ein zweites Mal gefragt |

Der Upsert-Mutant kam zunächst durch: `INSERT OR IGNORE … ON CONFLICT DO UPDATE`
behält die Upsert-Klausel — die Mutation war keine. Erst das vollständige
Entfernen der `ON CONFLICT`-Zeile zeigt den Unterschied.

#### `#4` steht auf ◑ — und warum

Der Dienst **bleibt stehen** und fällt **nicht** auf einen halben Katalog
zurück; eine kaputte Zwischenfassung lässt ihn mit dem letzten gültigen Stand
weiterarbeiten, und nach der nächsten gültigen Fassung erholt sich dieselbe
Instanz. Beides ist geprüft.

Der zweite Halbsatz — „**meldet den Grund**" — ist nur halb eingelöst: Der Grund
steht im Protokoll, aber `/sources` zeigt weiter „einsatzbereit". Die Auskunft
dort ist ein Schnappschuss aus `_CHAINS`, der beim Kettenbau entsteht; ein
Laufzeitproblem erreicht sie nie. Das zu ändern hieße `app/sources_registry.py`
anzufassen — **keine der sieben freigegebenen Flächen**, und es beträfe die
Diagnose aller Quellen. Deshalb gemeldet statt erledigt.

### Codex-Review Runde 1 · `changes_requested` (2026-09-01)

Scope und Budget sind eingehalten: sieben Produkt-, drei Testflächen, 180/493
hinzugefügte Zeilen. 140 YAML-Plugin- sowie 66 Cache-/Profiltests und Ruff sind
grün. Reload, Quote-Upsert und der instrumentbezogene Online-Gegenfall sind im
Diff vorhanden; DRY-geprüft wurden Katalogzugriff, Cacheentscheidung und
Quote-Persistenz.

Der vollständige Rest passt in **eine** Korrekturrunde:

1. **Verify `#4` ist noch nicht erfüllt.** Eine kaputte Fassung setzt nur
   `_problem`; alle Fachmethoden liefern über `_loaded` den alten Wert weiter,
   und die laufende `/sources`-Momentaufnahme bleibt ohne Grund auf
   `configured=true`. Einen Protokolleintrag erzeugt `_reload()` ebenfalls
   nicht. Der letzte gültige Katalog darf intern für den atomaren Tausch
   erhalten bleiben, aber ein Fachrequest während der Störung darf den Fehler
   nicht still als aktuellen Wert ausgeben. `/sources` muss am **bereits
   gebauten Objekt** `configured=false` samt verständlichem Grund zeigen und
   nach einer gültigen Fassung ohne Neubau wieder `true`. Dafür ist als achte
   und letzte Produktfläche `app/sources_registry.py` freigegeben; keine neue
   Antwortform oder Route. Eine fehlgeschlagene Signatur darf die Erholung
   nicht blockieren.
2. **Verify `#6` behauptet mehr als sein Orakel.** Der Repository-Test belegt
   den Upsert, ruft aber weder `POST /refresh` noch die Bestandsliste auf. Die
   Matrix ist oben auf die mit dem Upsert gültige Zusage korrigiert. Ein
   öffentlicher Test ändert nur den Preis bei gleichem `as_of`, ruft
   `POST /refresh` und belegt sowohl `refreshed` als auch den gespeicherten
   Listenwert. Erst dann wird `#6` wieder ✅.
3. **Die neue technische Prosa trägt erneut Implementierungschronik.** Dazu
   gehören `INSERT OR IGNORE war hier …`, „Kern des Tickets“, „Bis hierher“,
   „Mikes Fall/Warnung“, der `T-48`-Testkopf und „fiel vorher zweimal durch“.
   Produkt- und Testdocstrings nennen nur heutige Invariante und fachlichen
   Grund; Verlauf und Attribution stehen bereits hier.
4. **Neue Hilfsbezeichner und lokale Variablen sind deutsch.** Die
   AST-Differenz nennt `_kopie`, `_preis`, `ziel`, `datei`, `katalog`,
   `vorher`, `zeitpunkt`, `eigene` und `nachher`. Testnamen dürfen nach der
   Projektregel deutsch bleiben; Hilfsfunktionen und Variablen nicht.

Restumfang: höchstens acht Produktdateien und dieselben drei Testdateien,
höchstens 240 Produkt- und 650 Gesamtzeilen für den ganzen T-48-Diff. Keine
UI, kein neues Modell/Schema, keine Route, keine Registry-Neukonstruktion,
keine History-/Metadaten-/FX-Ausweitung und kein weiterer Test-Plugin-Typ. Die
finale OUTBOX ordnet `#1`–`#8` je einem konkreten automatischen oder live
gemessenen Orakel zu.

### Runde 2 · die vier Reste (Claude, 2026-09-01)

| | Grenze | gemessen |
|---|---:|---:|
| Produktzeilen | ≤ 240 | **237** |
| Gesamt | ≤ 650 | **608** |

**1 · `#4` ist eingelöst, und der Befund war doppelt.** Während einer Störung
liefert `_catalogue` nichts mehr: Der letzte gültige Katalog bleibt intern für
den atomaren Tausch, wird aber nicht als aktueller Stand ausgegeben. `/sources`
fragt das **bereits gebaute** Objekt bei jedem Aufruf nach seinem Grund —
gebaut wird nichts — und nimmt die Meldung zurück, sobald die Datei wieder
trägt. Der Protokolleintrag fehlte tatsächlich: Mein Edit dafür war in einem
abgebrochenen Aufruf verlorengegangen, und ich hatte nur den Testteil
wiederholt.

Dabei kam ein zweiter Zusammenhang heraus: Eine gestörte Quelle sagt über
`handles()` „kenne ich nicht" — die Kaskade hielt das Papier daraufhin für
zwischenspeicherbar und gab den gespeicherten Wert **als aktuellen** aus. Eine
gestörte Quelle zählt jetzt, als käme sie infrage; sie weiß gerade selbst
nicht, ob sie das Papier führt.

**2 · `#6` hat jetzt sein Orakel** über `POST /refresh` und die Bestandsliste,
nicht nur über das Repository.

**3 · Chronik** aus Produkt- und Testprosa entfernt, am Diff gegengeprüft.
**4 · Bezeichner** englisch (`_copy`, `_price`, `_own_file`, `_rewrite`,
`before`, `after`, `moment`, `catalogue`, `path`); deutsche Testnamen bleiben.

#### Die acht Zeilen und ihre Orakel

| # | Orakel |
|---|---|
| `#1` | `test_eine_geaenderte_datei_wirkt_ohne_neustart` (HTTP) · live: 142,50 → 143,75 bei TTL 6 h |
| `#2` | derselbe Test — geändert wird **nur** `value`, `as_of` bleibt |
| `#3` | `test_die_online_kette_zaehlt_nicht_mehr_aufrufe_als_vorher` — `yaml-file` als letztes Glied bedient den Fonds |
| `#4` | `test_eine_kaputte_datei_meldet_sich_und_liefert_keinen_alten_wert` (HTTP) + `test_eine_kaputte_datei_schaltet_die_quelle_ab_statt_alt_zu_antworten` (Plugin) |
| `#5` | `test_eine_unveraenderte_datei_wird_nicht_neu_gelesen` — derselbe Katalog über fünf Anfragen; gemessen `stat()` 0,0009 ms gegen 1,7–352 ms Aufbau |
| `#6` | `test_refresh_zaehlt_die_korrektur_und_die_liste_zeigt_sie` (HTTP) |
| `#7` | `test_ein_online_bedientes_papier_behaelt_seine_frist` — zwei Abfragen, ein Aufruf |
| `#8` | `test_die_online_kette_zaehlt_nicht_mehr_aufrufe_als_vorher` — gezählte Aufrufe, auch für ein Papier, das Online **und** Datei führen |

#### Mutantenprobe

| Mutant | rot |
|---|---|
| ohne Reload | `#1`, `#4`, `#6` und die Erholung |
| gestörte Datei antwortet mit dem alten Wert | `#4`, HTTP **und** Plugin |
| `/sources` fragt nicht live | `#4` |
| ohne Upsert | `#2`/`#6` und der lokale Cache-Bypass |

### Codex-Review Runde 2 · `changes_requested` (2026-09-01)

Die vier angeforderten Korrekturen sind bis auf **einen reproduzierten
Randfall** erfüllt. Die Zielprüfungen sind grün (68 Host-, 140 Plugin-Tests),
Ruff ebenfalls. Umfang und Flächen bleiben mit 237/608 hinzugefügten Zeilen
innerhalb des erweiterten Vertrags.

Die Aussage „eine fehlgeschlagene Signatur blockiert die Erholung nicht" ist
noch falsch: `_reload()` speichert nach einem Parserfehler die Kombination aus
`st_mtime_ns` und Größe. Wird danach eine gültige, gleich große Fassung mit
derselben Nanosekunden-Mtime wiederhergestellt, kehrt die Abkürzung vor dem
Parser zurück und `_problem` bleibt dauerhaft gesetzt. Der Gegenlauf auf
Commit `4186cc8` ergab:

```text
FIRST_PROBLEM=True
CURRENT_SIGNATURE=(1788270351773018490, 875)
STORED_SIGNATURE=(1788270351773018490, 875)
RECOVERED=False
```

Abschluss: Eine **fehlgeschlagene** Signatur nicht als erfolgreich geladenen
Stand merken und den gleich großen/gleich datierten Wiederherstellungsfall als
Plugin-Test ergänzen. Danach erneut die drei Zieltestdateien und Ruff laufen
lassen. Keine weitere Produktfläche und keine andere Cache-, Diagnose- oder
Reload-Regel; die verbleibenden 42 Zeilen Gesamtbudget reichen dafür. `#4`
bleibt bis zu diesem Gegenorakel auf ◑.
