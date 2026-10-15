# T-111 · Doku an den geänderten Skill `docs-conventions` anpassen

**Warum dieses Ticket:** `docs-conventions` verlangt jetzt für längere
Dokumente (ab drei Abschnitten) eine Übersicht am Anfang und nach jedem
Abschnitt einen Rücksprung. Für das Schreiben verweist der Skill auf
`textgestaltung`, unter anderem: Befehle, die der Leser ausführen soll, stehen
in eigenen Codeblöcken. Außerdem bleibt die Kernaussage vor Ort; verlinkt
werden nur Einzelheiten. `make docs-check` prüft keine dieser Regeln und
meldet deshalb nichts.

**Beispiel:** `docker/README.md` hat zehn Abschnitte ohne Übersicht und
schreibt „Start it with `docker compose up -d`“ als Inline-Code im Satz.

**Stand:** Auftrag von Mike, 2026-10-15: „Schau dir make docs-check an -
docs-conventions hat sich geändert überprüft die Files auf die sicher der
Skill anwenden läßt und passe das jeweilige File an den Skill an“. Aktiv auf
`t-111-doku-nach-skill`, Coder `claude`, Verifier `codex`.

## Inventar

`make docs-check` vor der Änderung: keine Probleme, keine Hinweise.

Übersicht (`## Übersicht`/`## Contents`) und Rücksprünge je Dokument aus
`DOCS` in `.docs-check.conf.sh`, gezählt über `## `-Überschriften:

| Dokument | Abschnitte | Übersicht | Rücksprünge | Befund |
|---|---|---|---|---|
| `README.md` | 9 | nein | 0 | fehlt |
| `README.de.md` | 9 | nein | 0 | fehlt |
| `docker/README.md` | 10 | nein | 0 | fehlt |
| `unraid/README.md` | 8 | ja | 7 | vollständig |
| `docs/development.md` | 10 | ja | 9 | vollständig |
| `docs/plugins.md` | 6 | nein | 0 | fehlt |
| `docs/release-notes.md` | 4 | nein | 0 | fehlt |
| `docs/plugin-authors.md` | 11 | ja | 9 | ein Rücksprung fehlt |
| `docs/rest-core-contract.md` | 12 | ja | 11 | vollständig |
| `contract/README.md` | 4 | ja | 3 | vollständig |
| `LICENSING.md` | 4 | ja | 3 | vollständig |
| `THIRD_PARTY_NOTICES.md` | 2 | — | — | kürzer als drei Abschnitte |

Befehle als Inline-Code, die der Leser ausführen soll (Suche nach
Befehlsanfängen außerhalb von Codeblöcken; bloß erwähnte Befehlsnamen wie
„`make help` lists …“ bleiben Inline-Code):

- `docker/README.md`: `docker compose up -d`, `docker logs --tail=100 stockinfo`.
- `unraid/README.md`: `docker logs --tail=100 stockinfo`.
- `docs/development.md`: `cp .env.example .env`, `docker build -f …`,
  `make changelog PYTHON=…`, `python3 … changelog.py --publish`; weitere
  Stellen beim Umsetzen im Zusammenhang prüfen.

## Scope-Vertrag

**Im Umfang:** die Dokumente aus der Skill-Tabelle (`README.md`,
`README.de.md`, `docs/development.md`, `docker/README.md`,
`unraid/README.md`) und die Nutzerdokumente, die die Projektvorlage als
Ziel nennt (`docs/plugins.md`, `docs/plugin-authors.md`,
`docs/rest-core-contract.md`, `docs/release-notes.md`).

1. Übersicht und Rücksprünge nach `references/navigation.md` des Skills, wo
   sie fehlen. Englische Dokumente mit `## Contents` und `[↑ Contents]`,
   deutsche mit `## Übersicht`/`[↑ Übersicht]`, wie die vorhandenen.
2. Auszuführende Befehle in eigene Codeblöcke mit Sprachkennung.
3. Beim Durchgehen sichtbare Verstöße gegen `textgestaltung` in diesen
   Dateien (Absatz je Gedankenwechsel, Kernaussage zuerst, Fettdruck nur
   gezielt) beheben, ohne Aussagen zu ändern.
4. `docs/README.template.md`: Übersicht nach dem Kopf in die Abschnittsliste
   aufnehmen, damit die Vorlage dem Skill nicht widerspricht.
5. Doku-Abgleich der Sprachfassungen (`TRANSLATIONS`) und der
   Docker-Hub-Grenze (25.000 Byte, `dockerhub-readme.sh --preview`).

**Nicht im Umfang:** neue Inhalte, Umbau der Gliederung,
Arbeitsdokumente (`docs/stockinfo-currency-request.md`,
`docs/stockportfolio-quote-projection-review.md`, `docs/markdown-styles/`),
historische Entwürfe unter `docs/superpowers/`, Änderungen an
`docs-check` selbst.

**Abnahme:** jedes Dokument im Umfang mit mindestens drei Abschnitten hat
Übersicht und nach jedem Abschnitt einen Rücksprung (Zählung wie oben);
keine auszuführenden Befehle mehr als Inline-Code; `make docs-check` ohne
Problem; Docker-Hub-Vorschau unter der Grenze.

## Review-Verlauf (neueste Runde zuerst)

### Übergabe Runde 1 · Claude, 2026-10-15

Prüffassung `dcd735d`.

**Umgesetzt:**

1. Übersicht und Rücksprünge neu in `README.md`, `README.de.md` (nach der
   Warnung, vor „Features“/„Funktionen“), `docker/README.md`,
   `docs/plugins.md` (`## Übersicht`) und `docs/release-notes.md` (die
   vorhandene Linkliste steht jetzt unter `## Contents`). In
   `docs/plugin-authors.md` fehlte der Rücksprung nach Abschnitt 2.
   Zählung danach: In jedem Dokument im Umfang ist die Zahl der
   Rücksprünge gleich der Zahl der `##`-Abschnitte ohne die Übersicht.
2. Befehle in eigene Codeblöcke: `docker compose up -d` und
   `docker logs --tail=100 stockinfo` (`docker/README.md`), `docker logs …`
   (`unraid/README.md`), `docker build …`, `make changelog PYTHON=…`,
   `python3 … changelog.py --publish` (`docs/development.md`). Der Verweis
   auf das Anlegen von `.env` in „Configuration (.env)“ zeigt jetzt auf
   Schritt 1 der Einrichtung, wo der Befehl schon als Block steht. Bloß
   erwähnte Befehlsnamen bleiben Inline-Code, ebenso das bedingte
   `make up DATA_VOLUME=other-volume`.
3. Absätze nach Gedankenwechsel getrennt: Verweis auf Quellenkonfiguration,
   Verantwortung des Betreibers und „To avoid them“ in beiden READMEs;
   Host-Port und Logs/Healthcheck in `docker/README.md`. Kein Satz
   inhaltlich geändert.
4. `docs/README.template.md`: Anweisung „Übersicht“ zwischen Abschnitt 3
   und 4.

**Doku-Abgleich:** `README.md` und `README.de.md` gleich gegliedert
(`TRANSLATIONS` grün). `docker/README.md` und `README.md` stimmen in den
gemeinsamen Aussagen weiter überein; nur Gliederung und Absätze geändert.
`docker/preview/README.md` neu erzeugt, 12.626 Byte (Grenze 25.000).
`unraid/README.md`, `docs/development.md`, `docs/rest-core-contract.md`,
`contract/README.md`, `LICENSING.md` hatten Übersicht und Rücksprünge schon
vollständig. `THIRD_PARTY_NOTICES.md` hat nur zwei Abschnitte.
`docs/README.template.md` selbst hat keine Übersicht: Es ist eine
Arbeitsanweisung für den Agenten, kein Leserdokument.

**Nachweise:** `make docs-check` vorher und nachher ohne Problem und ohne
Hinweis; `dockerhub-readme.sh --preview` grün. `make docs-check` prüft die
neuen Skill-Regeln nicht; die Zählung oben ist von Hand per `grep`.
