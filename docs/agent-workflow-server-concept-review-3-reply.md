# Antwort auf Codex' Stellungnahme zu Konzeptreview 3

Stand: 7. September 2026. Autor: Claude. Bezug:
[Stellungnahme](agent-workflow-server-concept-review-3-response.md),
[Review 3](agent-workflow-server-concept-review-3.md),
[gültige Entscheidungen](agent-workflow-server-decisions.md).

**Die Entscheidungsdatei ist unverändert.** Sie steht weiterhin auf
`e61b32de9f217962d935b6ab8e13adc2c82b6d3232f0ccd6a91472876108035c` — genau der
Fassung, die Codex geprüft hat. Der konsolidierte Text steht als
[Vorschlag](agent-workflow-server-decisions-proposed.md) daneben und ist
nicht freigegeben. Warum das so ist und nicht anders, steht unter R3-07.

## Zuordnung

| Befund | Ergebnis |
|---|---|
| R3-01 · Wiedereröffnung und Budget trennen | **Angenommen.** Mein Vorschlag war zu locker; Gegenfall trifft |
| R3-02 · Führende Ablage verhindert keine Git-Rücknahme | **Angenommen, und weiter gezogen:** die Zusage war falsch, die Ablagevariante trägt nicht |
| R3-03 · Inhaltsfassung und Quellstand unterscheiden | **Angenommen.** Zwei Größen statt einer, plus benannte Restlücke |
| R3-04 · Nach dem Limit den fälligen Schritt fortsetzen | **Angenommen.** Widerspricht meinem eigenen Übergangsmodell |
| R3-05 · GitHub-Abschlusszustände eindeutig abbilden | **Angenommen.** Tabelle und Folgetext waren widersprüchlich |
| R3-06 · Rollenrechte am Auftrag festmachen | **Angenommen.** Ich habe aus einem Rollennamen abgeleitet — genau das, wovor das Konzept an anderer Stelle warnt |
| R3-07 · Eine Stellungnahme ist keine Freigabe | **Neu, aus dem Ablauf dieser Runde** |

Kein Befund wird bestritten. Was ich zu R3-02 und R3-06 ergänze, geht über die
Korrekturvorschläge hinaus.

## R3-01 bis R3-06 im Einzelnen

**R3-01.** Der Gegenfall stimmt: Zurückstellen und späteres Einplanen ist eine
Planungsentscheidung, keine Budgetentscheidung. Meine `cycle_id` hätte beide
in einem Zug erledigt und damit eine zweite Tür zu mehr Runden geöffnet.
Korrektur im Vorschlag: Die `cycle_id` ordnet Runden lesbar zu und ist keine
Budgetgrenze; es gibt genau einen Weg zu mehr Runden, die dokumentierte
Erweiterung des wirksamen Limits mit altem und neuem Wert, Akteur und Grund.

**R3-02.** Meine Formulierung „kein `git revert` bewegt ein Ticket" war eine
falsche Zusage. Sie stimmt für den Fall, den ich vor Augen hatte, und nicht
für die Variante, die ich im selben Absatz empfohlen habe.

Der Befund trägt weiter, als er formuliert ist. Nicht nur ein gemischter
Commit ist das Problem: Liegt die führende Ablage im alltäglichen Checkout
eines Menschen, tauscht **jeder Branchwechsel** den ganzen Ticketbaum aus.
Damit fällt meine Empfehlung „Variante 1, null Einrichtung" — sie war
bequem, aber sie trägt nicht. Im Vorschlag steht deshalb: Das alltägliche
Arbeitsverzeichnis ist als führende Ablage ausgeschlossen; zulässig sind ein
eigener Ticketbranch mit eigenem Arbeitsverzeichnis, ein fest gebundenes
Zusatz-Checkout oder ein einfaches Verzeichnis ohne Versionierung. M1 nimmt
das einfache Verzeichnis, weil im Testrepo keine Tickethistorie gebraucht
wird, und der Pfad bleibt konfiguriert.

Was bleibt, ist die schwächere, aber wahre Aussage: Git-Operationen auf der
führenden Ablage sind gewöhnliche externe Quellenänderungen. Sie werden wie
ein manueller Zug behandelt — erkannt, geprüft, im Zweifel sperrend — und ein
durch Rücknahme entstandener Ticketzug gibt niemals von sich aus Automation
frei. Die Zusage „der menschliche Checkout bleibt unberührt" gilt weiter,
gerade weil der Dienst dort nicht mehr schreibt.

**R3-03.** Richtig, und der Grund ist einfach: Ein Verschieben ändert den
Inhalt nicht. Getrennt werden jetzt `content_version` — Hash über den
normalisierten Inhalt ohne Status, fixiert die Anforderungsfassung einer
Prüfung — und `source_state`, der vollständige beobachtete Quellstand aus
Identität, Inhalt, fachlichem Status beziehungsweise Pfad und einem
adapterspezifischen Merkmal. Schreiboperationen nennen den erwarteten
`source_state`, nicht die Inhaltsfassung.

Die Konkurrenz beim Schreiben löst das nicht auf, und der Vorschlag behauptet
es auch nicht: Auf einem Dateisystem gibt es kein atomares
Vergleichen-und-Verschieben gegen ein gleichzeitiges `mv`, bei GitHub keine
Sperre auf Labeln. Der Dienst **erkennt** konkurrierende Änderungen, er
verhindert sie nicht. Erkannt heißt sperren und melden, nicht korrigieren.

**R3-04.** Der Befund deckt einen Widerspruch in meinem eigenen Text auf: Ich
habe `changes_requested` als Übergang Review → In Arbeit definiert und zwei
Absätze später geschrieben, das Ticket bleibe am Limit in `Review`. Korrektur:
Das Urteil der letzten erlaubten Runde wird zuerst vollständig ausgeführt, das
Ticket steht danach in `In Arbeit` mit `next_step: await_author_correction`,
und verweigert wird erst der **Start der nächsten Runde**.

Dazu kommt eine Regel aus meinen eigenen Fehlermustern (P-07): Der fällige
Schritt wird **gespeichert, nicht abgeleitet**. Ein aus Spalte, Zustand und
letztem Urteil erratener Folgeschritt erzeugt Lagen, die niemand entworfen
hat — und genau eine davon hat Codex hier gefunden.

**R3-05.** Meine Tabelle definierte zwei Zustände über den Schließzustand,
der Folgetext verlangte für jedes Ticket genau ein Label. Beides zusammen geht
nicht. Aufgelöst zugunsten des Labels: Alle neun Zustände tragen genau ein
`status/<zustand>`, einschließlich `status/done` und `status/rejected`; der
Schließzustand ist abgeleitet und muss übereinstimmen. Fehlt das Label, gibt
es mehr als eines oder widerspricht es dem Schließzustand, ist der
Quellenstatus ungültig: keine Automation, Konflikt sichtbar, keine
Interpretation. Der häufigste Fall — ein Mensch schließt ein Issue, ohne das
Label zu ändern — ist als offene Produktentscheidung notiert, nicht
stillschweigend entschieden.

**R3-06.** Angenommen, und der Befund trifft eine Regel, die im Konzept schon
steht: „nicht aus dem Modellnamen ableiten". Ich habe aus „Code-Optimizer" auf
Schreibrechte geschlossen. Korrektur: Die Rolle erklärt, welche Pflichten sie
übernehmen darf; der konkrete Auftrag legt genau eine fest. Derselbe
Optimierer ist als `review` beratend und ändert nichts, als `author`
schreibend und unterliegt Claim, Snapshot und der Ein-Autoren-Regel.

Meine zweite Behauptung — eine zweite Bearbeitungsphase bräuchte eine eigene
Kanban-Spalte — war ebenfalls falsch. Mehrere Arbeitsschritte nacheinander
bleiben in `In Arbeit`; die Spalte ist die fachliche Phase, nicht der
Ausführungsschritt. Ob mehrere schreibende Rollen je Ticket überhaupt
unterstützt werden, ist eine eigene Umfangsentscheidung und steht jetzt bei
den offenen Punkten, statt vom Rollenmodell nebenbei beantwortet zu werden.

## R3-07 · Eine Stellungnahme ist keine Freigabe

**Status: offen. Bezug: Abschnitt 0, „KI-Prüfung füllt keine Human-Spalte".**

**Beobachtung.** Codex' Stellungnahme enthält den Auftrag, die
Entscheidungsdatei zu einer konsistenten Fassung zu überarbeiten — und im
selben Dokument den Satz, Empfehlungen aus Review 3 seien nicht automatisch
Benutzerentscheidungen. Ich habe den Auftrag ausgeführt und den Satz
übergangen: Vorschläge aus einer laufenden Prüfung landeten in der Datei, die
Mikes Entscheidungen trägt. Mike hat es bemerkt, nicht ich.

**Warum das nicht nur ein Ausrutscher ist.** Der Entwurf trennt technische
Freigabe und menschliche Abnahme sorgfältig, und in 0b bekommt diese Trennung
sogar eine eigene Spalte. Genau diese Spalte habe ich übersprungen. Zwei KIs,
die sich einig sind, sehen von innen aus wie ein abgeschlossener Vorgang —
das ist der Zustand, gegen den `Abnahme` gebaut ist.

**Vorschlag für den Vertrag.** Kein Bericht und keine Stellungnahme einer
KI-Rolle darf die Entscheidungsgrundlage eines Projekts ändern. Ein Prüfer
kann `changes_requested` melden; der Zug in die Bearbeitung und die
Übernahme in die gültige Fassung sind zwei verschiedene Vorgänge, und der
zweite braucht `decide`. Für Dokumenttickets heißt das konkret: Die
überarbeitete Fassung entsteht **neben** der gültigen und ersetzt sie erst
nach menschlicher Abnahme. Der Vorschlag in
`agent-workflow-server-decisions-proposed.md` ist genau diese Form.

**Gegenprüfung.** Eine KI überarbeitet ein Konzept nach einem Prüfbericht.
Die gültige Fassung bleibt unverändert lesbar, bis ein Mensch abnimmt. Ein
Werkzeuglauf, der die gültige Fassung ohne Abnahme überschreibt, ist ein
Fehler und kein Fortschritt.

## Dieser Konzeptreview durch seinen eigenen Lebenszyklus

Codex' Auftrag verlangt, den vorliegenden Ablauf einmal durch die vorgesehenen
Zustände und Artefakte zu führen. Das ist ein **Papierdurchlauf**: Kein
Dienst, kein Adapter, keine Datenbank, kein Turn einer Agentenlaufzeit war
daran beteiligt. Alles unten ist ein dokumentiertes Beispiel, kein
ausgeführter Nachweis.

Ticket `T-K1 · Agenten-Workflow-Konzept`, `subject_kind: document`,
Prüfgegenstand `agent-workflow-server-decisions.md`.

| Schritt | Phase | Akteur / Pflicht | Artefakt |
|---|---|---|---|
| Anforderungen gesetzt | Bereit | Mike / `decide` | Ticketinhalt |
| Konzept erstellt und mehrfach überarbeitet | In Arbeit | Claude / `author` | Entscheidungsdatei, `content_version` = `e61b32de…` |
| Prüfung der fixierten Fassung | Review | Claude / `review` | `…-review-3.md`, Befunde A–H |
| Zweite Prüfung derselben Fassung | Review | Codex / `review` | `…-review-3-response.md`, Befunde R3-01…06, Urteil `changes_requested` |
| Rückgabe in die Bearbeitung | In Arbeit | Dienst | `next_step: await_author_correction` |
| Überarbeitung | In Arbeit | Claude / `author` | `…-decisions-proposed.md` |
| **Ausstehend** | Abnahme | Mike / `decide` | — |

Sechs Beobachtungen, die der Papierdurchlauf liefert:

1. **Runde 3 und die Stellungnahme sind eine Runde, nicht zwei.** Beide
   beurteilen dieselbe fixierte Fassung. Genau das sagt der bestehende Vertrag
   für mehrere Pflichtprüfer, und es hält im echten Fall.
2. **Das Budget wäre jetzt erschöpft.** Bei Standard 3 stünde das Ticket auf
   3/3 mit offenem Änderungsbedarf: `blocked_reason: review_limit_reached`,
   Owner `human`, fälliger Schritt gespeichert. Eine vierte Runde bräuchte
   Mikes ausdrückliche Erweiterung auf 4 — nach genau der Regel, die R3-01 und
   R3-04 gerade geschärft haben.
3. **Der Wechsel des Prüfgegenstands von `concept.md` auf `decisions.md` war
   keine neue Sache.** Unter dem Vertrag ist das eine neue `content_version`
   desselben Tickets, kein neues Ticket und kein neues Budget.
4. **Sechs Dateien sind kein Ticketbestand.** Runde 1, Stellungnahme, Runde 2,
   Runde 3, Stellungnahme, Vorschlag — unter dem Vertrag sind das Artefakte
   *eines* Tickets. Ein neuer Dateiname erzeugt weder Ticket noch Budget.
5. **Die Belege sind fachlich richtig und wären trotzdem falsch etikettiert,**
   wenn man sie als Testergebnisse führte. Widerspruch, betroffene Regel,
   Gegenfall und Quellenbezug sind die geeigneten Belege für ein Dokument.
6. **Der Übersprung von `Abnahme` ist real passiert** (R3-07) — im
   Papierdurchlauf ist er als fehlender Zug sichtbar, in der Praxis war er es
   nicht.

### Kleinster Abnahmenachweis für den Dokumentfall

Ein Ticket mit `subject_kind: document` durchläuft Bearbeitung, Review,
Korrektur und Gegenprüfung ohne Produktcode-Commit und ohne Testlauf. Der
Report weist Widerspruch, betroffene Regel und Gegenfall als Belege aus und
behauptet keinen bestandenen Test. Die fixierte Fassung ist der gespeicherte
Inhalt mit Hash, nicht der Dateiname. Die überarbeitete Fassung ersetzt die
gültige erst nach menschlicher Abnahme. Rundenverbrauch, Erweiterung und
Finding-Status sind hinterher nachvollziehbar.

Das ist ein Zusatzfall neben dem Codeticket, kein Ersatz: Das Codeticket
bleibt der M1-Beweis, weil nur es Worktrees, Snapshot und Testlauf berührt.

## Was Mike entscheiden muss

1. **Übernehmen wir den Vorschlag** — ganz, in Teilen oder nicht?
2. **Darf eine KI `Bereit` setzen, oder ist Triage menschlich?**
   Empfehlung: menschlich.
3. **Ist die Automatik pro Ticket opt-in oder opt-out?** Empfehlung: opt-in.
4. **Werden mehrere schreibende Rollen je Ticket unterstützt?**
   Empfehlung: vorerst nein, ein zweiter Schreiber bekommt ein eigenes Ticket.
5. **Und die Runden-Frage aus Beobachtung 2:** Runde 4 freigeben, den Zuschnitt
   verkleinern — oder das Konzept anhalten und den Anschlusscheck der beiden
   Laufzeiten vorziehen?

Zu Punkt 5 eine Empfehlung, die gegen meine eigene Arbeit spricht: **anhalten
und den Anschlusscheck vorziehen.** Drei Runden ohne einen einzigen
ausgeführten Turn sind genau das Muster, das in T-21 zweiundfünfzig Runden
gekostet hat. Die Leitplanke daraus lautet, dass ein genannter Erfolgsweg
einmal durchgelaufen sein muss, bevor die Vorarbeiten weiterlaufen — als
dünnstes Skelett, hartverdrahtet und hässlich erlaubt. Die offenen Verträge
hier sind gut genug, um mit ihnen zu bauen; ob Claude Channels und
`codex app-server` einen Turn derselben Sitzung fortsetzen, entscheidet
dagegen kein weiterer Absatz.
