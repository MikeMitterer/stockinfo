# T-40 · Universelles Agenten-Implementierungs- und Review-Regelwerk

**Abgeschlossen durch Ablösung, 7. September 2026.** Mike hat bestätigt,
dass der Auftrag nach KanTandem übergeht. In StockInfo bleibt kein paralleler
T-40-Arbeitsauftrag offen.

Die acht ursprünglichen Kriterien sind **nicht pauschal erfüllt oder
abgenommen**. Ihr Stand und die noch offenen Arbeiten stehen in
[KanTandem · übernommene Nacharbeit](/Volumes/DevLocal/DevKI/Production/KanTandem/CONCEPT.md#6-übernommene-nacharbeit-aus-stockinfo-t-40).
Der begrenzte Anschlusscheck von KanTandem wird dadurch nicht erweitert.

## Ursprünglicher Auftrag · Historie

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| projektübergreifend / StockInfo als Ausgangspunkt | abgelöst durch KanTandem | 1 Tag | bestehende Regeln verallgemeinern und wiederverwendbar paketieren; kein Produktcode | — |

- **Angelegt:** 2026-08-29, auf Wunsch von Mike
- **Hängt ab von:** T-31 → T-38 → T-37 → T-35 → T-39 vollständig
  technisch freigegeben
- **Reihenfolge:** erst nach Abschluss der Plugin-Implementation; T-39 bleibt
  das letzte Plugin-/Produkt-Ticket
- **Ziel:** Das in StockInfo erprobte Regelwerk soll ohne StockInfo-Wissen in
  anderen Projekten einsetzbar sein.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ bestätigt mit Einschränkung (Fußnote) ·
◑ teilweise (Fußnote) · ➖ keine Live-Verifikation (nur Unit/Review).
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | Inventar | Statusprotokoll, Verify-Matrix, Vertical Acceptance, Testinfrastruktur, DRY, Konvergenz und Review-Muster sind vollständig erfasst; StockInfo-Sonderfälle sind von allgemeinen Regeln getrennt | | |
| **2** | wiederverwendbarer Workflow | die kanonische Fassung verwendet die Rollen `implementer`, `reviewer`, `human owner` statt Claude/Codex/Mike und enthält keine StockInfo-Pfade oder Asset-Beispiele als Voraussetzung | | |
| **3** | `task-verification-workflow` | das bestehende Skill wird erweitert statt ein konkurrierendes zweites Regelpaket anzulegen; Triggerbeschreibung und Anweisungen decken Implementierung plus unabhängigen Review ab | | |
| **4** | Bootstrap-Templates | ein neues Projekt kann mit kleinen Vorlagen für Board, `STATUS.md`, Verify-Matrix und Review-Muster starten; projektspezifische Namen und Pfade stehen nur in einem dünnen Adapter | | |
| **5** | Vertical-Acceptance-Beispiel | ein neutrales Beispiel zeigt roten öffentlichen Akzeptanzfall, dünnen vertikalen Pfad, Frischstart, negativen Mutanten und Matrix→Orakel-Zuordnung ohne eigenes Test-Subsystem | | |
| **6** | Gegenprobe | ein projektneutraler Test-/Review-Fall weist nach, dass der Workflow eine grüne Gesamtsuite ohne entscheidenden Akzeptanzfall ablehnt | | |
| **7** | StockInfo-Rückbindung | StockInfo verweist auf die universelle Quelle und behält nur Rollen, Pfade, Ticketkette und lokale Ausnahmen; keine zwei auseinanderlaufenden Vollkopien bleiben bestehen | | |
| **8** | kurze Einführung | ein Entwickler kann den Workflow in einem anderen bestehenden Repo in höchstens etwa 15 Minuten einrichten und weiß, welche Teile er anpassen muss | | |

---

## Verbindlicher Zuschnitt

1. **Bestehendes Skill erweitern.** T-40 verwendet `skill-creator` und
   `task-verification-workflow`. Es entsteht kein zweites Skill mit nahezu
   gleichem Zweck.
2. **Kern und Adapter trennen.** Universell sind Zustandsautomat, Owner-Riegel,
   zweistufige Verify-Matrix, Vertical-Acceptance-Riegel, Testinfrastruktur-
   Grenze, DRY-Prüfung, Konvergenz und Musterlernen. Lokal bleiben Agentennamen,
   Dateipfade, Branchkonventionen, Ticketreihenfolge und Produktausnahmen.
3. **Beispiele neutralisieren.** StockInfo-Befunde dürfen als Herkunft oder
   Beleg verlinkt werden, aber der Leser muss das Regelwerk ohne Kenntnisse von
   Wertpapieren, Plugins oder diesem Repository anwenden können.
4. **Klein paketieren.** Bevorzugt werden eine kurze Hauptanweisung, wenige
   Vorlagen und gezielt geladene Referenzen. Keine zweite Workflow-Engine, kein
   Daemon und keine neue Test-CLI.
5. **An einem fremden Kontext prüfen.** Die Gegenprobe verwendet ein neutrales
   Beispiel oder ein zweites bestehendes Projekt. Sie verändert dort nichts
   ohne ausdrückliche Berechtigung; ein temporärer Fixture-Repo genügt.

---

## Nicht im Scope

- keine Änderung am StockInfo-Produkt, Plugin-Vertrag oder Dashboard;
- keine allgemeine Coding-Style-Sammlung — dafür existieren eigene Skills;
- keine autonome Agentenplattform und keine neue Scheduler-Implementierung;
- keine Vollkopie von `_tickets/.agents/AGENT-WORKFLOW.md` in jedes Projekt.

---

## Auflösung

**Abschlussart:** Ablösung und Übergabe, keine vollständige fachliche Abnahme.

**Entscheidung:** Mike, 7. September 2026, „OK, passt“ zum Vorschlag,
T-40 in StockInfo als durch KanTandem abgelöst abzuschließen und die offenen
Anforderungen dort weiterzuführen.

**Übergabe:** Alle acht Kriterien sind in KanTandem/CONCEPT.md, Abschnitt 6,
mit bestehendem Ergebnis und verbleibender Arbeit erfasst. Der Projekteinstieg
verlinkt sie. Ticket-Skill und Vorlage wurden bereits verbessert; vollständige
Universalisierung, neutrale Gegenprobe und StockInfo-Rückbindung bleiben offen.

Die ursprünglichen AI- und Human-Zellen bleiben unverändert. Mit diesem
Abschluss wird kein bisher fehlender Test- oder Abnahmenachweis behauptet.
