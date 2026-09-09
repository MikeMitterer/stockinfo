# Coder-/Verifier-Workflow

Dieses Dokument ist der stabile Vertrag für Implementierung und unabhängigen
Review zwischen den aktuell zugeordneten Agenten. Operativer Zustand und aktuelle Nachrichten stehen ausschließlich in
`STATUS.md`; dieses Dokument enthält keine Laufhistorie.

Die Aktivierung richtet sich nach der Agentenlaufzeit und steht in
[AGENT-ACTIVATION.md](AGENT-ACTIVATION.md). Sie legt keine fachliche Rolle fest.
Die dauerhafte Lernschicht liegt in `CLAUDE-LESSONS.md` für Claude-Arbeit
und `CODEX-LESSONS.md` für Codex-Arbeit. Der Coder liest seine Sammlung
vor einer Übergabe; der Verifier liest vor dem Review die Sammlung des Autors
der geprüften Fassung. Bei gemischter Autorenschaft beide lesen. Dateinamen
bezeichnen die untersuchten Agenten, keine feste Coder-/Verifier-Zuordnung.

Vor fachlicher Arbeit laden **Coder und Verifier** den Skill `code-standards`
nach dem [Standard-Riegel](#standard-riegel--die-hausregeln-stehen-im-bericht-nicht-im-vorsatz).
Das gilt auch bei manuellem Einstieg ohne Scheduler oder Loop.

## Übersicht

- [Rollen und Zustandsprotokoll](#rollen-und-zustandsprotokoll)
- [Ticketpfade und Arbeitsbeginn](#ticketpfade-und-arbeitsbeginn)
- [Scope-Checkpoint — Breite entscheiden, bevor sie zum Review-Diff wird](#scope-checkpoint--breite-entscheiden-bevor-sie-zum-review-diff-wird)
- [Verifier-Selbstheilung — mechanische Kleinigkeiten ohne Zusatzrunde](#verifier-selbstheilung--mechanische-kleinigkeiten-ohne-zusatzrunde)
- [Kleine Befunde im laufenden Browser- oder Verify-Lauf](#kleine-befunde-im-laufenden-browser--oder-verify-lauf)
- [Portfolio-Riegel — das richtige Ergebnis vor lokaler Perfektion](#portfolio-riegel--das-richtige-ergebnis-vor-lokaler-perfektion)
- [Entwurfsrunden — wenn noch kein Produktcode existiert](#entwurfsrunden--wenn-noch-kein-produktcode-existiert)
- [Der Übergabe-Riegel — `<ready_phase>` steht zuletzt](#der-übergabe-riegel--ready_phase-steht-zuletzt)
- [Browsertests nach verfügbarer Ausstattung](#browsertests-nach-verfügbarer-ausstattung)
- [Testinfrastruktur-Riegel — schlank und online ist der Standard](#testinfrastruktur-riegel--schlank-und-online-ist-der-standard)
- [Vertical-Acceptance-Riegel — erst der Nutzerweg, dann die Fläche](#vertical-acceptance-riegel--erst-der-nutzerweg-dann-die-fläche)
- [Standard-Riegel — die Hausregeln stehen im Bericht, nicht im Vorsatz](#standard-riegel--die-hausregeln-stehen-im-bericht-nicht-im-vorsatz)
- [DRY-Prüfguard](#dry-prüfguard)
- [Aktivierung der Agenten](#aktivierung-der-agenten)

## Rollen und Zustandsprotokoll

**Die Zuordnung steht in `STATUS.md`, nicht im Dateinamen.** `implementer`
und `reviewer` sind verschiedene Agenteninstanzen; `owner` bezeichnet den
Akteur, der jetzt am Zug ist. Vor jedem Turn alle drei Felder lesen.
Ein Rollenwechsel erfolgt ausdrücklich und mit geordneter Übergabe.
Der Autor darf seine eigene Fassung nicht als unabhängiger Verifier abnehmen.

**Coder** ist die in `STATUS.md` unter `implementer` eingetragene Instanz.
**Verifier** ist die dort unter `reviewer` eingetragene Instanz.
Die konkrete Zuordnung und die Phasentabelle werden ausschließlich dort gepflegt.

In den Regeln unten bedeuten `<working_phase>`, `<ready_phase>` und
`<reviewing_phase>` die Arbeits-, Übergabe- und Prüfphase aus dieser Tabelle.
`<implementer>` und `<reviewer>` sind die dort eingetragenen Akteurs-IDs.
Diese Platzhalter erläutern den Vertrag; sie werden nie wörtlich in STATUS.md
übernommen. Bei Widersprüchen stoppt die Verarbeitung vor einer Änderung.

Weitere Felder: `ticket`, `handoff_commit`, `review_round`, `updated_at`,
`last_reviewed_ticket`, `last_reviewed_commit`, `last_reviewed_round`,
`workstream`, `priority_chain` und `priority_ticket`. Übergaben müssen das
aktive Prioritätsticket betreffen. Rundenverbrauch und offene Befunde bleiben
bei einem Rollenwechsel erhalten; ein Wechsel startet kein Review von selbst.

Der Coder stellt den Prüfgegenstand fertig, commitet die
Produktänderung und schreibt die vollständige `OUTBOX → <reviewer>`.
Erst zuletzt setzt er die passende Übergabephase, `owner` auf den Verifier,
`handoff_commit` und `review_round`. Danach keine weiteren Produktänderungen.
Eine Zwischenfrage oder unfertige Änderung ist keine Review-Übergabe.

Der Verifier prüft nur bei der zu ihm passenden Übergabephase und Owner-
Zuordnung. Er setzt die Prüfphase, prüft den eingefrorenen Stand und schreibt
sein Ergebnis in `INBOX → <implementer>`. Danach gelten `approved` oder
`changes_requested`, jeweils mit `owner` beim Coder. Die verarbeitete
OUTBOX wird entfernt. Human-Antworten bleiben unverändert; allein ein Review
verschiebt kein Ticket nach `40-done/`. Für Produktänderungen im Review gilt
nur die unten ausdrücklich begrenzte mechanische Selbstheilung.

Ein `scope_checkpoint` geht an den aktuellen Verifier. Bei `continue`,
`reduce` oder `split` geht die Arbeit in der passenden Arbeitsphase an den
Coder zurück. Eine echte menschliche Entscheidung setzt `blocked`
und `owner: mike`. Nach Freigabe des letzten priorisierten Tickets folgt
`portfolio_review`, `owner: mike`; kein automatischer neuer Arbeitsauftrag.

Das Tupel `(ticket, handoff_commit, review_round)` wird nach abgeschlossenem
Review nicht erneut bearbeitet. Die Identität des Prüfers bleibt im Bericht
festgehalten. Ein explizit zusätzlich beauftragter Verifier benötigt eine
eindeutige Auftragszuordnung; bloßes Tauschen der Rollen ist kein neuer Auftrag.

[↑ Übersicht](#übersicht)

## Ticketpfade und Arbeitsbeginn

`ticket`, `priority_ticket`, `priority_chain` und `last_reviewed_ticket`
enthalten Ticket-Dateinamen ohne Ordner. Vor fachlicher Arbeit muss genau
`_tickets/30-doing/<ticket>` existieren; `ticket == priority_ticket`,
Mitgliedschaft in der Kette und passende Rollen/Owner sind zusätzlich Pflicht.
Ein Ticket in Backlog, Done, Iced oder Rejected löst keine Arbeit aus.
Bei widersprüchlicher Ablage oder Priorität einmalig `portfolio_mismatch`
melden und vor der Arbeit stoppen.

Das nächste ausdrücklich eingeplante Kettenglied liegt in `20-ready/`.
Vor seinem ersten Produktedit verschiebt der Coder Ticket und Begleitdateien
nach `30-doing/` und setzt in demselben Commit `ticket`, `priority_ticket`,
Arbeitsphase und `review_round: 0`. Ein vorheriges Ticket bleibt bis zur
Abschlussbestätigung in `30-doing/`, auch wenn das nächste schon begonnen ist.
Nur das ausdrücklich in STATUS benannte Ticket ist aktiv.

Review und Nacharbeit ändern den Ordner nicht. Abschluss und übrige
Ordnerwechsel folgen der [Board-Anleitung](../README.md#von-der-aufnahme-bis-zum-abschluss).
Beim Verschieben aktuelle Verweise mitführen; historische Freigaben und
menschliche Antworten erhalten. Für bereits archivierte StockInfo-Skripte
bei T-68 gilt der dort genannte unveränderte Bestand.

[↑ Übersicht](#übersicht)

## Scope-Checkpoint — Breite entscheiden, bevor sie zum Review-Diff wird

*(Entscheidung Mike, 2026-08-30.)*

Vor dem ersten Produktedit trägt jedes Implementierungsticket einen
`Scope-Vertrag`: ein beobachtbares Ergebnis, höchstens drei fachliche
Änderungen, erwartete Produktflächen/-dateien, erwartete Test- und
Dokumentationsanpassungen, Nicht-Ziele sowie ein Budget für Produktdateien,
Test-/Dokudateien und gesamte Diff-Zeilen.

Coder stoppt **vor weiterer Produktarbeit**, sobald mindestens eines gilt:

- Eine nicht angekündigte Produktschicht wird berührt.
- Ein neuer öffentlicher Typ, Endpunkt, Vertrag, ein Schema, eine Abhängigkeit
  oder eine Abstraktion wird benötigt, ohne im Scope-Vertrag zu stehen.
- Die geschätzte Dateizahl wird um mehr als **25 Prozent** überschritten.
- Der gesamte Ticket-Diff wächst ohne Vorabfreigabe über **800 Zeilen**.
- Produktkommentare oder Test-Docstrings tragen Prozesshistorie statt der
  aktuellen Invariante und ihres fachlichen Grundes. Review-Runden,
  Commit-IDs, Gesprächszitate, Datumsfolgen und Implementierungschroniken
  gehören in Ticket, Spec und Git, nicht in den Code.

Coder friert einen stabilen Commit ein, beschreibt geplanten und tatsächlichen
Umfang samt Auslöser in der OUTBOX und setzt `phase: scope_checkpoint`,
`owner: <reviewer>` sowie `handoff_commit` auf diesen Stand. Das ist **kein
Code-Review**: Verifier prüft nur Ticketziel, Diff-Statistik und neu berührte
Flächen und erfindet keine zusätzlichen Qualitätsanforderungen.

Verifier antwortet mit genau einer Entscheidung:

- `continue`: rein mechanische Ausbreitung innerhalb des vereinbarten
  Ergebnisses;
- `reduce`: unnötige Änderungen entfernen;
- `split`: ein unabhängig lieferbares Ergebnis wird ein eigenes Ticket;
- `mike`: eine neue Produktentscheidung ist erforderlich.

Bei `continue`, `reduce` oder `split` setzt Verifier `phase: <working_phase>` und
`owner: <implementer>`; bei `mike` gilt `blocked`, `owner: mike`. Verifier darf das
Budget eines Tickets einmal erweitern. Eine zweite Überschreitung führt
standardmäßig zu `reduce` oder `split`; nur eine eindeutig mechanische
Restanpassung darf nochmals weiterlaufen.

Die normale OUTBOX-Übergabe nennt anschließend geplant/tatsächlich für
fachliche Änderungen, Produktdateien, Test-/Dokudateien und Diff-Zeilen. Jede
Abweichung erhält einen Satz Begründung; eine grüne Gesamtsuite ersetzt diese
Umfangskontrolle nicht. T-38 wird nicht rückwirkend unterbrochen, der Riegel
gilt ab T-37.

<a id="codex-selbstheilung--mechanische-kleinigkeiten-ohne-zusatzrunde"></a>

[↑ Übersicht](#übersicht)

## Verifier-Selbstheilung — mechanische Kleinigkeiten ohne Zusatzrunde

*(Entscheidung Mike, 2026-08-29.)*

Verifier darf einen beim Review gefundenen Rest in derselben Runde selbst
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
- Der Worktree enthält keinen parallelen Produktedit von Coder oder Mike.
  Bei fremden oder unklaren Änderungen gilt die Ausnahme nicht.

Die Selbstheilung erhält genau einen eigenen Produkt-Commit mit Präfix
`fix(review):` oder `style(review):`. Verifier prüft dessen vollständigen Diff
noch einmal mit dem zur Sprache passenden Inventar, führt mindestens die
direkt betroffenen Tests und statischen Checks aus und wiederholt jeden durch
den Fix berührten Smoke. Danach setzt Verifier `handoff_commit` auf diesen
finalen Produkt-Commit, behält `review_round` bei und dokumentiert im Ticket
sowohl den ursprünglich übergebenen als auch den selbst geheilten Stand.
Besteht die Gegenprüfung, darf dieselbe Runde unmittelbar `approved` werden;
andernfalls geht sie mit dem vollständigen Rest als `changes_requested` an
Coder. Diese Ausnahme ist kein Weg, einen strittigen Reviewbefund selbst zur
richtigen Lösung zu erklären.

### Der bereits benannte Rest wird nicht zur nächsten Runde

*(Entscheidung Mike, 2026-09-09. Gilt für den Verifier, gleich ob Claude oder
Codex — die Rolle steht in `STATUS.md`, nicht im Dateinamen.)*

Ist eine Kleinigkeit dieser Art **schon beschrieben** — in einem Befund, einer
Antwort an Mike oder einer eigenen Restliste —, dann erledigt der Verifier sie
selbst, statt dafür eine Runde zu eröffnen. Wer die Fundstellen bereits
aufzählen kann, hat die Arbeit ohnehin getan; sie danach durch die Übergabe zu
schicken, kostet einen vollen Zyklus für ein Ergebnis, das schon feststeht.

Zwei Bedingungen der Liste oben werden dafür gelockert:

- Der Rest darf aus einer **früheren** Runde stammen. Er muss nicht in der
  laufenden Prüfung entdeckt worden sein.
- **Fremde Änderungen im Arbeitsbaum blockieren nicht mehr allein.** Maßgeblich
  ist, dass die geheilten Dateien selbst unberührt sind: kein paralleler Edit
  an ihnen, und der eigene Commit nimmt nur sie mit. Fremde Dateien bleiben
  uncommitted liegen.

Unverändert gelten: rein mechanisch und verhaltensneutral, kein neuer Scope,
keine fachliche Entscheidung, eigener `fix(review):`- oder
`style(review):`-Commit, Inventar und Tests danach selbst gelaufen. Der Bericht
nennt die Zahl der geänderten Fundstellen und was **nicht** mitgezogen wurde.

Die Abgrenzung bleibt der belegte Schaden nach
[R-02](CODEX-LESSONS.md#r-02--entwicklungsstand-wird-wie-ein-breit-ausgerolltes-produkt-behandelt):
Was eine fachliche Entscheidung braucht, geht weiterhin als
`changes_requested` zurück. Nur der bereits verstandene, mechanische Rest wird
hier erledigt.

[↑ Übersicht](#übersicht)

## Kleine Befunde im laufenden Browser- oder Verify-Lauf

*(Entscheidung Mike, 2026-09-02, nach T-56 Punkt 5.)*

Nicht jeder kleine Befund braucht ein eigenes Bauticket. Coder darf ihn im
aktiven Abnahme- oder Verify-Ticket korrigieren und den betroffenen Handgriff
unmittelbar wiederholen, wenn **alle** folgenden Grenzen eingehalten sind:

- Das gewünschte Verhalten folgt bereits aus der vorhandenen Verify-Zeile
  oder einer bestehenden Produktregel; es braucht keine neue Entscheidung.
- Ursache und Korrektur sind vor dem Edit eindeutig benannt.
- Höchstens drei Produktdateien und eine Testdatei werden berührt; der Diff
  bleibt innerhalb von 100 neuen oder geänderten Zeilen.
- Öffentlicher Vertrag, API, Schema, Datenmodell, Migration, Konfiguration,
  Abhängigkeiten und Security bleiben unverändert; es entsteht keine neue
  Abstraktion oder Produktschicht.
- Die direkt betroffenen automatisierten Tests und der betroffene Browser-
  oder Verify-Handgriff werden nach der Korrektur erneut ausgeführt und mit
  ihrem tatsächlichen Ergebnis dokumentiert.

Coder bleibt dabei `<working_phase>`; es gibt **keine** Verifier-Zwischenfreigabe
zwischen Korrektur und Wiederholung. Die gemeinsame Übergabe enthält Befund,
Produkt-Diff und Wiederholungsbeleg. Erst dort prüft Verifier den finalen Stand.
Überschreitet der Befund eine dieser Grenzen, greift der normale
Scope-Checkpoint oder ein eigenes Ticket.

[↑ Übersicht](#übersicht)

## Portfolio-Riegel — das richtige Ergebnis vor lokaler Perfektion

*(Ergänzt 2026-08-27 nach 52 T-21-Runden ohne lauffähigen Plugin-Host.)*

Ein korrektes Review-Tupel genügt nicht, wenn das falsche Ticket bearbeitet
wird. `priority_chain` ist deshalb eine Produktentscheidung, keine
unverbindliche Empfehlung:

- `ticket` muss bei Arbeit und Übergabe exakt `priority_ticket` entsprechen.
- Die [Ticketpfade](#ticketpfade-und-arbeitsbeginn) müssen zum aktiven Auftrag
  passen. Bei veralteter Ablage oder Priorität `portfolio_mismatch` melden
  und stoppen.
- Ein Review-Finding erzeugt keine neue Priorität. Folgearbeiten kommen ins
  Board und werden erst durch eine ausdrückliche Portfolio-Entscheidung in die
  Kette aufgenommen.
- Nach einer Freigabe wird nur auf das **nächste Element derselben Kette**
  weitergeschaltet. Es gibt kein automatisches „nächstes Teilstück“ und keine
  Sortierung nach Ticketnummer.
- Nach dem letzten Element wechselt der Zustand auf `portfolio_review` mit
  `owner: mike`. Erst die Einordnung der übrigen Tickets in Gate oder Follow-up
  setzt eine neue Kette.
- Der Scheduler lehnt ein `<ready_phase>` außerhalb der Priorität mit
  `portfolio_mismatch` ab. Verifier reviewt diesen Handoff nicht.

Aktuell lautet die von Mike bestätigte MVP-Kette **T-22 → T-27a → T-27b →
T-23**. Ihr Ziel ist nicht mehr Vorarbeit, sondern ein belegter Lauf
**Registry → Core → REST** über beide Ladewege.

**Warum eine Freigabe nicht bei Mike landet** *(Entscheidung Mike,
2026-08-22)*: Als dieser Vertrag entstand, hieß `approved` sinngemäß „Verifier ist durch,
jetzt kommt Mikes Abnahme" — pro Ticket. Wenige Stunden später ist entschieden
worden, dass keine menschliche Abnahme nach jedem Einzelticket läuft. Damit
stand hinter `owner: mike` keine Arbeit mehr; die Reihe blieb nach jeder
Freigabe stehen, bis Mike sie von Hand weiterschob. Bei `blocked` bleibt er
Eigentümer — dort braucht es ihn wirklich. Das spätere Sammel-Ticket T-28
wurde am 2026-08-29 als veraltet verworfen; an der Owner-Regel ändert das
nichts.

[↑ Übersicht](#übersicht)

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

### Rundenlimit: Rest offenlegen und abschließen

**Vorgabe Mike, 2026-09-09; gilt für Coder und Verifier bei Code- und
Konzeptreviews.** `max_review_rounds` in `STATUS.md` begrenzt die regulären
vollständigen Reviewrunden je Ticket. Es ist keine Mindestanzahl, keine
Abbruchautomatik und kein Freigabegrund. `last_reviewed_round` bezeichnet
weiterhin die tatsächlich zuletzt abgeschlossene Runde.

**Beim Erreichen des Limits steht im Ticket deutlich, was noch offen ist
und warum das Limit erreicht wurde.** Der Verifier aktualisiert dazu die
bestehende Verify-Matrix und nennt im aktuellen Restabschnitt:

- jeden offenen Befund mit Fundstelle, konkreter Auswirkung und Einordnung
  als Blocker oder nicht blockierende Kleinigkeit;
- den Grund, weshalb er noch offen ist und die bisherigen Runden ihn nicht
  erledigt haben; auch eigene ausgelassene Korrekturen werden benannt;
- den nächsten konkreten Handgriff, den zuständigen Bearbeiter und den
  erforderlichen Nachweis für den Abschluss.

Ist nichts mehr offen, steht das ausdrücklich dort, zusammen mit dem Grund
für den Rundenverbrauch. Keine zweite Statusmatrix und kein pauschales
„Limit erreicht“ anstelle des Befunds.

**Eindeutige, verhaltensneutrale Kleinigkeiten erledigt der Verifier über die
Selbstheilung oben, auch am Limit.** Dazu gehören passende Kommentar- und
Docstring-Korrekturen. Das Limit rechtfertigt weder ihr Liegenlassen noch eine
zusätzliche vollständige Runde. Ein solcher Textrest ist ohne belegten
fachlichen Schaden kein Blocker. Ist Selbstheilung im konkreten Fall nicht
zulässig, bleibt der Rest mit Grund und Zuständigkeit sichtbar; er wird nicht
als erledigt ausgegeben.

**Echte Blocker bleiben beim aktuellen Ticket.** Der Coder behebt sie, der
Verifier prüft gezielt die Korrektur und ihre betroffenen Folgen. Das läuft
über die bestehenden Arbeits- und Übergabephasen weiter, ohne automatische
Übergabe an Mike. Es beginnt keine neue breite Suche nach Nebenbefunden.
Eine erforderliche Nachprüfung jenseits des regulären Limits wird im Ticket
als begründete Überschreitung mit Umfang und Ergebnis ausgewiesen; die
Rundennummer zählt ehrlich weiter. Weder Zähler zurücksetzen noch durch ein
neues Ticket denselben Blocker aus dem Limit herauslösen.

Solange ein Blocker offen ist, gibt es kein `approved`, keinen Anschluss an
das nächste Ticket und kein Verschieben nach `40-done/`. Nicht blockierende
Restpunkte verhindern eine begründete Freigabe nicht; sie bleiben ausdrücklich
sichtbar. Die sonstigen Regeln für den Ticketabschluss gelten unverändert.
`owner: mike` und ein gestoppter Ablauf sind nur nötig, wenn tatsächlich seine
Entscheidung oder eine von den Agenten nicht auflösbare Voraussetzung fehlt.
Das Erreichen der Zahl allein ist kein solcher Grund.

### Konvergenzprüfung bei wiederholt erfolglosen Entwurfsrunden

Die Regel zum Rundenlimit oben gilt auch für Entwürfe. Die folgende
Konvergenzprüfung ergänzt sie; sie erlaubt keine undokumentierte
Überschreitung. Mehrere Entwurfsrunden sind kein Qualitätsmerkmal und ihre
Anzahl allein ist auch kein Abbruchgrund. Als **grober Richtwert** lösen ungefähr drei
aufeinanderfolgende inhaltlich erfolglose Reviews desselben Entwurfsscope eine
ausdrückliche Konvergenzprüfung aus. Ein formaler Handoff-Blocker zählt dabei
nicht als inhaltlich erfolglose Runde.

Der Verifier beantwortet dann im Review knapp:

1. Sind die Grundentscheidungen stabil und alle betroffenen Schichten
   inventarisiert?
2. Ist der verbleibende Rest konkret, klein und abschließend benennbar?
3. Fehlt weder eine Produktentscheidung noch ein weiterer unabhängiger Scope?
4. Warum ist eine weitere Korrekturrunde voraussichtlich die letzte — oder
   warum wäre diese Annahme nicht belastbar?

Sind Rest und Abschlussweg konkret, kann eine gezielte Nachprüfung nötig
sein. Bei gesetztem `max_review_rounds` gilt dafür die dokumentierte
Überschreitung nach der Regel oben; der Konvergenz-Richtwert ersetzt das
Rundenlimit nicht. Je länger die Schleife
läuft, desto konkreter muss jedoch die Begründung für eine weitere punktuelle
Korrektur sein. Ist keine belastbare Konvergenz absehbar, endet die
Patch-Schleife: Coder erstellt eine konsolidierte Neufassung oder verkleinert
den Scope auf ein beobachtbares Ergebnis. Eine neue Grundentscheidung löst
dieselbe Neubewertung sofort aus; abhängige alte Aussagen, Tests und
Verify-Markierungen werden nicht nur mit Nachträgen überklebt.

Die Konvergenzprüfung ändert die Rollen nicht. Ein technischer Rebaseline- oder
Split-Auftrag bleibt `changes_requested` mit `owner: <implementer>`. `blocked` und
`owner: mike` gelten weiterhin ausschließlich für ein echtes Hindernis oder
eine tatsächlich notwendige Produktentscheidung. Nach jeder weiteren
inhaltlich erfolglosen Entwurfsrunde wird die Konvergenz erneut beurteilt.

<a id="der-übergabe-riegel--ready_for_codex-steht-zuletzt"></a>

[↑ Übersicht](#übersicht)

## Der Übergabe-Riegel — `<ready_phase>` steht zuletzt

*(Ergänzt 2026-08-24, nach einer Race Condition in Runde 15.)*

`STATUS.md` ist ein **gemeinsamer Dateihub**, kein Postfach mit Sperre. Verifier
liest die Datei, nicht den Git-Verlauf. Sobald dort `<ready_phase>` steht,
darf er claimen — auch wenn der Rest der Datei noch halb geschrieben ist.

In Runde 15 stand `phase: <ready_phase>` bereits auf der Platte, während die
`OUTBOX → <reviewer>` noch leer war. Verifier hat in genau diesem Fenster geclaimt und
ein Review ohne Nachricht begonnen. Kein Schaden, aber sichtbar Glück.

**Deshalb gilt für Coder bei jeder Übergabe diese Reihenfolge, ohne Ausnahme:**

1. Inhalt fertigstellen und committen.
2. `INBOX` leeren und `OUTBOX` **vollständig** schreiben.
3. **Zuletzt** `phase`, `owner`, `handoff_commit` und `review_round` setzen.
4. Sofort committen — der Zustand soll nicht länger als nötig nur auf der
   Platte liegen.

Schritt 3 ist der Riegel: Vorher gibt es nichts zu claimen. **Nach dem Claim
schreibt Coder bis zum Review-Ergebnis nicht mehr in `STATUS.md`** — auch nicht
„nur schnell" einen Tippfehler.

**Eng begrenzte Selbstheilung bei ausgebliebenem Status-Commit:** Findet Verifier
einen vollständigen `<ready_phase>`-Zustand nur uncommitted im Worktree, wartet
er kurz auf den unmittelbar folgenden Commit des Coders. Bleibt er aus, darf Verifier die
Übergabe nur dann atomar claimen und mitsichern, wenn ausschließlich
`_tickets/STATUS.md` verändert ist, die OUTBOX vollständig ist und der genannte
Produkt-Commit existiert. Bei weiteren Dirty-Dateien, unvollständiger OUTBOX
oder widersprüchlichem Handoff wird nicht geraten: formaler Handoff-Fehler.
Diese Ausnahme heilt nur den Transport; sie ersetzt nicht die Pflicht des Coders,
jede Übergabe sofort zu committen.

**Der Commit aus Schritt 4 kann scheitern — und dann ist der Riegel offen.**
*(Ergänzt 2026-08-27, nach T-22 Runde 2.)* In dieser Übergabe wies eine
Sicherheitsregel des Repos das Kommando ab, weil die **Commit-Message** die
Geheimnisdatei beim Namen nannte; der Riegel stand dadurch rund eine Minute
ohne Commit, und Verifier hat in genau diesem Fenster geclaimt. Der Fall ist
allgemeiner als sein Anlass: Jeder Hook, jeder Pre-Commit-Lauf und jeder
Formatprüfer kann Schritt 4 abweisen, nachdem Schritt 3 bereits auf der Platte
steht.

Deshalb: Scheitert der Commit, ist der Ready-Zustand **kein Zustand zum
Warten**. Entweder er wird sofort auf anderem Weg committet — die Ursache liegt
fast immer in der Message, nicht im Inhalt —, oder Schritt 3 wird
zurückgenommen, bis der Commit steht. Still im Ready zu verharren überlässt die
Übergabe dem Zufall, ob der Prüfer gerade nachsieht.

### Der Wechsel zum nächsten Kettenglied kommt **vor** dem ersten Produktedit

*(Ergänzt 2026-08-27, nach T-27a Runde 1.)* Nach einer Freigabe zieht Coder
zum nächsten Ticket der `priority_chain` weiter. Dabei entstand ein Fenster, in
dem Branch und Produktänderungen für T-27a schon sichtbar waren, während
`STATUS.md` noch `approved` und T-22 meldete.

Ein Race gab es nicht — der Owner blieb Coder. Trotzdem ist der Zustand
schädlich: **Wer nur die Datei liest, sieht ein abgeschlossenes Ticket und
gleichzeitig fremde Änderungen an einem anderen.** Das ist von einem
Kommunikationsabbruch nicht zu unterscheiden, und die Datei ist genau dafür da,
diesen Unterschied zu machen.

Deshalb ist der Wechsel ein eigener, **atomarer** Schritt vor dem ersten
Produktedit: `ticket`, `priority_ticket`, `review_round: 0` und
`phase: <working_phase>` in einem Commit. Erst danach der Branch, erst danach
die erste Zeile Code.

`review_round: 0` heißt wörtlich „noch keine Runde geprüft". Die `1` entsteht
beim Hochzählen der ersten Übergabe, nicht beim Arbeitsbeginn — sonst gäbe es
zwei verschiedene Runden mit derselben Nummer, und der Schlüssel
`(ticket, handoff_commit, review_round)` verlöre seine Eindeutigkeit genau
dort, wo die Duplikatsperre auf ihn baut. *(Der Loop-Prompt unten sagte hier
bis 2026-08-28 fälschlich `1`; Befund aus T-27a Runde 2.)*

Die Freigabe gilt für eingeplante Prüfungen, nicht für die von T-68
ausdrücklich ausgenommenen Archivskripte. Mike hat die Ausführung aller
versionierten Prüfskripte nach dem Muster
`./_tickets/30-doing/T-*.sh` ausdrücklich und dauerhaft freigegeben. Verifier darf diese
Skripte im Review ohne erneute fachliche Rückfrage ausführen, einschließlich
der für lokale Testserver oder externe Testquellen nötigen Sandbox-Freigabe.
Vor dem Lauf bleibt die übliche Sicherheitsprüfung des konkreten Skripts
verbindlich; die Freigabe erweitert weder den erlaubten Review-Scope noch die
Berechtigung, Produktcode oder fremde Ressourcen zu verändern.

<a id="browsertests-macht-claude--nicht-als-arbeitsteilung-sondern-mangels-browser"></a>

[↑ Übersicht](#übersicht)

## Browsertests nach verfügbarer Ausstattung

*(Entscheidung Mike, 2026-08-27, nach Runde 51.)*

Die damalige Browserzuordnung beschrieb die Ausstattung vom 27. August 2026.
Sie ist keine dauerhafte Eigenschaft von Coder oder Verifier.

**Heute entscheidet die verfügbare Ausstattung.** Der Coder führt
nötige visuelle Prüfungen mit tatsächlich verfügbaren Browserwerkzeugen aus
oder nennt konkret die fehlenden Belege. Für breite und schmale Ansichten
gelten die Messregeln aus `ux-standards`.

Der unabhängige Verifier bewertet die Belege und führt verfügbare Gegenproben
aus. Fehlt ihm ein Browser, weist er die nicht selbst geprüften Punkte aus.
Weder Agentenname noch Rollenwechsel ersetzen einen Browsernachweis.

[↑ Übersicht](#übersicht)

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
oder „Integrationstests“ ist keine solche Freigabe. Coder und Verifier dürfen sie
nicht aus vermuteten Bedürfnissen ableiten.

**Riegel beim Coder:** Reicht der schlanke Standard aus, wird er ohne
Rückfrage verwendet. Hält Coder ein Test-Subsystem dennoch für notwendig,
stoppt er vor Entwurf und Code mit `phase: blocked`, `owner: mike`, nennt die
minimale Standardlösung, den konkreten Mehrwert und den begrenzten Umfang der
gewünschten Ausnahme. Bis zur ausdrücklichen Entscheidung entsteht dafür kein
Code und kein Detailentwurf.

**Riegel beim Verifier:** Verifier inventarisiert in jedem Handoff neue
Test-Helfer, persistierte Testdaten, Plugins, Entry-Points, CLIs und
Transportpfade. Findet er ein Test-Subsystem ohne den Freigabeblock, ist das
unabhängig von grünen Tests ein `changes_requested`: entfernen und auf den
schlanken Standard zurückführen. Nur wenn der Standard nachweislich unmöglich
ist und dafür eine Produktentscheidung fehlt, wird an Mike blockiert.

[↑ Übersicht](#übersicht)

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
   Coder stoppt vor weiterer Flächenarbeit und hält fest, welcher dünne Pfad
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

**Riegel beim Verifier:** Verifier sucht die entscheidenden Akzeptanzfälle zuerst
und prüft mit einem kleinen Gegenlauf oder Mutanten, ob sie den alten/falschen
Zustand wirklich unterscheiden. Fehlen öffentlicher Eintritt, Frischstart,
negativer Mutant oder Matrix-Zuordnung, ist das unabhängig von grünen
Gesamtsuiten `changes_requested`.

Wird dieser Riegel während einer bereits laufenden Runde eingeführt, muss
Coder keinen Produktstand künstlich zurückdrehen. Vor der nächsten Übergabe
müssen die entscheidenden Tests jedoch nachweislich am alten beziehungsweise
minimal falschen Pfad rot und am neuen Pfad grün gewesen sein.

[↑ Übersicht](#übersicht)

## Standard-Riegel — die Hausregeln stehen im Bericht, nicht im Vorsatz

*(Entscheidung Mike, 2026-09-08.)*

Der Skill `code-standards` gilt für beide Rollen, und er gilt ab der ersten
Zeile: **Der Coder wendet ihn beim Schreiben an**, nicht erst, wenn der
Verifier danach fragt. Ein Review kann einen Standardverstoß nur finden — es
kann ihn nicht ungeschehen machen, und jede Fundstelle kostet eine Runde.

**Beide Rollen lesen die tatsächliche `SKILL.md` vor ihrer fachlichen Arbeit:**
der Coder vor dem ersten Codeedit, der Verifier vor der Prüfung. Dazu lesen
sie die zum Umfang passenden Referenzen aus dem Skill. Die bloße Nennung im
Prompt oder die Beschreibung im Skill-Katalog ersetzt das Lesen nicht.
Nach einem Kontextverlust ohne verfügbaren Skill-Inhalt erneut laden.

Der Verifier prüft die Anwendung unabhängig vom Coder-Bericht und berichtet **je Zeile der
Referenztabelle** ein Ergebnis:

- `✅` mit dem Beleg, der die Aussage trägt;
- `⚠️ n Befunde` mit Fundstelle und erwarteter Korrektur;
- `➖ nicht berührt`, wenn der Diff die Gruppe nicht anfasst.

Die OUTBOX des Coders trägt dieselben Zeilen. Sie sind seine Zusage, nicht
sein Wunsch: Ein `✅` ohne Beleg ist ein Befund, kein Ergebnis.
Beide Berichte nennen außerdem den tatsächlich gelesenen Skill-Pfad und die
verwendeten Referenzen. Fehlende Nachweise werden nachgetragen, bevor eine
Standards-Prüfung als vollständig bestätigt wird. Bei Konzept- und
Dokumentationsarbeit nur die anwendbaren Regeln prüfen; keine Codeprüfung
behaupten, wenn kein Code zum Prüfgegenstand gehört.

**Die Gruppenliste wird nicht hierher kopiert.** Sie steht in der Skill; eine
zweite Fassung wäre genau die parallele Wissensquelle, die der DRY-Prüfguard
unten verbietet. Kommt dort eine Referenz dazu, entsteht die Berichtszeile von
selbst. Wer die Zeilen nicht kennt, hat die Skill nicht geladen — und genau
das ist der Zweck der Konstruktion.

**Warum das nicht schon durch den Linter erledigt ist.** Ein grüner Lauf
belegt nur die Regeln, die der Linter kennt. `pyproject.toml` hat keinen
`[tool.ruff]`-Abschnitt; Ruff läuft mit Vorgaben, also ohne Importsortierung
(`I`) und ohne Quote-Stil (`Q`). Für genau die Hausregeln, um die es hier
geht, ist ein grüner Ruff-Lauf deshalb kein Nachweis.

[↑ Übersicht](#übersicht)

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

[↑ Übersicht](#übersicht)

## Aktivierung der Agenten

Die kopierbaren Startbefehle und die Unterschiede zwischen In-Context-Scheduler
und Chat-Loop stehen in [AGENT-ACTIVATION.md](AGENT-ACTIVATION.md).
Beide Wege lesen vor fachlicher Arbeit die Rollen und den Owner aus STATUS.md.

[↑ Übersicht](#übersicht)
