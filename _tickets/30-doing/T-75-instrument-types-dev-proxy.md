# T-75 · Typkatalog aus Swagger über den Dev-Proxy abrufen

Mikes `GET http://localhost:5173/instrument-types` liefert die SPA-HTML-Seite.
Der Backend-Aufruf auf Port 8000 liefert die Typen korrekt. Ursache ist der
fehlende Eintrag in `dashboard/api-prefixes.ts`; der bestehende Proxy-Test
prüft nur UI-Aufrufe und erfasst Swagger-Aufrufe deshalb nicht.

**Stand:** Nacharbeit läuft. Kein weiterer Handgriff erforderlich;
Review über STATUS.md und menschlicher Abschluss stehen aus.

## Scope und Prüfung

Eine Produktdatei (`dashboard/api-prefixes.ts`), eine Testdatei
(`dashboard/tests/viteProxy.spec.ts`), höchstens 150 Diff-Zeilen einschließlich
Board. Fehlendes Präfix ergänzen; den vorhandenen Test um die veröffentlichten
Vertragspfade erweitern. Keine API-, Schema- oder Abhängigkeitsänderung.

Prüfung: vorhandener Proxy-Test erst rot, dann grün; Mikes exakter HTTP-Aufruf
muss danach JSON mit `instrument_types` liefern. Dashboard-Suite und ESLint.

**Doku-Abgleich:** README/Entwicklungsserver verspricht bereits die API-
Weiterleitung. Die Korrektur erfüllt diese Zusage; keine neue Anleitung nötig.
Lessons: SI-CX-01 und AL-R-02 (Fassung 2026-09-11) angewendet: tatsächlichen
Nutzerweg messen und alle veröffentlichten Vertragspfade abdecken. Mein
voriger Hinweis auf „Example Value“ erklärte Mikes Fehler nicht.
