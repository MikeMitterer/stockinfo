# T-108 · Lokale Vorschau-Ausnahme aus AGENTS.md streichen

**Warum dieses Ticket:** `AGENTS.md` führt eine „Lokale Ausnahme zu
`docker-conventions`“: Die Vorschau `docker/preview/README.md` sei
versioniert und gehöre in denselben Commit wie `docker/README.md`. Der Skill
sagt das inzwischen selbst (`docker-conventions`, Abschnitt „Beschreibung
nach Docker Hub übertragen“, Skill-Commit `f41299c`). Als Ausnahme ist der
Absatz falsch, als Wiederholung überflüssig.

**Beispiel:** Ein Agent liest „Lokale Ausnahme“ und sucht im Skill die
abweichende Regel, die es nicht mehr gibt.

**Stand:** Auf Mikes Auftrag vom 2026-10-15 angelegt und aktiviert
(Vorschlag der StockPortfolio-Sitzung `stockportfolio-97`, von Mike
bestätigt: „Ja, der ist auch von mir“). Coder `claude`, Verifier `codex`,
Branch `t-108-vorschau-ausnahme`.

## Scope-Vertrag

**Beobachtbares Ergebnis:** `AGENTS.md` enthält keine Ausnahme zur
Docker-Hub-Vorschau mehr; der Verweis auf `docker-conventions` im Absatz
davor bleibt.

**Fachliche Änderung:** eine. **Datei:** `AGENTS.md`. **Diff-Budget:**
unter 10 Zeilen.

**Nicht-Ziele:** keine Änderung an `.docs-check.conf.sh` (dort bleibt
`DEPENDS` mit Frist 0 als technische Prüfung) und an der Doku.

## Umsetzung und technische Nachweise

### Verify

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | `docker-conventions` nennt Versionierung und denselben Commit | Fundstelle im Skill | ➖ |
| 2 | `grep -n 'Lokale Ausnahme' AGENTS.md` | kein Treffer | ➖ |
| 3 | `make docs-check` | keine Probleme | ➖ |

### Akzeptanzkriterien

- [ ] Absatz entfernt, sonst nichts geändert.
- [ ] `make docs-check` ohne Probleme.

### Auflösung

Offen.

## Review-Verlauf (neueste Runde zuerst)

Noch keine Übergabe.
