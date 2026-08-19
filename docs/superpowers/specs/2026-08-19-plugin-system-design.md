# StockInfo — Datenquellen als Python-Plugins

**Datum:** 2026-08-19
**Status:** Design zur Freigabe, überarbeitet nach Codex-Review
**Tickets:** T-17 bis T-23

## Ziel

Datenquellen — ISIN-Auflösung, Kurse, Tageshistorie, Devisen, ETF-Metadaten —
werden austauschbar, ohne die App zu ändern. Beigesteuerte Quellen sind
**Python-Plugins** gegen einen versionierten Vertrag.

## Motivation

Die App soll weltweit funktionieren, lässt sich hier aber nur für wenige Märkte
prüfen. Das ist keine Bequemlichkeitsfrage, sondern eine Erkenntnisgrenze: Die
Auflösung eines einzigen kanadischen Papiers hat am 2026-08-19 drei Anläufe
gebraucht, zwei davon mit falschem Ergebnis. Bei 33 Börsen in `EXCHANGES` ist
das prinzipiell nicht zu schaffen. Wer in Toronto sitzt, findet das Problem in
zehn Minuten.

Daraus folgt die Architektur, nicht umgekehrt: **Was hier nicht geprüft werden
kann, muss von dort lösbar sein, wo es auffällt.**

Der Präzedenzfall ist Home Assistant — tausende Geräte, ein Kernteam, das die
meisten nie besitzt, und ein Custom-Component-Verzeichnis, aus dem der Erfolg
kommt.

## Die Entscheidung: nur Python — kein zweites Format

Eine frühere Fassung dieses Designs sah **zwei** Wege vor: Beschreibungsdateien
(YAML) für REST-Quellen und Python für den Rest. Diese Entscheidung ist
zurückgenommen. Es gibt genau eine Sorte Plugin, und die ist Python.

### Warum der deklarative Weg gestrichen wurde

**Der Interpreter wäre selbst ein erhebliches Stück Software.** Die
Codex-Review vom 2026-08-19 hat aufgelistet, was ein tragfähiges Format
mindestens braucht: HTTP-Methode, Query/JSON-Body/Form-Body/Header,
Secret-Referenzen, URL-Kodierung der Platzhalter, Connect-/Read-/Gesamt-Timeout,
maximale Antwortgröße, Redirect-Regeln, erlaubte Content-Types, JSON-Pfad-Syntax
samt Verhalten bei mehrdeutigen Treffern, Typkonvertierung, statische
Wertetabellen, Statuscode-Mapping auf `NotFound`/`Unavailable`, Redaction beim
Protokollieren und eine eigene Schema-Version. Das ist zu spezifizieren, zu
implementieren, zu testen und zu pflegen — für einen Funktionsumfang, den Python
mitbringt.

**Der Machbarkeitsbeweis war unvollständig.** Das YAML-Beispiel der ersten
Fassung konnte OpenFIGI nicht abbilden: Der Dienst braucht `POST` mit einem
JSON-Array, das Schema kannte weder Methode noch Body. Ausgerechnet die eine
Quelle, die als „vollständig deklarativ machbar" gemessen worden war.

**Das Sicherheitsargument war zu stark formuliert.** Eine Beschreibungsdatei
führt keinen beliebigen Code aus — aber sie kann einen ihr übergebenen
`{config.api_key}` an eine frei gewählte URL senden, gegen interne Dienste
sprechen (SSRF), Weiterleitungen auf fremde Hosts folgen und Schlüssel in
Protokolle schreiben. Der Vorteil schrumpft von „kein Risiko" auf „kein
beliebiger Code" — real, aber deutlich kleiner als behauptet.

**Zwei Wege heißen doppelte Pflege.** Zwei Contract-Test-Suiten, zwei
Dokumentationen, zwei Fehlerbilder — und bei jeder Vertragsänderung beides
nachziehen.

**Die Einstiegshürde ist gesunken.** Ein Plugin ist rund 60 Zeilen (siehe
`plugin_api/examples/canada_file.py`), und der Contract-Test gibt die Zielvorgabe
maschinell vor. Mit KI-Unterstützung ist das kein Hindernis mehr für jemanden,
der seine API kennt.

### Was der Verzicht kostet

Ehrlich benannt, damit es keine stille Annahme bleibt:

- **Kein Nachladen zur Laufzeit.** Eine YAML-Datei ließe sich ohne Neustart neu
  einlesen, ein Python-Modul nicht sauber. Plugins werden beim Start geladen.
- **Fremder Code läuft mit den Rechten der App.** Das gilt jetzt für *alle*
  Plugins, nicht nur für die Sonderfälle. Siehe „Was bewusst nicht gebaut wird".
- **Ein Beiträger braucht eine Python-Umgebung**, nicht nur einen Texteditor.

### Was aus dem Ansatz bleibt

Das Wertvollste daran war nie das Dateiformat, sondern das Modell dahinter — und
das ist bereits in Python umgesetzt:

- **Zuständigkeit als Deklaration** statt als Code-Verzweigung (`handles()`)
- **Feld-Zuordnung mit Einheiten** (`FieldSpec`, `Reading`, `convert()`) — die
  Antwort auf `0.19` gegen `0.0003` gegen `19` für dieselbe Kostenquote
- **Plausibilitätsbereiche** gegen die stille Null

Damit entfällt auch die aufwendigste offene Frage der Review vollständig:
Formales Schema und Bedrohungsmodell für deklarative Quellen werden nicht mehr
gebraucht.

## Der Vertrag

Drei Entwurfsentscheidungen, alle bereits in `plugin_api/` umgesetzt:

**Anfragen sind Objekte.** `ResolveRequest` lässt sich um Felder erweitern,
ohne eine fremde Signatur zu brechen. Bei `resolve_isin(isin: str)` wäre jede
Erweiterung ein Bruch — und fremde Plugins kann man nicht nachziehen.

**Antworten sind vier Dinge, kein `None`.** `Resolved`, `NotResponsible`,
`NotFound`, `Unavailable`. Daraus folgt, ob die Kette weitersucht, ob 404 oder
502 richtig ist, und ob ein gespeicherter Stand überschrieben werden darf.

**Werte tragen Einheit und Herkunft.** Gemessen: dieselbe Kostenquote kommt bei
yfinance als `0.03` und `0.0003` an, bei justETF als `0.19`. `FieldSpec.plausible`
fängt zusätzlich die stille Null — eine Quelle meldete `0.0000` für einen Fonds,
der real rund 0,06 % kostet.

### Contract-Tests sind der Kern

Ein Autor erbt von `ResolverContract` oder `MetadataContract`, nennt zwei bis
drei Anfragen und bekommt den Vertrag maschinell geprüft. Gegenprobe mit
absichtlich fehlerhaften Plugins: gefangen werden `NotFound` statt
`NotResponsible`, Börsensuffix im Ticker, nicht deklarierte Felder, falsch
deklarierte Einheiten und durchgereichte Ausnahmen.

Das ersetzt Tests, die hier niemand schreiben könnte, durch Tests, die andere
für uns laufen lassen.

## Ladewege

| Weg | Wofür | Neustart nötig |
|---|---|---|
| Entry-Points (`pip install …`) | Beigesteuertes, versioniert, teilbar | ja |
| Verzeichnis `data/plugins/` | Ausprobieren, lokale Anpassungen | ja |

Beide Code-Wege landen in derselben Registry; `data/sources.yaml` bestimmt
Auswahl und Reihenfolge. Geladen wird beim Start — das genügt und entspricht
dem, was Home Assistant für Custom Components tut.

## Was bewusst nicht gebaut wird

**Kein Nachladen von Python-Code ohne Neustart.** Kostet Zustandsverwaltung und
Reload-Semantik für einen Gewinn, den man selten spürt.

**Keine Umschaltung über die Oberfläche.** Die Konfigurationsdatei genügt.

**Kein Sandboxing fremden Codes.** Ein Python-Plugin läuft mit den Rechten der
App. Wer selbst hostet, hat ohnehin ein Container-Image installiert, dem er
vertraut — dieselbe Vertrauensentscheidung eine Stufe kleiner. Was die App
schuldet: eine klare Ansage in der Dokumentation und **keine Automatik, die von
selbst etwas nachlädt**. Seit der deklarative Weg gestrichen ist, gilt das für
**jedes** Plugin — es gibt keinen risikoarmen Nebenweg mehr, auf den man
ausweichen könnte. Umso wichtiger sind die kuratierte Empfehlung und der
Hinweis, nur zu installieren, was man geprüft hat.

**Keine offene Feldmenge, zunächst.** Ein Plugin liefert eine Teilmenge der
bekannten Felder; unbekannte werden protokolliert und verworfen. Grund: Bei acht
Feldern ist die Wahrscheinlichkeit hoch, dass ein vermeintlich neues Feld ein
bekanntes unter anderem Namen ist — `fund_provider`, `fundFamily` und `family`
sind dreimal dasselbe. Die generische Tabelle lohnt erst, wenn wirklich neue
Bedeutungen auftreten.

## Die Kopplung, die bleibt

Yahoo ist kein Anbieter unter mehreren, sondern das Rückgrat: vier direkte
Importe, vier Instanziierungen in `container.py`, drei Rollen in einer Klasse
(von denen nur eine im Protokoll steht) — und `symbol` ist überall im System
das Yahoo-Format. T-21 löst den Identifikator davon; die Kursquelle selbst
auszutauschen bleibt darüber hinaus ein eigenes Vorhaben.

**Der Fallback für OpenFIGI ist yfinance.** Fällt yfinance aus, fallen
gleichzeitig weg: Kurse, Tageshistorie, Devisen, der Resolver-Fallback und die
ETF-Quelle für außereuropäische Papiere. Die Redundanz ist scheinbar.

## Reihenfolge

| Ticket | Warum an dieser Stelle |
|---|---|
| T-17 | verfälscht heute Daten — unabhängig vom Vorhaben |
| T-18 | behebt den Kanada-Fall, der das Vorhaben ausgelöst hat |
| T-19 | ohne verlustfreies Neu-Auflösen ist ein Quellenwechsel nicht ausprobierbar |
| T-20 | ohne die vier Antwortarten kann eine Kette nicht weiterschalten |
| T-21 | ohne MIC + Ticker müsste jedes Plugin Yahoo-Symbole verstehen |
| T-22 | Ketten und Schlüssel gehören in Konfiguration, nicht in die Composition-Root |
| T-23 | Schlussstein — hängt an T-20, T-21, T-22 |

Ein Ticket für deklarative Quellen entfällt — siehe „Die Entscheidung: nur
Python".

## Offene Entscheidungen

Aus der Codex-Review vom 2026-08-19 (`_tickets/codex-verification-2026-08-19-plugin-system-design.md`).
Jede Zeile braucht eine Entscheidung, bevor T-21 bis T-23 umgesetzt werden.
Die Empfehlung ist meine; die Entscheidung nicht.

| # | Frage | Empfehlung |
|---|---|---|
| 1 | Kanonische Identität und Anbieter-Aliase | `(ticker, mic)` ist Identität; `symbol` wird `NULL`-fähig, verliert den Unique-Index und ist abgeleiteter Yahoo-Alias |
| 2 | Historie beim Listingwechsel | Kursreihen invalidieren, manuelle Kennzahlen behalten. Offen: löschen oder archivieren — siehe T-19 |
| 3 | Verträge für Quote, Daily, FX | vor T-22 ausformulieren; solange bleibt `0.x` |
| 4 | Eigener `MetadataRequest` | ja — `ResolveRequest` kennt nur `preferred_mic`, nicht das aufgelöste Listing |
| 5 | Herkunft und Stand je Metadatenfeld | zunächst **nicht** je Feld: feste Feldmenge, ein `source`, wie heute. Erst wenn zwei Quellen sich wirklich überlappen |
| 6 | Aggregationsregeln der Ergebnisarten | `Unavailable` von irgendeiner zuständigen Quelle schlägt `NotFound` → 502. Sonst 404 |
| 7 | Timeout-Modell für fremden Code | **kooperativ**, keine harte Garantie. Siehe unten |
| 8 | Registry-Regeln (Entry-Point-Gruppe, Namen, Lifecycle, Versionsvergleich, Thread-Sicherheit) | mit T-23 festlegen, nicht vorher raten |
| 9 | Installationsmodell für Docker/Unraid | abgeleitetes Image mit zusätzlichen `pip install`-Schritten; Verzeichnis-Plugins nur für Bibliotheken, die schon im Image sind |
| 10 | Plugin-Tests im regulären Lauf | **erledigt** — `make test-plugin-api`, Teil von `make test` |

### Zu 7 — der harte Timeout ist nicht umsetzbar

T-23 verlangte, ein hängendes Plugin nach einer Zeitgrenze zu stoppen. Für
synchron laufenden Python-Code im selben Prozess geht das nicht: Ein
Future-Timeout lässt den **Aufrufer** zurückkehren, der Thread hängt weiter.
Wiederholte Hänger erschöpfen den Threadpool; native Bibliotheken können den
Prozess ganz blockieren.

Zwei ehrliche Möglichkeiten:

- **Eigene Worker-Prozesse** — ein hängender Aufruf lässt sich beenden. Preis:
  IPC, Serialisierung, Prozess-Lebenszyklus.
- **Kooperative Zeitgrenzen** — Plugins setzen ihre HTTP-Timeouts selbst, der
  Vertrag verlangt es, der Contract-Test kann es nicht erzwingen. Ein
  Schutzschalter verhindert *weitere* Aufrufe, nicht den laufenden.

**Empfehlung: kooperativ**, und die fehlende Garantie ausdrücklich
dokumentieren statt sie zu behaupten. Worker-Prozesse sind für eine
selbstgehostete App mit wenigen Quellen unverhältnismäßig.

### Zu 5 — der Widerspruch in der ersten Fassung

Das Design sagte „unbekannte Felder werden verworfen", während `FieldSpec`
Beschriftungen mitbringt, die nur für **neue** Felder einen Zweck haben. Beides
zusammen geht nicht.

Aufgelöst: Die Feldmenge bleibt vorerst geschlossen. `label_en`/`label_de`
bleiben im Vertrag, weil sie nichts kosten und den Weg offenhalten — sie werden
aber erst wirksam, wenn die generische Persistenz existiert. Bis dahin gewinnt
der Katalog der App.

### Zu 6 — was `is_configured()` nicht kann

Sie liefert `bool` und damit keinen Grund, obwohl `/sources` einen anzeigen
soll. Entweder ein strukturiertes Ergebnis oder eine zweite Diagnosemethode —
mit T-19 zu entscheiden.

Und: **OpenFIGI ohne Schlüssel ist nicht unkonfiguriert.** Der Dienst
funktioniert anonym mit niedrigerem Limit (`app/providers/openfigi_provider.py:24-50`).
Das Prüfkriterium in T-22 war falsch und ist korrigiert.

### Zu 2 — Reihenfolge gegen Kosten

Erste Fassung sagte beides: `sources.yaml` bestimmt die Reihenfolge, und `cost`
steuert sie auch. Genau eine Regel gilt:

1. Die ausdrückliche Reihenfolge in `sources.yaml` gewinnt immer.
2. `cost` ist Information — für Anzeige und Warnung, nicht für Sortierung.
3. Alphabetisch nur für Quellen, die nicht ausdrücklich konfiguriert sind.

### Zu 13 der Review — ISIN-Land ist eine Heuristik

Das ISIN-Präfix nennt die ausgebende Stelle, nicht den gewünschten Handelsplatz;
ein Land kann mehrere Börsen haben, und ein irischer Fonds wird europaweit
gehandelt. Die Kaskade in T-18 bleibt sinnvoll, gilt aber ausdrücklich als
Rückfall-Heuristik — mit sichtbarer Abweichung von der Präferenz und sichtbarer
Währung.

## Belege


Alle Messungen vom 2026-08-19, nachstellbar über die Tickets. Zwei
Einschränkungen in eigener Sache: Der Kanada-Befund stützt sich auf zwei ISINs,
nicht auf eine systematische Stichprobe. Und die Anbieter-Konventionen stammen
aus Übersichts- und Doku-Seiten, nicht aus der Praxis — vor einer Entscheidung
für einen konkreten Dienst gehört dessen Dokumentation gelesen, vor allem zum
Umgang mit Mehrfachnotierungen.
