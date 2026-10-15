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
| 1 | Neuer Satz gegen `dashboard/src/i18n/en.ts` (`about.*`) und die Statusleiste | Aussagen stimmen | ➖ |
| 2 | Vorschau neu erzeugen, `make docs-check` | keine Probleme, Vorschau unter 25.000 Bytes | ➖ |
| 3 | Doku-Abgleich | READMEs nennen den About-Reiter; nichts Nötiges geht verloren | ➖ |
| 4 | `grep` nach `dev-ports`, `setup-libs`, `DEV_MAKE`, `BASH_LIBS` in `docs/development.md` | keine Erklärung der Werkzeuge mehr; genutzte Befehle bleiben | ➖ |

### Akzeptanzkriterien

- [ ] About-Punkt in einem Satz, Vorschau aktuell.
- [ ] `make docs-check` ohne Probleme.

### Side-Effects

Die Docker-Hub-Beschreibung ändert sich erst mit dem nächsten `make push`.

### Auflösung

Offen.

## Review-Verlauf (neueste Runde zuerst)

Noch keine Übergabe.
