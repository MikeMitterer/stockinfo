# T-27 · Test-Infrastruktur für Plugins

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (`plugin_api/`) | offen | 1 Tag | Testwerkzeug im Vertragspaket, zweites Beispiel-Plugin | — |

**Löst:** Der Contract-Test ist das Hauptargument dafür, dass ein weltweites
Plugin-System überhaupt tragfähig ist — „Tests, die andere für uns laufen
lassen". Er deckt heute aber nur **eine Ebene** ab: eine einzelne Quelle,
isoliert, ohne Netz.

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

**Hängt an:** nichts für die Fake→Real-Grundlage. Die Ketten- und
Registry-Doubles brauchen T-20 bzw. T-23 als Gegenstand.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | HTTP-Plugin, Contract-Lauf **ohne Netz** | läuft gegen aufgezeichnete Antworten, schnell und wiederholbar | | |
| 2 | dasselbe Plugin, Lauf **mit** Netz (`--real`) | dieselben Testfälle gegen die echte API | | |
| 3 | Aufzeichnung erneuern | dokumentierter Weg; Schlüssel werden dabei **nicht** mitgeschrieben | | |
| 4 | Aufzeichnungsdatei | enthält keinen API-Key, kein Token, keinen Cookie | | |
| 5 | `FakeSource` aus dem Testkit | erlaubt, eine Kette zu bauen, ohne ein echtes Plugin zu schreiben | | |
| 6 | Kette aus drei Doubles | `NotResponsible` überspringt, `Unavailable` schaltet weiter, Reihenfolge ist prüfbar | | |
| 7 | absichtlich kaputte Test-Plugins | Registry lehnt falsche `api_version`, doppelte Namen und Importfehler ab — automatisiert geprüft | | |
| 8 | Plugin, das hängt | Schutzschalter greift im Test, **ohne** echte Wartezeit | | |
| 9 | zweites Beispiel-Plugin | spricht eine echte HTTP-API, nicht nur eine lokale Datei | | |
| 10 | `make test-plugin-api` | grün, ohne Netzzugriff | | |

```bash
# #1/#10 — schneller Lauf, aufgezeichnete Antworten
make test-plugin-api

# #2 — Gegenprobe gegen die echte API (braucht Netz und ggf. Schlüssel)
cd plugin_api && pytest --real
```

---

## Details

### Das Kernproblem: das Beispiel ist zu bequem

`CanadaFileResolver` liest eine lokale CSV — kein HTTP, keine Anmeldung, keine
Rate-Limits. Damit beweist die Skizze **nicht**, dass der Vertrag für den Fall
trägt, um den es eigentlich geht: eine REST-Quelle wie EODHD oder Twelve Data.

Ein Autor mit HTTP-Plugin müsste heute bei jedem Contract-Lauf echte Requests
machen — langsam, unzuverlässig, und es verbraucht sein Kontingent. Das schwächt
genau das Argument, mit dem dieses Vorhaben begründet ist.

### Fake → Real, der Hausstandard

`code-standards` beschreibt das Muster bereits, und es wurde beim Entwurf des
Vertragspakets übersehen: Dieselben Testfälle laufen gegen eine **aufgezeichnete**
und gegen die **echte** Quelle.

- Vorgabe ist der schnelle Lauf gegen Aufzeichnungen — kein Netz, deterministisch
- `--real` fährt dieselben Fälle gegen die API, für Releases und beim Erneuern
- Die Aufzeichnung entsteht über einen dokumentierten Weg und wird **um
  Geheimnisse bereinigt**, bevor sie ins Repository geht

Damit wird auch prüfbar, was heute niemand prüft: ob eine Aufzeichnung noch zur
API passt.

### Doubles für Ketten und Registry

Im Vertragspaket gibt es derzeit **keine einzige** `FakeSource`. Wer die
Kettenlogik testen will — Reihenfolge, Weiterschalten, Schutzschalter — muss
sich Doubles selbst bauen. Das gehört ins Testkit:

- `FakeSource` mit vorgebbarer Antwort je Anfrage (`Resolved`, `NotResponsible`,
  `NotFound`, `Unavailable`, „wirft", „hängt")
- absichtlich fehlerhafte Test-Plugins als Fixtures für die Registry: falsche
  `api_version`, doppelter Name, Importfehler, widersprüchliche Felddeklaration
- eine einspeisbare Uhr, damit TTL, Schutzschalter-Fenster und Rotation ohne
  echte Wartezeit prüfbar sind

### Was das Testkit nicht leisten kann

Contract-Tests beweisen **Form und Fehlerverhalten**, nicht fachliche Richtigkeit.
Dass ein Plugin das *richtige* Listing wählt, sagen sie nicht — dafür braucht es
jemanden vor Ort mit einem echten Papier. Diese Grenze gehört in die
Plugin-Dokumentation, damit sie niemand für mehr hält, als sie ist.

---

## Auflösung

_(offen)_
