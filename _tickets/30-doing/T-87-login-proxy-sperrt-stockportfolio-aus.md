# T-87 · Login-Proxy vor StockInfo sperrt StockPortfolio aus

StockInfos Anleitungen und Unraid-Vorlage empfehlen seit T-84 drei
gleichwertige Wege für den Zugriff von außen: LAN, VPN oder ein
**Reverse Proxy mit HTTPS und Login**. Für StockInfo allein stimmt das.
Wer StockInfo als Kursquelle für StockPortfolio betreibt, folgt dem dritten
Weg aber in eine Sackgasse: StockPortfolio bekommt dann keine Kurse mehr.

**Beispiel:** Ein Unraid-Nutzer betreibt beide Apps und will sie von unterwegs
erreichen. Er folgt der StockInfo-Vorlage und setzt StockInfo hinter einen
Proxy mit Basic-Auth oder einer SSO-Anmeldung (etwa Authelia). Das
StockInfo-Dashboard funktioniert nach der Anmeldung. In StockPortfolio bleibt
die Kurstabelle leer; im Browser stehen 401-Antworten oder CORS-Fehler.

**Stand:** Gemeldet aus StockPortfolio am 2026-10-01 (Mikes Auftrag).
Mike hat T-87 am selben Tag aktiviert („T-87 wird damit aktiv“). Coder
`claude`, Verifier `codex`; maßgeblich ist `STATUS.md`. Für Mike ist
aktuell kein Handgriff nötig.

## Scope-Vertrag (Claude, 2026-10-01)

**Ursache bestätigt:** StockInfo erlaubt CORS ohne Zugangsdaten
(`app/main.py`: `allow_credentials=False`). StockPortfolio ruft `fetch`
ohne `credentials`-Option auf, also mit dem Standard `same-origin`. Bei
einem Aufruf über Origins hinweg schickt der Browser weder Cookie noch
Basic-Auth mit. Ein Login-Proxy vor einem eigenen StockInfo-Host
blockiert StockPortfolio deshalb immer.

**Umfang nach Mikes Vorgaben vom 2026-10-01:**

- „Stelle einfach die Beschreibung, den Text richtig“: kein Prüf-Script,
  kein Proxy-Aufbau.
- „Die Grundaussage ist, dass der User StockInfo nicht im Internet laufen
  lassen soll, sondern entweder im LAN oder per VPN oder WireGuard“: Der
  Reverse Proxy mit Login entfällt als empfohlener Weg. Damit braucht
  StockPortfolio keinen Sonderhinweis.
- „Verkompliziert den Text nicht zu sehr. Alle User müssen sich auskennen“:
  kurze Sätze ohne Fachjargon, überall dieselbe Aussage.

- „Wireguard/Tailscale - wäre besser oder?“: Beide werden als
  VPN-Beispiel genannt.

- **Ergebnis:** Alle Texte sagen: StockInfo nicht ins Internet stellen,
  nur im Heimnetz nutzen, von außen per VPN (etwa WireGuard oder
  Tailscale). Kein Text
  empfiehlt mehr einen Reverse Proxy.
- **Fachliche Änderungen (2):** (1) `README.md` (Security model),
  `docker/README.md` (Hinweis oben und Quick start), `unraid/README.md`;
  (2) `templates/stockinfo.xml` (Overview, Description, Portfeld) im
  Vorlagen-Repo, aufbauend auf `fdeb4fd`.
- **Dateien:** drei READMEs, Vorlage, dieses Ticket. Kein Produktcode.
- **Budget:** 0 Produktdateien, 5 Dokudateien, 80 Diff-Zeilen.
- **Nicht-Ziele:** kein Prüf-Script, keine Anmeldung in StockInfo, keine
  Änderung an StockPortfolio.

**Doku-Abgleich:** Das Inventar aller versionierten Markdown- und
HTML-Dateien außerhalb von `_tickets/` nannte den Proxy-Weg nur in
`README.md`, `docker/README.md` und `unraid/README.md`. In der Vorlage
stand er nur in der Overview. Danach findet die Suche nach „reverse proxy“
in den aktuellen Anleitungen und der Vorlage keinen Treffer mehr. Die
Treffer in `CHANGELOG.md` und in der alten Spec betreffen Dev-Proxy und
Registry-Login und sind nicht betroffen. Die Erklärung zum Betrieb nur
auf dem eigenen Rechner (Loopback, Fix B1 aus T-84) bleibt im Root-README
erhalten, kürzer gefasst. `xmllint --noout` ist ok. Die Docker-Hub-Vorschau
hat 8.763 UTF-8-Bytes.

## Warum das passiert (Konsumentensicht)

- StockPortfolio ruft StockInfo **direkt aus dem Browser** auf, von einer
  anderen Origin aus (`STOCKINFO_API_URL`, CORS über `CORS_ORIGINS`).
- Diese Aufrufe senden keine Zugangsdaten mit: kein Cookie, kein
  `Authorization`-Header (`fetch` mit Standard-`credentials`,
  StockPortfolio `frontend/src/api/client.ts`).
- Der Browser zeigt für solche Cross-Origin-Aufrufe keinen Anmeldedialog.
  Eine Weiterleitung auf eine Login-Seite scheitert an CORS.

Ein Login-Proxy vor StockInfo blockiert also genau den Konsumenten, für den
StockInfo diese API anbietet. StockPortfolios eigene Texte warnen nur
allgemein: „Protect StockInfo separately and verify that browser API requests
work through your access path“. Einen gangbaren Weg nennen sie nicht.

## Betroffene Stellen

| Repo | Datei | Stelle |
|---|---|---|
| StockInfo | `README.md` | Security model, Zeilen um 199 |
| StockInfo | `docker/README.md` | Zeilen 10–12 und 40 |
| StockInfo | `unraid/README.md` | Zeilen 39–42 |
| Unraid-Templates | `templates/stockinfo.xml` | `Overview` (Network access), `Description`, Portfeld (Stand `fdeb4fd`) |

## Was zu klären ist

Über die Lösung entscheidet, wer StockInfo kennt. Offen ist aus
Konsumentensicht:

- Welcher Zugriffsweg von außen funktioniert, wenn StockPortfolio StockInfo
  nutzt, und wie die Anleitungen das sagen.
- Ob StockPortfolio dafür etwas ändern müsste. Das wäre dann ein eigenes
  Ticket im StockPortfolio-Board.

### Akzeptanzkriterien

- [ ] Die StockInfo-Anleitungen und die Vorlage empfehlen keinen Zugriffsweg,
      der StockPortfolio ohne Hinweis ausschließt.
- [ ] Der Betrieb zusammen mit StockPortfolio hat einen beschriebenen,
      geprüften Weg für den Zugriff von außen, oder die Grenze ist klar benannt.
- [ ] Der Doku-Abgleich nennt README, Docker-README, Unraid-Anleitung und
      `templates/stockinfo.xml`.

### Side-Effects

Betrifft Dokumentation und Vorlagentext. StockPortfolios Texte (T-67 dort)
sollten danach dieselbe Aussage treffen; der Abgleich läuft über das
StockPortfolio-Board.

## Übergabe Runde 1 (Claude, 2026-10-01)

| Repo | Prüfgegenstand |
|---|---|
| StockInfo | `7b46d6b` gegen `master` (`1cbc39e`): `README.md`, `docker/README.md`, `unraid/README.md` |
| Unraid-Templates | `a2d80a6` gegen `fdeb4fd`, nur `templates/stockinfo.xml` (Branch `docs/internet-zugriff-hinweis`, Arbeitskopie `/private/tmp/unraid-internet-hinweis`) |

Der Zwischencommit `b93ff36` (Sonderhinweis für StockPortfolio) ist durch
`7b46d6b` überholt; geprüft wird der Endstand.

### Verify

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | Die drei Anleitungen und die Vorlage lesen | Gleiche Aussage überall: nicht ins Internet, nur Heimnetz, von außen per VPN (WireGuard oder Tailscale); kein Reverse Proxy empfohlen | ➖ |
| 2 | Verständlichkeit prüfen | Kurze Sätze ohne Fachjargon, für Nutzer ohne Vorwissen lesbar (Mikes Vorgabe) | ➖ |
| 3 | Loopback-Absatz im Root-README gegen T-84 B1 prüfen | Native Bindung und Docker-Hostport weiterhin richtig getrennt | ➖ |
| 4 | Inventar nach „reverse proxy“ in aktuellen Anleitungen und Vorlage | Kein Treffer außer `CHANGELOG.md` und alter Spec (andere Bedeutung) | ➖ |
| 5 | `xmllint --noout` und Docker-Hub-Vorschau | XML gültig; Vorschau unter 25.000 Bytes (Coder: 8.763) | ➖ |

Kein Merge im Vorlagen-Repo, kein Push, kein Docker-Hub- oder Unraid-Update.
