# T-106 · About-Punkt in der Container-Anleitung kürzen

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
`330f00d`. Aktiviert wird es nach T-105.

## Scope-Vertrag

**Beobachtbares Ergebnis:** Der About-Punkt in `docker/README.md` ist ein
Satz; die Docker-Hub-Vorschau ist neu erzeugt.

**Fachliche Änderung:** eine. **Dateien:** `docker/README.md`,
`docker/preview/README.md`. **Diff-Budget:** unter 30 Zeilen ohne
`_tickets/`.

**Neuer Wortlaut:**

> - An **About** tab under Settings, also linked from the status bar, explains
>   the limits of the displayed data and links to the license documents.

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

### Akzeptanzkriterien

- [ ] About-Punkt in einem Satz, Vorschau aktuell.
- [ ] `make docs-check` ohne Probleme.

### Side-Effects

Die Docker-Hub-Beschreibung ändert sich erst mit dem nächsten `make push`.

### Auflösung

Offen.

## Review-Verlauf (neueste Runde zuerst)

Noch keine Übergabe.
