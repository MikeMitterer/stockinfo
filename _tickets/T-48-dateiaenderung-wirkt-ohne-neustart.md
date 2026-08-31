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
| `ON CONFLICT … DO UPDATE` | Ein Kurs mit gleichem Zeitpunkt und anderem Preis **ersetzt** den alten | Gilt für **alle** Quellen; eine korrigierte Online-Antwort überschreibt dann ebenfalls |
| Nur ehrlich zählen | `refreshed` zählt, was wirklich geschrieben wurde; ein verworfener Schreibversuch steht im Protokoll | Behebt Mikes Fall **nicht** |

Der erste Weg löst das Problem, der zweite behebt nur die Falschmeldung. Sie
schließen einander nicht aus.

**Schicht 3 (TTL).** Offen, ob eine Dateiquelle überhaupt eine TTL haben soll.
Sie schont bei entfernten Quellen ein Kontingent; bei einer lokalen Datei
schont sie nichts.

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
| **5** | Datei unverändert, viele Anfragen | sie wird nicht bei jeder Anfrage neu geparst | ➖ | |
| **6** | `POST /refresh` mit verworfenem Schreibversuch | `refreshed` zählt ihn **nicht** als Erfolg | ➖ | |

## Nicht-Ziele

- Kein Beobachter-Prozess, kein Datei-Watcher als Dienst.
- Keine Änderung am Plugin-Vertrag: Das Nachladen ist Sache der Quelle, nicht
  des Kerns.
- Keine neue Route und keine Anzeige der Katalog-Version im UI.

## Auflösung

_(offen — zuerst die drei Richtungsentscheidungen)_
