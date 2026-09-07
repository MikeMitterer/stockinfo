# VORSCHLAG · Agenten-Workflow: konsolidierte Fassung zur Prüfung

> **Das hier ist keine Entscheidungsdatei.** Es ist der Vorschlag, wie
> `agent-workflow-server-decisions.md` nach Konzeptreview 3 und Codex'
> Stellungnahme aussehen *würde*. Nichts darin ist von Mike freigegeben.
> Die gültige Fassung bleibt `agent-workflow-server-decisions.md`, unverändert.
> Erst Mikes Freigabe — ganz, teilweise oder gar nicht — macht daraus
> Entscheidungen; dann ersetzt diese Datei die andere und verschwindet.
>
> Änderungen gegenüber der gültigen Fassung stehen in 0b, 0c, im
> Mindestvertrag von Abschnitt 0, in 1a, in C, in M1 und in Abschnitt 5.
> Die Zuordnung zu den Befunden steht in
> [`agent-workflow-server-concept-review-3-reply.md`](agent-workflow-server-concept-review-3-reply.md).

Stand: 7. September 2026, konsolidierter Vorschlag nach Konzeptreview 3 und
Codex' Stellungnahme dazu. Kanban-Lebenszyklus, alternative Ticketquellen und
dokumentbasierte Prüfgegenstände sind eingearbeitet; die dazu offenen Verträge
stehen ausformuliert in 0b und 0c statt als Fragenliste. Ein praktischer
Ausführungsnachweis steht weiterhin vollständig aus.

**Vorgeschlagener Stand:** Vier benannte Produktentscheidungen lägen bei Mike;
sie stehen am Ende von Abschnitt 5. Ohne sie wäre der Rest widerspruchsfrei
umsetzbar. Frühere Review-Runden blieben als Prüfbelege daneben erhalten.

**Der Konzeptreview ist selbst ein Anwendungsfall des Produkts.** Er hat
bisher mehrere Runden gebraucht, ohne dass eine Zeile Produktcode gelaufen
wäre. Abschnitt 5 schlägt daraus eine ausdrückliche Konvergenzgrenze vor.

## Herkunft der Regeln in dieser Datei

Drei verschiedene Dinge stehen hier nebeneinander, und sie dürfen nicht
gleich aussehen. Eine Antwort auf eine Einzelfrage ist keine Abnahme des
Ganzen.

**Von Mike entschieden** — steht so oder sinngemäß von ihm:

- TypeScript, Node.js, SQLite, Vue 3 (0a).
- Kanban-Lebenszyklus mit den neun Zuständen; genau eine führende
  Ticketquelle, Dateien **oder** GitHub Issues, keine bidirektionale
  Spiegelung; kein `solved` neben `Erledigt`; technische Freigabe und
  menschliche Abnahme bleiben getrennt (0b).
- Ordner bestimmen den Ticketstatus. Worktrees haben ihre Berechtigung, aber
  nicht als Statusindikator (7. September 2026).
- Rollen sind grundsätzlich offen; Security-Analyst und Code-Optimizer sind
  vorstellbar (7. September 2026).
- Mehrbenutzerbetrieb entfällt, wenn er zu kompliziert wird
  (7. September 2026).
- Dokumentbasierte Konzeptreviews sind ein verbindliches Produktziel
  (7. September 2026).
- Review-Limit konfigurierbar, Standard 3; dauerhafte Agentensitzungen mit
  neuem Turn je Lauf; tokenfreies Worker-Polling; mehrere Instanzen desselben
  Providers sind eigenständige Agenten (frühere Runden).

**Vorgeschlagen, nicht entschieden** — von Claude oder Codex erarbeitet und
hier eingearbeitet, damit die Datei widerspruchsfrei lesbar ist: die
Übergangs- und Rechtetabelle, die Zustandsabbildung samt `next_step`, der
Ticketvertrag mit `content_version` und `source_state`, Ablageort und
Abgleichprotokoll, die GitHub-Labelabbildung, das Pflichtenmodell `author`,
`review`, `plan`, `decide`, der Vorschlags-/Abnahmeweg für Dokumente sowie
sämtliche Abnahmeergänzungen zu M1.

**Offen, nur Mike kann entscheiden:** siehe Abschnitt 5.

**Verbindliche Benutzerpräzisierungen sind hier bereits eingearbeitet:**
Kontext bleibt zwischen Läufen in derselben Agentensitzung erhalten;
automatische Übergaben erzeugen dauerhafte Folgeaufträge, die Worker ohne
Modellaufruf abfragen und über Laufzeitadapter aktivieren; das Review-Limit
ist konfigurierbar; mehrere spezialisierte Instanzen desselben Providers sind
eigenständige Agenten. Ältere Varianten gelten an diesen Stellen nicht mehr.
OpenCode mit OpenRouter ist als zusätzlicher Laufzeitadapter für gezielte
Modellversuche vorgesehen; sein eigenständiger Vertrag steht in Abschnitt 1c.
Ordner bestimmen den Ticketstatus; Rollennamen sind frei und offen, die Rechte
hängen an einer geschlossenen Pflichtenklasse; Prüfgegenstand kann Code oder
ein Dokument sein; Mehrbenutzerbetrieb entfällt, das Datenmodell trägt ihn
dennoch.
Der Technologieentscheid ist TypeScript mit Node.js, SQLite und Vue 3;
Begründung und Architekturgrenzen stehen in Abschnitt 0a.

**Eigenständiger Arbeitsauftrag:** Diese Datei genügt als Ausgangspunkt im
Projektordner. Es werden keine weiteren Konzept-, Setup- oder Ticketdateien
aus einem anderen Projekt benötigt. Externe Dokumentationslinks dienen nur
der Überprüfung der jeweiligen Werkzeugfähigkeiten.

## 0. Startauftrag für die neuen Claude- und Codex-Instanzen

Die Umsetzung entsteht in einem eigenen Projektordner mit eigenem Repository,
eigenen Arbeitstickets und eigenen Agentensitzungen. Das Testrepo für den
Vorabnachweis ist davon getrennt und enthält ausschließlich Testdaten.

**Auftrag an beide neuen Instanzen:**

```text
Lies diese Konzeptdatei vollständig; sie ist die einzige Regelquelle. Ältere
Review- und Stellungnahmedateien sind Prüfbelege, keine gültigen Regeln.
Prüfe vorhandene Projektregeln und den Arbeitsstand. Der Umsetzungsauftrag
gilt, sobald die vier offenen Produktentscheidungen aus Abschnitt 5 beantwortet
sind. Unterscheide dabei die drei Herkunftsklassen im Abschnitt „Herkunft der
Regeln": Nur die erste ist entschieden. Eröffne keine allgemeine neue Runde.
Verwende den festgelegten TypeScript-Stack aus Abschnitt 0a, bereits für
den programmatischen Vorabnachweis und anschließend für das Produkt.

Stimmt eure Arbeitsrollen vor dem ersten Edit ab: standardmäßig Claude als
Developer, Codex als Verifier, sofern der Benutzer nichts anderes festlegt.
Genau eine Instanz implementiert; die andere prüft unabhängig. Verändert
nicht gleichzeitig den Produktcode. Diese Arbeitsaufteilung ist von den
konfigurierbaren Rollen des späteren Produkts zu unterscheiden.

Beginnt mit dem kurzen Anschlusscheck beider Laufzeiten aus Abschnitt 2,
danach Versuch 1. Haltet Resultate und Einschränkungen
im neuen Projekt fest. Erst nach dessen Nachweis folgt Versuch 2, danach M1.
Implementiert M2 oder zusätzliche Rollen nicht vorgezogen. Routinefragen
zur Umsetzung entscheidet ihr selbst; bei einer fehlenden Produktentscheidung
oder einem nachgewiesenen technischen Hindernis konkret an den Benutzer wenden.

Erhaltener Sitzungskontext gehört bereits zum Vorabnachweis und zu M1.
Ein neuer Lauf bedeutet einen neuen Turn derselben Agentensitzung, keinen
neuen Chat. Automatisches Weiterschalten mit tokenfreiem Worker-Polling folgt in M2;
mehrere spezialisierte Verifier folgen danach. Die zugehörigen Verträge
stehen vollständig in Abschnitt 1a und 1b dieser Datei.

Begrenzt auch eure eigene Zusammenarbeit auf das konfigurierte Review-Limit
pro Arbeitsticket (Standard 3, beispielsweise auch 5). Danach bei offenen Befunden anhalten und
eine begrenzte menschliche Budgeterweiterung oder einen neuen Zuschnitt
abwarten. Fortschritt und Sitzungswechsel setzen diesen Zähler nicht zurück.
```

### Mindestvertrag, damit diese Datei allein genügt

Für die Umsetzung genügen anfangs kleine Markdown-Tickets mit Ziel,
Nicht-Zielen, Akzeptanzfällen, Prüfbelegen und Auflösung. Eine Matrix trennt
`AI` von `Human`; KI-Instanzen schreiben niemals in die Human-Spalte.
Ein simples gemeinsames STATUS-Dokument hält aktives Ticket, Owner,
Übergabecommit, Review-Runde, wirksames Rundenlimit und offene Nachricht fest.
Ein Agent startet erst, wenn die andere Instanz ihren eingefrorenen Stand
vollständig übergeben hat. Ein begonnener Runner ist noch kein bestandener Test.

Für das Produkt gelten diese Begriffe und Invarianten:

- **Akteure, Rollen, Pflichten:** Jeder Teilnehmer ist ein `actor` mit stabiler
  Identität und `kind: ai | human`. Der Rollenname ist frei und offen —
  „Security-Analyst", „Code-Optimizer" —, die Rechte hängen an der
  Pflichtenklasse des konkreten Auftrags: `author`, `review`, `plan`, `decide`.
  Akteurs-Identität, Laufzeit, Modellzugang, Modell, Rolle und Pflicht sind
  getrennt. Default: Claude schreibt, Codex prüft; umkehrbar. Mehrere Instanzen
  desselben Providers sind eigene Akteure.
- **Konfiguration M1:** Projektpfad, eindeutige Agent-IDs und Providerzuordnung,
  ein konfigurierbares `max_review_rounds` (Standard 3), persistente
  Sitzungszuordnung und endliche Laufzeitgrenze. Keine Geheimnisse in der
  versionierten Konfiguration. Timerwerte und deren Webbearbeitung folgen in M2.
- **Ausführungszustand (getrennt vom Ticketlebenszyklus in 0b):**
  `author_working` → `ready_for_review` → `reviewing` → `approved` oder
  `changes_requested`. `blocked` ist eine Kennzeichnung mit Grund, kein
  Zustand; der fällige Folgeschritt steht ausdrücklich in `next_step` und wird
  nicht erraten. Owner folgt der zuständigen Pflicht. Am Review-Limit wird das
  letzte Urteil vollständig ausgeführt und erst der **Start der nächsten
  Runde** verweigert, mit Owner `human`.
- **Übergabe:** stabile Übergabe-ID, Ticket-ID, Rundenzuordnung, `subject_kind`,
  fixierte Anforderungsfassung, Prüfgegenstand und Prüfbelege. Bei `code`
  ermittelt und validiert der Dienst Basiscommit, Commit und Tree-Hash selbst;
  bei `document` speichert er die übergebenen Inhalte unveränderlich und
  ermittelt deren Hash — ein Produktcode-Commit ist dafür nicht erforderlich.
  Besteht der Prüfgegenstand aus mehreren Dokumenten, fixiert die Übergabe
  deren Zuordnung und sämtliche Inhalte gemeinsam. Keine Freigabe eines anderen
  oder inzwischen veränderten Standes.
- **Nebenläufigkeit:** stabile Lauf-ID, Claim und Revision pro betroffenem
  Objekt; höchstens ein aktiver Turn je Agentensitzung. Gleiche
  Abschlussnachricht wird nur einmal wirksam. Nach Absturz
  keinen zweiten Schreiber starten, solange der alte Prozess noch laufen kann.
- **Problem-Report:** Pflichtartefakt mit Ticket/Runde/Snapshot, Autorrolle,
  eindeutiger Agent-ID, Spezialisierung, verständlicher Kurzfassung,
  ausgeführten Prüfungen und Einschränkungen.
  Jedes Finding nennt ID, Schwere, Status, Fundstelle, Erwartung, Beobachtung,
  Evidenz und später den Korrektur-/Gegenprüfbeleg. Die Fundstelle ist bei
  `code` die Datei-/Verify-Zeile mit Reproduktion, bei `document` die
  betroffene Regel mit Gegenfall und Quellenbezug.
- **Finding-Status:** `open`, `disputed`, `resolved`, `accepted`, `withdrawn`.
  Developer meldet Korrektur, Verifier bestätigt sie. Mensch akzeptiert einen
  Rest. Falsche Befunde werden begründet zurückgenommen. Blockierende Findings
  verhindern die Freigabe; ein Streit wird nicht endlos zwischen KIs verschoben.
- **Lernen:** Report hält konkrete Lernpunkte fest. Verallgemeinerte Muster
  brauchen mindestens zwei Belege oder eine nachgewiesene falsche
  Vollständigkeitsbehauptung. Muster enthalten Erkennungsregel und Gegenprobe,
  werden in passende Folgeaufträge aufgenommen und bleiben menschlich lesbar.
- **Abnahme:** technische Freigabe und menschliches Urteil getrennt führen.
  Merge, Veröffentlichung und Migration ergeben sich nicht aus `approved`.

M1 speichert ausschließlich seinen Testprojekt-Zustand. Die DB ist für den
technischen Ausführungszustand maßgeblich; Markdown-Reports sind Exporte.
Tickets selbst haben die in Abschnitt 0b festgelegte führende Quelle.

## 0a. Technologieentscheidung: TypeScript statt Python

**Festgelegt:** Node.js mit TypeScript und aktivierter strikter Typprüfung
(`strict`) für Workflow-Dienst, MCP-Anbindung, CLI, Worker und Laufzeitadapter.
SQLite verwaltet den dauerhaften Zustand; das Webinterface verwendet Vue 3
mit TypeScript. Die konkreten unterstützten Versionen, die SQLite-Anbindung
und das HTTP-Framework werden bei der Umsetzung gewählt und festgehalten.

Python wäre technisch ebenfalls geeignet. Beide Sprachen besitzen offizielle
MCP-SDKs; die Protokollunterstützung ist kein ausschlaggebender Unterschied.
[Offizielle MCP-SDKs](https://modelcontextprotocol.io/docs/sdk)
Für dieses Projekt entscheidet die gemeinsame Sprache mit dem Vue-Frontend:
Auftrags-, Report- und Konfigurationsverträge können gemeinsam gepflegt werden.
Der Dienst koordiniert externe KI-Laufzeiten und betreibt selbst kein Modell;
ein Python-Backend bringt deshalb allein wegen des KI-Bezugs keinen Vorteil.
Tokenfreies Polling ist in beiden Sprachen möglich. Die Sprachwahl begründet
keine zugesicherte Einsparung bei Modell-Tokens oder Laufkosten.

### Gemeinsamer Kern und klare Schnittstellen

- Ein Workflow-Kern setzt Zustandswechsel, Claims, Rollenrechte, Review-Limits
  und später Kontextgrenzen durch. MCP, HTTP/Web und CLI verwenden denselben
  Kern; sie implementieren diese Regeln nicht jeweils erneut. Im Serverbetrieb
  spricht die CLI mit dem Dienst und schreibt nicht parallel direkt in SQLite.
- Gemeinsame Datenverträge und Validierungsschemas liegen in einem Modul ohne
  Backend-Abhängigkeiten, das auch die Oberfläche verwenden kann. Externe
  MCP-, HTTP-, Konfigurations- und Laufzeitdaten werden zur Laufzeit validiert;
  TypeScript-Typen allein validieren keine eingehenden Nachrichten.
- Ein lokaler Backend-Prozess mit getrennten Modulen genügt zunächst. Die
  Worker können ab M2 als asynchrone Schleifen darin laufen. Verwaltete externe
  Laufzeiten wie Codex App Server bleiben separate Prozesse. Kein zusätzlicher
  Message-Broker, Microservice-Aufbau oder allgemeines Plugin-Framework für M1.
- Die Technologieentscheidung erweitert den Funktionsumfang nicht: M1 bleibt
  manuell gestartet, M2 ergänzt Automation und bearbeitbare Webkonfiguration.
  Weitere Modellzugänge hängen weiterhin an den definierten Laufzeitadaptern.

## 0b. Konzeptänderung: Kanban und alternative Ticketquellen

**Benutzerentscheidung vom 7. September 2026:** Das Produkt ist ein gemeinsames
Ticket- und Workflow-System für Mensch und KI-Agenten. MCP ist der Zugang der
Agenten; Web und CLI greifen auf denselben fachlichen Kern zu. Der bisherige
Zuschnitt auf offene und gelöste Tickets reicht für die praktische Arbeit nicht.

### Ticketlebenszyklus

Der normale Ablauf lautet: Eingang → Backlog → Bereit → In Arbeit → Review →
Abnahme → Erledigt. Er ist keine starre Einbahnstraße: Korrekturen führen aus
dem Review zurück in die Bearbeitung. Hinzu kommen Zurückgestellt und Verworfen.

| Zustand | Dateisystemordner | Bedeutung |
|---|---|---|
| Eingang | `inbox/` | Neu erfasst, noch nicht eingeordnet |
| Backlog | `backlog/` | Grundsätzlich angenommen, noch nicht zur Bearbeitung vorgesehen |
| Bereit | `ready/` | Anforderungen ausreichend klar; darf übernommen werden |
| In Arbeit | `in-progress/` | Umsetzung einschließlich angeforderter Korrekturen |
| Review | `review/` | Unabhängige Prüfung |
| Abnahme | `acceptance/` | Technisch freigegeben, menschliche Entscheidung ausstehend |
| Erledigt | `done/` | Gemäß den Abnahmeregeln abgeschlossen |
| Zurückgestellt | `deferred/` | Bewusst auf später verschoben; erneute Einplanung möglich |
| Verworfen | `rejected/` | Bewusst nicht weiterverfolgt; mit Begründung erhalten |

Zurückstellung und Verwerfung erhalten eine Begründung. Archivieren ist eine
Ansichtsfrage, kein zusätzliches fachliches Urteil. `solved` wird nicht als
zweiter, unklar abgegrenzter Abschluss neben Erledigt eingeführt. Technische
Freigabe und menschliche Abnahme bleiben ausdrücklich verschieden.

Blockiert ist eine zusätzliche Kennzeichnung mit Grund, etwa `blocked_reason`,
keine eigene Kanban-Spalte. Das Ticket behält seine fachliche Phase. Ein
blockierter Ausführungszustand, etwa am Review-Limit, bleibt zulässig und
bewirkt die sichtbare Blockadekennzeichnung. Die bisherigen detaillierten
Agentenzustände sind Ausführungszustände, keine weiteren Ticketspalten.

### Genau eine führende Ticketquelle pro Projekt

Ein Projekt verwendet entweder Dateisystem-Tickets oder GitHub Issues.
**Eine bidirektionale Spiegelung ist ausdrücklich ausgeschlossen.** Es gibt
keine parallel gepflegte zweite Ticketfassung. Ein späterer Quellenwechsel
wäre eine ausdrücklich angestoßene Migration, kein laufender Abgleich und
keine Voraussetzung für den ersten Ausbau.

Beide Varianten verwenden denselben Ticketvertrag, Kanban-Lebenszyklus und
dieselben MCP-Operationen. Ein Dateiadapter beziehungsweise GitHub-Adapter
liest und aktualisiert die gewählte Quelle. Menschen können die führende
Quelle direkt bearbeiten; der Dienst muss solche Änderungen erkennen.

Die gewählte Quelle führt Ticketinhalt und fachlichen Status. Die lokale DB
führt Agentensitzungen, Aufträge, Claims, Review-Runden, Snapshot-Zuordnungen
und Prüfbelege. Gesicherte Anforderungsfassungen dokumentieren den geprüften
Stand; sie sind keine zweite redaktionell bearbeitete Ticketquelle. Das Board
verbindet Ticketdaten mit dem tatsächlichen Ausführungsstand und zeigt
Widersprüche oder noch nicht übertragene Änderungen sichtbar an.

### Übergänge und Rechte

Rechte hängen an der **Pflichtenklasse** des konkreten Auftrags, nicht am
Rollennamen und nicht daran, ob ein Akteur Mensch oder KI ist; die Begriffe
stehen in Abschnitt 1a.

| Übergang | Wer darf |
|---|---|
| → Eingang (neu) | jeder Akteur; KI ausschließlich nach `Eingang`, nie höher |
| Eingang → Backlog → Bereit | `decide`; `plan` darf vorschlagen |
| Bereit → In Arbeit | Dienst bei Auftragsübernahme durch einen `author` |
| In Arbeit → Review | Dienst bei formal gültiger Übergabe |
| Review → In Arbeit | Dienst bei Urteil `changes_requested` |
| Review → Abnahme | Dienst bei Zustimmung aller Pflichtprüfer |
| Abnahme → Erledigt | ausschließlich `decide` |
| Abnahme → In Arbeit | `decide` (Abnahme verweigert) |
| beliebig → Zurückgestellt / Verworfen | `decide`, mit Begründung, Datum und Akteur |
| Zurückgestellt / Verworfen / Erledigt → Bereit | ausschließlich `decide`, mit Begründung |

Der Zug In Arbeit → Review gehört dem Dienst, nicht dem Autor: Er erfolgt erst
nach geprüfter Übergabe — Snapshot, Claim, Rechte, wirksame Grenzen. Kein Text
„bin fertig" bewegt ein Ticket.

**Wiedereröffnung erhält den Verbrauch.** Ein wiedereröffnetes Ticket beginnt
einen neuen Arbeitszyklus mit eigener `cycle_id`; die `cycle_id` ordnet Runden
lesbar zu und ist **keine Budgetgrenze**. Zusätzliche Runden entstehen
ausschließlich über die dokumentierte Erweiterung des wirksamen Limits nach
Abschnitt C, mit bisherigem und neuem Wert, Akteur und Begründung. Damit gibt
es genau einen Weg zu mehr Runden. Zurückstellen und späteres Einplanen ist
eine Planungsentscheidung und erneuert kein Budget.

KI-erzeugte Folgetickets landen in `Eingang`. Ein Autor schneidet sich seinen
Nachfolgeauftrag nicht selbst zu.

**Abbruch während eines laufenden Auftrags.** Der Zug nach `Zurückgestellt`
oder `Verworfen` wirkt sofort; der laufende Turn wird nicht mitten im Request
beendet. Der Auftrag geht auf `cancelling`, es startet kein neuer Turn, der
laufende endet mit Checkpoint, der Claim wird freigegeben. Worktree und Branch
bleiben erhalten; ein verworfenes Ticket ist kein Grund, Belege zu löschen.
Verbrauchte Runden bleiben verbraucht. Bereits geschriebene Reports bleiben
sichtbar, begründen aber keine Freigabe mehr.

### Zustandsabbildung

Der Kanban-Zustand steht in der führenden Quelle, der Ausführungszustand in
der DB. Gültig sind ausschließlich diese Kombinationen:

| Kanban | Ausführungszustand | Owner | Automatik |
|---|---|---|---|
| Eingang, Backlog | keiner | human | nein |
| Bereit | keiner | human | Start möglich, siehe Automatikfreigabe |
| In Arbeit | `author_working` | Autor | ja |
| Review | `ready_for_review`, `reviewing` | Prüfer | ja |
| Abnahme | `approved` | human | nein |
| Erledigt, Zurückgestellt, Verworfen | keiner | human | nein |

Jede andere Kombination ist ein Datenfehler: Sie sperrt die Automation und
wird sichtbar gemeldet. `approved` ist die technische Freigabe und identisch
mit dem Zug nach `Abnahme`; die menschliche Abnahme ist der Zug nach
`Erledigt`. `changes_requested` ist kein Zustand und keine Spalte, sondern das
Urteil, das den Zug Review → In Arbeit auslöst.

**Blockade ist eine Kennzeichnung, kein Zustand:** `blocked_reason` mit Owner,
zusätzlich zur Spalte. Damit bleibt erkennbar, *wobei* blockiert wurde.

**Der nächste Arbeitsschritt wird gespeichert, nicht abgeleitet.** Das Feld
`next_step` hält ausdrücklich fest, was fachlich fällig ist —
`await_author_correction`, `await_handoff`, `await_review`,
`await_human_decision` oder keiner. Ein aus Spalte, Zustand und letztem Urteil
erratener Folgeschritt erzeugt Lagen, die niemand entworfen hat.

**Am Rundenlimit.** Das Urteil der letzten erlaubten Runde wird zuerst
vollständig ausgeführt: `changes_requested` bewegt das Ticket regulär nach
`In Arbeit` und setzt `next_step: await_author_correction`. Erst der
**Start der nächsten Runde** wird verweigert — `blocked_reason:
review_limit_reached`, Owner `human`. Nach einer dokumentierten Erweiterung
läuft deshalb zuerst die Korrektur, dann eine neue Übergabe, dann die neue
Runde. Es wird nie ein Review auf einem unkorrigierten Stand wiederholt.

### Ticketvertrag: Identität, Fassung und Quellstand

Drei Größen, die auseinandergehalten werden, weil sie sich unterschiedlich
ändern:

| Größe | Bedeutung |
|---|---|
| `ticket_id` | Stabile Identität. Steht im Ticket selbst, nicht im Pfad und nicht im Dateinamen. Umbenennen und Verschieben lassen sie unberührt |
| `content_version` | Hash über den normalisierten Inhalt ohne Status. Fixiert die Anforderungsfassung einer Prüfung |
| `source_state` | Vollständiger beobachteter Quellstand: Identität, `content_version`, fachlicher Status beziehungsweise Pfad und ein adapterspezifisches Merkmal |

`content_version` allein genügt für Schreiboperationen nicht: Ein Verschieben
ändert sie nicht. Jede Schreiboperation nennt deshalb den **erwarteten
`source_state`**; weicht der tatsächliche ab, entsteht ein Konflikt und kein
Schreibvorgang.

Pflichtfelder beider Adapter: Identität, Titel, Priorität, Anforderungen mit
Akzeptanzfällen, Nicht-Ziele, Begründung samt Datum und Akteur bei
Zurückstellung oder Verwerfung, optionales `blocked_reason`, optionaler
Ticket-Override des Rundenlimits, Automatikkennzeichnung und der vorgesehene
Agent.

### Dateisystemvertrag und Ablageort

Die oben genannten Ordner liegen unter `_tickets/`. Der Ordner bestimmt den
Ticketstatus; ein Statuswechsel verschiebt die Datei. Die stabile Ticket-ID
bleibt erhalten. Es gibt kein zusätzliches bearbeitbares Statusfeld im Ticket;
beim GitHub-Adapter übernimmt das Statuslabel diese Rolle. Anforderungen,
Priorität und Blockade- oder Zurückstellungsgründe stehen in der Datei. Für
die Blockadekennzeichnung wird kein eigener Statusordner angelegt.

Zwei Regeln machen das Ordnermodell erst eindeutig:

1. Der Dienst liest den Status aus **genau einem konfigurierten Pfad**.
   Derselbe Ordnerbaum in einem Agenten-Worktree ist veraltetes Beiwerk und
   wird nie als Quelle gelesen.
2. **Agenten verschieben keine Ticketdateien.** Ein Statuswechsel läuft über
   MCP; der Dienst führt ihn in der führenden Ablage aus. Ein Statuszug ist
   damit nie Teil eines geprüften Trees.

Diese Regeln beseitigen die Mehrdeutigkeit zwischen Kopien. Sie sind **keine
Zusage gegen Git**: Liegt die führende Ablage in einem Arbeitsverzeichnis,
verändern Revert, Reset, Merge und Branchwechsel den Ticketbaum dort weiterhin
— ein Branchwechsel sogar auf einen Schlag. Solche Änderungen sind gewöhnliche
externe Quellenänderungen und werden wie ein manueller Zug behandelt: erkannt,
geprüft, im Zweifel sperrend. Ein durch Rücknahme entstandener Ticketzug gibt
niemals von sich aus Automation frei.

Daraus folgt der Ablageort: **Das alltägliche Arbeitsverzeichnis des Menschen
ist als führende Ablage ausgeschlossen** — dort wechseln Branches. Zulässig
sind ein eigener Ticketbranch mit eigenem Arbeitsverzeichnis, ein fest auf
einen Branch gebundenes Zusatz-Checkout oder ein einfaches Verzeichnis ohne
Versionierung. M1 verwendet das einfache Verzeichnis im Testrepo, weil dort
keine Tickethistorie gebraucht wird; der Pfad ist konfiguriert, sodass die
versionierte Variante später eine Konfigurationsänderung ist. Die Zusage, dass
der menschliche Checkout unberührt bleibt, gilt damit unverändert.

### Quellenabgleich, Konflikte und Wiederanlauf

Manuelles Verschieben und Änderungen über MCP, CLI oder Web unterliegen
denselben fachlichen Regeln. Der Dienst erkennt und prüft externe Änderungen.

*Abgleich als benannte Operation.* Die DB führt je Ticket den zuletzt
beobachteten `source_state` mit Zeitpunkt. Der Abgleich läuft beim
Dienststart, vor jedem Auftragsstart, vor jedem Statusschreiben und bei
Ereignissen eines Dateiwächters. **Kein Auftrag startet auf einem Lesestand,
der älter ist als der letzte Abgleich.** Der Wächter beschleunigt, er beweist
nichts: Ein Dienst, der stand, hat keine Ereignisse verpasst, sondern muss neu
lesen.

*Schreiben mit erwartetem Quellstand.* Absicht zuerst dauerhaft speichern
(von, nach, erwarteter `source_state`), unmittelbar vor dem Schreiben erneut
lesen und vergleichen, schreiben, danach das Ergebnis gegen die Absicht
prüfen. Jede Abweichung ist ein Konflikt: kein zweiter Versuch, keine stille
Überschreibung. Inhaltsänderung und Statuszug sind nie eine Operation.

*Die verbleibende Lücke wird benannt.* Auf einem Dateisystem gibt es kein
atomares Vergleichen-und-Verschieben gegenüber einem gleichzeitigen `mv` eines
Menschen; bei GitHub gibt es für Label keine Sperre. Der Dienst **erkennt**
konkurrierende Änderungen, er verhindert sie nicht. Erkannt heißt: sperren und
melden, nicht korrigieren.

*Deshalb ein klarer Bearbeitungsmodus statt einer unerfüllbaren Zusage.* Der
Dienst unterscheidet aktiven Betrieb und direkte Quellenbearbeitung. Im aktiven
Betrieb schreibt ausschließlich der Dienst in die Ticketquelle; menschliche
Änderungen laufen über Web oder CLI, Agenten über MCP.

Für direkte Dateiänderungen aktiviert der Mensch den Bearbeitungsmodus. Der
Dienst sperrt neue Auftragsstarts und Quellschreibvorgänge, lässt aktive Turns
geordnet enden und sichert ihre Ergebnisse. Erst wenn kein aktiver Turn und
keine unvollendete Quellschreiboperation verbleibt, bestätigt er den Modus —
**ein unklarer Prozesszustand ist keine Bestätigung.** Nach den Änderungen
fordert der Mensch die Wiederaufnahme an; der Dienst liest die Quelle
vollständig neu und prüft Identitäten, Statuszüge, Inhaltsänderungen und
bestehende Prüfbezüge. Bei einem Konflikt bleibt die Automation gesperrt. Ein
Neustart hebt den Bearbeitungsmodus nicht auf.

Das ist eine Vereinbarung, keine Betriebssystemsperre. Direkte Änderungen
außerhalb des bestätigten Modus sind vom sicheren Schreibvertrag nicht
abgedeckt: Erkannte Abweichungen sperren die Automation, aber eine lückenlose
Erkennung beliebiger konkurrierender Zugriffe wird ausdrücklich nicht
zugesichert. Für M1 genügt ein CLI-Weg zum Pausieren und Wiederaufnehmen; der
bestätigte Modus und seine Persistenz über einen Neustart gehören dann zur
M1-Abnahme. Beim GitHub-Adapter gilt dieselbe fachliche Regel, aber eine
lokale Sperre erreicht fremde Integrationen nicht; welche Garantien dort
tatsächlich bestehen, weist der Adapter nach seinem eigenen Nachweis aus.

*Wiederanlauf.* Nach einem Absturz entscheidet der tatsächliche Quellstand
gegen die gespeicherte Absicht: Ziel bereits erreicht → bestätigen. Quelle
unverändert am Ausgangspunkt → Schreiben wiederholen. Quelle steht woanders →
Konflikt, keine automatische Reparatur. Der Dienst korrigiert ausschließlich
seine eigene unvollendete Absicht.

| Fall | Antwort |
|---|---|
| Mensch verschiebt während eines laufenden Auftrags | Auftrag aussetzen, Konflikt sichtbar, Owner `human`; laufender Turn endet geordnet |
| Dieselbe Identität an zwei Orten | Ungültig, beide gesperrt, keine Automation |
| Identität verschwunden | Als `missing` markieren, Aufträge aussetzen; in der DB wird nichts gelöscht |
| Inhalt während eines Reviews geändert | Fixierte `content_version` bleibt für die Runde gültig; die neue Fassung wirkt ab der nächsten Übergabe |
| Ticket in `Erledigt` ohne Belege oder Abnahme | Widerspruch anzeigen, nicht stillschweigend zurückschieben |
| Ticketzug durch Revert, Reset oder Branchwechsel | Wie ein manueller Zug behandeln; gibt keine Automation frei |

### GitHub-Adapter

Alle neun Zustände werden über **genau ein** Label `status/<zustand>`
abgebildet, einschließlich `status/done` und `status/rejected`. Der
Schließzustand ist abgeleitet und muss übereinstimmen: `Erledigt` →
geschlossen mit Grund `completed`, `Verworfen` → geschlossen mit Grund
`not_planned`, alle übrigen offen. `blocked` ist ein zusätzliches Label, der
Grund steht im Text.

Drei Fehlerfälle mit derselben Antwort — ungültiger Quellenstatus, keine
Automation, Konflikt sichtbar: kein Statuslabel, mehr als eines, oder ein
Label, das dem Schließzustand widerspricht. Der Dienst interpretiert nichts
und schließt oder öffnet nichts von sich aus. Der häufigste Fall ist ein
Mensch, der ein Issue schließt, ohne das Label zu ändern; wie dieser Fall
ergonomisch aufgelöst wird, ist eine offene Produktentscheidung.

Erkennung über Polling mit Änderungszeitpunkt, Webhooks später; der Vertrag
bleibt gleich. **Reports werden nicht in die Ticketquelle geschrieben.** In
einem öffentlichen Repository würden Prüfbelege damit veröffentlicht; sie
bleiben lokal und gehen den Weg über den Export-Branch aus Abschnitt D.

### Automatikfreigabe und Auswahl

Sobald Worker selbständig abholen, startet das Ablegen in `Bereit` einen
bezahlten Turn. Deshalb: Automatik ist pro Ticket ausdrücklich gesetzt und
zusätzlich pro Projekt schaltbar; ohne beides bleibt ein Ticket liegen. Das
Ticket nennt den vorgesehenen Agenten — ein Auftrag ohne `agent_id` ist nicht
ausführbar.

Die Auswahl folgt der ausdrücklichen Priorität, bei Gleichstand der stabilen
Identität. **Nicht nach Änderungszeit:** Sonst springt ein Ticket durch eine
beliebige Korrektur nach vorn, und Korrekturen sind in einer Ordnerablage der
häufigste Vorgang.

### Reihenfolge der Adapter

Gemeinsamer Vertrag und Kanban zuerst, der Dateiadapter als erste Umsetzung,
der GitHub-Adapter **nach der M1-Abnahme**. Er bringt Anmeldung, Ratengrenzen,
Sichtbarkeit und Ereigniszustellung mit, und keines davon beweist etwas über
den Ablauf, um den es in M1 geht. Beide Quellen gehören zum Produktziel.

## 0c. Prüfgegenstände: Code und Dokument

**Benutzerentscheidung vom 7. September 2026:** Das System muss auch
dokumentbasierte Reviews tragen — Konzept, Spezifikation oder
Entscheidungsvorlage als Prüfgegenstand. Ein Produktcode-Diff und ein
ausgeführter Softwaretest sind dafür keine sinnvollen Pflichtvoraussetzungen.
Der vorliegende Konzeptreview ist der konkrete Anwendungsfall.

Ein Ticket nennt deshalb seinen `subject_kind`:

| `subject_kind` | Fixierte Fassung | Geeignete Prüfbelege |
|---|---|---|
| `code` | Basiscommit, Commit und Tree; isolierte Worktrees | Testlauf mit Befehl und Ergebnis, Diffstelle, Reproduktion |
| `document` | Gespeicherter Inhalt mit Hash; **kein** Produktcode-Commit nötig | Widerspruch, betroffene Regel, Gegenfall, Quellenbezug |

Ein Dateiname identifiziert keine unveränderliche Prüffassung; das leistet nur
der gespeicherte Inhalt mit seinem Hash. **Eine Textprüfung wird nie als
bestandener Laufzeittest ausgewiesen.** Die Belegart richtet sich nach der
Aufgabe, nicht nach der Gewohnheit des Prüfers.

Alles andere bleibt gleich, und das ist der Punkt: derselbe Kanban-Zyklus —
`In Arbeit` ist die Überarbeitung, `Review` die Dokumentprüfung, `Abnahme` die
menschliche Konzeptentscheidung —, dieselben Übergänge und Rechte, dieselben
stabilen Finding-IDs mit ihren Status, dasselbe Reviewbudget samt
ausdrücklicher Erweiterung. Es gibt kein zweites Board je Artefaktart.

Zwei Abgrenzungen, die im Dokumentfall besonders leicht verrutschen:

- **Stellungnahme, Korrekturmeldung und unabhängige Bestätigung sind drei
  Dinge.** Ein Widerspruch setzt ein Finding auf `disputed`, eine gemeldete
  Korrektur auf `resolved`; erst der Prüfer bestätigt sie. Eine neue
  Produktentscheidung macht betroffene alte Urteile nicht rückwirkend gültig.
- **Ein neuer Dateiname erzeugt weder ein Ticket noch ein Budget.** Runden
  eines Dokumentreviews zählen gegen dasselbe Ticket wie im Codefall.

Der `author` einer Pflichtenklasse erzeugt und ändert den Prüfgegenstand —
Produktcode oder Dokument. Die Überarbeitung eines Konzepts fällt damit weder
zwischen `plan` und `implement` noch verlangt sie eine eigene Rolle.

**Zwei Hashes, zwei Bezüge.** `requirements_version` fixiert die Fassung der
Ticketanforderungen, `subject_version` den Inhalt des geprüften Dokuments.
Beide sind Inhalts-Hashes und trotzdem verschiedene Dinge: Das eine sagt,
wonach geprüft wird, das andere, was geprüft wird.

### Gültige Fassung und Änderungsvorschlag

Ein Dokumentauftrag unterscheidet die bisher gültige Fassung vom aktuellen
Änderungsvorschlag. Der Autor bearbeitet ausschließlich den Vorschlag; die
gültige Fassung bleibt unverändert verfügbar. Bei einer erstmaligen Erstellung
gibt es zunächst noch keine gültige Fassung.

Jede Übergabe fixiert den Inhalt des Vorschlags und erhält eine stabile
Kennung mit Inhalts-Hash. Prüfberichte, technische Freigabe und menschliche
Abnahme beziehen sich auf genau diese Fassung. Eine weitere Bearbeitung
erzeugt eine neue Fassung; alte Urteile werden nicht darauf übertragen.

Erst nach Zustimmung aller für die Übergabe vorgesehenen Pflichtprüfer gelangt
das Ticket nach `Abnahme`. Der menschliche Entscheider nimmt die bezeichnete
Fassung ausdrücklich an oder weist sie zurück. **Die Übernahme in die gültige
Fassung darf der Dienst erst aufgrund dieser Abnahme ausführen.** Eine
Stellungnahme, Korrekturmeldung oder technische Freigabe allein berechtigt
nicht dazu.

Vor der Übernahme prüft der Dienst, dass die abgenommene Vorschlagsfassung und
die erwartete bisher gültige Fassung noch vorliegen. Bei Abweichung bleibt die
Übernahme offen und der Konflikt sichtbar. Abnahmeentscheidung und
erfolgreiche Übernahme werden getrennt dokumentiert: Ein Fehler beim Übernehmen
ist kein erfolgreicher Abschluss, und eine Wiederholung verwendet dieselbe
abgenommene Fassung.

Eine teilweise Annahme darf keine neue, ungeprüfte Mischfassung als vollständig
geprüft ausweisen. Für M1 genügt die Abnahme einer ganzen fixierten Fassung;
gewünschte Teiländerungen gehen zurück an den Autor und werden neu übergeben.

### Mehrere Artefakte an einem Ticket

Ein Ticket kann Konzeptfassung, Prüfbericht, Stellungnahme und Überarbeitung
zugleich führen. **Jeder Prüfauftrag nennt ausdrücklich seinen primären
Prüfgegenstand**, dessen fixierte Fassung und die herangezogenen
Referenzfassungen. Der Bezug auf dasselbe Ticket genügt nicht, um zwei
Prüfaufträge als Prüfung desselben Snapshots zu behandeln.

Mehrere Pflichtprüfer zählen nur dann zur gemeinsamen fachlichen Runde, wenn
sie derselben festgelegten Übergabe zugeordnet sind. Die Gegenprüfung eines
Berichts kann eine Klärung innerhalb dieser Runde sein; das wird mit Auftrag
und Bezug festgehalten und **nicht nachträglich aus Dateinamen abgeleitet**.
Eine neue überarbeitete Hauptfassung braucht eine neue Übergabe und deren
Gegenprüfung. Alle Runden bleiben dem Ticketbudget zugeordnet.

Abläufe ohne gespeicherte Übergabe- und Rundenzuordnung werden als
**Rekonstruktion** gekennzeichnet; daraus wird kein exakt gemessener
Rundenverbrauch abgeleitet. Für einen Papierdurchlauf dürfen konkrete
Budgetwerte ausdrücklich als Annahme verwendet werden.

## 1. Bisherige Bewertung der Punkte A–H

| Punkt | Entscheidung |
|---|---|
| A · Developer-Worktree | Übernehmen. Kein gestarteter Runner arbeitet im Arbeitsverzeichnis des Menschen. Developer erhält einen exklusiven Ticket-Branch im eigenen Worktree, Verifier einen detached Review-Worktree. |
| B · Vorabnachweis | Übernehmen: zwei sequenzielle Versuche mit kleinem MCP-Stub. Ein einzelner Fehlschlag bedeutet zunächst Diagnose des konkreten Hindernisses, keine pauschale Widerlegung aller Runner. |
| C · Konvergenz | Feste Obergrenze bereits in M1: standardmäßig drei Review-Runden pro Ticket. Fortschritt hebt das Limit nicht auf. Finding-Bewegung bleibt zusätzliche Diagnose. |
| D · Export | Eigener Export-Branch im Projektrepo ersetzt den Vorschlag eines separaten Audit-Repos. Umsetzung in M2; Veröffentlichung und Mitnahme müssen ausdrücklich geprüft werden. |
| E · Fortsetzung | Nach Benutzerpräzisierung: dauerhafte Sitzung je Agent, neuer Turn je Lauf. Checkpoint sichert offene Arbeit; neue Sitzung nur als kontrollierter Ausnahmeweg. |
| F · MVP zu groß | Übernehmen. M1 beweist einen manuell gestarteten Durchlauf mit zwei Rollen und sichtbarem Report. Timer, umfassende Konfiguration und Betriebssicherung folgen in M2. |
| G · Entscheidungen | Übernehmen. „Wartet auf dich“ ist Bestandteil der ersten Webübersicht. |
| H · Testbetrieb | M1 läuft ausschließlich auf einem separaten Testrepo. Die Übernahme realer Arbeitsdaten folgt nach Abnahme und Betriebsvorbereitung. |

### A: Konkrete Worktree-Regel

Im MVP gehört der Branch `agentboard/t-<id>` exklusiv zum Developer-Worktree.
Der Mensch arbeitet in seinem bisherigen Checkout auf seinem eigenen Branch.
Der Verifier prüft einen gespeicherten Commit im detached Worktree. Geteilt
werden Repository-Objekte, nicht Arbeitsverzeichnis oder aktiver Branch.
Git lässt denselben Branch regulär nicht in zwei Worktrees auschecken;
dieser Schutz wird nicht mit Force-Optionen umgangen.
[Git-Worktrees](https://git-scm.com/docs/git-worktree)

Diese Regel gilt für `subject_kind: code`. **Ein Dokumentauftrag braucht weder
Worktree noch Branch noch Commit:** Sein fixierter Stand ist der gespeicherte
Inhalt mit Hash. Auftragsvalidierung, Checkpoint, Wiederaufnahme und
Abnahmeprüfung dürfen für ihn keinen Git-Snapshot verlangen — eine
Wiederaufnahme lädt genau den gespeicherten Dokumentstand und nicht die
inzwischen veränderte Datei gleichen Namens.

Kein automatisches Fast-Forward oder Merge in den menschlichen Arbeitsbranch.
Das Ergebnis ist zunächst ein geprüfter Ticket-Commit. Ein neuer Lauf darf
einen vorhandenen Developer-Worktree erst übernehmen, wenn der vorherige
Prozess sicher beendet ist. Worktrees trennen Dateien, aber nicht automatisch
Ports, Datenbanken oder OS-Rechte; jeder Lauf bekommt eigene Testressourcen.

### C: Fortschritt beobachten, keine neue Scheingenauigkeit schaffen

**Nachtrag aus dem Benutzerauftrag: Review-Schleifen sind hart begrenzt.**
`max_review_rounds: 3` ist die Voreinstellung, konfigurierbar in der Datei
und später über CLI/Web. Das Limit gilt bereits in M1 für manuelle Starts
und später identisch für automatische Starts. Unbegrenzt ist kein gültiger
Konfigurationswert; eine KI darf die Grenze nicht selbst erhöhen.

Das Projekt setzt einen positiven ganzzahligen Standard, etwa 3 oder 5.
Ein Ticket kann ein vom Menschen ausdrücklich festgelegtes abweichendes
Limit besitzen. Auflösung: Ticket-Ausnahme vor Projektwert vor Standard 3.
CLI und Web zeigen später denselben wirksamen Wert und seine Herkunft,
beispielsweise **„Review 2/5 – Projektwert“**. M1 liest dieselbe Konfiguration
aus der Datei und zeigt sie über `config show`.

Änderungen werden mit Akteur und bisherigem/neuem Limit dokumentiert.
Eine Erhöhung behält den bisherigen Verbrauch; eine Senkung unter den
Verbrauch sperrt weitere Starts, widerruft aber kein bereits gültiges Urteil.
Ein bereits laufendes Review darf geordnet enden; vor jedem folgenden Start
wird das aktuelle wirksame Limit erneut geprüft.

Eine Runde ist die fachliche Prüfung einer neuen gültigen Übergabe, beginnend
mit der ersten Runde. Entwurfs- und Implementierungsreviews desselben Tickets
teilen sich das Budget. Bei mehreren Pflichtprüfern gehört deren Prüfung
derselben Übergabe zu einer gemeinsamen Runde. Zähler und wirksames Limit
werden dauerhaft gespeichert; jeder Reviewstart prüft die Grenze.

Nach der letzten konfigurierten Runde gilt: Bei `approved` normal abschließen.
Andernfalls wird das Urteil **zuerst vollständig ausgeführt** —
`changes_requested` bewegt das Ticket regulär nach `In Arbeit` und hinterlegt
`next_step: await_author_correction` — und erst der Start der nächsten Runde
verweigert: `blocked_reason: review_limit_reached`, `owner: human`. Nach einer
Erweiterung läuft deshalb Korrektur, neue Übergabe und dann die neue Runde;
niemals ein wiederholtes Review desselben unkorrigierten Standes. Report und
„Wartet auf dich“ nennen Rundenverbrauch, offene Findings, den fälligen
Arbeitsschritt und die kleinste vorgeschlagene Fortsetzung. Die UI zeigt
beispielsweise **„Review 3/3 – Entscheidung nötig“** oder bei Limit 5
**„Review 5/5 – Entscheidung nötig“**.

Der Mensch kann abschließen, den Scope neu schneiden oder ausdrücklich eine
begrenzte Zahl weiterer Runden freigeben. Beispiel: eine zusätzliche Runde
erhöht das wirksame Limit von 3 auf 4; sie setzt den Zähler nicht auf null.
Freigabe und Begründung bleiben nachvollziehbar. Sitzungswechsel, anderer
Provider, Compaction, neuer Commit, bloße Ticketumbenennung, ein neuer
Dateiname und **auch Zurückstellung mit späterer Wiedereröffnung** erneuern das
Budget nicht. Ein wiedereröffnetes Ticket beginnt einen neuen Arbeitszyklus;
dessen `cycle_id` ordnet Runden lesbar zu und ist keine Budgetgrenze. Ein
echtes Folgeticket braucht einen ausdrücklich autorisierten Zuschnitt; es darf
kein automatischer Ausweg um die Grenze sein. Es gibt genau einen Weg zu mehr
Runden: die dokumentierte Erweiterung des wirksamen Limits.

Fortsetzung eines unvollständigen Reviews zählt zur bereits begonnenen Runde.
Leerdurchläufe und formale Übergabeprüfungen zählen nicht als Fachreview.
Technische Wiederholungen bleiben separat durch Lauf-/Startgrenzen begrenzt;
eine neue Produktkorrektur ist dagegen eine neue Übergabe und neue Runde.

Weniger offene blockierende Findings ist ein brauchbares Signal. Es kann
trotzdem entstehen, wenn fünf kleine Fehler durch einen schwereren ersetzt
werden oder eine Regel still entfällt. Gleichbleibende Anzahl kann echten
Fortschritt bei einem großen Finding verdecken. Deshalb heißt die Anzeige
**„Blockierende Findings: vorher → nachher“**, nicht „Qualitätsfortschritt“.

Ergänzend gilt für M2: Drei aufeinanderfolgende abgeschlossene Fachreviews ohne Senkung
dieser Zahl lösen eine Konsolidierung und einen sichtbaren Halt aus. Die erste
Prüfung setzt die Ausgangsbasis. Formale Fehler und Checkpoints zählen nicht.
Bei geändertem Scope wird eine neue Basis begründet dokumentiert; das gesamte
Ausführungsbudget des Tickets wird dadurch nicht zurückgesetzt.

Stabile Finding-IDs und Statushistorie machen Korrektur, neue Findings,
Rücknahme und menschliche Restakzeptanz unterscheidbar. Zusätzlich begrenzen
Startzahl und Laufzeit die Automation, damit schwankende Finding-Zahlen keine
endlose Schleife ermöglichen. Im manuell gestarteten M1 genügt die Anzeige
dieser Bewegung zusätzlich zum festen Rundenlimit. Eine Fortsetzung wegen
sinkender Finding-Zahlen darf das feste Limit niemals umgehen.

### D: Export-Branch ja, automatische Portabilität nein

Ziel für M2: `refs/heads/agentboard/export` als Branch mit unabhängiger
Historie, geschrieben ohne den menschlichen Index oder Produktbranch zu
ändern. Exportaufträge bleiben in der DB wiederholbar, ihr Zustand im Web
sichtbar. Das erfordert keinen zweiten Repository-Ordner für den Benutzer.

Ein nur lokal erzeugter Branch ist aber nicht im Remote. Er muss gezielt
veröffentlicht werden; ein Single-Branch-Klon kann ihn auslassen. Ein normaler
Klon legt andere Branches außerdem nicht als Dateien im Standard-Checkout ab.
Die Anleitung muss das Öffnen des Export-Branches erklären. „Reports reisen
mit“ gilt erst nach einem überprüften Übertragungsweg.
[Git-Push](https://git-scm.com/docs/git-push),
[Git-Clone](https://git-scm.com/docs/git-clone)

Automatisches Veröffentlichen folgt ausschließlich einer konfigurierten,
autorisierten Freigabe. Snapshot-Refs außerhalb von `refs/heads` sind durch
den Report-Export nicht automatisch gesichert; eine vollständige Sicherung
muss auch die benötigten Codeobjekte erhalten. Vor Produktivbetrieb gehören
DB-Backup und Wiederherstellungsprobe dazu. M1 bietet einen lesbaren
Markdown-Download, verspricht aber noch keine produktive Backup-Lösung.

### E: Ein einheitlicher Abschlussvertrag für beide Rollen

Die drei Formen werden rollenunabhängig formuliert:

| Laufabschluss | Bedeutung |
|---|---|
| `completed` | Rollenauftrag beendet: Developer-Übergabe, vollständiges Verifier-Urteil oder konkret dokumentierter Entscheidungsbedarf |
| `checkpointed` | Rollenauftrag noch offen, Fortsetzungsartefakt gespeichert; nächster Turn setzt dieselbe Agentensitzung fort |
| `interrupted` | Kein gültiger geordneter Abschluss vorhanden; Wiederaufnahme muss den tatsächlichen Stand prüfen |

Nur `handoff` als Erfolgsform wäre für einen fertigen Verifier-Report zu eng.
Ein Verifier-Checkpoint enthält einen unvollständigen Report ohne Freigabe;
ein Developer-Checkpoint enthält den gesicherten Zwischenstand. In beiden
stehen Erledigtes, offene Punkte, Evidenz und der nächste konkrete Schritt.
Die bestehende Sitzung erhält dieses Paket beim nächsten Turn zusätzlich zu
ihrem erhaltenen Gesprächskontext. Eine Ersatzsitzung verwendet es nur beim
kontrollierten Wiederanlauf nach Abschnitt 1a.

Auch eine fortgesetzte Sitzung kann durch große Eingaben zu viel Kontext
bekommen. Begrenzter Auftrag, gezieltes Nachladen und kontrollierter
Sitzungswechsel bleiben nötig.
Verfügbare Kontextwerte werden bereits in M1 mit Quelle und Zeitpunkt erfasst,
fehlende als unbekannt. M2 ergänzt die konfigurierbare Kontextgrenze mit dem
verbindlichen Auslöser aus Abschnitt 1a. Pauschale 60/80-%-Grenzen sind keine
Vorgabe. Ein harter Timeout kann nur `interrupted` garantieren;
regelmäßiges Sichern und geordnetes Beenden reduzieren den Informationsverlust.

## 1a. Agentenidentität, Spezialisierung und dauerhafter Kontext

### Begriffe und Zuständigkeit

| Begriff | Bedeutung |
|---|---|
| `agent_id` | Stabile Identität einer konkreten konfigurierten KI-Instanz im Projekt |
| `runtime` | Agentenlaufzeit/Adapter: `claude-code`, `codex` oder später `opencode` |
| `provider` | Konfigurierter Modellzugang: etwa `anthropic`, `openai` oder `openrouter`; kein Rollenname |
| `model` | Gewähltes Modell; darf bei verschiedenen Agenten identisch sein |
| `role` | Frei vergebener, überall angezeigter Name des Arbeitsauftrags, etwa „Verifier Code & Tests", „Security-Analyst", „Code-Optimizer" |
| `duty` | Geschlossene Pflichtenklasse, die die Rechte trägt: `author`, `review`, `plan`, `decide` |
| `session_id` | Tatsächliche Sitzungs-/Threadkennung der Agentenlaufzeit, dauerhaft an den Agenten gebunden |
| `run_id` | Ein einzelner Arbeitsdurchlauf/Turn dieser Sitzung |

**Die Rechte hängen am Auftrag, nicht am Namen.** Eine Rolle erklärt, welche
Pflichten sie überhaupt übernehmen darf; die konkrete Übergabe legt genau eine
davon fest. „Code-Optimizer" ist deshalb keine Aussage über Schreibrechte: Als
`review` liefert er Empfehlungen und ändert nichts, als `author` schreibt er
und unterliegt Claim, Snapshot und der Regel vom genau einen aktiven Autor.
Aus dem Rollennamen wird nichts abgeleitet — dieselbe Regel gilt schon für
Security- und UX-Bezeichnungen.

Mehrere Arbeitsschritte nacheinander bleiben in `In Arbeit`; die Spalte ist
die fachliche Phase, nicht der Ausführungsschritt. Jeder schreibende Schritt
braucht seine eigene Übernahme und Übergabe. **Ob überhaupt mehrere
schreibende Rollen unterstützt werden, ist eine eigene Umfangsentscheidung**
und nicht durch das Rollenmodell beantwortet; die Regel gegen gleichzeitig
aktive Produktschreiber bleibt in jedem Fall bestehen.

Eine Rolle nennt ihre benötigten Werkzeuge — Browser, Testlauf, Netzzugang.
Fehlen sie dem zugeordneten Akteur, weist der Dienst die Rolle als nicht
ausführbar aus, statt eine schwächere Prüfung als vollwertige zu verbuchen.

Der Dienst adressiert immer eine `agent_id`. Er sendet niemals pauschal
„an Codex“, weil mehrere Codex-Instanzen konfiguriert sein können. Innerhalb
eines Projekts besitzt jeder aktive Agent seine eigene Sitzungsbindung und
höchstens einen aktiven Turn. Zwei Agenten teilen keine Sitzung, auch wenn
Laufzeit, Provider und Modell übereinstimmen. Sitzungskennungen sind zusammen
mit Laufzeitinstanz und Projekt zu speichern, nicht als global eindeutige Zeichenkette
vorauszusetzen.

Beispiel der geplanten Konfigurationsform; noch kein existierendes CLI-Schema.
Die fünf Runden sind ein ausdrücklicher Projekt-Override; der Standard bleibt 3:

```yaml
max_review_rounds: 5 # Projekt-Override; Standard: 3
agents:
  - agent_id: claude-dev
    runtime: claude-code
    provider: anthropic
    role: "Developer"
    duties: [author]
    enabled: true
  - agent_id: codex-code
    runtime: codex
    provider: openai
    role: "Verifier Code & Tests"
    duties: [review]
    enabled: true
  - agent_id: codex-ux
    runtime: codex
    provider: openai
    role: "UX-Pruefer"
    duties: [review]
    requires: [browser]
    enabled: false
humans:
  - actor_id: mike
    kind: human
    role: "Produktverantwortlich"
    duties: [decide, plan, author]
```

Die dritte Instanz ist ein Ausbaubeispiel und in M1 deaktiviert. Laufzeit-
und Providerwerte benennen Adapter und Modellzugang, nicht die Anmeldung:
Abonnement-Login oder API-Key werden separat über nicht geheime
Konfigurationsreferenzen zugeordnet. Die Beispielwerte erzwingen keinen
Wechsel von vorhandenen Abonnements auf API-Abrechnung. Laufzeit-
Sitzungskennungen und aktuelle Claims stehen in der Persistenz, nicht als
kopierbare IDs in dieser Beispielkonfiguration. Modell und verfügbare Werkzeuge
werden pro Akteur festgelegt. Ein Providerwechsel oder eine wesentliche
Änderung des Rollenauftrags benötigt eine geordnete neue Sitzungsbindung,
keine stille Weiterverwendung eines unpassenden Kontextes.

Menschliche Akteure stehen in derselben Liste, ohne Laufzeit, Provider und
Sitzung. `decide` ist ihnen vorbehalten; ein Mensch kann daneben `author` oder
`review` halten — dann ist er der Autor oder Prüfer des Tickets, und alle
Regeln zu Claim, Übergabe und Snapshot gelten unverändert für ihn.

**Einzelbenutzerbetrieb ist eine Voraussetzung, keine Zufälligkeit.** Das
Datenmodell trägt mehrere menschliche Akteure — Identität, Pflichten,
`assignee` an jedem Ticket, das auf einen Menschen wartet —, der Betrieb tut
es nicht: Zwei Menschen mit je eigenem lokalen Dienst auf derselben
Ticketquelle wären zwei Datenbanken über dieselben Tickets und damit genau die
Spiegelung, die 0b ausschließt. Mehrbenutzerbetrieb verlangt einen gemeinsamen
Host samt Authentisierung und ist nicht Teil dieses Vorhabens.

### Kontext bleibt zwischen den Turns erhalten

Im Normalbetrieb arbeitet Developer in seiner bestehenden Sitzung weiter.
Der nächste Review wird ebenso als neuer Turn der bestehenden Verifier-
Sitzung gestartet. Beide behalten ihre bisherigen Überlegungen, Entscheidungen
und Befunde im jeweiligen Gesprächskontext. Reports und Checkpoints ergänzen
diesen Kontext; sie ersetzen ihn nicht als Standardbetrieb.

Ein Runner-Prozess kann weiterlaufen oder über eine nachgewiesene Resume-
Funktion dieselbe Sitzung erneut öffnen. Entscheidend sind erhaltene Sitzung
und Verlauf, nicht die Lebensdauer eines bestimmten Prozesses. Der Adapter
muss Sitzungskennung, Turnstart, Turnende und Wiederaufnahme nachweisen.
Er darf fehlgeschlagenes Resume nicht still durch einen leeren Chat ersetzen.

Beim Wechsel des Tickets oder Review-Snapshots benennt der neue Turn den
aktuellen Auftrag und Stand ausdrücklich. Alter Gesprächskontext ist keine
frische Testevidenz. Der Prüfer muss Befunde weiterhin am aktuellen Snapshot
belegen. Vor jedem Turn wird der fixierte Stand validiert — bei `code`
Arbeitsverzeichnis und Commit, bei `document` der gespeicherte Inhalt samt
Hash; die dauerhafte Sitzung berechtigt nicht zur Arbeit am alten Stand.

Sitzungswechsel ist ein kontrollierter Ausnahmeweg bei nicht wiederherstellbarer
Sitzung, erreichter konfigurierter Kontextgrenze, Kontextproblemen oder
ausdrücklichem Auftrag: laufende Arbeit sichern,
Checkpoint und offene Reports speichern, Grund dokumentieren, Ersatzsitzung
initialisieren und Zuordnung aktualisieren. Die UI zeigt den Wechsel.
Reviewverbrauch, Claims und offene Findings bleiben erhalten. Vollständig
verlustfreie Kontextübernahme wird nicht behauptet. Verdichtung durch den
Provider kann ebenfalls Information verlieren; bekannte Verdichtungsereignisse
und Kontextwerte werden mit Quelle ausgewiesen, Unbekanntes nicht erfunden.

### Konfigurierbare Kontextgrenze und verantwortlicher Auslöser

Der Dienst überwacht in M2 den aktuell belegten Kontext je Agentensitzung anhand
der vom Adapter gelieferten Messwerte. Nicht die KI muss selbst bemerken, dass
ihre Sitzung zu groß wird. `context_limit_tokens` ist eine positive, vom Menschen
einstellbare Betriebsschwelle auf Projektebene mit optionalem Agent-Override;
CLI und Web zeigen Wert, Herkunft, letzten Messwert und Messzeitpunkt. Für den
Automatikbetrieb wird diese Schwelle ausdrücklich konfiguriert. Etwa 100.000
Tokens sind ein möglicher Erfahrungs-/Versuchswert, keine allgemeingültige
Qualitätsgrenze und kein behauptetes technisches Kontextfenster eines Modells.

Vor jedem neuen fachlichen Turn und bei verfügbaren Kontextereignissen prüft
der Dienst die Schwelle. Bei Erreichen markiert er die Sitzung dauerhaft als
wechselbedürftig und startet darin keine neue fachliche Aufgabe. Laufende Arbeit
endet geordnet mit einer gültigen Ticketübergabe oder einem Checkpoint; ein
offenes Ticket muss dafür nicht vollständig fertiggestellt werden. Der Adapter
fordert den Abschluss über seinen nachgewiesenen Steuerungsweg an. Ist kein
Eingriff im laufenden Turn möglich, wird spätestens am Turnende gewechselt.
Eine Begrenzung mitten im Modellrequest wird damit nicht garantiert; die
Betriebsschwelle muss Raum für Abschluss und Checkpoint lassen. Ein separater
Turn-Timeout bleibt wirksam. Fehlt ein brauchbarer gesicherter Zwischenstand,
anhalten und menschlichen Bedarf anzeigen, statt die Sitzung blind zu löschen.

Nach dem gesicherten Abschluss führt der Dienst den bereits beschriebenen
kontrollierten Sitzungswechsel aus. Er dokumentiert Messwert, Schwelle und Grund,
bindet die Ersatzsitzung an denselben Agenten und übergibt Checkpoint, Snapshot,
offene Findings und relevante Entscheidungen. Alte Sitzungsreferenz und Verlauf
bleiben nachvollziehbar. Erst nach erfolgreicher Initialisierung wird fachliche
Arbeit fortgesetzt. Reviewverbrauch bleibt erhalten. „Clear“ bedeutet diesen
kontrollierten Wechsel, keine verlustfreie Übertragung des gesamten Gesprächs.

Fehlt ein verlässlicher aktueller Kontextwert, darf der Dienst weder kumulierte
Abrechnungstoken als Ersatz verwenden noch eine eingehaltene Grenze behaupten.
Das gilt auch für veraltete oder ausgefallene Messungen. Adapterfähigkeit und
Webanzeige nennen dann ausdrücklich: „Automatische Kontextgrenze nicht verfügbar;
Sitzungswechsel manuell auslösen“. Der menschliche Wechselweg bleibt zugänglich.
Ein bereits ausgelöster Wechsel wird durch fehlende Messwerte nicht aufgehoben.

### Dritte/vierte KI und zwei Codex-Instanzen

Nach M2 kann ein Ticket zusätzlich `codex-ux` oder einen anderen Spezialisten
benötigen. Alternative Zusatzrollen sind ein gezielter Migrations-/Security-
Verifier oder ein Planner vor der Umsetzung. Der erste Ausbau bevorzugt
einen spezialisierten zusätzlichen Verifier; keine allgemeine Agentenhierarchie.

Vor der Übergabe stehen im Ticket die konkreten Pflichtprüfer und beratenden
Agenten fest; der Dienst friert diese Zuordnung für die Übergabe ein.
Alle Pflichtprüfer erhalten denselben Snapshot und arbeiten in separaten
Review-Worktrees mit eigenen Testressourcen. Parallelität ist nur zwischen
verschiedenen Sitzungen möglich. Jeder Report nennt Autor-ID und Spezialisierung.

Der Dienst sammelt alle Pflichturteile und gibt genau eine gebündelte Rückgabe
an den Developer. Freigabe setzt Zustimmung aller Pflichtprüfer voraus.
Beratende Reports sind sichtbar, werden aber nicht nachträglich zu einem
unangekündigten Gate. Ein fehlender Pflichtprüfer bleibt als Hindernis sichtbar;
Timeout ist keine Zustimmung. Bei Produktänderung entsteht eine neue Übergabe,
auf die alte Urteile nicht automatisch übertragen werden.

Mehrere Prüfer desselben Snapshots zählen gemeinsam als **eine Review-Runde**.
Widersprüche werden durch eine gezielte Gegenprobe geklärt; bleibt ein Streit
offen, entscheidet der Mensch. Keine Mehrheitsabstimmung über fachliche Wahrheit
und keine eigenständigen endlosen Nebenrunden zwischen Prüfern.

Die Agenten sehen relevante fremde Reports und Entscheidungen über den Dienst,
ihre Gesprächsverläufe bleiben getrennt. Ein aktiver Developer bleibt die
Schreibregel. Zwei implementierende Instanzen würden zusätzlich getrennte
Arbeitspakete, Branches und Integration benötigen und gehören nicht zu diesem
Ausbau. Auch zwei Instanzen desselben Modells dürfen getrennte Verifier sein;
das garantiert keine Vielfalt der Modellfehler.

## 1b. Tokenfreies Worker-Polling und Aktivierung bestehender Sitzungen

**Verbindliche Präzisierung:** Die regelmäßige Prüfung auf Arbeit ist gewöhnlicher
Programmcode außerhalb der KI. Sie startet keinen Modellaufruf, keinen KI-Turn
und keinen Prompt zum Lesen einer Statusdatei. Leerlaufprüfungen verbrauchen
damit keine Modell-Tokens; lokale Prozess-, Netzwerk- und DB-Arbeit fällt an.
Eine KI regelmäßig per Loop oder Scheduler „Gibt es Arbeit?“ fragen zu lassen,
erfüllt diesen Vertrag nicht. Datei statt SQLite oder MCP statt Dateizugriff
allein spart keine Tokens, wenn weiterhin das Modell die Prüfung übernimmt.

### Drei getrennte Aufgaben

| Baustein | Verantwortung |
|---|---|
| Workflow-Server mit SQLite | Aufträge, Zustände, Claims, Sitzungszuordnungen, Reports und Verlauf dauerhaft verwalten; CLI, MCP und Web greifen über denselben Dienst darauf zu |
| Worker je Agent | Ohne KI nach ausführbarer Arbeit fragen, einen Auftrag atomar übernehmen und seinen Start koordinieren; darf als Schleife im Dienst laufen und braucht keinen eigenen OS-Prozess |
| Laufzeitadapter | Den übernommenen Auftrag als neuen Turn der gebundenen KI-Sitzung starten, Start/Ende beobachten und Wiederaufnahme ermöglichen |

SQLite ist die zentrale Ablage, Markdown bleibt lesbarer Reportexport. Nur der
Dienst schreibt die Workflow-DB; die Agenten verwenden MCP-Werkzeuge für
Auftragsdetails und Ergebnisabgabe. SQLite aktiviert selbst keine KI-Sitzung.
Auch ein Dateiwächter benötigt dafür noch einen Laufzeitadapter.

Der Worker fragt zunächst nur nach ausführbarer Arbeit für seine `agent_id`.
Bei leerer Warteschlange wartet er weiter. Statusprüfung und atomare Übernahme
können eine einzige Dienstoperation sein; eine getrennte Vorabprüfung ist keine
Startsperre und ersetzt keinen Claim. Erst nach Übernahme lädt der Worker das
begrenzte Auftragspaket und aktiviert die KI. Weitere Ticketdetails, Prüfbelege
und relevante Reports kann diese anschließend gezielt über MCP nachladen.

```text
Worker → Workflow-Server/SQLite → keine Arbeit → warten (kein Modellaufruf)
                              → Auftrag übernommen
                                  → Laufzeitadapter
                                  → neuer Turn der bestehenden Sitzung
                                  → Ergebnis über MCP an Workflow-Server
```

### Übergabe und zuverlässiger Start

M1 startet jeden Turn noch ausdrücklich manuell. M2 automatisiert denselben
Vertrag: Der Developer meldet eine vollständige Übergabe an den Dienst, der
die zuständige bestehende Verifier-Sitzung aktiviert. Nach dem Review meldet
der Verifier Report und Urteil; bei Korrekturbedarf aktiviert der Dienst die
bestehende Developer-Sitzung. Rollen und Agenten bleiben konfigurierbar.

Der Ablauf ist verbindlich:

1. Ergebnis und Snapshot prüfen. Rollenrechte, aktive Zuordnung, gültigen Claim
   und Rundenlimit prüfen; kein Text „bin fertig“ als ausreichender Handoff.
2. Zustandswechsel und fälligen Folgeauftrag gemeinsam dauerhaft speichern.
3. Ein Worker übernimmt den fälligen Auftrag atomar, nachdem der Dienst
   Verfügbarkeit, Pause, Rechte und wirksame Grenzen geprüft hat. Er aktiviert
   den passenden Agenten über dessen Adapter mit einem neuen Turn derselben
   Sitzung. Ein bereits aktiver Agent erhält keinen zweiten parallelen Turn.
4. Startbestätigung und tatsächlichen Verlauf erfassen. Zustellung ist weder
   Arbeitsbeginn noch Erfolg. Wiederholte Ereignisse werden anhand stabiler
   Auftrags-/Laufkennungen entprellt; Zustandsabschlüsse sind idempotent.
5. Bei Pause, menschlichem Entscheidungsbedarf oder erreichtem Review-Limit
   keinen Folgeauftrag ausführen. Offene Arbeit bleibt sichtbar gespeichert.

Bei einem Absturz zwischen Speicherung und Aktivierung bleibt der Auftrag
erhalten. Bei unklarem Startresultat erst die gebundene Sitzung und ihren
aktiven Turn prüfen, statt blind erneut zu starten. Ein technischer
Kontrolltakt findet liegengebliebene Aufträge. Im ersten automatischen Betrieb
holt reguläres Worker-Polling die gespeicherten Folgeaufträge ab. Die Übergabe
erzeugt das Ereignis und den Auftrag; Polling ist dessen Zustellweg. Kein
zusätzlicher Message-Broker ist dafür im MVP
nötig. Die KI ruft die andere KI nicht unter Umgehung des Dienstes auf.

### Laufzeitanschluss und Start durch den Benutzer

Der Adapter ist selbst zu entwickelnder Verbindungscode. Bei Codex ist
`codex app-server` die vorgesehene Laufzeitschnittstelle: Der Adapter startet
den Prozess, initialisiert die Verbindung, legt einmal einen Thread an und
speichert dessen Kennung. Arbeitsaufträge starten über `turn/start` weitere
Turns dieses Threads; nach Neustart wird er über `thread/resume` wieder geöffnet.
Ein laufender App-Server-Prozess ist noch kein laufender Modellauftrag. Das
Leerlaufpolling bleibt vollständig im Worker außerhalb der Codex-Sitzung.

Das ist keine Fernsteuerungszusage für eine beliebige bereits geöffnete
interaktive Codex-Terminalsitzung. Der Adapter verwaltet die Sitzung; Status,
Ergebnisse und verfügbare Laufereignisse erscheinen im eigenen Webinterface
beziehungsweise in der Terminalausgabe. Eine zusätzlich interaktiv angeschlossene
native Terminaloberfläche ist kein Bestandteil der MVP-Zusage.

Für Claude Code sind Channels ein zu prüfender Anschluss an eine offene,
entsprechend gestartete Sitzung. Die lokale MCP-Brücke reicht ausschließlich
tatsächliche Arbeitsaufträge vom Worker in diese Sitzung weiter. Eigene Channels
sind derzeit experimentell und benötigen besondere Aktivierung; ein gewöhnlicher
MCP-Anschluss allein garantiert keinen Arbeitsstart. Unterstützte Resume-Wege
sind ebenfalls zulässig, wenn sie den Kontextnachweis erfüllen. Die konkreten
Fähigkeiten beider Laufzeiten sind vor Implementierung anhand der offiziellen
Dokumentation und im Vorabnachweis zu bestätigen.
[Claude Channels](https://code.claude.com/docs/en/channels),
[Codex App Server](https://learn.chatgpt.com/docs/app-server)

Ziel der Inbetriebnahme ist ein gemeinsamer Startbefehl für den lokalen Dienst.
Dieser lädt die Konfiguration, startet Worker und verwaltete Laufzeitprozesse
und stellt gespeicherte Sitzungsbindungen wieder her. Die Codex-Anbindung
startet damit den App Server ohne separaten manuellen Start. Falls der gewählte
Claude-Anschluss eine manuell gestartete Channels-Sitzung benötigt, nennt die
Einrichtung diesen zusätzlichen Schritt ausdrücklich. Fehlende Anmeldung oder
Verbindung wird als „Agent nicht verbunden“ angezeigt; Aufträge bleiben erhalten.
Zwei beliebig gestartete KI-Terminals sind nicht automatisch angeschlossen.

### Intervalle, Oberfläche und Nachweis

M2 erhält ein konfigurierbares positives `poll_interval_seconds`, zunächst
mit Standard 5 Sekunden, über dieselbe Datei-/CLI-/Web-Konfiguration. Es ist
vom Zeitplan fachlicher Aufgaben, Wiederherstellungstakt und Turn-Timeout zu
trennen. Bei Verbindungsfehlern begrenzt ein Backoff weitere Versuche, ohne die
KI zur Fehlerprüfung zu aktivieren. Spätere Push-Zustellung oder Long-Polling
können dieses Polling ersetzen; Auftrags- und Sitzungsvertrag bleiben gleich.
Es gibt keinen periodischen KI-Aufruf allein wegen eines abgelaufenen Timers.

Das Web zeigt Worker-Verbindung und letzten erfolgreichen Kontakt getrennt
von ausstehendem Start, aktiver KI-Arbeit und Blockade. Für die M2-Abnahme über
mehrere leere Pollingzyklen nachweisen: keine Turnstarts und keine Modellrequests.
Danach einen Auftrag zustellen und genau einen Turn in derselben Sitzung
belegen. Doppelabholung, Ausfall zwischen Claim und Start sowie unklaren
Startstatus prüfen; ein abgelaufener Claim allein rechtfertigt keinen zweiten
Start, solange der vorherige Turn noch laufen könnte. Das ist die technische
Ergänzung zum bestehenden Kontext- und Wiederanlaufnachweis.

## 1c. OpenCode/OpenRouter und vergleichbare Modellversuche

OpenCode ist ein weiterer Agentenlaufzeitadapter neben Claude Code und Codex.
OpenRouter ist dessen möglicher Modellzugang, nicht selbst die Agentensitzung.
Die Rollen-, Snapshot-, Report-, Kontext- und Rundenverträge gelten unverändert.
Die Implementierung dieses Adapters folgt nach dem bewiesenen M1-Ablauf;
sie ist kein zusätzlicher Pflichtversuch vor M1.

OpenCode dokumentiert die OpenRouter-Anbindung und bietet eine Server-API
mit Nachrichten an eine konkrete Sitzungs-ID, auch asynchron. Damit besteht
ein Integrationsweg für ereignisgesteuerte Fortsetzung. Die tatsächliche
Wiederaufnahme, Ereignisverarbeitung und Kontexttreue sind vor Aktivierung
des Adapters nachzuweisen.
[OpenCode-Provider](https://opencode.ai/docs/providers/#openrouter),
[OpenCode-Server](https://opencode.ai/docs/server/)

### Beispiel eines zusätzlichen Spezialisten

Dieser Ausschnitt gehört später zur Agentenliste des geplanten Schemas:

```yaml
agent_id: security-candidate-a
runtime: opencode
provider: openrouter
model: "<konkrete-verfuegbare-modell-id>"
account_ref: openrouter-experiments
role: verifier
specialization: security
enabled: false
```

Die Modell-ID ist ein ausdrücklich zu ersetzender Platzhalter, kein gültiger
Startwert. `account_ref` verweist auf separat verwaltete Zugangsdaten; der
Schlüssel steht nicht im Ticket oder Konzept. Vor Aktivierung eine tatsächlich
verfügbare Modell-ID, geeignetes Routing, Rechte und Kostenobergrenze festlegen.
Ob dieser Agent beratend oder verpflichtend prüft, wird wie bei anderen
Verifiern pro Ticket und Übergabe festgehalten, nicht aus dem Modellnamen
abgeleitet.

### Sitzung und Werkzeuge

Jeder Versuch hat eine eigene Agent-ID und dauerhafte OpenCode-Sitzung.
Folgeturns desselben Versuchs erhalten deren Kontext. Ein anderes Modell
wird für den Vergleich als separater Kandidat mit eigener Sitzung gestartet;
kein unbemerkter Modellwechsel innerhalb einer laufenden Prüfung.
Bestehende Claude-/Codex-Chats werden nicht als nativ übertragbar angenommen.
Ein bewusster Umzug verwendet den dokumentierten Checkpoint-Weg.

Der Adapter weist MCP-Aufruf, passenden Test-/Browserzugriff, strukturierten
Report, Turnende und Wiederaufnahme nach. Modellfähigkeit und verfügbare
Werkzeuge sind beide erforderlich; eine Security- oder UX-Bezeichnung allein
beweist nichts. Fachliche Rollenrechte gelten auch für OpenCode.

### Ein Modell zuerst beratend beurteilen

1. Neuen Kandidaten zunächst als beratenden Verifier ausführen. Sein Bericht
   darf die bestehende Freigaberegel weder umgehen noch unbemerkt verschärfen.
2. Kandidaten erhalten denselben Snapshot, Anforderungsstand, Prüfauftrag,
   verfügbare Werkzeuge und vergleichbare Zeit-/Aufwandsgrenzen. Bei Vergleich
   von Modellen innerhalb OpenCode bleibt die Laufzeit gleich. Ein Vergleich
   gegen native Claude-/Codex-Laufzeiten bewertet das Gesamtpaket, nicht nur
   das Modell; dieser Unterschied wird im Versuch vermerkt.
3. In einer unabhängigen Erstprüfung keine fremden Findings vorab liefern.
   Anschließend Belege und Gegenproben vergleichen: echte zusätzliche Fehler,
   übersehene vorbereitete Fehler, Fehlalarme, Werkzeugzuverlässigkeit,
   Qualität der Fortsetzung sowie tatsächlicher Verbrauch und Laufzeit.
4. Ergebnisse pro Kandidat festhalten. Mehr Findings sind nicht automatisch
   besser; für Vollständigkeitsbehauptungen braucht es bekannte Gegenfälle.
5. Erst nach nachvollziehbaren Ergebnissen auf mehreren passenden Fällen
   kann der Mensch den Kandidaten als Pflichtprüfer für bestimmte Tickets
   freigeben. Kein automatisches Modellranking oder umfangreiches Benchmark-
   System als Voraussetzung für diesen kleinen Versuch.

Versuchsläufe erhalten ein eigenes begrenztes Start-/Kostenbudget und dürfen
nicht als unbegrenzte Nebenreviews die Ticketgrenze umgehen. Mehrere Kandidaten
derselben Übergabe zählen fachlich zu einer Runde, ihre Ausführungskosten
werden dennoch einzeln erfasst. Ein beratender Vergleich erzeugt keine eigene
automatische Korrekturschleife mit dem Developer.

### Routing und Kosten nachvollziehbar halten

Modell-ID und konfigurierte Routing-/Fallback-Regeln gehören zum Laufmanifest.
Für Vergleichsläufe keine automatische Modellwahl oder stillen Modellfallback
verwenden. Provider-Fallbacks kontrollieren: OpenRouter kann dasselbe Modell
über unterschiedliche Ausführungsanbieter routen. Konfigurierte Route und
tatsächlich gemeldeten Anbieter getrennt festhalten; Unbekanntes kennzeichnen.
Die konkrete Unterstützung des gewählten Modells und Endpunkts prüfen.
[OpenRouter-Routing](https://openrouter.ai/docs/guides/routing/provider-selection)

OpenRouter-Nutzung ist separat von Claude-/ChatGPT-Abonnementkontingenten zu
erfassen. Nutzungs- und Kostenangaben können über OpenRouters Usage Accounting
bezogen werden; nur tatsächlich gelieferte Werte ausweisen.
[OpenRouter-Usage-Accounting](https://openrouter.ai/docs/cookbook/administration/usage-accounting)

Pro Account und Versuch ein ausdrücklich gesetztes Ausgabenlimit vorsehen.
Prüfung vor jedem neuen Start, begrenzte Parallelität und verfügbare
providerseitige Limits nutzen. Eine nachträgliche Kostenmeldung allein
garantiert kein centgenaues hartes Limit während laufender Requests; diese
Grenze benennen. Bei Budgeterschöpfung Arbeit erhalten und anhalten, statt
zu einem anderen Account oder Modell auszuweichen.

## 2. Vorabnachweis: klein und sequenziell

Kein Serverprodukt bauen, um dessen Ausführbarkeit zu prüfen. Ein Testrepo,
ein kleines nachvollziehbares Fehlverhalten und ein minimaler MCP-Stub genügen.
Der Stub liefert nur die zum Nachweis nötige Antwort; er implementiert noch
keine Ticketdatenbank, Claims oder komplette Workflow-Schnittstelle.

### Kurzer Anschlusscheck beider Laufzeiten vor Versuch 1

Innerhalb der bestehenden Versuchs-Time-Box zuerst bei beiden vorgesehenen
Laufzeiten Verbindung, adressierbaren Turnstart und Resume derselben Sitzung
mit einer kleinen Gesprächsentscheidung prüfen. Den unsichereren Anschluss
zuerst testen, insbesondere einen gewählten experimentellen Channels-Weg.
Hier noch keine fachlichen Tests oder vollständigen Reports bauen. Ein
blockierter Anschluss wird diagnostiziert, bevor in den vollständigen Ablauf
mit nur einer funktionierenden Laufzeit investiert wird. Der Check ersetzt
nicht den fachlichen Kontext- und Rollenbeweis der folgenden Versuche.

### Versuch 1: Kann ein Verifier tatsächlich arbeiten?

Ein Provider startet headless im isolierten Review-Worktree, führt einen
echten Test aus, ruft den MCP-Stub auf und beendet sich ohne interaktive
Rückfrage mit einem strukturell gültigen Problem-Report. Danach einen zweiten
Turn derselben Sitzung auslösen: Eine zuvor nur im Gespräch festgehaltene
Entscheidung muss korrekt berücksichtigt werden, ohne sie erneut einzuspeisen.
Sitzungskennung und beobachtetes Verhalten belegen die Fortsetzung. Daneben prüfen wir
einen Berechtigungsfehler und Prozess-Timeout: kein falsches Erfolgsresultat,
Prozessende erkennbar, Diagnose erhalten.

Zusätzlich bei beiden Turns beobachten, ob die Laufzeit aktuell belegten Kontext
meldet: genaue Feld-/Ereignisnamen, Einheit, Semantik, Quelle, Zeitpunkt und
Aktualisierungstakt festhalten. Aktuellen Belegungswert, Kontextkapazität und
kumulierte Abrechnungstoken getrennt halten; fehlende oder nur geschätzte Werte
benennen. Eine Tokensumme ist ohne belegte Semantik keine Kontextmessung.
In Versuch 2 dieselbe Beobachtung für die zweite Laufzeit ergänzen. Das Ergebnis
bestimmt je Adapter, ob M2 automatisch überwachen kann oder der manuelle
Wechselweg als bekannte Grenze ausgewiesen werden muss.

Nach dem Anschlusscheck ist der erste Provider der lokal einfacher
einsatzbereite. Vor dem Lauf
gewählte Rechte und Voraussetzungen festhalten. Bei einem Fehlschlag genau
zwischen fehlender Konfiguration, vorübergehendem Fehler und nicht unterstützter
Fähigkeit unterscheiden. Nur Letzteres widerlegt diesen konkreten Runner-Weg.
Keine pauschalen Sandbox-Umgehungen, um den Test künstlich grün zu bekommen.

### Versuch 2: Sind die Rollen wirklich vertauschbar?

Erst nach erfolgreichem Versuch 1: Zweiter Provider als Developer im eigenen
Ticket-Worktree; kleine Korrektur und Commit, dann Gegenprüfung. Anschließend
die Providerrollen tauschen. In einer unfertigen Arbeit bewusst einen normalen
Checkpoint erzeugen und in derselben Sitzung fortsetzen, auch nach Wiederaufnahme
der Verbindung beziehungsweise des Runner-Prozesses. Separat den kontrollierten
Ersatz durch eine neue Sitzung mit Checkpoint als Wiederherstellungsweg prüfen.

Je Versuch maximal einen halben Arbeitstag als Erkenntnis-Time-Box einplanen,
nicht als Erfolgsgarantie. Übrig gebliebene Prüfungen werden benannt. Am Ende
steht entweder ein bewiesener Ausführungsweg oder ein konkretes Hindernis;
weitere Infrastruktur entsteht daraus nicht automatisch.

Der bevorzugte M1-Weg sind danach nachgewiesene Runner mit dauerhafter
Sitzungsbindung oder zuverlässigem Resume. Ein CLI-Aufruf ohne erhaltenen
Kontext erfüllt die Anforderung nicht. Ein reduzierter Polling-Weg ist nur
zulässig, wenn auch er dieselbe Sitzung fortsetzt; sonst ist die fehlende
Fähigkeit eine offene Produktentscheidung. Automations- und Webausbau warten
auf den Nachweis.

## 3. M1: der eigentliche MVP

**Ein manuell gestartetes Ticket durchläuft Umsetzung, unabhängiges Review,
lesbaren Fehlerbericht, Korrektur und Gegenprüfung.**

| Bestandteil | Kleinster Umfang |
|---|---|
| Projekt | Ein separates Testrepo, ein menschlicher Akteur, ein lokaler Dienst |
| Rollen | Ein `author` und ein `review`, Zuordnung aus der Konfigurationsdatei; `config show` zeigt wirksame Werte |
| Ticketquelle | Dateiadapter, ein konfigurierter Ordnerpfad, voller Kanban-Zyklus lesbar; automatisiert nur Bereit → In Arbeit → Review → Abnahme |
| Ausführung | Ein expliziter CLI-Auftrag je Turn in derselben Agentensitzung; kein periodischer Timer und keine automatische Folgerunde |
| Arbeitsverzeichnisse | Bei `code` eigener Autoren-Ticket-Worktree und eigener detached Review-Worktree; bei `document` keiner. Mensch-Checkout bleibt unberührt und ist nie die Ticketablage |
| Zustand | Kleine lokale Persistenz, stabile Ticket-/Lauf-/Akteurs-IDs, `next_step`, persistente Sitzungszuordnung, ein aktiver Turn pro Akteur, wiederholbarer Abschluss |
| Snapshot | Bei `subject_kind: code` Basiscommit, Commit und Tree; bei `document` gespeicherter Inhalt mit Hash. Anforderungsstand fixiert, Drift geprüft |
| MCP | Minimaler vertikaler Vertrag: Auftrag übernehmen sowie Ergebnis oder Checkpoint abgeben; Operationen nach dem Beweisweg zuschneiden |
| Report | Pflichtbericht mit Finding-IDs, Evidenz, Korrekturstand und Markdown-Download; `withdrawn` für falsche Befunde |
| Lernen | Belege und Lernvorschläge im Report; vorhandene kuratierte Muster werden mitgegeben, zunächst manuell gepflegt |
| Web | Eine lesbare Übersicht und Reportdetail: Ticket, Rolle, Status, letztes Ereignis, offene Findings, **Wartet auf dich** |
| Grenzen | Konfigurierbares Review-Limit (Standard 3), Turn-Timeout, kontrolliertes Laufende, Checkpoint und kontrollierter Sitzungswechsel |

Die Persistenz verwendet SQLite; kein allgemeines Event-Sourcing-Framework
oder Plugin-System. Doppelte Ergebniszustellung darf weder zwei Reports
erzeugen noch das Urteil mehrfach weiterschalten. `completed` bedeutet allein
noch keine Freigabe: Der konkrete Ergebnisinhalt und Rollenrechte entscheiden.

„Wartet auf dich“ zeigt mindestens Produktfragen, strittige Befunde und
ausstehende menschliche Abnahme. Im M1 reichen eine lesbare Begründung und
ein dokumentierter manueller Entscheidungsweg. KI-Prüfung füllt keine
Human-Spalte; M1 benötigt dafür noch keinen vollständigen Admin-Webdialog.

### M1-Abnahme

1. Ein kleines Ticket mit klarer Akzeptanz und Gegenfall wird umgesetzt und
   als konkreter Commit übergeben.
2. Der Verifier findet einen vorbereiteten Fehler; der Report ist im Browser
   ohne Kenntnis des Chats verständlich und als Markdown herunterladbar.
3. Der Developer korrigiert mit Bezug auf die Finding-ID. Die Gegenprüfung
   bestätigt den neuen Snapshot; die vorherige Beobachtung bleibt erhalten.
4. Die Webübersicht zeigt das Ergebnis und die ausstehende menschliche
   Entscheidung. Der menschliche Checkout wurde nicht verändert.
5. **Quellenkonflikt:** Ein Mensch verschiebt das Ticket während eines
   laufenden Auftrags. Der Auftrag wird ausgesetzt, der Konflikt ist sichtbar,
   nichts wird stillschweigend zurückgeschoben und kein Turn startet neu.
6. **Ungültiger Quellenstand:** Dieselbe Identität liegt in zwei Ordnern; beide
   sind gesperrt. Ein Ticket in `Erledigt` ohne Belege zeigt den Widerspruch.
7. **Dokumentticket:** Ein Ticket mit `subject_kind: document` durchläuft
   denselben Weg ohne Produktcode-Commit und ohne Testlauf. Der Report weist
   Widerspruch, betroffene Regel und Gegenfall als Belege aus und behauptet
   keinen bestandenen Test.
8. **Wiederanlauf:** Der Dienst wird zwischen Quellschreiben und
   DB-Bestätigung beendet. Nach dem Start wird die gespeicherte Absicht gegen
   den tatsächlichen Quellstand aufgelöst, ohne eine zwischenzeitliche
   menschliche Änderung zu überschreiben und ohne Auftrag doppelt zu starten.
9. **Vorschlag und Abnahme:** Die gültige Dokumentfassung bleibt während
   Bearbeitung und Prüfung unverändert lesbar. Entsteht nach der Prüfung eine
   weitere Fassung, gilt die Freigabe der geprüften nicht für sie. Scheitert
   die Übernahme nach der Abnahme, bleibt die Entscheidung erhalten, der
   Fehler ist sichtbar, und der Dienst meldet keinen erfolgreichen Abschluss.
10. **Bearbeitungsmodus:** Solange ein Turn läuft, wird die Pause nicht
    bestätigt. Im bestätigten Modus bleibt ein direkter Zug nach
    `Zurückgestellt` bei der Wiederaufnahme erhalten und startet keinen
    Auftrag. Ein Neustart hebt den Modus nicht auf. Eine doppelte Identität
    verhindert die Wiederaufnahme.

Die im Vorabnachweis geprüfte Vertauschbarkeit wird bei der Anbindung beider
Runner erhalten. Einmalige Gegenproben für doppelte Abschlusszustellung,
unvollständigen Report und Wiederaufnahme sichern diesen kleinen Ablauf ab.
Die Limit-Gegenprobe prüft mindestens die Werte 3 und 5: Start von Runde N+1
nach N nicht freigegebenen Runden abweisen, auch nach Prozess- oder
Sitzungswechsel. Eine Projektänderung oder Ticket-Ausnahme ändert das
wirksame Limit, niemals den Verbrauch. Nur eine dokumentierte menschliche
Erweiterung erlaubt die zusätzlich freigegebenen Runden. Zwei Fälle gehören
ausdrücklich dazu: Zurückstellen und Wiedereröffnen bei erschöpftem Budget
bleibt gesperrt, und nach einer Erweiterung folgt zuerst die Autorenkorrektur
mit neuer Übergabe, nicht ein zweites Review desselben Standes.
Das sind keine zusätzlichen Produktsubsysteme.

### Verbrauch und Kontingente ohne feste Annahme über die Rollen

Der Benutzer betreibt derzeit nach eigener Angabe Claude mit einem 20-$- und
Codex mit einem 100-$-Account. Das ist ein Einsatzbeispiel, keine benötigte
Tarifkombination und keine Aussage über aktuelle Produktpreise. Monatspreis,
verfügbare Nutzung, Abrechnungstoken und aktuell belegter Kontext sind
unterschiedliche Größen. Aus dem Preisverhältnis folgt kein Tokenverhältnis.

Ein Verifier erzeugt möglicherweise weniger Code, kann aber viel Kontext lesen,
Tests auswerten und in mehreren Runden erneut prüfen. Der Entwurf setzt daher
nicht voraus, dass Verifikation weniger Kontingent benötigt als Entwicklung.
Ob die größere Kapazität dem Developer mehr nützt, wird an vergleichbaren
Tickets einschließlich Reviewqualität und nötiger Nacharbeit beurteilt.

M1 protokolliert je Lauf und Agent verfügbare Nutzungsdaten mit Quelle:
Input-/Output- und gegebenenfalls Cache-/Reasoning-Werte nach Providersemantik,
Laufdauer und erkannte Nutzungslimits. Zusätzlich den aktuell belegten Kontext
und gegebenenfalls die Kontextkapazität separat mit Messzeitpunkt und der im
Vorabnachweis geklärten Semantik protokollieren und in der lesbaren Übersicht
anzeigen. Fehlende Werte bleiben unbekannt; M1 löst noch keinen automatischen
schwellenbedingten Sitzungswechsel aus.
Keine doppelte Summierung kumulierter Sitzungswerte und keine Umrechnung von
Abonnementnutzung in vermeintlich exakte API-Kosten. M2 macht diese Daten je
Agent und Ticket sichtbar; das ist keine Voraussetzung für eine neue
Abrechnungsplattform im MVP.

Mehrere Agenten mit demselben Account sind getrennte Sitzungen, erhalten
dadurch aber nicht automatisch getrennte Kontingente. Die Konfiguration kann
eine nicht geheime `account_ref` zur Gruppierung verwenden; die tatsächlichen
Grenzen richten sich nach der jeweiligen Anmeldung und dem Provider.
Bei erschöpftem Kontingent Arbeit erhalten und Wartezustand samt bekannter
Resetzeit anzeigen. Kein stiller Wechsel zu kostenpflichtiger API-Nutzung,
anderem Account, Modell oder einer neuen kontextlosen Sitzung.

Die geplante Rollen-/Modellkonfiguration erlaubt einen bewussten Wechsel
zwischen Tickets nach gemessener Auslastung. Ein Providerwechsel übernimmt
keinen fremden nativen Sitzungskontext: dafür gilt der dokumentierte
Checkpoint-/Sitzungswechselweg aus Abschnitt 1a.
[OpenAI-Nutzung und Preise](https://learn.chatgpt.com/docs/pricing),
[Claude-Nutzungsgrenzen](https://support.claude.com/en/articles/11647753-how-do-usage-and-length-limits-work)

## 4. M2: vollständiger lokaler Arbeitsbetrieb

Die ursprünglichen Pflichtanforderungen bleiben bestehen. Folgendes ist aus
dem Test-MVP verschoben, nicht gestrichen:

- Automatische Folgeaufrufe nach Abschnitt 1b: Worker prüfen ohne Modellaufruf
  auf gespeicherte Aufträge und aktivieren nur bei Arbeit den Laufzeitadapter.
  Einmaliger Lauf, Pause und kontrollierter Abbruch. Worker-Pollingintervall,
  fachliche Zeitpläne und Wiederherstellungstakt bleiben getrennt konfigurierbar.
- CLI-/Web-Konfiguration für dieselben wirksamen Agenten-, Rollen-,
  Laufzeit-/Modellzugangs-, Spezialisierungs-, Review-Limit-, Kontextgrenz- und Timerwerte.
- Kontextüberwachung und schwellenbedingter kontrollierter Sitzungswechsel nach
  Abschnitt 1a; bei fehlender verlässlicher Messung sichtbarer manueller Wechselweg.
  Abnahme mit kleiner Testschwelle: Überschreitung führt zu Abschluss/Checkpoint
  und Ersatzsitzung, nicht zu einer neuen Fachaufgabe in der alten Sitzung.
  Fehlende/veraltete Werte und Neustart bei vorgemerkt anstehendem Wechsel prüfen;
  Reviewzähler und offene Findings bleiben erhalten.
- Ergänzende Konvergenzanzeige und Start-/Zeitbudgets für die Automation;
  das feste Review-Rundenlimit besteht bereits in M1.
- Authentisierter menschlicher Entscheidungsweg mit Herkunftsnachweis;
  keine behauptete OS-Isolation gegen gleichberechtigte lokale Prozesse.
- Versionierter Export-Branch, sichtbare Exportfehler, konsistente DB-Sicherung
  und bewiesene Wiederherstellung vor Übernahme realer Arbeitsdaten.
- Bequeme Musterkuratierung und nachvollziehbare Einbindung in Folgeaufträge.

Eine dritte/vierte KI und parallele Pflichtprüfer folgen nach dem Zwei-Agenten-
Betrieb gemäß Abschnitt 1a; mehrere Projekte bleiben eine spätere Erweiterung.
IDs, Sitzungsbindungen und Revisionen pro Objekt verhindern frühe Sackgassen,
ohne diese Ausbaustufen bereits zu implementieren.
OpenCode/OpenRouter ist ebenfalls eine Anschlussstufe nach M1. Der Adapter
verwendet die bestehenden Operationen und kann nach seinem eigenen Nachweis
eine Rolle übernehmen oder als zusätzlicher Spezialist aktiviert werden.
Er verändert weder M1-Abnahme noch das Review-Limit.

## 5. Inbetriebnahme und weiterer Konzeptreview

M1 verwendet ausschließlich ein separates Testrepo. Reale Arbeitsprojekte
werden erst nach dem Abnahmelauf und den nötigen Betriebsvoraussetzungen
aus M2 angebunden. Ein Import- oder Migrationssystem ist keine Voraussetzung
für die Umsetzung dieses Projekts.

Im Serverbetrieb ist die DB für den technischen Ausführungszustand maßgeblich.
Tickets werden in genau einer führenden Quelle nach Abschnitt 0b gepflegt.
Markdown-Reports sind lesbare Exporte; direkte Änderungen an diesen Reports
sind keine Zustandsänderungen des Dienstes. Dateisystem-Tickets sind dagegen
bearbeitbare Quelldaten und ausdrücklich keine bloßen Exporte.
Vor der ersten Nutzung mit realen Arbeitsdaten müssen Snapshot-Zuordnung,
Human-Einträge, offene Findings und Wiederherstellung nachweislich funktionieren.

### Offene Produktentscheidungen

Der übrige Text ist entweder von Mike entschieden oder ein Vorschlag; die
Zuordnung steht im Abschnitt „Herkunft der Regeln". Die folgenden Punkte
hängen an Mike, weil jede Antwort konsistent umsetzbar wäre und die Wahl eine
Präferenz ist, kein Sachzwang:

1. **Darf eine KI `Bereit` setzen, oder ist Triage menschlich?** Empfehlung:
   menschlich. `Bereit` heißt „Anforderungen sind klar" — das ist das Urteil,
   gegen das später geprüft wird.
2. **Ist die Automatik pro Ticket opt-in oder opt-out?** Empfehlung: opt-in,
   solange Kontingente knapp sind.
3. **Werden mehrere schreibende Rollen je Ticket überhaupt unterstützt?**
   Empfehlung: vorerst nein; ein zweiter Schreiber bekommt ein eigenes Ticket.
4. **Wie wird ein auf GitHub geschlossenes Issue ohne Labelwechsel behandelt?**
   Vertraglich ist es ein ungültiger Quellenstand. Ergonomisch wäre eine
   Rückfrage „als Erledigt oder Verworfen übernehmen?" freundlicher. Empfehlung:
   Konflikt in M1-Nähe, Rückfrage erst mit dem GitHub-Adapter.
5. **Darf direkt in der Ticketquelle bearbeitet werden, während der Dienst
   arbeitet — oder nur im pausierten Bearbeitungsmodus?** Das ist eine
   Einschränkung der Entscheidung „Menschen können die führende Quelle direkt
   bearbeiten" und deshalb Mikes. Empfehlung: Bearbeitungsmodus, weil die
   Alternative eine Zusage über gleichzeitige Editor-, Git- und Dienstzugriffe
   wäre, die kein lokaler Dienst einhalten kann. Der Preis ist gering: In M1
   startet ohnehin jeder Turn von Hand, und der Modus kostet dort einen
   CLI-Befehl. Wirksam wird die Einschränkung erst mit der Automation in M2.

### Konvergenzgrenze für dieses Konzept

Der Entwurf hat drei Reviewrunden verbraucht, ohne dass ein einziger Turn
einer echten Agentenlaufzeit gelaufen wäre. Genau dieses Muster hat in T-21
zweiundfünfzig Runden gekostet, und die Leitplanke daraus lautet: Nennt ein
Vorhaben einen Erfolgsweg, muss dieser Weg **einmal durchgelaufen** sein,
bevor die Vorarbeiten weiterlaufen — als dünnstes lauffähiges Skelett,
hartverdrahtet und hässlich erlaubt.

**Empfehlung, nicht Beschluss:** den Anschlusscheck beider Laufzeiten als
nächsten Arbeitsauftrag vorziehen und weitere Konzeptarbeit an Verträgen
zurückstellen, die der Vorabnachweis ohnehin bestätigen oder widerlegen wird.
Ob die Konzeptrunden weiterlaufen, entscheidet Mike; ein Anschlusscheck
beendet sie nicht von selbst und bestätigt auch keinen der fachlichen
Verträge hier. Er entscheidet Werkzeugdetails mit Evidenz — mehr nicht,
aber das ist derzeit das Einzige, was überhaupt niemand weiß.
