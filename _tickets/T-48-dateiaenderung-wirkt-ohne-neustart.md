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

Legende: ✅ live bestätigt · ➖ nicht geprüft.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | reines YAML-Profil, Preis in der Datei ändern | die Änderung ist **ohne Neustart** sichtbar | ➖ | |
| **2** | dasselbe, `as_of` unverändert | der korrigierte Wert kommt an — nicht nur bei neuem Zeitstempel | ➖ | |
| **3** | Online-Profil mit `yaml-file` als letztem Glied | dieselbe Zusage; die Datei ist dort dieselbe Quelle | ➖ | |
| **4** | Datei kaputt gemacht, während der Dienst läuft | der Dienst bleibt stehen und meldet den Grund; er fällt nicht auf einen halben Katalog zurück | ➖ | |
| **5** | Datei unverändert, viele Anfragen | die Antwortzeit bleibt brauchbar — gemessen, nicht geschätzt | ➖ | |
| **6** | `POST /refresh` mit verworfenem Schreibversuch | `refreshed` zählt ihn **nicht** als Erfolg | ➖ | |
| **7** | Online-Profil, TTL | die Cache-TTL gilt dort **unverändert** — kein Abruf mehr als vorher | ➖ | |
| **8** | Online-Profil, Provider-Aufrufe | gezählt vor und nach der Änderung: dieselbe Zahl | ➖ | |

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

_(offen — Scope-Checkpoint liegt bei Codex)_
