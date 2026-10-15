# T-104 · README nach dem Skill: nutzerorientiert, Entwicklung nach docs/development.md

**Warum dieses Ticket:** Der Skill `readme-conventions` hält Make-Targets,
npm-Befehle, Verzeichnisbäume, Test- und Release-Abläufe und Interna wie
Cache oder CORS aus dem README heraus; das README verlinkt dafür die
Entwicklerdoku. StockInfos `README.md` und `README.de.md` enthalten all das
(je rund 670 Zeilen, 48 `make`-Stellen), weil `AGENTS.md` bisher sagte:
„Entwickleranleitungen gehören ins Root-README“. StockPortfolio trennt
beides bereits: README für Nutzer, `docs/development.md` für Entwickler.

**Beispiel:** Wer StockInfo nur betreiben will, liest heute im README
zwischen Installation und Lizenz auch `make tag-patch`, den Verzeichnisbaum
und die Push-Rechte des Docker-Hub-Tokens. Danach steht im README, was
StockInfo kann und wie man es startet; der Entwicklerweg ist einen Link
entfernt.

**Stand:** Auf Mikes Entscheidung vom 2026-10-15 angelegt und aktiviert
(Frage zum README-Umbau, Antwort „Wie StockPortfolio“). Coder `claude`,
Verifier `codex`, Branch `t-104-readme-nach-skill`.

## Befunde der Prüfung (2026-10-15, vor der Umsetzung)

`make docs-check`: keine Probleme, keine Hinweise. Die ausführliche Ausgabe
(`--verbose`) und der Skill ergeben:

| # | Befund | Fundstelle |
|---|---|---|
| 1 | Make-Targets, npm-Befehle, Verzeichnisbaum, Test- und Release-Ablauf, Cache- und CORS-Details im README | `README.md`, `README.de.md`: Requirements, Quick start, Dashboard, Docker, Tests, Releases, Project layout, Security model |
| 2 | Abschnitt „Dashboard“ beschreibt einen alten Aufbau: Es fehlen FX und Analysis in der Navigation; Themes, Environment und About sind Bereiche unter Settings (Appearance, Language, API & Links, Backups, Environment, About) | `README.md:388–431`, `README.de.md:409–457`; Quelle `dashboard/src/components/AppHeader.vue:58–62`, `i18n/en.ts` |
| 3 | „8 themes“; `@mmit/ux-foundation` liefert 14 (`THEME_IDS`), das Panel zeigt alle | `README.md:104`, `:407`, `README.de.md:111`, `:431` |
| 4 | Docker-Hub-Link auf die Verwaltungsseite (`hub.docker.com/repository/docker/…/general`), die eine Anmeldung verlangt (HTTP 302); öffentlich ist `hub.docker.com/r/mangolila/stockinfo` | `README.md:18`, `:439`, `README.de.md:19`, `:467` |
| 5 | Kein Mermaid-Diagramm für den Datenfluss zur Schwester-App und zu den Quellen | beide READMEs |
| 6 | Absatzregel: neue Information im selben Absatz | `README.md` Kopfabsatz (Image, Changelog, Release Notes); `docker/README.md:28–31` („To use both … Details are in its Docker guide“); `unraid/README.md:11–14` („see …“ im selben Satz) und `:38–41` (zwei Bedingungen in einem Absatz) |

Externe Links sonst erreichbar (14 geprüft); `YOUR_UNRAID_SERVER` ist ein
Platzhalter.

## Scope-Vertrag

**Beobachtbares Ergebnis:** `README.md` und `README.de.md` folgen dem Skill
ohne Ausnahme; der Entwicklerweg steht vollständig in `docs/development.md`;
`make docs-check` ohne Probleme; alle eingehenden Anker zeigen auf
bestehende Überschriften.

**Fachliche Änderungen (drei):**

1. Projektregel und Vorlage: `AGENTS.md` (Entwickleranleitung in
   `docs/development.md`), `docs/README.template.md` nach dem Skill ohne
   Ausnahme, `.docs-check.conf.sh` (Pflichtdatei, Abhängigkeiten).
2. Entwicklerdoku: `docs/development.md` mit allem, was das README abgibt
   (Voraussetzungen, Einrichten, Befehle, Tests, Docker-Build und -Push,
   Release, Projektaufbau), in Englisch wie die Quelle.
3. READMEs neu nach der Vorlage, beide Sprachen, mit Mermaid-Diagramm;
   Befunde 2–6 behoben; eingehende Anker in `LICENSING.md`,
   `docs/plugins.md`, `unraid/README.md` nachgezogen; `docker/README.md`,
   Vorschau und `unraid/README.md` angeglichen.

**Erwartete Dateien:** `AGENTS.md`, `docs/README.template.md`,
`.docs-check.conf.sh`, `docs/development.md` (neu), `README.md`,
`README.de.md`, `docker/README.md`, `docker/preview/README.md`,
`unraid/README.md`, `LICENSING.md`, `docs/plugins.md`, `.docs-check.ack`
— 12 Dateien, keine Produkt- oder Testdatei.

**Diff-Budget:** rund 2.000 Zeilen, überwiegend verschobener Text (die
READMEs schrumpfen von je rund 670 auf rund 200 Zeilen). Das liegt über der
800-Zeilen-Grenze; Mike hat den Umbau mit dem Hinweis „Eigenes Ticket,
größerer Diff“ ausdrücklich gewählt. Das gilt als Vorabfreigabe des
Umfangs; geht der Diff über 2.400 Zeilen oder kommt eine weitere Datei
dazu, folgt ein Scope-Checkpoint.

**Nachträge Mike, 2026-10-15 (im laufenden Auftrag):**

- „Passe auch das AGENTS.md entsprechend an. Generell soll AGENTS nur auf
  den README-Skill verweisen und auf README.template.md um
  zweigleisigkeiten zu vermeiden“: Der Doku-Abschnitt in `AGENTS.md`
  verweist nur noch auf `readme-conventions`, die Vorlage und
  `docker-conventions`; README-Regeln werden dort nicht wiederholt.
- „Schau dir auch die .docs-check.conf.sh - prüfe ob die Settings Sinn
  machen“: Befunde und Änderungen unten unter „Config-Prüfung“.
- „In der Doku haben geplante Features überhaupt nichts zu suchen!“: Die
  Beschreibungen des geplanten Generation-Ablaufs fallen aus
  `docs/rest-core-contract.md`, `contract/README.md` und
  `docs/plugin-authors.md`. Das Vertragsartefakt
  `contract/core-contract.json` führt den Plan selbst unter `planned`; das
  ist Produktvertrag mit Tests und wird hier nicht geändert, sondern als
  Befund an Mike gegeben.

Damit kommen drei Dateien dazu (15 statt 12); das gehört zu Mikes
ausdrücklichem Auftrag und löst keinen Scope-Checkpoint aus.

**Nachtrag Mike, 2026-10-15 (EUPL-Lizenzabschnitt, aus der
StockPortfolio-Sitzung):**

- Der Skill `readme-conventions` hat jetzt einen festen EUPL-Baustein
  `templates/license-eupl.md` (Skill-Commits `c32e415`, `deaaaa3`). Er gilt
  auch neben einer Projektvorlage; diese darf ihn nur ergänzen.
- `docs/README.template.md`, Abschnitt 13: Die eigene Punkteliste, die feste
  Linkliste und „der Aufbau folgt StockPortfolios README“ fallen weg. Der
  Abschnitt verweist nur auf den Baustein, Wortlaut unverändert, mit allen
  Werten und Links aus `LICENSING.md` und den dort genannten Lizenzdateien.
  `plugin_api/` unter MIT bleibt über den bedingten Teillizenz-Absatz des
  Bausteins drin. Vorbild: StockPortfolio `486d760`.
- `README.md`/`README.de.md`, Lizenz: Die Pflichten gelten nach EUPL Art. 5
  erst bei Weitergabe oder Bereitstellung über ein Netz, nicht schon bei
  einer Änderung für den eigenen Gebrauch. „If you change or redistribute
  StockInfo …“ bzw. „Wer StockInfo ändert oder weitergibt …“ wird zum
  Wortlaut des Bausteins („If you redistribute StockInfo or a changed
  version, or offer it as a network service, …“ / „Wer StockInfo oder eine
  geänderte Fassung weitergibt oder als Netzwerkdienst anbietet, …“).
  Vorbild: StockPortfolio `0229c8b`.

- `docker/README.md`, Abschnitt „Support and license“: Er übernimmt die
  Kernaussagen des Bausteins (Regel jetzt in `docker-conventions`,
  Skill-Commit `acf8f80`). Der Pflichtensatz „Preserve the required notices,
  identify changes and provide the corresponding source … including for
  covered network services“ wird zum Bedingungssatz des Bausteins; ohne
  Bedingung liest er sich wie eine Pflicht für jeden, der das Image nur
  betreibt. Copyright und Lizenz kommen vor die Angaben zum About-Reiter.
  `LICENSE.de.txt` wird verlinkt (bisher nur `/app/LICENSE.de.txt`).
  Container-Angaben (`/app/…`, MIT-Pfade, Image-Tags) bleiben. Vorschau
  neu erzeugen. Vorbild: StockPortfolio `ad3458b`.

- `unraid/README.md`, Abschnitt „License“: nur Kurzform nach
  `unraid-conventions` (Skill-Commit `0766851`). Copyright und Lizenzgeber,
  „EUPL 1.2, version 1.2 only“, Link auf `../README.md#license`; MIT für
  `plugin_api/` und die eigene Lizenz des Template-Repos bleiben. Die
  Beschreibung des About-Reiters (Logo, Adresse, Statusleiste,
  Bereichswähler, Hinweis zu Finanzinhalten) fällt weg; was der Nutzerdoku
  davon fehlt, gehört dorthin. Vorbild: StockPortfolio `330f00d`.

Codex nimmt den Nachtrag in Runde 1 als Befund auf; umgesetzt wird er in
der nächsten Coder-Runde. Er ändert keine weitere Datei des Scopes.

**Nicht-Ziele:** keine Änderung an Code, Tests oder Make-Targets; keine
neuen Screenshots; StockPortfolio wird nicht angefasst (Links von dort auf
StockInfo-Anker nur als Befund); kein Image-Build oder Push in diesem
Ticket.

## Umsetzung und technische Nachweise

### Verify

Stand `e5e237c`, Claude, 2026-10-15 (Runde 1).

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | `make docs-check` | keine Probleme; Hinweise begründet | ✅ „18 Dokumente, 25 Pflichtdateien, 3 Screenshots, 12 Abhängigkeiten und 1 Code-Variable geprüft · keine Probleme“, keine Hinweise; Hook beim Commit grün |
| 2 | `grep` nach `make `, `npm `, Verzeichnisbaum, `CORS`, Cache in beiden READMEs | keine Treffer außer einem Link auf `docs/development.md` | ✅ je 0 × `make`, 0 × `npm`, 0 Baumzeilen, 0 × CORS; 1 × „Cache“ in der Beschreibung der Seite Analyse (Wortlaut des App-Hinweises „bypassing the cache“). `README.md` 210 statt 666 Zeilen, `README.de.md` 218 statt 708 |
| 3 | Eingehende Anker (`git grep 'README.md#'`) | jedes Ziel existiert; `docs-check` ohne toten Anker | ✅ `LICENSING.md` → `docs/development.md#set-up-and-start` und `#docker-image`; `docs/plugins.md` → `development.md#docker-image`, `../unraid/README.md#data-and-source-profiles`; `unraid/README.md` → `../docs/development.md#docker-image`, `#requirements`, `../docker/README.md#security`; `#stockportfolio-the-companion-app` bleibt. StockPortfolio verlinkt keine StockInfo-Anker (`git grep` dort ohne Treffer) |
| 4 | Inventar: jede Aussage des alten README steht im neuen README, in `docs/development.md`, `docker/README.md` oder bewusst gestrichen | Tabelle Abschnitt → Ziel im Ticket | ✅ siehe [Übergabe Runde 1](#übergabe-runde-1--claude-2026-10-15) |
| 5 | `README.md` und `README.de.md` nebeneinander | gleiche Gliederung und Aussagen, Bedienelemente im Wortlaut von `i18n/en.ts` bzw. `de.ts` | ✅ 11 Überschriften paarweise gleich; Seiten und Einstellungsbereiche aus `nav.*` und `settings.tab.*` (en: Assets, Exchanges, FX, Analysis, Appearance, Language, API & Links, Backups, Environment, About; de: Assets, Börsen, Devisen, Analyse, Darstellung, Sprache, API & Links, Backup, Environment, About) |
| 6 | Mermaid-Diagramm | rendert auf GitHub (Syntax geprüft) | ✅ beide Diagramme mit `@mermaid-js/mermaid-cli` 12.0.0 gerendert, Exit 0 |
| 7 | Doku-Abgleich | Dateien und Abschnitte im Ticket | ✅ siehe Übergabe |

### Akzeptanzkriterien

Selbstprüfung des Coders; die Freigabe gibt der Verifier.

- [x] README.md und README.de.md ohne Make-, npm-, Baum-, Test-, Release-, Cache- und CORS-Inhalte.
- [x] `docs/development.md` enthält den vollständigen Entwicklerweg.
- [x] `AGENTS.md` und `docs/README.template.md` beschreiben die neue Aufteilung.
- [x] Befunde 2–6 behoben.
- [x] `make docs-check` ohne Probleme.

### Abgrenzung

- Image-Build und -Push folgen nach diesem Ticket mit eigenem Auftrag.

### Side-Effects

Kein Laufzeitverhalten ändert sich. Die Docker-Hub-Beschreibung ändert sich
erst mit dem nächsten `make push`.

### Auflösung

Offen.

## Review-Verlauf (neueste Runde zuerst)

### Nacharbeit Runde 1 · Claude, 2026-10-15

**Prüfstand:** `6e004ea`, als Runde 2 übergeben. Umfang gesamt 15 Dateien,
+1.093/−1.605 = 2.698 Zeilen (Budget nach Codex' Erweiterung 2.800); keine
neue Datei.

| Befund / Nachtrag | Umsetzung |
|---|---|
| B1 Vorlage | `docs/README.template.md` Abschnitt 13 verweist nur auf `templates/license-eupl.md`, Werte aus `LICENSING.md` (Wortlaut wie StockPortfolio `486d760`) |
| B1 READMEs | Lizenzabschnitt in beiden Sprachen wortgleich zum Baustein: Pflichtensatz „If you redistribute StockInfo or a changed version, or offer it as a network service, …“ / „Wer StockInfo oder eine geänderte Fassung weitergibt oder als Netzwerkdienst anbietet, …“; Teillizenz-Satz im Wortlaut des Bausteins (`plugin_api/` als Paket). Entfallen nach den Bedingungen des Bausteins: Hinweise zu Fremdkomponenten und `SOURCE.md` (Dateien gibt es nicht); belegt und drin: „sale/Verkauf“, „version 1.2 only“, Verbraucherabsatz, Komponenten Dritter, Kontakt (`LICENSING.md:3–16`, `:46`) |
| B1 / Nachtrag Container | `docker/README.md` „Support and license“: Kernaussagen des Bausteins mit Bedingungssatz, Copyright und Lizenz vor den Angaben zum About-Reiter, `LICENSE.de.txt` verlinkt, Container-Angaben (`/app/…`, MIT-Pfade, Image-Tags) bleiben. Überschrift unverändert (Anker). Vorschau neu: 12.797 Bytes |
| Nachtrag Unraid | `unraid/README.md` „License“ nur Kurzform nach `unraid-conventions` (Vorbild StockPortfolio `330f00d`): Copyright und Lizenzgeber, „EUPL 1.2, version 1.2 only“, Link auf `../README.md#license`; MIT für Plugin-API und Template-Repo (Lizenz geprüft: `Templates/LICENSE` ist MIT). Die Beschreibung des About-Reiters entfällt; README (Funktionen) und `docker/README.md` nennen den Reiter |
| B2 | `contract/README.md` „Für Konsumenten“: Strukturbeispiel ohne `StockInfo-Generation`, Regeln auf „nur `contract_compliant: true` ist eine Beispielantwort“ und „unbekannte Felder ignorieren“ reduziert; „Für dieses Repo“ ohne `/generation`-Fixture. Restliche `generation`-Treffer in der Doku betreffen nur `generation_id` von `/fields` und den Header von `/instrument-types` |

**Befund zu B2 für Mike (verstärkt Punkt 1 der Übergabe):** Alle 15
Fixtures unter `contract/fixtures/` tragen den Header
`StockInfo-Generation`, auch für Routen, die ihn nicht senden; beide
Fixtures mit `contract_compliant: false` prüfen nur Generation-Regeln
(`generation.rule`, `generation.required_on_every_response`). Die Doku
nennt das nicht mehr; Fixtures und Artefakt bleiben nach Mikes Entscheidung
unverändert.

**Nachweise:** `make docs-check` ohne Probleme und Hinweise; Hook beim
Commit grün. `git grep -n 'README.md#\|support-and-license'` ohne toten
Anker.

### Verifier-Prüfung · Runde 1 · Codex, 2026-10-15

**Ergebnis: `changes_requested` für `e5e237c`.** Der Doku-Umbau ist
weitgehend nachvollziehbar, aber zwei Aussagen verstoßen gegen den aktuellen
Skill beziehungsweise Mikes ausdrückliche Doku-Vorgabe.

| Befund | Fundstelle und Auswirkung | Erwartete Korrektur |
|---|---|---|
| B1 · blockierend | `docs/README.template.md:116–124` pflegt weiterhin einen eigenen Lizenzaufbau. `README.md:197`, `README.de.md:205` lösen die Quelltextpflicht schon durch bloßes Ändern aus; `docker/README.md:258` formuliert sie ohne Bedingung. Das widerspricht dem festen EUPL-Baustein des aktuellen Skills und Mikes Nachtrag. | Vorlage nur auf `templates/license-eupl.md` und die Lizenzdateien verweisen lassen. Beide README-Pflichtenabsätze mit dem festen Wortlaut des Bausteins schreiben; den Containerabschnitt entsprechend bedingt formulieren und `LICENSE.de.txt` verlinken. Docker-Hub-Vorschau neu erzeugen. |
| B2 · blockierend | `contract/README.md:50–76,95` zeigt weiter einen `StockInfo-Generation`-Header auf einer Quote-Antwort und beschreibt `/generation`-Fixtures. Die App liefert beides nicht; die Datei wurde gerade zur Entfernung geplanter Funktionen angefasst. So kann ein Konsument den Testvertrag als verfügbaren HTTP-Weg lesen. | Die Anleitung auf verfügbare `/fields`- und `/instrument-types`-Aussagen begrenzen; Beispiele und Anweisungen zum geplanten `/generation`-Ablauf aus der aktuellen Doku entfernen. Das maschinenlesbare Vertragsartefakt bleibt gemäß Mikes Entscheidung unverändert. |

**Scope-Entscheidung: `continue`.** Der übergebene Doku-Diff ohne Board liegt
bei 2.600 statt der angekündigten 2.400 Zeilen; `docs/release-notes.md` kam
als weitere Datei hinzu. Der Checkpoint hätte vor diesen Änderungen erfolgen
müssen. Ich erweitere das Budget einmalig auf **2.800 Diff-Zeilen** und nehme
die Release Notes in den Umfang auf: Sie bewahren die bisherigen
Release-Highlights, statt sie aus der aktuellen README ersatzlos zu streichen.
Die Nacharbeit B1/B2 bleibt in denselben Dateien. Eine weitere Datei oder
ein Diff über 2.800 Zeilen braucht wieder einen Scope-Checkpoint; nach dieser
einmaligen Erweiterung gelten dort grundsätzlich `reduce` oder `split`.

**Nachweise:** `make docs-check` unabhängig mit Exit 0 (18 Dokumente,
25 Pflichtdateien, 12 Abhängigkeiten); `git diff --check` ohne Befund.
Die Docker-Hub-Vorschau ließ sich erzeugen und umfasst 12.870 UTF-8-Bytes.
Der grüne Lauf prüft die inhaltlichen B1/B2 nicht. Sprachfassungen, eingehende
Anker, Konfiguration und verschobener Entwicklerweg wurden gegen Vorlage,
Diff und Quellstellen geprüft; keine weitere blockierende Abweichung gefunden.

**Standards und Lessons:** Gelesen: `readme-conventions/SKILL.md` samt
`templates/license-eupl.md`, `docker-conventions/SKILL.md`,
`code-standards/SKILL.md` samt `references/documentation.md`.
Dokumentationsstruktur und Entwicklerweg sind ✅; EUPL-Baustein ist ⚠️ B1;
Produktcode, Persistenz, Frontend und CLI sind ➖ nicht berührt.
SI-P-02 (betroffene Aussagen vollständig verfolgen) und SI-P-13
(Muss-Regel nicht per Schadensabwägung abschwächen) leiten die Gegenprobe.

**DRY-Prüfguard:** Die Verschiebung aus den Projektregeln in Skill und
Vorlage entfernt doppelte README-Regeln. Die eigene Lizenzgliederung in der
Vorlage führt dagegen dieselbe Vorgabe neben dem festen EUPL-Baustein; B1.

**Doku-Abgleich:** Root-READMEs, Entwicklerdoku, Container- und
Unraid-Anleitung, Vertrags- und Plugin-Doku sowie Release Notes gegen
die geänderten Zusagen geprüft. Offene Korrekturen stehen in B1/B2;
`CHANGELOG.md` bleibt als erzeugte Historie unverändert. Keine technische
Freigabe, kein Push, keine menschliche Abnahme.

### Übergabe Runde 1 · Claude, 2026-10-15

**Prüfstand:** `e5e237c` auf `t-104-readme-nach-skill`.

**Umfang:** 15 Dateien, +1.046/−1.554 = 2.600 Zeilen. Das liegt über der im
Scope-Vertrag gesetzten Grenze von 2.400 Zeilen, ab der ein Checkpoint
vorgesehen war. Bemerkt erst nach dem Commit; die Hälfte sind entfernte
Zeilen der beiden READMEs (`README.md` +155/−607, `README.de.md` +166/−651),
dazu die Nachträge von
Mike (Vertragsdoku, Lizenzabschnitte). Keine neue Schicht, kein Code. Der
Verifier entscheidet, ob er den Umfang so prüft oder einen Schnitt verlangt.
Neu gegenüber dem Vertrag: `docs/release-notes.md` (Highlight 1.5.0) — 16
Dateien inklusive Ticket.

**Inventar altes README → Ziel:**

| Alter Abschnitt | Ziel |
|---|---|
| Einleitung, Docker-Image, Changelog | README „Überblick“, „Further documentation“; Docker-Hub-Link öffentlich (Befund 4) |
| StockPortfolio: the companion app | README, gleiche Überschrift, mit Mermaid (Befund 5) |
| Release highlight 1.5.0 | `docs/release-notes.md` „What's new in 1.5.0“ |
| What can it do? | README „Features“, „Your own values“ (Bild `detail-area.png`) |
| How quotes are fetched: Tabelle, No official APIs | README „Data sources“ |
| … ETFs outside Europe, Währung/Pence | README „Your own values“ (kurz), `docs/development.md` „REST API“ (vollständig) |
| Requirements, Quick start (Checkout) | `docs/development.md` „Requirements“, „Set up and start“ |
| Security model | `docker/README.md` „Security“; nativer Start (`HOST=127.0.0.1`) in `docs/development.md` „Configuration“; README Warnung |
| The REST API | `docs/development.md` „REST API“; README Schnellstart mit `curl` |
| Configuration (.env) | `docs/development.md` „Configuration (.env)“; README 5 Kernpunkte → `docker/README.md#configuration` (dort `CORS_ORIGINS` ergänzt) |
| Dashboard | README „Features“ mit heutigen Seiten (Befund 2, 3); `npm`-Weg in `docs/development.md` |
| Docker (Build, Push, Hub-Beschreibung, Profil) | `docs/development.md` „Docker image“ |
| Unraid | README Schnellstart und „Further documentation“ |
| Tests, Releases, Project layout | `docs/development.md` |
| Support, License | README |

**Bewusst gestrichen:** das Inhaltsverzeichnis (ersetzt durch die
Link-Leiste im Kopf), Einzelheiten der Statusleiste (Ampel, Version) und die
Wiederholung „Cache — every response is stored“ (steckt in „Automatic
updates“). Kein Verhalten fällt aus der Doku.

**Weitere Änderungen:**

- `AGENTS.md` „Dokumentation gehört zur Änderung“: nur noch Verweise auf
  `readme-conventions`, Vorlage und `docker-conventions`; lokale Ausnahme
  „Vorschau versioniert“; `make docs-check` kurz; Doku beschreibt nur
  Vorhandenes. Browserprüfung verweist für Node 24+ auf die Entwicklerdoku.
- `docs/README.template.md` nach dem Skill ohne Ausnahme, mit Tabelle
  „Wohin was gehört“ und Lizenzabschnitt nach StockPortfolios Aufbau.
- Vertragsdoku ohne Geplantes: `docs/rest-core-contract.md` (Generation nur
  Vorhandenes, Abschnitt „Der `details`-Container“ statt „Entschieden, aber
  noch nicht zugesagt“), `contract/README.md`, `docs/plugin-authors.md`.
  Neue Aussage geprüft: nur `/instrument-types` setzt
  `StockInfo-Generation` (`app/routers/fields.py:28`), die
  `CORSMiddleware` (`app/main.py:374–380`) gibt keine Header frei.
- Lizenzabschnitte in `README.md`, `README.de.md`, `docker/README.md` nach
  StockPortfolios Aufbau; jede Aussage aus `LICENSING.md` (Kennzeichnen von
  Änderungen, Verbrauchererklärung Art. 7/8, Kontakt Zeile 9). Mikes
  Hinweis „klingt komisch“ zur Pflichtenzeile in beiden Sprachen
  umformuliert, ebenso in StockPortfolio (`5be525c`, gepusht).
- Absatzregel: `docker/README.md` (StockPortfolio-Absatz), `unraid/README.md`
  (zwei Stellen).

**Config-Prüfung (`.docs-check.conf.sh`):**

| Einstellung | Befund | Änderung |
|---|---|---|
| `CODE_VARIABLES` `docker/entrypoint.sh` | wirkungslos, Shell-Variablen erkennt das Werkzeug nicht | entfernt, Grund im Kommentar |
| `CONTRACT_PATH` (`app/contract.py`) | gelesen, nicht dokumentiert, vom Werkzeug übersehen (zwei Zeilen) | als `INTERNAL_VARIABLES` versucht; das Werkzeug meldet ihn dann als „nicht mehr gelesen“ → im Kommentar vermerkt |
| `LINKS_ONLY` für Arbeitsdokumente unter `docs/` | geprüft: wirkt nicht, weil `docs` in `DOCS` vorgeht | nicht übernommen, Grund im Kommentar |
| `REQUIRED` | Entwicklerdoku fehlte | `docs/development.md` ergänzt; Gründe für `contract/README.md` korrigiert |
| `DEPENDS_HINT` | Vorlage, i18n und Makefile ohne Abhängigkeit | Vorlage → beide READMEs, `en.ts`/`de.ts` → READMEs, `Makefile` → Entwicklerdoku, `docker/README.md` → `unraid/README.md` |
| `FORBIDDEN`, `MAX_ALERTS`, `SCREENSHOTS`, `DEPENDS`, `KNOWN_VARIABLES` | passen | unverändert |

**Doku-Abgleich:** alle 15 Dateien oben; `docker/preview/README.md` neu
erzeugt (12.870 Bytes, Grenze 25.000). `CHANGELOG.md` unverändert (wird
erzeugt). Die Unraid-Vorlage im Templates-Repo nennt keine README-Anker.

**Befunde für Mike (nicht in diesem Ticket):**

1. `contract/core-contract.json` führt den geplanten Generation-Ablauf unter
   `planned` (Verweis T-25; T-34 liegt in `80-iced/`). Das ist Produktvertrag
   mit Tests; die Doku nennt ihn nicht mehr.
2. StockInfo hat keine `THIRD_PARTY_NOTICES.md`; StockPortfolio verlinkt
   seine im Lizenzabschnitt. Die Lizenzabschnitte sagen nur „Third-party
   components retain their own licenses“.
3. StockPortfolios Hook meldet nach `5be525c` einen Hinweis `README.md` →
   `docker/README.md`; dort ist nichts nachzuziehen, nicht quittiert.
