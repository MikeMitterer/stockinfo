# T-84 · Hinweise zum Internetbetrieb unabhängig prüfen

Die neuen StockInfo-Warnungen liegen in Anleitungen und Unraid-Vorlage vor,
wurden aber noch nicht unabhängig geprüft. StockInfo hat keine Anmeldung;
wer den Dienst erreichen kann, kann Daten ändern oder löschen. Vor einer
Veröffentlichung soll der zuständige Verifier prüfen, ob diese Grenze in
allen Texten zutreffend und gut sichtbar erklärt ist.

**Beispiel:** Ein Nutzer möchte den Unraid-Port 8000 am Router freigeben.
Die Vorlage soll schon bei der Installation warnen, und die Anleitungen
sollen einen geschützten Zugriffsweg nennen.

**Stand:** Mike hat am 2026-10-01 einen Reviewauftrag verlangt und später
Codex ausdrücklich als Verifier bestimmt. Claude ist Coder; die maßgebliche
Zuordnung steht in `STATUS.md`. Claude hat die StockInfo-Endfassung
`8b89864` und seinen StockInfo-Vorlagentext `fdeb4fd` zur unabhängigen
Prüfung übergeben. Eine Freigabe liegt noch nicht vor. Dieses Ticket ist
in `30-doing/` aktiv.

Für Mike steht jetzt kein Handgriff an. Abschluss und Veröffentlichung
bleiben nach der technischen Prüfung getrennt; Docker Hub und das
Unraid-Listing zeigen die neue Fassung derzeit nicht.

## Rollen und Scope-Vertrag (Claude, 2026-10-01)

Mike, 2026-10-01: „Du bist coder“. Coder `claude`, Verifier `codex`.
Codex' Vorbereitung (`396e8be`, `ca7ae2d`) ist Eingangsmaterial, keine
Übergabe. Damit Codex unabhängig prüfen kann, schreibt Claude die
StockInfo-Endfassung selbst auf dem aktuellen `master` und gleicht sie mit
der API ab.

- **Ergebnis:** Alle drei Anleitungen raten konsistent von einer direkten
  Internetfreigabe ab und nennen LAN, VPN und HTTPS-Reverse-Proxy mit
  Anmeldung. Der Abschnitt „Security model“ nennt die tatsächlich
  verändernden Routen.
- **Fachliche Änderungen (2):** Warnhinweise in `README.md`,
  `docker/README.md`, `unraid/README.md`; Routenliste im „Security model“
  berichtigt (`GET /analyze` schreibt nicht in die Datenbank; Restore,
  Löschen per Symbol und Detailpflege fehlten).
- **Dateien:** drei READMEs, dieses Ticket. Kein Produktcode.
- **Budget:** 0 Produktdateien, 4 Dokudateien, 150 Diff-Zeilen.
- **Nicht-Ziele:** keine Anmeldung bauen, keine Änderung an App oder Image.
  Die Unraid-Vorlage liegt in einem eigenen Repository. Der erste Text
  `ca7ae2d` stammte von Codex; Claudes neu verfasster StockInfo-Teil
  `fdeb4fd` ist der aktuelle Prüfgegenstand.

## Prüfgegenstand

| Repo | Time-box | Scope | GH-Issue |
|---|---|---|---|
| StockInfo | 0,5–1 h | `README.md`, `docker/README.md`, `unraid/README.md`; Commit `8b89864` gegen `7bac219` | — |
| Unraid-Templates | 0,5 h | ausschließlich `templates/stockinfo.xml` aus Commit `fdeb4fd` gegen `c828e24` | — |

Die ursprünglichen Vorbereitungscommits `396e8be` und `ca7ae2d` liegen
auf `docs/internet-zugriff-hinweis`; Claudes aktuelle Endfassungen stehen
oben. StockInfos Projekt-Root steht jetzt auf
`t-84-internetbetrieb-hinweise`; die frühere Arbeitskopie unter
`/private/tmp/stockinfo-internet-hinweis` entfällt mit T-85. Das
Unraid-Templates-Repository hat weiterhin seine Arbeitskopie
`/private/tmp/unraid-internet-hinweis`; T-85 ändert dort nichts. Das Gegenstück für StockPortfolio
wird im dortigen T-67 mit dessen Rollen geprüft. Der gemeinsame Template-
Commit wird pro Ticket nur für die eigene XML-Datei bewertet.
Eine Freigabe des gesamten Template-Commits braucht auch das StockPortfolio-
Prüfergebnis aus T-67.

Claude hat die StockInfo-Dokumentationsfassung auf dem aktuellen Stand
selbst geschrieben und die OUTBOX zuletzt mit `8b89864` übergeben. Der
unabhängige Review gehört `codex`. Die vorbereiteten Fassungen `396e8be`
und `ca7ae2d` aus der früheren Codex-Coder-Zuordnung sind nicht die
Prüffassungen; Claudes neuer Vorlagentext steht in `fdeb4fd`.

### Verify

Legende: ➖ unabhängige Prüfung steht aus. Die Autorprüfung ist unten genannt
und ersetzt kein Verifier-Urteil.

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | StockInfo-Diff gegen tatsächliche API-Routen und das Authentifizierungsmodell lesen | Hinweis erklärt fehlende Anmeldung und ändernde/löschende Zugriffe ohne unzutreffende Sicherheitszusage | ✅ |
| 2 | `README.md`, `docker/README.md` und `unraid/README.md` inhaltlich abgleichen | Direkte Internetfreigabe wird konsistent abgeraten; LAN, VPN und HTTPS-Proxy mit Anmeldung sind verständlich beschrieben | ✅ |
| 3 | `templates/stockinfo.xml` gegen die Anleitungen und Containerkonfiguration prüfen | Englischer Hinweis steht sichtbar in Overview, Description und Portfeld; keine andere Template-Funktion geändert | ✅ |
| 4 | Docker-Hub-Vorschau und XML erneut am endgültigen Prüfstand erzeugen | Vorschau unter 25.000 UTF-8-Bytes, Links korrekt; XML gültig | ✅ |
| 5 | Git-Fassung und Veröffentlichungsstand trennen | Review benennt geprüfte Commit-IDs und hält fest, dass kein Merge, Push oder Hub-/Unraid-Update belegt ist | ✅ |

**Coder-Belege (Claude, 2026-10-01), Endfassung auf `t-84-internetbetrieb-hinweise`:**

- **#1 Routen:** Gegen `app.openapi()` geprüft. Alle im „Security model“
  genannten Pfade existieren mit der genannten Methode. Ändernd sind
  insgesamt: `POST /backups`, `POST /backups/{name}/restore`,
  `DELETE /instruments/{isin}`, `DELETE /instruments/by-symbol/{symbol}`,
  `POST /instruments/intake`, `PUT …/isin`, `PUT …/overrides`,
  `PATCH /instruments/by-id/{listing_id}/details`, `POST /migration/confirm`,
  `POST /refresh` samt `{isin}`/`by-symbol`. Die bisherige Aussage, `GET
  /analyze` schreibe in die Datenbank, war falsch (`AnalyzerService` misst
  nur, ohne Persistenz) und ist berichtigt. Keine Anmeldung im Code
  (keine Security-Abhängigkeit an den Routern).
- **#2 Anleitungen:** `README.md` (Security model: Routenliste, VPN,
  HTTPS-Reverse-Proxy mit Login, „Never forward“; Docker-Abschnitt: kurzer
  Hinweis mit Link), `docker/README.md` (Hinweis direkt unter dem
  GitHub-Link, Quick start verweist darauf), `unraid/README.md` (fetter
  Hinweis, VPN mit Beispiel WireGuard). Alle drei: kein Login, Port nicht
  ins Internet, LAN, VPN, HTTPS-Proxy mit Login.
- **#3 Vorlage:** `ca7ae2d:templates/stockinfo.xml` gelesen: Hinweis in
  Overview (eigener Absatz „Security“), Description und Portfeld; sonst
  keine Template-Funktion geändert; deckt sich inhaltlich mit den
  Anleitungen. Seit `c828e24` keine weitere Änderung an `stockinfo.xml` auf
  dem `master` des Vorlagen-Repos. **Autorschaft:** Der Vorlagentext stammt
  unverändert von Codex; Claude hat ihn geprüft und übernimmt ihn. Codex
  kann diesen Teil deshalb nicht unabhängig abnehmen.
- **#4:** Docker-Hub-Vorschau 8.846 UTF-8-Bytes; `xmllint --noout` für die
  Vorlage aus `ca7ae2d` erfolgreich.
- **#5:** Kein Merge, Push, Docker-Hub- oder Unraid-Update; der
  Vorlagen-Commit liegt weiter nur auf `docs/internet-zugriff-hinweis` im
  Vorlagen-Repo.

**Autorbelege vom 2026-10-01 (Codex, Vorbereitung):** `git diff --check` ohne Befund;
`xmllint --noout` für beide Templates erfolgreich. Die Docker-Hub-Vorschau
von StockInfo wurde erzeugt und hatte 8.006 UTF-8-Bytes. Das sind
Vorprüfungen, keine unabhängige Freigabe.

### Akzeptanzkriterien

- [ ] `codex` prüft die eindeutig benannte Endfassung unabhängig und hält Befunde oder Freigabe im Ticket fest.
- [ ] Der Doku-Abgleich umfasst beide READMEs, die Unraid-Anleitung und den StockInfo-Teil der zentralen Vorlage.
- [ ] Der Coder löst nötige Korrekturen auf dem aktuellen Branch; danach wird die tatsächlich geprüfte Fassung übergeben.
- [ ] Veröffentlichung wird erst nach der vorgesehenen Abnahme als eigener Schritt ausgewiesen.

### Side-Effects

Nur Dokumentation und Template-Beschreibung. Die T-83-Umsetzung,
StockPortfolios eigener Review und die Containerkonfiguration bleiben
außerhalb dieses Reviewauftrags. Kein Produktcode wird durch das Ticket
geändert.

### Auflösung

Runde 1 ging mit `changes_requested` an Claude zurück. Die korrigierte
Runde 2 ist technisch freigegeben; beide Berichte stehen unten. Ein
Ticketabschluss und eine menschliche Abnahme liegen nicht vor.

## Nacharbeit Runde 2 (Claude, 2026-10-01)

- **B1:** `README.md` → Security model trennt jetzt native Bindung und
  Docker: nativ `HOST=127.0.0.1`; in Docker bleibt `HOST` bei `0.0.0.0`,
  veröffentlicht wird nur auf dem Host-Loopback (`-p 127.0.0.1:8000:8000`),
  mit ausdrücklichem Hinweis, dass `HOST=127.0.0.1` im Container den
  veröffentlichten Port unerreichbar macht. Der einleitende Satz zur
  Standardbindung unterscheidet ebenfalls nativ und Docker. Deckt sich mit
  `docker/README.md` (Quick start mit `127.0.0.1:8000:8000`).
- **B2:** Den StockInfo-Text der Unraid-Vorlage hat Claude eigenständig neu
  formuliert: Commit `fdeb4fd` im Vorlagen-Repo auf
  `docs/internet-zugriff-hinweis`, nur `templates/stockinfo.xml`, drei
  Stellen (Overview-Absatz „Network access“, Description, Portfeld).
  Inhalt: keine Anmeldung, konkrete Folgen (Instrumente ändern/löschen,
  Sicherungen einspielen), Port nie am Router freigeben, LAN, VPN mit
  WireGuard-Beispiel, Reverse Proxy mit HTTPS und Login. `xmllint --noout`
  ok, `git diff --check` sauber; `stockportfolio.xml` unverändert.
  Prüfgegenstand für Verify #3: `fdeb4fd` gegen `c828e24`, nur
  `templates/stockinfo.xml`.
- Docker-Hub-Vorschau unverändert gültig (`docker/README.md` in Runde 2
  nicht geändert).

## Verifier-Prüfung · Runde 1 (Codex, 2026-10-01)

**Ergebnis: `changes_requested`.** Claudes StockInfo-Endfassung `3733624`
gegen `7bac219` auf `t-84-internetbetrieb-hinweise` geprüft. Sie ist
gegenüber der früheren Codex-Vorbereitung `396e8be` inhaltlich neu
bearbeitet. Das Unraid-Template `ca7ae2d:templates/stockinfo.xml` ist
dagegen unverändert Codex-Text; dafür erteile ich kein unabhängiges
Verifier-Urteil. Kein Produktcode und keine Vorlage wurden im Review
geändert.

**B1 · Loopback-Anleitung vermischt Container- und Host-Bindung.**
`README.md:189-190` empfiehlt im Abschnitt „Security model“ direkt nach
dem Docker-Hinweis `HOST=127.0.0.1` als Loopback-Weg. Im Container bindet
damit Uvicorn nur an dessen eigenes Loopback; ein mit `-p` veröffentlichter
Hostport erreicht den Dienst nicht. Eine isolierte Netzprobe mit demselben
Testimage und `python -m http.server` zeigte: Container-Bindung an
`127.0.0.1`, Host-Publishing auf `127.0.0.1` → `curl` Exit 52 („Empty reply
from server“); Container-Bindung an `0.0.0.0` bei demselben Host-Publishing
→ `curl` Exit 0 mit Antwort. `docker/README.md:25` zeigt das richtige
Host-Publishing `-p 127.0.0.1:8000:8000`; [Docker-Dokumentation zur
Portfreigabe](https://docs.docker.com/engine/network/port-publishing/)
unterscheidet ebenfalls die Host-Adresse. Bitte im Root-README native
`HOST`-Bindung und Docker-Host-Publishing getrennt erklären, zumal der neue
Docker-Abschnitt auf diesen Sicherheitsabschnitt verweist.

**B2 · Der Vorlagentext hat keinen unabhängigen Verifier.** Claude hat
`ca7ae2d:templates/stockinfo.xml` aus der früheren Codex-Coder-Arbeit
unverändert übernommen. Ich kann die eigene Formulierung in Overview,
Description und Portfeld nicht unabhängig abnehmen. Der Diff betrifft
faktisch nur diese drei Texte, und `xmllint --noout` besteht; das ist ein
Syntax- und Umfangsnachweis, kein unabhängiges Texturteil. Für Verify #3
braucht es eine eigenständig von Claude verfasste Endfassung mit neuer
Commit-ID oder einen ausdrücklich zugeordneten anderen unabhängigen
Verifier. Der StockPortfolio-Teil des gemeinsamen Vorlagen-Commits ist
kein T-84-Prüfgegenstand.

**Bestätigte Nachweise:** `app.openapi()` enthält keine Security-Schemes
und keine globale Security-Anforderung. Die im README genannten Methoden
und Pfade existieren. Die Aufzählung ist mit „including“ erkennbar
beispielhaft; `POST /backups` und `POST /migration/confirm` sind weitere
schreibende Wege. Der veraltete Satz über `GET /analyze` ist entfernt;
die Route ruft den Analyzer ohne Datenbankschreiben auf. Alle drei
Anleitungen warnen vor direkter Portfreigabe und nennen LAN, VPN und
HTTPS-Proxy mit Anmeldung. [Unraids WireGuard-Anleitung](https://docs.unraid.net/unraid-os/system-administration/secure-your-server/wireguard/)
bestätigt den VPN-Beispielweg. Docker-Hub-Vorschau 8.846 UTF-8-Bytes mit
absoluten Bildlinks; XML aus `ca7ae2d` syntaktisch gültig;
`git diff --check 7bac219 3733624` sauber. Beide eigenen
Netztestcontainer wurden entfernt. `origin/master` enthält die T-84-
Dokumentation nicht; kein Merge, Push, Hub- oder Unraid-Update wurde in
diesem Review ausgeführt oder als geschehen bestätigt.

**Standards und Doku-Abgleich:** `code-standards` (Dokumentation),
`docker-conventions` und `unraid-conventions` wurden auf die betroffenen
Dateien angewandt. Struktur, Anker und kurze Warntexte ✅; Docker-Bindung
⚠️ B1; unabhängiger Unraid-Textnachweis ⚠️ B2. DRY und Produktcode-Regeln
➖, da nur Dokumentation und Vorlage betroffen sind. Die Aussagen von
`README.md`, `docker/README.md` und `unraid/README.md` wurden gemeinsam
abgeglichen; ihre Kernwarnung stimmt überein, der Loopback-Weg im Root-
README muss korrigiert werden. Die mechanische Berichtigung des veralteten
Ticketstands ist im separaten Review-Commit `fb29d46` festgehalten.
Menschliche Abnahme wurde nicht erteilt.

## Verifier-Prüfung · Runde 2 (Codex, 2026-10-01)

**Ergebnis: technisch `approved`.** StockInfo-Commit `8b89864` gegen
`67e398c` und ausschließlich `templates/stockinfo.xml` aus Claudes
Vorlagen-Commit `fdeb4fd` gegen `c828e24` unabhängig geprüft. Die beiden
Befunde aus Runde 1 sind behoben; Verify #1–#5 sind ✅. Kein Produktcode
und keine Vorlage wurden von Codex geändert.

**B1 erledigt:** `README.md` trennt jetzt native Bindung
(`HOST=127.0.0.1`) von Docker: Der Container behält `HOST=0.0.0.0`, und
`-p 127.0.0.1:8000:8000` bindet nur den Hostport an Loopback. Das stimmt
mit dem Docker-Quick-start und der unabhängigen Netzprobe aus Runde 1
überein. Der Text sagt ausdrücklich, dass `HOST=127.0.0.1` *im Container*
den veröffentlichten Port unerreichbar macht.

**B2 erledigt, begrenzter Prüfgegenstand:** Claudes neuer Vorlagentext
`fdeb4fd` unterscheidet sich in Overview, Description und Portfeld von
Codex' vorbereitetem `ca7ae2d`. Er nennt fehlende Anmeldung, mögliche
Änderungen/Löschungen und das Einspielen von Sicherungen; er rät von
Router-Portfreigabe ab und nennt LAN, VPN sowie einen Reverse Proxy mit
HTTPS und Login. Das stimmt mit den drei StockInfo-Anleitungen und den
tatsächlichen Routen überein. Der Diff `ca7ae2d..fdeb4fd` betrifft nur
`templates/stockinfo.xml`; der Gesamtstand des Vorlagenbranches enthält
weiterhin `stockportfolio.xml` aus `ca7ae2d`. Diese Freigabe gilt nur für
StockInfos XML-Datei. Der StockPortfolio-Anteil braucht sein eigenes
Prüfergebnis aus T-67, bevor der Gesamtbranch integriert wird.

**Unabhängige Nachweise:** `git diff --check 67e398c 8b89864` und
`git diff --check c828e24 fdeb4fd -- templates/stockinfo.xml` bestanden.
`xmllint --noout` bestand für `fdeb4fd:templates/stockinfo.xml`. Die
Docker-Hub-Vorschau wurde erneut erzeugt: 8.846 UTF-8-Bytes, absolute
GitHub-Bildlinks, unter 25.000 Bytes. Die T-84-Änderungen liegen auf dem
StockInfo-Ticketbranch und dem Vorlagenbranch; in den lokalen
`origin/master`-Ständen sind sie nicht enthalten. In diesem Review fand
kein Merge, Push, Docker-Hub- oder Unraid-Update statt. Die veralteten
Prüfcommit-Verweise des Tickets wurden im mechanischen Review-Commit
`e8163c9` berichtigt.

**Standards und Doku-Abgleich:** `code-standards` (Dokumentation),
`docker-conventions` und `unraid-conventions` wurden erneut angewandt.
Dokustruktur/Links ✅; Host- und Containerport ✅; Unraid-Text und XML ✅;
DRY und Produktcode-Regeln ➖. `README.md`, `docker/README.md` und
`unraid/README.md` geben die Zugriffsgrenze und die drei Zugriffswege
inhaltlich gleich wieder; nur das Root-README änderte sich in Runde 2.
Die technische Freigabe ist keine menschliche Abnahme und kein Auftrag,
den gesamten Vorlagenbranch oder das Ticket als abgeschlossen zu markieren.
