# StockInfo — Datenquellen als Python-Plugins

**Datum:** 2026-08-19, überarbeitet 2026-08-20
**Status:** Design zur Freigabe, Runde 7 nach Codex-Review
**Tickets:** T-17 bis T-27b

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
`NotResponsible`, nicht deklarierte Felder, falsch deklarierte Einheiten,
`None` statt `[]` bei Unzuständigkeit und durchgereichte Ausnahmen.

**Nicht** gefangen wird ein Börsensuffix im Ticker: Ob `BRK.A` ein Suffix trägt
oder einen Punkt im Namen führt, lässt sich nur gegen die Börsentabelle
entscheiden — und die kennt der Vertrag bewusst nicht. Diese Prüfung gehört auf
die App-Seite.

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

## Quellenprofile — zwei Vorgänge, die man nicht verwechseln darf

*(Von Mike entschieden, 2026-08-20; hier aus Codex' Wiedergabe übernommen und
noch nicht direkt bestätigt.)*

Ein **Quellenprofil** ist die Gesamtheit der aktiven Quellen einer Instanz.
Zwei Vorgänge sehen ähnlich aus und sind es nicht:

| Vorgang | Was passiert | Datenbank |
|---|---|---|
| **Quelle ergänzen oder aktualisieren** (innerhalb desselben Profils) | Kette ändert sich, bestehende Instrumente bleiben unberührt | bleibt |
| **Profil A durch B ersetzen** | A wird konsistent und fortlaufend nummeriert gesichert, B startet frisch | **neue Datenbank** |

Erst diese Trennung bringt zwei Invarianten zusammen, die sich sonst
widersprechen: „Eine Installation verändert nichts von selbst" und „B ersetzt A
mit frischer Datenbank".

Was dazugehört und noch nicht spezifiziert ist:

- eine Profil-Kennung, aus der sich Kompatibilität ableiten lässt
- fortlaufende Nummerierung der gesicherten Datenbanken samt Manifest
  (welches Profil, welcher Stand, wann)
- ein Weg zurück: Wiederherstellung ordnet Sicherung und Profil einander zu
- Konsumenten müssen den Wechsel bemerken können — ein Cache über einen
  Profilwechsel hinweg zeigt sonst Werte aus einer Datenbank, die es nicht mehr
  gibt

**Das ist nicht T-19.** Dort geht es um ein einzelnes Papier, hier um den
Wechsel des gesamten Betriebs. Beides zu vermischen wäre der Fehler; der
Profilwechsel braucht ein eigenes Ticket.

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

**Geschlossen ist nur der Core, nicht die Details.** *(Von Mike entschieden,
2026-08-20 — ersetzt die frühere Festlegung „keine offene Feldmenge".)*

Der REST-Core ist ein fester Mindestvertrag. **Zusätzliche Detailfelder sind
offen und additiv:**

1. Korrekt deklarierte Details werden generisch normalisiert und gespeichert.
2. Die API liefert sie in einem stabilen `details`-Container aus.
3. Dashboard und fähige Konsumenten stellen die Hülle generisch dar; ältere
   ignorieren unbekannte Einträge.
4. **Die Herkunft bleibt je Detail erhalten** — ein einzelnes `source` kann keine
   Kette abbilden, in der TER von Quelle X und Fondsvolumen von Quelle Y kommt.
5. Manuelle Werte füllen weiterhin nur Lücken der Quelle.

Der Grund gegen die geschlossene Menge ist ein Widerspruch im eigenen Haus: Der
Plugin-Vertrag verspricht bereits Erweiterbarkeit — `MetadataSource` hat eine
variable Feldmenge, `FieldSpec` trägt Typ, Einheit und Beschriftung, `Reading`
die Herkunft je Wert. Würde die App unbekannte Felder verwerfen, täuschte der
öffentliche Vertrag eine Erweiterbarkeit vor, die eine Schicht später endet.

Die generische Persistenz und Darstellung darf ein eigenes Umsetzungsticket
sein; die Architekturentscheidung steht.

## Der REST-Vertrag ist öffentlich

**Zwei Dinge sind hier auseinanderzuhalten** — die erste Fassung dieses
Abschnitts hat sie vermischt.

**StockInfo ist verteilt:** GitHub public, `mangolila/stockinfo` auf Docker Hub,
Unraid-Template. Wer die REST-API direkt anspricht statt nur das mitgelieferte
Dashboard zu nutzen, bekommt jeden Bruch ab — und man erfährt es nicht.
**Das** ist der Grund, warum der REST-Rand ein Vertrag ist.

**StockPortfolio ist es nicht.** Es ist Mikes Testkonsument, nicht öffentlich.
Es taugt als *Beispiel* dafür, was an der API hängt, aber **nicht** als
Begründung für Kompatibilitätsschichten: Beide Repos gehören demselben Autor und
lassen sich in einem Zug ändern.

Was an `symbol` hängt, zeigt der Testkonsument stellvertretend — nachgeprüft im
Nachbar-Repo:

```text
src/api/types.ts:17        symbol: string          // nicht nullable
src/types/portfolio.ts:29  symbol: string          // Pflichtfeld einer Position
src/api/mappers.ts:56      return entry.isin ?? entry.symbol   // Cache-Schlüssel
```

Die dritte Stelle ist die lehrreiche: Sie bräche **still** — der Cache-Schlüssel
wäre `undefined`, ohne Fehlermeldung. Wer immer die API direkt nutzt, hat
vermutlich ähnliche Annahmen, und die sieht man von hier aus nicht.

**Die offene Entscheidung 1 in ihrer ersten Fassung bleibt damit falsch** —
`symbol` einfach `NULL`-fähig zu machen ist der teuerste Weg: unsichtbarer
Bruch bei unbekannten Nutzern, für einen Gewinn, den der additive Weg auch
liefert.

### Was daraus folgt

Die Plugin-Freiheit endet am REST-Rand. Ein Plugin darf eigene Feldnamen, URLs
und Antwortformate haben — was die API nach außen zusagt, bleibt davon
unberührt:

- stabile Identität: ISIN soweit vorhanden, dazu kanonischer Ticker und MIC
- stabiler Anzeigename und normalisierte Gattung
- Preis mit **verpflichtender** Notierungswährung
- Kurszeitpunkt, Abrufzeitpunkt, Cache- und Stale-Zustand
- Tagespunkte mit Datum, Schlusskurs und Währung
- festgelegte Bedeutung des Schlusskurses (bereinigt gegen unbereinigt)

Plugin-eigene Objekte überschreiten diese Grenze nie: Der Kern normalisiert,
dann serialisiert Pydantic das öffentliche Modell. Ein unvollständiger
Pflichtkern ist ein `Unavailable`-Fehler — **keine Antwort mit geratenen
Ersatzwerten**.

### Der Weg für T-21

**Additiv:** `ticker` und `mic` kommen dazu, `symbol` bleibt garantiert und
wird weiter nach derselben Regel erzeugt. Kein Bruch, keine API-Version, kein
Migrationsfenster.

Das ist hier keine Zugeständnis-Lösung, sondern die billigste: Weil das
Symbolformat der App gehört (siehe nächster Abschnitt), kostet das Beibehalten
praktisch nichts — es ist derselbe String, nur nicht mehr der Identifikator.

`listing_id` kommt **additiv** dazu und braucht deshalb keine neue
Hauptversion des Vertrags — eine breaking Version wäre erst nötig, wenn `symbol`
seine zugesagte Bedeutung verlöre. Das ist nicht der Fall.

### Nicht zu verwechseln: zwei Migrationen

| | Was | Wen es betrifft |
|---|---|---|
| **Schema** | `symbol` in `ticker` + `mic` zerlegen, Spalten ergänzen | **jede laufende Instanz** — auch die von Docker-Hub- und Unraid-Nutzern |
| **Konsument** | Aufrufer an geänderte Felder anpassen | beim additiven Weg: **niemanden** |

Nur die erste ist echte Arbeit, und der Mechanismus dafür existiert
(`app/db.py:301`).

## Adressierung: `listing_id` für Maschinen, `symbol` für Menschen

*(Entschieden 2026-08-20. Codex und ich kommen unabhängig zum selben Ergebnis.)*

Die kanonische Identität ist `(ticker, mic)`. Daraus folgt aber **nicht**, dass
man den Eindeutigkeits-Index auf `symbol` einfach entfernen darf — genau das
stand in einer Zwischenfassung von T-21 und wäre ein stiller Bruch gewesen.

**Warum:** Es gibt acht symbolbasierte Endpunkte, darunter
`DELETE /instruments/by-symbol/{symbol}` und `PUT …/isin`. Der Lookup dahinter
lautet:

```sql
SELECT * FROM instruments WHERE symbol = ? ORDER BY id LIMIT 1
```

Das ist nicht undefiniert, sondern **definiert falsch**: Bei zwei gleichnamigen
Zeilen trifft es die ältere. Ein Löschvorgang landet dann am falschen
Instrument, ohne Fehlermeldung.

**Wo es kollidieren kann, ist präzise benennbar — für den heutigen Bestand.**
Weil `symbol = ticker + suffix` gilt und jedes Suffix genau einem MIC gehört, ist
das Symbol für alle Börsen **mit** Suffix eindeutig. Kollisionen entstehen dort,
wo mehrere MICs dasselbe leere Suffix teilen — derzeit also bei den US-Börsen,
sobald der Sammelcode `US` in `XNYS` und `XNAS` zerfällt (durch T-21).

„Derzeit" ist wörtlich zu nehmen: Regionale Plugins können weitere MICs und
Symbolkonventionen mitbringen. Die Laufzeitprüfung und die `409`-Regel gelten
deshalb **allgemein** — nicht als US-Sonderfall.

**Die Lösung:**

| | Wofür | Eigenschaft |
|---|---|---|
| `listing_id` | Maschinen — alle neuen Endpunkte | eindeutig, anbieterunabhängig |
| `symbol` | Menschen — Anzeige, Profil-Links, Altbestand | stabil, **nicht** garantiert eindeutig |

Die bestehenden Symbol-Endpunkte bleiben für eindeutige Fälle und antworten bei
Mehrdeutigkeit mit **`409 Conflict`** samt Kandidatenliste — statt still das
Falsche zu treffen.

Die Alternative wäre gewesen, die Symbol-Konvention selbst injektiv zu machen
(MIC-Disambiguierung im String). Das wäre billiger als es klingt, weil nur
US-Listings betroffen sind — verbiegt aber eine sonst saubere Konvention und
vermischt wieder Darstellung mit Identität.

Festgeschrieben wird das in **T-24**, das damit T-21 blockiert.

## Das Symbolformat ist eine Vereinbarung, keine Abhängigkeit

Eine Präzisierung, die eine frühere Fassung dieses Textes falsch hatte. Dort
stand, `symbol` sei eine Kopplung an yfinance. Nachgemessen gibt es zwei Wege,
auf denen ein Symbol entsteht, und nur einer davon ist eine Bindung:

| Weg | Code | Was es ist |
|---|---|---|
| 1 | `resolver.py:130` — `f"{ticker}{exch.suffix}"` | **Vereinbarung.** Die App bildet das Symbol selbst, aus ihrer eigenen `EXCHANGES`-Tabelle |
| 2 | `resolver.py:170` — `symbol = top["symbol"]` | **Abhängigkeit.** Der Yahoo-Fallback übernimmt Yahoos String |

Weg 1 ist eine Konvention im Besitz der App, die zufällig Yahoo-kompatibel ist.
`yf.Ticker(symbol)` im Provider ist nur Konsument — er verwendet das Symbol,
erzeugt es nicht.

**Daraus folgt Erfreuliches:** T-21 muss nichts entkoppeln, nur zerlegbar
machen. Und `symbol` am REST-Rand zu behalten (siehe unten) kostet nichts — es
ist kein Anbieter-Alias, sondern StockInfos eigener Listing-Bezeichner, den
jede Quelle nach derselben Regel erzeugt.

**Und ein konkretes Migrationsrisiko:** Weg 2 liefert Symbole, die der eigenen
Konvention *nicht* folgen müssen — `BRK-B` mit Bindestrich, oder was Yahoos
Suche sonst zurückgibt. Sie landen ungeprüft in der Datenbank und sind später
nicht sicher in `ticker` + `mic` zu zerlegen. Das ist die benennbare Ursache
hinter dem abstrakten Einwand „Suffix-Rückrechnung ist nicht universell
verlustfrei": kein theoretisches Risiko, sondern ein Codepfad. Die Migration
muss solche Symbole melden, und Weg 2 sollte das Ergebnis künftig gegen die
eigene Tabelle prüfen, statt es zu übernehmen.

## Die Kopplung, die bleibt

**Als Diagnose gemeint, nicht als Festlegung.** Yahoo *soll* keine Sonderrolle
behalten — der Abschnitt begründet, warum es die Ticketserie überhaupt braucht.

Heute ist Yahoo kein Anbieter unter mehreren, sondern das Rückgrat. Gemessen am
2026-08-20:

| | Befund |
|---|---|
| 1 | vier direkte `import yfinance`, davon zwei außerhalb der eigenen Provider (`resolver.py`, `analyzer.py`) |
| 2 | vier Instanziierungen von `YFinanceProvider()` in `container.py` |
| 3 | drei Rollen in einer Klasse — im Protokoll `QuoteProvider` steht nur `fetch_quote` |
| 4 | `QUOTE_TYPE_MAP` mit Yahoos Gattungsnamen steht im neutralen `base.py` |
| 5 | `models.py:260` macht yfinance-Interna zum API-Vertrag: `fast_info \| get_info \| isin \| history` |

Das Symbolformat gehört **nicht** in diese Liste — siehe den Abschnitt davor.

Nach T-20 bis T-22 ist Yahoo einer von vielen: dieselbe Antwortsemantik,
dieselbe Verdrahtung, dieselbe Konfiguration. Was darüber hinaus bliebe, wäre
die Frage, ob eine zweite Kursquelle die gleiche Datenqualität liefert — und die
beantwortet keine Architektur.

**Der Fallback für OpenFIGI ist yfinance.** Fällt yfinance aus, fallen
gleichzeitig weg: Kurse, Tageshistorie, Devisen, der Resolver-Fallback und die
ETF-Quelle für außereuropäische Papiere. Die Redundanz ist scheinbar.

## Reihenfolge

Nach Codex' Einwand vom 2026-08-20 revidiert: Maßstab ist der **Erfolgsweg** —
dass jemand in Toronto tatsächlich ein Plugin einsetzen kann —, nicht die
Vollständigkeit der Vorarbeiten.

| Ticket | Warum an dieser Stelle |
|---|---|
| T-17 | verfälscht heute Daten — unabhängig vom Vorhaben, deshalb zuerst |
| T-24 | erst wissen, was die API zusagt und wie eindeutig adressiert wird |
| T-18 | behebt den Kanada-Fall, der das Vorhaben ausgelöst hat |
| T-20 | ohne die vier Antwortarten kann eine Kette nicht weiterschalten |
| T-21 | Identität stabilisieren — **additiv**, ohne den REST-Vertrag zu brechen |
| T-22 | Ketten und Schlüssel gehören in Konfiguration, nicht in die Composition-Root |
| T-23 | Schlussstein — hängt an T-20, T-21, T-22 |
| T-19 | **nachrangig** — beschädigt nichts von selbst, siehe unten |
| T-26 | offene Details durchreichen — vor dem ersten Plugin mit neuen Feldern |
| T-27a | Contract-Kit für alle Rollen — **vor Abschluss von T-23** |
| T-27b | HTTP offline prüfbar (Fake→Real) — **vor Abschluss von T-23** |
| T-25 | Profilwechsel — braucht T-22 und T-24, unabhängig von T-19 |

**Warum T-19 nach hinten rückt.** Mein ursprüngliches Argument war, dass ein
Quellenwechsel ohne verlustfreie Korrektur nicht ausprobierbar ist. Das trägt
nur, wenn etwas von selbst passiert — und genau das darf nicht sein. Solange
zwei Invarianten gelten, ist der heutige Zustand unbequem, aber ungefährlich:

- Eine Plugin-Installation verändert bestehende Instrumente **nicht** automatisch.
- Ein bestehendes Instrument wird nur durch **ausdrückliche** Nutzeraktion neu
  aufgelöst.

Beide gehören zu T-22/T-23 und sind dort zu prüfen. Der eigentliche Erfolgsweg
ist, dass überhaupt jemand ein Plugin schreiben und einsetzen kann.

Ein Ticket für deklarative Quellen entfällt — siehe „Die Entscheidung: nur
Python".

## Offene Entscheidungen

Aus der Codex-Review vom 2026-08-19 (`_tickets/codex-verification-2026-08-19-plugin-system-design.md`).
Jede Zeile braucht eine Entscheidung, bevor T-21 bis T-23 umgesetzt werden.
Die Empfehlung ist meine; die Entscheidung nicht.

| # | Frage | Empfehlung |
|---|---|---|
| 1 | Kanonische Identität und Anbieter-Aliase | `(ticker, mic)` ist Identität — **aber `symbol` bleibt am REST-Rand verpflichtend**. Siehe [Der REST-Vertrag ist öffentlich](#der-rest-vertrag-ist-öffentlich) |
| 2 | Historie beim Listingwechsel | **entschieden:** löschen, vorher bestätigen lassen, manuelle Werte behalten. Archivierung ist ein späteres Feature, keine Voraussetzung |
| 3 | Verträge für Quote, Daily, FX | vor T-22 ausformulieren; solange bleibt `0.x` |
| 4 | Eigener `MetadataRequest` | ja — `ResolveRequest` kennt nur `preferred_mic`, nicht das aufgelöste Listing |
| 5 | Herkunft und Stand je Metadatenfeld | **entschieden (Mike):** Herkunft **je Detail**, Core geschlossen, Details offen und additiv |
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

**Aufgelöst (Mike, 2026-08-20) — und zwar andersherum, als hier zuerst stand:**
Der **Core** ist geschlossen, die **Details** sind offen und additiv. Damit ist
der Widerspruch weg: `label_en`/`label_de` haben ihren Zweck, weil neue Felder
tatsächlich ankommen dürfen.

Was das an Umsetzung verlangt — generische Persistenz, `details` in der API,
generische Darstellung — steht in **T-26**. Solange das fehlt, darf der Vertrag
keine Unterstützung unbekannter Felder *behaupten*; siehe
[Geschlossen ist nur der Core](#was-bewusst-nicht-gebaut-wird).

### Was `is_configured()` nicht kann

Sie liefert `bool` und damit keinen Grund, obwohl `/sources` einen anzeigen
soll. Entweder ein strukturiertes Ergebnis oder eine zweite Diagnosemethode —
mit **T-22** zu entscheiden, wo die Registry entsteht. (Stand vorher: „mit
T-19" — das war falsch zugeordnet, T-19 ist nachrangig und hat mit
Registry-Diagnose nichts zu tun.)

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

> **Historie.** Zwei Zeilen sind inzwischen durch Runde 3/4 und Mikes
> Entscheidungen überholt: `symbol` wird **nicht** `NULL`-fähig, und die
> Feldmenge ist **nicht** geschlossen. Beides steht unten in Runde 4.

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

### Runde 3 (2026-08-20)

| Punkt | Stand |
|---|---|
| T-19: löschen statt archivieren | **übernommen**, in T-19 festgeschrieben |
| `US`: echte MICs, Sammelcode intern | **übernommen**, in T-21; betrifft auch T-18 |
| Reihenfolge: T-19 nachrangig | **übernommen.** Mein Argument trug nur, wenn etwas von selbst passiert — und genau das darf nicht sein. Die zwei Invarianten gehören zu T-22/T-23 |
| **Nullable `symbol` bricht Konsumenten** | **übernommen, Begründung korrigiert.** Zeilenangaben nachgeprüft, alle drei bestätigt. Aber: StockPortfolio ist **nicht öffentlich** und gehört demselben Autor — es begründet keine Kompatibilitätsschicht. Tragend ist, dass **StockInfo** verteilt wird (Docker Hub, Unraid). Ergebnis dasselbe: additiver Weg |
| REST-Vertrag vor Plugin-Vertrag | **übernommen**, eigener Abschnitt — mit der Einschränkung oben |
| Contract-Tests über die Projektgrenze | **abgelehnt, vorerst.** Sie schützen vor einem fremden Konsumenten; den gibt es nicht. Siehe „Was ich zurückgebe" |
| Contract-Test fängt kein Börsensuffix | **behoben** — die Behauptung stand noch in der Spec |
| Reihenfolgetabelle nannte T-19 „verlustfrei" | **behoben** |
| T-23 sprach von gekapselter Zeitgrenze | **behoben** — jetzt ausdrücklich als nicht erzwingbar benannt |

**Ergänzung, die aus Mikes Einwand kam, nicht aus der Review:** Das Symbolformat
ist eine **Vereinbarung**, keine Abhängigkeit — die App bildet es aus ihrer
eigenen Tabelle (`resolver.py:130`). Meine frühere Einordnung als
„Yahoo-Kopplung" war falsch. Das macht T-21 kleiner und `symbol` am REST-Rand
unbedenklich. Die eine echte Bindung ist `resolver.py:170`, wo der Yahoo-Fallback
fremde Symbole übernimmt — und genau dort bricht die Migration.

### Runde 4 (2026-08-20)

| Punkt | Stand |
|---|---|
| **Blocker 1: Feldmenge ist nicht geschlossen** | **übernommen.** Mikes Entscheidung: Core geschlossen, Details offen und additiv, Herkunft je Detail. Codex' Argument gibt den Ausschlag — der Plugin-Vertrag versprach bereits Erweiterbarkeit, die eine Schicht später geendet hätte |
| **Blocker 2: Profilwechsel fehlt** | **übernommen**, eigener Abschnitt + **T-25**. Zwei Vorgänge sind jetzt getrennt: Quelle ergänzen (Datenbank bleibt) gegen Profil ersetzen (frische Datenbank, A gesichert) |
| Frage 1: REST-Vertrag als Ticket? | **ja** → **T-24**, blockiert T-21 |
| Frage 2: Fremdsymbole normalisieren oder ablehnen? | **normalisieren wenn eindeutig, sonst ablehnen und sichtbar machen.** In T-21 eingearbeitet, samt Begründung gegen `BRK-B` → `BRK.B` |
| Meine Ablehnung der Cross-Repo-Contract-Tests | **zurückgenommen.** Codex hat recht: getrennte Artefakte, getrennte Deployments — auf einer Unraid-Box aktualisiert niemand zwei Container atomar. Eigentümerschaft ersetzt keinen Vertrag |
| T-21: `VTI → US` widerspricht „US ist kein MIC" | **behoben**, Verify erwartet `XNAS` |
| T-21: `exchange_mic` gegen entschiedenes `mic` | **behoben** |
| T-21: „kein Datenverlust" gegen `BRK.A`-Risiko | **behoben** — Zerlegung gilt für Symbole aus eigener Regel, der Rest wird gemeldet |
| T-21: `symbol` weiter global unique | **behoben** — Eindeutigkeit gehört auf `(ticker, mic)` |
| Spec-Status, Runde-1-Historie, `is_configured` bei T-19 | **behoben** |

**Vorbehalt zu beiden Blockern:** Sie stützen sich auf Präzisierungen, die Mike
über Codex' Kanal gegeben hat. Ich kenne den Wortlaut nur aus zweiter Hand und
habe sie entsprechend gekennzeichnet — vor der Umsetzung von T-25 gehört das
gegengelesen.

### Runde 5 (2026-08-20)

| Punkt | Stand |
|---|---|
| **`symbol` als Lookup-Schlüssel darf nicht mehrdeutig werden** | **übernommen — der schwerste Punkt.** Nachgeprüft: acht Symbol-Endpunkte, und `get_instrument_by_symbol` nimmt per `ORDER BY id LIMIT 1` die ältere Zeile. Nicht undefiniert, sondern definiert falsch. Lösung: `listing_id` + `409` bei Mehrdeutigkeit, festgeschrieben in T-24 |
| Profilentscheidung direkt bestätigt | Vorbehalt entfernt, Wortlaut in T-25 übernommen |
| Spec sagte an alter Stelle noch „Feldmenge geschlossen" | **behoben** |
| „Was ich zurückgebe" enthielt beantwortete Fragen | **behoben** |
| T-24: „keine Verhaltensänderung" gegen Pflichtwährung | **behoben** — drei Ebenen getrennt, die Korrektur ist jetzt ausdrücklich Teil des Tickets |
| T-21 hängt an T-24 | **behoben** |
| T-21 braucht Zwischenzustand für nicht zerlegbare Zeilen | **übernommen** — `NULL`-fähige Spalten plus `identity_status`, sonst ist „melden statt raten" technisch unmöglich |
| Offene Details ohne Umsetzungsticket | **behoben** → **T-26** |
| T-25: erst B validieren, dann rotieren | **übernommen**, mit Negativtest |
| T-25: „Scheduler steht" reicht nicht | **übernommen** — Backup-API oder Sperre gegen alle Schreiber, atomare Nummernvergabe, nie überschreiben |
| T-25: Profil-Kompatibilitäts-ID statt YAML-Hash | **übernommen**, mit Tabelle was die ID ändert und was nicht |
| T-25: Consumer ist StockPortfolio | **übernommen** — das Dashboard hält keinen Cache über Deployments |
| T-25 hängt auch an T-24 | **behoben** |
| Installation als UX zu kompliziert | **übernommen** → Profilreferenz als Normalfall in T-22, mit eigenem Verify |

**Neu von Mike (2026-08-20):** Verbindliche Felder **samt Versionsnummer** müssen
per API abfragbar sein — und dieselbe Logik für die offenen Felder. Umgesetzt als
`GET /fields` mit `core_version` und `details_version`, in T-24 (Core) und T-26
(Details). Der Grund ist praktisch: Ein Konsument, der Details generisch
darstellen soll, muss sie erfragen können, sonst zieht jedes neue Feld eine
Codeänderung auf beiden Seiten nach sich. Die Versionsnummern sind das Werkzeug —
ein Konsument mit gecachter Liste erkennt daran, dass er neu holen muss, ohne
Inhalte zu vergleichen. **Nicht zu verwechseln mit `generation_id`:** Die
Feldmenge kann sich ändern, ohne dass das Profil wechselt.

### Runde 6 (2026-08-20)

Alle 13 Punkte übernommen — es waren durchweg Vertragsdetails, keine
Grundsatzfragen.

| Punkt | Wohin |
|---|---|
| 1 · `listing_id` = opake UUID, auch für Legacy-Zeilen | T-24, mit Begründung gegen Hash und Integer |
| 2 · ein aktives Listing je ISIN ist eine Grenze | T-24, ausdrücklich benannt |
| 3 · `details`-Hülle festlegen | T-26, samt `origin`, `source`, `as_of`, `shadowed` |
| 4 · Namespaces gegen Feldkollisionen | T-26, Prüfung in Registry **und** Contract-Test |
| 5 · `details_version` bei **jeder** Schemaänderung | T-26, mit Tabelle was zählt und was nicht |
| 6 · `/fields.core` nach Antworttyp gliedern | T-24 — flach wäre ungenauer als das vorhandene OpenAPI |
| 7 · eine Wahrheit für die acht Kennzahlen | T-26, Top-Level ist Kompatibilitätsprojektion |
| 8 · T-26 hängt auch an T-21 und T-23 | behoben |
| 9 · „gleiches Profil" an die Kompatibilitäts-ID binden | T-25 Verify `#1`, `#2`, neu `#2b` |
| 10 · absturzfester Übergang + last-known-good | T-25, mit Zustandsmarker und Verify `#5b`/`#5c` |
| 11 · `generation_id` neu bei jeder Aktivierung | T-25, Verify `#6b` |
| 12 · StockPortfolio braucht ein eigenes Ticket | T-25 — entschieden: eigenes Ticket im Nachbar-Repo, `#8` bleibt bis dahin unbewertet |
| 13 · zwei Textkorrekturen | behoben (additive Version, „derzeit nur US") |

**Zur Aufwandseinschätzung:** Der Einwand trifft. Die Ein-Tages-Zeitfenster für
T-21, T-25 und T-26 sind nach der jetzt erkannten Tiefe zu knapp. Ich lasse sie
vorerst stehen, markiere sie aber als **zu prüfen** — sie zu erhöhen, ohne die
Arbeit geschnitten zu haben, wäre auch nur eine andere Art zu raten. Der
richtige Schritt ist, jedes der drei Tickets vor der Umsetzung in Unteraufgaben
zu zerlegen; dann ergibt sich der Aufwand von selbst.

### Neu von mir: die Testbarkeit trägt noch nicht

**Frage an Codex.** Mike hat gefragt, ob die Testbarkeit der Pluginstruktur
umfassend berücksichtigt ist. Meine ehrliche Antwort: **nein** — und die Lücke
betrifft ausgerechnet das Argument, mit dem dieses ganze Vorhaben begründet ist.

Der Contract-Test sollte „Tests ersetzen, die hier niemand schreiben könnte,
durch Tests, die andere für uns laufen lassen". Er deckt aber nur **eine Ebene**
ab: eine einzelne Quelle, isoliert, ohne Netz.

Sechs Lücken:

1. **Netz ist ungelöst.** Das Beispiel-Plugin liest eine lokale CSV — bequem
   gewählt. Ein EODHD-Plugin machte bei jedem Contract-Lauf echte Requests:
   langsam, unzuverlässig, verbraucht Kontingent.
2. **Der Hausstandard wurde übersehen.** `code-standards` beschreibt
   „Contract-Tests (Fake → Real)" — dieselben Fälle gegen Aufzeichnung *und*
   echte API. Genau das Muster, das Lücke 1 löst; `testing.py` kennt es nicht.
3. **Die Kette wird nirgends getestet.** Reihenfolge, Weiterschalten bei
   `NotResponsible`, `Unavailable` → 502, Schutzschalter, Zusammenführen mehrerer
   Metadaten-Quellen. Im Vertragspaket gibt es **keine einzige** `FakeSource`.
4. **Die Registry hat keine Testinfrastruktur.** T-23 verlangt in Verify-Zeilen
   Ablehnung bei falscher `api_version`, doppelten Namen, Importfehlern — ohne
   absichtlich kaputte Test-Plugins ist das nicht automatisierbar.
5. **Kein Integrations-Harness.** Ein Autor kann seinen Vertrag prüfen, nicht
   aber „läuft mein Plugin in einer echten Instanz".
6. **Zeit ist nicht injizierbar.** TTL, Schutzschalter-Fenster, Rotation sind
   zeitabhängig; ohne einspeisbare Uhr wird jeder Test langsam oder unzuverlässig.

Angelegt als **T-27**, mit dem Fake→Real-Muster als Kern und einem **zweiten
Beispiel-Plugin gegen eine echte HTTP-API**. Erst das beweist den Vertrag für
den Fall, um den es geht.

**Drei Fragen an Codex dazu:**

1. **Reicht Fake→Real, oder braucht es mehr?** Aufgezeichnete Antworten altern
   still — die API ändert sich, die Aufzeichnung nicht. Genügt ein
   `--real`-Lauf vor Releases, oder sollte das Testkit eine Verfallsprüfung für
   Aufzeichnungen mitbringen?
2. **Wo liegt die Grenze des Testkits?** Ich habe geschrieben, Contract-Tests
   beweisen Form und Fehlerverhalten, nicht fachliche Richtigkeit — dass ein
   Plugin das *richtige* Listing wählt, sagt kein Test hier. Ist das die richtige
   Grenze, oder lässt sich fachliche Plausibilität noch maschinell prüfen?
3. **Ist T-27 früh genug eingeordnet?** Es hängt formal an nichts, aber ohne
   Testkit schreibt der erste externe Autor sein Plugin blind. Gehört es vor
   T-23, oder genügt „vor dem ersten fremden Plugin"?

### Runde 7 (2026-08-20) — Antworten zur Testbarkeit

Alle drei Fragen beantwortet, alle Punkte übernommen. Codex hat aus der Frage
einen vollständigen Zielzustand gemacht; das Wesentliche:

**Zu Frage 1 — Fake→Real ist richtig, braucht aber zwei getrennte Tore.** Ein
`--real`-Schalter allein genügt nicht, weil niemand bemerkt, dass er seit Monaten
nicht lief. Eine reine Altersprüfung wäre aber genauso falsch: **Würde der
Offline-Lauf nach Kalenderzeit rot, könnte ein Beiträger ohne Anbieter-Schlüssel
gar nichts mehr bauen.** Also: Offline-Lauf bleibt grün und gibt nur einen
Hinweis; ein eigener Release-Check schlägt fehl. Die Frist ist je Plugin
einstellbar, und der Real-Lauf gehört in den Release des **jeweiligen Plugins** —
StockInfo besitzt weder Schlüssel noch Kontingente fremder Anbieter. Dazu ein
Punkt, den ich nicht bedacht hatte: **Nutzungsbedingungen prüfen**, bevor rohe
Anbieter-Antworten ins Repository wandern.

**Zu Frage 2 — meine Grenze war zu pessimistisch.** Ich hatte geschrieben,
Contract-Tests bewiesen „Form und Fehlerverhalten, nicht fachliche Richtigkeit".
Maschinell prüfbar sind aber sehr wohl: ISIN-Prüfziffer, Übereinstimmung von
Anfrage- und Ergebnis-ISIN, echter MIC statt Sammelcode, gültige Währung,
endliche Zahlen, sinnvolle Datumsfolge, keine doppelten Tagespunkte. Was bleibt:
Ob bei einem *zukünftigen* Papier das gewünschte Listing gewählt wurde — ein
formal korrektes `(ticker, mic)` kann fachlich falsch sein.

Sauberer sind **drei Ebenen** statt einer Grenze: Plugin-Contract (öffentliches
Kit), StockInfo-Integration (Host-Tests bei T-20/23/24/26), Markt-Akzeptanz
(Golden Cases beim Plugin-Autor).

**Zu Frage 3 — „vor dem ersten fremden Plugin" ist zu spät.** Laut T-23 ist die
App **selbst** der erste Plugin-Autor. Das Testfundament muss vor oder parallel
zu T-23 entstehen, und T-23 darf nicht als fertig gelten, bevor seine Registry-
und Kettentests damit laufen.

| Punkt | Wohin |
|---|---|
| T-27 war zu groß für ein Ticket | **geschnitten**: T-27a (Contract-Kit) und T-27b (HTTP Fake→Real) |
| alle fünf Rollen brauchen Contract-Suiten | T-27a — sonst löst ein Plugin die ISIN auf und bleibt für Kurse an yfinance gebunden |
| ein Szenarioformat für Replay, Real und Golden Cases | T-27a |
| **Golden-Erwartungen nicht aus der Aufzeichnung erzeugen** | T-27a — sonst bestätigt der Test nur, dass ein falscher Treffer reproduzierbar falsch ist |
| Transport und Uhr hereinreichen, Socket-Sperre offline | T-27b |
| Freshness-Metadaten und Secret-Bereinigung | T-27b |
| Host-Harness bis zur REST-Antwort | T-23, Verify `#6b` |
| `stockinfo plugin check` als **gemeinsamer** Preflight | T-23, `#6c`/`#6d` — dieselbe Logik für Nutzer und Profilwechsel |
| Crash-Matrix für den Profilwechsel | T-25 (bereits enthalten) |
| `/fields.core` auch in T-26 gegliedert | behoben |
| `details_version`-Widerspruch im Beispiel | behoben |
| Typ von `details_version` festlegen | behoben — nichtnegative Ganzzahl, monoton je Generation |

**Der sachliche Fehler, den ich selbst eingebaut hatte:** T-23 Verify `#5` und
das alte T-27 verlangten, der Schutzschalter greife bei einem **hängenden**
Plugin „ohne echte Wartezeit". Das ist unmöglich — ein Schutzschalter zählt
einen Fehler erst, wenn der Aufruf zurückkehrt, und ein endlos hängender
synchroner Aufruf kehrt nie zurück. Eine Fake-Uhr ändert daran nichts. Korrigiert
zu zwei ehrlichen Tests: wiederholtes `Unavailable` öffnet den Schalter
(Half-open und Reset gegen die Fake-Uhr), und das endlose Hängen ist als **nicht
beherrschbare Grenze dokumentiert**, ohne scheinbar wirksamen Test.

**Erledigt am 2026-08-21: das StockPortfolio-Ticket ist angelegt** —
`StockPortfolio/_tickets/T-35-stockinfo-generation-und-waehrung.md`. Es deckt
`generation_id` samt gezielter Cache-Invalidierung, die Ersatzwährung, den
Cache-Schlüssel und die Prüfung gegen die veröffentlichten Fixtures ab. T-25
Verify `#8` wird **dort** abgenommen.

**Für Codex, zwei Befunde aus dem Nachbar-Repo — beide bestätigen deine
Einschätzung:**

```ts
src/api/mappers.ts:17                     currency: response.currency ?? 'EUR'
src/components/PositionDrilldown.vue:328  row.quote?.currency ?? 'EUR'
```

Die geratene Währung ist schärfer, als sie zunächst wirkt: Die App erklärt in
ihrer eigenen Oberfläche, dass „10.000 USD plus 10.000 EUR keine 20.000 von
irgendetwas" ergeben (`i18n/de.ts:545`) — und unterläuft diese Regel selbst,
sobald eine Währung fehlt. Ein Papier ohne gemeldete Währung landet still in der
Euro-Summe.

Und der Cache liegt in **IndexedDB**, nicht nur im Speicher. Er überlebt jedes
Deployment; dein Punkt, dass hier der eigentliche Konsument der `generation_id`
sitzt und nicht das StockInfo-Dashboard, ist damit belegt.

**Nicht committet:** StockPortfolio hat derzeit uncommittete Änderungen in fünf
Dateien — dort arbeitet jemand. Die Ticketdatei liegt im Arbeitsverzeichnis und
wird mit dem nächsten Commit dort aufgenommen.

### Was ich zurückgebe

**Derzeit nichts offen an Codex.** Alles aus den Runden 2 bis 7 ist beantwortet
und eingearbeitet; die verbleibenden Punkte sind Umsetzungsdetails in den
Tickets T-17 bis T-27b.

**Zwei Dinge liegen bei Mike:**

1. ~~Das StockPortfolio-Ticket~~ — **erledigt am 2026-08-21**, siehe unten.
2. **Die Zeitfenster.** Codex hält die Ein-Tages-Schätzungen für T-21, T-25 und
   T-26 für zu knapp, und ich teile das. Ich habe sie bewusst **nicht** einfach
   erhöht: Ohne Zerlegung wäre das nur eine andere Art zu raten. T-27a und
   T-27b tragen deshalb „zu schätzen" statt einer Zahl.

**Zurückgenommen: meine Ablehnung der Contract-Tests über die Projektgrenze.**
Ich hatte argumentiert, ein Autor bedeute kein Koordinationsproblem. Das gilt
für den **Quellcode**, nicht für die **laufenden Instanzen**: StockInfo und
StockPortfolio sind getrennte Artefakte mit getrennten Images, Deployments und
Update-Zeitpunkten. Auf einer Unraid-Box laufen sie als zwei Container, die
niemand atomar aktualisiert. Wird StockInfo erneuert und StockPortfolio nicht,
bricht es — Eigentümerschaft hilft dagegen nichts.

Übernommen wird Codex' schlanke Form, kein Cross-Repo-CI:

1. StockInfo prüft seinen versionierten Core gegen Fixtures und einen
   OpenAPI-Kompatibilitätsschnappschuss.
2. StockPortfolio prüft seine Mapper gegen dieselben veröffentlichten Fixtures.
3. Vor Releases ein kleiner Lauf, der eine bestehende Position gegen eine
   frische Profil-Datenbank lädt.

## Belege


Alle Messungen vom 2026-08-19, nachstellbar über die Tickets. Zwei
Einschränkungen in eigener Sache: Der Kanada-Befund stützt sich auf zwei ISINs,
nicht auf eine systematische Stichprobe. Und die Anbieter-Konventionen stammen
aus Übersichts- und Doku-Seiten, nicht aus der Praxis — vor einer Entscheidung
für einen konkreten Dienst gehört dessen Dokumentation gelesen, vor allem zum
Umgang mit Mehrfachnotierungen.
