# T-27b · HTTP-Plugins offline prüfbar machen (Fake → Real)

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (`plugin_api/`) | wartet · Plugin-MVP 3/4 | zu schätzen | Referenztransport, Record/Replay, Scrubbing, Freshness | — |

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
| 2 | derselbe Lauf, fehlende Aufzeichnung | **Fehler** — fällt niemals still ins Netz zurück | | |
| 3 | derselbe Lauf, Socket-Zugriff | technisch **gesperrt**, nicht nur unerwünscht | | |
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

**Entwurf, Runde 1 — noch keine Zeile Produktcode.** Der Zuschnitt hat mehrere
Entscheidungen, die sich billiger widerlegen als umsetzen lassen; deshalb geht
er nach der Entwurfsregel aus `CODEX-REVIEW-AUTOMATION.md` vor der Umsetzung in
die Prüfung.

### Drei Module, und warum nicht eins

| Modul | Inhalt | Warum getrennt |
|---|---|---|
| `testing/http.py` | `HttpRequest`, `HttpResponse`, `Transport` (Protocol), `ReplayTransport`, `RecordingTransport`, `MissingRecording` | Der Transport ist das, was Plugin-Autoren **anfassen**; er darf nicht mit dem Dateiformat verheiratet sein |
| `testing/recordings.py` | Dateiformat, Metadaten, Signatur, Bereinigung, Frist­prüfung | Das Format überlebt einen Bibliothekswechsel; der Transport nicht unbedingt |
| `testing/pytest_plugin.py` | `--real`, `--record`, die Socket-Sperre als autouse-Fixture | Ein `pytest11`-Entry-Point gehört nicht in einen Modulimport — sonst hängt jeder Import an pytest |

`Transport` ist wie `ScenarioRunner` **eine** Methode. Real- und Replay-Betrieb
tauschen nur dieses Objekt; das Plugin bekommt es samt Uhr per Konstruktor.

### Die Signatur wird **nach** dem Bereinigen gebildet

Das ist die Entscheidung, an der ein naiver Entwurf scheitert. Steckt der
Schlüssel als Query-Parameter in der Anfrage und bildet man die Signatur über
die rohe URL, dann trägt jede Aufzeichnung den Schlüssel im Schlüsselfeld —
also genau dort, wo Bereinigung nicht mehr hinkommt, ohne die Zuordnung zu
zerstören. Und ein Beiträger mit einem *anderen* Schlüssel fände seine
Aufzeichnung nie wieder.

Deshalb: **Bereinigen, dann signieren** — beim Aufzeichnen wie beim Abspielen,
über denselben Code. Signaturbestandteile sind Methode, Host, Pfad, sortierte
und bereinigte Query, sowie ein Hash des bereinigten Rumpfs.

### Zwei Tore, und was jedes von beiden liest

| Tor | Liest | Grün, wenn |
|---|---|---|
| `make test-plugin-api` (offline) | `recorded_at`, `scenario_signature` | jede Anfrage getroffen, Metadaten vollständig, Aufzeichnung bereinigt. Alter → **Warnung** über `warnings.warn`, kein Fehlschlag |
| Release-Check | `last_real_ok`, `max_age_days` | ein Real-Lauf hat bestätigt und liegt innerhalb der Frist |

`max_age_days` steht **in der Aufzeichnung**, nicht in einer zentralen Tabelle:
Sie ist eine Eigenschaft dieses Anbieters, und eine zentrale Liste liefe beim
ersten fremden Plugin auseinander. `last_real_ok` schreibt ausschließlich ein
erfolgreicher `--real`-Lauf zurück; die Änderung steht danach im Diff und wird
mitcommittet. Das ist Absicht — so ist im Repository sichtbar, wann zuletzt
wirklich jemand den Anbieter gefragt hat.

**`scenario_signature`** fängt den Fall ab, den sonst niemand bemerkt: Ein
Szenario wird umgeschrieben, die Aufzeichnung bleibt die alte, und der Lauf ist
grün gegen eine Frage, die so nicht mehr gestellt wird.

### Die Socket-Sperre ist eine Sperre, keine Bitte

Eine autouse-Fixture ersetzt `socket.socket` und `socket.create_connection`
durch etwas, das wirft — außer unter `--real`. Der Nachweis ist ein eigener
Test, der einen Verbindungsversuch unternimmt und den Fehler erwartet; ohne ihn
belegt die Sperre nur, dass sie existiert, nicht dass sie greift.

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

### Offene Frage an den Reviewer

Verify `#10` — „Anbieter nicht erreichbar, der normale Build bleibt grün" — ist
im Offline-Betrieb **trivial wahr**, weil dort ohnehin kein Netz existiert. Ein
belastbarer Nachweis prüft die Gegenrichtung: dass der `--real`-Lauf bei einem
nicht erreichbaren Host mit einer deutbaren Meldung fehlschlägt statt mit einem
Stacktrace. Ist das die richtige Lesart der Zeile, oder verlangt sie mehr?
