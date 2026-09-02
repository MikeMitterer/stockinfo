# T-57 · Die Tickets sagen nicht, was offen ist — drei Konstruktionsfehler

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Prozess + ein Übersichtswerkzeug) | Vorschlag bei Codex | 2–3 h | Human-Spalte, Abschluss von Prüftickets, Übersicht über den Rest | — |

- **Angelegt:** 2026-09-02, aus drei Einwänden von Mike an einem Tag
- **Hängt ab von:** nichts. Berührt jedes Ticket, ändert an keinem den Inhalt
- **Verzahnt mit:** T-56, das die ersten beiden Vorschläge bereits anwendet

**Löst:** Mike muss wiederholt nachfragen, was tatsächlich offen ist — und
bekommt die falsche Antwort. Am 2026-09-02 habe ich ihm T-31, T-38 und T-51
als offen gemeldet. Alle drei waren freigegeben.

Das war kein Flüchtigkeitsfehler. Es sind drei Fehler in der Buchführung, und
jeder für sich erzeugt denselben Effekt: **Der Zustand eines Tickets steht
nirgends verlässlich.**

---

## Fehler 1 · Die Human-Spalte steht überall, auch wo sie nichts beiträgt

> **Mike:** *„Was nicht optimal ist: dass es für alle Punkte eine
> Human-Spalte gibt, obwohl du bzw. Codex weit effizienter testen könnt.
> Tests, Smoke-Skripte können über die KI laufen — da brauche ich nicht
> dasselbe nochmal machen."*

Heute trägt **jede** Verify-Zeile beide Spalten. Für die meisten ist die
KI-Messung strikt besser: wiederholbar, mit Statuscodes, mit einem Mutanten
als Gegenprobe. Mike daneben nochmal klicken zu lassen, fügt nichts hinzu —
es hält nur das Ticket offen.

**Vorschlag: Die Spalte richtet sich danach, wer die Frage beantworten kann.**

| Art der Zeile | Wer entscheidet | Beispiel |
|---|---|---|
| **maschinell** | KI allein — keine Human-Spalte | „`POST /backups` antwortet 201, die Datei liegt da" |
| **Sichtprüfung** | KI im Browser — keine Human-Spalte | „der Knopf ist sichtbar und klickbar" |
| **Urteil** | **nur Mike** — keine KI-Spalte | „ist dieser Satz verständlich?", „willst du das so?" |

Eine Zeile hat damit **eine** Spalte statt zwei. Ein Ticket wartet nur noch
dann auf Mike, wenn es wirklich eine Urteilszeile trägt — und die meisten
tragen keine.

**Die Gegenfrage an Codex:** Gibt es eine maschinelle Zeile, auf der ein
menschlicher Blick doch etwas beiträgt? Mir fällt ein Kandidat ein — *„die
Zahlen stimmen, aber die Tabelle ist unlesbar"* —, und ich halte ihn für eine
**Sichtprüfungszeile**, nicht für eine Urteilszeile.

## Fehler 2 · Ein Prüfticket, das Befunde findet, bleibt selbst offen liegen

> **Mike:** *„Wenn UI-Tests durch die KI fehlschlagen, führt das zu weiteren
> Tickets, aber das ursprüngliche Ticket bleibt weiterhin offen. Schmarren.
> Ich teste nicht ein Ticket, für das es schon Fehlerkorrekturen gibt."*

So ist es T-50 ergangen. Der Lauf **hat funktioniert** — er fand fünf
Defekte, die alle repariert und freigegeben sind. Trotzdem stand T-50 danach
als offenes Ticket da und wartete auf Mikes Lauf, obwohl sich das, was er
sehen sollte, inzwischen fünfmal geändert hatte.

Die Ursache ist eine Verwechslung: **Ein Prüfticket wird behandelt wie ein
Bauticket.** Ein Bauticket ist fertig, wenn der Code stimmt. Ein Prüfticket
ist fertig, wenn **die Prüfung stattgefunden hat und jeder Befund erledigt
oder klar zugeordnet ist.** Dass Befunde entstehen, ist sein Erfolg, nicht
sein Rückstand.

**Vorschlag, zwei Teile:**

1. **Kleine lokale Befunde bleiben im Prüfticket.** Sie werden dort korrigiert
   und gezielt nachgemessen; dafür entsteht kein eigenes Ticket. Nur Befunde
   außerhalb der Kleinbefund-Grenzen aus `CODEX-REVIEW-AUTOMATION.md` tragen
   ihren Rückstand in einem eigenen Ticket oder Scope-Checkpoint.
2. **Mikes Lauf findet nie auf einem Stand mit offenen Befunden statt.**
   Findet mein Vorlauf etwas, geht das Ticket **nicht** weiter an Mike,
   sondern zurück in die Umsetzung; nach der Reparatur wird der betroffene
   Punkt **erneut** gelaufen. Mike bekommt eine vollständig grüne Liste oder
   gar keine.

Damit kann *„ein Ticket mit angehängten Fehlerkorrekturen liegt bei Mike"*
nicht mehr entstehen.

## Fehler 3 · 42 offene Tickets, und keines sagt verlässlich, ob es offen ist

> **Mike:** *„Aktuell sind viel zu viele Tickets als offen markiert bzw.
> liegen noch nicht in `solved`. Das ist für mich sehr unübersichtlich. Ich
> muss immer wieder nachfragen, was tatsächlich offen ist."*

Zwei Ursachen, gemessen am 2026-09-02:

**Die Statuszeile im Ticketkopf ist von Hand gepflegt und deshalb falsch.**
Ein Auszug aus dem Inventar — links, was das Ticket über sich sagt, rechts,
was seine Verify-Matrix zeigt:

| Ticket | sagt über sich | ist tatsächlich |
|---|---|---|
| T-51 | `offen` | Codex-freigegeben, 4/4 |
| T-47 | `**in Arbeit**, Scope-Checkpoint bei Codex` | freigegeben, 12/12 |
| T-31 | `offen (entschieden 2026-08-28)` | freigegeben, Runde 7, 9/9 |
| T-44 | `aktiv` | freigegeben, 6/6 |
| T-32 | `offen` | **stimmt** — und ist die Ausnahme |

Von 42 Tickets tragen 20 eine Statusangabe, die ihrem Inhalt widerspricht.
Eine Angabe, die an 42 Stellen von Hand nachgezogen werden muss, wird nicht
nachgezogen.

**Und der zweite Grund: 28 fertige Tickets liegen noch neben den offenen.**
Das ist der Stapel, den Mike gerade freigegeben hat zu räumen.

**Vorschlag, zwei Teile:**

1. **Der Verify-Matrix wird geglaubt, nicht der Statuszeile.** Der Zustand
   wird aus den Marken abgeleitet, nicht behauptet. Die Statuszeile im Kopf
   entfällt oder trägt nur noch, was die Matrix nicht sagen kann
   („eingefroren", „ruht bis zu Mikes Kommando").
2. **Ein Werkzeug beantwortet die Frage, statt dass Mike sie stellt.** Das
   Inventar für diesen Befund existiert bereits als Wegwerf-Skript; es liest
   die Tabellen, bestimmt die `AI`-Spalte über die Kopfzeile und zählt nur
   Datenzeilen. Als gepflegtes Skript mit einem `make tickets` davor
   beantwortet es die Frage in einer Sekunde.

**Kein `grep`.** Die Legende jeder Matrix enthält alle vier Marken — eine
Textsuche zählt sie mit und liefert für jedes Ticket ein falsches Ergebnis.
Das ist derselbe Fehler wie bei der Bezeichnerprüfung: **Inventar statt
Rateliste.**

### Warum ein Makefile-Ziel und nicht einfach ein Skript

Mikes Regel für Makefiles ist „klein halten, keine Einmal-Schüsse, auf
Anforderung erweitern". Das hier ist keine Einmal-Sache: Er hat die Frage in
dieser Sitzung dreimal gestellt. Genau das ist die Anforderung.

---

## Mikes Frage: Wäre Kanban der Ansatz?

> **Mike:** *„Ist so eine Art von Kanban-Konzept für die Tickets ein Ansatz
> bzw. was würde dagegen sprechen?"*

**Als Denkmodell: ja, und es ist bereits halb gebaut.** `STATUS.md` führt eine
Phasenkette — `claude_working` → `ready_for_codex` → `codex_reviewing` →
`changes_requested`/`approved` → `portfolio_review`. Das *sind* Kanban-Spalten.
Nur gilt die Kette heute für **die Sitzung**, nicht für das Ticket: Es gibt
genau eine `phase`, und sie beschreibt, woran gerade gearbeitet wird. Die
anderen 41 Tickets haben keinen Zustand — deshalb muss Mike fragen.

**Was dagegen spricht, ist nicht Kanban, sondern das Brett.**

1. **Ein Brett wäre eine zweite Wahrheit.** Genau daran krankt es jetzt schon:
   Statuszeile, Verify-Matrix, `STATUS.md` und das Verzeichnis sagen
   Verschiedenes. Eine fünfte Stelle, die von Hand nachgezogen werden muss,
   macht es schlimmer, nicht besser.
2. **Ein Werkzeug außerhalb des Repos zerschneidet den Kanal.** Claude und
   Codex stimmen sich über eine Datei ab, weil sie *im* Repo liegt, mit dem
   Stand versioniert ist und ohne Zugangsdaten lesbar bleibt. Ein Board bei
   GitHub oder Trello wäre für beide Agenten eine API mit Anmeldung — und für
   einen Codex-Lauf ohne Netz gar nicht da.
3. **Der Engpass ist nicht die Menge paralleler Arbeit.** Kanbans eigentliches
   Werkzeug ist das WIP-Limit. Hier läuft ohnehin ein Ticket zur Zeit; das
   Problem ist nicht „zu viel gleichzeitig", sondern **„fertig ist nicht
   definiert"**.

**Der Vorschlag ist deshalb Kanban ohne Brett:**

- **Eine** maschinenlesbare Zustandszeile je Ticket — die Spalte, in der es
  steht. Nicht zusätzlich zur heutigen Statuszeile, sondern **an ihrer
  Stelle**.
- Das Verzeichnis bleibt die letzte Spalte: `_tickets/` ist das Brett,
  `_tickets/solved/` ist `done`. Kein zweiter Ort.
- `make tickets` zeichnet das Brett aus den Dateien. Niemand pflegt eine
  Ansicht.

| Spalte | Bedeutung | wartet auf |
|---|---|---|
| `backlog` | angelegt, nicht eingeplant | niemanden |
| `ready` | eingeplant, nicht begonnen | Claude |
| `doing` | in Umsetzung | Claude |
| `review` | bei Codex | Codex |
| `judgment` | **die einzige Spalte, die auf Mike wartet** | Mike |
| `frozen` | eingefroren oder ruhend (T-21, T-40) | eine Entscheidung |

**Und der Riegel gegen genau den Fehler, der heute passiert ist:** Die
Zustandszeile wird nicht geglaubt, sondern **gegen die Verify-Matrix
gehalten**. Sagt ein Ticket `doing`, während alle Marken ✅ sind, meldet
`make tickets` den Widerspruch. Ein Zustand, den niemand nachzieht, fällt
damit auf, statt drei Wochen still falsch zu sein — dasselbe Prinzip wie beim
Mutanten: **die Buchführung bekommt eine Gegenprobe.**

Der Punkt, an dem ich unsicher bin und Codex' Meinung will: Ob `judgment` und
`review` wirklich zwei Spalten brauchen oder ob `review` mit dem
`owner`-Feld auskommt.

## Verify

Die Spalten folgen dem Vorschlag aus Fehler 1 — jede Zeile hat nur die, die
sie entscheiden kann.

| # | Where | Look for | Wer |
|---|---|---|---|
| **1** | eine berührte Verify-Matrix | Zeilen tragen genau eine Spalte; die Art ist erkennbar | KI |
| **2** | `CODEX-REVIEW-AUTOMATION.md` | die drei Regeln stehen dort, wo eine Übergabe sie liest | KI |
| **3** | `make tickets` | nennt die offenen Tickets mit dem Grund; die Legende verfälscht die Zählung nicht | KI |
| **4** | Gegenprobe zu `#3` | ein Ticket, dem man eine Marke wegnimmt, taucht auf; eines mit voller Matrix nicht | KI |
| **5** | `_tickets/` | nach dem Räumen liegen dort nur noch Tickets, die etwas verlangen | KI |
| **6** | der Vorschlag als Ganzes | **Will Mike es so?** Insbesondere: soll die Statuszeile im Kopf ganz verschwinden? | **Mike** |

## Nicht-Ziele

- **Keine inhaltliche Änderung an einem Ticket.** Es geht um Buchführung.
- Keine Automatik, die Tickets selbstständig nach `solved/` verschiebt. Das
  Räumen bleibt eine Entscheidung, die jemand trifft.
- Keine neue Ticketverwaltung, kein Werkzeug jenseits der einen Übersicht.
- Kein Umschreiben der bereits abgelegten Tickets in `solved/`.

---

## Was Codex an diesem Vorschlag prüfen soll

1. **Fehler 1** — gibt es eine maschinelle Zeile, auf der eine Human-Spalte
   doch etwas beiträgt?
2. **Fehler 2** — kann ein Prüfticket schließen, während seine Befunde offen
   sind, ohne dass etwas verlorengeht? Meine Sorge: Die Verbindung
   Prüfticket → Befundticket muss dann irgendwo stehen bleiben.
3. **Fehler 3** — trägt „der Matrix glauben, nicht der Statuszeile"? Es gibt
   Tickets **ohne** Matrix (T-14, T-19, T-26, T-29, T-30, T-32, T-40). Für
   die braucht die Regel eine Antwort.
4. Ist das ein Ticket oder drei? Ich halte es für eines, weil alle drei
   Fehler dieselbe Frage falsch beantworten — aber das ist eine Ansicht.
