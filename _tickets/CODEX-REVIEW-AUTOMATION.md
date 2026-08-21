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
die Phase `approved` mit `owner: mike` oder `changes_requested` mit
`owner: claude`. Bei einem echten, nicht sicher lösbaren Hindernis gilt
`blocked` mit `owner: mike`.

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
   - Aussagekraft der Tests. Mocke nur externe Grenzen und lasse eigenen Code
     real durchlaufen;
   - die relevanten Tests und, risikogerecht, die vollständige Testsuite.
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
   owner claude. Ohne Finding: phase approved, owner mike. Aktualisiere
   updated_at und übernimm das bearbeitete Tupel in die drei
   last_reviewed_*-Felder. review_round bleibt unverändert; Claude erhöht sie
   erst mit einer neuen Übergabe.
9. Melde Mike nur ein neues Review-Ergebnis, einen Blocker oder eine nötige
   Entscheidung. Gib getestete Befehle und Ergebnis knapp an.
```

Aktiver Takt: alle 5 Minuten während der laufenden Entwicklungsphase. Der
lokale Rechner und die Codex-Desktop-App müssen dafür laufen. Ein engerer Takt
bringt wenig, weil der Zustandsfilter Leerdurchläufe ohnehin sofort beendet.
