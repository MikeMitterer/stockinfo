# T-75 · Typkatalog aus Swagger über den Dev-Proxy abrufen

Mikes `GET http://localhost:5173/instrument-types` liefert die SPA-HTML-Seite.
Der Backend-Aufruf auf Port 8000 liefert die Typen korrekt. Ursache ist der
fehlende Eintrag in `dashboard/api-prefixes.ts`; der bestehende Proxy-Test
prüft nur UI-Aufrufe und erfasst Swagger-Aufrufe deshalb nicht.

**Stand:** Korrektur umgesetzt, live geprüft und unabhängig geprüft —
**approved**, Claude, Runde 1, `fc67ea3`. Keine Befunde. Nur der
menschliche Abschluss (Verschieben nach `40-done/`) steht noch aus.

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

## Nachweis · Codex, 2026-09-26

Der erweiterte Proxy-Test war zuerst rot und nannte ausschließlich
`/instrument-types` als fehlenden Pfad. Nach Ergänzung bestanden alle
**378 Dashboard-Tests**; ESLint für beide Dateien und `git diff --check` grün.
TypeScript-Compilerinventar beider Dateien geprüft: alle Bezeichner englisch.
Bekannte Sass- und vue-i18n-Warnungen im Gesamtlauf, keine Testfehler.

Mikes Aufruf `curl -X GET http://localhost:5173/instrument-types -H 'accept: */*'`
liefert nun HTTP 200, `content-type: application/json`, `cache-control: no-store`
und `instrument_types: [bond, crypto, etc, etf, fund, stock]`, `complete: true`.
Nachweisdateien: `/private/tmp/stockinfo-t75-headers.txt` und
`/private/tmp/stockinfo-t75-body.json`. Der laufende Server übernahm die
Konfiguration; kein manueller Neustart. Der bestätigende HTTP-Aufruf benötigte
freigegebenen Zugriff außerhalb der Sandbox. Meine zwischenzeitliche Vermutung
eines ausgegangenen Servers war durch die spätere Listener-Prüfung widerlegt.

Standards gelesen: `code-standards/SKILL.md` und `references/frontend.md`.
Architektur unverändert, eine bestehende Präfixliste; Frontend/Qualität durch
Compilerinventar, ESLint, Tests und echten HTTP-Weg geprüft. Shell/CLI, Python,
Persistenz und API-Vertrag unverändert. Doku-Abgleich wie oben.

## Unabhängiger Review · Claude, Runde 1, 2026-09-26

**Ergebnis: approved.** Geprüft am eingefrorenen Stand `fc67ea3`. Volles
Ergebnis mit Belegen steht in
[STATUS](../STATUS.md#inbox--codex--t-75-runde-1--approved); hier nur die
Kurzfassung.

- Rot/Grün selbst nachgestellt: `/instrument-types` testweise wieder aus
  `apiPrefixes` entfernt, Test wird rot mit genau diesem einen Eintrag,
  Fassung danach wiederhergestellt.
- Eigener Testlauf: `viteProxy.spec.ts` 3 passed, volle Dashboard-Suite
  378 passed, ESLint sauber.
- TS-Compiler-Inventar (nicht `grep`) über beide Dateien: 118 Bezeichner,
  keiner deutsch.
- Live selbst reproduziert: Mikes exakter Aufruf auf Port 5173 liefert bei
  mir ebenfalls HTTP 200 mit den sechs Typen und `complete: true`.

Menschlicher Abschluss (Verschieben nach `40-done/`) steht noch aus.
