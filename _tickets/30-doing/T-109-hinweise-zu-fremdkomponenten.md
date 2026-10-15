# T-109 · Hinweise zu Fremdkomponenten (THIRD_PARTY_NOTICES.md)

**Warum dieses Ticket:** StockInfo liefert im Dashboard und damit im
Docker-Image Material anderer Urheber aus, nennt es aber nirgends. Die
Lizenzen verlangen, dass Copyright-Hinweis und Lizenztext mitgegeben werden.
StockPortfolio führt dafür eine `THIRD_PARTY_NOTICES.md`; der Lizenzbaustein
von `docs-conventions` verlinkt sie in der Details-Zeile.

**Beispiel:** Das GitHub-Symbol in der Statusleiste ist das Feather-Icon
„github“ (MIT). Wer das Image weitergibt, gibt diesen Pfad mit weiter, aber
keinen MIT-Hinweis dazu.

**Stand:** Auf Mikes Auftrag vom 2026-10-15 („5 - ja“, „erledige erst
T-109“) angelegt und aktiviert. Coder `claude`, Verifier `codex`, Branch
`t-109-fremdkomponenten`.

## Inventar (2026-10-15)

Gesucht wurde nach Fremdmaterial, das StockInfo selbst ausliefert, nicht nach
Abhängigkeiten, die ihre Lizenzdateien mitbringen (Python-Pakete im Image
behalten ihre `*.dist-info`-Lizenzen):

| Material | Fundstelle | Herkunft und Lizenz | Beleg |
|---|---|---|---|
| GitHub-Symbol | `dashboard/src/components/StatusBar.vue:83–85` | Feather `icons/github.svg`, MIT, Copyright (c) 2013-2023 Cole Bemis; Pfad mit gerundeten, leicht verschobenen Koordinaten | gleiche Befehlsfolge wie `raw.githubusercontent.com/feathericons/feather/main/icons/github.svg`; eingeführt mit `11e77fa` ohne Herkunftsvermerk |
| Schrift Inter | Dashboard-Build (`inter-latin-wght-normal-*.woff2`) | `@fontsource-variable/inter` über `@mmit/ux-foundation`, SIL Open Font License 1.1, Copyright 2016 The Inter Project Authors | `dashboard/node_modules/@fontsource-variable/inter/LICENSE` |
| Schrift Space Grotesk | Dashboard-Build (`space-grotesk-latin-wght-normal-*.woff2`) | `@fontsource-variable/space-grotesk` über `@mmit/ux-foundation`, SIL OFL 1.1, Copyright 2020 The Space Grotesk Project Authors | `…/space-grotesk/LICENSE` |

Nicht aufgenommen: Navigations-Icons (aus `@mmit/ux-foundation`, Mikes
eigene Bibliothek); Swagger UI (lädt FastAPI zur Laufzeit vom CDN, nicht im
Repo und nicht im Image); `mangolila-logo-*`, `logo.*`, `stockinfo-icon.*`
(eigene Marken). Keine Fundstelle mit „copied from“, SPDX oder fremdem
Copyright im Quelltext (`git grep` über `app`, `dashboard/src`,
`dashboard/public`, `plugin_api/src`, `scripts`, `docker`, `examples`).

## Scope-Vertrag

**Beobachtbares Ergebnis:** `THIRD_PARTY_NOTICES.md` nennt die drei
Komponenten mit Herkunft und vollem Lizenztext; die Datei liegt im Image
unter `/app/THIRD_PARTY_NOTICES.md` und wird von `make build` geprüft; die
Lizenzabschnitte verlinken sie.

**Fachliche Änderungen (drei):**

1. `THIRD_PARTY_NOTICES.md` anlegen (Aufbau wie StockPortfolio).
2. Ins Image aufnehmen: `docker/Dockerfile` (COPY und Prüfung),
   `docker/build.sh` (beide Lizenzlisten).
3. Doku: Details-Zeile in `README.md`/`README.de.md` nach dem
   EUPL-Baustein, `LICENSING.md`, `docker/README.md` (Dateien im Image),
   `docs/development.md` (was `make build` kopiert), Vorschau;
   `.docs-check.conf.sh` (`REQUIRED`, `DEPENDS` von `LICENSING.md`).

**Erwartete Dateien:** 2 Produkt (`docker/Dockerfile`, `docker/build.sh`),
8 Doku/Config (`THIRD_PARTY_NOTICES.md`, `README.md`, `README.de.md`,
`LICENSING.md`, `docker/README.md`, `docker/preview/README.md`,
`docs/development.md`, `.docs-check.conf.sh`).

**Diff-Budget:** unter 250 Zeilen (die beiden Lizenztexte machen rund 120
aus).

**Nachweis:** `make build` (nur lokal, kein Push) mit der Lizenzprüfung im
Image; Gegenprobe: abweichende Datei → Build-Prüfung schlägt fehl.

**Nicht-Ziele:** keine Lizenzinventur aller npm- und Python-Abhängigkeiten;
keine neue Schrift- oder Icon-Quelle; kein Push des Images. Die Lizenzliste
steht heute dreimal (Dockerfile, zweimal in `build.sh`); sie wird hier nur
ergänzt, eine Zusammenführung ist ein eigener Befund.

## Umsetzung und technische Nachweise

### Verify

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
Stand `9d4f4b1`, Claude, 2026-10-15.

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | Inhalt gegen die Quellen | Herkunft, Copyright und Lizenztext wörtlich aus den genannten LICENSE-Dateien | ✅ Python-Vergleich der beiden ```` ```text ````-Blöcke: MIT gleich `feathericons/feather/main/LICENSE`, OFL gleich `@fontsource-variable/space-grotesk/LICENSE` ab Zeile 3; Inter und Space Grotesk ab Zeile 3 identisch |
| 2 | `make build` | Build grün, Lizenzprüfung nennt `THIRD_PARTY_NOTICES.md` | ✅ `mangolila/stockinfo:1.5.0-261015.1757.1d3ad.ahead116`: „6 Lizenzdokumente und OCI-Labels stimmen“; `sha256sum /app/THIRD_PARTY_NOTICES.md` im Image = Repository (`902513c7…`) |
| 3 | Gegenprobe: Datei im Image weicht ab oder fehlt | Prüfung schlägt mit Exit ≠ 0 fehl | ✅ M1 Datei fehlt im Repository → „Lizenz fehlt oder ist leer“, Exit 1; M2 Dockerfile kopiert sie nicht → `RUN test -s /app/THIRD_PARTY_NOTICES.md` scheitert, Exit 1; M3 Datei im Image verändert → „Lizenz weicht ab: THIRD_PARTY_NOTICES.md“, Exit 1. Alle mit `STRICT=0`, danach zurückgesetzt und sauber neu gebaut |
| 4 | `make docs-check` | keine Probleme; Sprachfassungen gleich | ✅ 19 Dokumente, 26 Pflichtdateien, 1 Sprachfassung, keine Probleme |
| 5 | Doku-Abgleich | Lizenzabschnitte, Container- und Entwicklerdoku | ✅ siehe Übergabe |

### Akzeptanzkriterien

Selbstprüfung des Coders; die Freigabe gibt der Verifier.

- [x] `THIRD_PARTY_NOTICES.md` mit den drei Komponenten.
- [x] Datei im Image, von `make build` geprüft.
- [x] Lizenzabschnitte und Anleitungen verlinken bzw. nennen sie.
- [x] `make docs-check` ohne Probleme.

### Abgrenzung

StockPortfolio nutzt dieselben Schriften über `@mmit/ux-foundation`, seine
`THIRD_PARTY_NOTICES.md` nennt sie nicht; das ist ein Befund für Mike, keine
Änderung hier.

### Side-Effects

Das nächste Image enthält eine Datei mehr unter `/app`.

### Auflösung

Offen.

## Review-Verlauf (neueste Runde zuerst)

### Verifier-Prüfung · Runde 1 · Codex, 2026-10-15

**Ergebnis: `changes_requested` für `9d4f4b1`.** Ein blockierender
Inhaltsbefund bleibt bei der zugesagten vollständigen Übernahme der
Fremdlizenz-Hinweise.

| Befund | Fundstelle und Auswirkung | Erwartete Korrektur |
|---|---|---|
| B1 · unvollständiger Inter-Copyright-Hinweis | `dashboard/node_modules/@fontsource-variable/inter/LICENSE:1` enthält nach „Copyright 2016 The Inter Project Authors“ zusätzlich `Inter-Italic[opsz,wght].ttf: Copyright 2016 The Inter Project Authors (https://github.com/rsms/inter)`. `THIRD_PARTY_NOTICES.md:48` lässt diesen Teil weg. Der Coder hat nur den gemeinsamen Lizenztext ab Zeile 3 verglichen; damit blieb gerade der unterschiedliche Copyright-Kopf ungeprüft. Die Datei verspricht, die Hinweise der ausgelieferten Schrift vollständig mitzugeben. | Den Copyright-Hinweis für Inter vollständig aus der installierten Paketlizenz übernehmen und den gesamten Kopf jeder Schriftlizenz gegen die zugehörige Paketdatei prüfen. Die gemeinsame OFL-Fassung kann einmal stehen bleiben. |

**Nachweise:** Die installierten Fontsource-Pakete sind beide Version 5.3.0
und deklarieren `OFL-1.1`; der Textvergleich der Inter-Kopfzeile zeigt den
fehlenden Teil. Die [Feather-Lizenz](https://github.com/feathericons/feather/blob/master/LICENSE)
bestätigt MIT und Cole Bemis als Quelle. `make docs-check` lief unabhängig
mit Exit 0 (19 Dokumente, 26 Pflichtdateien); `bash -n docker/build.sh`
und `git diff --check 2bddbc3..9d4f4b1` waren grün. Diese Prüfungen
vergleichen den Copyright-Kopf nicht. Den Docker-Build habe ich wegen des
inhaltlichen Blockers nicht wiederholt; seine Funktionsnachweise und drei
roten Gegenproben stehen in der Coder-Übergabe.

**Doku- und Standardabgleich:** Root-READMEs, LICENSING.md, Container- und
Entwicklerdoku nennen die neue Datei konsistent. Die Bash-Änderung bündelt
die Lizenzliste innerhalb von `build.sh`; Dockerfile und Build-Prüfung
enthalten den neuen Pfad. Keine Produktänderung durch den Verifier, keine
menschliche Abnahme und kein Push.

### Übergabe Runde 1 · Claude, 2026-10-15

**Prüfstand:** `9d4f4b1` (Produkt `a3faa7f`, `1d3ad0b`; Quittung
`9d4f4b1`) auf `t-109-fremdkomponenten`. 11 Dateien, +179/−14 = 193 Zeilen
(Budget 250). Gegenüber dem Vertrag zusätzlich `.docs-check.ack`.

**Änderungen:**

- `THIRD_PARTY_NOTICES.md` neu: Feather `github` (MIT), Inter und Space
  Grotesk (SIL OFL 1.1, Fontsource 5.3.0), je Herkunft, Copyright und
  Lizenztext.
- `docker/Dockerfile`: `COPY` und `test -s` um die Datei ergänzt.
- `docker/build.sh`: `readonly LICENSE_FILES=(…)` einmal oben; beide
  Schleifen (`prepareConfig`, `verifyBuiltImage`) nutzen sie; die
  Erfolgsmeldung zählt die Liste statt fest „fünf“ (`1d3ad0b`, beim ersten
  Build aufgefallen). Das Dockerfile führt die Dateien weiter selbst, weil es
  keine Bash-Variable lesen kann; der Kommentar an `LICENSE_FILES` nennt das.
- Doku: Details-Zeile beider READMEs nach dem EUPL-Baustein; `LICENSING.md`
  (Verweis bei den Fremdkomponenten, Datei im Image); `docker/README.md`
  (Dateien im Image), Vorschau neu (11.867 Bytes); `docs/development.md`
  (was `make build` kopiert); `.docs-check.conf.sh` (`DOCS`, `REQUIRED`).

**Code-Standards** (`code-conventions`, `references/shell.md`): Bash-
Konstante groß und `readonly`, Array in Anführungszeichen expandiert;
`bash -n` grün, ShellCheck ohne Meldung zu den neuen Zeilen (die übrigen
Meldungen sind alt). DRY: Die doppelte Liste in `build.sh` ist
zusammengeführt; Dockerfile bleibt notwendiges Wiring.

**Doku-Abgleich:** `README.md`, `README.de.md` (Lizenz), `LICENSING.md`,
`docker/README.md`, `docs/development.md` geändert; `unraid/README.md`
unverändert (nennt die Dateien im Image nicht, Hinweis quittiert).

**Befund für Mike:** StockPortfolio bindet dieselben Schriften über
`@mmit/ux-foundation` ein; seine `THIRD_PARTY_NOTICES.md` nennt nur
Codicons und Lucide.
