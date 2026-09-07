# T-60 · Das Dashboard hat keinen ESLint-Gate

**In Arbeit seit 2026-09-07: Codex entwickelt, Claude prüft.** Die frühere
Abhängigkeit ist erfüllt: Die installierte `@mmit/ux-foundation` 0.8.0 liefert
`@mmit/ux-foundation/eslint`, beide Konfigurationshelfer lassen sich direkt
mit Node importieren. Der erste Lint-Lauf findet nur einen Namensbefund.

## Für dich

Aktuell kein Handgriff nötig. Mike hat Umsetzung und anschließenden
Claude-Review beauftragt. Die mechanische Überschreitung des alten Zeilenbudgets
durch das npm-Lockfile geht als Scope-Checkpoint an Claude.

## Umsetzung und technische Nachweise · 2026-09-07

Vor dem ersten Produktedit: `npm --prefix dashboard run lint` scheitert mit
`Missing script: lint`. Danach Bestandsinventar mit einer temporären Flat-Config
außerhalb des Projekts: JavaScript/TypeScript `recommended`, Vue `flat/essential`
(Fehlervermeidung ohne zusätzliche Stilregeln), Foundation-Sperren für `src/`.
**124 Dateien geprüft, genau ein Fehler in einer Datei:**

| Regel | Anzahl | Datei | Geplante Korrektur |
|---|---:|---|---|
| `vue/multi-word-component-names` | 1 | `dashboard/src/components/Toolbar.vue` | Expliziter Komponentenname `AssetToolbar` über `defineOptions`; keine Regelabschaltung. |

JSON-Befund: `/tmp/stockinfo-t60-first-lint.json`. Konfiguration und installierte
Prüfwerkzeuge: `/tmp/stockinfo-t60-lint.1fiFQi/`. Wiederholung aus `dashboard/`:

```bash
# #10: unverändertes Erstinventar, vor Bereinigung
node /tmp/stockinfo-t60-lint.1fiFQi/node_modules/eslint/bin/eslint.js . --config /tmp/stockinfo-t60-lint.1fiFQi/eslint.config.mjs --format json --output-file /tmp/stockinfo-t60-first-lint.json
```

### Scope-Checkpoint · mechanisches Lockfile

Die beauftragten ESLint-Abhängigkeiten sind durch npm eingetragen. Der Diff
umfasst bisher `package.json` (+5) und `package-lock.json` (+1472/-57).
Damit überschreitet bereits die generierte Auflösung das alte 250-Zeilenbudget
und den allgemeinen 800-Zeilen-Riegel. Weitere Produktarbeit pausiert bis zur
Scope-Entscheidung; dies ist noch keine Code-Review-Übergabe.

Vorgeschlagen: `continue` für höchstens **fünf Produktdateien** (die vier unten
plus `Toolbar.vue`), Entfernung des Regex-Tests, ein Ticket und **250 manuell
geänderte Zeilen plus höchstens 1800 generierte Lockfile-Zeilen**. Keine neue
Funktion, Parserkopie, Stilbereinigung oder öffentliche Produkt-API. Der
zusätzliche Komponentenname behebt den einzigen gemessenen Bestandsbefund.

Versionen des ersten Laufs: Node 26.8.1, ESLint 9.39.5,
`@eslint/js` 9.39.5, `typescript-eslint` 8.69.0, `eslint-plugin-vue` 10.11.0,
`globals` 17.12.0. npm meldet ESLint 9 als nicht mehr unterstützt; die Wahl
entspricht der bestehenden Foundation-Toolchain. Die Versionsentscheidung
ist bei der Scope-Prüfung mit zu bewerten, nicht als unbelegtes Qualitätsgrün.

## Ursprünglicher Scope-Vertrag und Verify-Matrix

Die Kriterien bleiben gültig; die frühere Abhängigkeitsblockade ist aufgehoben.
Die Budgeterweiterung oben ist bis zur Entscheidung nur ein Vorschlag.

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Dashboard) | in Arbeit — Scope-Checkpoint | 2–3 h | ESLint-Grundlage, Foundation-Wächter, verpflichtender Make-Einstieg | — |

- **Angelegt:** 2026-09-04, auf Mikes Auftrag
- **Hängt ab von:** `ux-foundation` T-19 „Wächter gehört ins Fundament“
- **Danach:** erst beginnen, wenn der öffentliche ESLint-Einstiegspunkt des
  Fundaments feststeht und in einer installierbaren Version vorliegt

**Löst:** Das Dashboard hat derzeit keinen ESLint-Lauf. In
`dashboard/package.json` fehlen Script und Abhängigkeiten, eine
`eslint.config.*` gibt es nicht und das Root-Makefile ruft keinen Linter auf.
Die Formulierung „ESLint grün“ in T-56 beziehungsweise `STATUS.md` war damit
nicht reproduzierbar; selbst der vorhandene `eslint-disable`-Kommentar ist
heute wirkungslos.

Der bestehende `dashboard/tests/storageAccess.spec.ts` ersetzt ESLint nicht.
Er durchsucht nur `.ts` und `.vue` mit einem regulären Ausdruck. Dadurch kann
er gültige Syntax missverstehen und Zugriffsformen wie JavaScript-Dateien,
Bracket-Notation oder statische Aufrufe über `Reflect` beziehungsweise
`Object` übersehen. Der allgemeine, syntaxbasierte Wächter entsteht deshalb
einmal im Fundament; StockInfo bindet ihn in seine normale Prüfkette ein.

---

## Scope-Vertrag

### Ergebnis

Ein frischer Checkout kann mit einem dokumentierten Standardbefehl das
gesamte Dashboard linten. Derselbe normale Root-Testlauf, der heute Vitest
startet, scheitert auch an einem verbotenen direkten Speicherzugriff unter
`dashboard/src/`. StockInfo besitzt keine eigene Kopie der Foundation-Regel.

### Fachliche Änderungen (maximal drei)

1. Das Dashboard erhält eine Flat-Config und die dazu kompatiblen
   ESLint-Abhängigkeiten für TypeScript und Vue; `npm run lint` ist der eine
   lokale Einstiegspunkt.
2. Die Config bindet den **öffentlichen** ESLint-Einstiegspunkt von
   `@mmit/ux-foundation` ein und konfiguriert den App-Vertrag: direkter
   `localStorage`-Zugriff ist in `dashboard/src/` verboten, Tests dürfen ihn
   für Gegenproben verwenden.
3. Das Root-Makefile erhält `lint-dashboard`; `test-dashboard` hängt davon ab,
   sodass `make test` den Gate nicht umgehen kann. Der Regex-Wächter entfällt.

### Produktflächen / Dateien

- `dashboard/eslint.config.js`
- `dashboard/package.json`
- `dashboard/package-lock.json`
- `Makefile`

### Tests / Dokumentation

- `dashboard/tests/storageAccess.spec.ts` wird entfernt; seine Zusage lebt
  anschließend im ESLint-Gate und in dessen Foundation-Tests.
- Dieses Ticket dokumentiert Abhängigkeit, Mutanten und das Ergebnis des
  erstmaligen Bestandslaufs.

### Nicht-Ziele

- Kein Python-Linter und keine Bereinigung des Backend-Bestands.
- Keine lokale StockInfo-Regel und kein eigener Datei-, TypeScript- oder
  Vue-SFC-Parser.
- Keine pauschalen `eslint-disable`-Blöcke, keine flächige Abschwächung
  empfohlener Regeln und keine nebenbei ausgeführte Stilbereinigung.
- Keine Laufzeitänderung an `safeStorage` oder an der Oberfläche.

### Budget

- höchstens vier geänderte Produktdateien plus Entfernung des bisherigen
  Regex-Tests
- höchstens 250 neue oder geänderte Zeilen
- Zeigt der erste ehrliche ESLint-Bestandslauf mehr als zehn zu ändernde
  Produktdateien oder sprengt er das Zeilenbudget, folgt ein
  Scope-Checkpoint. Die Befunde werden nach Regel-ID inventarisiert und in
  eigene Folgetickets getrennt; sie werden nicht mit globalen Ausnahmen
  versteckt.

---

## Technischer Vertrag

- Flat Config auf Basis der offiziellen JavaScript-, TypeScript- und
  Vue-Konfigurationen; Versionsstände müssen zueinander und zur im Projekt
  verwendeten Node-Version passen.
- Die Config muss direkt durch Node geladen werden können. Vite transpiliert
  eine ESLint-Konfiguration nicht.
- Der Foundation-Einstiegspunkt wird unter seinem veröffentlichten
  Paketnamen importiert, nicht über einen internen Alias oder einen Pfad in
  `node_modules`.
- Der Speicherwächter gilt für ausführbaren Anwendungscode unter
  `dashboard/src/`; Bezeichner in Kommentaren, Strings, Typen und Objektschlüsseln
  sind kein Zugriff.
- Die vorhandene Ausnahme für Tests ist explizit und pfadbezogen. Eine
  Abschaltung für das gesamte Projekt erfüllt den Vertrag nicht.
- `lint-dashboard` erhält einen normalen `##`-Hilfetext nach den
  Makefile-Konventionen und wird als `.PHONY` deklariert.
- `package-lock.json` wird durch npm erzeugt und stimmt mit
  `dashboard/package.json` überein.

## Erstinventar vor der Bereinigung

Vor der ersten Produktänderung wird der ungeschönte ESLint-Lauf festgehalten:
Anzahl der Fehler je Regel-ID und betroffene Dateien. Dieser Befund entscheidet,
ob das Ticket im Budget bleibt. Bereits vorhandene Meldungen werden nicht
durch eine immer längere Ignore-Liste „grün“ gemacht.

---

## Verify

Legende: ✅ bestanden · ⚠️ fehlgeschlagen · ◑ teilweise · ➖ nicht geprüft

| # | Where | Look for | AI | Human |
|---|---|---|:--:|:--:|
| **1** | `dashboard/package.json`, `dashboard/eslint.config.js` | `npm run lint` existiert, prüft TypeScript und Vue und lädt die Config ohne Vite | ➖ | |
| **2** | Root-Makefile | `make test-dashboard` startet zuerst `lint-dashboard`; der Gate ist damit auch Teil von `make test` | ➖ | |
| **3** | Paketgrenze | die Speicherregel kommt über den öffentlichen Export von `@mmit/ux-foundation`; StockInfo enthält keine Regelkopie und keinen eigenen Parser | ➖ | |
| **4** | positiver Mutant `.ts` | `localStorage.getItem('x')` unter `dashboard/src/` macht `npm run lint` und `make test-dashboard` rot | ➖ | |
| **5** | positiver Mutant `.vue` | `window['localStorage'].setItem('x', '1')` in Script oder Template macht den Gate rot | ➖ | |
| **6** | statischer Mutant | `Reflect.deleteProperty(window, 'localStorage')` macht den Gate rot, sofern T-19 diese Form als Teil seines Vertrags ausliefert | ➖ | |
| **7** | negative Mutanten | lokaler Parameter namens `localStorage`, Typ-Member, Objektschlüssel, String und Kommentar bleiben grün | ➖ | |
| **8** | Test-Override | bestehende Test-Gegenproben dürfen Browser-Storage direkt verwenden; derselbe Code unter `dashboard/src/` ist verboten | ➖ | |
| **9** | alter Wächter | `dashboard/tests/storageAccess.spec.ts` ist entfernt; kein Regex-Dateiscan ersetzt ESLint | ➖ | |
| **10** | Erstinventar | Fehler je Regel-ID und betroffene Dateien sind im Ticket dokumentiert; eine Budgetüberschreitung führt zum Scope-Checkpoint | ➖ | |
| **11** | Locks und Qualitätsläufe | `npm --prefix dashboard ci`, `npm --prefix dashboard run lint`, `npm --prefix dashboard test`, `npm --prefix dashboard run build` und `make test-dashboard` sind grün | ➖ | |
| **12** | Gegenprobe zum Gate | ein temporär eingebauter positiver Mutant wird vom normalen Make-Lauf nachweislich gefunden und danach vollständig entfernt | ➖ | |

Die Human-Spalte bleibt unangetastet. Dieses Ticket enthält keine
Geschmacks- oder Produktentscheidung; die Nachweise kann Codex vollständig
reproduzieren.

## Erwartete Nebenwirkung

Der Vitest-Zähler sinkt durch das Entfernen des zwei Testfälle umfassenden
Regex-Wächters.
Das ist kein Verlust an Schutz: Der neue Gate läuft vor der Dashboard-Suite,
versteht Syntax und wird mit positiven und negativen Mutanten belegt. Falls
der allgemeine Erstlauf Altlasten findet, werden sie sichtbar gemacht — nicht
im selben Ticket unkontrolliert mitrepariert.
