---
schema_version: 1
id: SI-R-01
project: stockinfo
kind: case
discovery_phase: human_feedback
affected_work:
- review
subject_author: claude
discovered_by: mike
recorded_by: unknown
structured_by: codex
prevention_roles:
- implementer
- reviewer
provenance:
  project: stockinfo
  file: _tickets/.agents/CLAUDE-LESSONS.md
  heading: R-01 · Integrationsaufwand verdrängt die fachliche Architekturentscheidung
  revision: 5fc549b84ae7d449780b856d3046230da6c5bf2d
  file_sha256: f506fd721ef98bf9c51bff326b06c22a39c24eee57f14daa4e0e93f06bd78dff
  section_sha256: 326b58a95cb8ed962f21950544b540dc3e482e515560d5026a9c2c34622040ae
  captured_at: '2026-09-11'
---

# SI-R-01 · Integrationsaufwand verdrängt die fachliche Architekturentscheidung

**Implementer-Regel:** Befund, tatsächlichen Aufrufweg und Nutzerauswirkung getrennt prüfen.

**Verifier-Prüfung:** Die behauptete Wirkung am realen Aufrufweg belegen; begrenzte Alternativen gleich bewerten.

## Originalbelege und Einordnung

**Einzelfall-Lehre auf ausdrücklichen Auftrag von Mike, 2026-09-08.**
Hier wird kein zweiter Vorfall und kein statistisch wiederkehrendes Muster
behauptet. Untersucht ist Claude als Verifier von T-66; Codex hat die
Fehlgewichtung zunächst übernommen. Die Regel gilt für beide Rollen.

**Erkennungsregel:** Ein korrekter lokaler Befund — ein bestehender Guard
erfasst einen neuen Transport nicht — wird zum ausschlaggebenden Argument
gegen diesen Transport, bevor Nachrichtenwirkung, tatsächlicher Schaden und
der notwendige Integrationsschritt getrennt bewertet sind. „Noch nicht
abgesichert“ wird wie „technisch ungeeignet“ behandelt.

**Beleg:** T-66 Konzept Runde 1, Prüfstand `eb628f9`, Review `a2193e7`.
Claude priorisierte SSE, weil `migration_guard` als HTTP-Middleware keinen
WebSocket-Handshake prüft. Der Befund stimmt. Seine Gewichtung war zu hoch:
Die geplanten Nachrichten steuern das UI; Datenmutationen bleiben REST.
Der existierende Chartweg lautet `AppDashboard.select` → `loadChart` →
`useHistory.load`/`useDaily.load` → `apiClient.get`, ebenfalls HTTP.
Bei aktiver Migration bleibt die Datenanfrage gesperrt. Ein dennoch geöffnetes
Chart-Dock ist ein UI-Zustandsproblem, kein dadurch belegter ungeschützter
Datenzugriff. Der Migrationsriegel ist außerdem eine Betriebssperre, kein
Nachweis einer umgangenen Authentisierung. Eine reale Bindungs-/Zugriffslücke
wäre separat zu prüfen und dürfte nicht bagatellisiert werden.

**Wie die Fehlgewichtung entstand:** Die überprüfte Middleware-Eigenschaft
wurde mit einer ungeprüften Aussage über ihre Folgen verbunden. Der Review
stellte Bypass oder doppelte Prüfung in den Vordergrund und behandelte den
ebenfalls möglichen zentralen ASGI-Umbau vor allem als Kostenargument. Damit
dominierte die Wiederverwendung eines Hilfsmechanismus die Passung zum
eigentlichen Ablauf: wenige Serverbefehle, UI-Aktion oder REST-Anfrage und
Rückmeldung. Die bidirektionale Verbindung und der zusätzliche Bindungsaufwand
bei getrenntem SSE-/REST-Rückkanal wurden nicht gleichgewichtig bewertet.

**Codex-Anteil:** Codex prüfte die HTTP-Middleware, übernahm die Schlussfolgerung
aber ohne eigene Folgenbewertung und konsolidierte zunächst SSE in `26590c8`.
Nach Mikes Einwand wurde WebSocket mit gemeinsamer ASGI-Absicherung empfohlen
(`e4b793e`). Claude zog in Runde 2 die SSE-Empfehlung mit genau diesem
Wirkungsabgleich zurück (`e5e0b20`). Es waren zwei Runden, keine weitere nötig.

**Gegenprüfung vor einem Architekturveto:**

1. Nachricht bis zur Wirkung verfolgen: reiner UI-Zustand, Lesen oder Schreiben;
   welche vorhandene Grenze erreicht der Folgeaufruf tatsächlich?
2. Den Auslöser und konkreten unerwünschten Effekt nennen. Ein nicht erfasster
   Transport allein beweist weder Datenzugriff noch Datenverlust.
3. Fachliche Eignung, Schutzanforderung und einmaligen Integrationsaufwand
   getrennt bewerten. Eine gemeinsame Erweiterung erhält DRY; nur die Kopie
   derselben Regel wäre ein Duplikat.
4. Beide Varianten nach denselben Kriterien vergleichen: Nachrichtenrichtungen,
   Bindung, Bestätigung, Fehlerbehandlung und Betrieb. „Passt zum bisherigen
   Guard“ ist ein Kostenpunkt, kein pauschales Architekturveto.
5. Ein Vetobefund nennt, was trotz eines angemessenen zentralen Integrationsfixes
   technisch schlechter oder unzulässig bliebe. Gibt es das nicht, ist der Fix
   Umsetzungsumfang; die Entscheidung folgt dem Nutzerablauf und seinen Vorgaben.

Keine neue Prozessschicht, keine zusätzlichen Reviewrunden: Diese fünf Fragen
werden bei der Gewichtung eines konkreten Befunds beantwortet. Sie sind kein
Grund, hypothetische Risiken oder weitere Sicherheitsarchitektur zu erfinden.
