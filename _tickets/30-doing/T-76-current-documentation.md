# T-76 · Anleitungen an den aktuellen API-Stand anpassen

README und Referenzen enthalten überholte API-Beispiele und widersprüchliche
Verfügbarkeitsangaben. Das Quote-Beispiel scheitert am aktuellen Modell:
`identity` fehlt, während `isin` auf oberster Ebene nicht mehr zulässig ist.
Die Anleitungen sollen den vorhandenen Stand korrekt erklären.

**Stand:** Vier Anleitungen korrigiert, technisch geprüft und mit `d2f0827`
in `master` integriert sowie nach `origin/master` gepusht. Mike beauftragt
„Dann aktualiere das“ und anschließend „Danach push + merge“.
Der unterstützende Faktencheck
`docs_check` ist abgeschlossen; eine formale Freigabe durch Claude wird nicht
behauptet.

## Übersicht

- [Auftrag und Umfang](#auftrag-und-umfang)
- [Prüfung](#prüfung)
- [Doku-Abgleich und Lessons](#doku-abgleich-und-lessons)

## Auftrag und Umfang

Scope-Vertrag: aktuelle Antworten, Routen und Testbefehle im README korrigieren;
Identität, Detailfelder und verfügbare Generation-Auskunft in den Referenzen
konsistent erklären; Navigation und direkt betroffene Beispiele nachziehen.
Vier Dokudateien: `README.md`, `docs/rest-core-contract.md`,
`docs/plugin-authors.md`, `contract/README.md`. Keine Produkt- oder
Testcodeänderung, keine neue API-Zusage. Budget: vier Dokudateien und
Board-Nachweise, insgesamt höchstens 800 Diff-Zeilen. Historische Entwürfe
bleiben Historie. Keine Board-Migration im Rahmen dieses Doku-Auftrags.

Merge und Push sind gemäß Mikes Auftrag erledigt. Für die Ablage des Tickets
unter `40-done/` steht die gesonderte Abschlussbestätigung noch aus.

[↑ Übersicht](#übersicht)

## Prüfung

| # | Prüfung | Nachweis | AI |
|---|---|---|---|
| 1 | Antwortbeispiele gegen JSON und aktuelle Modelle | 5 JSON-Blöcke lesbar; Quote-, Fields- und Typkatalog-Beispiele gegen Pydantic-Modelle validiert | ✅ |
| 2 | Referenzen gegen Vertrag, Routen und gezielte API-Tests | 113 passed, 35 skipped; Inhalte gegen Code und Konfiguration gelesen | ✅ |
| 3 | Relative Links, Abschnittsanker und Diff | 117 lokale Links/Anker gültig; `git diff --check` sauber | ✅ |
| 4 | Integration und Remote-Stand | Fast-Forward nach `master`, Push erfolgreich; `HEAD` und `origin/master` auf `d2f0827`, Arbeitsbaum sauber | ✅ |

Prüfung #2: `.venv/bin/pytest tests/test_contract.py
tests/test_contract_openapi.py tests/test_api_fields.py
tests/test_api_instrument_types.py -q`. Die 35 Skips betreffen Prüfungen,
die auf die jeweilige positive/negative Fixture nicht zutreffen. Eine
Starlette/httpx-Abkündigungswarnung; keine Fehler. Kein Gesamttestlauf oder
Live-Nachweis externer Kursanbieter behauptet.

Nach dem Merge erneut dieselbe gezielte Suite ausgeführt: 113 passed,
35 skipped. Produktstand `d2f0827`; der anschließende Sitzungsnachtrag
betrifft nur Ticket, STATUS und ACTIVITY.

Unterstützender Faktencheck durch `docs_check`: Generation, Identität,
Testbefehle, Yahoo-Tageskurse und Pence-Ablehnung gegen Code gelesen. Ein
kleiner Befund zu `planned` korrigiert: Das Artefakt führt die bereits
vorhandene persistierte UUID noch im geplanten Gesamtprotokoll auf.

Zusätzlicher Auftrag von Mike: Docker-Hub-Verweis ins README aufnehmen und
die fehlende Beschreibung erklären. Link im Einstieg und Docker-Abschnitt
ergänzt. Öffentliche Hub-API am 2026-09-26: `description: ""`,
`full_description: null`, `is_automated: false`. `docker/build.sh` und
`pushImage2DockerHub` veröffentlichen nur Tags; keine README-Synchronisierung
eingerichtet. Automatische Übernahme bei Hub-Autobuilds gegen
[Docker-Dokumentation](https://docs.docker.com/docker-hub/repos/manage/information/#repository-overview)
geprüft. Keine Änderung der Docker-Hub-Metadaten beauftragt oder durchgeführt.

[↑ Übersicht](#übersicht)

## Doku-Abgleich und Lessons

Datei- und Überschrifteninventar erhoben; aktuelle Benutzer- und
Konsumentenanleitungen von historischen Specs, Plänen und Reviewberichten
getrennt. Die vier betroffenen Dateien enthalten die zusammenhängenden
Aussagen zu API-Beispielen, Identität, Details, Generation und Tests.

**Doku-Abgleich:** README: Version 1.1.0, Quellen, Routen, Identitätsbeispiel,
Konfiguration, Testumfang und Docker Hub aktualisiert. REST-Referenz:
Identitätsformen, verfügbare/geplante Generation, Detailfelder und Navigation
abgeglichen. Plugin-Anleitung: Generation-Grenze korrigiert. Vertrags-README:
Fixture-Nachweise von Laufzeitverhalten getrennt, Prüfbefehle und Navigation
nachgezogen. Budget eingehalten: vier Dokudateien, kein Produkt-/Testcode.

Zwei bestehende Abweichungen zwischen Code und Vertragsartefakt sind jetzt
sichtbar dokumentiert: Yahoo verwendet `auto_adjust=True`, der Daily-Adapter
gibt `adjusted` nicht weiter; Yahoo lehnt `GBp` über `currency_problem` ab.
Belege: `app/providers/yfinance_provider.py`, `app/plugins/yfinance_quotes.py`,
`app/plugin_adapters.py` und `plugin_api/src/stockinfo_plugin/invariants.py`.
Eine Änderung von Kursverhalten oder Vertragsartefakt gehört nicht zu diesem
Doku-Auftrag und bleibt einer gesonderten Entscheidung vorbehalten.

Lokale Codex-Lessons SI-CX-01, SI-R-02 und SI-T-66 gelesen (Bestand vom
2026-09-11). Gemeinsame Regel AL-R-02, Fassung 2026-09-11, berücksichtigt:
keine punktuelle Korrektur ohne Abgleich der anderen aktuellen Aussagen.
Der gemeinsame Bestand kennzeichnet die Regel weiterhin als `needs_review`.
Die Befunde sind eine weitere Dokumentationsausprägung des bekannten
Inventarproblems; kein neuer unabhängiger Lesson-Typ wird behauptet.
Prüfungen verwenden temporäre Datenbanken; kein neuer Migrations- oder
Kompatibilitätsaufwand. Keine globale Lessons-Änderung beauftragt.

[↑ Übersicht](#übersicht)
