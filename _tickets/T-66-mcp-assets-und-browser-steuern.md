# T-66 · Assets und Charts über eine KI bedienen

StockInfo soll sich **aus dem KI-Chat bedienen** lassen: Assets hinzufügen,
ändern und löschen sowie deren Charts öffnen und schließen.

Dafür erhält StockInfo einen eigenständigen MCP-Server im Unterordner
**`mcp/`**. MCP stellt der KI benannte Werkzeuge bereit. Der Server übersetzt
deren Aufrufe in StockInfo-REST-Aufrufe; die Geschäftsregeln bleiben in StockInfo.

**Beispiel:** Du beauftragst die KI, ein eindeutig bestimmtes Asset aufzunehmen
und seinen Chart anzuzeigen. Falls noch keine Ansicht verbunden ist, öffnet
das System eine Browseransicht. Nach der Aufnahme erscheint das Asset im UI,
anschließend sein Chart. Ein weiterer Auftrag schließt den Chart wieder.

**Stand:** Konzept festgehalten, **von Mike am 2026-09-08 freigegeben und in
die Kette aufgenommen**. Es gibt weder eine Umsetzung noch technische
Prüfnachweise. Der nächste Schritt ist der Zuschnitt, nicht der erste Produktedit.

## Für dich

**Deine Freigabe zur Umsetzung liegt vor** („Du kannst die loop nochmal starten
und T-66 durchgehen"). Ein Termin ist nicht gesetzt.

Als Nächstes erstellt der Coder Datei-Inventar und Scope-Vertrag und schlägt
dir gegebenenfalls eine Zerlegung in einzeln prüfbare Teiltickets vor. Erst
danach entsteht Code. Bis zu deiner Bedienabnahme sind von dir keine
Handgriffe nötig.

Zwei Punkte werden dich voraussichtlich noch erreichen, weil sie
Produktentscheidungen sind und nicht vom Coder allein getroffen werden:
die **Sprachwahl** für `mcp/` (TypeScript ist bisher nur ein Vorschlag) und
der konkrete **Launcher- und Authentisierungsweg** für den Browserstart.

Die technische Verifikation übernimmt der in [STATUS.md](STATUS.md) unter
`reviewer` benannte Verifier. Eine technische Freigabe ersetzt deine
abschließende Bedienabnahme nicht.

## Was danach möglich sein soll

- **Assets lesen und eindeutig auswählen.**  
  Die KI kann vorhandene Assets finden und deren Zustand lesen.
  Mehrdeutige Symbole dürfen nicht zur Änderung des falschen Assets führen.

- **Assets hinzufügen, ändern und löschen.**  
  Die Werkzeuge verwenden die bestehenden Aufnahme- und Bearbeitungsregeln.
  „Ändern“ meint die von StockInfo zur Bearbeitung freigegebenen Felder,
  einschließlich manueller Detailwerte; keine beliebigen Providerdaten.

- **Eine Browseransicht starten und zuordnen.**  
  Die KI kann das Öffnen selbst auslösen. Erst die Rückmeldung der geladenen
  Seite bestätigt eine verbundene Sitzung. Ein gestarteter Browserprozess
  allein ist noch kein Erfolg.

- **Charts gezielt öffnen und schließen.**  
  Ein Chart-Auftrag nennt Asset, gegebenenfalls Zeitraum und Zielansicht.
  „Chart schließen“ schließt den Chart, nicht den Browser oder das Asset.
  Andere Tabs oder Geräte werden dadurch nicht umgeschaltet.

- **Deine Oberfläche aktuell halten.**  
  Änderungen durch KI, dich oder den Hintergrund-Refresh werden nach
  erfolgreichem Speichern an die betroffenen Ansichten gemeldet.
  Offene, ungespeicherte Eingaben dürfen dabei nicht still überschrieben werden.

## Architektur und Grenzen

### Eigenständiges Subprojekt im selben Repository

`mcp/` erhält eigene Abhängigkeiten, Tests, Startanweisungen und Konfiguration.
Der Dienst ist unabhängig vom Python-Backend startbar und deploybar.
Die StockInfo-Adresse wird konfiguriert, nicht auf die Workstation festgelegt.

Der MCP-Server wird **nicht in FastAPI eingebettet**. Er importiert keine
Python-Interna und greift nicht auf die StockInfo-Datenbank zu. Sämtliche
StockInfo-REST-Zugriffe werden beispielsweise in `mcp/src/clients/stockinfo/`
gebündelt; Werkzeugdefinitionen liegen getrennt davon unter `mcp/src/tools/`.

TypeScript ist der bisherige **Vorschlag**, keine getroffene Sprachentscheidung.
Die konkrete Bibliothek und Transportkonfiguration werden beim Scope-Zuschnitt
festgelegt. Für einen entfernten MCP-Zugang ist Streamable HTTP vorgesehen.

### StockInfo bietet eine allgemeine UI-Steuerung

Zusätzlich zu den Datenrouten benötigt StockInfo einen Vertrag für
Browser-Sitzungen, UI-Befehle und Ausführungsbestätigungen.
Diese Schnittstelle kennt keine MCP-Werkzeuge und ist auch für andere
Automationen nutzbar.

Vorgeschlagener Ablauf: MCP sendet einen UI-Auftrag über REST an StockInfo.
StockInfo übermittelt ihn per **SSE** an die Zielansicht. SSE ist ein
Ereigniskanal vom Server zum Browser; der Browser bestätigt über REST.
WebSockets sind dafür keine Voraussetzung.

Auftragskennungen ordnen Bestätigungen zu. „Angenommen“, „ausgeführt“,
„fehlgeschlagen“ und „Zeitüberschreitung“ müssen unterscheidbar sein.
Nach einer Wiederverbindung lädt die Ansicht den aktuellen Datenstand;
alte UI-Befehle dürfen nicht unkontrolliert erneut ausgeführt werden.

### Browserstart erfolgt auf dem Benutzergerät

Bei lokalem MCP-Betrieb kann der Dienst den Browser auf demselben Rechner öffnen.
Bei Serverbetrieb braucht es einen **lokalen Launcher** oder eine nachgewiesene
gleichwertige Fähigkeit der KI-Anwendung. Ein auf dem Server gestarteter Browser
erfüllt diese Anforderung nicht.

Die Ansicht verbindet sich über eine kurzlebige, einmal verwendbare Kennung
mit der zugehörigen Steuerungssitzung. Fremde Sitzungen dürfen weder übernommen
noch gesteuert werden. Fehlt der lokale Startweg, meldet das Werkzeug diesen
Zustand verständlich; es behauptet keinen erfolgreichen Browserstart.

Die konkrete Launcher-Ausführung sowie Authentisierung und Sitzungsbindung
werden vor dem Produktedit festgelegt. Lokaler Betrieb und interner
Serverbetrieb müssen als getrennte Prüfläufe nachgewiesen werden.

## Umfang vor dem ersten Produktedit zuschneiden

Dieses Ticket hält den Gesamtumfang fest. **Mikes OK liegt vor** — der Coder
erstellt jetzt das Datei-Inventar und einen Scope-Vertrag mit Budget nach dem
[Board-Vertrag](README.md#scope-vertrag-für-implementierungstickets).
Falls nötig, wird die Umsetzung in verlinkte, einzeln prüfbare Teiltickets zerlegt.

Die Schätzung unten liegt um ein Vielfaches über den zuletzt gelieferten
Tickets. Ein einzelner Scope-Vertrag über den ganzen Umfang würde sowohl den
Breitenalarm des Vertical-Acceptance-Riegels als auch jedes bisher übliche
Diff-Budget reißen. Eine Zerlegung ist deshalb der erwartete Fall, nicht die
Ausnahme — und sie gehört vor den ersten Produktedit.

Betroffen sind `mcp/`, die benötigten REST-/Ereignis-Schnittstellen im Backend,
die Sitzungs- und Chart-Steuerung im Dashboard sowie der lokale Startweg.
Bestehende REST-Verträge und manuelle Bedienung müssen weiter funktionieren.

**Nicht enthalten:** Restore, Migration, eine allgemeine Browserautomation mit
simulierten Klicks, ein Umbau der Geschäftslogik oder eine umfassende neue
Benutzerverwaltung. Bestehende Betriebsriegel dürfen durch MCP nicht umgangen
werden. Zugriffsschutz für die neuen Schnittstellen gehört zum Umfang.

Die bisherige Schätzung beträgt **6–10 Entwicklertage** für den beschriebenen
Umfang einschließlich einfachem macOS-Launcher und Tests. Sie ist eine grobe
Planungsannahme, kein zugesagtes Budget; der Scope-Vertrag präzisiert sie.

## Technische Verifikation

Die folgende Tabelle ist die **einzige aktuelle Verify-Matrix**.
Alle Ergebnisse sind offen. `➖` bedeutet hier: noch nicht geprüft.

Die späteren Läufe verwenden isolierte Testdaten. **L** bezeichnet lokalen
Betrieb auf macOS; **S** StockInfo und MCP auf einem internen Server mit Browser
und Startweg auf dem Benutzergerät. Konkrete Test-Assets, URLs, Startbefehle und
Prüfbelege ergänzt der Coder bei der Umsetzung unter derselben Prüfnummer.

| # | Lauf | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|---|:--:|
| 1 | L, S | MCP separat starten und StockInfo-Adresse konfigurieren. | Verbindet sich über REST; keine DB-Zugriffe oder Python-Imports. | ➖ |
| 2 | L, S | Asset suchen und aufnehmen; mehrdeutige Eingabe versuchen. | Eindeutiges Asset erscheint; Mehrdeutigkeit erzeugt keine falsche Aufnahme. | ➖ |
| 3 | L, S | Manuellen Detailwert ändern, dann Test-Asset löschen. | Bestehende Fachregeln gelten; UI zeigt gespeicherten Stand bzw. Entfernung. | ➖ |
| 4 | L, S | Ohne verbundene Ansicht den Browserstart anfordern. | Browser öffnet auf dem Benutzergerät; Sitzung meldet Bereitschaft zurück. | ➖ |
| 5 | L, S | Zwei Ansichten öffnen; Chart in einer öffnen und schließen. | Nur die Zielansicht reagiert; Ausführung wird korrekt bestätigt. | ➖ |
| 6 | L, S | KI-, UI- und Hintergrundänderungen auslösen; parallel Eingabe offenhalten. | Ansichten aktualisieren sich; ungespeicherte Eingabe bleibt geschützt. | ➖ |
| 7 | L, S | Verbindung trennen, Auftrag senden, danach neu verbinden. | Ausfall oder Timeout sichtbar; Datenabgleich, keine blinde Befehlswiederholung. | ➖ |
| 8 | L, S | Fremde Sitzung oder verbrauchte Verbindungskennung verwenden. | Zugriff wird abgewiesen; keine fremde Ansicht wird gesteuert. | ➖ |
| 9 | L, S | REST und manuelle Asset-/Chart-Bedienung ohne MCP verwenden. | Bisherige Bedienwege funktionieren weiterhin. | ➖ |

Vor der Bedienabnahme erhält Mike oben einen kurzen Arbeitsbereich mit den
konkreten Handgriffen und Verweisen auf diese Prüfnummern. Human-Urteile werden
nicht vorweggenommen. Review-Fassung, Befunde und Auflösung werden erst nach
den jeweiligen Prüfungen ergänzt.
