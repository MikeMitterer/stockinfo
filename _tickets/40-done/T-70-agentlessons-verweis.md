# T-70 · StockInfo als Quelle für AgentLessons

Die StockInfo-Lessons liegen als Einzeldateien vor, damit AgentLessons sie
einsammeln und ihre Herkunft belegen kann. Die Agentenanleitungen beschreiben
den Zugriff auf die lokalen Originale und das zentrale Archiv.

**Abgeschlossen am 2026-09-25.** Mike bestätigt die Bereinigung, den lokalen
Ticketabschluss und die Übernahme nach `master`: „Ich folge deiner Empfehlung -
erledig das“. Für StockInfo ist kein weiterer Handgriff offen. Der Abschluss
betrifft diesen lokalen Anteil, nicht das gesamte AgentLessons-Hauptticket.

## Abschluss und Nachweise

Alle 16 lokalen Lessons sind im zentralen Archiv vorhanden; ihre SHA-256-Werte
stimmen mit `archive.source_sha256` überein. Vier Archivtexte enthalten
angepasste Verweise, ansonsten stimmen die Textkörper mit den Originalen
überein. `agent-lessons --info` bestätigt StockInfo als erreichbare Quelle mit
`_tickets/.agents/lessons`; der letzte Sammelstand umfasst 16 Lessons.
Die Originale bleiben deshalb Bestandteil dieses Repositorys.

**Doku-Abgleich:** `AGENTS.md` und `LESSONS-ACCESS.md` beschreiben den
vorhandenen Collector, seine Aufrufe und die Ablehnung relativer XDG-Pfade.
T-70 und STATUS verweisen auf das eigenständige AgentLessons-Projekt.
Board-README, Workflow und Lessons-Einstiege bleiben inhaltlich passend.
Produktanleitungen und Specs sind von der reinen Agenten-Dokumentation nicht
betroffen. Lokale Lessons und Produktcode bleiben unverändert.

Abschlussprüfung: 181 lokale Dateiverweise und Abschnittsanker in den
25 Markdown-Dateien des gesamten Branch-Diffs ohne Befund; 16 von 16
Archiv-Prüfsummen passend. `git diff --check` ist ohne Befund.
`agent-lessons --info` und `agent-lessons --resolve SI-CX-01 -p stockinfo`
prüfen den dokumentierten Lesezugriff. Produktcode ist im gesamten Branch-Diff
unverändert; deshalb wurden keine Produkttests erneut ausgeführt.
Es wird kein neuer unabhängiger Review behauptet; die folgenden Freigaben
gelten für ihre damaligen Fassungen.

Lessons-Einordnung: SI-R-02 begrenzt die Arbeit auf die tatsächlich genutzte
Quellenanbindung; SI-CX-01 verlangt aktuelle Nachweise statt alter Laufangaben.
Der veraltete Projektverweis und Collector-Text werden direkt korrigiert;
daraus wird kein zusätzliches Fehlermuster abgeleitet.

## Herkunft und technische Freigaben · 2026-09-11

**Freigabe:** Mike, 2026-09-11, im Codex-Chat von StockPortfolio:
„StockInfo-Anteil passt“. Die Aktivierung und Rollen stehen in [STATUS](../STATUS.md).

**Einzige fachliche Ticketquelle:**
[AgentLessons T-41](../../../../../DevKI/Production/AgentLessons/_tickets/30-doing/T-41-agentlessons-projektuebergreifend-sammeln.md).
Dort stehen vollständiger Umfang, Schemaentscheidung, Nachweise und Review.
Das Hauptticket entstand in StockPortfolio und wurde am 2026-09-11 nach
AgentLessons übertragen. Sein aktueller Zustand steht in
[AgentLessons STATUS](../../../../../DevKI/Production/AgentLessons/_tickets/STATUS.md).
Dieser Verweis enthält keine zweite Verify-Matrix oder kopierte Auftragsfassung.
StockInfo-Commits werden dort gesondert als Prüffassung genannt.

**Prüfergebnis:** Der StockInfo-Anteil `b498c66` ist durch `claude` im
[gemeinsamen Review Runde 1](../../../../../DevKI/Production/AgentLessons/_tickets/30-doing/T-41-agentlessons-projektuebergreifend-sammeln.md#review-runde-1--claude-2026-09-11)
technisch freigegeben. Die menschliche Abschlussabnahme war damals noch offen.

**Bearbeiteter Folgeauftrag:** Die Umbenennung und ID-Verweise aus
[R1-F2](../../../../../DevKI/Production/AgentLessons/_tickets/30-doing/T-41-agentlessons-projektuebergreifend-sammeln.md#folgeauftrag-r1-f2--sprechende-dateinamen--2026-09-11)
werden im selben Verweisticket geführt; das frühere Prüfergebnis bleibt erhalten.

**Runde 2:** Auch der Folgeauftrag `2165f64` ist durch `claude` im gemeinsamen
T-41-Review technisch freigegeben. Vollständiges Urteil im Hauptticket;
die damals noch offene lokale Abschlussabnahme ist oben dokumentiert.
