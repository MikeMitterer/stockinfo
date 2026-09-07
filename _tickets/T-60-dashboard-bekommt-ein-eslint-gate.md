# T-60 · Das Dashboard hat keinen ESLint-Gate

**In Arbeit seit 2026-09-07: Codex entwickelt, Claude prüft.** Die frühere
Abhängigkeit ist erfüllt: Die installierte `@mmit/ux-foundation` 0.8.0 liefert
`@mmit/ux-foundation/eslint`, beide Konfigurationshelfer lassen sich direkt
mit Node importieren. ESLint, 339 Dashboardtests und der Build sind grün;
Claude hat den Prüfstand `485eca4` in Runde 1 freigegeben (`1f8fd2f`).

## Für dich

Aktuell kein Handgriff nötig. Mike hat Umsetzung und anschließenden
Claude-Review beauftragt. Claude hat die mechanische Budgeterweiterung mit `continue` freigegeben
(`bfb6bc5`). Technisch freigegeben; Mikes Abschlussbestätigung ist noch offen.
Die Entwicklung setzt unabhängig davon bei T-32 fort.

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
und den allgemeinen 800-Zeilen-Riegel. Der Scope-Checkpoint ist durch Claudes `continue` in `bfb6bc5` verarbeitet;
es lag noch keine Code-Review-Übergabe vor.

Freigegeben durch Claude: `continue` für höchstens **fünf Produktdateien** (die vier unten
plus `Toolbar.vue`), Entfernung des Regex-Tests, ein Ticket und **250 manuell
geänderte Zeilen plus höchstens 1800 generierte Lockfile-Zeilen**. Keine neue
Funktion, Parserkopie, Stilbereinigung oder öffentliche Produkt-API. Der
zusätzliche Komponentenname behebt den einzigen gemessenen Bestandsbefund.

Versionen des ersten Laufs: Node 26.8.1, ESLint 9.39.5,
`@eslint/js` 9.39.5, `typescript-eslint` 8.69.0, `eslint-plugin-vue` 10.11.0,
`globals` 17.12.0. npm meldet ESLint 9 als nicht mehr unterstützt; die Wahl
entspricht der bestehenden Foundation-Toolchain. Die Versionsentscheidung
ist bei der Scope-Prüfung mit zu bewerten, nicht als unbelegtes Qualitätsgrün.

### Abschlussnachweise · Codex, 2026-09-07

- #1–3: Öffentlicher Foundation-Import, Node-ladbare Flat-Config und `npm run lint` grün. `make test-dashboard` führt zuerst ESLint aus; `make test` hängt weiterhin von diesem Target ab.
- #4–8, #12: TypeScript, JavaScript, Vue-Script, Vue-Template und `Reflect.deleteProperty` mit echten Sperrkennungen rot; lokaler Parameter, Typ-Member, Schlüssel, String, Kommentar sowie Testzugriff grün. TS- und Vue-Dateimutanten stoppen auch den normalen Make-Lauf vor Vitest. Alle temporären Dateien entfernt. Rohbeleg: `/tmp/stockinfo-t60-mutants.json`; nach Frischinstallation sieben ESLint-Gegenproben nochmals bestätigt.
- #9–10: Regex-Speicherwächter entfernt; der produktive Erstlauf reproduzierte genau den einen Namensfehler, danach grün. Erstinventar oben.
- #11: `npm ci` erfolgreich (343 Pakete); Netzwerk-Timeouts vorher sind keine bestandenen Läufe. `make test-dashboard`: **51 Dateien, 339 Tests bestanden**, einschließlich vorgeschaltetem ESLint. `npm run build`: Typprüfung und Build erfolgreich. Logs: `/tmp/stockinfo-t60-final-dashboard.log`, `/tmp/stockinfo-t60-final-build.log`.
- Bezeichnerinventar über TypeScript-Compiler-API und Vue-SFC-Parser: alle Bezeichner in Config, Toolbar und geändertem Test englisch. DRY: keine eigene Speicherregel und kein neuer Parser; ein gemeinsamer Restriktionswert für beide Foundation-Helfer.

**Zusätzliche Testkorrektur für #11:** Der bereits vor T-60 vorhandene
`componentStyles.spec.ts` verbot auch `min-width: 0` in `DetailEditor.vue`.
Das ist die Freigabe zum Schrumpfen im Flex-Layout; die UI-Datei bleibt
unverändert. Nur dieser Nullwert wird ausgenommen. Vier neue Fälle prüfen
Null, feste Mindestbreite, eine feste Breite nach Null und weiterhin verbotenes
Padding. Zuerst **2 rot / 4 grün** (Null-Gegenprobe und Bestand rot), danach
**6 grün**. Im ohnehin geänderten Test sind die bisherigen deutschen Bezeichner
per AST-Inventar vollständig nachgezogen. Eine zusätzliche bestehende Testdatei,
keine weitere Produktdatei oder Stilbereinigung. Dieser Mitzieher war im ersten
Scope-Checkpoint noch nicht enthalten und ist im Review ausdrücklich mitzuprüfen.

```bash
# #11: erfolgreiche Frischinstallation nach Netzwerk-Timeouts
npm --prefix dashboard ci --prefer-offline --fetch-timeout=30000 --fetch-retries=1 --no-audit --no-fund
# #1–3, #9, #11: ESLint und alle Dashboardtests
make test-dashboard
# #11: CSS-Ausnahme und Gegenfälle separat
npm --prefix dashboard test -- tests/componentStyles.spec.ts
# #11: Typprüfung und Produktionsbuild
npm --prefix dashboard run build
```

<details>
<summary>Gegenproben #4–8 und #12 reproduzieren (aus der Projektwurzel)</summary>

```bash
cd dashboard
node --input-type=module <<'JS'
import { ESLint } from 'eslint'
import { writeFileSync, unlinkSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
const lint = new ESLint()
const cases = [
  ['src/t60-probe.ts', "localStorage.getItem('x')", 'no-restricted-globals'],
  ['src/t60-probe.js', "localStorage.getItem('x')", 'no-restricted-globals'],
  ['src/T60Probe.vue', `<script setup>window['localStorage'].setItem('x','1')</script>`, 'no-restricted-properties'],
  ['src/T60Probe.vue', `<template><button @click="window['localStorage'].setItem('x','1')">Save</button></template>`, 'vue/no-restricted-syntax'],
  ['src/t60-probe.ts', "Reflect.deleteProperty(window,'localStorage')", 'no-restricted-syntax'],
  ['src/t60-probe.ts', `export function read(localStorage: {getItem(key: string): string}) {return localStorage.getItem('x')}; export interface RecordShape {localStorage: string}; export const record = {localStorage: 'localStorage.getItem'}; // localStorage.getItem('x')`, null],
  ['tests/t60-probe.ts', "localStorage.setItem('x','1')", null],
]
for (const [filePath, source, expected] of cases) {
  const [result] = await lint.lintText(source, {filePath})
  const rules = result.messages.map(message => message.ruleId)
  if (expected ? !rules.includes(expected) : rules.length) throw new Error(JSON.stringify({filePath, rules}))
}
for (const [filePath, source] of [cases[0], cases[2]]) {
  writeFileSync(filePath, source, {flag: 'wx'})
  try {
    const result = spawnSync('make', ['-C', '..', 'test-dashboard'], {encoding: 'utf8'})
    const output = result.stdout + result.stderr
    if (!result.status || !output.includes(filePath) || output.includes('vitest run')) throw new Error(output)
  } finally { unlinkSync(filePath) }
}
console.log('Seven rule probes and two Make stop probes passed')
JS
cd ..
```

</details>

Keine Backend- oder Browserprüfung nötig: keine Fachregel und kein UI-Layout
geändert. npm meldet das Supportende von ESLint 9 (Foundation-Major, siehe
Scope-Entscheidung); Sass-Deprecations und die bestehende Bundlegrößenwarnung
bleiben Hinweise. Keine neue Freigabe eines anderen Tickets.

## Ursprünglicher Scope-Vertrag und Verify-Matrix

Die Kriterien bleiben gültig; die frühere Abhängigkeitsblockade ist aufgehoben.
Die Budgeterweiterung oben ersetzt das ursprüngliche Zeilenbudget.

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Dashboard) | in Arbeit — Scope freigegeben | 2–3 h | ESLint-Grundlage, Foundation-Wächter, verpflichtender Make-Einstieg | — |

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
- `dashboard/src/components/Toolbar.vue` — expliziter Komponentenname

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

- höchstens fünf geänderte Produktdateien; zusätzlich Entfernung des bisherigen
  Regex-Tests und die unten begründete Korrektur eines bestehenden CSS-Tests
- höchstens 250 manuelle Zeilen plus 1800 generierte Lockfile-Zeilen
  (Scope-Entscheidung Claude, `bfb6bc5`; ursprüngliches Budget oben dokumentiert)
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
| **1** | `dashboard/package.json`, `dashboard/eslint.config.js` | `npm run lint` existiert, prüft TypeScript und Vue und lädt die Config ohne Vite | ✅ | |
| **2** | Root-Makefile | `make test-dashboard` startet zuerst `lint-dashboard`; der Gate ist damit auch Teil von `make test` | ✅ | |
| **3** | Paketgrenze | die Speicherregel kommt über den öffentlichen Export von `@mmit/ux-foundation`; StockInfo enthält keine Regelkopie und keinen eigenen Parser | ✅ | |
| **4** | positiver Mutant `.ts` | `localStorage.getItem('x')` unter `dashboard/src/` macht `npm run lint` und `make test-dashboard` rot | ✅ | |
| **5** | positiver Mutant `.vue` | `window['localStorage'].setItem('x', '1')` in Script oder Template macht den Gate rot | ✅ | |
| **6** | statischer Mutant | `Reflect.deleteProperty(window, 'localStorage')` macht den Gate rot, sofern T-19 diese Form als Teil seines Vertrags ausliefert | ✅ | |
| **7** | negative Mutanten | lokaler Parameter namens `localStorage`, Typ-Member, Objektschlüssel, String und Kommentar bleiben grün | ✅ | |
| **8** | Test-Override | bestehende Test-Gegenproben dürfen Browser-Storage direkt verwenden; derselbe Code unter `dashboard/src/` ist verboten | ✅ | |
| **9** | alter Wächter | `dashboard/tests/storageAccess.spec.ts` ist entfernt; kein Regex-Dateiscan ersetzt ESLint | ✅ | |
| **10** | Erstinventar | Fehler je Regel-ID und betroffene Dateien sind im Ticket dokumentiert; eine Budgetüberschreitung führt zum Scope-Checkpoint | ✅ | |
| **11** | Locks und Qualitätsläufe | `npm --prefix dashboard ci`, `npm --prefix dashboard run lint`, `npm --prefix dashboard test`, `npm --prefix dashboard run build` und `make test-dashboard` sind grün | ✅ | |
| **12** | Gegenprobe zum Gate | ein temporär eingebauter positiver Mutant wird vom normalen Make-Lauf nachweislich gefunden und danach vollständig entfernt | ✅ | |

Die Human-Spalte bleibt unangetastet. Dieses Ticket enthält keine
Geschmacks- oder Produktentscheidung; die Nachweise kann Codex vollständig
reproduzieren.

## Erwartete Nebenwirkung

Der Regex-Wächter mit zwei Tests entfällt; vier CSS-Gegenproben kommen hinzu.
Der abschließende Lauf umfasst deshalb 339 Tests (vorher 337).
Das ist kein Verlust an Schutz: Der neue Gate läuft vor der Dashboard-Suite,
versteht Syntax und wird mit positiven und negativen Mutanten belegt. Falls
der allgemeine Erstlauf Altlasten findet, werden sie sichtbar gemacht — nicht
im selben Ticket unkontrolliert mitrepariert.

## Review-Historie · T-60 Runde 1, `approved`

Geprüft hat **Claude** als zugeordneter Verifier. Prüfstand `485eca4`,
Vergleichsbasis `5028dfe`. Die verarbeitete OUTBOX ist entfernt. Nach dem
Prüfstand liegt kein Produktedit; der Arbeitsbaum war bei Beginn und am Ende
deckungsgleich mit dem eingefrorenen Stand.

### Der Riegel beißt — mit eigenen Mutanten, nicht mit deinen

Die Begründung des Tickets ist, dass der alte Regex-Wächter drei Zugriffsformen
übersehen konnte. Ich habe genau diese drei selbst gebaut, statt deine Proben zu
bewerten:

```
src/__t60probe/plain.js       localStorage.getItem('x')
  → no-restricted-globals    Unexpected use of 'localStorage'
src/__t60probe/bracket.ts     window['localStorage'].getItem('x')
  → no-restricted-properties 'window.localStorage' is restricted
src/__t60probe/viaReflect.ts  Reflect.get(globalThis, 'localStorage')
  → no-restricted-syntax     Use safeStorage from @mmit/ux-foundation
✖ 3 problems (3 errors, 0 warnings)
```

Alle drei greifen — genau die Formen, die der entfernte Regex nicht sehen
konnte. Der Ersatz ist damit nicht gleichwertig, sondern **stärker**. Die
Zusage des gelöschten `storageAccess.spec.ts` lebt weiter.

### Eine Form greift nicht — und das ist richtig so

Ein nackter Bezeichner im Vue-**Template** wird nicht gemeldet. Ich habe das
nicht als Lücke stehen lassen, sondern nachgesehen, ob dort überhaupt etwas zu
holen ist. Erst die Kontrolle: Ein Script-Verstoß in derselben `.vue`-Datei
wird gemeldet, die Datei wird also geprüft. Dann der Compiler:

```
{{ localStorage.getItem("y") }}        → _ctx.localStorage.getItem("y")
{{ window.localStorage.getItem("y") }} → _ctx.window.localStorage.getItem("y")
{{ Math.max(1,2) }}                    → Math.max(1,2)
```

Vue löst `localStorage` gegen den Komponentenkontext auf, nicht gegen das
Browser-Global — anders als `Math`, das auf Vues Allowlist steht. Ein
Template-Zugriff auf den echten Speicher ist damit **nicht erreichbar**; es gibt
nichts zu bewachen. Kein Befund gegen T-60.

Als Beobachtung für das Fundament, nicht für dieses Ticket: Die zwölf Selektoren
aus `noDirectGlobalsInTemplates` verlangen alle ein `window.`/`globalThis.`/
`self.`-Präfix, und auch diese Formen kompilieren zu `_ctx.window`. Der
Template-Helfer bewacht dort also durchweg Unerreichbares. Das gehört nach
`ux-foundation`, nicht hierher — T-60 verbietet ausdrücklich eine lokale Kopie.

### Der Make-Riegel lässt sich nicht umgehen

```
make test-dashboard  (mit einem Lint-Fehler in src/)
  → make: *** [lint-dashboard] Error 1     Exitcode 2
  → vitest wurde nicht erreicht (0 Treffer im Protokoll)
```

`make -n test` zeigt die Kette Backend → Plugin-API → Beispiel →
`lint-dashboard` → Vitest. Auch über das Sammelziel kommt niemand am Gate
vorbei. Sauberer Lauf: **51 Dateien, 339 Tests**, dazu `vue-tsc` ohne Befund und
ein erfolgreicher Vite-Build.

### Der CSS-Mitzieher, den du ausdrücklich vorgelegt hast

Beides geprüft, was hier schiefgehen kann.

**Unterscheiden die Gegenfälle?** Ich habe die Ausnahme aufgeweicht, sodass
*jeder* `min-width`-Wert erlaubt wäre. Rot werden genau die zwei erwarteten:

```
× min-width: 12rem; bleibt korrekt eingeordnet
× min-width: 0; min-width: 12rem; bleibt korrekt eingeordnet
```

**Ist der Hauptwächter noch scharf?** An einer echten Naive-Klasse
`.detail-editor__text` eine feste Mindestbreite hinter die erlaubte Null
gesetzt:

```
src/components/DetailEditor.vue → .detail-editor__text: min-width
FAIL  Eigenes CSS auf Naive-Komponenten
```

Der Punkt, an dem eine naive Umsetzung gescheitert wäre, ist getroffen: Das
`.some()` über **alle** Deklarationen fängt die spätere feste Angabe, die in CSS
gewinnt. Die Verengung erlaubt wirklich nur den Flex-Nullwert.

Der Umbau der deutschen Bezeichner in derselben Datei ist die Regel aus
CLAUDE.md richtig angewandt — die deutsche Prosa in `describe`/`it` bleibt, die
Bezeichner ziehen mit.

### Umfang: innerhalb der erweiterten Grenze

Gemessen, nicht übernommen — und deckungsgleich mit deiner Angabe:

| | gemessen | Grenze |
|---|---|---|
| manuelle Zeilen | **182** (+89/−93) | 250 |
| Lockfile | **1529** (+1472/−57) | 1800 |
| Produktdateien | 5 | 5 |

Der zusätzliche Test-Diff bleibt mit 70 Zeilen und einer Testdatei innerhalb der
Regel für kleine Befunde im laufenden Lauf; Ursache, Korrektur und
Wiederholungsbeleg stehen dabei. Dass du ihn ausgewiesen hast, statt ihn
mitlaufen zu lassen, ist der Grund, warum er hier keine eigene Runde braucht.

### Weitere Abnahmebedingungen

- **DRY.** `storageRestrictions` steht einmal und geht an beide öffentlichen
  Helfer. Keine Kopie einer Foundation-Regel, kein eigener Parser, keine neue
  Test-CLI. Der Testinfrastruktur-Riegel ist eingehalten.
- **Bezeichner englisch, als Inventar gemessen:** TypeScript-Compiler über die
  drei verbliebenen geänderten Dateien, 217 Bezeichner, kein deutscher.
- **`Toolbar.vue`** bekommt genau eine Zeile `defineOptions({ name:
  'AssetToolbar' })`. Keine Umbenennung der Datei, keine Layoutänderung — die
  mildere der beiden Möglichkeiten, wie im `continue` vorgesehen.
- **ESLint 9** ist unverändert die Foundation-Folge; nichts daran hat sich
  seit dem Scope-Checkpoint verschoben.

### Nicht selbst geprüft

Kein `npm ci` aus leerem `node_modules` — ich habe gegen den installierten Stand
gelintet und getestet. Deine Reproduzierbarkeitsangabe bleibt dein Beleg. Kein
Backend- und kein Browserlauf; beides ist unberührt.

### Nächster Schritt

Freigegeben. Weiter nach der bestehenden Kette zu
`T-32-testdatenbank-abschottung.md`. Zur Erinnerung aus meinem Prüfstand dort:
Der Riegel gehört in die Testumgebung, `#3` ist laut Codex' eigener Einordnung
kein Pflichtumfang, und die Gegenprobe gehört mit eingecheckt. T-60 bleibt
offen, bis Mike es bestätigt.

