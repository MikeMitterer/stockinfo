# _tickets — Verify-Board

Der Ablageort zeigt den Arbeitsstand eines Tickets. Die genaue Reihenfolge,
Rollen und aktuelle Bearbeitungsphase stehen ausschließlich in [STATUS.md](STATUS.md).

## Übersicht

- [Ablage](#ablage)
- [Von der Aufnahme bis zum Abschluss](#von-der-aufnahme-bis-zum-abschluss)
- [Nachweise und Agentenregeln](#nachweise-und-agentenregeln)
- [Historischer Stand](#historischer-stand--august-2026)

## Ablage

```text
_tickets/
├── .agents/       # Workflow, Aktivierung, Scheduler und Erfahrungen
├── 10-backlog/    # gewollt, noch nicht eingeplant
├── 20-ready/      # beauftragt, als Nächstes vorgesehen
├── 30-doing/      # begonnen, einschließlich Review und Nacharbeit
├── 40-done/       # abgeschlossen
├── 80-iced/       # auf Eis, keine Wiederaufnahme eingeplant
├── 90-rejected/   # bewusst verworfen
├── README.md      # diese Anleitung
├── STATUS.md      # Rollen, Reihenfolge, Phase und Mailbox
└── QUESTIONS.md   # offene Fragen während der Arbeit
```

Tickets und ihre Begleitdateien liegen gemeinsam im passenden Ordner.
Im Root bleiben nur die drei genannten Board-Dateien. Der versteckte
Ordner [.agents/](.agents/) ist versioniert und wird bei Inventaren und
Linkprüfungen ausdrücklich eingeschlossen.

[↑ Übersicht](#übersicht)

## Von der Aufnahme bis zum Abschluss

1. Neue gewollte Arbeit in `10-backlog/` erfassen. Noch keine Umsetzung aus
   Ticketnummer, Dateiablage oder einer Konzeptfreigabe ableiten.
2. Beauftragte Folgearbeit nach `20-ready/` verschieben und in STATUS einplanen.
   Die Ordnernummern sortieren die Ablage; sie bestimmen keine Priorität.
3. Vor dem ersten Edit das nächste Kettenglied von `20-ready/` nach `30-doing/`
   verschieben. In demselben Commit `ticket`, `priority_ticket`, Arbeitsphase
   und `review_round: 0` setzen; vorhandene Reviewhistorie bleibt erhalten.
4. Während Umsetzung, Review und Nacharbeit bleibt das Ticket in `30-doing/`.
   Die Phase steht ausschließlich in STATUS; die technische Verify-Matrix
   beschreibt die Nachweise und ist kein zweiter Board-Status.
5. Erst nach der erforderlichen Abschlussbestätigung nach `40-done/`
   verschieben. Eine technische Freigabe allein verschiebt kein Ticket.
   Vorhandene menschliche Antworten bleiben unverändert; offene Blocker
   verhindern den Abschluss und den Beginn des nächsten Tickets.
6. Zurückstellen nach `80-iced/`, Verwerfen nach `90-rejected/`: Grund und Datum
   festhalten. Wiederaufnahme braucht eine ausdrückliche Einplanung nach
   `20-ready/`; diese Ordner starten keine automatische Arbeit.

Bei jedem Verschieben Begleitdateien und aktuelle Verweise mitführen.
Vor der Aufnahme in Ready oder Doing die [Grenzen in STATUS](STATUS.md#ticketgrenzen)
nach der gemeinsamen [Aufnahmeregel](.agents/AGENT-WORKFLOW.md#ticketgrenzen) prüfen.
Die mit T-68 aus `solved/` archivierten Skripte bleiben bytegleich und werden
für die Ordnerumstellung nicht erneut ausgeführt. Neue oder künftig geänderte
Skripte folgen dem aktuellen Ticket-Skill und finden den Projekt-Root unabhängig
vom Ticketordner. Historische Berichte behalten ihre Aussagen und Belege.

[↑ Übersicht](#übersicht)

## Nachweise und Agentenregeln

`AI` füllt die KI anhand konkreter Belege: ✅ bestätigt, ⚠️ mit Einschränkung,
◑ teilweise, ➖ ohne Live-Nachweis. `Human` und Originalantworten schreibt
nur der Mensch. Jedes Ticket hat eine aktuelle technische Verify-Matrix.
[QUESTIONS.md](QUESTIONS.md) sammelt kurzfristige Fragen; Antworten werden
ins Ticket oder die passende dauerhafte Dokumentation übertragen.

Das Board kennt drei Rollen: **Coder** (`implementer`) setzt um, **Verifier**
(`reviewer`) prüft unabhängig, **Observer** (`observer`) beobachtet den Ablauf,
ohne etwas zu ändern. Zugeordnet werden sie ausschließlich in
[STATUS.md](STATUS.md); `unassigned` heißt bereit, aber unbesetzt, und hält
keine Arbeit auf. Der Observer ist derzeit unbesetzt.

Der gemeinsame [Workflow](.agents/AGENT-WORKFLOW.md) regelt Rollen, Übergabe,
Scope-Vertrag, Rundenlimit, Selbstheilung und Fortsetzung. Die
[Aktivierung](.agents/AGENT-ACTIVATION.md) beschreibt die jeweiligen Laufzeiten;
der [Codex-Scheduler](.agents/CODEX-IN-CONTEXT-SCHEDULER.md) deren Codex-Vertrag.
Die Linkeinstiege [Claude](.agents/CLAUDE-LESSONS.md) und
[Codex](.agents/CODEX-LESSONS.md) verweisen auf lokale Einzeldateien.
[Zugriff und Pflege](.agents/LESSONS-ACCESS.md) beschreiben das vollständige
Verzeichnisinventar und den gemeinsamen Bestand in AgentLessons. Der Workflow
regelt Vorbeugung, unabhängige Gegenprüfung und Lessons-Pflege.

Beide Rollen laden `code-standards` vor fachlicher Arbeit. Scope-Vertrag und
Soll/Ist-Budget richten sich nach dem gemeinsamen Workflow. Die allgemeinen
Ticketformate und die sechs Ordner sind im Skill `task-verification-workflow`
beschrieben; diese README beschreibt ihre Anwendung in StockInfo.
Andere bestehende Projektboards behalten ihre dokumentierte Ablage bis zu
einer eigenen Umstellung.

[↑ Übersicht](#übersicht)

## Historischer Stand · August 2026

Die folgende Übersicht dokumentiert eine frühere Runde. Aktuelle Einordnung:
Ticketordner; aktive Arbeit und Priorität: `STATUS.md`.

**Offen (Board-Root):**

| Ticket | Thema | Status |
|---|---|---|
| [T-09](40-done/T-09-manuelle-etf-werte-nachtragen.md) | Asset-Kennzahlen manuell nachtragen (persistent, DB+API+UI) | in-review |
| [T-13](40-done/T-13-toasts-und-dialoge.md) | Toasts statt Banner, Dialoge auf `NModal` — der Rest aus T-12 | in-review |
| [T-14](80-iced/T-14-kontrast-umgekehrte-leisten.md) | Kontrast auf umgekehrten Leisten — und ein Prüfskript, das ihn sieht | ready |

`in-review` heißt: umgesetzt, die `AI`-Spalte der Verify-Matrix ist gefüllt, die
`Human`-Spalte noch nicht. **Nach `solved/` wandert ein Ticket erst auf Ansage** —
die KI verschiebt es nie von sich aus.

**Erledigt (`solved/`):** T-01…T-08, T-10, T-11-Reihe und T-12.

Zur T-11-Reihe: Der Branch-Stapel wurde am 16.08.2026 per Fast-Forward nach
`master` geführt. T-11d/e/f/g/h wurden nicht einzeln umgesetzt — sie wollten
nachbauen, was `@mikemitterer/ux-foundation` mitbringt, und gingen in T-12 auf.

Zu T-12: Die App bezieht Token, Themes, Schriften, Reset, Symbole, Leisten und
die wiederkehrenden Composables aus dem Fundament; Bedienelemente kommen von
Naive UI. Die vier eigenen Paletten (`earth`, `night`, `sunset`, `neon`) sind
entfallen. Eigen bleibt die **Marke** — Koralle nach Pflaume.

Zu T-13: Meldungen sind Toasts, die Dialoge sitzen auf `NModal`, und die
„?"-Hinweise kommen als `UxInfoHint` aus dem Fundament. „Alle aktualisieren"
ist dabei in die Kopfzeile gezogen — im oberen rechten Eck des Inhalts
verdeckte die Meldung sonst den Knopf, mit dem man ihre Ursache behebt.
Verify #7 (Kontrast in `sepia`) reißt und lebt als **T-14** weiter.

Zu T-09: Fehlende Kennzahlen (TER, Vola, Thesaurierend) lassen sich an Ort und
Stelle nachtragen und liegen in einer **eigenen** Tabelle — der Kurs-Refresh
schreibt die Instrumentenzeile neu und hätte sie sonst mitgenommen. Vorrang hat
die Quelle; verdeckt sie eine Eingabe, sagt die Oberfläche das und nennt den
eigenen Wert.

**Voraussetzung Test:** Stack läuft (`make dev-up`) — Backend `:8000`,
Dashboard `:5173`.
