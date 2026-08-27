# Codex-Review-Automation

Dieses Dokument ist der stabile Vertrag für den periodischen Claude→Codex-
Review. Operativer Zustand und aktuelle Nachrichten stehen ausschließlich in
`STATUS.md`; dieses Dokument enthält keine Laufhistorie.

Der kurze Laufzeitvertrag des internen Schedulers steht separat in
`CODEX-IN-CONTEXT-SCHEDULER.md`. Er läuft **in dem bestehenden
Codex-Review-Chat** und ist weder `/goal` noch ein ChatGPT-Scheduled-Task oder
eine Desktop-App-Automation. So kehrt nur eine neue Übergabe in denselben
fachlichen Kontext zurück. Die Chat-Historie ist die kurzfristige Lernschicht;
das versionierte
`CLAUDE-REVIEW-PATTERNS.md` ist die kanonische, compaction- und
sitzungsfeste Lernschicht sowie die Datenbasis für den späteren Skill.

## Zustandsprotokoll

`STATUS.md` enthält unter **Maschinenlesbarer Zustand** genau diese Felder:

- `phase`: `claude_working`, `ready_for_codex`, `codex_reviewing`,
  `changes_requested`, `approved`, `portfolio_review` oder `blocked`
- `ticket`: Ticketdatei im Board-Root
- `handoff_commit`: exakt zu prüfender Produkt-Commit
- `review_round`: bei jeder neuen Übergabe hochzählen
- `owner`: `claude`, `codex` oder `mike`
- `updated_at`: lokales Datum im Format `YYYY-MM-DD`
- `last_reviewed_ticket`, `last_reviewed_commit`, `last_reviewed_round`:
  zuletzt abgeschlossenes Review-Tupel zur dauerhaften Duplikatsperre
- `workstream`: aktuell priorisierter Arbeitsstrom
- `priority_chain`: ausdrücklich freigegebene Ticketreihenfolge
- `priority_ticket`: genau das Ticket, das jetzt bearbeitet werden darf

Der eindeutige Schlüssel eines Reviews ist
`(ticket, handoff_commit, review_round)`. Derselbe Schlüssel wird nie zweimal
bearbeitet.

Claude commitet vor der Übergabe die Produktänderungen, beschreibt sie in
`OUTBOX → Codex`, setzt `ready_for_codex` und `owner: codex` und verändert
danach keinen Produktcode mehr. Ein nachfolgender Commit darf ausschließlich
Kommunikations- oder Ticketdateien enthalten.

Codex prüft nur `ready_for_codex`. Nach den Vorbedingungen setzt Codex
`codex_reviewing`. Codex verändert im Review keinen Produktcode, keine
Human-Spalte und verschiebt kein Ticket nach `solved/`. Das Ergebnis kommt in
`INBOX → Claude`; die verarbeitete OUTBOX-Nachricht wird entfernt. Danach ist
die Phase `approved` oder `changes_requested`, **beide mit `owner: claude`**.
Bei einem echten, nicht sicher lösbaren Hindernis gilt `blocked` mit
`owner: mike`.

## Portfolio-Riegel — das richtige Ergebnis vor lokaler Perfektion

*(Ergänzt 2026-08-27 nach 52 T-21-Runden ohne lauffähigen Plugin-Host.)*

Ein korrektes Review-Tupel genügt nicht, wenn das falsche Ticket bearbeitet
wird. `priority_chain` ist deshalb eine Produktentscheidung, keine
unverbindliche Empfehlung:

- `ticket` muss bei Arbeit und Übergabe exakt `priority_ticket` entsprechen.
- Ein Review-Finding erzeugt keine neue Priorität. Folgearbeiten kommen ins
  Board und werden erst durch eine ausdrückliche Portfolio-Entscheidung in die
  Kette aufgenommen.
- Nach einer Freigabe wird nur auf das **nächste Element derselben Kette**
  weitergeschaltet. Es gibt kein automatisches „nächstes Teilstück“ und keine
  Sortierung nach Ticketnummer.
- Nach dem letzten Element wechselt der Zustand auf `portfolio_review` mit
  `owner: mike`. Erst die Einordnung der übrigen Tickets in Gate oder Follow-up
  setzt eine neue Kette.
- Der Scheduler lehnt ein `ready_for_codex` außerhalb der Priorität mit
  `portfolio_mismatch` ab. Codex reviewt diesen Handoff nicht.

Aktuell lautet die von Mike bestätigte MVP-Kette **T-22 → T-27a → T-27b →
T-23**. Ihr Ziel ist nicht mehr Vorarbeit, sondern ein belegter Lauf
**Registry → Core → REST** über beide Ladewege.

**Warum eine Freigabe nicht bei Mike landet** *(Entscheidung Mike,
2026-08-22)*: Als dieser Vertrag entstand, hieß `approved` „Codex ist durch,
jetzt kommt Mikes Abnahme" — pro Ticket. Wenige Stunden später ist entschieden
worden, dass die Abnahme **gesammelt am Ende über T-28** läuft. Damit stand
hinter `owner: mike` keine Arbeit mehr; die Reihe blieb nach jeder Freigabe
stehen, bis Mike sie von Hand weiterschob. Bei `blocked` bleibt er Eigentümer
— dort braucht es ihn wirklich.

## Entwurfsrunden — wenn noch kein Produktcode existiert

*(Ergänzt 2026-08-24, nach einem Blocker in T-21 Runde 12.)*

Ein Ticket darf **vor** der Umsetzung in die Prüfung gehen: Bei T-21 Teil 3 hat
sich der Zuschnitt zweimal als falsch erwiesen, und ein Entwurf ist billiger zu
widerlegen als eine Umsetzung. Für solche Runden gilt der Vertrag oben mit drei
Abweichungen:

- **Der `handoff_commit` enthält keinen Produktcode**, sondern Spec- und
  Ticketdateien. Die Vorbedingung „alle Commits danach betreffen nur
  `_tickets/`" gilt **unverändert weiter** — auch `docs/superpowers/specs/`
  zählt in einer Entwurfsrunde als eingefrorener Inhalt.
- **Geprüft wird der Dateistand**, nicht nur der Diff. Ein Entwurf wird über
  mehrere Runden umgeschrieben; sein Diff gegen den Vorgänger sagt weniger als
  das Dokument selbst. Die OUTBOX nennt die zu prüfenden Dateien beim Namen.
- **Testläufe belegen den unveränderten Produktstand**, nicht den Entwurf. Sie
  gehören trotzdem in den Bericht, damit sichtbar bleibt, dass nichts abgerutscht
  ist.

**Die Reihenfolge, an der es schon einmal gescheitert ist:** erst den Inhalt
**vollständig** fertigstellen, dann committen, dann diesen Commit als
`handoff_commit` eintragen — und danach ausschließlich `_tickets/` anfassen.
Eine nachgezogene Statuszeile im Entwurf ist Inhalt, keine Formalie.

### Konvergenzprüfung statt starrer Rundengrenze

Mehrere Entwurfsrunden sind kein Qualitätsmerkmal und ihre Anzahl allein ist
auch kein Abbruchgrund. Als **grober Richtwert** lösen ungefähr drei
aufeinanderfolgende inhaltlich erfolglose Reviews desselben Entwurfsscope eine
ausdrückliche Konvergenzprüfung aus. Ein formaler Handoff-Blocker zählt dabei
nicht als inhaltlich erfolglose Runde.

Der Reviewer beantwortet dann im Review knapp:

1. Sind die Grundentscheidungen stabil und alle betroffenen Schichten
   inventarisiert?
2. Ist der verbleibende Rest konkret, klein und abschließend benennbar?
3. Fehlt weder eine Produktentscheidung noch ein weiterer unabhängiger Scope?
4. Warum ist eine weitere Korrekturrunde voraussichtlich die letzte — oder
   warum wäre diese Annahme nicht belastbar?

Sind Rest und Abschlussweg konkret, ist auch eine vierte oder weitere Runde
zulässig. Der Richtwert ist **keine absolute Grenze**. Je länger die Schleife
läuft, desto konkreter muss jedoch die Begründung für eine weitere punktuelle
Korrektur sein. Ist keine belastbare Konvergenz absehbar, endet die
Patch-Schleife: Claude erstellt eine konsolidierte Neufassung oder verkleinert
den Scope auf ein beobachtbares Ergebnis. Eine neue Grundentscheidung löst
dieselbe Neubewertung sofort aus; abhängige alte Aussagen, Tests und
Verify-Markierungen werden nicht nur mit Nachträgen überklebt.

Die Konvergenzprüfung ändert die Rollen nicht. Ein technischer Rebaseline- oder
Split-Auftrag bleibt `changes_requested` mit `owner: claude`. `blocked` und
`owner: mike` gelten weiterhin ausschließlich für ein echtes Hindernis oder
eine tatsächlich notwendige Produktentscheidung. Nach jeder weiteren
inhaltlich erfolglosen Entwurfsrunde wird die Konvergenz erneut beurteilt.

## Der Übergabe-Riegel — `ready_for_codex` steht zuletzt

*(Ergänzt 2026-08-24, nach einer Race Condition in Runde 15.)*

`STATUS.md` ist ein **gemeinsamer Dateihub**, kein Postfach mit Sperre. Codex
liest die Datei, nicht den Git-Verlauf. Sobald dort `ready_for_codex` steht,
darf er claimen — auch wenn der Rest der Datei noch halb geschrieben ist.

In Runde 15 stand `phase: ready_for_codex` bereits auf der Platte, während die
`OUTBOX → Codex` noch leer war. Codex hat in genau diesem Fenster geclaimt und
ein Review ohne Nachricht begonnen. Kein Schaden, aber sichtbar Glück.

**Deshalb gilt für Claude bei jeder Übergabe diese Reihenfolge, ohne Ausnahme:**

1. Inhalt fertigstellen und committen.
2. `INBOX` leeren und `OUTBOX` **vollständig** schreiben.
3. **Zuletzt** `phase`, `owner`, `handoff_commit` und `review_round` setzen.
4. Sofort committen — der Zustand soll nicht länger als nötig nur auf der
   Platte liegen.

Schritt 3 ist der Riegel: Vorher gibt es nichts zu claimen. **Nach dem Claim
schreibt Claude bis zum Review-Ergebnis nicht mehr in `STATUS.md`** — auch nicht
„nur schnell" einen Tippfehler.

**Eng begrenzte Selbstheilung bei ausgebliebenem Status-Commit:** Findet Codex
einen vollständigen `ready_for_codex`-Zustand nur uncommitted im Worktree, wartet
er kurz auf Claudes unmittelbar folgenden Commit. Bleibt er aus, darf Codex die
Übergabe nur dann atomar claimen und mitsichern, wenn ausschließlich
`_tickets/STATUS.md` verändert ist, die OUTBOX vollständig ist und der genannte
Produkt-Commit existiert. Bei weiteren Dirty-Dateien, unvollständiger OUTBOX
oder widersprüchlichem Handoff wird nicht geraten: formaler Handoff-Fehler.
Diese Ausnahme heilt nur den Transport; sie ersetzt nicht Claudes Pflicht,
jede Übergabe sofort zu committen.

## Ausführungs-Guard für Ticket-Prüfskripte

Mike hat die Ausführung aller versionierten Prüfskripte nach dem Muster
`./_tickets/T-*.sh` ausdrücklich und dauerhaft freigegeben. Codex darf diese
Skripte im Review ohne erneute fachliche Rückfrage ausführen, einschließlich
der für lokale Testserver oder externe Testquellen nötigen Sandbox-Freigabe.
Vor dem Lauf bleibt die übliche Sicherheitsprüfung des konkreten Skripts
verbindlich; die Freigabe erweitert weder den erlaubten Review-Scope noch die
Berechtigung, Produktcode oder fremde Ressourcen zu verändern.

## Browsertests macht Claude — nicht als Arbeitsteilung, sondern mangels Browser

*(Entscheidung Mike, 2026-08-27, nach Runde 51.)*

**Codex kann keine Browsertests ausführen.** Seine Umgebung hat keinen
verbundenen Browser; er hat das in Runde 51 selbst so gemeldet („Ein echter
Desktop-/Mobile-Browsercheck war in dieser Codex-Umgebung nicht möglich"). Das
ist keine Frage der Gelegenheit, sondern der Ausstattung — es wird sich beim
nächsten Review nicht anders verhalten.

Daraus folgt eine Rollenregel, die von der übrigen Aufteilung abweicht:

* **Claude führt visuelle Prüfungen aus** — in breiter und schmaler Ansicht,
  nach `ux-standards`: gemessen, nicht geschätzt (waagrechter Überhang,
  Höhe der Leisten, Kanten von Kopf/Inhalt/Fuß, Kontrast gegen die
  **gerenderte** Fläche).
* **Codex prüft das Ergebnis**, so wie er Code und Tests prüft — er verlangt
  die Messung, liest die Zahlen und widerspricht ihnen, wenn sie nicht tragen.
  Er wiederholt sie nicht.
* **Eine ungemessene Oberfläche wird benannt, nicht verschwiegen.** Wo eine
  Übergabe ohne visuelle Prüfung herausgeht, steht in der OUTBOX, **was**
  ungemessen blieb — nicht nur, dass etwas fehlt. „Die Toastbreite in schmaler
  Ansicht" ist eine Lücke, „visuelle QA offen" ist eine Floskel.

Der Grund, warum das hier steht und nicht nur im Ticket: Ohne die Regel fragt
Codex bei jeder UI-Übergabe nach einem Check, den er nicht bekommen kann, und
Claude verweist auf eine Zuständigkeit, die nirgends steht. Beides kostet je
eine Runde.

## DRY-Prüfguard

DRY ist eine **eigene Abnahmebedingung** und darf nicht still unter dem
Sammelbegriff „Code-Standards“ verschwinden. Jeder inhaltliche Review prüft den
Übergabediff und den berührten Umgebungscode ausdrücklich auf doppelte
Implementierung und doppelte Wissensquellen.

Dabei gilt:

- Jede neue oder geänderte Regel, Konstante, Zuordnung, Validierung,
  Transformation, Fehlerbehandlung und Hilfsfunktion wird mit `rg` im gesamten
  Projekt gesucht. Geprüft wird auch gegen vorhandene Package-Utilities,
  Composables sowie `.libs/`; ein anderer Name oder leicht abweichende Syntax
  macht dieselbe Fachregel nicht zu neuer Logik.
- Zwei Stellen mit identischer oder fast identischer Fachlogik sind bereits
  eine DRY-Verletzung. Besonders kritisch sind parallele Sources of Truth wie
  mehrfach gepflegte Feldlisten, Statuswerte, Regex-Regeln, Börsen-/Provider-
  Mappings, Endpoint-Pfade und Serialisierungsregeln.
- Tests und Prüfskripte sind nicht ausgenommen. Wiederholtes Setup gehört in
  Fixtures oder Helper; wiederverwendbare Bash-Logik in BashLib. Eigenständige
  Erwartungen dürfen denselben fachlichen Wert dagegen bewusst wiederholen,
  wenn gerade diese Unabhängigkeit ein belastbares Orakel bildet.
- Notwendiges Wiring, Protokoll-Implementierungen und absichtlich unabhängige
  Orakel sind nicht automatisch Duplikation. Wo DRY und KISS kollidieren, muss
  die Nicht-Extraktion fachlich begründet sein; bloß grüne Tests sind keine
  Begründung.
- Das Review-Ergebnis nennt immer knapp den geprüften DRY-Scope und das
  Ergebnis. Ein gefundener Kandidat wird bis zur gemeinsamen Wissensquelle
  zurückverfolgt; bei einem Finding stehen beide Fundstellen und die erwartete
  gemeinsame Abstraktion oder Source of Truth dabei.

## Trigger für den Codex-In-Context-Scheduler

Der Scheduler enthält keine Kopie des Review-Verfahrens. Sein vollständiger
Auftrag ist:

```text
Führe _tickets/CODEX-IN-CONTEXT-SCHEDULER.md aus.
```

Erst wenn dieser kurze Vertrag eine neue Übergabe erkennt, liest Codex dieses
Dokument und `CLAUDE-REVIEW-PATTERNS.md` vollständig und führt das Review aus.
Damit kosten Leerdurchläufe nur den Zustandscheck; die ausführlichen Regeln
bleiben trotzdem versioniert und überstehen Exit sowie Compaction.

## Prompt für den periodischen Claude-Loop

Das Gegenstück zum Codex-Task: Claude fragt im selben Takt, ob eine Antwort
aus dem Review auf ihn wartet. Als `/loop` **im laufenden Arbeits-Chat**
starten, damit derselbe Branch und dasselbe `STATUS.md` gesehen werden. Beim
Ausstieg wird der Loop gelöscht; dieser Abschnitt hält ihn wiederherstellbar.

```text
/loop 5m Du bist Claude, der Implementierer im StockInfo-Board. Beachte CLAUDE.md und die Skills task-verification-workflow, code-standards, git-conventions.

1. Lies _tickets/STATUS.md, _tickets/CODEX-REVIEW-AUTOMATION.md und _tickets/CLAUDE-REVIEW-PATTERNS.md. Der maschinenlesbare Zustand oben in STATUS.md ist massgeblich, nicht dein Gedaechtnis. Pruefe vor jeder Arbeit: ticket muss exakt priority_ticket entsprechen und in priority_chain stehen. Bei Abweichung nichts implementieren, portfolio_mismatch melden und Schluss.
2. Ist `owner` nicht `claude`: veraendere keine Datei, antworte in einer Zeile mit Phase und Owner, Schluss.
3. Bei `phase: changes_requested`: Arbeite die Findings aus INBOX -> Claude der Reihe nach ab, schwerste zuerst. Jedes Finding einzeln verifizieren statt der Zusammenfassung glauben; behauptete Vollstaendigkeit mit rg belegen. Bei wiederholter Entwurfsnacharbeit gilt die Konvergenzpruefung dieses Dokuments: ungefaehr drei erfolglose Runden sind ein Richtwert, keine harte Grenze. Ist eine weitere punktuelle Runde konkret und voraussichtlich abschliessend, begruende das mit dem vollstaendigen Restumfang in der OUTBOX. Verlangt das Review Rebaseline oder Scope-Verkleinerung, korrigiere nicht weiter lokal, sondern konsolidiere beziehungsweise schneide neu. Vor dem ersten Edit auf einem Feature-Branch `t-NN-<slug>` sein. Danach relevante Pytests, das Ticket-Smoke-Script `./_tickets/T-*.sh --run` und `make test` laufen lassen und die Ergebnisse mit Zahlen nennen. Dann genau EIN Uebergabe-Commit, INBOX leeren, Ergebnis nach OUTBOX -> Codex, `review_round` +1, `phase: ready_for_codex`, `owner: codex`, `updated_at` auf heute. Danach keinen Produktcode mehr anfassen.
4. Bei `phase: approved`: Ticket NICHT nach solved/ verschieben, das macht Mike. Nur zum naechsten Element aus priority_chain wechseln, priority_ticket und ticket gemeinsam setzen, review_round fuer das neue Ticket auf 1 setzen, eigener Branch vor dem ersten Edit, phase: claude_working. War das freigegebene Ticket das letzte Element, nichts Neues beginnen: phase: portfolio_review, owner: mike; Mike braucht die Gate-vs-Follow-up-Einordnung.
5. Bei `phase: claude_working`: die begonnene Arbeit fortsetzen, sonst wie Punkt 3 uebergeben.
6. Bei `phase: blocked`, `phase: portfolio_review` oder wenn eine Entscheidung von Mike noetig ist: nichts weiterschreiben, in einer Zeile melden, `owner: mike` lassen und den Loop stoppen.
7. Melde nur Uebergabe, Blocker oder Entscheidungsbedarf. Leerdurchlaeufe bleiben einzeilig.
```

Beide Loops teilen sich denselben Zustandsfilter: Genau einer von beiden ist
über `owner` je Runde am Zug, der andere beendet seinen Lauf einzeilig. Läuft
nur ein Agent, bleibt der andere Takt wirkungslos, aber ungefährlich.
