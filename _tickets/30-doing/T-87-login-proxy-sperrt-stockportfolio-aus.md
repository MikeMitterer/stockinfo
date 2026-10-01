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

**Umfang nach Mikes Vorgabe:** „Stelle einfach die Beschreibung, den Text
richtig“. Die Anleitungen benennen die Grenze. Sie empfehlen keinen
weiteren Zugriffsweg, und ein Prüfaufbau mit Proxy entfällt.

- **Ergebnis:** Alle drei Anleitungen sagen: Mit StockPortfolio
  funktionieren nur LAN und VPN. Ein Login-Proxy vor StockInfo blockiert
  StockPortfolios Browseraufrufe, weil diese keine Anmeldung mitsenden.
- **Fachliche Änderungen (2):** (1) Hinweis in `README.md` (Security
  model), `docker/README.md` (Hinweis oben und Quick start) und
  `unraid/README.md`; (2) derselbe Hinweis knapp in
  `templates/stockinfo.xml`. Die Vorlage liegt im Vorlagen-Repo und
  baut auf `fdeb4fd` auf.
- **Dateien:** drei READMEs, Vorlage, dieses Ticket. Kein Produktcode.
- **Budget:** 0 Produktdateien, 5 Dokudateien, 80 Diff-Zeilen.
- **Nicht-Ziele:** kein Prüf-Script; keine Empfehlung eines nicht
  geprüften Proxy-Wegs, etwa StockInfo unter einem Pfad des
  StockPortfolio-Hosts; keine Anmeldung in StockInfo; kein
  `allow_credentials=True`; keine Änderung an StockPortfolio.

**Doku-Abgleich (StockInfo-Teil):** Das Inventar aller versionierten
Markdown-, XML- und HTML-Dateien außerhalb von `_tickets/` nennt den
Proxy-Weg nur in `README.md`, `docker/README.md` und `unraid/README.md`.
Alle drei sind angepasst und sagen dasselbe. Die Treffer in `CHANGELOG.md`
und in der alten Spec betreffen Dev-Proxy und Registry-Login und sind
nicht betroffen. Die Docker-Hub-Vorschau hat 9.001 UTF-8-Bytes. Offen
ist `templates/stockinfo.xml`.

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
