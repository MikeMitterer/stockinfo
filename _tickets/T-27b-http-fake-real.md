# T-27b · HTTP-Plugins offline prüfbar machen (Fake → Real)

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (`plugin_api/`) | aktiv · Plugin-MVP 3/4 | ~7 h | Referenztransport, Record/Replay, Scrubbing, Freshness | — |

**Löst:** Das Beispiel-Plugin liest eine lokale CSV — bequem gewählt. Ein
EODHD- oder Twelve-Data-Plugin machte bei jedem Contract-Lauf echte Requests:
langsam, unzuverlässig, verbraucht Kontingent. Damit trägt der Vertrag für den
Fall, um den es eigentlich geht, noch nicht.

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

**Hängt an:** T-27a (das Szenarioformat kommt von dort).
**Muss vor Abschluss von T-23 stehen.**

> **Verbindliche MVP-Reihenfolge, Mike 2026-08-27:** T-22 → T-27a →
> **T-27b** → T-23. Erst nach Codex-Freigabe von T-27a beginnen.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | HTTP-Beispielplugin, `make test-plugin-api` | läuft **strikt offline** gegen Aufzeichnungen | | |
| 2 | derselbe Lauf, fehlende Aufzeichnung | **Fehler** über den Audit-Kanal — auch dann, wenn das Szenario `Unavailable` erwartet und der Lauf fachlich grün wäre | | |
| 2b | Ledger nach dem Lauf | eine **unbenutzte** Aufzeichnung schlägt fehl; Ausnahme nur mit `only: real` in der Datei | | |
| 3 | derselbe Lauf, Socket-Zugriff | technisch **gesperrt**, nicht nur unerwünscht | | |
| 3b | Test **ohne** Opt-in | `socket.socket` bleibt unangetastet — die Sperre greift nicht ins fremde Projekt | | |
| 4 | Aufzeichnungsdatei | kein Schlüssel, kein Token, kein Cookie — in Kopf, Query, Rumpf und Antwort | | |
| 5 | Aufzeichnungsdatei | trägt `recorded_at`, letzten erfolgreichen Real-Lauf, Versionen, Szenario-Signatur | | |
| 6 | **überalterte** Aufzeichnung, Offline-Lauf | bleibt **grün**, gibt nur einen Hinweis | | |
| 7 | dieselbe Lage, Release-Check | schlägt **fehl** und verlangt einen Real-Lauf | | |
| 8 | Frist | je Plugin einstellbar | | |
| 9 | `pytest --real` | dieselben Szenarien gegen die echte API | | |
| 10 | Anbieter ist gerade nicht erreichbar | der normale Build bleibt grün; nur der Real-Lauf schlägt fehl | | |

---

## Details

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

## Auflösung

**Entwurf, Runde 2 — noch immer keine Zeile Produktcode.** Runde 1 hat sechs
Korrekturen bekommen; alle sechs treffen zu, und zwei davon hätten die
Umsetzung erst nach dem Bauen widerlegt. Die Grundrichtung — Transport und Uhr
hereingereicht, zwei getrennte Tore, Signatur nach der Bereinigung,
Frankfurter/EZB als geklärter Referenzweg — bleibt.

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

Eine unbenutzte Aufnahme darf ausdrücklich `only: real` tragen, wenn sie zu
einem Fall gehört, der offline nicht läuft. Das ist die einzige Ausnahme, und
sie steht in der Datei, nicht in einem Schalter.

### Zwei Signaturen, nicht eine — und beide nach dem Bereinigen

Runde 1 hatte hier eine Behauptung: Eine Signatur aus Methode, URL und Rumpf
sollte auch **Szenario-Drift** bemerken. Sie kann es nicht. Ändert jemand
`expect` von `NotFound` auf `Unavailable` oder verschiebt eine Grenze in
`plausible`, bleibt die HTTP-Anfrage Zeichen für Zeichen dieselbe. Die Signatur
hätte genau das zertifiziert, wogegen sie gebaut war.

| Signatur | Über was | Wer bildet sie | Wofür |
|---|---|---|---|
| `request_signature` | Schema, normalisierter Host **mit Port**, Pfad, sortierte bereinigte Query, ausgewählte bereinigte Header, kanonischer Rumpf-Hash | `recordings.py` | Zuordnung Anfrage → Aufnahme |
| `scenario_signature` | `case_id`, `expect.__name__`, sortiertes `golden`, sortiertes `plausible`, `real_ok` | der Szenario-Harness | Erkennung, dass sich die **Frage** geändert hat |

Die Aufnahme bindet beide: `request_signature` je Interaktion,
`scenario_signature` einmal je Datei. Läuft eine Suite gegen eine Aufzeichnung
mit abweichender `scenario_signature`, ist das ein Fehlschlag mit der
Aufforderung, neu aufzuzeichnen.

`note` geht **nicht** in die Signatur ein. Die Herkunftsangabe ist Prosa; sie
soll sich verbessern lassen, ohne eine Neuaufzeichnung zu erzwingen — sonst
wird die Signatur zum Grund, Dokumentation nicht anzufassen.

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
python -m stockinfo_plugin.testing.freshness <aufnahme>...   # Exit 0 / 1
make check-recordings                                        # ruft ihn auf
```

Die Arbeit steckt in `check_release_readiness(policy, recordings) -> list[str]`
— eine reine Funktion, direkt testbar, ohne pytest und ohne Netz. Das `__main__`
darüber ist nur Ausgabe und Exit-Code.

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
wird ausdrücklich angefordert:

```python
@pytest.mark.offline_http          # oder: die Fixture direkt anfordern
def test_die_szenarien_laufen_aus_der_aufzeichnung(replayed_source): ...
```

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
