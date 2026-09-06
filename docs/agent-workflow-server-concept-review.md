# Review: agent-workflow-server-concept.md

Stand: 6. September 2026. Gegenstand ist der Codex-Entwurf
[agent-workflow-server-concept.md](agent-workflow-server-concept.md).
Gegengelesen wurden zusätzlich die Setup-Datei
[claude-codex-ticket-system-setup.md](claude-codex-ticket-system-setup.md)
und der Auftragstext
[claude-agent-workflow-concept-prompt.md](claude-agent-workflow-concept-prompt.md).

Diese Datei ändert den Entwurf nicht. Sie sammelt Befunde und konkrete
Gegenvorschläge für den geplanten Vergleich beider Konzepte.

## Was der Entwurf gut löst

An den Stellen, an denen solche Konzepte üblicherweise unsauber werden, ist er
ungewöhnlich diszipliniert:

- Die Trennung **Konfiguration ≠ registrierter Timer ≠ Heartbeat ≠ echte
  Ausführung** (Abschnitt 9). Damit fällt die häufigste stille Lüge weg, eine
  gesetzte Einstellung sei bereits ein laufender Durchlauf.
- Die ausdrückliche Feststellung, dass eine MCP-Benachrichtigung keine
  schlafende Sitzung weckt (Abschnitt 3).
- Die Absage an Mehrheitswahl zwischen Modellen über fachliche Wahrheit
  (Abschnitt 4).
- Die Einbahnrichtung DB → Markdown statt zweier gleichberechtigter Wahrheiten
  (Abschnitt 11).

Die Befunde unten setzen darauf auf; sie stellen den Ansatz nicht in Frage.

## Befunde im Überblick

| Nr | Befund | Gewicht |
|---|---|---|
| 1 | `Snapshot` trägt die Beweislast und ist nirgends definiert | hoch |
| 2 | Stufenfolge testet die einzige technische Unbekannte zuletzt | hoch |
| 7 | Kontext als endliche Ressource kommt im Konzept nicht vor | hoch |
| 3 | Geltungsbereich von `revision` offen — global wäre ein Rückschritt | mittel |
| 4 | Mensch-Grenze wird als Durchsetzung beschrieben, ist aber Disziplin | mittel |
| 5 | Konvergenzbremse des Dateiboards fällt beim Übergang weg | mittel |
| 6 | „DB ist kanonisch" verliert die Haltbarkeit, die Git geschenkt hat | mittel |
| 8 | Finding-Lebenszyklus ohne Endzustand für einen falschen Befund | klein |

Die Nummerierung folgt der Reihenfolge der Erstbesprechung, nicht dem Gewicht.

---

## 1 · `Snapshot` ist das tragende Konzept — und das einzige ohne Definition

**Befund.** Das Wort kommt zwölfmal vor und trägt die gesamte Beweislast:
„Alle erforderlichen Prüfer müssen den identischen Snapshot freigeben",
„Report gehört zum konkreten Snapshot", „Gesamtfreigabe wartet auf alle
Pflichturteile desselben Snapshots". `git` kommt genau einmal vor (Zeile 329)
— und nur, um zu sagen, dass der *Dateimodus* damit arbeitet. `worktree`
kommt nicht vor.

Damit exportiert der Entwurf seine härteste Zusage nach außen. Abschnitt 5
sagt es selbst und lässt es offen: „Reviewer nutzen einen eingefrorenen
Snapshot **oder** getrennte schreibgeschützte Prüfumgebungen."

Das Dateiboard hatte dafür einen echten Mechanismus: `handoff_commit`,
`STATUS.md` identisch zu `HEAD`, Zielcommit als Vorfahr von `HEAD`, und eine
Drift-Gegenprobe unmittelbar vor dem Urteil. Der Server ersetzt diese
Disziplinregel durch eine Datenbanktransaktion — die schützt Zeilen, während
die Befunde über *Code* außerhalb der Transaktion liegen. Das ist in der
Zusicherung ein Rückschritt, kein Fortschritt.

**Vorschlag: Snapshot ist ein vom Dienst erzeugtes Git-Objekt, kein
Datenbankfeld.**

- Bei `handoff_submit` legt der Dienst selbst
  `refs/agentboard/snapshot/<handoff_id>` an und speichert `commit_sha` und
  `tree_sha`. Die Ref hält die Objekte am Leben, auch wenn der Branch
  weiterläuft — Unveränderlichkeit per Konstruktion statt per Zusage.
- Jeder Prüfer bekommt `git worktree add --detach` auf diese Ref: eigenes
  Verzeichnis, eigener Testlauf, eigener Port. Damit wird aus dem Hedge in
  Abschnitt 4 („sofern Testumgebung und Dateien sich nicht beeinflussen" — bei
  einem gemeinsamen Checkout praktisch nie erfüllt) echte Parallelität.
- `review_submit` nennt den `snapshot_id`; der Dienst prüft `tree_sha` und die
  Sauberkeit des Worktrees selbst. Drift heißt dann **Urteil abgewiesen**, nicht
  „der Reviewer möge nochmal nachsehen".

Ein Mechanismus, drei Baustellen. Zusätzlich schrumpft Risiko 2 der eigenen
Risikoliste („ein alter Agent schreibt trotz abgelaufenem Claim weiter in den
Checkout"): Der Schaden bleibt im Developer-Worktree und kann kein Prüfurteil
mehr verfälschen.

**Der eigentliche Gewinn liegt daneben.** Die OUTBOX-Tabelle (geplant/
tatsächlich, Produktdateien, Diff-Zeilen) ist heute eine Selbstauskunft des
Developers. Mit einer Snapshot-Ref rechnet der Dienst sie per
`git diff --numstat base..snapshot` selbst aus. Genau die Zahlen, deren
Erfindung das Musterregister überhaupt nötig gemacht hat, sind dann gemessen
statt behauptet.

## 2 · Die Stufenfolge baut das Sichere zuerst und testet das Unsichere zuletzt

**Befund.** Stufen 2 und 3 liefern Kern, SQLite, MCP, CLI und Web. Die einzige
Stelle, an der das Konzept ein technisches „weiß ich nicht" einräumt — ob eine
KI überhaupt verlässlich autonom startet — steht als Stufe 4 dahinter. Das ist
die Risikoreihenfolge verkehrt herum.

Die unausgesprochene Konsequenz: Bleibt es bei `client_poll`, weil
`managed_runner` nie zustande kommt, kaufen die Stufen 2–3 eine Oberfläche und
Transaktionssicherheit über *derselben* Polling-Schleife, die das Dateiboard
schon hat. Das kann eine völlig richtige Entscheidung sein — aber man trifft
sie vor dem Dienst, nicht nach ihm.

**Vorschlag: eine Stufe 0 vor Stufe 2.** Ein Wegwerf-Skript, das genau eine
Frage beantwortet: Läuft ein nicht-interaktiver Verifier-Durchlauf headless
durch und erzeugt einen brauchbaren Report? Überschaubarer Aufwand, und das
Ergebnis entscheidet die Architektur — bei positivem Ausgang ist
`managed_runner` der Normalfall und `client_poll` der Rückfall, nicht
umgekehrt. Derzeit diktiert eine ungetestete Vermutung den Betriebsmodus.

## 3 · Der Geltungsbereich von `revision` ist offen

**Befund.** Abschnitt 5 schafft das globale `reviewing`-Feld ausdrücklich ab
und ersetzt es durch mehrere Review-Läufe je Übergabe. Zwei Sätze später steht:
„Alle Mutationen nennen die erwartete Zustandsrevision." Wessen Revision? Bei
einer Revision pro Projekt kollidieren zwei Pflichtprüfer, die gleichzeitig
disjunkte Reports schreiben, und einer bekommt eine Stale-Ablehnung ohne
Sachkonflikt — der eben abgeschaffte globale Lock durch die Hintertür.

**Vorschlag.** Geltungsbereich explizit festschreiben: Revision je Aggregat
(`ReviewRun` für Prüfoperationen, `Ticket` für Ticketoperationen), nicht je
Projekt. Ein Satz im Dokument, sonst wird es in der Implementierung falsch
entschieden.

## 4 · Die Mensch-Grenze wird als Durchsetzung beschrieben, ist aber Disziplin

**Befund.** „Eine KI kann sich nicht durch ein übergebenes `agent_id`-Feld zum
Menschen erklären; der Dienst bindet die Identität an ihre Verbindung." Das
stimmt gegen ein gefälschtes Feld. Es stimmt nicht gegen einen Agenten mit
Shell-Zugriff auf demselben Rechner im Einbenutzerbetrieb ohne Auth — der ruft
den Web-Endpunkt per `curl` auf. Anforderung 9 („KI füllt die Human-Spalte
nicht aus") wird stärker zugesagt, als sie eingelöst ist.

**Vorschlag.** Entweder ein Admin-Token außerhalb des Agenten-Arbeitsbereichs
(`~/.config/…`, Modus 0600 — dieses Projekt hat mit der `.env`-Regel bereits
die passende Konvention), oder ausdrücklich hinschreiben, dass es eine
Disziplin- und keine Sicherheitsgrenze ist, und die **Nachweisbarkeit** zur
eigentlichen Kontrolle machen: jeder Human-Eintrag ein Ereignis mit Herkunft,
jede Abweichung sichtbar. Die zweite Variante ist billiger und trägt weiter als
eine Zusage, die bei der ersten Gegenprobe fällt.

## 5 · Die Konvergenzbremse fällt beim Übergang weg

**Befund.** Die Setup-Datei kennt sie: „Nach ungefähr drei inhaltlich
erfolglosen Entwurfsrunden prüfen beide Rollen, ob Ziel und Grundentscheidungen
stabil sind." Im Serverkonzept steht nichts Vergleichbares — der begrenzte
Wiederanlauf in Abschnitt 9 betrifft Laufzeitfehler, nicht Review-Runden.

Das ist der Punkt, an dem Automatisierung eine Regel kaputtmacht, statt sie zu
übernehmen: Die Drei-Runden-Regel wirkte, weil ein Mensch im Chat mitgelesen
hat. Mit Timer, drei Pflichtprüfern und „im MVP laufen Pflichtprüfungen neu"
merkt Runde 9 niemand — außer an der Abrechnung. Risiko 3 nennt nur die
Verzögerung, nicht die Kosten.

**Vorschlag.** Rundenzähler je Ticket mit sichtbarer Schwelle, danach
Pflicht-Konsolidierung oder `owner: human`; dazu ein Laufbudget je Ticket und
Tag in der Übersicht. Die Oberfläche dafür existiert im Entwurf bereits.

## 6 · „DB ist kanonisch" verliert die Haltbarkeit, die Git geschenkt hat

**Befund.** Im Dateimodus liegen Reports und Findings in der Git-Historie:
versioniert, ohne Dienst lesbar, praktisch unverlierbar. Im Servermodus ist die
DB kanonisch und Markdown „lesbarer Export" — nirgends steht, dass dieser
Export je committet wird. Eine kaputte SQLite-Datei kostet dann sämtliche
Reports.

**Vorschlag.** Der Dienst committet den Export selbst, je Zustandsübergang oder
je Übergabe. Kostet fast nichts, stellt die Haltbarkeit wieder her und erhält
nebenbei die Eigenschaft, dass ein Freund das Board ohne laufenden Server lesen
kann.

## 7 · Kontext ist eine endliche Ressource — das Konzept weiß nichts davon

**Befund.** Der Entwurf modelliert Zeit (Intervalle, Laufzeitgrenzen,
Heartbeat) und Nebenläufigkeit (Claims, Revisionen) sorgfältig. Die Ressource,
die in der Praxis zuerst ausgeht, kommt nicht vor: der Kontext der Sitzung.
Erfahrungswert aus dem laufenden Betrieb dieses Projekts — unabhängig vom
Anbieter — ist ein spürbarer Qualitätsabfall ab grob 100k Token. Ein Lauf mit
`max. eine aktive Ausführung` und „Laufzeitgrenze" endet damit an der falschen
Größe: Die Uhr sagt nichts darüber, ob das Modell noch gut arbeitet.

Das ist nicht bloß ein fehlender Zähler. Es fehlt der **Zustandsübergang**, den
ein volles Kontextfenster braucht: Ein Lauf, der abbricht, ohne einen
verwertbaren Zwischenstand zu hinterlassen, wirft die gesamte Arbeit weg — und
Abschnitt 9 kennt für das Ende eines Laufs nur `interrupted` und „Abbrechen".

**Vorschlag: `context_budget` als konfigurierbare Größe je Rollenprofil, mit
zwei Schwellen und einem eigenen Abschlussweg.**

### `context_budget` ist eine gesetzte Arbeitsgrenze, nicht das Kontextfenster

Das ist die entscheidende Festlegung, und sie gehört vor alles andere:
`context_budget` ist ein **absolut konfigurierter Wert** — Startwert 100 000
Token — und wird ausdrücklich *nicht* aus der Fenstergröße des Modells
abgeleitet. Die beobachtete Verschlechterung setzt lange vor dem vollen Fenster
ein; sie ist ein Erfahrungswert, kein Bruchteil der Kapazität.

Daraus folgt unmittelbar: **Ein Modell mit größerem Fenster bekommt nicht
automatisch ein größeres Budget.** Der Wechsel auf ein 1M-Fenster hebt die
Grenze nicht an. Wer sie anheben will, tut das als bewusste Entscheidung mit
Beleg — etwa Läufen, die jenseits der bisherigen Grenze nachweislich noch
saubere Ergebnisse geliefert haben.

Das Fenster des Modells dient nur als Plausibilitätsschranke: Ist das
konfigurierte Budget größer als das gemeldete Fenster, ist die Konfiguration
falsch, und der Dienst sagt das beim Setzen statt beim Auslösen.

Konfiguriert wird der Wert je Rollenprofil — ein Verifier, der viel fremden
Code liest, verbraucht anders als ein Developer — wie jede andere Einstellung
über CLI und Web mit Revisionsprüfung (Abschnitt 8).

### Zwei Schwellen, nicht eine

Eine harte Obergrenze allein feuert zu spät. Das Schreiben eines brauchbaren
Zwischenstands kostet selbst Kontext — und die Fähigkeit, den eigenen
Arbeitsstand präzise zu beschreiben, degradiert gemeinsam mit allem anderen.
Wer bei Erschöpfung auslöst, bekommt den schlechtesten Checkpoint genau dann,
wenn er am meisten zählt.

| Schwelle | Vorgabe | Wirkung auf den Lauf |
|---|---|---|
| `soft_limit` (Startwert 60 %) | Kein neues Teilziel mehr beginnen | Auf einen abschließbaren Stand zuarbeiten |
| `hard_limit` (Startwert 80 %) | Nur noch den Checkpoint schreiben | `checkpoint_submit`, danach Lauf beenden |

**Beide Prozentwerte beziehen sich auf `context_budget`, nicht auf das
Kontextfenster.** Bei einem Budget von 100 000 Token heißt das 60 000 und
80 000 — unabhängig davon, ob das Modell 200 000 oder eine Million fasst. Die
Oberfläche zeigt entsprechend absolute Zahlen gegen das Budget („62 000 /
100 000"), keinen Fensterfüllstand; sonst liest jemand die Anzeige als „noch
viel Platz", während die Arbeitsgrenze längst erreicht ist.

### Der Dienst kann den Kontext nicht messen — das gehört hingeschrieben

Der Server sieht MCP-Aufrufe, nicht das Kontextfenster der Sitzung. Der Wert
kommt also per `work_heartbeat` als `context_used` vom Agenten selbst und ist
damit eine **Selbstauskunft**, nicht eine Messung — dieselbe Kategorie wie die
Diff-Zahlen der OUTBOX, und derselbe Vorbehalt. Der Entwurf sollte das genauso
klar sagen wie beim Wecken schlafender Sitzungen (Abschnitt 3).

Als Gegengewicht kennt der Dienst Ersatzgrößen, die er tatsächlich misst:
Laufdauer, Zahl der gesehenen Tool-Runden, Zahl der Übergaben im Ticket, Größe
des bisherigen Diffs. Auslösen sollte, was zuerst greift; die Oberfläche zeigt,
welche Größe ausgelöst hat. Eine Schwelle, die immer über die Ersatzgröße
kommt, ist ein Hinweis auf falsch gemeldete Selbstauskunft.

### Der Kontext-Checkpoint ist nicht der Scope-Checkpoint

Die Maschinerie existiert bereits fast vollständig: stabilen Zwischenstand
committen, Auslöser und Plan/Ist nennen, per eigenem Statuscommit übergeben.
Verwechseln darf man beide trotzdem nicht, denn sie stellen verschiedene Fragen:

| | Scope-Checkpoint | Kontext-Checkpoint |
|---|---|---|
| Auslöser | Umfang wächst über die Vereinbarung | `hard_limit` erreicht |
| Frage | Ist der Zuschnitt noch richtig? | Kann eine frische Sitzung hier weitermachen? |
| Entscheidungen | `continue`, `reduce`, `split`, `human` | `resume_fresh`, `split`, `handover`, `human` |
| Zählt als Runde? | Nein | Nein — siehe unten |

`resume_fresh` bedeutet: gleiches Ticket, gleicher Scope, neue Sitzung mit
leerem Kontext. `handover` gibt an einen anderen Agenten ab — das ist der
Fall, in dem die Trennung von Rolle und Sitzung aus Abschnitt 4 sich das erste
Mal wirklich auszahlt.

### Die Qualität des Checkpoints wird an der Fortsetzung gemessen

Das ist der Teil, der die Idee über eine gute Absicht hinaushebt. Ein
Kontext-Checkpoint ist genau dann gültig, wenn eine Sitzung, die die
Unterhaltung nie gesehen hat, damit weiterarbeiten kann. Das ist prüfbar, weil
die Fortsetzung ohnehin von einer frischen Sitzung erledigt wird: Muss die
frische Sitzung Fragen stellen, die der Checkpoint hätte beantworten müssen,
war er mangelhaft — und das ist ein belegter Befund für das Musterregister,
nicht bloß ein Ärgernis. Der Lernkreislauf aus Abschnitt 6 nimmt diese
Fehlerklasse ohne Erweiterung auf.

### Anschlüsse an den übrigen Entwurf

- **Eigener Endzustand.** Budget-Erschöpfung endet einen Lauf als
  `exhausted`/`checkpointed`, nicht als `interrupted`. Das ist ein geordnetes
  Ende, kein Ausfall, und die Oberfläche muss es unterscheiden.
- **Kein falscher Rundenzähler.** Ein Kontext-Checkpoint zählt nicht als
  erfolglose Entwurfsrunde im Sinne von Befund 5. Sonst sieht ein Ticket, das
  nur zu groß für ein Fenster war, aus wie ein Ticket, das nicht konvergiert —
  zwei Probleme mit gegenteiliger Behandlung.
- **Prüfer laufen genauso leer.** Ein Verifier, dem mitten im Review der
  Kontext ausgeht, darf keine Teilfreigabe liefern. Die Setup-Datei hat die
  Regel bereits: abgebrochenes Review → ausdrücklich unvollständiger Report,
  kein Freigabeclaim, kein `last_reviewed_*`. Im Server heißt das: der
  `ReviewRun` endet `incomplete`, der Report wird ohne Urteil gespeichert, die
  Übergabe bleibt offen. Zusammen mit Befund 1 ist die Wiederholung billig —
  der frische Prüfer bekommt denselben Worktree auf derselben Snapshot-Ref,
  ganz ohne Drift.
- **Verdichtung ist ein Ereignis.** Wenn die Laufzeitumgebung den Kontext still
  verdichtet, arbeitet der Agent mit einer Zusammenfassung weiter und verliert
  womöglich genau die Zusagen, auf die er sich verpflichtet hat. Ein Sprung von
  `context_used` nach unten bei weiterlaufendem Lauf ist messbar: Der Dienst
  schreibt ein `context_reset`-Ereignis, die Oberfläche zeigt es, und der
  Verifier weiß, dass Vollständigkeitsbehauptungen ab dieser Stelle besonders
  zu prüfen sind. Das trifft eine hier bereits belegte Fehlerklasse.

### Kleinster nützlicher Umfang

Für den MVP genügt: eine konfigurierbare Zahl je Rollenprofil, `context_used`
im Heartbeat, zwei Schwellen, ein zusätzlicher Laufzustand und eine
MCP-Operation `checkpoint_submit`. Ersatzgrößen, `context_reset`-Erkennung und
`handover` sind Ausbau. Die Gegenprobe für Stufe 2 lautet dann: **Ein Ticket
wird absichtlich über das Budget getrieben, per Checkpoint übergeben und von
einer frischen Sitzung ohne Rückfragen zu Ende gebracht.**

## 8 · Finding-Lebenszyklus ohne Endzustand für einen falschen Befund

**Befund.** `open`, `disputed`, `resolved`, `accepted` decken den Fall nicht
ab, dass ein Finding sich als falsch herausstellt. Ein irrtümlicher Befund
bleibt entweder dauerhaft `disputed` oder wird vom Menschen fälschlich
`accepted` — beides verzerrt die Statistik, aus der später Muster entstehen.

**Vorschlag.** Endzustand `withdrawn` mit Begründung des Verifiers. Dazu die
Angabe, wer einen `disputed`-Stillstand auflöst; heute steht nur, dass die
Gegenprobe entscheidet, nicht was bei beidseitigem Beharren geschieht.

---

## Verfahrenshinweis

Diese Review ist nach Lektüre des Codex-Entwurfs entstanden. Für das
unabhängige Claude-Konzept aus `claude-agent-workflow-concept-prompt.md` ist
die verfassende Sitzung damit als unbeeinflusste Autorin ausgeschieden — das
braucht eine frische Sitzung oder die Offenlegung, die der Auftragstext
ausdrücklich dafür vorsieht.
