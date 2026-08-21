# T-25 · Quellenprofil wechseln — Sicherung und frische Datenbank

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | offen | 1 Tag | Profilbegriff, Sicherung, Rotation, Wiederherstellung | — |

**Löst:** Ein **Quellenprofil** ist die Gesamtheit der aktiven Quellen einer
Instanz. Profil A durch B zu ersetzen ist etwas anderes, als innerhalb von A
eine Quelle zu ergänzen — und dieser Unterschied fehlt im Entwurf bisher ganz.

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

> **Von Mike bestätigt (2026-08-20)**, im Wortlaut über Codex' Kanal:
> „Plugin B ersetzt Plugin A. Die Datenbank von A wird nach einem normalen,
> fortlaufend nummerierten Backup-Schema gesichert; B verwendet eine frische
> Datenbank. Kanada kann Profil B, Russland C und Österreich/Deutschland A
> verwenden." Der frühere Vorbehalt „nur aus zweiter Hand" ist damit erledigt.

**Hängt an:** T-22 (ohne Profil gibt es nichts zu wechseln), **T-24**
(`generation_id` gehört zum REST-Vertrag) **und T-23** (liefert den
programmatischen Preflight, den die Rotation wiederverwendet).
**Nicht zu verwechseln mit T-19**, das ein einzelnes Papier neu auflöst.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Quelle **innerhalb** desselben Profils ergänzen, **Kompatibilitäts-ID unverändert** | bestehende Instrumente unverändert, **dieselbe** Datenbank | | |
| 2 | Paketversion anheben, **Kompatibilitäts-ID unverändert** | dito — kein Datenbankwechsel | | |
| 2b | Profilname gleich, aber **Kompatibilitäts-ID erhöht** (z.B. adjusted → unadjusted) | gilt als neue Generation, **frische** Datenbank | | |
| 3 | Profil A durch B ersetzen | **erst B vollständig validieren**, dann A sichern, dann wechseln | | |
| 3b | B mit fehlendem Wheel / Syntaxfehler / fehlendem Pflicht-Key | Rotation findet **nicht** statt; A bleibt aktiv, keine leere neue DB | | |
| 4 | nach #3 | B läuft auf einer **frischen** Datenbank | | |
| 4b | Sicherung läuft, gleichzeitig ein API-Schreibzugriff | Sicherung ist trotzdem konsistent | | |
| 5 | Sicherungsverzeichnis | fortlaufend nummeriert, mit Manifest: Profil, Stand, Zeitpunkt | | |
| 5b | **Crash-Matrix**: sechs injizierbare Fehlerpunkte, je Punkt Neustart und Recovery | nach jedem: genau **eine** vollständige Generation aktiv, keine Nummer überschrieben, nie B mit As Datenbank, A vollständig startbar | | |
| 5d | derselbe Preflight wie T-23 vor jeder Rotation | identische Logik, keine zweite Validierung — **Abnahme hier**, bereitgestellt in T-23 | | |
| 5c | B ungültig, Neustart | A läuft wieder **vollständig** — Konfiguration *und* Plugin-Umgebung, nicht nur die alte Datenbank | | |
| 6 | Wiederherstellung | ordnet Sicherung und Profil einander zu; ein unpassendes Paar wird abgelehnt | | |
| 6b | dieselbe Sicherung zweimal einspielen | jede Aktivierung bekommt eine **neue** `generation_id` | | |
| 7 | **`GET /generation`** | liefert die aktive `generation_id`, mit `Cache-Control: no-store` | | |
| 7b | Prozessneustart **ohne** Profilwechsel | dieselbe `generation_id` | | |
| 7c | verträgliche Konfigurationsänderung (Schlüssel, Zeitgrenze) | dieselbe `generation_id` | | |
| 7d | Profilwechsel **und** jede Restore-Aktivierung | **neue** `generation_id` | | |
| 7e | Harness-Stufe 2 | `/generation` und der Antwort-Header laufen im Integrationslauf mit | | |
| 8 | **StockPortfolio** nach Profilwechsel (Abnahme in deren T-35) | erkennt die neue `generation_id`, leert **nur** Quote-/History-Caches; Portfolio, Stückzahlen und Ziele bleiben | | |
| 8b | dasselbe ohne Profilwechsel | Cache bleibt — die Generation ändert sich nicht bei jeder Konfigänderung | | |

---

## Details

### Zwei Vorgänge, die man nicht verwechseln darf

| Vorgang | Bestehende Instrumente | Datenbank |
|---|---|---|
| Quelle ergänzen/aktualisieren (in A) | unverändert | bleibt |
| Profil A → B | — | **frisch**, A wird gesichert |

Erst diese Trennung bringt zwei Invarianten widerspruchsfrei zusammen:

- „Eine Installation verändert nichts von selbst" (Voraussetzung dafür, dass
  T-19 nachrangig sein darf)
- „B ersetzt A mit frischer Datenbank"

### Erst validieren, dann rotieren

Die Reihenfolge ist nicht beliebig:

1. B installieren
2. **alles prüfen** — Plugin-Importe, Vertragsversionen, Pflichtkonfiguration,
   sind alle Rollen besetzt
3. erst dann A sichern und die aktive Datenbank wechseln

Ein nicht verfügbares Wheel, ein Syntaxfehler oder ein fehlender Pflichtschlüssel
darf weder eine leere neue Datenbank erzeugen noch die laufende A-Generation
ablösen. Dafür gibt es den Negativtest `#3b`.

### Was ein belastbares Backup braucht

Nicht nur die Datei kopieren:

- **Fortlaufende Nummer**, atomar vergeben — sonst kollidieren zwei gleichzeitig
  startende Läufe
- **Temporäre Datei, dann atomar veröffentlichen** — eine abgebrochene Sicherung
  darf nie wie eine gültige aussehen
- **Niemals überschreiben.** Eine vorhandene Nummer ist vergeben, Punkt
- **Konsistenz gegen *alle* Schreiber.** „Der Scheduler steht" genügt nicht —
  API-Requests schreiben auch. Es braucht die SQLite-Backup-API oder eine
  Wartungssperre, die Scheduler **und** Requests umfasst
- **Manifest**: Profil-ID, **Profil-Kompatibilitäts-ID**, Plugin-Pakete samt
  Versionen, StockInfo-Version, DB-Schema-Version. „Stand" allein ist zu
  unbestimmt, um eine Wiederherstellung zuzuordnen
- **Zuordnung beim Zurückholen**: Eine Sicherung aus Profil A in Profil B
  einzuspielen ist ein Fehler, kein Sonderfall

### Die Profil-Kompatibilitäts-ID — kein Hash über die Datei

Verify `#2` verlangt, dass eine neue Paketversion **keine** neue Datenbank
erzeugt. Daraus folgt zwingend eine ausdrückliche Kennung statt eines Hashes
über die ganze Konfiguration:

| Änderung | Kompatibilitäts-ID |
|---|---|
| API-Schlüssel, Zeitgrenze, Patch-Version | **unverändert** |
| fachlich inkompatibler Profilstand | erhöht sich — bewusst |
| `a/1` → `b/1` | anderes Profil, neue Datenbank |
| `a/1` → `a/2` | entscheidet der Profilautor, nicht ein Hash |

Ohne diese Regel kann der Launcher „Quelle aktualisieren" und „Profil ersetzen"
nicht zuverlässig unterscheiden — und würde bei jeder Schlüsseländerung die
Datenbank wegwerfen.

### Der Konsument, auf den es ankommt, ist StockPortfolio

Ein Cache über den Profilwechsel hinweg zeigt Werte aus einer Datenbank, die es
nicht mehr gibt. Deshalb gehört eine **`generation_id`** in die API — sie
gehört zum Vertrag aus T-24.

**Das StockInfo-Dashboard ist dafür der falsche Prüffall:** Es hält keinen
persistenten Cache über getrennte Deployments hinweg. StockPortfolio tut das —
dort liegt der eigentliche Fall. Nötig ist dort:

- die letzte `generation_id` speichern
- bei Änderung **nur** Quote- und History-Caches leeren
- Portfolio, Stückzahlen, Ziele und Benutzerdaten behalten

**Angelegt am 2026-08-21: `StockPortfolio/_tickets/T-35-stockinfo-generation-und-waehrung.md`.**
Verify `#8` kann in einem Ticket mit Scope „StockInfo (Backend + Dashboard)"
nicht grün werden — es wird **dort** abgenommen. Das Ticket hält fest:

- letzte `generation_id` speichern, bei Änderung reagieren
- **nur** Kurs- und History-Caches leeren — nie Portfolio, Stückzahlen, Ziele
- **keine EUR-Ersatzwährung**, wenn die Kurswährung fehlt (heute wird geraten)
- mittelfristig `listing_id` als bevorzugten Maschinen-/Cache-Schlüssel
- Rückfall auf ISIN/Symbol für alte gespeicherte Positionen bleibt

Ein Befund aus der Prüfung dort ist unabhängig von diesem Vorhaben ernst:
`mappers.ts:17` setzt `currency: response.currency ?? 'EUR'` — eine fehlende
Kurswährung wird geraten. Die App erklärt an anderer Stelle selbst, dass
„10.000 USD plus 10.000 EUR keine 20.000 von irgendetwas" ergeben; der Rückfall
unterläuft genau diese Regel. Der Cache liegt in **IndexedDB** und überlebt jedes
Deployment — Codex' Einschätzung, dass hier der eigentliche Konsument sitzt, ist
damit bestätigt.

### Absturzfester Übergang

Die Sicherungsdatei atomar zu schreiben genügt nicht; auch der Übergang
`A aktiv → A gesichert → B aktiv` muss es sein. Ein Abbruch dazwischen darf
beim nächsten Start weder A erneut rotieren noch B mit As Datenbank öffnen.

Dafür ein kleiner, dauerhafter Zustandsmarker mit:

- bisher aktiver Profil- und Kompatibilitäts-ID
- gewünschtem, **validiertem** Zielprofil
- Sicherungsnummer und deren Status
- Pfad der aktiven Datenbank
- Ziel-`generation_id`

Jeder Zwischenzustand muss beim Neustart deterministisch fortgesetzt **oder**
auf A zurückgerollt werden können.

**Die Crash-Matrix, konkret** *(Codex, 2026-08-21 — eine frühere Fassung dieses
Tickets hatte nur einen allgemeinen Absturztest, und die Spec behauptete
fälschlich, die Matrix sei schon enthalten).* **Sieben** Fehlerpunkte — „vor und
nach Aktivierung" sind zwei verschiedene persistierte Zustände, nicht einer —,
einzeln injizierbar, jeder mit Neustart und Recovery-Lauf:

| # | Abbruch nach/während | |
|---|---|---|
| 1 | erfolgreicher Validierung von B | |
| 2 | dem temporären Backup | |
| 3 | atomarer Veröffentlichung des Backups | |
| 4 | Schreiben des Übergangsmarkers | |
| 5 | Anlegen der frischen B-Datenbank | |
| 6 | unmittelbar **vor** Aktivierung von B | |
| 7 | unmittelbar **nach** Aktivierung von B | |

Für **jeden** Punkt gelten dieselben Invarianten: genau eine vollständige
Generation aktiv, keine Backupnummer überschrieben, niemals B mit der Datenbank
von A, und A einschließlich Konfiguration und Plugin-Umgebung wieder startbar.

Das braucht eine einspeisbare Uhr und kontrollierte UUID-Erzeugung — echte
Wartezeiten oder Manipulation der Systemuhr gehören nicht in die Suite.

**Und „A bleibt aktiv" braucht mehr als die alte Datenbank:** Die geänderte
`sources.yaml` zeigt ja weiterhin auf B. Es braucht eine gespeicherte
*last-known-good*-Konfiguration **samt Plugin-Umgebung**, sonst startet A nach
einem gescheiterten Wechsel gar nicht mehr.

### Wiederherstellung vergibt eine neue Generation

Beim Zurückholen einer Sicherung bekommt **jede Aktivierung** eine neue
`generation_id` — auch wenn im Backup eine alte gespeichert ist. Sonst sieht ein
Konsument bei zweimaliger Wiederherstellung dieselbe Kennung und behält seinen
Cache, obwohl sich der Inhalt geändert hat.

Die fachlichen `listing_id`s im Backup bleiben dabei erhalten. Das trennt
**Datenidentität** von **Betriebsereignis**.

---

## Auflösung

_(offen)_
