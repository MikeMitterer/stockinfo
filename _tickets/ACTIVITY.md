# Aktuelle Tätigkeit

- 2026-09-26 18:23:38 CEST · codex · hat auf Mikes Klarstellung die doppelten Unraid-Infos entfernt und die gemeinsame Skill-Regel korrigiert. READMEs verlinken nur die zentrale Unraid-Anleitung; korrigierter Stand zur Prüfung übergeben.
- 2026-09-26 18:20:45 CEST · codex · hat den neuen unraid-conventions-Skill abgeglichen und die Installationskurzfassung im Root-README ergänzt. Nachtrag f6abd45 ist zur unabhängigen Prüfung über STATUS.md übergeben.
- 2026-09-26 18:11:59 CEST · codex · hat T-78 umgesetzt und die Unraid-Anleitung samt README-Verweisen geprüft. Die Prüffassung 68702c6 ist über STATUS.md an Claude übergeben.
- 2026-09-26 18:08:50 CEST · codex · lagert die Unraid-Anleitung nach dem StockPortfolio-Vorbild aus und gleicht Port, Datenpfad und Einstellungen mit dem StockInfo-Template ab.
- 2026-09-26 17:47:31 CEST · codex · hat StockInfo und ProjectTools nach master integriert und gepusht. Die neue Docker-Hub-Beschreibung ist veröffentlicht und zurückgelesen; T-76 und T-77 werden abgeschlossen.
- 2026-09-26 13:58:52 CEST · claude · T-77 Runde 2 approved (efeab04/a1908f7: Docker-Hub-Beschreibung + 403-Diagnose); Formalbefund: uncommitteter AGENTS.md/Ticket-Nachtrag lag außerhalb des Prüfstands, gesichert und wiederhergestellt, nicht mitgeprüft
- 2026-09-26 · codex · T-77: Eigene docker/README.md mit GitHub-Link, Container-Anleitung und Repo-Bildern; Uploader nutzt diese Quelle. 47 Tests grün, Vorschau 6.232 Bytes. Token-Anpassung hat laut Mike den Live-403 behoben.
- 2026-09-26 13:27:46 CEST · claude · T-77 Runde 1 unabhängig geprüft: approved, ein Whitespace-Fund selbst geheilt (535e7a7); Zustand auf portfolio_review an Mike
- 2026-09-26 · codex · T-77: Defaults master und docker/preview/README.md, automatische Docker-Hub-Zielermittlung fertig; 43 Tests grün, reale Vorschau 24.929 Bytes. Erneute Übergabe über STATUS.md.
- 2026-09-26 12:58:06 CEST · codex · T-77: CLI-Gestaltung nach Mikes Befund korrigiert; BashLib-Farben, ausgerichtete Optionen und Beispiele im echten Pseudoterminal geprüft. 34 gezielte Tests grün; abschließende Review-Übergabe wird vorbereitet.
- 2026-09-26 12:49:18 CEST · codex · T-77 ergänzt: Bash-Einstieg mit eigener Cache-venv, Eingabe-/Credential-Prüfungen und Requirements-Datei; ProjectTools 3005e11. 30 gezielte Tests grün, Projekt-venv unverändert. Beide Skills und T-77 aktualisiert; erneute Übergabe an Claude vorbereitet.
- 2026-09-26 12:34:48 CEST · claude · Claude-Durchlauf: Übergabe für T-77 Runde 1 wurde vor meinem Claim zurückgenommen (Bash-Einstieg-Fix nötig); owner wieder codex, kein Review, nichts geändert
- 2026-09-26 12:28:41 CEST · codex · T-77: Gemeinsamer Docker-Hub-README-Upload in ProjectTools 3c4e025; StockInfo-Push angebunden, Größenregel und Makefile-Skill ergänzt. 17 gezielte Tests bestanden; bereite Claudes Review über STATUS.md vor.
- 2026-09-26 12:28:21 CEST · claude · prüft Rollenzuordnung: codex arbeitet an T-77 (codex_working), kein Review fällig; startet Board-Loop als Verifier
- 2026-09-26 12:07:57 CEST · codex · T-77: Lokales README-Upload-Script mit Linkkonvertierung und Make-Targets beauftragt; GitHub-Automatisierung entfällt.
- 2026-09-26 11:55:09 CEST · codex · T-76: Dokumentation mit d2f0827 in master integriert und gepusht. Docker-Hub-Beschreibung und automatische Synchronisierung sind unverändert; Funktionsweise erklärt.
- 2026-09-26 11:53:54 CEST · codex · T-76: Vier Anleitungen korrigiert, 113 gezielte Tests bestanden, 35 Fixture-Skips. Beispiele und 117 lokale Links geprüft; Docker-Hub-Link und Erklärung ergänzt.
- 2026-09-26 11:44:32 CEST · codex · T-76: README und API-Referenzen werden an den aktuellen Code angeglichen; anschließend sind Merge und Push beauftragt.
- 2026-09-26 11:26:30 CEST · claude · T-75 auf Mikes Bestätigung nach 40-done verschoben. 20-ready/ und 30-doing/ sind wieder leer, keine Kette eingeplant.
- 2026-09-26 11:25:15 CEST · claude · T-75 unabhängig geprüft: approved, Runde 1, fc67ea3. Eigene Rot/Grün-Gegenprobe, 3/378 Tests, TS-Compiler-Inventar und live selbst reproduzierter HTTP-Aufruf auf Port 5173. Letztes Kettenglied, phase: portfolio_review, owner: mike.
- 2026-09-26 11:22:00 CEST · claude · T-74 und T-73 auf Mikes Bestätigung nach 40-done verschoben. Beginne jetzt die Prüfung von T-75 (Runde 1, fc67ea3).
- 2026-09-26 11:15:26 CEST · codex · T-75: Swagger-Aufruf über Port 5173 liefert jetzt echte JSON-Typen. 378 Dashboard-Tests bestanden; Korrektur fc67ea3 über STATUS.md zur Prüfung vorbereitet.
- 2026-09-26 11:00:53 CEST · claude · T-73 unabhängig geprüft: approved, Runde 1, a559c09. Eigener Testlauf (15 gezielt, 1236/35/2 gesamt) und Struktur-/AST-Vergleich bestätigen den Coder-Bericht; zwei Ausfälle datumsbedingt in unberührter Datei. Letztes Kettenglied erreicht, phase: portfolio_review, owner: mike.
- 2026-09-26 10:30:58 CEST · codex · T-73 umgesetzt: GET /instrument-types, Core 4.4.0 und HTTP-Fixtures. 144 gezielte Tests grün; übergebe Claude über STATUS.md mit zwei nachgewiesenen Altbefunden.
- 2026-09-26 10:17:03 CEST · codex · T-73 aktiv: Implementiere die dynamische REST-Auskunft der Plugin-Assettypen. T-74 ist von Claude freigegeben.
- 2026-09-26 10:08:37 CEST · claude · T-74 unabhängig geprüft: approved, Runde 1, fc0063e. Keine Befunde; offene ACTIVITY/Workflow-Konvention als nicht blockierender Hinweis vermerkt. Owner geht an codex zurück, nächstes Kettenglied T-73.
- 2026-09-26 10:00:54 CEST · codex · T-74: 82 englische Feldbeschreibungen umgesetzt, 120 gezielte Tests bestanden. Bereite den Review vor; T-73 ist auf Mikes Auftrag nach Doing verschoben.
- 2026-09-26 09:55:34 CEST · codex · T-73: Übersetze die 82 Feldbeschreibungen ins Englische und prüfe den API-Vertrag.
- 2026-09-25 14:20:38 CEST · codex · T-72 als Backlog-Ticket angelegt: Vitest 5, npm-Audit, Dashboard-Tests und Makefile-Docker-Build als Prüfkriterien. T-71 und STATUS unverändert.
- 2026-09-25 14:18:13 CEST · codex · Erstellt auf Mikes Auftrag ein Backlog-Ticket für das Dashboard-Upgrade auf Vitest 5; T-71 und seine Review-Übergabe bleiben unverändert.

Nur zur Information für den Nutzer; Rollen und Aufträge stehen in [STATUS.md](STATUS.md).
