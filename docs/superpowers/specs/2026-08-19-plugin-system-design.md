# StockInfo — Datenquellen als Plugins: deklarativ und als Code

**Datum:** 2026-08-19
**Status:** Design zur Freigabe
**Tickets:** T-17 bis T-23

## Ziel

Datenquellen — ISIN-Auflösung, Kurse, Tageshistorie, Devisen, ETF-Metadaten —
werden austauschbar, ohne die App zu ändern. Beigesteuerte Quellen kommen auf
zwei Wegen ins System: als **Beschreibungsdatei** ohne Code für den Normalfall
und als **Python-Plugin** für den Sonderfall.

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

## Die Entscheidung: zwei Sorten, harte Grenze

### Was gemessen wurde

Am 2026-08-19 geprüft, ob die bestehenden Quellen über schlichtes HTTP
erreichbar sind — also ob eine Beschreibungsdatei sie fassen könnte:

| Quelle | Über HTTP + JSON? | Beleg |
|---|---|---|
| OpenFIGI | **ja**, vollständig | `POST` → `$[0].data[0].ticker = AAPL` |
| Yahoo Kurs | **ja**, Kernfall | `chart.result.0.meta.regularMarketPrice = 126.975` |
| Yahoo ISIN-Suche | **ja** | `quotes.0.symbol = IWDA.L` |
| justETF | **nein** | HTTP 200, aber `text/html`, 504 KB |

Und die Kandidaten, um die es real geht, sind sämtlich REST mit JSON: EODHD,
Twelve Data, Financial Modeling Prep, Marketstack. Genau die Sorte, die ein
kanadischer oder japanischer Nutzer beisteuern würde.

### Deklarativ ist der Regelfall

```yaml
name: eodhd
kind: resolver
handles:
  isin_prefix: [CA, US]
  mic: [XTSE, US]
request:
  url: https://eodhd.com/api/search/{isin}
  params: { api_token: "{config.api_key}" }
response:
  pick: "$[0]"
  map:
    ticker: Code
    mic:    Exchange
    name:   Name
```

Drei Vorteile, die für dieses Vorhaben entscheidend sind:

- **Kein Ausführungsrisiko.** Eine Beschreibungsdatei kann keine Schlüssel
  abziehen. Die Sicherheitsfrage, die bei fremdem Code offenbleibt,
  verschwindet für den Großteil der Fälle.
- **Der Autor muss kein Python können** — nur seine API kennen. Das senkt die
  Schwelle für genau die Nutzer, die erreicht werden sollen.
- **Es ist laufzeitfähig.** Eine geänderte Datei neu einzulesen ist trivial;
  ein Python-Modul sauber neu zu laden ist es nicht.

Dazu: Eine Beschreibungsdatei ist Text. Sie lässt sich in ein Issue kopieren,
per Pull Request beitragen und gegen ein Schema prüfen, bevor sie je läuft.

**Es ist keine getrennte Baustelle.** Der `map:`-Teil ist dasselbe
Feld-Mapping mit Einheiten, das ohnehin gebraucht wird — die `READS`-Tabelle
kommt nur aus einer Datei statt aus einer Klasse.

### Python ist der Sonderfall

Für Scraping (justETF), Bibliotheken mit eigenem Objektmodell (yfinance),
mehrstufige Anmeldung und eigene Rate-Limit-Logik. Der Vertrag dafür steht
bereits als eigenständiges Paket `stockinfo-plugin-api` (Commit `840121c`).

### Die Grenze — und warum sie hart sein muss

**Erlaubt in Beschreibungsdateien:** Pfad-Auswahl, Feld-Zuordnung,
Einheiten-Umrechnung, Zuständigkeits-Deklaration.

**Nicht erlaubt:** Bedingungen, Schleifen, Ausdrücke, HTML-Selektoren.

Wer mehr braucht, schreibt ein Python-Plugin. Der Fallstrick heißt *inner
platform effect*: Sobald Bedingungen und Transformationen ins YAML wandern, ist
eine schlechte Programmiersprache entstanden. Diese Grenze schriftlich
festzuhalten ist wichtiger als das Format selbst — sonst weicht sie schleichend
auf, und zwar mit jeweils guten Einzelbegründungen.

**HTML-Scraping bleibt bewusst draußen**, obwohl es technisch ginge (Home
Assistant hat `scrape:`). HTML-Struktur ändert sich, Selektoren brechen still,
und der Weg endet unweigerlich bei „hier bräuchte ich noch eine Bedingung".

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
| Beschreibungsdateien | REST-Quellen ohne Code | perspektivisch nein |

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
selbst etwas nachlädt**. Der deklarative Weg umgeht das Risiko für den Großteil
der Fälle.

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

Der deklarative Weg bekommt ein eigenes Ticket **nach** T-23: Vorher wüsste man
nicht, wogegen man ihn baut. Er ist trotzdem der Regelfall — nur nicht der erste
Bauschritt.

## Offene Punkte

- **Beschriftungen fremder Felder.** Ein Plugin kann keine Übersetzungen für
  alle Sprachen liefern. Vorschlag: Rückfallkette App-Katalog → Plugin-Label in
  der aktiven Sprache → Plugin-Label englisch → Feldname roh. Das ist eine
  bewusste Ausnahme von „kein sichtbarer Text ohne Katalog-Eintrag" und braucht
  eine Entscheidung.
- **Wer schreibt Plugins?** Nur intern → Entry-Points entfallen, Verzeichnis
  genügt. Auch Dritte → beide Wege, plus Vorlage-Repo.
- **Konkreter Anbieter im Blick?** Bei Twelve Data (MIC-basiert) fällt T-21 fast
  von selbst ab; bei EODHD kommt eine Zuordnungstabelle dazu.

## Belege

Alle Messungen vom 2026-08-19, nachstellbar über die Tickets. Zwei
Einschränkungen in eigener Sache: Der Kanada-Befund stützt sich auf zwei ISINs,
nicht auf eine systematische Stichprobe. Und die Anbieter-Konventionen stammen
aus Übersichts- und Doku-Seiten, nicht aus der Praxis — vor einer Entscheidung
für einen konkreten Dienst gehört dessen Dokumentation gelesen, vor allem zum
Umgang mit Mehrfachnotierungen.
