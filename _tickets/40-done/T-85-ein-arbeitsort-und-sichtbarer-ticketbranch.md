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
| 1 | `AGENTS.md`, `STATUS.md` und Board-Einstiege lesen | Ein Arbeitsort, Owner-Wechsel und Branch-Prüfung widerspruchsfrei beschrieben | ✅ |
| 2 | `git worktree list --porcelain` und `git branch --show-current` im StockInfo-Root prüfen | Root und `STATUS.branch` stimmen; keine benötigte Ticketfassung liegt nur außerhalb des Roots | ✅ |
| 3 | T-84 mit seinem bisherigen Branch und Commit vergleichen | Ticket und Dokumentationsstand bleiben vollständig erhalten und vom Root aus erreichbar | ✅ |
| 4 | Übergabe, technische Freigabe und menschliche Abnahme am dokumentierten Beispiel durchgehen | Merge auf `master` erfolgt nach technischer Freigabe, ohne Abnahme oder Push vorzutäuschen | ◑ |

**Belege (Claude, 2026-10-01):**

1. Die Regel steht einmal in `AGENTS.md` im Abschnitt „Ein Arbeitsort: der
   Projekt-Root“. STATUS (Hinweis über dem Zustandsblock), Workflow
   („Ticketpfade und Arbeitsbeginn“), Aktivierung (Board-Pfad und
   Claude-Durchlauf Schritt 1), Codex-Scheduler („Projekt“) und
   `_tickets/README.md` („Ablage“) verweisen nur darauf. Sie nennen jeweils
   die Prüfung, die an ihrer Stelle anfällt.
2. `git worktree list --porcelain` zeigt nur noch den Root, auf
   `t-85-ein-arbeitsort`; `STATUS.branch` nennt denselben Branch. Der
   saubere Worktree `/private/tmp/stockinfo-internet-hinweis` ist per
   `git worktree remove` entfernt; dort lag nur die ignorierte, erzeugte
   Vorschau `docker/preview/`. Der verwaiste Eintrag
   `stockinfo-release-20260925` (Gitdir fehlte, `release/stockinfo-0-7`
   ohne Commits außerhalb von `master`) ist per `git worktree prune`
   entfernt. Sein Verzeichnis unter `/private/tmp` ist nicht gelöscht.
3. Der Branch `docs/internet-zugriff-hinweis` steht unverändert auf
   `6ca09d2`; Doku-Commit `396e8be` ist darin enthalten. Der
   reine Ticket-Commit `6ca09d2` ist per `cherry-pick -x` als `336ef69`
   auf das Board übernommen. T-84 liegt damit unter `10-backlog/`. Das
   Ticket nennt jetzt den Root als Arbeitsort für seinen Branch.
4. Durchlaufen an diesem Ticket: technische Freigabe durch Codex
   (`4bcad36`), danach lokaler Merge von `t-85-ein-arbeitsort` nach
   `master` durch den Coder. Mikes Abnahme stand vorab fest (siehe Auflösung).
   Kein Push.

### Akzeptanzkriterien

- [x] Neue Arbeit nutzt nur den StockInfo-Root und einen dort ausgecheckten Ticketbranch.
- [x] `STATUS.branch` ist maschinenlesbar und stimmt mit Git überein.
- [x] Nur der Owner wechselt den Branch; der Verifier prüft die übergebene Fassung ohne Wechsel.
- [x] Technische Freigabe, lokaler Merge, menschliche Abnahme und Veröffentlichung sind getrennt dokumentiert.
- [x] T-84 ist im Root sichtbar; seine vorbereiteten Änderungen und Nachweise bleiben erhalten.
- [x] Doku-Abgleich nennt StockInfo-Dateien und den tatsächlichen Stand der gemeinsamen Skill-Übernahme.

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

**Doku-Abgleich (Claude, 2026-10-01):**

- Geändert: `AGENTS.md` (neuer Abschnitt mit Übersichtseintrag),
  `_tickets/STATUS.md` (Feld `branch` und Hinweis),
  `_tickets/.agents/AGENT-WORKFLOW.md`, `AGENT-ACTIVATION.md`,
  `CODEX-IN-CONTEXT-SCHEDULER.md`, `_tickets/README.md`, T-84 (Arbeitsort).
- Unverändert: `README.md`, `docker/README.md` und `unraid/README.md`.
  Sie erwähnen weder Worktrees noch Ticketbranches; „`master`“ steht dort nur
  für veröffentlichte Links. `git grep` nach `worktree`, `/private/tmp` und
  `show-current` außerhalb archivierter Tickets: die übrigen Treffer meinen
  den Arbeitsbaum, sind Historie in STATUS oder ein temporäres
  Datenverzeichnis des T-63-Smokes.
- Gemeinsames Paket: Die installierte Fassung `df699dd1…` enthält keine
  Arbeitsort- oder `branch`-Regel. `PROJECT-RULES.md` mergt dort erst nach
  menschlicher Abnahme. `AGENTS.md` weist den früheren lokalen Merge als
  StockInfo-Ausnahme aus. Übernahme: AgentLessons T-52, offen.
- Offen, nicht Teil von T-85: Der lokale Workflow trägt noch keinen
  `Übernahmestand der Board-Konventionen` (Paket: `2026-09-28-activity-local`).
  Zuständig ist der Coder des Board-Abgleichs, sobald Mike ihn einplant.

### Auflösung

Umgesetzt auf `t-85-ein-arbeitsort`, Übergabe an den Verifier `codex`.
Nach technischer Freigabe mergt der Coder lokal nach `master`. Der Branch
enthält dabei auch die Boardcommits zu T-82 und T-83 sowie den T-84-Ticket-Commit;
das sind ausschließlich Dateien unter `_tickets/`. Kein Push.

**Abschluss · Mike, 2026-10-01.** Vor dem Review hat Mike festgelegt:
„Wenn Codex das abgenommen hat ist es auch für mich OK und das Ticket ist
erledigt. Fange dann gleich mit T-83 an“. Codex hat Runde 1 mit dem Stand
`4bcad36` freigegeben. Claude hat das Ticket nach `40-done/` verschoben und
den Branch lokal nach `master` gemergt. Danach ist T-83 aktiviert, mit
Claude als Coder. Ein Push ist nicht beauftragt und nicht erfolgt. Offen
bleiben AgentLessons T-52 und der Abgleich des Board-Konventionsstands.

### Verifier-Prüfung · Runde 1 (Codex, 2026-10-01)

**Ergebnis: `approved`.** Prüfgegenstand war `7b19fb3` gegen `7d38879`.
Die technische Freigabe umfasst den verhaltensneutralen Review-Commit
`4bcad36` zu T-84. Sie ist keine menschliche Abnahme und belegt noch keinen
Merge, Push oder eine Veröffentlichung.

- **Verify #1:** Die Regel steht in `AGENTS.md`; STATUS, Workflow, Aktivierung,
  Scheduler und Board-README verweisen auf sie. Rollen und Owner waren beim
  Review eindeutig; `branch` und `git branch --show-current` stimmten auf
  `t-85-ein-arbeitsort` überein. Die lokale Abweichung vom gemeinsamen
  `PROJECT-RULES.md` ist ausdrücklich benannt.
- **Verify #2:** `git worktree list --porcelain` zeigte nur den Projekt-Root.
  `docs/internet-zugriff-hinweis` steht weiter auf `6ca09d2`, das den
  vorbereiteten Dokumentations-Commit `396e8be` enthält. Die Branches
  `t-83-assets-datenhinweis` und `t-85-ein-arbeitsort` bewahren die jeweiligen
  Boardstände. Der Arbeitsbaum war nach der Korrektur sauber.
- **Verify #3:** Das T-84-Ticket aus `6ca09d2` ist mit seinem Prüfgegenstand
  und den offenen Verify-Zeilen im Root unter `10-backlog/` erhalten. Bei der
  Übernahme wurde der Arbeitsorttext angepasst. Im übernommenen Ticket
  stand T-83 noch als aktiv; `4bcad36` hat diese zwei Gegenwartsaussagen an
  STATUS angepasst. Der vollständige Selbstheilungs-Diff wurde erneut gelesen;
  `git diff --check 7d38879 4bcad36` blieb sauber.
- **Verify #4:** Die Dokumente trennen technische Freigabe, lokalen Merge,
  Mikes Abnahme und Push. Der tatsächliche Merge ist noch ausstehend; die
  Zeile bleibt deshalb auf ◑. Claude führt ihn erst nach dieser Freigabe aus.

**Umfang:** `git diff --name-status 7d38879 7b19fb3` bestätigt acht
Dokumentations- und Boarddateien, keine Produktdatei. Seit der Übergabe kam
außer STATUS nur die genannte T-84-Textkorrektur hinzu. Der Vergleich
`master..7b19fb3` enthält zusätzlich die bereits benannten Boardtickets
T-82 und T-83, keinen Produktcode. DRY: Die neue Arbeitsortregel steht nur
in `AGENTS.md`; die übrigen aktiven Einstiege verlinken sie.

**Code-Standards:** Gelesen:
`/Users/macminipro/.codex/skills/code-standards/SKILL.md` und
`references/documentation.md`. Architektur ➖, Shell ➖, CLI ➖,
Frontend/i18n ➖, Python ➖, Persistenz ➖, Qualität/Tests ➖: nicht berührt.
Dokumentation ✅: Übersicht und Rücklink in `AGENTS.md`, aktuelle
Board-Einstiege und T-84-Stand abgeglichen. DRY ✅: eine Regelquelle mit
Verweisen. Die passenden Autoren-Lessons SI-P-02, SI-P-06, SI-P-11,
SI-P-12 und SI-P-13 wurden auf Diff und Übergabe angewendet; ein neues
allgemeines Muster ist aus der redaktionellen T-84-Korrektur nicht belegt.

**Doku-Abgleich:** `AGENTS.md`, STATUS, Workflow, Aktivierung, Scheduler,
`_tickets/README.md` und T-84 sind geprüft; die T-84-Gegenwartsaussagen
wurden nachgezogen. `README.md`, `docker/README.md` und `unraid/README.md`
enthalten keine Aussagen zu Worktrees oder Ticketbranches und benötigen
keine Änderung. AgentLessons T-52 bleibt die offene gemeinsame Übernahme
der Branchregel. Der lokale Board-Konventionsstand
`2026-09-28-activity-local` ist weiterhin nicht vollständig übernommen;
der offene Abgleich ist oben mit dem zuständigen künftigen Board-Coder
benannt. Dieser Review behauptet keine zentrale Übernahme.
