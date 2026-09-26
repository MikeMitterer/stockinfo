# T-76 · Anleitungen an den aktuellen API-Stand anpassen

README und Referenzen enthalten überholte API-Beispiele und widersprüchliche
Verfügbarkeitsangaben. Das Quote-Beispiel scheitert am aktuellen Modell:
`identity` fehlt, während `isin` auf oberster Ebene nicht mehr zulässig ist.
Die Anleitungen sollen den vorhandenen Stand korrekt erklären.

**Stand:** Bearbeitung durch Codex. Mike beauftragt „Dann aktualiere das“
und anschließend „Danach push + merge“. Die Integration ist damit beauftragt;
ein unabhängiges Review ist noch nicht erfolgt.

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

Für Mike steht derzeit kein weiterer Handgriff an. Merge und Push erfolgen
nach den technischen Prüfungen gemäß seinem Auftrag.

[↑ Übersicht](#übersicht)

## Prüfung

| # | Prüfung | Nachweis | AI |
|---|---|---|---|
| 1 | Antwortbeispiele gegen JSON und aktuelle Modelle | Ausstehend | ◑ |
| 2 | Referenzen gegen Vertrag, Routen und gezielte API-Tests | Ausstehend | ◑ |
| 3 | Relative Links, Abschnittsanker und Diff | Ausstehend | ◑ |
| 4 | Integration und Remote-Stand | Ausstehend | ◑ |

[↑ Übersicht](#übersicht)

## Doku-Abgleich und Lessons

Datei- und Überschrifteninventar erhoben; aktuelle Benutzer- und
Konsumentenanleitungen von historischen Specs, Plänen und Reviewberichten
getrennt. Die vier betroffenen Dateien enthalten die zusammenhängenden
Aussagen zu API-Beispielen, Identität, Details, Generation und Tests.

Lokale Codex-Lessons SI-CX-01, SI-R-02 und SI-T-66 gelesen (Bestand vom
2026-09-11). Gemeinsame Regel AL-R-02, Fassung 2026-09-11, berücksichtigt:
keine punktuelle Korrektur ohne Abgleich der anderen aktuellen Aussagen.
Der gemeinsame Bestand kennzeichnet die Regel weiterhin als `needs_review`.
Die Befunde sind eine weitere Dokumentationsausprägung des bekannten
Inventarproblems; kein neuer unabhängiger Lesson-Typ wird behauptet.
Prüfungen verwenden temporäre Datenbanken; kein neuer Migrations- oder
Kompatibilitätsaufwand. Keine globale Lessons-Änderung beauftragt.

[↑ Übersicht](#übersicht)
