# Antwort auf die Stellungnahme · Runde 2

Stand: 6. September 2026. Bezug:
[Stellungnahme](agent-workflow-server-concept-response.md),
[Review Runde 1](agent-workflow-server-concept-review.md),
[Konzept](agent-workflow-server-concept.md).

Auftrag laut Abschnitt 3 der Stellungnahme: nur konkrete Widersprüche,
fehlende Pflichtanforderungen und zu großer MVP-Scope. Je Punkt entweder
einverstanden oder ein konkreter Gegenfall mit kleinerer Alternative.
Stilfragen und Zukunftserweiterungen bleiben draußen.

## Zuerst: vier Korrekturen an mir, die zutreffen

Nicht aus Höflichkeit vorangestellt, sondern weil drei davon meine eigenen
Formulierungen als das entlarven, was die Review anderswo kritisiert.

1. **„Unveränderlichkeit per Konstruktion" war falsch.** Eine Ref ist per
   `git update-ref` veränderbar, ein detached Worktree nicht schreibgeschützt.
   Unveränderlich ist der gespeicherte Objekt-Hash; die Ref hält den Stand nur
   erreichbar. Die Stellungnahme formuliert das korrekt, ich nicht.
2. **„Praktisch unverlierbar" über die Git-Historie war dieselbe
   Überzeichnung.** Ein lokales Repo überlebt keinen Plattenausfall. Der
   Einwand trifft, und die Konsequenz — DB-Sicherung plus Wiederherstellungs­probe
   statt Export als Ersatzsicherung — ist richtig.
3. **Die Kontextmessung war bei mir zu grob.** Kumulierte Abrechnungstoken,
   aktuell belegter Kontext und Agentenschätzung sind drei Größen. Ein
   sinkender Wert ist ein *Hinweis* auf einen Reset, kein Beweis für
   Compaction — mein „messbar" hat mehr behauptet, als es einlöst.
   `unknown` als zulässiger Wert mit Quelle und Zeitpunkt ist die bessere Form.
4. **Die Abnahmeprobe des Checkpoints war zu scharf geschnitten.** „Frische
   Sitzung ohne Rückfragen" hätte eine legitime neue Produktentscheidung als
   Checkpoint-Fehler gewertet. Die Präzisierung — nur *bereits verfügbare, im
   Checkpoint verlorene* Information ist ein Fehler — ist die richtige Grenze.

## Urteil je Befund

| Nr | Entscheidung der Stellungnahme | Mein Urteil |
|---|---|---|
| 1 · Snapshot | Commit/Tree fixieren, Review-Worktrees, Laufmanifest | Einverstanden. Ein Punkt fehlt: der **Developer** braucht ebenso einen eigenen Worktree → A |
| 2 · Ausführung | Vorabnachweis vor Ausbau, beide Provider, Rollentausch | Im Prinzip einverstanden, Gegenfall zum Zuschnitt → B |
| 3 · Revision | Revision je Objekt, Urteil separat transaktional | Einverstanden, kein Einwand |
| 4 · Mensch-Grenze | Getrennte Zugänge, keine Isolationsbehauptung | Einverstanden, die Korrektur an meiner Formulierung trifft |
| 5 · Konvergenz | Halt nach drei `changes_requested`, konfigurierbar | Einverstanden im Ziel, Zählweise ist der Gegenfall → C |
| 6 · Haltbarkeit | Getrenntes Audit-Repo, Exportauftrag, DB-Backup | Mechanik einverstanden, Ort kostet eine Zusage aus Stufe 1 → D |
| 7 · Kontext | Frische Läufe, Fortsetzungsweg, ehrliche Telemetrie | Richtung einverstanden, aber die Konsequenz ist nicht zu Ende gezogen → E |
| 8 · `withdrawn` | Mit Begründung, einmal Gegenprobe, dann Mensch | Einverstanden, kein Einwand |

Dazu drei Befunde zum MVP selbst → F, G, H.

---

## A · Der Developer-Runner braucht denselben Worktree-Mechanismus

**Gegenfall.** Der MVP schreibt „ein aktiver Produkt-Schreiber" fest und lässt
den Dienst gleichzeitig einen Developer-Runner starten. In StockInfo arbeitet
Mike im selben Checkout. Damit gibt es zwei Schreiber, und die Einschränkung
aus Abschnitt 5 des Konzepts — „eine Serversperre verhindert nicht, dass eine
unabhängig geöffnete Shell Quelldateien ändert" — trifft jetzt einen Prozess,
den der Dienst **selbst** gestartet hat. Das ist eine andere Qualität als eine
fremde Shell: dafür ist er verantwortlich.

**Kleinere Alternative.** Die Maschinerie existiert für den Verifier bereits.
Regel: *Kein vom Dienst gestarteter Runner teilt sich ein Arbeitsverzeichnis
mit dem Menschen.* Damit wird „ein aktiver Produkt-Schreiber" von einer
Absichtserklärung zu einer Eigenschaft des Aufbaus — ein Arbeitsverzeichnis je
Rolle, geteilt wird der Branch, nicht der Baum.

Eine Fußangel gehört gleich in den Vorabnachweis, sonst wird sie erst in der
Implementierung entdeckt: Git verweigert denselben Branch in zwei Worktrees.
Der Developer-Runner braucht also entweder den Ticket-Branch exklusiv (und der
Mensch bleibt davon weg) oder einen detached Stand mit anschließendem
Fast-Forward durch den Dienst. Welche Variante, entscheidet der Versuch.

## B · Der Vorabnachweis ist richtig, sein Zuschnitt widerspricht seiner Zeitgrenze

**Gegenfall.** Fünf Schritte über zwei Provider, mit echtem Test, gültigem
Report, Developer-Korrektur, vollem Rollentausch, MCP-Aufruf, fehlender
Berechtigung, Timeout und frischer Fortsetzung — auf einen halben Arbeitstag.
Das ist genau die scheinpräzise Zeitzusage, die das Konzept an anderer Stelle
zurecht vermeidet. Die Zeitgrenze ist als Abbruchregel richtig; die Ladung
passt nicht hinein.

Zweitens baut der Nachweis das Experiment zur Plattform aus, wovor er selbst
warnt: Ob der Runner MCP erreicht, beantwortet ein Stub-Server. Dafür den
Workflow-Vertrag zu benutzen, verschiebt Kernarbeit in den Spike.

**Kleinere Alternative.** Sequenzieren statt bündeln, weil Versuch 2 nur
zählt, wenn Versuch 1 gelingt:

- **Versuch 1 — die architekturentscheidende Frage.** Ein Provider, Rolle
  Verifier: Läuft er headless mit den vorgesehenen Rechten, führt einen echten
  Test aus, erreicht einen MCP-Stub und endet ohne interaktive Rückfrage mit
  einem strukturell gültigen Report? Scheitert das, ist `managed_runner` tot
  und die Client-Polling-Entscheidung fällt sofort — ohne den zweiten Versuch.
- **Versuch 2 — die Vertauschbarkeit.** Zweiter Provider, Developer-Rolle,
  Korrektur mit Commit, dann Rollentausch. Erst hier braucht es das
  Worktree-Thema aus A.

Fehlerpfade (Berechtigung, Timeout, Fortsetzung) hängen an Versuch 1, nicht an
beiden. Die halbe-Tag-Grenze gilt dann je Versuch und ist plausibel.

## C · „Drei erfolglose Runden" zählt der MVP falsch

**Gegenfall.** Die Setup-Datei zählt *inhaltlich* erfolglose Runden und
schließt formale Transportfehler ausdrücklich aus. Die Stellungnahme
übernimmt den Ausschluss, zählt aber rohe `changes_requested`. Eine Runde, in
der von fünf blockierenden Findings vier geschlossen wurden und ein kleines
neues auftauchte, ist Fortschritt — sie sieht in diesem Zähler aus wie
Stillstand. Gesunde Tickets halten bei Runde 3 an, und da der Halt „Mensch
entscheidet" bedeutet, ist der Preis Mikes Zeit.

**Kleinere Alternative.** Nicht Runden zählen, sondern die Bewegung, die der
Dienst ohnehin in der Finding-Tabelle stehen hat: Eine Runde ist erfolglos,
wenn sie die Zahl der offenen **blockierenden** Findings nicht senkt.
Drei solcher Runden hintereinander halten an. Das braucht kein Urteil eines
Modells, ist aus vorhandenen Daten berechenbar und trifft den Fall, den die
Regel meint. Meine Runde-1-Formulierung („Rundenzähler mit Schwelle") war
hier genauso ungenau — der Zähler ist das Falsche, die Richtung ist das
Richtige.

## D · Das getrennte Audit-Repo kostet eine Zusage aus Stufe 1

**Gegenfall.** Die Begründung gegen Autocommits im Produktbranch überzeugt
(Entwicklerzustand, Index, Snapshot-Linie). Der gewählte Ort tut es nicht: Im
Dateimodus liegen die Reports unter `_tickets/reports/` **im Projekt** — wer
das Repo klont, hat sie. Genau das ist die Portabilitätszusage von Schritt 1
(„ein Freund kann das Board ohne laufenden Server lesen"). Ein separates
lokales Audit-Repo bricht sie: zwei Repos, und geklont wird nur eines.

**Kleinere Alternative.** Gleiches Repo, eigener Orphan-Branch
(`agentboard/export`), der nie in ein Arbeitsverzeichnis ausgecheckt wird —
geschrieben über Plumbing, das den Index nicht anfasst. Ergebnis: Der
Produktbranch bleibt unberührt, Entwicklerzustand und Index ebenso, aber
Reports reisen mit dem Klon. Der Exportauftrag in der DB und die Anzeige
„ausstehend/fehlgeschlagen" bleiben unverändert richtig, ebenso das getrennte
DB-Backup mit Wiederherstellungsprobe und einem externen Ziel.

## E · „Frischer Lauf pro Auftrag" macht den Checkpoint zum Normalfall

Das ist mein wichtigster Punkt dieser Runde, und er vereinfacht.

**Gegenfall.** Der MVP legt fest: „frischer Lauf pro Auftrag", jeder Rollenlauf
startet mit einem begrenzten Auftragspaket. Zugleich bleibt der Checkpoint als
Ausnahme beschrieben — „zusätzlich gibt es einen expliziten Fortsetzungsweg",
und die Abnahme prüft einen „**erzwungenen** Checkpoint". Beides zusammen geht
nicht auf: Wenn jeder Lauf frisch startet, endet **jeder** Lauf an einem
Ticket, das noch nicht fertig ist, mit einem Fortsetzungsartefakt. Nicht bei
Kontexterschöpfung — immer. Der Notausgang ist der Hauptausgang.

**Kleinere Alternative, die Arbeit spart statt sie zu schaffen.**

- Ein Lauf endet in genau drei Formen: `handoff` (fertig zur Prüfung),
  `checkpoint` (Arbeit geht weiter, Stand ist beschrieben), `interrupted`
  (abgebrochen, kein Stand). Kein eigener Budget-Sonderweg.
- Damit fällt `context_budget` als *Auslöser* aus dem MVP heraus. Der frische
  Lauf begrenzt den Kontext bereits durch seinen Zuschnitt; was übrig bleibt,
  ist eine Laufzeit- und Startgrenze, die der Dienst ohnehin misst — und die
  die Stellungnahme in Abschnitt 5 schon vorsieht. Die Telemetrie mit Quelle,
  Zeitpunkt und `unknown` bleibt sinnvoll, aber als **Anzeige**, nicht als
  Steuerung. Ein Mechanismus weniger im MVP, ohne die Sache zu verlieren.
- Der Gewinn liegt woanders und wird dadurch täglich geprüft statt einmal in
  einem Abnahmeschritt: Wenn jeder Lauf ein Fortsetzungsartefakt schreibt und
  der nächste Lauf blind davon startet, ist die Checkpoint-Qualität eine
  Dauermessung. Ein mangelhafter Checkpoint fällt sofort auf, nicht bei
  Abnahmeschritt 8.

Die 60/80-%-Schwellen bleiben als das stehen, was die Stellungnahme aus ihnen
gemacht hat — experimentelle Startwerte für den Fall, dass Telemetrie da ist.
Sie tragen im MVP keine Last mehr.

## F · Der MVP-Umfang ist größer, nicht kleiner als der ursprüngliche Stufenplan

**Gegenfall.** Das Konzept sagte: „Keine Provider-Matrix oder fertige
Plattform bauen, bevor Übergabe → Review → Problem-Report → Korrektur einmal
wirklich funktioniert." Die MVP-Tabelle enthält jetzt zwei Runner-Anbindungen,
SQLite mit Claims, sieben MCP-Operationen, Reports mit Export, Musterregister,
drei Webansichten, Start/Pause/Abbruch/Einmallauf/Intervall mit CLI-Parität,
Rundenschwelle, Laufzeit- und Startlimits, Kontextanzeige, Fortsetzung,
versionierten Export, DB-Backup und sichtbare Sicherungsfehler. Das ist der
Inhalt der ursprünglichen Stufen 2, 3 und 4 unter einer Überschrift.

Die zehnschrittige Abnahme bestätigt es: Sie prüft Rollentausch, doppelten
Tick, Checkpoint-Fortsetzung, Konvergenzhalt und Backup-Wiederherstellung —
kein „erstes kleines durchgängiges Ticket" mehr.

**Kleinere Alternative — die Stellungnahme liefert sie selbst.** Ihr letzter
Absatz nennt die Baufolge: „zuerst CLI-Auftrag → Snapshot → Verifier →
Report, dann Korrektur und Gegenprüfung, anschließend die kleine Webansicht
und Timersteuerung." Der erste Abschnitt **ist** der MVP; alles danach ist
M2. Konkret aus der Tabelle nach M2 verschieben:

| Verschieben | Warum das nichts kostet |
|---|---|
| Pause/Abbruch/Intervall | Für den Beweisweg genügt „einmal ausführen"; der Timer gehört zum Runner-Ausbau |
| CLI-Parität für alle Werte | Der Beweis braucht die Operationen, nicht zwei gleichwertige Oberflächen dafür |
| DB-Backup und Wiederherstellungsprobe | Ein Prototyp ohne produktive Daten hat nichts zu verlieren; die Zusage bleibt für M2 verbindlich |
| Musterkuratierung | Am Tag 1 ist das Register leer — Muster brauchen zwei belegte Vorkommen. Die **Mitgabe** im Auftragspaket kostet fast nichts und bleibt drin; der Pflegeweg wartet |
| Konfigurationsansicht im Web | Solange nur Rollen und ein Intervall existieren, reicht die Datei plus `config show` |

Übrig bleibt: ein Ticket, zwei Rollen, Snapshot, Verifier-Lauf, Report im Web
lesbar, Korrektur, Gegenprüfung. Das entspricht Abnahmeschritt 1 bis 4 und
ist der Satz, den das Konzept selbst als Ziel formuliert hat.

## G · Eine Pflichtanforderung fehlt in der MVP-Oberfläche

**Gegenfall.** Anforderung 6 des Auftrags endet mit „**und anstehende
Entscheidungen**". Das Konzept hatte es: „Die Standardansicht zeigt zuerst
offene Probleme und benötigte Entscheidungen." Die MVP-Liste der Stellungnahme
zeigt „Rollen, Status, letztes echtes Ereignis, nächsten Lauf und offene
Findings" — die Entscheidungen fehlen.

Das ist keine Kosmetik, weil die Stellungnahme die Zahl der Wege dorthin
gerade erhöht hat: `blocked`, Konvergenzhalt nach drei Runden, `disputed` ohne
Einigung, akzeptierter Restbefund, menschliche Abnahme. Fünf Arten, auf Mike
zu warten — und ohne diese Ansicht wartet das System still, was den
Hauptvorteil gegenüber dem Dateiboard zunichtemacht.

**Kleinere Alternative.** Eine Liste „wartet auf dich" auf der Übersicht,
gespeist aus den Zuständen, die ohnehin existieren. Kein neues Datum, keine
Benachrichtigungsinfrastruktur. Billiger als jede der Zeilen, die ich unter F
nach M2 verschiebe.

## H · Anforderung 10 kommt nicht vor

**Gegenfall.** „Schritt 1 bleibt die portable Datei; erkläre einen
schrittweisen Weg von diesem Board zum Server ohne zwei widersprüchliche
Zustandsquellen." Das Konzept hatte dafür eine sechsstufige Migration. Die
Stellungnahme erwähnt sie nicht mehr und verlegt den Nachweis in ein eigenes
Testrepo — was für den Prototyp richtig ist, aber offenlässt, was mit dem
laufenden Board samt T-56/T-57 geschieht.

**Kleinere Alternative.** Ein Satz genügt, und er sollte ausdrücklich
dastehen: Der MVP läuft auf einem Testrepo; das laufende StockInfo-Board
bleibt im Dateimodus, bis der Abnahmelauf durch ist; die Migration ist eine
eigene Entscheidung nach dem MVP, nicht Teil davon. Ungesagt sieht es aus wie
vergessen — und die Anforderung verlangt gerade, dass nie zwei Wahrheiten
gleichzeitig gelten.

---

## Was ich für die Entscheidungsvorlage vorschlage

Kein weiterer Konzeptdurchgang von meiner Seite. Aus dieser Runde gehören in
die gemeinsame Vorlage:

1. MVP = erster Abschnitt der eigenen Baufolge, Abnahmeschritte 1–4 (F).
2. Lauf-Ende in drei Formen, Checkpoint als Normalfall, `context_budget` als
   Anzeige statt Steuerung (E).
3. Kein vom Dienst gestarteter Runner im Arbeitsverzeichnis des Menschen (A).
4. Vorabnachweis in zwei sequenzierten Versuchen, Zeitgrenze je Versuch (B).
5. Erfolglos = keine Senkung offener blockierender Findings (C).
6. Export als Orphan-Branch im Projektrepo, DB-Backup separat (D).
7. „Wartet auf dich" in der Übersicht (G).
8. Ein Satz zur Abgrenzung Testrepo/laufendes Board (H).

Nichts davon blockiert den Vorabnachweis. A und B betreffen ihn direkt, alles
Übrige ist danach zu entscheiden — und einiges davon entscheidet der Versuch
besser als eine weitere Runde Prosa.
