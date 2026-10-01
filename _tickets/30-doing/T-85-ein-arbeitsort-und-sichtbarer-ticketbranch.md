# T-85 · Ein Arbeitsort und sichtbarer Ticketbranch für StockInfo

**Warum dieses Ticket:** Mike hat am 2026-10-01 beauftragt, die neuen
StockPortfolio-Regeln für Branches und Arbeitsorte auch auf StockInfo zu
übertragen. Derzeit liegt T-84 nur in einem zusätzlichen Worktree unter
`/private/tmp/stockinfo-internet-hinweis`; vom StockInfo-Projekt-Root aus ist
das Ticket nicht sichtbar. Künftig sollen Board und prüfbarer Quellstand an
einem Ort liegen.

**Beispiel:** Mike öffnet den StockInfo-Root, liest in `STATUS.md` den aktiven
Branch und prüft genau diesen Stand dort. Ein Ticket im Backlog ist vom Root
aus sichtbar, auch wenn seine Umsetzung noch nicht aktiviert wurde.

**Stand:** Aktiviert von Mike am 2026-10-01 („Setze als erstes T-85 um“),
vor T-83. Coder `claude`, Verifier `codex`. Arbeitsbranch
`t-85-ein-arbeitsort`, abgezweigt von `t-83-assets-datenhinweis` (`7d38879`).
Dieser Branch enthält gegenüber `master` nur Boardcommits.

## Gewünschte Änderung

1. StockInfos `AGENTS.md` erhält die lokale Regel: Alle Instanzen arbeiten im
   Projekt-Root, ohne neue Worktrees oder Kopien, sofern Mike keine Ausnahme
   ausdrücklich anordnet. `_tickets/` liegt nur dort.
2. `STATUS.md` nennt den im Root ausgecheckten Branch in einem
   maschinenlesbaren Feld `branch`. Vor jedem fachlichen Durchlauf vergleichen
   die Rollen dieses Feld mit `git branch --show-current`; bei Abweichung
   stoppen sie und melden den Konflikt. Nur der aktuelle Owner schaltet den
   Branch. Der Verifier prüft die Übergabe im Root und liest ältere Fassungen
   mit Git, ohne den Branch zu wechseln.
3. Nach technischer Freigabe wird der geprüfte Ticketbranch lokal nach
   `master` integriert und der Root auf `master` zurückgestellt. Mikes
   menschliche Abnahme erfolgt auf `master`; Nacharbeit beginnt auf einem
   neuen Branch von `master`. Veröffentlichung und Push bleiben getrennte
   Entscheidungen. Bestehende offene menschliche Abnahmen bleiben offen.
4. Vorhandene Branches und Worktrees, insbesondere T-84, werden ohne Verlust
   der Ticket- und Commit-Geschichte in den einen Arbeitsort überführt. Der
   aktive T-83-Stand bleibt bis zu seiner ordentlichen Übergabe unangetastet;
   fremde Änderungen werden nicht verworfen.
5. Workflow, Aktivierung, Scheduler, Board-Einstieg und relevante Anleitungen
   werden auf dieselbe Regel abgeglichen. Die gemeinsame Übernahme im
   AgentLessons-Paket ist ein eigener Auftrag: AgentLessons T-52. Lokale
   StockInfo-Ausnahmen und dessen Rollen bleiben maßgeblich.

## Verify

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | `AGENTS.md`, `STATUS.md` und Board-Einstiege lesen | Ein Arbeitsort, Owner-Wechsel und Branch-Prüfung widerspruchsfrei beschrieben | ➖ |
| 2 | `git worktree list --porcelain` und `git branch --show-current` im StockInfo-Root prüfen | Root und `STATUS.branch` stimmen; keine benötigte Ticketfassung liegt nur außerhalb des Roots | ➖ |
| 3 | T-84 mit seinem bisherigen Branch und Commit vergleichen | Ticket und Dokumentationsstand bleiben vollständig erhalten und vom Root aus erreichbar | ➖ |
| 4 | Übergabe, technische Freigabe und menschliche Abnahme am dokumentierten Beispiel durchgehen | Merge auf `master` erfolgt nach technischer Freigabe, ohne Abnahme oder Push vorzutäuschen | ➖ |

### Akzeptanzkriterien

- [ ] Neue Arbeit nutzt nur den StockInfo-Root und einen dort ausgecheckten Ticketbranch.
- [ ] `STATUS.branch` ist maschinenlesbar und stimmt mit Git überein.
- [ ] Nur der Owner wechselt den Branch; der Verifier prüft die übergebene Fassung ohne Wechsel.
- [ ] Technische Freigabe, lokaler Merge, menschliche Abnahme und Veröffentlichung sind getrennt dokumentiert.
- [ ] T-84 ist im Root sichtbar; seine vorbereiteten Änderungen und Nachweise bleiben erhalten.
- [ ] Doku-Abgleich nennt StockInfo-Dateien und den tatsächlichen Stand der gemeinsamen Skill-Übernahme.

### Side-Effects

Die Umstellung berührt den laufenden T-83-Branch und vorbereitete
Dokumentationsarbeit. Deshalb keine Worktrees entfernen oder Branches wechseln,
bevor der zuständige Owner den Übergang anhand der Git-Stände geplant hat.

### Doku-Abgleich

Betroffen: StockInfo `AGENTS.md`, `_tickets/STATUS.md`,
`_tickets/.agents/AGENT-WORKFLOW.md`, `AGENT-ACTIVATION.md`,
`CODEX-IN-CONTEXT-SCHEDULER.md`, `_tickets/README.md` und gegebenenfalls
Benutzungsanleitungen mit Branch- oder Arbeitsortbezug. `README.md` und
`docker/README.md` auf widersprüchliche Betriebs- oder Entwicklungsangaben
prüfen. AgentLessons T-52 bleibt eine offene zentrale Übernahme, bis Paket
und Skill tatsächlich geändert und installiert sind.

### Auflösung

Offen. Dieses Backlog-Ticket aktiviert keine Arbeit und ändert keine Rollen.
