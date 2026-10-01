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

## Verifier-Prüfung · Runde 1 (Codex, 2026-10-01)

**Ergebnis: `approved`.** StockInfo `7b46d6b` gegen `1cbc39e` und
`a2d80a6:templates/stockinfo.xml` gegen `fdeb4fd` unabhängig geprüft.
`a2d80a6` ist der neue Vorlagenstand; `fdeb4fd` enthält noch die frühere
Proxy-Empfehlung. Nach dem Produktcommit folgten im StockInfo-Branch nur
Ticket- und Statuscommits. Kein Produktcode und keine Vorlage wurden im
Review geändert; eine menschliche Abnahme ist damit nicht erteilt.

| Verify | Ergebnis und Beleg |
|---|---|
| #1 | ✅ Alle drei READMEs und `a2d80a6:templates/stockinfo.xml` nennen Heimnetz und VPN für Zugriff von außen. Die Vorlage nennt WireGuard und Tailscale im Overview. Keine dieser aktuellen Aussagen empfiehlt den Login-Proxy. |
| #2 | ✅ Die geänderten Warnungen bestehen aus kurzen, direkten Sätzen und erklären den Nutzweg ohne Proxy-Fachbegriffe. Andere, bereits bestehende Fachtexte der Vorlage sind nicht Teil dieser Textänderung. |
| #3 | ✅ `README.md` trennt `HOST=127.0.0.1` für nativen Start von Docker-Host-Publishing mit `-p 127.0.0.1:8000:8000`; im Container bleibt `HOST` unverändert. Der T-84-B1-Fix bleibt erhalten. |
| #4 | ✅ `git grep` über alle versionierten Markdown- und HTML-Dateien außerhalb von `_tickets/` findet „Reverse-Proxy“ nur in der historischen Design-Spec `docs/superpowers/specs/2026-07-13-single-container-deployment-design.md`. In `a2d80a6:templates/stockinfo.xml` gibt es keinen Treffer. |
| #5 | ✅ `xmllint --noout` für die XML aus `a2d80a6` und beide `git diff --check` bestanden. Die Docker-Hub-Vorschau wurde erzeugt und misst 8.763 UTF-8-Bytes; die Grenze beträgt 25.000. |

**Umfang:** 2/2 fachliche Änderungen, 0/0 Produktdateien, 5/5
Dokudateien einschließlich der externen Vorlage. Die drei README-Diffs
haben 53 geänderte Zeilen; die XML hat sechs. Das bleibt unter dem
vereinbarten Budget von 80 Diff-Zeilen. Es gab keinen Anlass für ein
Prüf-Script oder einen Produktlauf. Ein Live-Test mit VPN oder auf Unraid
war nicht Teil von Mikes Textauftrag und wird nicht behauptet.

**Doku-Abgleich:** `README.md` („Security model“), `docker/README.md`
(Warnung und „Quick start“), `unraid/README.md` (Installation) und
`a2d80a6:templates/stockinfo.xml` (Overview, Description, Portfeld)
sagen inhaltlich dasselbe. Das Root-README behält den Sonderfall für
Zugriff nur vom eigenen Rechner. Historische Spec und Changelog bleiben
Historie. StockPortfolio-Texte sind im dortigen Board zu prüfen; diese
Freigabe umfasst sie nicht.

**Standards:** Gelesen:
`/Users/macminipro/.codex/skills/code-standards/SKILL.md` mit
`references/documentation.md`, dazu `docker-conventions` und
`unraid-conventions`. Die lokale Entscheidung gegen einen Login-Proxy
geht der allgemeineren Unraid-Empfehlung vor.

| `code-standards`-Gruppe | Ergebnis |
|---|---|
| Architektur, Shell, CLI, Frontend, Python, Persistenz, Qualität | ➖ Kein Code oder Test im Diff. |
| Dokumentation | ✅ Die geänderten Abschnitte sind kurz; vorhandene Inhaltsverzeichnisse und Anker bleiben intakt. |
| DRY | ✅ Die Sicherheitszusage ist über die vier nötigen Auslieferungsorte konsistent; keine zusätzliche gepflegte Quelle wurde eingeführt. |

**Lessons-Einordnung:** Claudes einschlägige lokale Lessons wurden vor
dem Review gegen die Übergabe geprüft, insbesondere SI-P-11 (gültiger
Übergabecommit), SI-P-12 (vollständiges Fundstelleninventar) und SI-P-13
(Muss-Regeln). Kein neuer Fehlbefund und keine neue Lesson. Der separate
Abgleich der Board-Konventionen gegen Paketfassung `df699dd1` bleibt
offen: Der lokale Workflow trägt die Kennung
`2026-09-28-activity-local` noch nicht und bildet Activity-Pflege,
Observer-Koordination und Lessons-Einordnung nicht vollständig ab.
`ACTIVITY.md` ist bereits über die Root-`.gitignore` ausgeschlossen;
STATUS verlinkt die Datei erst in einem älteren Abschnitt. Diese
Board-Übernahme ist kein T-87-Blocker und braucht einen gesondert
schreibberechtigten Board-Schritt. Keine zentrale Paketänderung wurde
behauptet.
