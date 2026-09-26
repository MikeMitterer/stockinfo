# T-74 · Feldbeschreibungen der REST-API auf Englisch

`GET /fields` liefert deutsche `meaning`-Texte, auch bei `Accept-Language: en`.
Die technischen Beschreibungen sollen einheitlich Englisch sein. Beispiel:
`quote.price` erklärt den letzten bekannten Kurs künftig auf Englisch.

**Stand:** Umsetzung und gezielte Vertragsprüfung abgeschlossen. Mike hat die feste Sprache bestätigt:
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
| 1 | Alle Beschreibungen englisch, Aussagen erhalten | 61 Core- und 21 Plugin-Einträge vollständig übersetzt und gelesen; JSON-/AST-Vergleich bestätigt ausschließlich Text- und Versionsänderung | ➖ |
| 2 | Route liefert feste Sprache | Sechs API-Fälle: beide Quellen, jeweils ohne Sprachheader sowie mit `en` und `de`; vor der Änderung rot, danach grün | ✅ |
| 3 | Vertrag und Pflichtfelder bleiben konsistent | 120 Tests bestanden, 29 bestehende Auslassungen; Snapshot ohne Aktualisierungsmodus geprüft | ✅ |
| 4 | Doku und Cacheversion passen zur Änderung | Drei Anleitungen abgeglichen; Version 4.3.1, Snapshot unterscheidet sich nur in der Version | ✅ |

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

Prüfbefehl:

```bash
.venv/bin/python -m pytest tests/test_api_fields.py tests/test_contract.py tests/test_contract_openapi.py tests/test_contract_required_fields.py tests/test_open_details_flow.py -q
```

Der Lauf verwendet über `tests/conftest.py` frische temporäre Datenbanken.
Ergebnis: **120 passed, 29 skipped**, eine vorbestehende Starlette-Warnung
zur künftig entfallenden httpx-Unterstützung im TestClient. Keine vollständige
Backend-Suite und kein Deployment behauptet. Die Änderung betrifft nur
Beschreibungen; der gezielte Lauf deckt die Route und ihre Vertragskonsumenten ab.

`ruff check`, `ruff format --check` für beide Python-Dateien und
`git diff --check` bestanden. Vollständiges AST-Bezeichnerinventar geprüft:
englische Bezeichner, deutsche Testnamen als Projektausnahme. Der JSON-Vergleich
mit der Ausgangsfassung bestätigt unveränderte Schlüssel, Arten, Pflichtangaben
und sonstige Vertragsdaten. Der AST-Vergleich nach Austausch des Textkatalogs
bestätigt unveränderte Plugin-Logik; Ruff hat zusätzlich vorhandene Zeilen umbrochen.

## Standards und Übergabe

Gelesen: `/Users/macminipro/.codex/skills/code-standards/SKILL.md`,
Referenzen `python.md` und `documentation.md`. Feste englische technische
Vertragsbeschreibungen gemäß Mikes Auftrag; keine neue i18n-Infrastruktur.

| Referenz | Ergebnis |
|---|---|
| Architektur | ✅ vorhandene zwei fachliche Vertragsquellen erhalten; keine zweite Laufzeitliste |
| Shell / CLI | ➖ nicht berührt |
| Frontend | ➖ nicht berührt |
| Python | ✅ AST-Inventar, unveränderte Logik, Ruff-Prüfung |
| Persistenz | ➖ nicht geändert; Testdatenbanken bleiben isoliert |
| Qualität | ✅ sechs rote/grüne Sprachfälle und 120 erfolgreiche gezielte Tests |
| Dokumentation | ✅ REST-Referenz, Vertrags-README und Plugin-Anleitung nennen dieselbe Sprachregel |

Umfang: geplant/tatsächlich drei fachliche Änderungen, zwei Produktdateien
und fünf Test-/Dokudateien. Ticket und Status enthalten ausschließlich Auftrag,
Nachweise und Übergabe. Keine neuen Abhängigkeiten oder öffentlichen Strukturen.

Board-Konventionen: vorhandene Rollen und lokale Übergaberegeln verwendet,
Aktivitätsmeldungen über den globalen Helfer geschrieben. Der ältere lokale
Workflow dokumentiert die globale Übernahmefassung noch nicht; eine allgemeine
Board-Migration ist nicht Teil von T-74 und bleibt als gesonderter Auftrag offen.

Unabhängiger Review: **ausstehend**, zuständig ist Claude laut STATUS.
