# T-27b · HTTP-Plugins offline prüfbar machen (Fake → Real)

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (`plugin_api/`) | offen | zu schätzen | Referenztransport, Record/Replay, Scrubbing, Freshness | — |

**Löst:** Das Beispiel-Plugin liest eine lokale CSV — bequem gewählt. Ein
EODHD- oder Twelve-Data-Plugin machte bei jedem Contract-Lauf echte Requests:
langsam, unzuverlässig, verbraucht Kontingent. Damit trägt der Vertrag für den
Fall, um den es eigentlich geht, noch nicht.

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

**Hängt an:** T-27a (das Szenarioformat kommt von dort).
**Muss vor Abschluss von T-23 stehen.**

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | HTTP-Beispielplugin, `make test-plugin-api` | läuft **strikt offline** gegen Aufzeichnungen | | |
| 2 | derselbe Lauf, fehlende Aufzeichnung | **Fehler** — fällt niemals still ins Netz zurück | | |
| 3 | derselbe Lauf, Socket-Zugriff | technisch **gesperrt**, nicht nur unerwünscht | | |
| 4 | Aufzeichnungsdatei | kein Schlüssel, kein Token, kein Cookie — in Kopf, Query, Rumpf und Antwort | | |
| 5 | Aufzeichnungsdatei | trägt `recorded_at`, letzten erfolgreichen Real-Lauf, Versionen, Szenario-Signatur | | |
| 6 | **überalterte** Aufzeichnung, Offline-Lauf | bleibt **grün**, gibt nur einen Hinweis | | |
| 7 | dieselbe Lage, Release-Check | schlägt **fehl** und verlangt einen Real-Lauf | | |
| 8 | Frist | je Plugin einstellbar | | |
| 9 | `pytest --real` | dieselben Szenarien gegen die echte API | | |
| 10 | Anbieter ist gerade nicht erreichbar | der normale Build bleibt grün; nur der Real-Lauf schlägt fehl | | |

---

## Details

### Zwei Gates statt eines Schalters

Ein bloßer `--real`-Schalter genügt nicht: Niemand bemerkt zuverlässig, dass er
seit Monaten nicht gelaufen ist. Eine reine Altersprüfung ist aber ebenso
falsch — **würde der Offline-Lauf nach Kalenderzeit rot, könnte ein Beiträger
ohne Anbieter-Schlüssel nach Ablauf der Frist gar nichts mehr bauen.**

Deshalb zwei getrennte Tore:

| Tor | Läuft | Schlägt fehl bei |
|---|---|---|
| `make test-plugin-api` | bei jedem Commit, **strikt offline** | unerwarteter Request, fehlende Metadaten, nicht bereinigte Geheimnisse. Alter → nur **Hinweis** |
| Release-/Wartungs-Check | vor einer Veröffentlichung | überalterte oder nie real bestätigte Aufzeichnung |

Die Frist gehört **je Plugin** eingestellt: Ein träger Referenzdienst braucht
eine andere als ein Anbieter ohne stabile API-Version.

**Und der Real-Lauf gehört zum Release des jeweiligen Plugins**, nicht zu dem
von StockInfo — StockInfo besitzt weder die Schlüssel noch die Kontingente
fremder Anbieter.

### „Dieselben Tests" heißt nicht „bytegleich"

Preis, Abrufzeitpunkt und Teile der Metadaten ändern sich legitim. Gleich sind
**Szenarien und Invarianten**, nicht die Antwort selbst. Freshness beweist dabei
für sich genommen nichts — maßgeblich bleibt ein erfolgreicher Real-Lauf; die
Altersgrenze sorgt nur dafür, dass er nicht vergessen wird.

### Vor dem Commit einer Aufzeichnung

- **Bereinigen**: Kopfzeilen, Query-Parameter, Rumpf, Cookies und sensible
  Antwortfelder
- **Nutzungsbedingungen prüfen.** Rohe Anbieter-Antworten ins Repository zu
  legen, ist nicht bei jedem Dienst erlaubt — das gehört vor den ersten Commit
  geklärt, nicht danach

### Der Referenzweg: Transport und Uhr hereinreichen

Record/Replay wird unnötig schwer, wenn jedes Plugin seine HTTP-Bibliothek fest
verdrahtet. Der Vertrag **erzwingt** keine bestimmte Bibliothek — das Kit bietet
aber einen klaren Weg an:

- Beispielplugins bekommen Client/Transport **und Uhr per Konstruktor**
- das Kit stellt einen kleinen Replay-Transport bereit
- Real- und Replay-Modus tauschen nur diesen Transport
- der Offline-Lauf sperrt zusätzlich Socket-Zugriffe

Wer eine andere Bibliothek nutzt, schreibt einen eigenen Adapter — entscheidend
ist die von außen prüfbare Eigenschaft, nicht die Bibliothek. Die Dokumentation
zeigt trotzdem den hereingereichten Weg: Er ist für neu entstehende Plugins
deutlich einfacher und sicherer als ein selbstgebauter Mock-Aufbau.

---

## Auflösung

_(offen)_
