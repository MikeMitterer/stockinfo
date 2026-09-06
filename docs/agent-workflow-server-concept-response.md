# Stellungnahme zum Review und Vorschlag für den MVP

Stand: 6. September 2026. Bezug:
[Review](agent-workflow-server-concept-review.md) und
[ursprüngliches Konzept](agent-workflow-server-concept.md).
Dies ist eine Gegenposition mit konkreten Entscheidungen, keine implementierte
Serverfunktion. Die beiden Ausgangsdokumente bleiben zum Vergleich erhalten.

## Entscheidung in einem Satz

Den lokalen Workflow-Dienst weiterverfolgen, aber **zuerst die reale
KI-Ausführung nachweisen**, Snapshots präzisieren und den ersten MVP auf einen
vollständigen Zwei-Rollen-Ablauf mit lesbaren Reports und kleiner Websteuerung
begrenzen. Die meisten Befunde tragen; einige vorgeschlagene Mechanismen
versprechen mehr, als sie technisch durchsetzen.

## 1. Antworten auf die acht Befunde

| Nr. | Bewertung | Entscheidung |
|---|---|---|
| 1 · Snapshot | Wesentliche Lücke des Entwurfs | Commit und Tree serverseitig fixieren, eigene Review-Worktrees; Umgebung separat belegen |
| 2 · Ausführung zu spät | Übernehmen | Kleiner Ausführungsnachweis vor Serverausbau; beide Provider prüfen |
| 3 · Revision | Übernehmen | Revision pro fachlichem Objekt, Gesamturteil separat transaktional ableiten |
| 4 · Mensch-Grenze | Präzisierung nötig | Authentisierte Operationen vorsehen; keine Isolation gegen beliebige Shellzugriffe desselben OS-Benutzers behaupten |
| 5 · Konvergenz | Übernehmen | Review-Runden, Laufgrenzen und sichtbarer Halt gehören schon in den MVP |
| 6 · Haltbarkeit | Lücke stimmt, Lösung ergänzen | DB-Backup und versionierter Export mit Wiederherstellungsprobe; kein Autocommit in den aktiven Produktbranch |
| 7 · Kontext | Problem übernehmen, Messmodell korrigieren | Frische Läufe, Fortsetzungsartefakt und optionale Telemetrie; unbekannte Werte bleiben unbekannt |
| 8 · Falsches Finding | Übernehmen | `withdrawn` mit Begründung; ungelöster Streit endet beim Menschen |

### 1 · Was ein Snapshot konkret garantiert

Vorgeschlagener Minimalvertrag:

- `snapshot_id`, Projektidentität, `base_commit`, `commit_sha`, `tree_sha`.
- Der Dienst löst Commit und Tree selbst auf und legt eine eigene Ref unter
  `refs/agentboard/snapshots/<id>` an. Eine ID wird niemals neu belegt.
- Der Verifier arbeitet in einem eigenen detached Worktree am gespeicherten
  Commit. Vergleichsbasis und zu prüfende Anforderungsfassung werden in der
  Übergabe ebenfalls festgehalten.
- Vor und nach dem Lauf prüft der Dienst HEAD und versionierte Dateien gegen
  den gespeicherten Stand. Report und Urteil nennen genau diesen Snapshot.
- Testausgaben, Logs und temporäre Daten gehen in separate Laufverzeichnisse.
  Nicht versionierte benötigte Eingaben müssen im Laufmanifest stehen;
  unbekannte lokale Konfigurationsdateien dürfen nicht still mitwirken.

Eine Ref ist **kein unveränderliches Git-Objekt**: `git update-ref` kann sie
verändern. Unveränderlich referenziert wird hier der gespeicherte Objekt-Hash;
die Ref hält den Stand erreichbar, der Dienst schützt ihre Zuordnung.
Ein detached Worktree ist ebenfalls nicht automatisch schreibgeschützt.
[Git-Refs](https://git-scm.com/docs/git-update-ref),
[Git-Worktrees](https://git-scm.com/docs/git-worktree)

Die Kontrolle vor/nach dem Lauf erkennt verbleibende Drift, beweist aber nicht,
dass ein Agent eine Datei zwischendurch verändert und wiederhergestellt hat.
Für den MVP gilt kooperative Arbeit mit begrenzten Runner-Rechten; stärkere
Isolation benötigt eine tatsächlich durchgesetzte Sandbox. Tests dürfen ihre
eigenen Ausgaben schreiben, aber keine stillen Produktkorrekturen vornehmen.

Auch derselbe Tree garantiert noch nicht dieselbe Laufzeit: Abhängigkeiten,
Toolversionen, Testdaten und externe Dienste können abweichen. Dafür genügt
zunächst ein kleines Laufmanifest mit Setup-/Testbefehlen, Versionen und
Einschränkungen. Keine allgemeine Reproduzierbarkeitsplattform bauen.

Die Diff-Statistik kann der Dienst gegen `base_commit` messen. Fachliche
Änderungen und die Einteilung Produkt/Test/Doku bleiben dagegen teilweise
semantische Bewertungen. Binärdateien werden separat gezählt; fehlende
Zeilenzahlen sind keine Null. Der Gewinn ist echte Messung der messbaren
Größen, keine automatische Wahrheit über den gesamten Scope.

### 2 · Headless vorziehen, aber Erfolg genauer definieren

Die installierten CLIs bieten bereits `codex exec` beziehungsweise
`claude --print`; die offiziellen Dokumentationen beschreiben die
nichtinteraktive Ausführung. Ich habe die lokale Hilfe gelesen, aber noch
keinen Modelllauf oder Runner-Prototyp gestartet.
[Codex](https://learn.chatgpt.com/docs/non-interactive-mode),
[Claude Code](https://code.claude.com/docs/en/headless)

Die offene Frage ist daher nicht nur „kann ein Prozess antworten?“, sondern:
Kann er mit den vorgesehenen Rechten einen echten Test ausführen, MCP benutzen,
einen gültigen Report liefern und ohne Rückfrage geordnet enden?

Ein erfolgreicher Verifier-Test belegt außerdem noch keinen Developer-Runner.
Der Vorabnachweis muss eine kleine Korrektur sowie Prüfung abdecken und die
Rollen anschließend zwischen Claude und Codex tauschen. Funktioniert das,
wird der vom Dienst gestartete CLI-Runner mein bevorzugter MVP-Weg. Falls
nicht, wird vor weiterem Ausbau ausdrücklich über Client-Polling entschieden.

### 3 · Revisionen pro Objekt

`ReviewRun` besitzt eine eigene Revision für Claim und Reportabschluss,
`Ticket` für Priorität und fachlichen Zustand, `Configuration` für Einstellungen.
Zwei Prüfer können ihre unabhängigen Läufe abschließen. Die Ableitung eines
gemeinsamen Übergabeurteils erfolgt in einer kurzen Transaktion auf der
Übergabe; ein tatsächlicher Konflikt wird dort erneut ausgewertet.
Keine Projekt-Gesamtrevision als Pflicht für jeden Heartbeat.

### 4 · Menschliche Abnahme: tatsächliche Grenze nennen

Der ursprüngliche Entwurf fordert bereits authentisierte Admin-Operationen;
„ohne Auth“ ist deshalb keine von ihm festgelegte Betriebsart. Offen blieb
aber zu Recht das Bedrohungsmodell.

Ein Token außerhalb des Projektordners mit Modus `0600` schützt nicht vor
einem unbeschränkten Agentenprozess desselben Benutzers. Für den lokalen MVP:
getrennte Human-/Agent-Zugänge, keine Admin-Zugangsdaten in Agentenprompts,
Umgebungen oder MCP-Konfigurationen, ausschließlich lokal gebundener Dienst.
Jede Abnahme wird mit authentisiertem Zugang und Herkunft protokolliert.

Das schützt die fachliche Schnittstelle vor falschen Rollenoperationen.
Eine harte Grenze gegen gleichberechtigte lokale Prozesse wird erst durch
OS-/Sandbox-Isolation möglich. Ein Ereignis mit Human-Zugang beweist dessen
Verwendung, nicht zweifelsfrei die physische Anwesenheit eines Menschen.

### 5 · Konvergenz sichtbar begrenzen

Vorschlag für den MVP: Nach drei abgeschlossenen Reviews mit
`changes_requested` am selben Ticket keine vierte Runde automatisch starten.
Stattdessen kurze Konsolidierung: verbleibende Findings, was sich tatsächlich
verbessert hat, kleinster nächster Schritt; Mensch entscheidet Fortsetzen,
Verkleinern oder Aufteilen. Die Schwelle ist konfigurierbar.

Kontextfortsetzungen und Transportfehler zählen nicht als erfolgloses Review,
verbrauchen aber Ausführungsbudget. Deshalb zusätzlich Laufzeitgrenze pro Lauf,
Startlimit pro Ticket und Tag sowie höchstens ein automatischer Wiederanlauf
bei einem vorübergehenden technischen Fehler. Ein wiederholter identischer
Berechtigungs-/Konfigurationsfehler wird unmittelbar angehalten.

Kosten und Token nur anzeigen, soweit der Provider sie tatsächlich liefert.
Ein begrenztes Start-/Zeitbudget ist auch ohne zuverlässige Preiszuordnung
durchsetzbar. Keine ausgedachten Eurozahlen bei Abonnement-Anmeldung.

### 6 · Backup und Git-Export lösen verschiedene Probleme

Übernehmen: Reports müssen ohne laufenden Dienst lesbar und versioniert sein.
Aber Commits im aktiven Produktbranch würden Entwicklerzustand, Index und
Snapshot-Linie unnötig beeinflussen. Vorschlag: separates lokales Audit-Repo
für die lesbaren Exporte, mit Commits bei Übergabe, Reviewabschluss und
menschlicher Entscheidung. Kein Commit pro Heartbeat.

DB-Transaktion und Git-Commit sind nicht atomar. Die DB hält deshalb einen
offenen Exportauftrag; dessen Verarbeitung ist wiederholbar. Die Oberfläche
zeigt „Export ausstehend/fehlgeschlagen“, statt eine Sicherung zu behaupten.

Ein Markdown-Export ersetzt keine vollständige Datenbanksicherung.
Zusätzlich konsistente DB-Backups und eine praktische Wiederherstellungsprobe
einplanen. SQLite stellt dafür eine Backup-API bereit.
[SQLite-Backup](https://sqlite.org/backup.html)
Ein lokales Git-Repo schützt ebenfalls nicht vor Ausfall derselben Festplatte;
ein externes Sicherungsziel ist separat zu konfigurieren. „Git ist praktisch
unverlierbar“ wäre dieselbe Überzeichnung, die das Review sonst zurecht kritisiert.

### 7 · Kontextwechsel gehört hinein, 100k ist eine Arbeitshypothese

Der Erfahrungswert von etwa 100k Token kann als bewusst gewähltes
Arbeitsbudget dienen. Er ist kein hier nachgewiesenes, providerübergreifendes
Qualitätsgesetz. Größeres Modellfenster hebt dieses Arbeitsbudget nicht
automatisch an. 60 % für geordnetes Auslaufen und 80 % für Checkpoint-Beginn
sind sinnvolle experimentelle Startwerte, keine garantierten Schutzschwellen.

Die wichtigere Korrektur betrifft die Messung: Kumulierte Abrechnungstoken,
aktuell belegter Kontext und eine Agentenschätzung sind unterschiedliche
Größen. Ein MCP-Server kennt nur die von ihm beobachteten Aufrufe, nicht alle
internen Tool-Runden oder das vollständige Kontextfenster.

Telemetrie enthält deshalb Wert, Quelle und Zeitpunkt; bei fehlender Quelle
`unknown`. Ein sinkender gemeldeter Wert ist ein Hinweis auf einen Reset,
aber ohne Laufzeitereignis kein Beweis für Compaction. Ebenso beweist ein
früher ausgelöstes Zeitlimit keine falsche Kontextmeldung.

**MVP-Vereinfachung:** Jeder Rollenlauf startet frisch mit einem begrenzten
Auftragspaket aus Ticket, Scope, Snapshot, offenen Findings und relevanten
Mustern. Zusätzlich gibt es einen expliziten Fortsetzungsweg. Verfügbare
Kontexttelemetrie kann ihn früh auslösen; andernfalls gelten beobachtbare
Zeit-/Startgrenzen und freiwillige Checkpoints. Ein harter Prozessabbruch
kann keinen nachträglichen geordneten Checkpoint garantieren.

Ein Checkpoint enthält: Rolle, Ticket/Snapshot, erledigte und offene Schritte,
belegte Befunde, ausgeführte Prüfungen, verbleibende Fragen und nächsten
konkreten Schritt. Developer ergänzen ihren gesicherten Zwischencommit;
Verifier verändern den Snapshot nicht und liefern einen unvollständigen
Report ohne Urteil. Erst ein gespeicherter Checkpoint rechtfertigt den Zustand
`checkpointed`; sonst bleibt der Lauf `interrupted`.

Die frische Sitzung muss damit ohne Rückgriff auf den alten Chat fortsetzen
können. Eine notwendige neue Produktentscheidung ist dennoch eine legitime
Rückfrage. Nur bereits verfügbare, im Checkpoint verlorene Information ist
ein Checkpoint-Fehler. Die Wiederaufnahme zählt nicht als neue Review-Runde.

### 8 · Falsche Findings zurücknehmen

`withdrawn` ergänzen, mit Begründung und Gegenbeleg des Verifiers. In Statistiken
als zurückgenommener Befund ausweisen, nicht als behobenen Developer-Fehler.
Einmal eine gezielte Gegenprobe bei `disputed`; bleibt der Streit bestehen,
entscheidet der Mensch. Keine unendliche Debatte und keine zusätzliche
Schiedsrichter-KI als MVP-Voraussetzung.

## 2. Der konkrete MVP

**Ergebnis:** Ich starte im Web ein kleines Ticket. Die konfigurierte
Developer-KI bearbeitet es; die Verifier-KI prüft einen fixierten Stand. Ich
sehe Fehlerbericht, Korrektur und Freigabe. Derselbe Ablauf funktioniert mit
vertauschten Providern und übersteht einen unterbrochenen Lauf.

### Vorabnachweis, bevor der Dienst ausgebaut wird

Ein begrenztes Experiment in einem eigenen Testrepo, ohne Produktänderungen
in StockInfo. Testbefund absichtlich klein und eindeutig.

1. Claude und Codex jeweils headless mit vorgesehenen Zugriffsrechten starten.
2. Verifier liest einen fixierten Stand, führt einen echten Test aus und
   liefert einen strukturell gültigen Problem-Report.
3. Developer korrigiert, commitet und liefert die geforderte Übergabe.
4. Rollen tauschen und den gleichen Aufgabentyp erneut durchlaufen.
5. MCP-Aufruf, fehlende Berechtigung, Timeout und frische Fortsetzung prüfen.

Zeitlich auf einen kurzen Versuch begrenzen, beispielsweise einen halben
Arbeitstag. Das ist eine Time-Box für Erkenntnisgewinn, keine Lieferzusage.
Bei Scheitern benennen wir die konkrete fehlende Fähigkeit und entscheiden
über Polling oder einen kleineren Betriebsumfang. Kein wiederholtes Ausbauen
des Experiments zu einer eigenen Plattform.

### Umfang des ersten nutzbaren Dienstes

| Teil | Gehört in den MVP |
|---|---|
| Betrieb | Ein lokaler Dienst, ein Benutzer, ein Git-Projekt |
| Rollen | Genau Developer und Verifier, Claude/Codex vertauschbar |
| Ausführung | Zwei dünne CLI-Anbindungen, derselbe Rollenvertrag; frischer Lauf pro Auftrag |
| Zustand | SQLite, ein aktiver Produkt-Schreiber, Claims und wiederholbare Abschlüsse |
| Prüfinhalt | Fixierter Commit/Tree, ein eigener Review-Worktree, eigenes Test-Ausgabeverzeichnis |
| MCP | Zustand/Auftrag lesen, Claim, Übergabe, Reviewabschluss, Checkpoint und Laufstatus melden |
| Reports | Pflichtbericht, Finding-Status einschließlich withdrawn, Direktlink, Markdown-Download |
| Lernen | Kleines kuratiertes Musterregister, beim nächsten passenden Auftrag mitgeliefert |
| Web | Eine Projektübersicht mit Ticket-/Reportdetail und kleiner Konfigurationsansicht |
| Steuerung | Start, Pause, Abbruch, einmaliger Lauf, konfigurierbares Intervall; gleiche Werte per CLI |
| Grenzen | Rundenschwelle, Laufzeit-/Startlimit, ehrliche Kontextanzeige und Fortsetzung |
| Haltbarkeit | Versionierter Reportexport, DB-Backup, sichtbare Sicherungsfehler |

Der zentrale Timer startet die nachgewiesenen CLI-Runner. Die bisherigen
/loop- und In-Context-Scheduler bleiben im Datei-Setup verfügbar, laufen aber
nicht zusätzlich für dieselbe Rolle im Servermodus. Für den MVP keine drei
gleichberechtigten Betriebsarten implementieren.

CLI und Web benötigen nur dieselben wenigen Kernoperationen. Die Oberfläche
muss Rollen, Status, letztes echtes Ereignis, nächsten Lauf und offene Findings
zeigen. Sie braucht noch keine frei gestaltbare Workflow-Canvas, Modellrangliste
oder komplexe Reporting-Analyse.

Eine dritte/vierte KI, parallele Pflichtprüfer, mehrere Projekte und Remote-
Betrieb sind Anschlussstufen. Dafür stabile IDs und getrennte ReviewRun-
Revisionen vorsehen; deren komplette Ausführung noch nicht bauen.

### Der Ablauf, an dem wir den MVP abnehmen

1. Kleines Ticket mit beobachtbarem Erfolg und entscheidendem Gegenfall anlegen.
2. Developer übergibt, Dienst fixiert Snapshot und misst den Diff.
3. Verifier findet den vorbereiteten Fehler; Report ist im Web sofort lesbar.
4. Developer korrigiert mit Bezug auf Finding-ID; Verifier bestätigt den neuen
   Snapshot. Alte Beobachtung bleibt in der Historie erhalten.
5. Menschliche Abnahme erfolgt separat. Ein Agentenzugang kann sie nicht
   über eine normale API-/MCP-Operation setzen.
6. Rollenwechsel und gleicher Ablauf in umgekehrter Zuordnung.
7. Doppelter Tick erzeugt keinen zweiten Lauf. Abbruch erzeugt kein Approved.
8. Erzwungener Checkpoint lässt sich in einer frischen Sitzung fortsetzen.
9. Drei fehlgeschlagene Reviews halten die Kette sichtbar an.
10. Export bleibt ohne Dienst lesbar; ein Backup lässt sich wiederherstellen.

**Baufolge innerhalb dieses Umfangs:** zuerst CLI-Auftrag → Snapshot →
Verifier → Report, dann Korrektur und Gegenprüfung, anschließend die kleine
Webansicht und Timersteuerung. Die Bausteine werden an diesem selben Ticket
ergänzt. Der Prototyp darf anfangs hässlich sein; der Beweisweg muss durchlaufen.

## 3. Nicht zu viele weitere Konzeptrunden

Mein Vorschlag: **höchstens zwei weitere Dokumentrunden** vor dem
Ausführungsnachweis, keine erneute Komplettüberarbeitung beider Konzepte.

1. Claude prüft diese Stellungnahme nur auf konkrete Widersprüche,
   fehlende Pflichtanforderungen und zu großen MVP-Scope. Ergebnis pro Punkt:
   einverstanden oder konkreter Gegenfall samt kleinerer Alternative.
2. Eine kurze gemeinsame Entscheidungsvorlage konsolidiert Ziel, MVP-Grenze,
   Snapshot-Vertrag, Ausführungsweg, Grenzen und Abnahmelauf. Offene
   Implementierungsdetails werden im Vorabnachweis entschieden, nicht durch
   weitere spekulative Architekturprosa.

Ein neuer konkreter Blocker darf die Umsetzung stoppen; Stilpräferenzen und
zukünftige Erweiterungsmöglichkeiten verlängern die Konzeptrunde nicht.
Der nächste Erkenntnisgewinn soll aus einem realen Lauf kommen.
