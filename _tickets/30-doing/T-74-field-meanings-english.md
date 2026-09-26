# T-74 · Feldbeschreibungen der REST-API auf Englisch

`GET /fields` liefert deutsche `meaning`-Texte, auch bei `Accept-Language: en`.
Die technischen Beschreibungen sollen einheitlich Englisch sein. Beispiel:
`quote.price` erklärt den letzten bekannten Kurs künftig auf Englisch.

**Stand:** Umsetzung, gezielte Vertragsprüfung und unabhängiger Review
abgeschlossen — **approved**, Claude, Runde 1, `fc0063e`. Mike hat die feste
Sprache bestätigt: „Passt - meaning auf Englisch“. Keine Befunde. Nur der
menschliche Abschluss (Verschieben nach `40-done/`) steht noch aus.

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
| 1 | Alle Beschreibungen englisch, Aussagen erhalten | 61 Core- und 21 Plugin-Einträge vollständig übersetzt und gelesen; JSON-/AST-Vergleich bestätigt ausschließlich Text- und Versionsänderung; vom Verifier mit eigenem Python-Strukturvergleich (Core) und eigenem AST-Bezeichnerinventar (Plugin) nachgerechnet, 0 verbliebene deutsche Zeichen | ✅ |
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

## Unabhängiger Review · Claude, Runde 1, 2026-09-26

**Ergebnis: approved.** Geprüft am eingefrorenen Stand `fc0063e`
(identisch mit `HEAD~1` zum Prüfzeitpunkt, kein weiterer Produktcommit).
Volles Ergebnis mit Belegen steht in
[STATUS](../STATUS.md#inbox--codex--t-74-runde-1--approved); hier nur die
Kurzfassung.

- Eigener Python-Strukturvergleich von `core-contract.json` gegen den
  Vorgänger (`meaning` und `core_version` maskiert): identisch, nur diese
  beiden Felder geändert. 61 Core- plus 21 Plugin-Einträge einzeln
  ausgezählt und auf verbliebene deutsche Sonderzeichen geprüft: 0 Treffer.
- Eigener AST-Vergleich von `app/contract.py` (String-Konstanten maskiert):
  identisch, keine Logikänderung. Eigenes Bezeichnerinventar über
  `ast.Name`/`ast.arg`/Funktions- und Klassennamen: 44 Bezeichner, keiner
  deutsch.
- Testbefehl aus diesem Ticket selbst erneut ausgeführt:
  **120 passed, 29 skipped**, deckungsgleich mit der Übergabe. `ruff check`,
  `ruff format --check` und `git diff --check` erneut grün.
- Drei Doku-Anpassungen inhaltlich gegen den tatsächlichen Response-Text
  geprüft, nicht nur auf Vorhandensein.
- Die feste, nicht sprachheader-abhängige `meaning`-Sprache ist Mikes
  ausdrückliche Entscheidung und fällt unter die Ausnahme für stabile
  technische Vertragsfelder ohne Endnutzer-Publikum — kein i18n-Befund.

Keine Befunde. Die im Ticket bereits selbst benannte offene Board-Konvention
(`AGENT-WORKFLOW.md` dokumentiert den Übernahmestand
`2026-09-11-lessons-follow-through` noch nicht, `STATUS.md` verlinkt
`ACTIVITY.md` nicht) bleibt außerhalb des T-74-Scope offen sichtbar; sie
blockiert diese Freigabe nicht.

Menschlicher Abschluss (Verschieben nach `40-done/`) steht noch aus.
