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

`ready_for_codex` ist **keine Zwischenfrage**. Ist der Sachverhalt im aktiven
Ticket bereits entschieden, leitet Claude die Implementierung daraus ab und
bleibt bei `claude_working`, `owner: claude`. Fehlt tatsächlich eine
Produktentscheidung, gilt `blocked`, `owner: mike`. Ein unfertiger
Produktzwischenstand wird weder durch einen vorläufigen Commit noch durch eine
Frage an Codex zu einer Review-Übergabe; `handoff_commit` und `review_round`
bleiben bis zur vollständigen Übergabe auf dem zuletzt abgeschlossenen Stand.

Codex prüft nur `ready_for_codex`. Nach den Vorbedingungen setzt Codex
`codex_reviewing`. Codex verändert im Review grundsätzlich keinen Produktcode;
die eng begrenzte Selbstheilung unten ist die einzige Ausnahme. Die
Human-Spalte bleibt immer unverändert, und Codex verschiebt kein Ticket nach
`solved/`. Das Ergebnis kommt in `INBOX → Claude`; die verarbeitete
OUTBOX-Nachricht wird entfernt. Danach ist die Phase `approved` oder
`changes_requested`, **beide mit `owner: claude`**. Bei einem echten, nicht
sicher lösbaren Hindernis gilt `blocked` mit `owner: mike`.

## Codex-Selbstheilung — mechanische Kleinigkeiten ohne Zusatzrunde

*(Entscheidung Mike, 2026-08-29.)*

Codex darf einen beim Review gefundenen Rest in derselben Runde selbst
korrigieren, wenn **alle** folgenden Bedingungen erfüllt sind:

- Die Korrektur ist rein mechanisch, eindeutig und verhaltensneutral, zum
  Beispiel eine vollständige Bezeichner-Umbenennung, Formatierung oder eine
  Korrektur in Kommentar, Docstring oder technischer Prosa.
- Die Änderung lässt sich als abschließende, deterministische Ersetzung
  angeben. Sie eröffnet keinen neuen Scope und braucht keine fachliche oder
  gestalterische Entscheidung.
- Unverändert bleiben insbesondere Fachlogik, API und Plugin-Vertrag,
  Datenmodell und Migration, Konfiguration, Abhängigkeiten, Security,
  UI-Verhalten, i18n-Texte sowie Fixtures, Assertions und Erwartungswerte von
  Tests.
- Der Worktree enthält keinen parallelen Produktedit von Claude oder Mike.
  Bei fremden oder unklaren Änderungen gilt die Ausnahme nicht.

Die Selbstheilung erhält genau einen eigenen Produkt-Commit mit Präfix
`fix(review):` oder `style(review):`. Codex prüft dessen vollständigen Diff
noch einmal mit dem zur Sprache passenden Inventar, führt mindestens die
direkt betroffenen Tests und statischen Checks aus und wiederholt jeden durch
den Fix berührten Smoke. Danach setzt Codex `handoff_commit` auf diesen
finalen Produkt-Commit, behält `review_round` bei und dokumentiert im Ticket
sowohl den ursprünglich übergebenen als auch den selbst geheilten Stand.
Besteht die Gegenprüfung, darf dieselbe Runde unmittelbar `approved` werden;
andernfalls geht sie mit dem vollständigen Rest als `changes_requested` an
Claude. Diese Ausnahme ist kein Weg, einen strittigen Reviewbefund selbst zur
richtigen Lösung zu erklären.

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
worden, dass keine menschliche Abnahme nach jedem Einzelticket läuft. Damit
stand hinter `owner: mike` keine Arbeit mehr; die Reihe blieb nach jeder
Freigabe stehen, bis Mike sie von Hand weiterschob. Bei `blocked` bleibt er
Eigentümer — dort braucht es ihn wirklich. Das spätere Sammel-Ticket T-28
wurde am 2026-08-29 als veraltet verworfen; an der Owner-Regel ändert das
nichts.

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

**Der Commit aus Schritt 4 kann scheitern — und dann ist der Riegel offen.**
*(Ergänzt 2026-08-27, nach T-22 Runde 2.)* In dieser Übergabe wies eine
Sicherheitsregel des Repos das Kommando ab, weil die **Commit-Message** die
Geheimnisdatei beim Namen nannte; der Riegel stand dadurch rund eine Minute
ohne Commit, und Codex hat in genau diesem Fenster geclaimt. Der Fall ist
allgemeiner als sein Anlass: Jeder Hook, jeder Pre-Commit-Lauf und jeder
Formatprüfer kann Schritt 4 abweisen, nachdem Schritt 3 bereits auf der Platte
steht.

Deshalb: Scheitert der Commit, ist der Ready-Zustand **kein Zustand zum
Warten**. Entweder er wird sofort auf anderem Weg committet — die Ursache liegt
fast immer in der Message, nicht im Inhalt —, oder Schritt 3 wird
zurückgenommen, bis der Commit steht. Still im Ready zu verharren überlässt die
Übergabe dem Zufall, ob der Prüfer gerade nachsieht.

### Der Wechsel zum nächsten Kettenglied kommt **vor** dem ersten Produktedit

*(Ergänzt 2026-08-27, nach T-27a Runde 1.)* Nach einer Freigabe zieht Claude
zum nächsten Ticket der `priority_chain` weiter. Dabei entstand ein Fenster, in
dem Branch und Produktänderungen für T-27a schon sichtbar waren, während
`STATUS.md` noch `approved` und T-22 meldete.

Ein Race gab es nicht — der Owner blieb Claude. Trotzdem ist der Zustand
schädlich: **Wer nur die Datei liest, sieht ein abgeschlossenes Ticket und
gleichzeitig fremde Änderungen an einem anderen.** Das ist von einem
Kommunikationsabbruch nicht zu unterscheiden, und die Datei ist genau dafür da,
diesen Unterschied zu machen.

Deshalb ist der Wechsel ein eigener, **atomarer** Schritt vor dem ersten
Produktedit: `ticket`, `priority_ticket`, `review_round: 0` und
`phase: claude_working` in einem Commit. Erst danach der Branch, erst danach
die erste Zeile Code.

`review_round: 0` heißt wörtlich „noch keine Runde geprüft". Die `1` entsteht
beim Hochzählen der ersten Übergabe, nicht beim Arbeitsbeginn — sonst gäbe es
zwei verschiedene Runden mit derselben Nummer, und der Schlüssel
`(ticket, handoff_commit, review_round)` verlöre seine Eindeutigkeit genau
dort, wo die Duplikatsperre auf ihn baut. *(Der Loop-Prompt unten sagte hier
bis 2026-08-28 fälschlich `1`; Befund aus T-27a Runde 2.)*

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

## Testinfrastruktur-Riegel — schlank und online ist der Standard

*(Produktentscheidung Mike, 2026-08-28, nach dem verworfenen T-27b-
Offline-Subsystem.)*

Ohne eine ausdrückliche Ausnahme gilt für jedes Ticket:

- **Unit-Tests** benutzen die normalen Mittel des vorhandenen Testframeworks
  und die von Sprache oder Bibliothek angebotenen Fakes, Mocks und
  Transport-Hooks. Kleine testlokale Fixtures und Helper sind erlaubt.
- **Integrationstests** laufen gegen den echten Online-Dienst und benutzen die
  bereits vorhandene Anbieterbibliothek beziehungsweise den vorhandenen
  Produktclient. Ein Marker zum gezielten Auswählen oder Abwählen ist erlaubt;
  er macht aus dem Integrationstest keinen Offline-Test.
- Ein Plugin oder Adapter benutzt die vorhandene API-Anbindung. Es schreibt
  HTTP-Aufruf, Anfrageformat, Antwortauswertung oder Fehlersemantik nicht für
  den Testweg ein zweites Mal.

Folgendes gilt als **eigenes Test-Subsystem** und ist standardmäßig nicht im
Scope: Record/Replay und Cassettes, persistierte Datenverkehrsmitschnitte,
eigene Transport- oder Proxy-Schichten, globale Socket-Sperren, neue
Bereinigungs-, Signatur- oder Serialisierungsformate, Freshness- und
Veröffentlichungstore, eigene Test-CLIs sowie Testframework-Plugins oder
Entry-Points. Die Liste ist eine Erkennungshilfe, keine Einladung, dieselbe
Architektur unter einem anderen Namen zu bauen.

Eine Ausnahme ist nur gültig, wenn das aktive Ticket **vor dem ersten Entwurf
und vor dem ersten Produktedit** diesen Block enthält:

```markdown
> **Ausnahme Testinfrastruktur — ausdrücklich freigegeben von Mike, YYYY-MM-DD:**
> <konkret begrenzter Umfang und Grund>
```

Eine allgemeine Forderung nach Robustheit, CI-Tauglichkeit, Reproduzierbarkeit
oder „Integrationstests“ ist keine solche Freigabe. Claude und Codex dürfen sie
nicht aus vermuteten Bedürfnissen ableiten.

**Riegel beim Implementierer:** Reicht der schlanke Standard aus, wird er ohne
Rückfrage verwendet. Hält Claude ein Test-Subsystem dennoch für notwendig,
stoppt er vor Entwurf und Code mit `phase: blocked`, `owner: mike`, nennt die
minimale Standardlösung, den konkreten Mehrwert und den begrenzten Umfang der
gewünschten Ausnahme. Bis zur ausdrücklichen Entscheidung entsteht dafür kein
Code und kein Detailentwurf.

**Riegel beim Reviewer:** Codex inventarisiert in jedem Handoff neue
Test-Helfer, persistierte Testdaten, Plugins, Entry-Points, CLIs und
Transportpfade. Findet er ein Test-Subsystem ohne den Freigabeblock, ist das
unabhängig von grünen Tests ein `changes_requested`: entfernen und auf den
schlanken Standard zurückführen. Nur wenn der Standard nachweislich unmöglich
ist und dafür eine Produktentscheidung fehlt, wird an Mike blockiert.

## Vertical-Acceptance-Riegel — erst der Nutzerweg, dann die Fläche

*(Produktentscheidung Mike, 2026-08-29, nach T-31 Runde 4.)*

Der Riegel gilt, sobald ein Ticket eine neue oder geänderte Fachregel durch
mehr als eine Produktschicht trägt — etwa Eingang, Service, Persistenz und UI.
Er ergänzt TDD und die Verify-Matrix; er baut kein eigenes Test-Subsystem.

### Vor dem ersten Produktedit

1. Das Ticket nennt die **kleinste Zahl entscheidender Akzeptanzfälle** am
   öffentlichen Eintrittspunkt. Jeder Fall beschreibt Eingabe, beobachtbares
   Ergebnis und den fachlich falschen Gegenfall. Ein Test, der ein bereits
   fertig gebautes Domainobjekt hinter der zu prüfenden Erkennung einspeist,
   gilt nicht als Beleg für den Eintrittsweg.
2. Für jeden neuen Unterschied läuft mindestens ein Akzeptanztest zuerst
   **rot**. Die OUTBOX nennt den Test und den beobachteten roten Grund. Der
   Test darf klein und mit normalen Fakes gebaut sein; entscheidend ist, dass
   er die echte Produktkette bis zur behaupteten Grenze aufruft.
3. Danach entsteht zuerst **ein dünner vertikaler Pfad** vom öffentlichen
   Eingang bis zum Ergebnis. Horizontale Verbreiterung auf weitere Rollen,
   Adapter, Artefakte oder UI-Varianten beginnt erst, wenn dieser Pfad grün ist.

### Während der Umsetzung

4. Ändert das Ticket Schema, Konfiguration, Installation, Loader oder
   Startzustand, gehört ein Lauf auf **frischem Zustand** zum Pflicht-Gate:
   leere Datenbank beziehungsweise neues Volume, normaler Produktstart und
   mindestens eine echte Operation mit der neuen Form. Isoliertes SQL oder
   ein direkt konstruierter Repository-Wert genügt nicht.
5. Jede neue Schranke oder Invariante bekommt einen **negativen Mutanten**:
   eine minimal falsche Implementierung oder Quelle, die ausschließlich die
   neue Regel verletzt. Der benannte Test muss daran rot werden. Das ist ein
   normaler Testfall, kein Mutationstest-Framework.
6. Berührt der geplante Diff mehr als drei Produktschichten oder ungefähr
   25–30 Produktdateien, ist das ein **Breitenalarm**, keine starre Grenze.
   Claude stoppt vor weiterer Flächenarbeit und hält fest, welcher dünne Pfad
   bereits grün ist. Fehlt er, wird der Rest neu geschnitten; Dateizahl oder
   grüne Gesamttestzahl ersetzen diese Begründung nicht.

### Vor der Übergabe

7. Die OUTBOX ordnet jede offene Verify-Zeile einem konkreten Orakel zu:
   `Matrix # → Test/Browser-Szenario → Ergebnis`. Eine Gesamtsumme wie „800
   Tests grün" ist nur Zusatzinformation. Fehlt der konkrete Beleg, bleibt die
   AI-Zelle `⚠️`, `◑` oder `➖`.
8. Kommentare, Docstrings, Typen und Snapshots sind Mitzieher, kein
   Verhaltensbeleg. Eine Behauptung „gebaut" braucht zuerst den ausführbaren
   Pfad und sein Orakel.

**Riegel beim Reviewer:** Codex sucht die entscheidenden Akzeptanzfälle zuerst
und prüft mit einem kleinen Gegenlauf oder Mutanten, ob sie den alten/falschen
Zustand wirklich unterscheiden. Fehlen öffentlicher Eintritt, Frischstart,
negativer Mutant oder Matrix-Zuordnung, ist das unabhängig von grünen
Gesamtsuiten `changes_requested`.

Wird dieser Riegel während einer bereits laufenden Runde eingeführt, muss
Claude keinen Produktstand künstlich zurückdrehen. Vor der nächsten Übergabe
müssen die entscheidenden Tests jedoch nachweislich am alten beziehungsweise
minimal falschen Pfad rot und am neuen Pfad grün gewesen sein.

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

1. Lies _tickets/STATUS.md, _tickets/CODEX-REVIEW-AUTOMATION.md und _tickets/CLAUDE-REVIEW-PATTERNS.md. Der maschinenlesbare Zustand oben in STATUS.md ist massgeblich, nicht dein Gedaechtnis. Pruefe vor jeder Arbeit: ticket muss exakt priority_ticket entsprechen und in priority_chain stehen. Bei Abweichung nichts implementieren, portfolio_mismatch melden und Schluss. Pruefe vor jedem Entwurf und vor dem ersten Produktedit ausserdem den Testinfrastruktur-Riegel und den Vertical-Acceptance-Riegel. Standard sind normale Unit-Tests plus echte Online-Integrationstests ueber vorhandene Sprach-, Bibliotheks- und Produkt-APIs. Record/Replay, Cassettes oder Mitschnitte, eigene Transport-/Socket-/Freshness-/CLI-/Testplugin-Infrastruktur sind ohne den datierten Ausnahmeblock von Mike im aktiven Ticket verboten. Ist eine Ausnahme wirklich noetig, vor Entwurf und Code mit phase: blocked und owner: mike stoppen; sie niemals aus Robustheit, CI oder Reproduzierbarkeit ableiten. Bei einem mehrschichtigen Fachumbau zuerst die entscheidenden oeffentlichen Akzeptanzfaelle rot belegen, danach einen duennen vertikalen Pfad gruen bauen; Frischstart, negativer Mutant und Matrix-zu-Orakel-Zuordnung sind vor der Uebergabe Pflicht.
2. Ist `owner` nicht `claude`: veraendere keine Datei, antworte in einer Zeile mit Phase und Owner, Schluss.
3. Bei `phase: changes_requested`: Arbeite die Findings aus INBOX -> Claude der Reihe nach ab, schwerste zuerst. Jedes Finding einzeln verifizieren statt der Zusammenfassung glauben; behauptete Vollstaendigkeit mit rg belegen. Bei wiederholter Entwurfsnacharbeit gilt die Konvergenzpruefung dieses Dokuments: ungefaehr drei erfolglose Runden sind ein Richtwert, keine harte Grenze. Ist eine weitere punktuelle Runde konkret und voraussichtlich abschliessend, begruende das mit dem vollstaendigen Restumfang in der OUTBOX. Verlangt das Review Rebaseline oder Scope-Verkleinerung, korrigiere nicht weiter lokal, sondern konsolidiere beziehungsweise schneide neu. Vor dem ersten Edit auf einem Feature-Branch `t-NN-<slug>` sein. Danach relevante Pytests, das Ticket-Smoke-Script `./_tickets/T-*.sh --run` und `make test` laufen lassen und die Ergebnisse mit Zahlen nennen. Dann genau EIN Uebergabe-Commit, INBOX leeren, Ergebnis nach OUTBOX -> Codex, `review_round` +1, `phase: ready_for_codex`, `owner: codex`, `updated_at` auf heute. Danach keinen Produktcode mehr anfassen.
4. Bei `phase: approved`: Ticket NICHT nach solved/ verschieben, das macht Mike. Nur zum naechsten Element aus priority_chain wechseln, priority_ticket und ticket gemeinsam setzen, review_round fuer das neue Ticket auf 0 setzen — die 1 entsteht erst beim Hochzaehlen in Schritt 3, wenn die erste Uebergabe tatsaechlich herausgeht —, eigener Branch vor dem ersten Edit, phase: claude_working. War das freigegebene Ticket das letzte Element, nichts Neues beginnen: phase: portfolio_review, owner: mike; Mike braucht die Gate-vs-Follow-up-Einordnung.
5. Bei `phase: claude_working`: die begonnene Arbeit fortsetzen, sonst wie Punkt 3 uebergeben.
6. Bei `phase: blocked`, `phase: portfolio_review` oder wenn eine Entscheidung von Mike noetig ist: nichts weiterschreiben, in einer Zeile melden, `owner: mike` lassen und den Loop stoppen.
7. Melde nur Uebergabe, Blocker oder Entscheidungsbedarf. Leerdurchlaeufe bleiben einzeilig.
```

Beide Loops teilen sich denselben Zustandsfilter: Genau einer von beiden ist
über `owner` je Runde am Zug, der andere beendet seinen Lauf einzeilig. Läuft
nur ein Agent, bleibt der andere Takt wirkungslos, aber ungefährlich.
