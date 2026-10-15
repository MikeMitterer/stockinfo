# T-106 · Container-Anleitung und Entwicklerdoku kürzen

**Warum dieses Ticket:** `docker/README.md` beschreibt unter „What you get“
den About-Reiter mit Logo, Postadresse, Website-Link, dem Hinweis zu
Finanzinhalten und dem Bereichswähler auf schmalen Bildschirmen. Das ist
Oberflächendetail, das nicht in eine Container-Anleitung gehört; die
Docker-Hub-Beschreibung wird dadurch länger, ohne dem Betreiber zu helfen.

**Beispiel:** Heute fünf Zeilen über Logo und Adresse neben dem About-Text.
Danach ein Satz: Der Reiter erklärt die Grenzen der angezeigten Daten und
verlinkt die Lizenzdokumente.

**Stand:** Auf Mikes Auftrag vom 2026-10-15 in `20-ready/` angelegt
(Vorschlag der StockPortfolio-Sitzung `stockportfolio-97`, von Mike
bestätigt: „Ja, der ist auch von mir“). Vorbild: StockPortfolio `ad3458b`,
`330f00d`. Nach der Freigabe von T-105 aktiviert (2026-10-15) auf
`t-106-doku-kuerzen`, Coder `claude`, Verifier `codex`.

## Scope-Vertrag

**Beobachtbares Ergebnis:** Der About-Punkt in `docker/README.md` ist ein
Satz; die Docker-Hub-Vorschau ist neu erzeugt.

**Fachliche Änderungen (zwei):** About-Punkt kürzen; in der
Entwicklerdoku keine gemeinsamen Werkzeuge erklären (Regel „Nur die eigene
Anwendung“ in `readme-conventions`, Skill-Commit `0ac008a`).

**Dateien:** `docker/README.md`, `docker/preview/README.md`,
`docs/development.md`. **Diff-Budget:** unter 40 Zeilen ohne `_tickets/`.

**Neuer Wortlaut `docker/README.md`:**

> - An **About** tab under Settings, also linked from the status bar, explains
>   the limits of the displayed data and links to the license documents.

**`docs/development.md`, Nachtrag Mike, 2026-10-15** („Ja, beide mit in
T-106“):

1. „Set up and start“, `make dev-down`: der Halbsatz „It uses `dev-ports.sh`
   from ProjectTools with the ports in `.dev-ports.conf.sh`,“ entfällt
   (Vorschlag `stockportfolio-97`). Danach: „… frees ports 5173 and 8000.
   It only ends your own processes inside this project and can be run as
   often as you like.“
2. „Requirements“: Der Absatz, wie `scripts/setup-libs.sh` MakeLib, BashLib
   und ProjectTools über `DEV_MAKE`, `BASH_LIBS` und `PROJECT_TOOLS` findet,
   wird zu einem Satz: „For the maintainer, `make setup` also links the
   shared libraries under `.libs/`.“ Was die Docker-Image-Zeile dort sagt
   („The Docker image needs none of this“), bleibt, wenn es weiter zutrifft.

Befehle, die das Projekt nutzt (`dockerhub-readme.sh`, `changelog.py`),
bleiben.

**Mechanische Folge, beim Aktivieren ergänzt (Claude, 2026-10-15):** Der
Skill `readme-conventions` heißt jetzt `docs-conventions`
(`~/.claude/skills/docs-conventions`, Baustein unverändert unter
`templates/license-eupl.md`). Vier Verweise ziehen mit: `AGENTS.md:145`,
`docs/README.template.md:15` und `:118`, `.docs-check.conf.sh:158`. Damit
kommen diese drei Dateien in den Umfang (6 statt 3); reine Umbenennung,
keine neue Regel. Budget bleibt unter 40 Zeilen.

**Nicht-Ziele:** keine Änderung an READMEs oder Oberfläche. Fehlt der
Nutzerdoku danach etwas aus der gestrichenen Beschreibung, wird es dort
ergänzt; das prüft der Doku-Abgleich.

## Umsetzung und technische Nachweise

### Verify

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | Neuer Satz gegen `dashboard/src/i18n/en.ts` (`about.*`) und die Statusleiste | Aussagen stimmen | ✅ Grenzen der Daten: `about.intro`, `about.use`; Lizenzdokumente: `about.licenseLink`, `about.licensingLink`; Statusleiste: `status.about` „About StockInfo“ |
| 2 | Vorschau neu erzeugen, `make docs-check` | keine Probleme, Vorschau unter 25.000 Bytes | ✅ Vorschau 11.732 Bytes; `make docs-check` ohne Probleme und Hinweise nach Quittung |
| 3 | Doku-Abgleich | READMEs nennen den About-Reiter; nichts Nötiges geht verloren | ✅ `README.md`/`README.de.md` „Settings … About“ unter Funktionen; Logo, Adresse und Bereichswähler sind Oberflächendetail (Regel in `docs-conventions`: gehört in einen User Guide, den StockInfo nicht hat) |
| 4 | `grep` nach `dev-ports`, `setup-libs`, `DEV_MAKE`, `BASH_LIBS` in `docs/development.md` | keine Erklärung der Werkzeuge mehr; genutzte Befehle bleiben | ✅ keine Treffer; `dockerhub-readme.sh` und `changelog.py` stehen weiter als genutzte Befehle |
| 5 | `git grep readme-conventions` außerhalb `_tickets/` | kein Treffer | ✅ kein Treffer |

### Akzeptanzkriterien

Selbstprüfung des Coders; die Freigabe gibt der Verifier.

- [x] About-Punkt in einem Satz, Vorschau aktuell.
- [x] `make docs-check` ohne Probleme.

### Side-Effects

Die Docker-Hub-Beschreibung ändert sich erst mit dem nächsten `make push`.

### Auflösung

Offen.

## Review-Verlauf (neueste Runde zuerst)

### Übergabe Runde 1 · Claude, 2026-10-15

**Prüfstand:** `b5f641c` (Produkt `35d9761`, Quittung `b5f641c`) auf
`t-106-doku-kuerzen`. 7 Dateien, +15/−20 = 35 Zeilen (Budget 40).

- `docker/README.md`: About-Punkt im Wortlaut aus dem Scope-Vertrag;
  Vorschau neu.
- `docs/development.md`: `make dev-down` ohne `dev-ports.sh`;
  „Requirements“ ohne `setup-libs.sh` und die Fundvariablen.
- Umbenennung `readme-conventions` → `docs-conventions` in `AGENTS.md`,
  `docs/README.template.md` (2 ×), `.docs-check.conf.sh`. In `AGENTS.md`
  zusätzlich „Schreibregeln der READMEs“ → „der Projektdoku“, weil der
  Skill jetzt die ganze Projektdoku regelt. Tickets unter `_tickets/`
  behalten den alten Namen als Verlauf.
- Quittiert: `docs/README.template.md` → `README.md`/`README.de.md` (nur
  Skill-Name), `docker/README.md` → `unraid/README.md` (Unraid beschreibt den
  Reiter nicht).

Code-Standards: ➖ kein Code; Dokumentation ✅. DRY: Die Regeln stehen in
`docs-conventions` und `docker-conventions`; die Doku wiederholt sie nicht.
