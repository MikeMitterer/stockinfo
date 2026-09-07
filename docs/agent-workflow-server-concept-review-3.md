# Konzeptreview Runde 3 · Kanban und alternative Ticketquellen

Stand: 7. September 2026. Grundlage:
[Entscheidungen](agent-workflow-server-decisions.md), Abschnitt 0b.
Vorgeschichte: [Runde 1](agent-workflow-server-concept-review.md),
[Stellungnahme](agent-workflow-server-concept-response.md),
[Runde 2](agent-workflow-server-concept-review-2.md).

Auftrag laut 0b: die sechs dort benannten Punkte klären und die Änderung mit
den bisherigen Verträgen konsistent machen. Diese Runde beantwortet sie mit
konkreten Regeln, nicht mit weiteren Fragen. Wo eine Regel eine Produktfrage
voraussetzt, steht sie am Ende unter „Was nur Mike entscheiden kann".

## Unstrittig

Vier Entscheidungen aus 0b halte ich für richtig und fasse sie nicht an:
genau eine führende Ticketquelle ohne bidirektionale Spiegelung; `blocked`
als Kennzeichnung statt als zehnte Spalte; kein `solved` neben `Erledigt`;
und die Trennung von technischer Freigabe und menschlicher Abnahme in zwei
sichtbare Spalten. Der letzte Punkt ist der eigentliche Gewinn der Änderung:
„approved ist keine Abnahme" war bisher eine Regel im Fließtext und ist jetzt
ein Ort, an dem ein Ticket liegenbleibt, bis ein Mensch es anfasst.

## Befunde

| Nr | Punkt aus 0b | Urteil |
|---|---|---|
| A | 5 · Ticketablage und Worktrees | **Blockierend.** Der Ordnerstatus im Produktrepo macht den Review-Snapshot selbstbezüglich → A |
| B | 4 · Quellenänderung, Konflikt, Wiederanlauf | Zwei Schreiber ohne Konfliktregel; Schreibprotokoll und Abgleichpunkt fehlen → B |
| C | 2 · Zuordnung Ausführungszustand ↔ Kanban | Abbildung ist behauptet, nicht festgelegt; `blocked` steht in zwei Rollen → C |
| D | 1 · Übergänge, Rechte, Wiedereröffnung, Abbruch | Wiedereröffnung ist der offene Ausweg um das Rundenlimit aus Abschnitt C → D |
| E | 3 · Ticketvertrag und GitHub-Abbildung | Neun Zustände passen nicht auf `open`/`closed`; Belege würden veröffentlicht → E |
| F | 6 · M1/M2, Abnahme, Sicherung | M1 wächst still um Triage und Board; Sicherung hat jetzt zwei Artefakte → F |
| G | — (neu) | `Bereit` wird in M2 zum Kostenschalter; Auswahlregel in `ready/` fehlt → G |
| H | — (Rückfrage Mike) | **Mehrere Menschen sind nicht abbildbar:** `human` ist eine Rolle, keine Identität → H |

---

## A · Ordnerstatus im Produktrepo macht den Snapshot selbstbezüglich

**Gegenfall.** 0b legt `_tickets/<zustand>/` fest und macht den Ordner zum
Status. Abschnitt A der Entscheidungen legt gleichzeitig fest: Developer
arbeitet im eigenen Worktree auf `agentboard/t-<id>`, Verifier in einem
detached Review-Worktree, der Mensch in seinem Checkout. Das sind drei
Arbeitsverzeichnisse desselben Repositories — und damit drei Kopien von
`_tickets/`, jede auf einem anderen Commit. Der Satz „genau eine führende
Ticketquelle" gilt dann nur noch dem Namen nach.

Drei Folgen, die nicht Geschmackssache sind:

1. **Der Snapshot enthält seinen eigenen Status.** Die Übergabe fixiert
   Commit und Tree. Beim Handoff muss das Ticket von `in-progress/` nach
   `review/`. Macht der Developer den Zug im Ticket-Branch, enthält der
   geprüfte Commit die Aussage „dieses Ticket ist im Review" — geprüft wird
   ein Baum, der sein eigenes Prüfergebnis vorwegnimmt. Macht es der Dienst
   woanders, laufen Branch und führende Quelle auseinander.
2. **Merge und Revert verschieben Tickets.** `git revert` auf einen
   Produkt-Commit nimmt den Ticketzug mit zurück. Eine Umbenennung auf einer
   Seite gegen eine Inhaltsänderung auf der anderen ergibt einen
   Rename/Modify-Konflikt, dessen Auflösung ein Ticket in zwei Ordnern liegen
   lässt. Der Ordner ist dann kein Status mehr, sondern ein Merge-Resultat.
3. **Der Verifier liest im Review-Worktree einen veralteten Ticketstand**
   und hat keinen Weg zu merken, dass er veraltet ist — der Ordner sieht
   genauso gültig aus wie in der führenden Ablage.

**Kleinere Alternative.** Keine neue Maschinerie, sondern die, die für den
Export-Branch in Abschnitt D bereits beschlossen ist: eine eigene Historie in
einem eigenen Worktree.

- Die Tickets liegen auf einem eigenen Branch, etwa `agentboard/tickets`, der
  **einmal** in genau ein Arbeitsverzeichnis ausgecheckt ist. Dieser Pfad ist
  die führende Ablage. Produktbranches enthalten kein `_tickets/`.
- Nur der Dienst und der Mensch schreiben dort. Agenten ändern den
  Ticketstatus ausschließlich über MCP, niemals durch Verschieben einer Datei
  in ihrem Worktree. Ein Statuszug ist damit nie Teil eines geprüften Trees.
- Der Developer bekommt den Ticketinhalt als **fixierte Anforderungsfassung**
  im Auftragspaket — das steht ohnehin schon in Abschnitt 0. Sie ist eine
  Kopie zum Lesen, kein zweiter Bestand: Sie hat keinen Ordner und damit
  keinen Status.

Damit bleibt die Versionierung der Tickets erhalten (Mikes heutige Praxis in
StockInfo), die Zahl der Kopien fällt auf eins, und Punkt 5 aus 0b — „Kopien
dürfen nicht zu mehreren unabhängig bearbeiteten führenden Ticketbeständen
werden" — ist nicht mehr eine Absicht, sondern eine Eigenschaft des Aufbaus.

Die Variante „Ticketordner neben dem Repo, nicht versioniert" löst dasselbe
Problem, verliert aber Historie und Begründungen. Ich halte den eigenen Branch
für die bessere Wahl; die Entscheidung gehört Mike.

## B · Zwei Schreiber auf die führende Quelle, aber keine Konfliktregel

**Gegenfall.** 0b sagt beides: „Menschen können die führende Quelle direkt
bearbeiten" und „Manuelles Verschieben und Änderungen über MCP, CLI oder Web
unterliegen denselben fachlichen Regeln". Zwei Schreiber ohne Vorrangregel
sind ein Last-Writer-Wins, und das ist hier besonders unangenehm: Der Dienst
schreibt in die Quelle *und* in die DB, ohne gemeinsame Transaktion. Fällt er
zwischen beiden Schreibvorgängen aus, steht die Datei in `review/` und die DB
im Zustand `developer_working` — oder umgekehrt. Punkt 4 aus 0b verlangt
genau dafür eine Regel; hier ist sie.

**Vorschlag.**

*Abgleich als benannte Operation.* Die DB führt je Ticket `source_path`,
`source_revision` und `seen_at`. Ein `reconcile` liest die Quelle neu und
vergleicht. Er läuft beim Dienststart, vor jedem Auftragsstart, vor jedem
Statusschreiben und bei Ereignissen eines Dateiwächters. **Kein Auftrag
startet auf einem Lesestand, der älter ist als der letzte Abgleich.** Der
Wächter ist Beschleunigung, nie Nachweis: Ein Dienst, der stand, hat keine
Ereignisse verpasst, sondern muss neu lesen.

*Schreibprotokoll in drei Schritten.* Absicht zuerst dauerhaft speichern
(`von`, `nach`, erwartete Quellrevision), dann die Quelle schreiben, dann
bestätigen. Beim Wiederanlauf entscheidet der tatsächliche Quellstand:
Ziel bereits korrekt → bestätigen. Quelle unverändert auf `von` → erneut
ausführen. Quelle steht woanders → Konflikt, keine automatische Reparatur.
Inhaltsänderung und Statuszug sind nie eine Operation.

*Konfliktklassen und ihre Antwort.*

| Fall | Antwort |
|---|---|
| Mensch verschiebt während eines laufenden Auftrags | Auftrag aussetzen, Konflikt sichtbar, Owner `human`; laufender Turn endet geordnet (→ D) |
| Dieselbe ID in zwei Ordnern | Ungültig, beide gesperrt, keine Automation, Mensch entscheidet |
| ID verschwunden | Ticket als `missing` markieren, Aufträge aussetzen; in der DB wird nichts gelöscht |
| Inhalt während des Reviews geändert | Fixierte Prüffassung bleibt für die Runde gültig; die neue Fassung wirkt erst für die nächste Übergabe |
| Datei in `done/` ohne Belege oder Abnahme | Widerspruch anzeigen, nicht stillschweigend zurückschieben |

*Der Dienst repariert die Quelle nicht.* Er korrigiert ausschließlich seine
eigene unvollendete Absicht. Alles andere wäre ein Werkzeug, das dem Menschen
seinen Zug wieder wegnimmt. Und der harte Teil von Punkt 4 steht als eigener
Satz: **Ein ungültiger oder nicht abgeglichener Quellenstatus gibt keine
Automation frei** — auch dann nicht, wenn die DB für sich stimmig aussieht.

## C · Die Abbildung der Zustände ist behauptet, nicht festgelegt

**Gegenfall.** Abschnitt 0 führt `developer_working → ready_for_review →
reviewing → approved | changes_requested` plus `blocked`. 0b sagt dazu nur,
das seien „Ausführungszustände, keine weiteren Ticketspalten". Ohne Abbildung
gibt es zwei Wahrheiten über dasselbe Ticket. `blocked` steht zusätzlich in
beiden Rollen: in Abschnitt 0 als Zustand, in 0b als Kennzeichnung.

**Vorschlag.**

| Kanban | Zulässige Ausführungszustände | Owner | Automatik |
|---|---|---|---|
| Eingang, Backlog | keiner | human | nein |
| Bereit | keiner (wartet auf Übernahme) | human | Start möglich (→ G) |
| In Arbeit | `developer_working` | developer | ja |
| Review | `ready_for_review`, `reviewing` | verifier | ja |
| Abnahme | `approved` | human | nein |
| Erledigt, Zurückgestellt, Verworfen | keiner | human | nein |

Daraus folgen drei Festlegungen:

1. **`changes_requested` ist keine Spalte, sondern der Zug Review → In
   Arbeit.** Der Zustand existiert nur als Ereignis am Übergang.
2. **`approved` ist der Zug Review → Abnahme, ausgelöst vom Dienst nach
   Zustimmung aller Pflichtprüfer.** Der Zug Abnahme → Erledigt ist die
   menschliche Abnahme und gehört keiner KI. Damit ist die Trennung aus
   Abschnitt 0 nicht mehr nur eine Regel, sondern ein Ort im Board.
3. **Der Zug In Arbeit → Review gehört dem Dienst, nicht dem Developer.** Er
   passiert, wenn die Übergabe formal gültig ist — Snapshot, Claim, Rechte,
   Rundenlimit geprüft. Das ist dieselbe Regel wie in 1b Schritt 1: „kein Text
   ‚bin fertig' als ausreichender Handoff", nur jetzt sichtbar am Board.

`blocked` wird durchgehend ein Flag mit `blocked_reason` und Owner, nie ein
Zustand. Sonst geht verloren, *wobei* blockiert wurde: Am Rundenlimit bleibt
das Ticket in `Review`, `blocked_reason: review_limit_reached`, Owner `human`.
Gibt der Mensch eine weitere Runde frei, wird nur das Flag entfernt und der
vorherige Zustand läuft weiter — mit einem Zustand `blocked` müsste man raten,
wohin zurück.

Owner ist abgeleitet (Spalte plus Flag), kein eigenständig editierbares Feld.
Ein drittes editierbares Feld wäre eine dritte Wahrheit.

## D · Wiedereröffnung ist derzeit der Ausweg um das Rundenlimit

**Gegenfall.** Abschnitt C der Entscheidungen sperrt jeden Umweg um
`max_review_rounds`: Sitzungswechsel, anderer Provider, Compaction, neuer
Commit, Umbenennung — nichts erneuert das Budget, und „ein echtes Folgeticket
braucht einen ausdrücklich autorisierten Zuschnitt". 0b führt jetzt
`Erledigt`, `Verworfen` und `Zurückgestellt` ein und damit einen Rückweg, den
diese Aufzählung nicht kennt. Ein Ticket bei 3/3 nach `Zurückgestellt` und
zurück nach `Bereit` zu ziehen, wäre genau der automatische Ausweg, den
Abschnitt C ausschließt — und es ist ein Zug, der wie normale Planung aussieht.

**Vorschlag: Übergänge mit Akteur.**

| Übergang | Wer darf |
|---|---|
| → Eingang (neu) | Mensch; KI **nur** nach `Eingang`, nie höher |
| Eingang → Backlog → Bereit | Mensch (Triage); KI darf vorschlagen |
| Bereit → In Arbeit | Dienst bei Auftragsübernahme |
| In Arbeit → Review | Dienst bei gültiger Übergabe |
| Review → In Arbeit | Dienst bei `changes_requested` |
| Review → Abnahme | Dienst bei Zustimmung aller Pflichtprüfer |
| Abnahme → Erledigt | **nur Mensch** |
| Abnahme → In Arbeit | Mensch (Abnahme verweigert) |
| beliebig → Zurückgestellt / Verworfen | Mensch, mit Begründung |
| Zurückgestellt / Verworfen / Erledigt → Bereit | **nur Mensch**, mit Begründung; neuer Arbeitszyklus |

Dazu vier Regeln:

1. **Wiedereröffnung ist ausschließlich menschlich** und erzeugt einen neuen
   Arbeitszyklus mit eigener `cycle_id`. Der Verbrauch des alten Zyklus bleibt
   in der Historie sichtbar. Damit ist die Wiedereröffnung genau die
   „dokumentierte menschliche Erweiterung", die Abschnitt C schon vorsieht —
   und keine Lücke.
2. **Aus `Review` mit `review_limit_reached` führt kein Weg über
   `Zurückgestellt` zurück ins Budget.** Zurückstellen ist von dort erlaubt,
   die Rückkehr geht aber nach `Bereit` und ist damit eine sichtbare
   menschliche Entscheidung, kein Planungsdetail.
3. **KI-erzeugte Folgetickets landen in `Eingang`**, nie in `Bereit`. Sonst
   schneidet sich der Developer seinen Nachfolgeauftrag selbst zu — dieselbe
   Umgehung, nur eine Ticket-ID weiter.
4. **Zurückkehrende Tickets tragen `previous_state`** und laufen höchstens
   nach `Bereit` zurück, nie direkt nach `Review`: Der alte Snapshot ist
   inzwischen nicht mehr der geprüfte Stand.

**Abbruch während eines laufenden Auftrags.** Der Kanban-Zug wirkt sofort, der
laufende Turn wird nicht mitten im Request abgeschossen — dieselbe Grenze, die
1a schon für die Kontextschwelle benennt. Der Auftrag geht auf `cancelling`,
kein neuer Turn startet, der laufende endet mit Checkpoint, der Claim wird
freigegeben. Worktree und Branch bleiben erhalten; ein verworfenes Ticket ist
kein Grund, Belege zu löschen. Verbrauchte Runden bleiben verbraucht. Bereits
geschriebene Reports bleiben als Evidenz sichtbar, begründen aber keine
Freigabe mehr.

## E · Ticketvertrag und die GitHub-Abbildung

**Gegenfall.** Ein GitHub-Issue kennt `open` und `closed`. Neun Kanban-
Zustände passen darauf nicht. 0b verlangt „denselben Ticketvertrag, Kanban-
Lebenszyklus und dieselben MCP-Operationen" für beide Adapter, nennt die
Abbildung aber nicht. Zweitens gilt „kein zusätzliches bearbeitbares
Statusfeld im Ticket" — beim GitHub-Adapter ist das Label genau dieses Feld;
der Satz muss ausdrücklich auf den Dateiadapter begrenzt werden.

**Vorschlag: gemeinsamer Kern.**

- **Identität.** Die stabile ID steht im Frontmatter, nicht im Pfad und nicht
  im Dateinamen. Dateiname und Slug dürfen sich ändern, die ID nicht.
  Umbenennen ist damit erkennbar, statt als „Ticket weg, Ticket neu" zu
  erscheinen. Beim GitHub-Adapter ist die Issue-Nummer die ID.
- **Revision.** Hash über den normalisierten Inhalt ohne Status; beim
  GitHub-Adapter `updated_at` zusammen mit der Node-ID.
- **Pflichtfelder** beider Adapter: ID, Titel, Priorität, Anforderungen mit
  Akzeptanzfällen, Nicht-Ziele, optional `blocked_reason`,
  `deferred_reason`/`rejected_reason`, `previous_state`, ein
  Ticket-Override für das Rundenlimit und die Automatikkennzeichnung (→ G).

**Vorschlag: GitHub-Abbildung.**

| Kanban | GitHub |
|---|---|
| Eingang … Abnahme | `open` + genau ein Label `status/<zustand>` |
| Erledigt | `closed`, `state_reason: completed` |
| Verworfen | `closed`, `state_reason: not_planned` |
| Zurückgestellt | `open` + `status/deferred` |
| `blocked` | zusätzliches Label `blocked`, Grund im Issue-Text |

Das Label führt, `open`/`closed` wird daraus abgeleitet. Fehlt das Label oder
stehen zwei davon am Issue, ist der Quellenstatus ungültig: keine Automation,
Konflikt sichtbar (→ B). Erkennung über Polling mit `since`, Webhooks später;
beides ändert den Vertrag nicht.

Zwei Punkte, die vor der Entscheidung „beide Quellen gehören zum Produktziel"
auf dem Tisch liegen sollten: Labels darf jeder mit Schreibrecht setzen, der
ungültige Zustand ist also der Normalfall, nicht die Ausnahme. Und in einem
öffentlichen Repository macht ein automatisch geschriebener Report die
Prüfbelege öffentlich. Voreinstellung deshalb: **Reports werden nicht in die
Ticketquelle geschrieben.** Sie bleiben lokal und gehen den Weg über den
Export-Branch aus Abschnitt D.

## F · Was das für M1, Abnahme und Sicherung heißt

**Gegenfall.** M1 war „ein manuell gestartetes Ticket durchläuft Umsetzung,
Review, Report, Korrektur, Gegenprüfung". Mit 0b kommen neun Zustände, Triage,
Wiedereröffnung, Fremdänderungserkennung und ein Board dazu. Das ist genau die
Art stiller Vergrößerung, die Punkt F der Bewertung („MVP zu groß") schon
einmal zurückgeschnitten hat.

**Vorschlag: Vertrag vollständig, Umsetzung schmal.**

- M1 kennt **alle** Ordner und liest sie. Automatisiert wird nur die Kette
  `Bereit → In Arbeit → Review → Abnahme`. Triage, Wiedereröffnung,
  Zurückstellen und Verwerfen sind in M1 menschliche Züge in der Quelle plus
  Abgleich — kein Dialog, keine Bearbeitungsoberfläche.
- Der Dateiadapter ist M1. **Der GitHub-Adapter kommt frühestens nach der
  M1-Abnahme** und darf den M1-Schnitt nicht mitgestalten: Er bringt
  Anmeldung, Rate Limits, Sichtbarkeit und Ereigniszustellung mit, und keines
  davon beweist etwas über den Ablauf, um den es in M1 geht.
- Die M1-Abnahme bekommt drei Gegenproben dazu: ein manueller Zug während
  eines laufenden Auftrags erzeugt einen sichtbaren Konflikt und keinen
  Start; dieselbe ID in zwei Ordnern sperrt beide; eine Datei in `done/` ohne
  Belege zeigt den Widerspruch, statt ihn zu glätten.

**Sicherung.** Bisher war die DB das einzige zu sichernde Artefakt. Jetzt sind
es zwei, und sie können auseinanderlaufen. Die in Abschnitt D geforderte
Wiederherstellungsprobe muss deshalb den unangenehmen Fall enthalten: DB aus
einem älteren Stand zurückspielen, während die Ticketquelle weitergelaufen
ist. Erwartetes Ergebnis ist ein sichtbarer Abgleichkonflikt — nicht ein
stilles Überschreiben der Quelle mit dem alten DB-Stand.

## G · `Bereit` wird in M2 zum Kostenschalter

**Neu, nicht aus der Liste in 0b.** In M2 holt der Worker Arbeit selbständig
ab. Ab dann startet das Ablegen einer Datei in `ready/` einen bezahlten Turn.
Ein Triage-Irrtum kostet dann Kontingent, und der Ordner sieht dabei aus wie
eine harmlose Sortierung. Dazu kommt: Liegen fünf Tickets in `ready/`, ist
nirgends festgelegt, welches der Worker nimmt.

**Vorschlag.** Automatik ist pro Ticket ausdrücklich zu setzen (Feld im
Ticket) und zusätzlich pro Projekt schaltbar; ohne beides bleibt ein Ticket in
`Bereit` liegen. Das Ticket nennt außerdem den vorgesehenen Developer-Agenten
— ein Auftrag ohne benannte `agent_id` ist nicht ausführbar, passend zu 1a
(„Der Dienst adressiert immer eine `agent_id`").

Die Auswahl in `bereit` folgt der ausdrücklichen Priorität im Ticket, bei
Gleichstand der stabilen ID. **Nicht nach Änderungszeit** — sonst springt ein
Ticket durch eine beliebige Korrektur an der Datei nach vorn, und in einer
Ordnerablage ist eine Korrektur der häufigste Vorgang überhaupt.

## H · Mehrere Menschen: `human` ist eine Rolle, keine Identität

**Gegenfall.** Für KIs ist die Identität sauber getrennt: `agent_id`,
`runtime`, `provider`, `model`, `role`, `specialization` — 1a besteht sogar
ausdrücklich darauf, dass der Dienst nie „an Codex" adressiert, weil mehrere
Codex-Instanzen existieren können. Für Menschen gibt es diese Trennung nicht.
`human` steht als dritte Rolle neben `developer` und `verifier`, M1 nennt
„ein Benutzer", und die Weboberfläche zeigt „Wartet auf dich". Sobald zwei
Menschen am Projekt arbeiten, adressiert der Dienst also genau so pauschal
„an den Menschen", wie er es bei Codex zu Recht verbietet.

Das ist derselbe Kategorienfehler, den 0b bei `blocked` schon korrigiert hat:
`human` beschreibt, *wer* jemand ist, `developer` und `verifier`, *was* er
tut. In einer Spalte stehen sie nur, solange es genau einen Menschen gibt.

**Vorschlag: Akteur statt Rolle.**

- Jeder Teilnehmer ist ein `actor` mit stabiler ID und `kind: ai | human`.
  Für `kind: ai` gilt der Vertrag aus 1a unverändert. Für `kind: human`
  kommen `person_id`, Anzeigename und Rechtestufe dazu; Laufzeit, Provider
  und Sitzung entfallen.
- `role` wird auf `developer` und `verifier` reduziert und ist von `kind`
  unabhängig. Das ist kein Zusatzaufwand, sondern räumt einen vorhandenen
  Fall auf: Mike schreibt den Code, Codex prüft — dann *ist* der Mensch der
  Developer. Heute hat der Entwurf dafür keinen Platz.
- Die menschliche Abnahme hängt dann nicht mehr an einem Rollennamen,
  sondern an einem Recht: Der Zug Abnahme → Erledigt verlangt
  `kind: human` **und** die Abnahmeberechtigung. Das ist strenger als die
  heutige Formulierung und drückt genau das aus, was gemeint war.

**Rechte: zwei Stufen, nicht mehr.**

| Stufe | Darf |
|---|---|
| `member` | Tickets anlegen, triagieren, kommentieren, Developer- oder Verifier-Rolle übernehmen, Aufträge starten |
| `maintainer` | zusätzlich: Abnahme, Wiedereröffnung, Rundenlimit erhöhen, Automatik und Budgets schalten, Konfiguration und Export |

Alles, was in Abschnitt C und D bisher „der Mensch entscheidet" heißt, ist
damit ein `maintainer`-Recht. Eine feinere Rechtematrix wäre für ein lokales
Werkzeug Überbau; diese eine Grenze ist die, die zählt — sonst kann jeder
Beteiligte das Rundenlimit anheben, und die harte Grenze aus Abschnitt C ist
eine Bitte.

**Zuweisung.** „Wartet auf dich" braucht ein `assignee` mit `person_id`, sonst
wartet es auf niemanden. Für jede Spalte mit Owner `human` gilt: Entweder ist
ein Mensch zugewiesen, oder es greift ein konfigurierter Standardempfänger.
Ein Ticket in `Abnahme` ohne Empfänger ist ein sichtbarer Mangel, kein
neutraler Zustand. Die Übersicht filtert nach angemeldeter Person und zeigt
daneben unverändert den Gesamtstand.

**Nachweis der Herkunft wird früher nötig.** M2 sieht einen
„authentisierten menschlichen Entscheidungsweg mit Herkunftsnachweis" vor.
Mit einem Menschen ist das eine Formalie. Mit zweien ist eine Abnahme ohne
Anmeldung eine Behauptung über eine Person, die sie nicht getroffen haben
muss. Für M1 genügt eine konfigurierte `actor_id` je CLI-/Weboberfläche,
aber die Datei sollte ausdrücklich sagen, dass das eine Zuschreibung ist und
kein Nachweis — und dass Mehrbenutzerbetrieb die Authentisierung aus M2
voraussetzt, nicht nur nahelegt.

**Der harte Teil: mehrere Menschen entscheiden, wo der Dienst läuft.**
Abschnitt A setzt „der Mensch arbeitet in seinem bisherigen Checkout"
voraus, M1 „ein lokaler Dienst". Zwei Menschen haben zwei Rechner, zwei
Checkouts und — wenn jeder seinen eigenen Dienst startet — zwei SQLite-
Datenbanken über dieselben Tickets. Genau das ist die bidirektionale
Spiegelung, die 0b ausschließt, nur eine Ebene tiefer. Es gibt zwei saubere
Auswege:

1. **Ein gemeinsamer Dienst auf einem Host.** Menschen greifen über Web und
   CLI zu, die Agenten laufen dort, wo Zugangsdaten und Worktrees liegen.
   Der Dateiadapter bleibt möglich, weil es weiterhin genau eine führende
   Ablage gibt — auf dem Host. Das verlangt Authentisierung und macht aus
   dem „lokalen Dienst" einen kleinen Server; die Verträge ändert es nicht.
2. **Eine von Haus aus geteilte Quelle**, also GitHub Issues. Dann ist die
   führende Ablage ohnehin gemeinsam, und mehrere lokale Dienste sind
   denkbar — brauchen aber untereinander eine Claim-Regel, sonst starten
   zwei Dienste denselben Auftrag. Das ist die aufwendigere Variante.

Was **nicht** funktioniert, ist der naheliegende dritte Weg: jeder startet
seinen eigenen lokalen Dienst auf dem git-versionierten Ticketbranch und
gleicht per `push`/`pull` ab. Dann sind Ticketstatus und Ausführungsstand
zwei Repliken mit Merge-Konflikten, und die Zusage aus 0b ist verletzt.

**Antwort auf die Frage.** Abbildbar ist das, und der Aufwand am Modell ist
klein: `actor` mit `kind`, zwei Rechtestufen, `assignee`. Der Ausbau steckt
nicht im Datenmodell, sondern in Authentisierung und Betriebsform. Deshalb
mein Vorschlag: **Das Datenmodell schon in M1 mehrbenutzerfähig schneiden**
— IDs, `kind`, Rechtestufe und `assignee` von Anfang an, auch wenn nur Mike
eingetragen ist. Nachträglich einen Akteursbegriff einzuziehen, berührt
Owner, Board, Reports, Historie und jede Berechtigungsprüfung. Der
**Mehrbenutzerbetrieb** selbst bleibt hinter M2 und ist eine eigene Stufe,
zusammen mit der Entscheidung über den gemeinsamen Host.

## Kleinere Anmerkungen

- „Es gibt kein zusätzliches bearbeitbares Statusfeld im Ticket" gilt für den
  Dateiadapter. Beim GitHub-Adapter ist das Label dieses Feld; den Satz dort
  begrenzen, sonst widerspricht 0b sich selbst.
- Die Ordnernamen sind englisch, die Zustandsnamen im Text deutsch. Für die
  Verträge (DB, MCP, Konfiguration) sollte durchgehend die englische Form
  gelten und die deutsche nur Anzeige sein — sonst entsteht ein zweites
  Vokabular, das übersetzt werden muss.
- Der „Mindestvertrag" in Abschnitt 0 beschreibt für die beiden
  implementierenden Instanzen noch das alte Modell aus flachen Tickets und
  einem STATUS-Dokument. Wenn dieses Bootstrap-Ticketsystem von Anfang an
  dieselben neun Ordner benutzt, ist es der erste echte Test der Änderung, und
  die beiden Vokabulare laufen nicht auseinander.
- `Zurückgestellt` und `Verworfen` brauchen neben der Begründung auch das
  Datum und den Akteur; ohne beides ist „bewusst auf später verschoben" nach
  drei Monaten nicht mehr von „vergessen" zu unterscheiden.

## Was nur Mike entscheiden kann

1. **Liegen die Tickets im Produktrepo auf einem eigenen Branch mit eigenem
   Worktree, oder daneben ohne Versionierung?** (→ A; ich empfehle den
   eigenen Branch.)
2. **Darf eine KI `Bereit` setzen, oder ist Triage menschlich?** (→ D; ich
   empfehle menschlich, weil `Bereit` heißt „Anforderungen sind klar" — und
   das ist das Urteil, gegen das später geprüft wird.)
3. **Bekommt eine Wiedereröffnung ein frisches Rundenbudget?** (→ D; ich
   empfehle ja, aber ausschließlich durch einen menschlichen Zug.)
4. **Kommt der GitHub-Adapter erst nach der M1-Abnahme?** (→ F; ich empfehle
   ja.)
5. **Ist die Automatik pro Ticket opt-in oder opt-out?** (→ G; ich empfehle
   opt-in, solange Kontingente knapp sind.)
6. **Sollen mehrere Menschen am selben Projekt arbeiten können — und wenn
   ja, auf einem gemeinsamen Host oder über GitHub als Quelle?** (→ H; ich
   empfehle, das Datenmodell sofort mehrbenutzerfähig zu schneiden und den
   Betrieb auf einen gemeinsamen Host zu legen, sobald es so weit ist.)

Punkt 1 blockiert die weiteren Verträge: Solange die Ablage nicht feststeht,
sind Snapshot, Abgleich und Konfliktregeln nicht abschließend formulierbar.
Punkt 6 hängt daran — ein gemeinsamer Host verträgt sich mit dem
Dateiadapter, verteilte Rechner nicht. Die übrigen vier lassen sich
unabhängig voneinander entscheiden.
