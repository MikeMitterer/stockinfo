# T-64 · Handelsplätze im UI erklären und Plugin-Autoren prüfbar anbinden

T-30 liefert die Deklaration zusätzlicher MICs, den Aufnahmeweg und die
REST-Auskunft. Dieses Ticket ergänzt die Exchanges-Oberfläche und den
ausführbaren Nachweis für Plugin-Autoren. Noch nicht umgesetzt; aus dem
Scope-Checkpoint zu T-30 vom 2026-09-08 abgetrennt.

## Für dich

Mike hat die dynamische Exchanges-Seite am 2026-09-08 ausdrücklich beauftragt:
„UI berücksichtigst du auch“ und „Die Exchanges Seite muss entsprechend
dynamisch werden“. T-64 folgt unmittelbar nach dem laufenden T-30-Review,
vor T-21 #2g. T-30 ist freigegeben; STATUS.md führt jetzt T-64 als aktives Ticket. Aktuell kein weiterer Handgriff nötig.

## Umsetzung und technische Nachweise

Abhängigkeit: [T-30](T-30-plugin-boersenauskunft.md), dessen REST-Auskunft
die einzige Datenquelle der Oberfläche ist. Der
[Gesamtentwurf](../docs/superpowers/specs/2026-09-08-plugin-exchanges-design.md)
beschreibt das vereinbarte Verhalten.

- Exchanges zeigt MIC, Handelsplatz, Region und Unterstützung mit Quelle und
  Rolle. Nicht angegeben, inaktiv und bestandsabhängig bleiben unterscheidbar.
- App-Suffixe sind zusätzliche Information; Sammelcodes wie US stehen
  separat mit Mitgliedern. Keine Behauptung eines vollständigen ISO-Katalogs.
- Geerbte Autor-Vertragsprüfungen kontrollieren die neuen Deklarationen;
  ein ausführbares Beispiel demonstriert sie ohne Host-Interna.
- Tests für Quelle/Rolle und fehlende Deklaration sowie Browserlauf in DE/EN
  und schmalem Fenster. Kein eigenes Test-Subsystem.

| # | Nachweis | AI | Human |
|---|---|:--:|---|
| 1 | Exchanges verwendet ausschließlich REST und zeigt die neue MIC-Deklaration samt Rolle korrekt. | ➖ | |
| 2 | Fehlende oder nicht einsatzbereite Quelle erzeugt keine positive Unterstützungsmarkierung. | ➖ | |
| 3 | Sammelcode, Standardsymbol, Suche und schmales Fenster in DE/EN geprüft. | ➖ | |
| 4 | Autor-Harness erkennt ungültige Deklarationen; Beispiel und kopierbarer Prüfbefehl funktionieren. | ➖ | |

## Herkunft

Claude entschied am 2026-09-08 im Scope-Checkpoint zu `d0e6ad0`: `split`.
T-30 behält Plugin/Core/REST; UI, Browserlauf, Autor-Harness und Beispiel
werden separat geliefert. Der Split selbst änderte die Priorität nicht;
Mikes anschließender UI-Auftrag priorisiert T-64 direkt nach T-30.
