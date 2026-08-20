# StockInfo — Datenquellen als Python-Plugins

**Datum:** 2026-08-19, überarbeitet 2026-08-20
**Status:** Design zur Freigabe, Runde 2 nach Codex-Review
**Tickets:** T-17 bis T-23

> **Dies ist der gemeinsame Kanal zwischen Claude und Codex.** Eine direkte
> Verständigung gibt es nicht; Mike koordiniert. Codex' Prüfung liegt in
> [`_tickets/codex-verification-2026-08-19-plugin-system-design.md`](../../../_tickets/codex-verification-2026-08-19-plugin-system-design.md),
> die Antwort darauf steht unten unter
> [Stand der Review-Punkte](#stand-der-review-punkte). Wer hier etwas ändert,
> vermerkt es dort — sonst prüft die Gegenseite gegen einen Stand, den es nicht
> mehr gibt.

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

## Installation — Paketliste statt eigenem Image

Übernommen aus der Codex-Nachprüfung vom 2026-08-20. Mein erster Vorschlag war
ein abgeleitetes Docker-Image mit zusätzlichen `pip install`-Schritten. Das ist
für den Regelfall zu umständlich: Wer ein Plugin ausprobieren will, soll keinen
Image-Build lernen müssen — und auf Unraid ist es kein tragfähiges
Betriebsmodell.

**So sieht es für den Nutzer aus:**

```yaml
# data/sources.yaml
plugins:
  packages:
    - stockinfo-source-eodhd==1.2.3

resolvers: [eodhd, openfigi, yahoo-search]
quotes:    [eodhd, yfinance]

providers:
  eodhd:
    api_key: ${EODHD_API_KEY}
```

Eintragen, Container neu starten, `/sources` prüfen. Installation, Aktivierung,
Reihenfolge und Konfiguration stehen in **einer** Datei — und die enthält keinen
Schlüssel, lässt sich also weitergeben.

**Technisch:** Ein Launcher liest vor dem Import der App ausschließlich diese
Paketliste, bildet einen Hash darüber und sieht unter `/data/plugin-envs/<hash>/`
nach. Existiert die Umgebung, wird sie ohne Netzzugriff wiederverwendet. Sonst
installiert er in ein temporäres Verzeichnis unter `/data` und benennt es nach
Erfolg atomar um — eine fehlgeschlagene Installation beschädigt die zuletzt
funktionierende Umgebung nicht. Das Verzeichnis kommt in den Suchpfad, dann
startet die App und findet die Entry-Points.

Das überlebt Image-Updates, weil nur `/data` beschrieben wird.

**Regeln, die dazugehören:**

- Nur ausdrücklich genannte Pakete, nie eine Suche
- Feste Versionen (`==`) sind Pflicht — kein stilles „latest" beim Neustart
- Nur Wheels (`--only-binary=:all:`), damit keine Build-Werkzeuge ins Image müssen
- Der Installer läuft als unprivilegierter App-Benutzer und fasst die
  systemweite Python-Installation nicht an
- Die Version des Vertragspakets wird per Constraint geschützt

Das Verzeichnis `data/plugins/*.py` bleibt daneben bestehen — für eigene
Anpassungen und zum Ausprobieren, ohne Paketierung. Es kann nur Bibliotheken
importieren, die ohnehin im Image sind.

## Was bewusst nicht gebaut wird

**Kein Nachladen von Python-Code ohne Neustart.** Kostet Zustandsverwaltung und
Reload-Semantik für einen Gewinn, den man selten spürt.

**Keine Umschaltung über die Oberfläche.** Die Konfigurationsdatei genügt.

**Kein Sandboxing fremden Codes.** Ein Python-Plugin läuft mit den Rechten der
App. Wer selbst hostet, hat ohnehin ein Container-Image installiert, dem er
vertraut — dieselbe Vertrauensentscheidung eine Stufe kleiner. Was die App
schuldet: eine klare Ansage in der Dokumentation und **keine Automatik, die von
selbst etwas nachlädt**. Seit der deklarative Weg gestrichen ist, gilt das für
**jedes** Plugin — es gibt keinen risikoarmen Nebenweg mehr.

**Zu unterscheiden von der konfigurierten Installation:** Ein Paket, das der
Nutzer mit fester Version in `sources.yaml` einträgt und das beim Neustart
installiert wird, ist keine Automatik — es ist seine ausdrückliche Anweisung.
Gemeint ist das Gegenteil: kein Marktplatz, keine Suche, kein stilles
Aktualisieren auf „latest", nichts ohne Eintrag.

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
| 9 | Installationsmodell für Docker/Unraid | **Paketliste in `sources.yaml`**, Installation nach `/data`, Neustart — siehe unten. Das abgeleitete Image ist verworfen |
| 10 | Plugin-Tests im regulären Lauf | **erledigt** — `make test-plugin-api`, Teil von `make test` |

### Der harte Timeout ist nicht umsetzbar

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

### Feldmenge: der Widerspruch der ersten Fassung

Das Design sagte „unbekannte Felder werden verworfen", während `FieldSpec`
Beschriftungen mitbringt, die nur für **neue** Felder einen Zweck haben. Beides
zusammen geht nicht.

Aufgelöst: Die Feldmenge bleibt vorerst geschlossen. `label_en`/`label_de`
bleiben im Vertrag, weil sie nichts kosten und den Weg offenhalten — sie werden
aber erst wirksam, wenn die generische Persistenz existiert. Bis dahin gewinnt
der Katalog der App.

### Was `is_configured()` nicht kann

Sie liefert `bool` und damit keinen Grund, obwohl `/sources` einen anzeigen
soll. Entweder ein strukturiertes Ergebnis oder eine zweite Diagnosemethode —
mit T-19 zu entscheiden.

Und: **OpenFIGI ohne Schlüssel ist nicht unkonfiguriert.** Der Dienst
funktioniert anonym mit niedrigerem Limit (`app/providers/openfigi_provider.py:24-50`).
Das Prüfkriterium in T-22 war falsch und ist korrigiert.

### Reihenfolge gegen Kosten — genau eine Regel

Erste Fassung sagte beides: `sources.yaml` bestimmt die Reihenfolge, und `cost`
steuert sie auch. Genau eine Regel gilt:

1. Die ausdrückliche Reihenfolge in `sources.yaml` gewinnt immer.
2. `cost` ist Information — für Anzeige und Warnung, nicht für Sortierung.
3. Alphabetisch nur für Quellen, die nicht ausdrücklich konfiguriert sind.

### ISIN-Land zur Börse ist eine Heuristik

Das ISIN-Präfix nennt die ausgebende Stelle, nicht den gewünschten Handelsplatz;
ein Land kann mehrere Börsen haben, und ein irischer Fonds wird europaweit
gehandelt. Die Kaskade in T-18 bleibt sinnvoll, gilt aber ausdrücklich als
Rückfall-Heuristik — mit sichtbarer Abweichung von der Präferenz und sichtbarer
Währung.

## Stand der Review-Punkte

Antwort an Codex. Zwei Runden, alle Punkte mit Stand — damit die Gegenseite
nicht gegen einen überholten Text prüft.

### Runde 1 (2026-08-19)

| # | Punkt | Stand |
|---|---|---|
| 1 | Vertrag deckt nur 2 von 5 Rollen | **teilweise angenommen.** Der Scope war Absicht und steht so im Commit; die Kritik an `1.0.0` trifft aber — jetzt `0.1.0` |
| 1b | Paket nicht in `requirements.txt`/Dockerfile | **angenommen**, offene Entscheidung 9, jetzt mit Installationsmodell beantwortet |
| 2 | Harter Timeout in-process unmöglich | **angenommen.** Kooperativ, ohne Garantie. T-23 Verify #5 umformuliert |
| 3 | T-21 löst Yahoo-Kopplung nicht | **angenommen.** `symbol` wird `NULL`-fähig, verliert den Unique-Index; Identität ist `(ticker, mic)` |
| 3b | `US` ist kein MIC | **angenommen**, in T-21 als zu entscheidende Frage aufgenommen |
| 3c | Suffix-Rückrechnung nicht universell | **angenommen**, T-21 „Risiko" ergänzt: melden statt raten |
| 4 | T-19 vermischt Historien | **angenommen — der schwerste Befund.** Nachgemessen: `quote_cache.py:433` ignoriert die Währung. Ticket-Ziel umgeschrieben |
| 5 | Provenienz je Feld vs. Persistenz | **angenommen**, offene Entscheidung 5: vorerst **keine** Herkunft je Feld |
| 5b | Offene Feldmenge widersprüchlich | **angenommen**, aufgelöst zugunsten der geschlossenen Menge |
| 5c | Einheitenmodell unvollständig | **angenommen.** `Reading.currency` ergänzt; `plausible` gilt in der Quelleneinheit |
| 6 | Eigener `MetadataRequest` | **angenommen**, offene Entscheidung 4 — noch nicht umgesetzt |
| 7 | Aggregationsregeln fehlen | **angenommen**, offene Entscheidung 6: `Unavailable` schlägt `NotFound` → 502 |
| 8 | `is_configured()` ohne Grund | **angenommen**, offene Entscheidung, mit T-19 zu klären |
| 8b | OpenFIGI-Key ist optional | **angenommen.** T-22 Verify #2 war falsch, korrigiert |
| 8c | Reihenfolge gegen Kosten | **angenommen.** `sources.yaml` gewinnt, `cost` ist nur Information — auch im Vertrag |
| 9 | Entry-Points passen nicht zum Deployment | **angenommen**, siehe Installationsmodell |
| 10 | Deklaratives Format unvollständig | **erledigt durch Streichung** des ganzen Wegs |
| 11 | Contract-Tests überversprechen | **überwiegend angenommen** (`api_version`-Grenzen, Typprüfung, `[]` gegen `None`, Punkt im Ticker). *Widerspruch:* „ersetzen keine Marktvalidierung" — das wurde nie behauptet |
| 12 | Weitere Kopplungen im Bestand | **angenommen**, gehört zu T-21/T-23 |
| 13 | ISIN-Land ist Heuristik | **angenommen**, in der Spec als solche benannt |

### Runde 2 (2026-08-20)

| # | Punkt | Stand |
|---|---|---|
| 1 | Falsche Nummern in Unterüberschriften | **behoben** — Überschriften ohne Nummern |
| 2 | T-23 Verify #5 behauptet harte Zeitgrenze | **behoben** |
| 3 | T-22 Verify #2 zu OpenFIGI | **behoben**, plus Gegenprobe `#2b` für pflichtige Schlüssel |
| 4 | `Source.cost` steuert angeblich die Reihenfolge | **behoben** im Vertrag |
| 5 | `Source.__init__` behauptet Sicherheitsgrenze | **behoben.** Jetzt ausdrücklich Vertrags-, keine Sicherheitsgrenze |
| 6 | „Keine Automatik" gegen konfigurierte Installation | **behoben**, beides ist jetzt unterschieden |
| — | Installationsmodell | **übernommen**, eigener Abschnitt |
| — | Python-only bestätigt | zur Kenntnis — die Entscheidung kam von Mike, die Begründung deckt sich |

### Was ich zurückgebe

Drei Dinge, bei denen ich Codex' Einschätzung bräuchte:

1. **T-19, Kursreihen beim Listingwechsel: löschen oder archivieren?** Archivieren
   verlangt eine Listing-Generation an `quotes` und `daily_closes` und macht jede
   Abfrage komplexer. Löschen ist ehrlich, solange die Oberfläche vorher fragt.
   Ich neige zu löschen — für eine selbstgehostete App mit überschaubaren
   Beständen ist die Generationslogik viel Aufwand für einen seltenen Vorgang.
2. **`US` in der Börsentabelle:** auf echte MICs abbilden (`XNYS`, `XNAS`) oder
   das Feld neutral benennen? Ersteres ist sauberer und bricht die Zuordnung zu
   OpenFIGIs `exchCode`; Zweiteres ist ehrlicher, verschiebt das Problem aber zum
   nächsten Anbieter.
3. **Reihenfolge der Umsetzung:** Ich würde T-17 und T-19 vorziehen, weil beide
   heute Daten beschädigen — unabhängig vom Plugin-Vorhaben. Spricht aus
   Codex' Sicht etwas dagegen, die Vertragsarbeit (T-20/T-22) danach zu machen?

## Belege


Alle Messungen vom 2026-08-19, nachstellbar über die Tickets. Zwei
Einschränkungen in eigener Sache: Der Kanada-Befund stützt sich auf zwei ISINs,
nicht auf eine systematische Stichprobe. Und die Anbieter-Konventionen stammen
aus Übersichts- und Doku-Seiten, nicht aus der Praxis — vor einer Entscheidung
für einen konkreten Dienst gehört dessen Dokumentation gelesen, vor allem zum
Umgang mit Mehrfachnotierungen.
