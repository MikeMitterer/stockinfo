# Qualitätsprofil

Woran man in diesem Projekt ein gutes Ergebnis erkennt, auch wo kein Werkzeug
misst. Maßstab für den Qualitätslauf am Sprintende und für den Reviewer
(Guard `quality`, Bericht ist Pflicht). Ein Konzeptticket, das den Aufbau
ändert, gleicht es ab.
Leere Abschnitte heißen „noch nicht entschieden“; „keine“ ist eine Entscheidung.
Eine Aussage mit „nur“ oder „nie“ nennt, was sie durchsetzt (Test, Lint-Regel);
ohne das ist sie eine Konvention. Steht eine Regel schon in den Projektregeln
([`AGENTS.md`](../AGENTS.md)), verweist das Profil auf den Abschnitt, statt sie
zu wiederholen.

## Übersicht

- [Messbare Grenzen](#messbare-grenzen)
- [Aufbau und Zuständigkeiten](#aufbau-und-zuständigkeiten)
- [Eine Quelle je Wissen](#eine-quelle-je-wissen)
- [Tests](#tests)
- [Fehler und Ausgaben](#fehler-und-ausgaben)
- [Dokumentation](#dokumentation)
- [Bewusste Ausnahmen](#bewusste-ausnahmen)

## Messbare Grenzen

Was `make check` aufruft, steht im `Makefile` (Target `check`) und in der
[Entwicklerdoku](development.md#tests). Was es bricht:

| Prüfung | Quelle | Wirkung |
|---|---|---|
| ruff mit den Standardregeln (Fehler, Importe, Namen) | `Makefile`, Target `check` | bricht `make check` für `app`, `tests`, `scripts`, `plugin_api` |
| Typen des Dashboards (`vue-tsc`), Schlüssel des englischen Katalogs gegen den deutschen (`satisfies typeof de` in `dashboard/src/i18n/en.ts`) | `dashboard/tsconfig*.json` | bricht `make check` |
| ESLint samt Speicherregeln der UX-Foundation | `dashboard/eslint.config.js` | bricht `make check` (über `test-dashboard`) |
| Nutzerdoku gegen das Projekt | `.docs-check.conf.sh` | bricht `make check` und den Pre-Commit-Hook |

Komplexität, Modulgröße, doppelter Code und bekannte Lücken in Abhängigkeiten
misst bisher kein Prüflauf; der Qualitätslauf misst sie von Hand (ruff `C90`,
`SIM`, `RET`, `PLR09`; pylint `duplicate-code`; `pip-audit`; `npm audit`).
Kehrt eine Fundart im nächsten Lauf wieder, wird sie hier zur Schranke oder ihr
Grund steht dabei (L-175).

[↑ Übersicht](#übersicht)

## Aufbau und Zuständigkeiten

Die Ordner und ihre Aufgaben beschreibt die
[Entwicklerdoku](development.md#project-layout).

- **Datenbank nur in `app/persistence/`:** Treiber, ORM, SQL und Dateizugriffe
  auf die Datenbank stehen nur dort; durchgesetzt von
  `tests/test_persistence_boundary.py`.
- **Routen sind dünn:** `app/routers/` übersetzt HTTP in Aufrufe der Dienste
  unter `app/services/` und deren Ergebnisse in die Modelle aus
  `app/models.py`. Fachentscheidungen fallen im Dienst. Konvention.
- **Quellen über den Plugin-Vertrag:** Eigene Quellen liegen als Plugins unter
  `app/plugins/` und erfüllen denselben Vertrag wie fremde (`plugin_api/`).
  Der Core nutzt die Werttypen des Vertrags (`stockinfo_plugin`) als eigene;
  `app/plugin_adapters.py` übersetzt zwischen Plugin-Aufrufen und den
  Diensten. Der Vertrag ist ein eigenes Paket und importiert nichts aus
  `app/`. Konvention; die Vertragsseite prüft `make test-plugin-api`.
- **Dashboard:** `src/api/` spricht die REST-API, `src/composables/` hält
  Zustand und Abläufe, `src/components/` zeigt an. Speicher nur über
  `safeStorage` der UX-Foundation (ESLint). Sonst Konvention.
- **Bezeichner sind englisch, Erklärungen deutsch:** Regel und Gegenprobe per
  Inventar stehen in [`AGENTS.md`](../AGENTS.md#bezeichner-sind-englisch-ausnahmslos).
- **Muster vor Fallunterscheidung:** Verzweigt Logik an mehreren Stellen nach
  derselben Art (Quelle, Identitätsform, Format), gehört die Entscheidung an
  eine Stelle; dieselbe Fallunterscheidung an mehreren Orten ist ein Befund.
  Konvention.
- Ein Modul, das zu lang wird, wird nach einem fachlichen Teil geteilt, nicht
  nach Zeilen. Konvention.

[↑ Übersicht](#übersicht)

## Eine Quelle je Wissen

- **Einstellungen** stehen in `app/config.py` (Settings-Klasse) mit ihrem
  Standardwert; Doku und `.env.example` nennen sie, ohne den Code zu ersetzen.
- **Texte des Dashboards** stehen nur in `dashboard/src/i18n/` (de und en).
  Ein sichtbarer Text im Komponentencode ist ein Befund (Skill
  `code-conventions`, i18n).
- **Feldlisten und Wertgruppen** (Metadatenfelder, Identitätsformen, Rollen der
  Quellen) stehen einmal als Konstante; weitere Stellen leiten ab statt
  abzuschreiben. DRY ist eine MUST-Regel des Skills `code-conventions`; ein
  Verstoß bleibt blockierend (Lesson SI-P-13,
  [`AGENTS.md`](../AGENTS.md#tatsächlicher-entwicklungsstand)).
- **REST-Vertrag:** `contract/` mit OpenAPI-Schnappschuss; Prüfung siehe
  [contract/README.md](../contract/README.md).

[↑ Übersicht](#übersicht)

## Tests

- Ein Test belegt ein Verhalten, das ein Mensch bemerken würde; keine Tests für
  reine Darstellung oder Implementierungsdetails.
- Datenbanken in Tests: siehe
  [`AGENTS.md`](../AGENTS.md#datenbankzugriffe-in-tests); durchgesetzt von
  `tests/conftest.py`.
- Wächtertests (Grenzen, Vollständigkeit) leiten ihre Fälle aus der Quelle ab
  und haben eine Gegenprobe, die den Verstoß findet; Vorbild
  `tests/test_persistence_boundary.py`.
- Außengrenzen in Tests tragen die Signatur ihres Vertrags; durchgesetzt von
  `tests/test_boundaries.py`.
- Online-Tests tragen die Marke `integration` und laufen nicht in
  `make check`.
- Sichtbare Abläufe belegt `dashboard/e2e/visual-check.mjs` (siehe
  [`AGENTS.md`](../AGENTS.md#browserprüfung)).

[↑ Übersicht](#übersicht)

## Fehler und Ausgaben

- **REST:** Fachfehler, die das Dashboard erklärt, antworten mit
  `detail = {code, params}` (`ErrorDetail`, `app/routers/validation.py`); das
  Dashboard übersetzt den Code über `errors.reason` bzw. `migration.reason`
  (`dashboard/src/api/reason.ts`) und zeigt nie den Text des Backends.
  **Offen:** Ein Teil der Routen liefert `detail` noch als deutschen Satz
  (etwa `Kein Kurs für …`); ob alle auf Codes umziehen, ist nicht entschieden.
- **Logs:** strukturiert über `structlog` mit einem Ereignisnamen in
  `snake_case` und Feldern statt eingesetzter Werte. Konvention.
- **Make und Skripte:** Statuszeilen mit ✓, ✗ oder ⚠; ein Abbruch nennt den
  nächsten Schritt als Befehl. Konvention.

[↑ Übersicht](#übersicht)

## Dokumentation

Welche Anleitung was enthält und wie sie geschrieben wird, regeln der Skill
`docs-conventions` und [`docs/README.template.md`](README.template.md);
der Doku-Abgleich gehört zur Änderung
([`AGENTS.md`](../AGENTS.md#dokumentation-gehört-zur-änderung)).
`make docs-check` prüft Links, Befehle, Variablen und abhängige Dateien.

[↑ Übersicht](#übersicht)

## Bewusste Ausnahmen

- `docs/superpowers/` enthält historische Entwürfe und Pläne; sie werden nicht
  nachgezogen.

[↑ Übersicht](#übersicht)
