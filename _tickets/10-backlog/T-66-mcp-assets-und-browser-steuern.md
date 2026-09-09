# T-66 · MVP-Konzept: Assets und Charts über eine KI bedienen

StockInfo soll sich **aus dem KI-Chat bedienen** lassen: vorhandene Assets
finden, aufnehmen, manuelle Detailwerte ändern, löschen und deren Charts
gezielt öffnen oder schließen. Ein eigenständiger MCP-Server übersetzt diese
Werkzeuge in StockInfo-Aufrufe; die Geschäftsregeln bleiben im Backend.

**MVP-Beispiel:** „Nimm SAP.DE auf und zeige den Chart.“ Der MCP-Prozess nimmt
das Asset über REST auf, öffnet bei Bedarf eine eigene StockInfo-Ansicht und
wartet auf deren Rückmeldung. „Schließe den Chart“ schließt nur das Diagramm
in dieser verbundenen Ansicht.

**Stand:** Konzept von beiden KI geprüft; Claude hat die Fassung `e4b793e`
in Runde 2 freigegeben. Codex hat die Review-Auflösung nachgeprüft. Keine
offenen Konzeptbefunde, keine dritte Runde. Codex ist Autor der Redaktion;
seine Eigenprüfung wird nicht als zusätzliche unabhängige Abnahme bezeichnet.

**Für Mike:** TypeScript ist als Sprache verbindlich festgelegt. Die Vorlage
ist bereit zur Entscheidung über lokalen MVP, stdio und WebSocket zum
WebClient. Es wurde kein Produktcode
geschrieben. Eine Umsetzung braucht einen eigenen Auftrag.

## Auftrag und Scope dieses Tickets

Mikes Rückmeldungen vom 2026-09-08:

- „Ziel bei T-66 ist erstmal ein MVP“
- „Könnt ihr beide reviewen?“
- „Ich möchte erstmal ein Tickt bzw das das Konzept ordentlich steht und beide KI das verifiziert haben“
- „Genau - bei Claude läuft auch wieder der Loop der alle 5 min das Status.md überprüft“
- „Als kommunikationsweg zum WebClient steht SSM oder WebSockets zur Verfügung - kläre auch mit Claude ab was in dem Fall besser passt“
- „Die Anzahl der Iterationen über das Ticket T-66 sollte sowieso begrenzt sein - also, nicht ausufern!“
- „Die Entscheidung muss für die technisch bessere Lösung fallen! und nicht deshalb weil bestimmte Guards erweitert werden müssen“
- „Verankere im Ticket noch dass der MCP-Server mit Typescript gebaut wird“

### Das Ziel ist Erkenntnis, nicht nur die Funktion

Mike am 2026-09-08: „Hauptargument ist, dass es mich interessiert wie der MCP
in Verbindung mit StockInfo funktioniert."

**Das ist der tragende Grund für dieses Ticket** und nicht nur seine
Begründung. Es ändert, woran der Wert hängt:

- **Aufwandsargumente gegen MCP-spezifische Teile sind kein Ablehnungsgrund.**
  Ein Kommandozeilenwerkzeug gegen dieselbe REST-API wäre billiger zu bauen,
  mit `subprocess` statt echtem Protokolllauf zu prüfen und zusätzlich für
  Mensch, Skripte und Cron nutzbar. Es beantwortet Mikes Frage nicht. Diese
  Alternative ist geprüft und verworfen; sie wird nicht erneut vorgeschlagen.
- **Prüfnachweis `#1` ist Kern, nicht Kür.** Der echte Lauf
  MCP-Client → Server → REST → frische Datenbank ist der teuerste Beleg des
  ersten Abschnitts und unter diesem Ziel zugleich der wertvollste: Er *ist*
  die Antwort auf die Frage.
- **Der lehrreiche Teil ist Abschnitt 1.** Werkzeugdeklaration, Typisierung,
  Annotationen wie „destruktiv", die Fehlersemantik, die beim Modell ankommt,
  und das Verhalten bei mehrdeutigen Treffern — das ist MCP. Abschnitt 2 und 3
  sind WebSocket-, Bindungs- und Guard-Arbeit im Backend; dort liegt der
  Großteil von Aufwand und Risiko, und MCP ist daran nur der Auslöser.

Daraus folgt eine **bewusste Zäsur nach Abschnitt 1**: Danach ist die Frage
beantwortet, und die Fortsetzung ist eine eigene Entscheidung von Mike, keine
Selbstverständlichkeit.

**Höchstens zwei Konzept-Reviewrunden insgesamt.** Danach geht das Ergebnis
mit gegebenenfalls offenen Restpunkten an Mike. Keine dritte Schleife und
kein zusätzlicher Funktionsumfang für Detailpolitur.

„SSM“ wird hier als **SSE / Server-Sent Events** verstanden; diese Annahme
wurde Mike im Chat genannt. Transportentscheidung siehe unten.

Der frühere Auftrag „Du kannst die loop nochmal starten und T-66 durchgehen“
wird durch den aktuellen Auftrag eingegrenzt: Konzeptarbeit, noch kein Code.

**Scope-Vertrag:** Ein Ergebnis — ein geprüftes MVP-Konzept. Zwei fachliche
Arbeiten: Zuschnitt am Bestand und Review-Auflösung. **0 Produktdateien**,
höchstens **2 Ticket-/Statusdateien**, **600 Diff-Zeilen** ohne bereits
vorhandenen Status-Verlauf. Kein Scaffold, keine Installation, keine neuen
Abhängigkeiten und keine Änderung von Arbeitsdaten.

## MVP-Vorschlag zur späteren Entscheidung

| Ansatz | Nutzen und Grenze | Bewertung |
|---|---|---|
| Lokaler MCP, Datenwerkzeuge und eine verbundene Ansicht | Der Beispielablauf ist vollständig; kein entfernter Launcher nötig. | **Empfohlen** |
| Nur Datenwerkzeuge | Kleinster Umfang; Charts lassen sich noch nicht steuern. | Kleinerer möglicher Zuschnitt |
| Lokaler und entfernter MCP, mehrere Zielgeräte | Bisheriger Gesamtentwurf; zusätzlicher Zugriffsschutz und lokaler Launcher für entfernte Nutzung. | Spätere Ausbaustufe |

Für den vorgeschlagenen MVP laufen **KI-Client, MCP, StockInfo und Browser
auf demselben Mac**. Ein MCP-Prozess steuert höchstens eine ausdrücklich
verbundene Ansicht. Andere Tabs bleiben manuell bedienbar und reagieren nicht
auf dessen Chartbefehle. Mehrere gleichzeitig steuernde MCP-Prozesse und
mehrere Backend-Worker werden nicht zugesagt.

Später: entfernter MCP über Streamable HTTP, interner Serverbetrieb, Launcher
auf dem Benutzergerät, mehrere steuerbare Ansichten und allgemeine
Push-Synchronisierung von UI-/Hintergrundänderungen. Diese Punkte sind nicht
gestrichen, sondern außerhalb dieses MVP. Der ursprüngliche Gesamtentwurf
bleibt über Git nachvollziehbar.

## MCP-Subprojekt und Datenwerkzeuge

`mcp/` ist unabhängig vom Python-Backend startbar und erhält eigene
Abhängigkeiten, Tests, Startanleitung und Konfiguration. **Verbindliche
Sprachentscheidung von Mike, 2026-09-08: Der MCP-Server wird in TypeScript
gebaut.** TypeScript passt zur vorhandenen Dashboard-Werkzeugkette.
Vorgesehen sind das offizielle MCP-SDK und zunächst stdio. Bibliotheks- und
Laufzeitversion werden im späteren Bauticket fixiert.

Der KI-Client startet den MCP-Prozess; stdout enthält ausschließlich
MCP-Nachrichten, Logs gehen nach stderr.
[Protokollgrundlage: MCP-Transporte](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports).

Der MCP-Server importiert keine Backend-Interna und greift nicht auf SQLite zu.
REST-Zugriffe liegen gebündelt, beispielsweise in `mcp/src/clients/stockinfo/`,
Werkzeugdefinitionen getrennt in `mcp/src/tools/`. Kein generisches Werkzeug
für beliebige URLs, REST-Methoden, Shell-Befehle oder Browserklicks.

Backend-/Dashboard-Adresse und Steuerungszugang werden beim Start konfiguriert.
Im lokalen MVP sind nur Loopback-Ziele zulässig; Werkzeugparameter dürfen
keinen anderen Host einsetzen. Zugangswerte stehen weder in Antworten noch
Logs. Setup-Beispiele verwenden Platzhalter statt echter Geheimnisse.

| Werkzeugvorschlag | Eingang und Wirkung | REST / Grenze |
|---|---|---|
| `list_assets` | Bestand lesen; optionale Namens-/Symbolsuche filtert diesen Bestand. | `GET /instruments`, keine weltweite Wertpapiersuche. |
| `get_asset` | Genau eine `listing_id` samt Detailwerten lesen. | Auswahl aus `GET /instruments`; kein neuer Leseendpunkt nötig. |
| `add_asset` | Einen rohen `identifier` aufnehmen. | `POST /instruments/intake`, keine eigene Symbol-/MIC-Auflösung. |
| `get_editable_fields` | Feldkatalog und Zielasset lesen. | `GET /fields` plus Asset; Definitionen/Anwendbarkeit/Werte liefern. |
| `set_asset_details` | `listing_id`, Feldnamen, Werte und ggf. Währung. | Bestehender `PATCH /instruments/by-id/{listing_id}/details`. |
| `delete_asset` | Genau eine `listing_id` samt Historie löschen. | Kleiner neuer DELETE-Weg per Listing-ID erforderlich. |
| `open_chart` | `listing_id`, optional vorhandener Zeitraum; Ansicht öffnen/verwenden. | Allgemeiner StockInfo-UI-Auftrag, kein Quote-GET als Ersatz. |
| `close_chart` | Chart in der verbundenen Ansicht schließen. | Gleicher UI-Auftragsweg; Browser/Asset bleiben erhalten. |

`listing_id` bleibt opak. Mehrere Suchtreffer ergeben Kandidaten und keine
Mutation. Eine gelöschte ID wird nicht durch ein anderes Asset gleichen
Namens ersetzt. Der neue DELETE-Weg muss die Auswahl und Löschung im Backend
eindeutig halten; eine vorgeschaltete Suche mit anschließendem Symbol-DELETE
würde die ID-Zusage nicht erfüllen.

„Bearbeiten“ meint ausschließlich die **deklarierten manuellen Detailwerte**.
Identität, Börse, Providerwerte und frei editierbarer Name sind nicht enthalten.
`null` entfernt nur den benannten manuellen Wert; ausgelassene Felder bleiben.
Das Backend prüft Definition, Anwendbarkeit und Bearbeitbarkeit. MCP zeigt den
wirksamen und manuellen Wert sowie eine Providerüberlagerung (`shadowed`).
Es führt keinen zweiten editierbaren Feldkatalog.

Der Legacy-Override-PUT ersetzt den vollständigen Satz. Er wird nicht als
partielles MCP-Update verwendet, damit andere Werte nicht versehentlich
verschwinden. Das Löschwerkzeug wird als destruktiv beschrieben/annotiert.
Die konkrete Beauftragung erfolgt im KI-Client; die Annotation allein ist
keine Zugriffskontrolle und garantiert keinen Dialog in jedem Client.

## WebClient: SSE plus REST oder WebSocket?

Beide Varianten erfüllen den fachlichen Ablauf. Im Bestand gibt es noch
keinen SSE-, WebSocket- oder Sitzungs-/ACK-Kanal. Ein bereits vorhandener
Transport gibt daher nicht den Ausschlag.

| Kriterium | SSE plus REST-Rückmeldung | WebSocket |
|---|---|---|
| Chartauftrag zum Browser | Ereignis im SSE-Strom | Nachricht im Socket |
| Bereitschaft, ACK, Editorstatus zurück | Zusätzlicher REST-Aufruf | Nachricht auf derselben Verbindung |
| Browserunterstützung | Native `EventSource`-API; automatischer Wiederaufbau | Native `WebSocket`-API; Wiederaufbau durch Anwendung |
| Bindung und Zugriff | SSE-Stream und ACK-Route müssen dieselbe Ansicht prüfen | Nach Anmeldung an diese Verbindung gebunden; Auftrags-ID weiter nötig |
| Zugang ohne URL-Geheimnis | Native EventSource hat keinen frei setzbaren Authorization-Header; Cookie- oder Fetch-Streaming-Lösung nötig | Anmeldung als erste Nachricht möglich; davor keine Aufträge/Daten |
| Betrieb | Gewöhnlicher HTTP-Strom; Buffering/Timeouts beachten | Upgrade-Unterstützung nötig, besonders später hinter Proxy |
| Bestehender Migrationsriegel | Zentraler HTTP-Guard erfasst Stream-Anmeldung, Auftrag und ACK | HTTP-Middleware wird umgangen; zentraler ASGI-Umbau mit Regression nötig |
| Fachliche Passung | Benachrichtigungskanal plus separater Rückkanal | **Empfohlen:** bidirektionale Steuerung auf einer gebundenen Verbindung |

**Beide KI empfehlen nach Gegenprüfung WebSocket.** Der Ablauf ist eine
bidirektionale Steuerung: Auftrag, Bereitschaft, Bestätigung und Editorstatus
gehören zu derselben verbundenen Ansicht. WebSocket bildet diese Beziehung
direkt ab. Anmeldung als erste Nachricht bindet die Verbindung, ohne für den
Browser zusätzliche ACK-/Anmelde-REST-Routen oder Sitzungscookies einzuführen.
Das ist ein Strukturvorteil für diesen Ablauf, kein Geschwindigkeitsargument.
Fachliche ACKs und Zeitgrenzen bleiben trotzdem erforderlich.

SSE plus REST ist technisch tragfähig und für reine Benachrichtigungen gut
geeignet. Hier müssten Stream und Rückkanal zusätzlich zusammengeführt und
abgesichert werden. Der geringere Umbauaufwand am heutigen HTTP-Guard wiegt
nach Mikes Vorgabe nicht schwerer als die Passung zur bidirektionalen Steuerung.
Claude hat diese fachliche Abwägung in Runde 2 bestätigt und seine frühere
SSE-Empfehlung zurückgezogen. Es entsteht nur ein Transport ohne vorsorglichen
Abstraktionslayer.

**Konsequenz ausdrücklich im Scope:** `app/main.py:migration_guard` erfasst
heute nur HTTP; beide KI haben das am installierten Middleware-Code geprüft.
Er wird für die spätere Umsetzung zentral auf ASGI-Ebene geführt und verwendet
dieselbe Gate-/Allowlist-Entscheidung für HTTP und WebSocket. Keine zweite
Migrationsregel in der Socket-Route. HTTP behält seine bisherigen Antworten;
eine gesperrte WebSocket-Anmeldung wird vor Nutzdaten abgewiesen. Lebenszyklus-
Scopes bleiben unberührt. Neue UI-Aufträge und Datenmutationen kommen weiterhin
über REST hinter diesem Guard; Browsernachrichten melden nur Bereitschaft und
Ausführung, sie eröffnen keinen zweiten Mutationsweg.

Grundlagen: [MDN SSE](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events),
[EventSource-Konstruktor](https://developer.mozilla.org/en-US/docs/Web/API/EventSource/EventSource),
[MDN WebSocket](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket),
[FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/).
Die Empfehlung ist eine Bewertung für StockInfo, keine Vorgabe dieser Quellen.
MCP-stdio und WebClient-Transport sind getrennte Verbindungen.

## Verbindliche Fachregeln unabhängig vom Transport

**Eine gezielt verbundene Ansicht.** StockInfo erhält eine allgemeine
UI-Steuerung für Anmeldung, Auftrag und Rückmeldung, ohne MCP-Werkzeugnamen
im Backend. MCP sendet UI-Aufträge über REST. Der WebClient empfängt sie über
WebSocket und meldet Bereitschaft, Ausführung und Editorstatus darüber zurück.

Der Steuerungskanal ist standardmäßig deaktiviert. Vorgeschlagen ist für den
lokalen MVP ein explizit eingerichteter gemeinsamer Zugangswert zwischen MCP
und Backend. Nur dieser darf eine Bindung erstellen und Aufträge senden.
Die Browseransicht bekommt stattdessen eine 60 Sekunden gültige Einmalkennung
im URL-Fragment. Lesen und Entfernen liegen als exportierte Helfer in
`useHashTab.ts`, neben den bestehenden URL-Helfern; keine zweite Hash-Zerlegung
in einer Komponente. Die Übernahme erfolgt vor der normalen Hash-Normalisierung.

Der Browser meldet sich als erste WebSocket-Nachricht mit der Einmalkennung an.
Bis zur erfolgreichen Anmeldung gibt es keine Nutzdaten oder Aufträge; fehlt
sie nach fünf Sekunden, wird die Verbindung geschlossen. Die Kennung wird
atomar verbraucht und die Ansicht an genau diesen Socket gebunden. Es braucht
keine Sitzungscookie und kein Query-Geheimnis. Der MCP-Steuerungs-POST verwendet
weiter seinen eigenen Zugang. Ein Ansichtsbezeichner allein autorisiert nichts.

MCP startet nur die konfigurierte Dashboard-Adresse über den lokalen
Betriebssystemaufruf mit getrennten Argumenten, ohne Shell. Es übernimmt keine
vorhandene manuelle Registerkarte. Browser-Origin, Einmalkennung, Bindung und
Auftragszuordnung werden serverseitig geprüft. Die Browserverbindung erfordert
den konfigurierten Origin. Ohne passende Bindung gibt es keine Befehle.
Eine gebrauchte/abgelaufene Kennung oder zweite Übernahme wird abgewiesen.
CORS allein ersetzt diese Prüfungen nicht. Kein langlebiger MCP-Zugang gelangt
zum Browser; Verbindungskennungen werden nicht protokolliert.

**Bestätigte Ausführung.** Browserstart allein ist kein Erfolg. Der WebClient
meldet Bereitschaft; `open_chart` wartet insgesamt höchstens 30 Sekunden auf
Verbindung und passende Ausführungsbestätigung. Er nutzt bestehende
Chartauswahl, Zeiträume und Schließfunktion. „Ausgeführt“ heißt, dass das
richtige Chart-Dock geöffnet/geschlossen ist. Leere Kurse oder Ladefehler
bleiben gesondert sichtbar und werden nicht als geladene Kursdaten bezeichnet.

Auftragszustände: `accepted`, `executed`, `failed`, `timed_out`.
Eine eindeutige Auftragskennung und die gebundene Ansicht ordnen ACKs zu.
Nach Timeout wird kein späteres ACK zum rechtzeitigen Erfolg umgedeutet.
Timeout bedeutet fehlende Bestätigung, nicht den Beweis einer Nichtausführung.

**Begrenzte Laufzeit statt Queue-System.** Ein ausstehender UI-Auftrag,
flüchtige Bindung, keine dauerhafte Queue und kein Replay. Weitere gleichzeitige
Aufträge werden als beschäftigt abgewiesen. Neustart oder Verbindungsabbruch
verwerfen die Bindung; erneutes Verbinden erfordert eine neue Einmalkennung.
Der Client lädt dann aktuelle Daten, spielt aber keine alten Befehle ab.
Ein neuer Socket mit verbrauchter Kennung wird abgewiesen; Wiederaufbau der
Verbindung ist kein fachliches Befehls-Replay.
Ohne verbundene Ansicht meldet `close_chart` „keine verbundene Ansicht“ und
startet keinen Browser. Die bestehende Ansicht wird durch Neuverbinden nicht
automatisch zur zweiten steuerbaren Ansicht.

**Speicherung und Darstellung getrennt.** Ein aufgenommenes Asset bleibt
gespeichert, wenn danach der Browserstart scheitert. Werkzeugantworten nennen
Schreib- und UI-Ergebnis getrennt. Bei unklarem REST-Schreibausgang gibt es
keinen automatischen Retry; zuerst wird durch Lesen abgeglichen.

Nach MCP-Mutationen wird die verbundene Ansicht zum Neuladen aufgefordert.
Ohne Verbindung genügt das REST-Ergebnis. Offene Eingaben werden nicht still
überschrieben: Neuladen wird bis Speichern/Abbrechen verschoben und sichtbar
als ausstehend gemeldet. Der aktuelle Neuladeauftrag erhält dabei sofort
`failed` mit dem Grund „Eingabe offen“; nur ein zusammengefasstes lokales
„Daten neu laden“-Flag bleibt, keine wartende Befehlsqueue. Chartwechsel dürfen mit „Eingabe offen“
abgelehnt werden. Benachrichtigungen über andere Tabs und Hintergrundläufe
bleiben spätere Ausbaustufe. Deren manuelle Bedienung bleibt erhalten.

## Bestandsabgleich und spätere Lieferabschnitte

Codex inventarisierte am 2026-09-08 alle Router-Funktionen mit Python-AST und
las die UI-Aufrufwege. `mcp/` existiert noch nicht.

| Ort | Vorhanden / konkrete Lücke |
|---|---|
| `app/routers/instruments.py`, `intake_service.py` | Aufnahme und Börsenabdeckung existieren. |
| `app/routers/dashboard.py`, `fields.py` | Liste, Katalog und Detail-PATCH existieren; DELETE nur per ISIN/Symbol. |
| `quote_cache.py:set_detail_overrides` | Prüft kompletten Patch vor atomarem Schreiben. |
| `useOverrides.ts` | Bestätigt unterschiedliche PUT-/PATCH-Semantik. |
| `AppDashboard.vue` | `select`, `onRangeChange`, `closeChart`; bisher nur lokale UI-Aktionen. |
| `useHashTab.ts` | Besitzt Hash-Struktur; Bindung muss vor Normalisierung übernommen werden. |
| Router-Inventar, `useInstruments.ts` | Kein Sitzungs-/ACK-Kanal; Neuladen über explizite Aktionen. |
| `app/main.py`, `dashboard/api-prefixes.ts`, `vite.config.ts` | Zentraler HTTP-Guard wird ASGI-Guard; bei Entwicklung braucht der neue Socket-Pfad Proxy-Weiterleitung mit Upgrade. |

Spätere Umsetzung in drei aufeinander aufbauenden Abschnitten, **jetzt keine
Bautickets und kein Code**:

1. MCP→REST mit Datenwerkzeugen und eindeutigem Löschweg; erster echter
   Protokolllauf bis frischer Datenbank.
2. Eine lokale Ansicht, gemeinsamer HTTP-/WebSocket-Guard, Zugriff/Bindung und
   Chart-Auftrag mit ACK/Timeout; bisherige HTTP-Absicherung gegenprüfen.
3. Aktualisierung, Schutz offener Eingaben und vollständiger Browsernachweis.

**Nach Abschnitt 1 wird angehalten und Mike entschieden.** Dort ist das
Erkenntnisziel oben erreicht; Abschnitt 2 und 3 tragen den Großteil von
Aufwand und Risiko und lehren über MCP wenig. Die Fortsetzung ist eine eigene
Portfolio-Entscheidung, kein automatischer Anschluss.

Jeder Abschnitt braucht vor Implementierung einen eigenen Datei-/Diff-Scope.
Die alte Schätzung von 6–10 Tagen betraf den größeren Gesamtentwurf und ist
kein Budget dieses Konzepts. Nicht enthalten: Restore, Migration, DB-Umbau,
neue Benutzerverwaltung oder Umbau der Geschäftslogik. Existierende
Betriebsriegel müssen auch neue Daten-/UI-Wege sperren; die gemeinsame
ASGI-Prüfung und ihre HTTP-Regression sind Pflichtumfang, kein späterer Zusatz.

## Verifikation des Konzepts und spätere Abnahme

| Konzeptprüfung | Nachweis | Codex | Claude |
|---|---|---|---|
| K1 MVP / spätere Ausbaustufen | Lokaler Beispielablauf, Remote ausdrücklich später. | Eigenprüfung erfolgt | Runde 1 bestätigt |
| K2 REST / eindeutige Identität | Inventar, Wiederverwendung, DELETE-Lücke und zentraler Hash-Leser. | geprüft; B2-Auflösung nachgeprüft | Runde 2 bestätigt |
| K3 WebClient-Transport | Bidirektionaler Ablauf spricht für WebSocket, gemeinsamer ASGI-Guard im Scope. | WebSocket empfohlen; Endprüfung erfolgt | Runde 2: WebSocket bestätigt |
| K4 Fehler / prüfbare Abnahme | ACK, Schreibausgang, Editor, Neustart und Betriebsriegel. | Konzeptprüfung, kein Laufzeitbeleg | Runde 1 bestätigt |

Runde 1 (`eb628f9`): Claude bestätigt den Bestand und empfiehlt SSE wegen der
HTTP-Middleware; Codex prüfte diesen Befund nach. Mike priorisiert anschließend
ausdrücklich die technische Passung gegenüber dem Guard-Umbauaufwand. Die
aktuelle Empfehlung lautet deshalb WebSocket mit zentraler ASGI-Absicherung.
B2 verortet den Bindungsleser in `useHashTab.ts`. Runde 2 (`e4b793e`, Review
`e5e0b20`) bestätigt beide Auflösungen ohne neue Befunde. Für die Umsetzung:
WebSocket-Scopes tragen kein HTTP-`method`; im Pending-Zustand sind deren
Handshakes gesperrt, während die bestehende HTTP-Allowlist erhalten bleibt.
Die Analyse der anfänglichen Guard-Überbewertung steht in
[Review-Lehre R-01](../.agents/CLAUDE-LESSONS.md#r-01--integrationsaufwand-verdrängt-die-fachliche-architekturentscheidung).

Keine dieser Angaben behauptet bestandene Produkt- oder UI-Tests. Die einzige
geplante Produkt-Verify-Matrix folgt; alle Läufe sind offen:

Regression des unveränderten Bestands: 46 Aufnahme-/Identitätstests sowie
`make test-dashboard` mit ESLint und 374 UI-Tests grün. Diese Läufe bestätigen
keinen MCP-Code; es gab keinen neuen Browserlauf. UI-Log: `/tmp/t66-concept-ui.log`.

| # | Späterer Lauf / Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | Lokal: echter MCP-Client startet Prozess, listet Werkzeuge, liest frischen Bestand. **Kern des Erkenntnisziels, nicht ersetzbar durch Unit-Tests.** | Protokoll→REST→DB; stdout ohne Logs, keine Backend-/DB-Imports. Werkzeugliste, Typen, Annotationen und Fehlerdarstellung im Client festhalten. | ➖ |
| 2 | MIC/Suffix/ISIN aufnehmen, nicht abgedeckte Börse und mehrdeutige Suche versuchen. | Core-Regeln wie UI; Fehler verändert keinen falschen Datensatz. | ➖ |
| 3 | Detail setzen/zurücksetzen, gesperrtes Feld versuchen; eine von zwei gleichnamigen Zeilen per ID löschen. | Nur benannte Felder/Zeile geändert; Providerüberlagerung korrekt gemeldet. | ➖ |
| 4 | Ohne Verbindung Chart öffnen; Browserstart scheitern lassen. | Eigene lokale Ansicht, Bereitschaft/Erfolg nur mit ACK; keine Scheinerfolge. | ➖ |
| 5 | Verbundene und manuelle Ansicht: Chart öffnen/Zeitraum wechseln/schließen. | Nur Zielansicht reagiert; leere/gestörte Kursdaten sichtbar. | ➖ |
| 6 | MCP-Mutation bei offener Eingabe, dann Speichern/Abbrechen. | Gespeichert, UI zunächst ausstehend; Eingabe nicht still überschrieben. | ➖ |
| 7 | Trennung, verspätetes/fremdes ACK, Prozessneustart, unklarer Schreibausgang. | Timeout/Fehler korrekt, kein Replay oder blinder Schreib-Retry. | ➖ |
| 8 | Falscher Zugang/Origin, verbrauchte Bindung, aktiver Betriebsriegel; HTTP-/WebSocket-Anmeldung vergleichen. | Beide gesperrt; alte HTTP-Antworten erhalten, kein fremder Zugriff oder Geheimnisweitergabe. | ➖ |
| 9 | DE/EN, Desktop/Mobil: manuelle Asset-/Chart-Bedienung mit und ohne MCP. | Bestehende Bedienung erhalten, Meldungen verständlich, kein Überlauf. | ➖ |

Isolierte Testdaten und normale Framework-Fakes an Außengrenzen; mindestens
ein echter MCP-Client→Server→REST→frische-DB-Lauf und ein Browserlauf sind
Pflicht. Negative Mutanten prüfen falsche Ziel-ID, übersprungene ACK-Prüfung
und überschriebenen Editorzustand. Unit-Tests ersetzen keine Browserbelege.
Remote-Läufe sind außerhalb des MVP und werden nicht als bestanden geführt.
