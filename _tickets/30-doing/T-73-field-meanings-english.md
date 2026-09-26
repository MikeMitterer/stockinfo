# T-73 · Feldbeschreibungen der REST-API auf Englisch

`GET /fields` liefert deutsche `meaning`-Texte, auch bei `Accept-Language: en`.
Die technischen Beschreibungen sollen einheitlich Englisch sein. Beispiel:
`quote.price` erklärt den letzten bekannten Kurs künftig auf Englisch.

**Stand:** Umsetzung läuft. Mike hat die feste Sprache bestätigt:
„Passt - meaning auf Englisch“. Aktuell ist kein weiterer Handgriff nötig.
Unabhängiger Review und menschlicher Abschluss stehen noch aus.

## Scope-Vertrag

1. Alle 61 Core- und 21 Plugin-Beschreibungen übersetzen, fachliche Aussagen erhalten.
2. Vertragsversion von 4.3.0 auf 4.3.1 erhöhen, damit gecachte Kataloge erneuert werden.
3. Englisch als feste Sprache für `meaning` dokumentieren und über die Route prüfen.

Produktdateien: `contract/core-contract.json`, `app/contract.py`.
Begleitdateien: OpenAPI-Snapshot, `tests/test_api_fields.py`,
`docs/rest-core-contract.md`, `contract/README.md`, `docs/plugin-authors.md`.
Budget: 2 Produktdateien, 5 Test-/Dokudateien, insgesamt höchstens 500 Diff-Zeilen
einschließlich Ticket und Status. Keine neuen Felder, Sprachparameter,
Abhängigkeiten oder Änderungen an Kursdaten und UI-Übersetzungen.

## Verify-Matrix

| # | Prüfung | Nachweis | AI |
|---|---|---|---|
| 1 | Alle Beschreibungen englisch, Aussagen erhalten | Vollständiger Vergleich der 82 Einträge steht aus | ◑ |
| 2 | Route liefert feste Sprache | API-Test mit fehlendem, deutschem und englischem Sprachheader steht aus | ◑ |
| 3 | Vertrag und Pflichtfelder bleiben konsistent | Vertrags- und Routentests stehen aus | ◑ |
| 4 | Doku und Cacheversion passen zur Änderung | Inhaltsabgleich und Snapshotprüfung stehen aus | ◑ |

## Nachweise und Einordnung

Ausgangsbefund: lokale API-Probe mit temporärer Testdatenbank, Status 200,
61 Core- und 21 Plugin-Einträge; englischer Sprachheader lieferte deutsche Texte.
Die bisherigen fünf Routentests bestanden ohne Sprachprüfung.

Lessons gelesen: SI-CX-01, SI-R-02, SI-T-66 (lokale Fassung mit
`captured_at: 2026-09-11`). Temporäre Testdatenbanken, begrenzter Umfang,
keine Behauptung eines Deployments. AL-R-02 (`needs_review`, Fassung vom
2026-09-11) als zusätzliche Inventarhilfe: alle Einträge zählen und vergleichen.
Der Sprachbefund ist ein begrenzter Einzelfall; keine neue globale Lesson abgeleitet.

**Doku-Abgleich:** Datei- und Überschrifteninventar geprüft. Betroffen sind die
Auskunft zu `/fields` in der REST-Referenz, der Vertrags-README und der
Plugin-Autorenanleitung. Haupt-README und historische Entwürfe brauchen für
diese Textänderung keine Anpassung.
