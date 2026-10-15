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
| 1 | Inhalt gegen die Quellen | Herkunft, Copyright und Lizenztext wörtlich aus den genannten LICENSE-Dateien | ➖ |
| 2 | `make build` | Build grün, Lizenzprüfung nennt `THIRD_PARTY_NOTICES.md` | ➖ |
| 3 | Gegenprobe: Datei im Image weicht ab oder fehlt | Prüfung schlägt mit Exit ≠ 0 fehl | ➖ |
| 4 | `make docs-check` | keine Probleme; Sprachfassungen gleich | ➖ |
| 5 | Doku-Abgleich | Lizenzabschnitte, Container- und Entwicklerdoku | ➖ |

### Akzeptanzkriterien

- [ ] `THIRD_PARTY_NOTICES.md` mit den drei Komponenten.
- [ ] Datei im Image, von `make build` geprüft.
- [ ] Lizenzabschnitte und Anleitungen verlinken bzw. nennen sie.
- [ ] `make docs-check` ohne Probleme.

### Abgrenzung

StockPortfolio nutzt dieselben Schriften über `@mmit/ux-foundation`, seine
`THIRD_PARTY_NOTICES.md` nennt sie nicht; das ist ein Befund für Mike, keine
Änderung hier.

### Side-Effects

Das nächste Image enthält eine Datei mehr unter `/app`.

### Auflösung

Offen.

## Review-Verlauf (neueste Runde zuerst)

Noch keine Übergabe.
