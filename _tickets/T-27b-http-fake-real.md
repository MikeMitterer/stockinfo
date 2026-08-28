# T-27b · Die vorhandenen APIs als Plugins, gegen den echten Dienst geprüft

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (`app/plugins/`) | aktiv · Plugin-MVP 3/4 | ~1 h | Rollen-Schale um die vorhandene Anbindung, Integrationstest | — |

**Löst:** Die Beispiel-Plugins lesen lokale CSV-Dateien — bequem gewählt. Damit
hat noch **kein einziges** Plugin eine echte API angesprochen, und der Vertrag
aus T-27a ist für den Fall, um den es eigentlich geht, ungeprüft.

Die App hat drei solche Anbindungen bereits: Yahoo, justETF und OpenFIGI. Sie
werden **benutzt**, nicht nachgebaut — ein Plugin, das seine API neu schreiben
muss, um den Vertrag zu erfüllen, wäre der Fehler und nicht die Lösung.

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

**Hängt an:** T-27a (das Szenarioformat kommt von dort).
**Muss vor Abschluss von T-23 stehen.**

> **Verbindliche MVP-Reihenfolge, Mike 2026-08-27:** T-22 → T-27a →
> **T-27b** → T-23. Erst nach Codex-Freigabe von T-27a beginnen.

---

> ## ⚠ Produktentscheidung Mike, 2026-08-28: **kein Offline-Lauf**
>
> Wörtlich: *„Wer sagt, dass der Offline-Lauf funktionieren muss? Der
> Integrationstest muss laufen, der Integrationstest verwendet das API, das
> Plugin, das zur Verfügung steht. Wir brauchen keine extrem aufwändige
> Offline-Variante des Tests."*
>
> Damit fällt die **Grundannahme** dieses Tickets, nicht ein Detail daran.
> Record/Replay, Bereinigung, Aufzeichnungsformat, Freshness-Tore und
> Socket-Sperre sind hinfällig; die Verify-Zeilen 1 bis 10 der ursprünglichen
> Fassung waren fast ausschließlich Zusagen darüber.
>
> Ebenfalls von Mike, und der zweite tragende Punkt: **Ein Plugin schreibt
> seine API nicht neu.** Es benutzt die vorhandene Anbindung — Yahoo, justETF,
> OpenFIGI, also genau die Kette der ursprünglichen Implementierung.
>
> Der Entwurf, den Codex in drei Runden geprüft und freigegeben hat, ist damit
> überholt. Die alte Auflösung steht unten als **überholt markiert**, weil die
> Review-Historie sonst ins Leere zeigt; maßgeblich ist die Neufassung ganz
> unten.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

Neufassung nach der Produktentscheidung oben. Die alte Matrix steht im
Abschnitt „Überholt" am Ende.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | `app/plugins/openfigi_resolver.py` | erfüllt die **Resolver**-Rolle des Vertrags aus `plugin_api` | ✅ [^rolle] | |
| 2 | dasselbe Plugin | benutzt `OpenFigiClient`, **schreibt keinen HTTP-Aufruf neu** | ✅ [^dry] | |
| 3 | `tests/test_plugin_openfigi_integration.py` | fragt die **echte** OpenFIGI-API, kein Mock | ✅ [^echt] | |
| 4 | derselbe Test | zwei Papiere über **zwei** Anfragewege (`micCode` und `exchCode`) | ✅ [^echt] | |
| 5 | Papier, das die Börse nicht führt | `NotFound`, **nicht** `Unavailable` | ✅ [^echt] | |
| 6 | ISIN mit falscher Prüfziffer | `NotResponsible`, **ohne** den Dienst zu fragen | ✅ [^ratenlimit] | |
| 7 | `pytest -m "not integration"` | wählt die fremden Dienste ab, der Rest bleibt grün | ✅ [^marker] | |
| 8 | `make test` | grün, inklusive Integrationstests | ✅ [^lauf] | |
| 9 | Yahoo und justETF | als Rolle **noch offen** — sie sprechen nicht direkt HTTP | ➖ [^kette] | |

[^rolle]: `OpenFigiResolver` erbt `Resolver` aus `stockinfo_plugin` und
    beantwortet `ResolveRequest` mit `Resolved`, `NotFound`, `NotResponsible`
    oder `Unavailable`. Damit erfüllt die App zum ersten Mal selbst einen der
    fünf Verträge aus T-27a — ein Vertrag, den niemand erfüllt hat, ist eine
    Behauptung.
[^dry]: Das Plugin ist **Übersetzung, keine zweite Implementierung.** Der
    HTTP-Aufruf, das Anfrageformat, die Auswertung der Antwort und die Regel
    für brauchbare Yahoo-Symbole bleiben in `app/providers/openfigi_provider.py`.
    Übersetzt wird nur `map_isin() → Resolved | NotFound` und
    `SourceUnavailableError → Unavailable`.

    Die zweite Zeile ist die wichtigere: Dieser Client hat den Umbau hinter
    sich, bei dem ein Ausfall als „kenne ich nicht" zurückkam und damit aus
    einem 502 ein 404 wurde. Diese Unterscheidung ein zweites Mal zu
    formulieren hieße, sie ein zweites Mal falsch zu machen.
[^echt]: **Gegen den echten Dienst gelaufen, nicht gegen eine Annahme** — und
    genau das hat einen Fehler in meiner ersten Fassung aufgedeckt:

        US0378331005 @ XNAS (micCode=XNAS) -> None
        US0378331005 @ US   (exchCode=US)  -> 'AAPL'
        IE00B3RBWM25 @ XETR (micCode=XETR) -> 'VGWL'
        CA78012H5675 @ XETR (micCode=XETR) -> None

    `handles()` prüfte zuerst mit `mic_is_wellformed` — und hätte damit
    ausgerechnet `US` abgewiesen, den Sammelcode, über den OpenFIGI US-Papiere
    überhaupt kennt. Welche Codes das sind, weiß der Dienst und nicht der
    Vertrag.

    Die Golden-Werte stammen **nicht** aus dem Dienst: `AAPL` und `VGWL` sind
    nachgeschlagen und hingeschrieben. Käme der Erwartungswert aus derselben
    Antwort, die geprüft wird, prüfte der Test nur, ob der Dienst mit sich
    selbst übereinstimmt.
[^ratenlimit]: Der Test reicht einen Client herein, dessen **Benutzung ein
    Fehler ist**. Ohne ihn bewiese er nur, dass `NotResponsible` herauskommt —
    nicht, dass unterwegs niemand gefragt wurde. Und darum geht es: Ein
    Ratenlimit, das für eine unmögliche Frage draufgeht, fehlt später bei einer
    echten.
[^marker]: `pytest -m "not integration"`: **638 passed, 29 skipped, 4
    deselected**. Der Marker ist eine Möglichkeit, kein Vorschlag, ihn zu
    überspringen — im normalen Lauf laufen die vier mit.
[^lauf]: `make test`: Backend **642 passed / 29 skipped** (vorher 638),
    Plugin-API **260 passed / 1 skipped**, Dashboard **259 passed**.
    `ruff check app tests plugin_api` und `git diff --check` sauber.
[^kette]: **Gemessen, und es ist der Grund für den Zuschnitt.** Von den drei
    Anbietern der ursprünglichen Kette spricht nur OpenFIGI direkt HTTP
    (`httpx.post`). Yahoo geht über `yfinance`, justETF über
    `justetf_scraping` — dort sitzt der Transport in der Bibliothek. Für die
    Rollen `QuoteSource` und `MetadataSource` ist das kein Hindernis, aber ein
    eigener Schritt; er gehört zu T-23, wo die App ohnehin als Plugin-Autor
    auftritt.

---

## Details

> **Überholt.** Alles ab hier bis einschließlich „Codex-Review · Entwurfsrunde 3"
> beschreibt den Offline-Ansatz, den die Produktentscheidung vom 2026-08-28
> aufgehoben hat. Der Abschnitt bleibt stehen, damit die drei Review-Runden
> nicht ins Leere zeigen — **maßgeblich ist die Auflösung ganz am Ende.**

### Zwei Gates statt eines Schalters

Ein bloßer `--real`-Schalter genügt nicht: Niemand bemerkt zuverlässig, dass er
seit Monaten nicht gelaufen ist. Eine reine Altersprüfung ist aber ebenso
falsch — **würde der Offline-Lauf nach Kalenderzeit rot, könnte ein Beiträger
ohne Anbieter-Schlüssel nach Ablauf der Frist gar nichts mehr bauen.**

Deshalb zwei getrennte Tore:

| Tor | Läuft | Schlägt fehl bei |
|---|---|---|
| `make test-plugin-api` | bei jedem Commit, **strikt offline** | unerwarteter Request, fehlende Metadaten, nicht bereinigte Geheimnisse. Alter → nur **Hinweis** |
| Release-/Wartungs-Check | vor einer Veröffentlichung | überalterte oder nie real bestätigte Aufzeichnung |

Die Frist gehört **je Plugin** eingestellt: Ein träger Referenzdienst braucht
eine andere als ein Anbieter ohne stabile API-Version.

**Und der Real-Lauf gehört zum Release des jeweiligen Plugins**, nicht zu dem
von StockInfo — StockInfo besitzt weder die Schlüssel noch die Kontingente
fremder Anbieter.

### „Dieselben Tests" heißt nicht „bytegleich"

Preis, Abrufzeitpunkt und Teile der Metadaten ändern sich legitim. Gleich sind
**Szenarien und Invarianten**, nicht die Antwort selbst. Freshness beweist dabei
für sich genommen nichts — maßgeblich bleibt ein erfolgreicher Real-Lauf; die
Altersgrenze sorgt nur dafür, dass er nicht vergessen wird.

### Vor dem Commit einer Aufzeichnung

- **Bereinigen**: Kopfzeilen, Query-Parameter, Rumpf, Cookies und sensible
  Antwortfelder
- **Nutzungsbedingungen prüfen.** Rohe Anbieter-Antworten ins Repository zu
  legen, ist nicht bei jedem Dienst erlaubt — das gehört vor den ersten Commit
  geklärt, nicht danach

### Der Referenzweg: Transport und Uhr hereinreichen

Record/Replay wird unnötig schwer, wenn jedes Plugin seine HTTP-Bibliothek fest
verdrahtet. Der Vertrag **erzwingt** keine bestimmte Bibliothek — das Kit bietet
aber einen klaren Weg an:

- Beispielplugins bekommen Client/Transport **und Uhr per Konstruktor**
- das Kit stellt einen kleinen Replay-Transport bereit
- Real- und Replay-Modus tauschen nur diesen Transport
- der Offline-Lauf sperrt zusätzlich Socket-Zugriffe

Wer eine andere Bibliothek nutzt, schreibt einen eigenen Adapter — entscheidend
ist die von außen prüfbare Eigenschaft, nicht die Bibliothek. Die Dokumentation
zeigt trotzdem den hereingereichten Weg: Er ist für neu entstehende Plugins
deutlich einfacher und sicherer als ein selbstgebauter Mock-Aufbau.

---

## Auflösung (überholt — siehe Neufassung am Ende)

**Entwurf, Runde 3 — noch immer keine Zeile Produktcode.** Zehn Korrekturen
über zwei Runden; die Grundrichtung — Transport und Uhr hereingereicht, zwei
getrennte Tore, Signatur nach der Bereinigung, Frankfurter/EZB als geklärter
Referenzweg — hat alle überstanden.

Runde 2 hat vier Zustandskanten getroffen, und zwei davon waren Aussagen von
mir, die schlicht nicht stimmten: Die Szenario-Signatur ließ die Anfrage selbst
weg, und ein Flag `only: real` hätte etwas geregelt, das es im Modell von
T-27a gar nicht gibt.

### Vier Module, und warum nicht eins

| Modul | Inhalt | Warum getrennt |
|---|---|---|
| `testing/http.py` | `HttpRequest`, `HttpResponse`, `Transport` (Protocol), `ReplayTransport`, `RecordingTransport`, `MissingRecording`, `ReplayLedger` | Der Transport ist das, was Plugin-Autoren **anfassen**; er darf nicht mit dem Dateiformat verheiratet sein |
| `testing/recordings.py` | Dateiformat, Metadaten, `request_signature`, Kanonisierung, Bereinigung | Das Format überlebt einen Bibliothekswechsel; der Transport nicht unbedingt |
| `testing/freshness.py` | `RecordingPolicy`, `check_release_readiness()`, `python -m …` | Der Release-Check läuft **ohne** pytest und ohne Transport; er darf nicht an beiden hängen |
| `testing/pytest_plugin.py` | `--real`, `--record`, Marker und Fixtures — **keine** autouse-Wirkung | Ein `pytest11`-Entry-Point gehört nicht in einen Modulimport, darf aber auch nichts an sich reißen (siehe unten) |

`Transport` ist wie `ScenarioRunner` **eine** Methode. Real- und Replay-Betrieb
tauschen nur dieses Objekt; das Plugin bekommt es samt Uhr per Konstruktor.

### Der Audit-Kanal — Befund 1 aus Runde 1, und der schwerste

Der Entwurf hatte denselben Fehler wie T-27a Runde 2, eine Ebene weiter außen:
`ReplayTransport` wirft `MissingRecording`, ein **korrektes** Plugin übersetzt
Transportfehler pflichtgemäß in `Unavailable`, und `DirectRunner` fängt fremde
Ausnahmen ebenfalls als `Unavailable` ab. Ein Szenario mit
``expect=Unavailable`` wäre also **grün geworden, gerade weil die Aufzeichnung
fehlte**. Jedes Glied der Kette verhält sich richtig; das Ergebnis ist wertlos.

Ein Befund, der durch das fachliche Ergebnis läuft, kann von einer Erwartung
aufgesogen werden. Deshalb läuft er nicht dort:

`ReplayTransport` führt ein `ReplayLedger` mit `hits`, `misses` und
`unused`. Nach der Suite prüft `assert_replay_clean(ledger)` **unabhängig vom
fachlichen Ergebnis** und schlägt hart fehl bei

* jedem **Miss** — eine Anfrage ohne Aufzeichnung, mit Signatur und
  bereinigter URL in der Meldung,
* jeder **unbenutzten** Aufzeichnung — sie bedeutet, dass das Plugin diese
  Anfrage nicht mehr stellt; die Aufnahme ist stehengebliebener Ballast, der
  eine Abdeckung vortäuscht.

**Unbenutzt ist immer ein Fehler — ohne Ausnahme.** Runde 2 sah hier ein Flag
`only: real` vor. Das war schlicht falsch, und zwar nachprüfbar:
`run_scenarios` wählt `[s for s in scenarios if s.real_ok] if only_real else
list(scenarios)` — der Offline-Lauf führt **alle** Fälle aus, `real_ok`
beschränkt nur den Real-Lauf, und im Real-Modus wird gar keine Aufnahme
abgespielt. Eine „nur real benutzte" Replay-Datei kann es in diesem Modell
nicht geben.

Das Flag wäre also eine **zweite Szenarioauswahl** neben `real_ok` gewesen —
und die einzige Wirkung, die es je gehabt hätte, wäre gewesen, verwaiste
Dateien zu legitimieren. Ist ein Fall nicht abspielbar, verletzt er das Ziel
des Tickets („derselbe Fall offline und real") und wird nicht in Metadaten
versteckt.

### Zwei Signaturen, nicht eine — und beide nach dem Bereinigen

Runde 1 hatte hier eine Behauptung: Eine Signatur aus Methode, URL und Rumpf
sollte auch **Szenario-Drift** bemerken. Sie kann es nicht. Ändert jemand
`expect` von `NotFound` auf `Unavailable` oder verschiebt eine Grenze in
`plausible`, bleibt die HTTP-Anfrage Zeichen für Zeichen dieselbe. Die Signatur
hätte genau das zertifiziert, wogegen sie gebaut war.

| Signatur | Über was | Wer bildet sie | Wofür |
|---|---|---|---|
| `request_signature` | Schema, normalisierter Host **mit Port**, Pfad, sortierte bereinigte Query, ausgewählte bereinigte Header, kanonischer Rumpf-Hash | `recordings.py` | Zuordnung Anfrage → Aufnahme |
| `scenario_signature` | `case_id`, **qualifizierter Typ und alle Felder von `request`**, qualifizierter Name von `expect`, sortiertes `golden`, sortiertes `plausible`, `real_ok` | der Szenario-Harness | Erkennung, dass sich die **Frage** geändert hat |

Die Aufnahme bindet beide: `request_signature` je Interaktion,
`scenario_signature` einmal je Datei. Läuft eine Suite gegen eine Aufzeichnung
mit abweichender `scenario_signature`, ist das ein Fehlschlag mit der
Aufforderung, neu aufzuzeichnen.

`note` geht **nicht** in die Signatur ein. Die Herkunftsangabe ist Prosa; sie
soll sich verbessern lassen, ohne eine Neuaufzeichnung zu erzwingen — sonst
wird die Signatur zum Grund, Dokumentation nicht anzufassen.

**Die Anfrage gehört hinein — Befund 1 aus Runde 2.** Runde 2 hatte sie
weggelassen, und die Lücke ist genau der Fall, für den beide Signaturen gebaut
sind: Ändert jemand die ISIN im Szenario, während ein **fehlerhaftes** Plugin
weiterhin dieselbe HTTP-Anfrage sendet, bleibt `request_signature` gleich —
und die alte Aufnahme bestätigt einen Fall, den sie nie gesehen hat. Die
Gegenprobe dazu ändert deshalb **ausschließlich** ein Request-Feld und hält die
emittierte HTTP-Anfrage absichtlich konstant; ohne diese Konstanz prüfte der
Test nur den Transport.

#### Wie kanonisch serialisiert wird

Ein Signaturbestandteil ohne festgelegte Darstellung ist eine Signatur, die auf
einem anderen Rechner anders ausfällt.

| Wert | Darstellung |
|---|---|
| Typen (`request`, `expect`) | **qualifiziert**: `modul.QualName`, nicht `__name__` — zwei gleichnamige Klassen aus verschiedenen Modulen sind nicht derselbe Fall |
| `date` / `datetime` | ISO 8601; ein `datetime` **muss** einen Zeitzonenbezug tragen (`invariants.has_timezone`), sonst ist es kein Zeitpunkt |
| `Enum` | `EnumKlasse.NAME` — nicht der Wert, der sich ändern darf |
| Dataclass, verschachtelt | Feld für Feld, nach Feldnamen sortiert |
| `float` | `repr()`; es rundtrippt in Python exakt und ist damit stabiler als jede Formatierung |
| `None` | `null`, ausdrücklich unterschieden von einem fehlenden Feld |

Serialisiert wird als JSON mit `sort_keys=True`, gehasht mit SHA-256. Ein Typ
ohne Regel in dieser Tabelle ist ein **Fehler**, keine stille Zeichenkette —
sonst entstehen zwei verschiedene Fälle mit derselben Signatur, und der
Fehlschlag käme erst Jahre später als unerklärlicher Treffer.

**Bereinigen kommt vor Signieren**, bei beiden und über denselben Code. Steckt
der Schlüssel als Query-Parameter in der Anfrage und bildet man die Signatur
über die rohe URL, dann trägt jede Aufzeichnung den Schlüssel im Schlüsselfeld
— also genau dort, wo Bereinigung nicht mehr hinkommt, ohne die Zuordnung zu
zerstören. Und ein Beiträger mit einem *anderen* Schlüssel fände seine
Aufzeichnung nie wieder.

#### Kanonisierung, damit zwei verschiedene Anfragen nicht dieselbe werden

* **Host** kleingeschrieben, Port nur wenn er vom Standard des Schemas abweicht
* **Query** paarweise sortiert, nach der Bereinigung, Prozentkodierung
  normalisiert
* **Header** nur eine benannte Auswahl — `accept`, `content-type` und die
  API-Version des Anbieters. Alle Header aufzunehmen machte die Signatur von
  der HTTP-Bibliothek abhängig; gar keine ließe eine JSON- und eine
  CSV-Anfrage an denselben Pfad zusammenfallen
* **Rumpf** bei JSON über sortierte Schlüssel kanonisiert, sonst über die rohen
  Bytes

### Zwei Tore, und was jedes von beiden liest

| Tor | Liest | Grün, wenn |
|---|---|---|
| `make test-plugin-api` (offline) | `recorded_at`, `scenario_signature`, Ledger | jede Anfrage getroffen, keine unbenutzte Aufnahme, Metadaten vollständig, Datei bereinigt. Alter → **Warnung**, kein Fehlschlag |
| `make check-recordings` (Release) | `last_real_ok` gegen die **Policy** | ein vollständiger Real-Lauf hat bestätigt und liegt innerhalb der Frist |

#### Die Frist gehört einmal je Plugin, nicht in jede Datei

Runde 1 legte `max_age_days` in jede Aufzeichnung. Das war falsch, und zwar
nicht theoretisch: Zwei Dateien desselben Plugins können auseinanderdriften,
und dann gilt für dieselbe Quelle je nach Datei eine andere Frist — ohne dass
irgendwo steht, welche die gemeinte ist. Genau das Muster, das der DRY-Guard
„parallele Sources of Truth" nennt.

Deshalb: Die **Policy** (`RecordingPolicy(max_age_days=…)`) steht einmal in der
Testkonfiguration des Plugins. Der Release-Check liest ausschließlich sie. Die
Aufzeichnung trägt den beim Aufnehmen wirksamen Wert weiterhin als
`max_age_days_at_record` — aber ausdrücklich als **Auditwert**: Er erklärt eine
alte Entscheidung, er trifft keine neue.

#### Der Release-Check ist ein Befehl, kein Vorhaben

„Release-Check" allein ist keine Schnittstelle. Konkret:

```
python -m stockinfo_plugin.testing.freshness <verzeichnis>   # Exit 0 / 1
        [--max-age-days N]                                   # Ad-hoc-Übersteuerung
make check-recordings                                        # ruft ihn auf
```

Die Arbeit steckt in `check_release_readiness(policy, recordings) -> list[str]`
— eine reine Funktion, direkt testbar, ohne pytest und ohne Netz. Das `__main__`
darüber ist nur Ausgabe und Exit-Code.

**Woher die Policy kommt — Befund 4 aus Runde 2.** Runde 2 legte sie in die
pytest-Fixture, und der CLI-Befehl bekommt keine Fixture; die Angabe hatte im
Release-Check schlicht keine Quelle. Sie steht deshalb **deklarativ neben den
Aufzeichnungen**:

```
recordings/
  recordings-policy.toml        # max_age_days = 90
  frankfurter_fx.recording.json
```

`RecordingPolicy.from_file()` lesen **beide** — die Fixture im Test und das
`__main__` im Release-Check. Eine Quelle, zwei Leser. `--max-age-days`
übersteuert für einen einzelnen Lauf und wird in der Ausgabe als Übersteuerung
benannt, damit niemand ein grünes Ergebnis für die Policy hält. Fehlt die
Datei, ist das ein Fehler und kein Standardwert: Eine stillschweigend
angenommene Frist ist genau die Angabe, die niemand je bewusst gesetzt hat.

#### Die Versionen, die Verify `#5` verlangt

| Feld | Woher | Bei Abweichung |
|---|---|---|
| `schema_version` | Format dieser Datei, ganze Zahl | **Fehler** — die Datei wird nicht geraten, sondern neu aufgezeichnet |
| `plugin_api_version` | `stockinfo_plugin.API_VERSION` (ganze Zahl) | größer als der laufende Vertrag → **Fehler**; kleiner → Warnung und Neuaufzeichnung empfehlen |
| `recorder_version` | Version des aufzeichnenden Plugin- beziehungsweise Beispielpakets | Release-Check: **Fehler**; offline: Warnung |
| `provider_api_version` | Pfadsegment beziehungsweise Versionsheader des Anbieters (bei Frankfurter `v2`) | **Fehler** — der Anbieter hat sich unter uns geändert |

Jede dieser vier Regeln bekommt eine **mutative** Gegenprobe: Feld verfälschen,
erwarteten Ausgang und erwartete Meldung prüfen — nach dem Muster der 23
Mutanten aus T-27a. Ohne sie belegte die Tabelle nur, dass die Felder da sind,
nicht dass sie gelesen werden.

`last_real_ok` schreibt ausschließlich ein **vollständig** erfolgreicher Lauf
zurück; die Änderung steht danach im Diff und wird mitcommittet. So ist im
Repository sichtbar, wann zuletzt wirklich jemand den Anbieter gefragt hat.

### Die Socket-Sperre ist eine Sperre — aber sie gehört nicht dem ganzen Projekt

Runde 1 hatte sie als autouse-Fixture in einem `pytest11`-Plugin. Das ist zu
weit gegriffen, und der Grund ist ein Mechanismus, den man leicht übersieht:
**pytest lädt installierte `pytest11`-Plugins automatisch**, und eine
autouse-Fixture daraus wirkt auf *alle* Tests des fremden Projekts. Wer unser
Kit installiert, hätte damit still auch seine eigenen Integrationstests vom
Netz getrennt — ein Paket, das Verträge anbietet, hätte fremde Testläufe
umgebaut.

Deshalb liefert das Plugin nur **Optionen, Marker und Fixtures**. Die Sperre
wird ausdrücklich angefordert — und zwar auf **einem** Weg, nicht wahlweise:

```python
def test_die_szenarien_laufen_aus_der_aufzeichnung(replay_runner): ...
```

`replay_runner` **hängt zwingend** an der Guard-Fixture; wer den Replay-Betrieb
anfordert, bekommt die Sperre mit, ohne sie zu erwähnen. Der Marker
`@pytest.mark.offline_http` löst denselben Weg nur deklarativ aus, er ist kein
zweiter.

Der Unterschied ist nicht kosmetisch: „Marker **oder** Fixture" hieße, dass die
Referenzsuite die Sperre vergessen kann, ohne dass etwas auffällt — der Lauf
bliebe grün, nur eben aus der Aufzeichnung *und* potenziell aus dem Netz. Eine
Sperre, deren Anwendung optional ist, prüft am Ende die Disziplin des Autors
statt der Eigenschaft.

Der Nachweis hat zwei Hälften, und die zweite ist die wichtigere:

1. **Mit** Opt-in schlägt ein Verbindungsversuch fehl — sonst ist die Sperre
   eine Behauptung.
2. **Ohne** Opt-in bleibt `socket.socket` unangetastet — sonst wüsste niemand,
   dass sie begrenzt ist, und der Befund aus dieser Runde käme über eine andere
   Tür zurück.

### Die Betriebsarten, vollständig

| Betriebsart | Transport | Sockets | Aufnahmen | Metadaten |
|---|---|---|:--:|---|
| Standard (offline) | `ReplayTransport` | gesperrt, wo angefordert | nur gelesen | nur gelesen; Alter → Warnung |
| `--real` | echter Transport | offen | **nicht** geschrieben | `last_real_ok` nach vollständig grünem Lauf |
| `--record` | echter Transport, mitschreibend | offen | neu geschrieben | `recorded_at` **und** `last_real_ok` |
| `make check-recordings` | keiner | irrelevant | nur gelesen | liest `last_real_ok` gegen die Policy |

`--record` braucht Netz und ist deshalb ein Real-Betrieb; `--real --record`
gemeinsam ist zulässig und bedeutet dasselbe wie `--record` allein. Der
Release-Check ist ein eigener Befehl und lässt sich mit keinem der Schalter
kombinieren.

**Geschrieben wird erst am Ende, und nur ganz.** Ein Lauf, der bei Fall sieben
von zehn scheitert, darf weder die sieben Aufnahmen davor noch `recorded_at`
zurücklassen: Danach stünde eine halbe Wahrheit in der Datei, und der nächste
Lauf hielte sie für vollständig. Also Sammeln im Speicher, Schreiben über eine
temporäre Datei und `os.replace` — atomar, nachdem die **gesamte ausgewählte**
Suite grün war.

**Und „ausgewählt" ist die Falle dahinter:** Wer mit `-k` einen Teil auswählt,
hat den Rest nicht bestätigt. `last_real_ok` würde trotzdem behaupten, der
Anbieter sei vollständig gefragt worden — dieselbe stille Überzeichnung wie
`P-01`. Deshalb: Wurde deselektiert, bleibt `last_real_ok` unverändert und der
Lauf sagt es ausdrücklich.

#### `--real` bestätigt nur, was offline auch belegt ist

`--real` schreibt `last_real_ok` **ausschließlich** an eine vorhandene Aufnahme
mit passender `scenario_signature`. Fehlt sie oder driftet sie, wird nichts
gestempelt, und die Meldung verweist auf `--record`.

Der Grund: `last_real_ok` ist eine Aussage über *diese* Aufzeichnung — „was
hier steht, hat der Anbieter bestätigt". Ohne Aufnahme gäbe es nichts zu
bestätigen; bei abweichender Signatur bestätigte der Real-Lauf eine andere
Frage als die, die in der Datei steht. Beides wäre eine Freshness-Angabe ohne
Gegenstand, und der Release-Check baut auf ihr auf.

#### `os.replace` ist pro **Datei** atomar — und die Suite ist die Datei

Das ist die ehrliche Grenze: Ersetzt ein Lauf mehrere Dateien und stirbt der
Prozess dazwischen, bleibt ein gemischter Stand. Ein Manifest darüber würde das
Problem nur verschieben — dann sind Manifest und Dateien nicht gemeinsam
atomar.

Deshalb zwei Festlegungen statt einer Beteuerung:

1. **Die Aufzeichnung einer Szenariosuite ist genau eine Datei.** Damit ist die
   Einheit, die zusammen stimmen muss, auch die Einheit, die `os.replace`
   atomar ersetzt. Innerhalb einer Suite gibt es keinen gemischten Stand.
2. **Über mehrere Suiten hinweg ist der Commit die Generation.** Jeder
   veröffentlichende Lauf schreibt dieselbe `run_id` in jede Datei, die er
   anfasst. Ein abgebrochener Lauf hinterlässt damit **unterschiedliche**
   `run_id`s — sichtbar im Diff vor dem Commit, und der Release-Check weist
   einen Stand mit uneinheitlicher `run_id` ab. Wir behaupten keine
   dateiübergreifende Atomarität; wir machen ihr Fehlen **erkennbar**.

Beide Gegenrichtungen gehören in die Tests: ein Suite-Fehlschlag (nichts
geschrieben, keine halbe Datei) **und** ein Abbruch mitten in der
Veröffentlichung (erste Datei vollständig und gültig, uneinheitliche `run_id`,
Release-Check rot).

`MissingRecording` ist aus demselben Grund ein **Fehler** und kein Rückfall:
Ein Transport, der bei fehlender Aufzeichnung ins Netz greift, macht die
gesamte Offline-Zusage zu einer Vermutung.

### Das Beispielplugin: Frankfurter/EZB — und warum ausgerechnet das

Das Ticket verlangt die Klärung der Nutzungsbedingungen **vor** dem ersten
Commit einer Aufzeichnung. Sie ist geklärt:

* [api.frankfurter.dev](https://frankfurter.dev/) — frei, quelloffen, **ohne
  Schlüssel und ohne Kontingent**, Daten von der EZB.
* Die EZB erlaubt die Wiedergabe ausdrücklich: *„When such information is
  distributed or reproduced, it must appear accurately and the ECB must be
  cited as the source"* — und, für uns der entscheidende Satz: *„If the
  information is modified by the user … this must be stated explicitly."*

Eine bereinigte, gekürzte Aufzeichnung **ist** eine Änderung. Deshalb trägt
jede Aufzeichnungsdatei zwei Pflichtfelder `source` und `notice`, in denen
Quelle und Eingriff genannt werden. Das ist keine Förmlichkeit, sondern die
Bedingung, unter der die Datei überhaupt im Repository liegen darf.

**Und die Quelle wird festgenagelt, nicht angenommen.** Frankfurter kann
mehrere Anbieter ausliefern; geklärt haben wir die Bedingungen genau eines.
Jede Anfrage pinnt deshalb `providers=ECB`, und die **Antwort wird darauf
geprüft** — liefert sie einen anderen Anbieter, ist das ein Fehlschlag und
keine Aufzeichnung. Sonst läge irgendwann eine Datei im Repository, deren
Rechtelage wir nie geprüft haben, und niemandem fiele es auf.

### Wo die Bereinigung endet — und dass sie endet

Bereinigt werden konfigurierte Geheimwerte **und** sensible Schlüsselnamen
(`authorization`, `api_key`, `token`, `cookie`, `set-cookie`, …), rekursiv in
Query, Kopf, Rumpf und Antwort, danach ein Blick auf die **serialisierte**
Datei: Steht ein bekannter Geheimwert noch im Text, wird nicht geschrieben.

Die Grenze steht ausdrücklich in der Dokumentation, weil eine verschwiegene
Grenze schlimmer ist als eine bekannte:

* Ein Geheimnis, das uns niemand genannt hat, wird nicht gefunden. Die Prüfung
  kennt Werte und Namen — sie kennt keine Bedeutung.
* Ein Geheimnis **in** einem undurchsichtigen Feld (signierte URL, JWT-Nutzlast,
  Opaque-Token) überlebt, weil es nicht als eigener Wert vorkommt.
* Deshalb bleibt der Blick eines Menschen in den Diff vor dem Commit einer
  Aufzeichnung Teil des Verfahrens. Das Werkzeug macht ihn billiger, nicht
  überflüssig.

Fachlich passt es: Ein `FxSource` ist eine der fünf Rollen aus T-27a, und
Wechselkurse sind der Fall, bei dem „dieselben Tests, andere Zahlen" natürlich
auftritt — der Kurs ändert sich täglich, `base`/`quote` nie.

**Die Kehrseite nenne ich, statt sie zu umgehen:** Ein schlüsselloser Anbieter
hat nichts zu bereinigen. Verify `#4` wäre an diesem Beispiel trivial erfüllt
und damit nichts wert. Die Bereinigung wird deshalb an anderer Stelle
nachgewiesen — an synthetischen Aufzeichnungen mit Schlüssel, Token und Cookie
in Kopf, Query, Rumpf und Antwort, plus einer Prüfung über **alle** committeten
Aufzeichnungen. Einen echten Anbieter mit Schlüssel nur zu Vorführzwecken zu
befragen, wäre die schlechtere Wahl: Wir hätten seine Bedingungen zu klären,
ohne sein Angebot zu nutzen.

### Was diese Runde ausdrücklich **nicht** entscheidet

* Welche HTTP-Bibliothek ein fremdes Plugin verwendet. Der Vertrag erzwingt
  keine; das Kit liefert einen Adapter für `httpx` als gangbaren Weg mit.
* Wie ein kommerzieller Anbieter mit Kontingent eingebunden wird. Das ist die
  Frage, für die T-27b das Werkzeug baut — beantworten wird sie das erste
  Plugin, das ihn wirklich anspricht.

### Verify `#10` hat zwei Hälften — beantwortet in Runde 1

Meine Lesart war zu eng. Der Nachweis besteht aus beiden Richtungen:

1. **Offline grün mit einem vergifteten Live-Transport.** Der Suite wird ein
   echter Transport untergeschoben, der bei jedem Aufruf wirft — und der Lauf
   bleibt grün. Das beweist, was die Zeile eigentlich meint: dass der
   Offline-Weg den Live-Weg **nie berührt**. Ohne diese Hälfte prüft man nur,
   dass gerade kein Netz da war.
2. **Real rot bei unerreichbarem Host**, mit einer deutbaren und
   **geheimnisfreien** Meldung statt eines Stacktrace — die URL in der Meldung
   läuft durch dieselbe Bereinigung wie die Aufzeichnung.

### Der Schnitt bleibt ein beobachtbares Ergebnis

Vier Module, ein Beispielplugin, ein Befehl — aber eine einzige Aussage, an der
das Ticket gemessen wird: **Dieselben Szenarien laufen offline aus der
Aufzeichnung und real über HTTP, ohne geheimen und ohne stillen Netzpfad.**
Time-box `~7 h`.

---

## Codex-Review · Entwurfsrunde 1 · `a1ac605`

Die Grundrichtung trägt: Transport und Uhr werden injiziert, Offline- und
Release-Gate bleiben getrennt, die Signatur entsteht erst nach der
Bereinigung, und Frankfurter/EZB ist als rechtlich geklärter Referenzweg
geeignet. Vor Produktcode braucht der Entwurf sechs Korrekturen:

1. **Hoch · Eine fehlende Aufzeichnung darf nicht zum erwarteten Fachfehler
   werden.** `ReplayTransport` wirft `MissingRecording`; ein korrektes Plugin
   muss Transportfehler aber in `Unavailable` übersetzen, und `DirectRunner`
   fängt fremde Ausnahmen ebenfalls als `Unavailable`. Ein Szenario mit
   `expect=Unavailable` könnte deshalb trotz fehlender Aufnahme grün werden —
   derselbe Selbstbestätigungsfehler wie T-27a Runde 2. Der Replay-Harness
   braucht einen **separaten Audit-Kanal**: jeden Miss protokollieren und nach
   dem Lauf unabhängig vom fachlichen Ergebnis hart fehlschlagen. Ebenso
   festlegen, wie unerwartete und unbenutzte Aufzeichnungen behandelt werden.
2. **Hoch · Request-Signatur und Szenario-Signatur sind zwei verschiedene
   Dinge.** Die beschriebene Signatur aus Methode/URL/Body findet eine
   HTTP-Aufnahme; sie bemerkt keine Änderung an `expect`, `golden` oder
   `plausible`. Damit erfüllt sie die behauptete Szenario-Drift-Erkennung
   nicht. Benötigt werden `request_signature` für Replay-Lookup und eine
   getrennte `scenario_signature` über die urteilsrelevanten kanonischen
   Scenario-Felder. Die Aufnahme bindet beide; der Scenario-Harness, nicht der
   HTTP-Transport, berechnet die zweite.
3. **Hoch · Ein `pytest11`-Entry-Point mit globaler Autouse-Socket-Sperre ist
   zu invasiv.** Pytest lädt installierte `pytest11`-Plugins automatisch, und
   eine Plugin-Autouse-Fixture wirkt auf alle Tests des fremden Projekts. Das
   Contract-Kit würde damit nach bloßer Installation auch unabhängige
   Integrationstests vom Netz trennen. Siehe [offizielle pytest-Dokumentation
   zur Plugin-Autoload-Reihenfolge](https://docs.pytest.org/en/latest/how-to/writing_plugins.html).
   Das Plugin darf Optionen/Marker/Fixtures bereitstellen, die Sperre muss aber
   ausdrücklich für die HTTP-Szenariosuite aktiviert werden — etwa über das
   Root-`conftest.py` des Plugin-Autors oder einen Marker mit kontrollierter
   Fixture — und genau dieser Opt-in-Weg braucht eine Gegenprobe.
4. **Hoch · Die Betriebsarten sind noch widersprüchlich.** Die Sperre ist nur
   unter `--real` offen, aber `--record` braucht ebenfalls Netz. Eine
   verbindliche Matrix muss Default/`--real`/`--record`/Freshness-Check,
   zulässige Kombinationen, Transportwahl, Socket-Regel und Dateischreibrechte
   festlegen. `recorded_at` ändert nur ein erfolgreicher Record-Lauf;
   `last_real_ok` erst ein **vollständig** erfolgreicher Real-/Record-Lauf,
   atomar nach der gesamten ausgewählten Suite — nie schon nach der ersten
   grünen Anfrage. Teilfehler dürfen weder Metadaten noch Aufnahmen halb
   aktualisieren.
5. **Mittel · „Je Plugin" darf nicht „in jeder Aufnahme dupliziert" heißen.**
   `max_age_days` in jeder Datei kann innerhalb desselben Plugins driften. Die
   aktuelle Policy gehört einmal in die Plugin-Testkonfiguration beziehungsweise
   Fixture; eine Aufnahme darf den beim Erstellen wirksamen Wert als Auditwert
   tragen, aber der Release-Check liest die eine aktuelle Policy. Dazu einen
   konkreten, automatisierbaren Release-Befehl benennen und testen —
   „Release-Check“ allein ist noch keine ausführbare Schnittstelle.
6. **Mittel · Kanonisierung, Bereinigungsgrenze und Referenzquelle müssen
   präziser sein.** Die Request-Signatur braucht neben Methode und Pfad auch
   Schema/normalisierten Host samt Port, sortierte bereinigte Query,
   relevante bereinigte Header (zum Beispiel `Accept`, `Content-Type` und
   Anbieter-API-Version) und einen kanonischen Body-Hash; sonst kollidieren
   fachlich verschiedene Requests. Scrubbing muss konfigurierte Secret-Werte
   **und** sensible Schlüsselnamen rekursiv in Request und Response behandeln,
   danach die serialisierte Datei prüfen und seine unvermeidliche Grenze offen
   dokumentieren. Beim Beispiel muss jede Anfrage `providers=ECB` festpinnen
   und die Provider-Angabe der Antwort prüfen; Frankfurter kann sonst Quellen
   mischen. Die [Frankfurter-Dokumentation](https://frankfurter.dev/) verweist
   je Provider auf dessen Bedingungen, während die
   [EZB-Bedingungen](https://www.ecb.europa.eu/services/using-our-site/disclaimer/html/index.en.html)
   Quellenangabe und Kennzeichnung von Änderungen verlangen.

**Antwort auf Verify `#10`:** Die vorgeschlagene Gegenrichtung gehört dazu,
reicht allein aber nicht. Der Nachweis hat zwei Hälften: Der Offline-Lauf läuft
mit einem absichtlich unerreichbaren/„poisoned“ Live-Transport grün und beweist
damit, dass er ihn nie berührt; der Real-Lauf gegen einen unerreichbaren Host
schlägt rot mit einer deutbaren, geheimnisfreien Meldung statt Stacktrace fehl.

**Prozess:** Vor Umsetzung die Time-box aus „zu schätzen“ in eine konkrete
Größe ändern. Der Schnitt darf mehrere Module berühren, bleibt aber ein
beobachtbares Ergebnis: dieselben Szenarien laufen offline aus Aufnahme und
real über HTTP, ohne geheimen oder stillen Netzpfad.

**Evidenz:** Seit `f1254fe` änderte sich ausschließlich das Ticket; der
Produktstand blieb mit Backend 638/29 skipped, Plugin-API 260/1 skipped und
Dashboard 259 unverändert. Die Quellen- und Rechteaussagen wurden an den oben
verlinkten Primärseiten geprüft.

---

## Codex-Review · Entwurfsrunde 2 · `617b407`

Die sechs Befunde aus Runde 1 sind im Grundsatz aufgelöst. Audit-Kanal,
Signaturtrennung, Opt-in-Grenze, Modusmatrix, zentrale Policy und
Kanonisierung bilden jetzt einen implementierbaren Kern. Vor Produktcode
bleiben vier präzise Restpunkte:

1. **Hoch · Die Szenario-Signatur lässt die eigentliche Anfrage weg.** Sie
   enthält `case_id`, `expect`, `golden`, `plausible` und `real_ok`, aber nicht
   Typ und Felder von `Scenario.request`. Ändert jemand etwa die ISIN im
   Szenario, während ein fehlerhaftes Plugin weiterhin die alte HTTP-Anfrage
   sendet, bleiben `request_signature` **und** die heutige
   `scenario_signature` gleich; die alte Aufnahme kann den neuen Fall
   bestätigen. In die Signatur gehören der qualifizierte Request-Typ und alle
   kanonisch serialisierten Request-Felder. Für `expect` ebenfalls den
   qualifizierten statt nur den kurzen Klassennamen verwenden; Datumswerte,
   Enums und verschachtelte Strukturen brauchen eine festgelegte kanonische
   Darstellung. Eine Gegenprobe ändert ausschließlich das Request-Feld und
   hält die emittierte HTTP-Anfrage absichtlich gleich.
2. **Hoch · `only: real` an einer unbenutzten Aufnahme widerspricht T-27a.**
   Der normale Lauf führt dort **alle** Szenarien offline aus; `real_ok`
   beschränkt nur den Real-Lauf. Im Real-Modus wird gerade keine Aufnahme
   abgespielt. Eine „nur real“ benutzte Replay-Datei kann es in diesem Modell
   daher nicht geben; das neue Flag wäre eine zweite Szenarioauswahl und könnte
   verwaiste Dateien legitimieren. Unbenutzt muss immer fehlschlagen. Falls ein
   Fall nicht replaybar ist, verletzt er das Ziel „derselbe Fall offline und
   real“ und wird nicht über Metadaten versteckt.
3. **Mittel · Schreib- und Bestätigungs-Lifecycle braucht noch die letzte
   Zustandskante.** `--real` darf `last_real_ok` nur an einer vorhandenen
   Aufnahme mit passender `scenario_signature` aktualisieren; bei fehlender
   oder driftender Aufnahme muss es auf `--record` verweisen, sonst ist die
   Real-Bestätigung nicht an den Offline-Beleg gebunden. Außerdem ist
   `os.replace` nur **pro Datei** atomar. Wenn eine Suite mehrere Dateien
   ersetzt und der Prozess dazwischen stirbt, bleibt ein gemischter Stand.
   Entweder ein Plugin-Bundle/Manifest wird mit einem Replace veröffentlicht,
   oder der Entwurf nennt ehrlich einen generationsgebundenen Commit-Schritt,
   durch den der Release-Check nur eine vollständig publizierte Generation
   akzeptiert. Tests brauchen Suite-Fehler **und** Abbruch während der
   Veröffentlichung als Gegenrichtungen.
4. **Mittel · CLI-Policy und die versprochenen „Versionen“ sind noch
   undefiniert.** `python -m …freshness <aufnahme>...` bekommt in der gezeigten
   Signatur keine `RecordingPolicy`; festlegen, ob sie aus einem Manifest,
   einem expliziten `--max-age-days` oder einer importierbaren Plugin-
   Konfiguration stammt. Verify `#5` verlangt Versionen, der Entwurf benennt
   aber keine Felder. Mindestens Format-/Schema-Version, Plugin-API-Version und
   Version des aufzeichnenden Plugins beziehungsweise Beispielpakets mit
   Vergleichsregel festschreiben und mutativ testen.

Beim Socket-Opt-in bitte einen **kanonischen** Weg wählen statt „Marker oder
Fixture“: Die bereitgestellte Replay-/Scenario-Fixture hängt zwingend am
Socket-Guard; der Marker darf diesen Weg nur deklarativ auslösen. So kann die
Referenzsuite den Guard nicht versehentlich vergessen, während fremde Tests
ohne Opt-in unangetastet bleiben.

**Evidenz:** Die Änderung bleibt rein dokumentarisch; der Produktstand ist
unverändert. Die Runde ist weiterhin konvergent: vier Zustandskanten im
vorhandenen Entwurf, keine neue Schicht und keine Rebaseline.

---

## Codex-Review · Entwurfsrunde 3 · `af72b5a` · umsetzungsreif

Die vier Restkanten sind geschlossen. Die Grundentscheidungen sind über drei
Runden stabil geblieben, alle betroffenen Schichten sind inventarisiert, es
fehlt keine Produktentscheidung und kein unabhängiger Scope. Eine weitere
Entwurfsrunde würde keine zusätzliche Sicherheit mehr erzeugen; der nächste
Beleg muss ausführbarer Produktcode sein.

Eine eindeutige Fachkorrektur hat Codex direkt im Ticket vorgenommen:
`stockinfo_plugin.API_VERSION` ist eine Ganzzahl, keine semantische Version.
Eine aufgezeichnete höhere API-Version ist für den laufenden Vertrag
unverständlich und damit ein Fehler; eine ältere ist zunächst eine Warnung mit
Empfehlung zur Neuaufzeichnung. Major-/Minor-Vergleiche gehören nur zu echten
SemVer-Feldern wie `recorder_version`.

**Freigabeumfang:** Freigegeben ist der Entwurf zur Umsetzung **im selben
Ticket T-27b**, nicht das fertige Ticket und nicht der Wechsel zu T-23. Die
Implementierung muss die im Verify-Block und in der Auflösung benannten
Mutanten/Gegenproben tatsächlich ausführen; Prosa allein ist ab jetzt keine
weitere Übergabegrundlage.

---

## Auflösung · Neufassung nach der Produktentscheidung

Maßgeblich ist dieser Abschnitt; alles oberhalb der Verify-Matrix bis hierher
beschreibt den aufgehobenen Offline-Ansatz.

### Was gebaut wurde

`app/plugins/openfigi_resolver.py` — eine **Rollen-Schale** um den vorhandenen
`OpenFigiClient`. Sie enthält keinen HTTP-Aufruf, kein Anfrageformat, keine
Antwortauswertung; das alles bleibt in `app/providers/openfigi_provider.py`.
Übersetzt wird ausschließlich in die Sprache des Vertrags:

    map_isin() liefert einen Ticker      →  Resolved
    map_isin() liefert None              →  NotFound
    SourceUnavailableError               →  Unavailable
    ISIN ohne gültige Prüfziffer         →  NotResponsible

`tests/test_plugin_openfigi_integration.py` fragt den echten Dienst. Vier
Fälle: zwei Auflösungen über **zwei verschiedene** Anfragewege, ein Papier, das
die Börse nicht führt, und eine ISIN mit falscher Prüfziffer, die gar nicht
erst gefragt wird.

### Warum der Test gegen die echte API läuft

Weil er dann etwas belegt, was kein Double belegen kann: dass das
Anfrageformat noch stimmt, dass die Antwort noch so aussieht wie gedacht, und
dass die Übersetzung in die Rollen trägt. Der Preis ist die Abhängigkeit von
einem fremden Dienst und seinem Ratenlimit — deshalb der Marker `integration`
und `-m "not integration"` als Ausweg, wenn kein Netz da ist.

**Und der Test hat sich sofort bezahlt gemacht.** Meine erste Fassung von
`handles()` prüfte das Börsenmerkmal mit `mic_is_wellformed`. Am echten Dienst
gemessen:

    US0378331005 @ XNAS (micCode=XNAS) -> None
    US0378331005 @ US   (exchCode=US)  -> 'AAPL'

`US` ist der Sammelcode der eigenen Tabelle und kein MIC — die Formprüfung
hätte genau den Weg abgewiesen, über den OpenFIGI US-Papiere kennt. Gegen ein
Double wäre das nie aufgefallen, weil das Double geantwortet hätte, was ich
ihm gesagt hätte.

### Was offen bleibt und wohin es gehört

Yahoo und justETF sprechen nicht direkt HTTP, sondern über `yfinance` und
`justetf_scraping`. Für ihre Rollen (`QuoteSource`, `MetadataSource`) ist das
kein Hindernis, aber ein eigener Schritt — er gehört zu **T-23**, wo die App
ohnehin als Plugin-Autor auftritt und die Registry die Quellen lädt.

### Verifikation

* `make test`: Backend **642 passed / 29 skipped** (vorher 638), Plugin-API
  **260 passed / 1 skipped**, Dashboard **259 passed**.
* `pytest -m "not integration"`: **638 passed, 29 skipped, 4 deselected**.
* `ruff check app tests plugin_api` und `git diff --check` sauber.

---

## Codex-Review · Runde 4 · `8698aa0` · Nacharbeit

Die Produktkorrektur geht in die richtige Richtung, ist aber noch nicht
vollständig. Das Inventar bestätigt zunächst die wichtige Hälfte: Von den
begonnenen T-27b-Modulen `testing/http.py`, `testing/recordings.py`,
`testing/freshness.py`, `testing/pytest_plugin.py` sowie Frankfurter-Beispiel
und -Test ist nichts im Quellbaum oder in Paketmetadaten verblieben. Es gibt
keinen Record-/Replay-Entry-Point, keine Cassette und keinen Mitschnitt. Der
echte OpenFIGI-Lauf bestand unabhängig mit **4 passed**.

Drei Befunde verhindern die Freigabe:

1. Der Online-Erfolgsfall gibt `Resolved(ticker="AAPL", mic="US", ...)`
   zurück. `US` ist nach den eigenen Invarianten ein Sammelcode statt eines
   MIC; `is_real_mic("US")` ist `False`. Damit widerspricht das erste echte
   Plugin unmittelbar `ResolverContract`. Zugleich wiederholt der Adapter die
   bereits in `app.resolver.OpenFigiResolver` vorhandene Kette aus
   `figi_lookup`, Client-Aufruf und Ergebnis-/Fehlerübersetzung. Er muss diese
   vorhandene Resolver-API delegieren und darf nur deren Ergebnis in den
   Plugin-Typ übersetzen. Ein echter Online-Erfolgsfall verwendet einen echten
   MIC.
2. Der abgebrochene Offline-Ansatz steckt noch in der öffentlichen
   T-27a-Szenario-API: `Scenario.real_ok`, `only_real`, die dazugehörige
   Validierungsregel und mehrere Docstrings/Tests existieren ausschließlich für
   die nun gestrichenen zwei Betriebsarten. Entfernen; die normalen
   Unit-Test-Bausteine (`Scenario`, Validierung, `DirectRunner`, vollständiger
   Lauf) bleiben bestehen.
3. Der vermeintliche Unit-Test mit `PoisonedClient` steht unter dem
   modulweiten `integration`-Marker und wird im netzfreien Lauf abgewählt.
   Normale Unit-Tests prüfen Zuständigkeit und alle Übersetzungsrichtungen mit
   kleinen testlokalen Doubles und wenden den vorhandenen `ResolverContract`
   auf den Adapter an. Die Integrationsdatei enthält nur echte Netzfälle.

**Evidenz:** `pytest -q tests/test_plugin_openfigi_integration.py` scheiterte
in der Netzwerksandbox erwartungsgemäß mit drei `Unavailable`-Antworten und
bestand mit freigegebenem Netz anschließend **4/4**. `pytest -q -m "not
integration"` bestand mit **638 passed / 29 skipped / 4 deselected** und
belegt zugleich, dass der Poisoned-Client-Test dort fehlt. Die direkte
Vertragsgegenprobe erzeugte `Resolved(..., mic='US')` und
`contract_mic_valid=False`.

Der neue Prozessriegel aus Commit `e5f86fa` hält diese Fehlerklasse dauerhaft
fest: ohne datierte Ausnahme von Mike keine Record-/Replay-, Transport-,
Socket-, Freshness-, CLI- oder Testplugin-Infrastruktur; Standard sind normale
Unit-Tests und echte Online-Integrationstests über vorhandene APIs.
