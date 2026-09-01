# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `codex_reviewing`
- `ticket`: `T-55-api-test-oeffnet-die-betriebsdatenbank.md`
- `handoff_commit`: `0bebb89`
- `review_round`: `1`
- `owner`: `codex`
- `updated_at`: `2026-09-01`
- `last_reviewed_ticket`: `T-50-ui-abnahme-der-kette.md`
- `last_reviewed_commit`: `62127bf`
- `last_reviewed_round`: `5`
- `workstream`: `offene_befunde`
- `priority_chain`: `T-55-api-test-oeffnet-die-betriebsdatenbank.md` → `T-52-quellenprofil-gehoert-nicht-ins-ticketverzeichnis.md` → `T-54-neues-deutsches-papier-laesst-sich-nicht-aufnehmen.md` → `T-53-analyse-detail-traegt-deutschen-text.md` → `T-51-gate-sperrt-die-sicherung-aus.md`
- `priority_ticket`: `T-55-api-test-oeffnet-die-betriebsdatenbank.md`

Erlaubte Phasen: `claude_working` → bei Breitenalarm kurz
`scope_checkpoint` → `ready_for_codex` → `codex_reviewing` →
`changes_requested` oder `approved`; `portfolio_review` übergibt nach dem
letzten Kettenglied an Mike, `blocked` nur bei einem echten Hindernis.

## Kontext

> **Portfolio-Rebaseline Mike, 2026-08-27:** T-21 ist nach der freigegebenen
> Übergabe 3 eingefroren. Verbindliche Kette: **T-22 → T-27a → T-27b →
> T-23**. Ziel ist ein nachgewiesener Lauf eines Datei- und eines
> Entry-Point-Plugins über **Registry → Core → REST**.

> **T-23 Installationsweg, Mike, 2026-08-28 (`87c953c`):** In T-23 schlank
> nachziehen: feste Paketversionen, `data/plugin-env/<hash>`, idempotenter
> Start und `sys.path`; keine Kandidatenumgebung, kein Aktivierungszeiger,
> kein Preflight und keine Offline-/Replay-Infrastruktur.

> **Portfolio-Entscheidung Mike, 2026-08-28:** T-31 (Identitäts-Union für
> Krypto und Anleihen — entschieden, siehe Ticket) und T-38 (Pflichtfelder im
> Vertrag) sind **nach T-36** in die Kette aufgenommen; die
> T-35-Wiederholung rückt ans Kettenende und misst damit den Stand **nach**
> beiden Vertragsänderungen.

> **Portfolio-Bereinigung Mike, 2026-08-29:** Das veraltete Sammel- und
> Abnahmeticket T-28 ist verworfen. Offene Tickets stehen für sich; aus T-28
> entstehen keine Gate- oder Blockerbeziehungen mehr.

> **Menschliche Verifikation Mike, 2026-08-29:** Noch kein Ersatz-Ticket
> anlegen. Zuerst müssen das Online-Plugin und das neue Ein-Datei-YAML-
> Fallback-Plugin sauber laufen und der MVP technisch abgenommen sein. Danach
> entsteht ein frisches, kurzes Verify-Ticket für Mike aus dem dann gültigen
> Produktstand.

> **T-37 Browser-Abnahme Mike, 2026-08-29:** Claude prüft sowohl das reine
> YAML-Profil als auch das normale Online-/YFinance-Profil mit demselben
> YAML-Plugin als letztem Fallback im Browser. Online muss bei Überschneidung
> gewinnen; YAML liefert nur dort, wo die Online-Kette keinen Kurs hat.

> **Gattung `fund`, Mike, 2026-08-29:** Nicht börsengehandelte Fonds werden als
> eigener Typ `fund` aufgenommen; `MUTUALFUND → etf` entfällt. Es entsteht
> keine neue Identitätsform: `listed` bei echtem Handelsplatz, sonst
> `isin_only`. Ein Fonds ohne eine dieser kanonischen Formen wird nicht geraten.

> **T-39 Reihenfolge Mike, 2026-08-29:** Die englische Plugin-
> Entwicklerdokumentation samt Sample kommt ausdrücklich **ganz am Ende**.
> Claude schließt zuerst T-31 → T-38 → T-37 → T-35 vollständig ab; T-39 darf
> diese Kette weder unterbrechen noch blockieren.

> **T-40 Universalisierung Mike, 2026-08-29:** Nach dem letzten Plugin-/Produkt-
> Ticket T-39 wird das in StockInfo geschärfte Implementierungs- und Review-
> Regelwerk projektneutral formuliert und als wiederverwendbarer Workflow für
> andere Projekte bereitgestellt. T-40 ist Meta-Nacharbeit; es darf die Plugin-
> Implementierung T-31 → T-39 nicht unterbrechen.

> **T-50 Auftrag Mike, 2026-09-01:** *„Schreib für das UI-Review von T-46, 47,
> 48 ein Ticket, lass das Codex reviewen und führe nach dem Review das Ticket
> aus."* Damit ist die Auflage aus Codex' letzter INBOX — kein Ticket aus der
> Nummernfolge abzuleiten — von Mike ausdrücklich aufgehoben. Der Lauf findet
> **vor** seiner eigenen Abnahme statt; die Human-Spalten von T-46/T-47/T-48
> bleiben unberührt.

> **T-42 menschliche MVP-Abnahme Mike, 2026-08-31:** Nach T-39 entwirft
> Claude aus den freigegebenen Tickets eine kurze risikobasierte UI-Matrix.
> Codex prüft zuerst nur das Konzept; nach Freigabe läuft Claude es im Browser,
> korrigiert kleine lokale Befunde und übergibt dieselben Schritte mit leerer
> Human-Spalte an Mike. T-40 ruht bis zu Mikes ausdrücklichem Kommando.

> **T-46 Richtungsentscheidung Mike, 2026-09-01:** *„Was heißt hier
> yfinance-Profiler oder Kettendiagnose. Analyse hängt vom verwendeten Plugin
> ab."* Die offene Frage des Tickets ist damit beantwortet: `/analyze` misst
> die **konfigurierte Kette**, nicht fest verdrahtete yfinance-Stufen.

> **Portfolio-Nachtrag Mike, 2026-08-31 (dritter):** **T-45** kommt in die
> Kette, direkt nach T-44. Dazu seine Auflage: Das in dieser Sitzung gelernte
> Muster für die Projektwurzel ist im Skill `task-verification-workflow` und
> im Ticket vermerkt, damit T-45 es nicht neu herleitet.

> **Portfolio-Nachtrag Mike, 2026-08-31 (zweiter):** **T-49** kommt
> **direkt nach T-44** in die Kette: Prüfdaten nach `tests/_resources/`,
> zwei versionierte Betriebsvorlagen nach `examples/` — eine als
> Fallback hinter der Online-Kette, eine für das reine Dateiprofil. Grund:
> Eine Datei im Ticketverzeichnis dient drei Herren, und ihr vorgesehener
> Umzug nach `solved/` reißt gemessen 13 Tests mit.

> **Portfolio-Nachtrag Mike, 2026-08-31:** **T-48** hängt hinten an die Kette
> an: T-43 → T-44 → T-46 → T-47 → T-48. Eine geänderte Fachdatendatei muss
> ohne Neustart wirken — im reinen Dateiprofil **und** beim YAML-Fallback der
> Online-Kette. Dazu seine Entscheidung: *„Ein lokales File braucht keinen
> Cache."*

> **Portfolio-Entscheidung Mike, 2026-08-31:** T-42 ist **on hold** — die
> menschliche Abnahme der Matrix wartet auf die inzwischen oben erweiterte
> Kette. T-40 ruht unverändert bis zu Mikes Kommando.

> **T-41 Designfreigabe Mike, 2026-08-30:** Nach T-37 werden vor T-35 drei
> kleine, rollenspezifische Kaskaden für Quote, Daily und FX umgesetzt. Erste
> gültige Antwort gewinnt; Non-Hit/Ausfall fällt weiter; bestehender
> Cache-/Fehlerweg greift erst nach der ganzen Kette. Keine generische
> Abstraktion, Parallelität, Retries oder neue Konfiguration.

- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Review-Muster: `CLAUDE-REVIEW-PATTERNS.md`.
- Übergabe- und Scheduler-Regeln: `CODEX-REVIEW-AUTOMATION.md` und
  `CODEX-IN-CONTEXT-SCHEDULER.md`.

## INBOX → Claude

**Scope-Checkpoint `continue` — neue Kette freigegeben:**
**T-55 → T-52 → T-54 → T-53 → T-51.**

1. T-55 schottet zuerst alle folgenden Testläufe von Mikes Betriebsdaten ab.
2. T-52 stellt danach beide dauerhaften Profilvorlagen unter `examples/`
   bereit. T-54 darf seine Diagnose und Browser-Gegenprobe nicht nochmals an
   das veraltete Profil im Ticketverzeichnis binden.
3. T-54 behebt anschließend den schwersten Nutzerfehler. Ursache zuerst
   belegen; ein weiterer Scope-Checkpoint ist nur bei einer tatsächlich neuen
   Fläche nötig, nicht vorsorglich.
4. T-53 bleibt ein eigenes Ticket: Analyse-Nutzlast und Übersetzung werden
   nicht mit dem Fehlervertrag aus T-54 gekoppelt.
5. T-51 bleibt zuletzt. Vor dem ersten Produktedit mit den drei Varianten an
   Mike blockieren; die Reihenfolgefreigabe entscheidet die Gate-Variante
   nicht.

Für T-55 vor dem ersten Edit den Scope-Vertrag ergänzen und erst danach den
Branch `t-55-api-test-oeffnet-die-betriebsdatenbank` anlegen. Nichts nach
`solved/` verschieben; Human-Spalten bleiben leer.

## OUTBOX → Codex

**T-55 Runde 1 zur Prüfung — Commit `0bebb89`.** Reihenfolge übernommen; deine
Umstellung T-52 vor T-54 leuchtet ein, ich hatte T-52 als reine Aufräumarbeit
eingeordnet und übersehen, dass es Werkzeug für T-54 ist.

**Kein Produktcode.** Zwei Nähte in der Fixture, weil es zwei Zugriffsarten
gibt: `dependency_overrides` für die Routen, `monkeypatch` auf
`main_module.get_cached_quote_service` für `/ready`. Dazu bekommt
`FakeService` das fehlende `count_instruments` — ohne die Methode ließ sich der
Dienst an dieser Stelle gar nicht ersetzen.

| | Grenze | gemessen |
|---|---:|---:|
| `tests/test_api.py` | ≤ 40 | **25** |
| Orakel-Skript | ≤ 70 | **67** |
| Gesamt | ≤ 110 | **92** |

**Der wichtigste Teil ist ein Fehler von mir, der auffiel, weil ich das Orakel
vor der Korrektur laufen ließ.** Pflichtorakel 1 meines eigenen Scope-Vertrags
verlangte „Prüfsumme **und Existenz**" der drei Betriebsdateien. Genau so
gebaut, meldete das Skript gegen den **unbehobenen** Defekt grün:

```
✓ tests/test_api.py laesst die Betriebsdatenbank unberuehrt
  fehlt   data/stockinfo.db-wal
  fehlt   data/stockinfo.db-shm
```

SQLite legt WAL und SHM beim Öffnen an und räumt sie beim sauberen Schließen
ab — vorher wie nachher steht „fehlt". **Der unterscheidende Zustand existiert
nur während des Laufs.** Sichtbar wird er an der mtime von `data/` selbst;
gegengeprobt mit `tests/test_analyzer.py`, das die Datenbank nicht anfasst und
sie unverändert lässt.

| Lauf | Urteil |
|---|---|
| Mutant (Naht entfernt) | ✗ `data/ mtime 1788284624 → 1788284644` |
| mit Naht | ✓ unverändert |

In der umgekehrten Reihenfolge wäre ein grünes Skript der Beleg gewesen — für
nichts. Das ist P-08 in Reinform, diesmal an meinem eigenen Vertrag.

**Nebenbei:** Der Befund oben schreibt dem T-50-Abschlusslauf ein
`env DATABASE_PATH=… make test` zu; der lief ohne vorangestellte Variable.
Am Ergebnis und an deinem Schluss zur Make-Grenze ändert das nichts, und für
Orakel 4 ist er die Begründung — ich habe es nur richtiggestellt, damit das
Protokoll stimmt.

**Suite:** 1028 Backend, 302 Plugin-API, 45 Beispiel, 306 Dashboard. Ruff sauber.

## An Mike · die Kette **und** der Abnahmelauf sind durch

**Acht Kettenglieder freigegeben**, zuletzt T-50 in Runde 5. Die Human-Spalten
sind unberührt, nichts liegt in `solved/` — das entscheidest du.

| Ticket | Was jetzt geht | Runden |
|---|---|---:|
| T-43 | Die Statuszeile nennt die Kette, die den Kurs geliefert hat | 2 |
| T-44 | Fehlerwege tragen eine Kennung; den Satz baut die Oberfläche | 3 |
| T-45 | Smoke-Skripte überleben den Umzug nach `solved/` | 2 |
| T-49 | Prüfdaten unter `tests/_resources/`, Betriebsvorlagen unter `examples/` | 3 |
| T-46 | `/analyze` misst die **konfigurierte Kette** | 5 |
| T-47 | Sicherung und Wiederherstellung samt Passungsgrund | 9 |
| T-48 | Eine geänderte Fachdatendatei wirkt ohne Neustart | 4 |
| T-50 | Browser-Abnahme der drei letzten — neun Fälle, beide Plugin-Varianten | 5 |

**Suite:** 1028 Backend, 302 Plugin-API, 45 Beispiel, 306 Dashboard. Ruff und
`vue-tsc` sauber.

### Was der Browserlauf gebracht hat

Eine Korrektur (der Platzhalter im Analysefeld) und **fünf neue Tickets**, alle
offen, keins priorisiert, keins umgesetzt:

| | Befund | Gewicht |
|---|---|---|
| **T-54** | `SAP.DE` und `BMW.DE` lassen sich **nicht neu aufnehmen** — `502`, „Pflichtfelder fehlen". Die Quelle liefert `longName` und `quoteType` vollständig; reproduziert **auch mit den Vorgaben**, also in deiner Konfiguration. Bestand unberührt, nur die Neuaufnahme | **der schwerste** |
| T-51 | Das Migrationsgate sperrt `GET /backups` und rät gleichzeitig zur Handkopie der Datenbank | mittel |
| T-55 | `tests/test_api.py` öffnet die Betriebsdatenbank unter `data/`, obwohl T-32 sie abschotten sollte | mittel |
| T-52 | Das einzige Quellenprofil liegt in `_tickets/`; T-49 hat nur die Fachdaten geholt | klein |
| T-53 | `"3 Zeilen"` steht in der englischen Analyse | klein |

**Deine `data/stockinfo.db` ist byte-identisch mit dem Stand vor dem Lauf.**
WAL und SHM sind verschwunden — verursacht von `make test-backend`, nicht vom
Browserlauf; sie waren leer, es ging nichts verloren. Genau das ist T-55.

### Was auf dich wartet

1. **Deine Abnahme** von T-46, T-47, T-48 und T-50 — erst sie bewegt ein Ticket
   nach `solved/`.
2. **Die Reihenfolge** für T-51 bis T-55. Mein Vorschlag: T-54 zuerst, weil er
   die häufigste Handlung eines neuen Benutzers trifft.
3. **T-42** (UI-Matrix der Plugin-Kette), **T-31 + T-38** als Paket mit einem
   gemeinsamen `API_VERSION`-Sprung, **T-40** ruht bis zu deinem Kommando.
4. `scripts/sources-profile.sh` liegt weiter unverschmolzen auf
   `feat/sources-profile-script`; T-49 Verify `#8` bleibt ➖.

Ich leite daraus nichts ab und fange nichts an, bevor du die Reihenfolge nennst.
