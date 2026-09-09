# StockInfo — Einstieg für Codex

**Die Projektregeln stehen in [`CLAUDE.md`](CLAUDE.md).** Sie gelten
unverändert auch hier: Namensregeln, Sprachtrennung, das Inventar statt der
Textsuche, der Ablauf vor Arbeitsbeginn.

Diese Datei existiert, weil `AGENTS.md` der übliche projektweite Einstieg für
Codex ist — sie **verweist**, sie kopiert nicht. Eine zweite Regelkopie liefe
beim ersten Nachtrag auseinander, und die Fassung vom 2026-08-26 hat genau das
vorgeführt: Aus einer blinden Ersetzung von „Claude" durch „Codex" wurde eine
„Mailbox zwischen Codex und Codex" und ein `owner`-Riegel, der das Gegenteil
sagte.

## Rollen und Aktivierung

**Coder und Verifier werden ausschließlich in `_tickets/STATUS.md` zugeordnet.**
Die eigene Instanz prüft vor jedem Turn `implementer`, `reviewer` und `owner`.
Nur der zuständige Coder implementiert; der Verifier prüft unabhängig.
Wer nicht am Zug ist, verändert keinen Produktcode.

- `_tickets/.agents/AGENT-WORKFLOW.md` enthält den gemeinsamen fachlichen Vertrag.
- Die passende Mustersammlung vor Übergabe beziehungsweise Review lesen:
  `_tickets/.agents/CODEX-LESSONS.md` für Codex-Arbeit,
  `_tickets/.agents/CLAUDE-LESSONS.md` für Claude-Arbeit; bei gemischter
  Autorenschaft beide. Maßgeblich ist der Autor der geprüften Fassung.
- `_tickets/.agents/AGENT-ACTIVATION.md` enthält die laufzeitspezifische Startsyntax.

Die historischen Dateinamen legen keine Rollen fest.
