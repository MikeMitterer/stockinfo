# Codex-Review-Automation

Dieses Dokument ist der stabile Vertrag für den periodischen Claude→Codex-
Review. Operativer Zustand und aktuelle Nachrichten stehen ausschließlich in
`STATUS.md`; dieses Dokument enthält keine Laufhistorie.

Der Scheduled Task läuft **in dem bestehenden Codex-Review-Chat**, nicht als
Standalone-Task. So kehrt jeder Lauf in denselben fachlichen Kontext zurück.
Die Chat-Historie ist die kurzfristige Lernschicht; das versionierte
`CLAUDE-REVIEW-PATTERNS.md` ist die kanonische, compaction- und
sitzungsfeste Lernschicht sowie die Datenbasis für den späteren Skill.

## Zustandsprotokoll

`STATUS.md` enthält unter **Maschinenlesbarer Zustand** genau diese Felder:

- `phase`: `claude_working`, `ready_for_codex`, `codex_reviewing`,
  `changes_requested`, `approved` oder `blocked`
- `ticket`: Ticketdatei im Board-Root
- `handoff_commit`: exakt zu prüfender Produkt-Commit
- `review_round`: bei jeder neuen Übergabe hochzählen
- `owner`: `claude`, `codex` oder `mike`
- `updated_at`: lokales Datum im Format `YYYY-MM-DD`
- `last_reviewed_ticket`, `last_reviewed_commit`, `last_reviewed_round`:
  zuletzt abgeschlossenes Review-Tupel zur dauerhaften Duplikatsperre

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

## Ausführungs-Guard für Ticket-Prüfskripte

Mike hat die Ausführung aller versionierten Prüfskripte nach dem Muster
`./_tickets/T-*.sh` ausdrücklich und dauerhaft freigegeben. Codex darf diese
Skripte im Review ohne erneute fachliche Rückfrage ausführen, einschließlich
der für lokale Testserver oder externe Testquellen nötigen Sandbox-Freigabe.
Vor dem Lauf bleibt die übliche Sicherheitsprüfung des konkreten Skripts
verbindlich; die Freigabe erweitert weder den erlaubten Review-Scope noch die
Berechtigung, Produktcode oder fremde Ressourcen zu verändern.

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

## Prompt für den periodischen Codex-Task

Den folgenden Prompt als Scheduled Task **in diesem bestehenden Review-Chat**
für dieses **lokale Projekt** verwenden. Keinen Standalone-Task und keinen
separaten Worktree wählen: Claude und Codex müssen dasselbe `STATUS.md` und
denselben Branch sehen. Ein bereits bestehender Standalone-Task wird pausiert
oder gelöscht, damit nicht zwei Reviewer dieselbe Übergabe bearbeiten.

```text
Du bist der unabhängige Reviewer für Claudes Arbeit im Projekt StockInfo.
Dieser Scheduled Task kehrt alle fünf Minuten in den bestehenden Review-Chat
zurück. Nutze dessen bisherigen Kontext für die fortlaufende Mustererkennung,
aber behandle die versionierten Projektdateien als kanonischen Zustand.
Arbeite ausschließlich im aktuellen lokalen Projekt und beachte AGENTS.md,
CLAUDE.md sowie die zutreffenden Skills, insbesondere
task-verification-workflow und code-standards.

1. Lies zuerst _tickets/STATUS.md,
   _tickets/CODEX-REVIEW-AUTOMATION.md und
   _tickets/CLAUDE-REVIEW-PATTERNS.md vollständig. Diese Dateien sind das
   Gedächtnis nach einer Chat-Compaction. Verbinde sie mit den bisherigen
   Beobachtungen dieses Chats, statt bei jedem Lauf bei null anzufangen.
2. Wenn phase nicht ready_for_codex ist: Verändere keine Datei und antworte
   knapp "Keine neue Claude-Übergabe" mit aktueller Phase. Beende den Lauf.
3. Validiere bei ready_for_codex vor jedem Schreibzugriff:
   - ticket, handoff_commit und review_round sind gesetzt;
   - Ticketdatei und Commit existieren;
   - handoff_commit ist Vorfahr von HEAD;
   - alle Commits danach betreffen nur _tickets/ bzw. Kommunikationsdateien;
   - der Arbeitsbaum enthält keine uncommittierten Produktänderungen.
   Ist eine Bedingung verletzt, setze phase blocked und owner mike, schreibe
   den konkreten Grund in INBOX → Claude und beende den Lauf.
4. Prüfe, dass dieses Tupel (ticket, handoff_commit, review_round) nicht den
   drei last_reviewed_*-Feldern entspricht. Setze dann phase codex_reviewing,
   owner codex und aktualisiere updated_at.
5. Prüfe unabhängig:
   - Ticket, Spezifikation und Akzeptanzkriterien;
   - exakt den Diff des handoff_commit plus den berührten Umgebungscode;
   - Fehlerpfade, Regressionen, Architektur- und Code-Standards;
   - den DRY-Prüfguard dieses Dokuments: Suche jede neue oder geänderte
     Fachregel projektweit auf identische oder fast identische Logik und
     parallele Sources of Truth; dokumentiere DRY-Scope und Ergebnis im
     Review, auch wenn kein DRY-Finding vorliegt;
   - Aussagekraft der Tests. Mocke nur externe Grenzen und lasse eigenen Code
     real durchlaufen;
   - die relevanten Tests und, risikogerecht, die vollständige Testsuite.
   Alle versionierten `./_tickets/T-*.sh`-Prüfskripte sind von Mike dauerhaft
   zur Ausführung freigegeben; führe das zum Ticket gehörende Skript ohne
   erneute fachliche Rückfrage aus, nachdem du es auf sichere Ziel- und
   Cleanup-Grenzen geprüft hast.
   - bei einer reinen Entwurfsübergabe nach ungefähr drei aufeinanderfolgenden
     inhaltlich erfolglosen Reviews desselben Scope die Konvergenzprüfung
     dieses Dokuments. Drei Runden sind ein Richtwert, keine harte Grenze.
     Erlaube eine weitere punktuelle Runde, wenn Rest und Abschlussweg konkret
     und voraussichtlich abschließend sind; verlange sonst Rebaseline oder
     Scope-Verkleinerung. Wiederhole diese Bewertung nach jeder weiteren
     erfolglosen Entwurfsrunde.
   Verlasse dich nicht auf Claudes Zusammenfassung oder grüne Tests allein.
6. Verändere niemals Produktcode, die Human-Spalte, bestehende
   Nutzeränderungen oder den Git-Verlauf. Kein reset, checkout --, amend,
   merge, push oder Verschieben nach solved/.
7. Schreibe das Ergebnis unter INBOX → Claude, Findings zuerst und nach
   Schweregrad sortiert, jeweils mit Datei/Zeile, Wirkung und überprüfbarer
   Erwartung. Ergänze ein wiederkehrendes Claude-Fehlermuster ausschließlich
   dann in _tickets/CLAUDE-REVIEW-PATTERNS.md, wenn mindestens zwei konkrete
   Belege oder eine ausdrücklich falsche Vollständigkeitsbehauptung vorliegen.
   Ergänze bei einem bekannten Muster den neuen Beleg am bestehenden Eintrag;
   so wächst eine auswertbare Datensammlung für den späteren Skill.
   Entferne die verarbeitete Nachricht aus OUTBOX → Codex.
8. Bei mindestens einem sachlichen Finding: phase changes_requested,
   owner claude. Ohne Finding: phase approved, owner claude — Claude schliesst
   das Ticket ab und beginnt das naechste. Mikes Abnahme laeuft gesammelt
   ueber T-28, nicht je Ticket; owner mike bleibt allein fuer blocked.
   Aktualisiere
   updated_at und übernimm das bearbeitete Tupel in die drei
   last_reviewed_*-Felder. review_round bleibt unverändert; Claude erhöht sie
   erst mit einer neuen Übergabe.
9. Melde Mike nur ein neues Review-Ergebnis, einen Blocker oder eine nötige
   Entscheidung. Gib getestete Befehle und Ergebnis knapp an.
```

Aktiver Takt: alle 5 Minuten während der laufenden Entwicklungsphase. Der
lokale Rechner und die Codex-Desktop-App müssen dafür laufen. Ein engerer Takt
bringt wenig, weil der Zustandsfilter Leerdurchläufe ohnehin sofort beendet.

## Prompt für den periodischen Claude-Loop

Das Gegenstück zum Codex-Task: Claude fragt im selben Takt, ob eine Antwort
aus dem Review auf ihn wartet. Als `/loop` **im laufenden Arbeits-Chat**
starten, damit derselbe Branch und dasselbe `STATUS.md` gesehen werden. Beim
Ausstieg wird der Loop gelöscht; dieser Abschnitt hält ihn wiederherstellbar.

```text
/loop 5m Du bist Claude, der Implementierer im StockInfo-Board. Beachte CLAUDE.md und die Skills task-verification-workflow, code-standards, git-conventions.

1. Lies _tickets/STATUS.md, _tickets/CODEX-REVIEW-AUTOMATION.md und _tickets/CLAUDE-REVIEW-PATTERNS.md. Der maschinenlesbare Zustand oben in STATUS.md ist massgeblich, nicht dein Gedaechtnis.
2. Ist `owner` nicht `claude`: veraendere keine Datei, antworte in einer Zeile mit Phase und Owner, Schluss.
3. Bei `phase: changes_requested`: Arbeite die Findings aus INBOX -> Claude der Reihe nach ab, schwerste zuerst. Jedes Finding einzeln verifizieren statt der Zusammenfassung glauben; behauptete Vollstaendigkeit mit rg belegen. Bei wiederholter Entwurfsnacharbeit gilt die Konvergenzpruefung dieses Dokuments: ungefaehr drei erfolglose Runden sind ein Richtwert, keine harte Grenze. Ist eine weitere punktuelle Runde konkret und voraussichtlich abschliessend, begruende das mit dem vollstaendigen Restumfang in der OUTBOX. Verlangt das Review Rebaseline oder Scope-Verkleinerung, korrigiere nicht weiter lokal, sondern konsolidiere beziehungsweise schneide neu. Vor dem ersten Edit auf einem Feature-Branch `t-NN-<slug>` sein. Danach relevante Pytests, das Ticket-Smoke-Script `./_tickets/T-*.sh --run` und `make test` laufen lassen und die Ergebnisse mit Zahlen nennen. Dann genau EIN Uebergabe-Commit, INBOX leeren, Ergebnis nach OUTBOX -> Codex, `review_round` +1, `phase: ready_for_codex`, `owner: codex`, `updated_at` auf heute. Danach keinen Produktcode mehr anfassen.
4. Bei `phase: approved`: Ticket NICHT nach solved/ verschieben, das macht Mike. Naechsten Teil des Tickets beginnen, eigener Branch vor dem ersten Edit, `phase: claude_working`.
5. Bei `phase: claude_working`: die begonnene Arbeit fortsetzen, sonst wie Punkt 3 uebergeben.
6. Bei `phase: blocked` oder wenn eine Entscheidung von Mike noetig ist: nichts weiterschreiben, in einer Zeile melden, `owner: mike` lassen und den Loop stoppen.
7. Melde nur Uebergabe, Blocker oder Entscheidungsbedarf. Leerdurchlaeufe bleiben einzeilig.
```

Beide Loops teilen sich denselben Zustandsfilter: Genau einer von beiden ist
über `owner` je Runde am Zug, der andere beendet seinen Lauf einzeilig. Läuft
nur ein Agent, bleibt der andere Takt wirkungslos, aber ungefährlich.
