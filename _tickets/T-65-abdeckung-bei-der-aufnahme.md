# T-65 · Abdeckung schon bei der Aufnahme prüfen

Die Exchanges-Seite zeigt seit dem T-21-Nachtrag die tatsächlich konfigurierte
Kursabdeckung. Die **Aufnahme eines Assets** kennt sie noch nicht: Ein
Wertpapier an einem Handelsplatz, für den keine aktive Kursquelle zuständig
ist, lässt sich weiterhin anlegen und liefert danach nie einen Kurs.

Dieses Ticket schließt die Lücke am öffentlichen Eingang. Dieselbe aktuelle,
nutzbare Abdeckung, die `/exchanges` ausweist, entscheidet auch darüber, ob
eine Aufnahme angenommen wird.

**Herkunft:** Von Mike am 2026-09-08 ausdrücklich beauftragt — „Ja dann
implementiere das - das gehört zur Vollständigen implementierung des Plugins
dazu". Der Umfang wurde von Mike in `2fae61a` innerhalb von T-21 festgelegt.
Der Scope-Checkpoint vom selben Tag hat ihn als eigenständig lieferbares
Ergebnis abgetrennt (`split`), weil er einen eigenen Nutzerweg bedient und
T-21 ohne ihn vollständig bleibt.

## Für dich

Aktuell ist **keine zusätzliche Prüfung durch dich** angesetzt.

Du hast das Ticket am 2026-09-08 in die Kette aufgenommen. Es steht **hinter
T-21**: Es liest die dort validierte Deklaration, also muss diese zuerst
stehen und geprüft sein. Die jeweils laufende Arbeit steht in
[STATUS.md](STATUS.md).

Ein Rest aus der Abtrennung: Der Umfangsabschnitt steht noch in
`T-21-identitaet-mic-und-ticker.md`, weil dort unfertige Änderungen im
Worktree liegen. Er wird beim nächsten T-21-Anfassen durch einen Verweis auf
dieses Ticket ersetzt.

## Scope-Vertrag · 2026-09-08

**Ergebnis:** Eine Aufnahme über `/instruments/intake` wird abgelehnt, wenn
für den Handelsplatz keine aktive, nutzbare Kursquelle zuständig ist — mit
verständlicher Begründung in DE und EN, ohne Kursabfrage und ohne
Datenbankzeile.

Zwei fachliche Änderungen:

1. Die Aufnahme prüft dieselbe aktuelle, nutzbare Kursabdeckung wie
   `/exchanges` — bei Symbolen **vor** der Quellenabfrage, bei ISIN **nach**
   der Auflösung und **vor** Kursabfrage und Speicherung.
2. Strukturierte Ablehnung mit verständlichem DE/EN-Text.

**Nicht-Ziele.** Keine MIC-Prüfung für Paar- und ISIN-only-Identitäten. Eine
fehlende oder ungültige Deklaration verspricht keine Abdeckung. Die normale
Prüfung des konkreten Wertpapiers bleibt notwendig — Abdeckung der Börse ist
keine Zusage für den einzelnen Titel. Bestehende Kurs-Lesewege und der Refresh
werden nicht umgebaut. Kein neuer Endpunkt, kein Schema, kein Plugin-Hook,
kein Konfigurationsformat, kein Datenbankumbau. Die Abdeckung wird aus der
bestehenden validierten Deklaration gelesen; es entsteht **keine zweite
MIC-Liste**.

**Mitzuziehen:** Die UI verwendet für das Hinzufügen bisher den Kurs-GET statt
des Aufnahme-POST. Diese Umstellung gehört zum Ergebnis, einschließlich der
bestehenden Paar- und Quellenfehlerfälle.

**Budget:** höchstens **10 Produktdateien** (`exchange_catalog`, `container`,
`intake_service`, `quote_cache`, `quote_service`, Aufnahme- und Kursrouter,
`useInstrumentActions`, DE/EN), **6 Test-/Dokudateien** (Profiltests,
Aufnahme-Regressionen, UI-Aktionen und Fehlertexte, Autorenanleitung, Ticket)
und **700 manuelle Diff-Zeilen**.

## Akzeptanz am öffentlichen Eingang

Jeweils mit frischer Testdatenbank, alle an `/instruments/intake`:

- Ein abgedecktes Listing ist aufnehmbar.
- Ein bekannter, unversorgter MIC wird abgelehnt — **ohne** Kursabfrage und
  **ohne** Datenbankzeile.
- Alias und MIC verhalten sich gleich.
- Eine ISIN kann die Prüfung nicht umgehen.
- Eine YAML-Ergänzung oder -Entfernung wirkt beim nächsten Request.
- Online mit Fallback und reines YAML stimmen mit `/exchanges` überein.
- Metadaten allein erlauben keine Aufnahme; defekte oder fehlende Zusagen
  ebenfalls nicht.
- BTC-EUR bleibt aufnehmbar.

Je neuem Unterschied läuft eine Akzeptanzprobe **zuerst rot**, danach die
grüne Gegenprobe. Anschließend unabhängiges Review.

**UI-Nachweise** (von Mike ausdrücklich verlangt): DE und EN zeigen den MIC
und einen verständlichen Grund. Browserläufe in beiden Profilen prüfen Erfolg,
Ablehnung und die **unveränderte Asset-Liste nach einer Ablehnung**.

| # | Nachweis | AI |
|---|---|:--:|
| intake-coverage | Aufnahme und REST-Abdeckung stimmen in beiden Profilen überein; keine Speicherung bei Ablehnung. | ➖ |
| intake-coverage-ui | Die Aufnahme zeigt den Abdeckungsfehler in DE und EN verständlich. | ➖ |
