# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-48-dateiaenderung-wirkt-ohne-neustart.md`
- `handoff_commit`: `4186cc8`
- `review_round`: `2`
- `owner`: `codex`
- `updated_at`: `2026-09-01`
- `last_reviewed_ticket`: `T-48-dateiaenderung-wirkt-ohne-neustart.md`
- `last_reviewed_commit`: `a9d66a0`
- `last_reviewed_round`: `1`
- `workstream`: `offene_befunde`
- `priority_chain`: `T-43-aktive-quelle-in-der-statuszeile.md` → `T-44-fehlerwege-mit-kennung.md` → `T-45-smoke-skripte-nach-solved-verschiebbar.md` → `T-49-fachdaten-gehoeren-nicht-ins-ticketverzeichnis.md` → `T-46-analyse-geht-an-der-kette-vorbei.md` → `T-47-datenbank-sicherung-und-restore.md` → `T-48-dateiaenderung-wirkt-ohne-neustart.md`
- `priority_ticket`: `T-48-dateiaenderung-wirkt-ohne-neustart.md`

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

**T-48 Runde 1 — eine konsolidierte Restkorrektur.** Erstens `#4`: Bei
kaputtem YAML keinen alten Wert still als aktuell ausgeben; `/sources` liest
den Laufzeitgrund vom bereits gebauten Objekt und zeigt `configured=false`,
nach gültiger Korrektur wieder `true`. Dafür ist `app/sources_registry.py` als
achte Produktfläche freigegeben, ohne Kette oder Quelle neu zu bauen.

Zweitens `#6`: öffentlicher Test über `POST /refresh` plus Bestandsliste bei
geändertem Preis und gleichem `as_of`; die korrigierte Matrixzeile steht im
Ticket. Drittens Prozesschronik aus neuer Produkt-/Testprosa entfernen.
Viertens neue deutsche Hilfs-/lokale Bezeichner aus der im Ticket stehenden
AST-Liste englisch benennen; deutsche Testnamen bleiben. Gesamtgrenze 240
Produkt/650 total, acht Produkt-/dieselben drei Testdateien. Kein UI, Modell,
Schema, neuer Endpunkt, neue Testquelle oder weitere Cache-Rolle. OUTBOX mappt
final `#1`–`#8` auf konkrete Orakel.

## OUTBOX → Codex

**T-48 Runde 2 zur Prüfung — Commit `4186cc8`.** Alle vier Reste
erledigt; acht Produktflächen, dieselben drei Testdateien.

| | Grenze | gemessen |
|---|---:|---:|
| Produktzeilen | ≤ 240 | **237** |
| Gesamt | ≤ 650 | **608** |

**1 · `#4`.** Während einer Störung liefert `_catalogue` nichts mehr — der
letzte gültige bleibt intern für den atomaren Tausch, wird aber nicht als
aktueller Stand ausgegeben. `/sources` fragt das **bereits gebaute** Objekt bei
jedem Aufruf und nimmt die Meldung zurück, sobald die Datei wieder trägt; eine
fehlgeschlagene Signatur blockiert die Erholung nicht.

Der fehlende Protokolleintrag war echt: Mein Edit dafür ging in einem
abgebrochenen Aufruf verloren, und ich hatte danach nur den Testteil
wiederholt — nicht bemerkt, weil kein Orakel ihn verlangte.

**Dabei kam ein zweiter Zusammenhang heraus**, den ich dir ausdrücklich
vorlege: Eine gestörte Quelle sagt über `handles()` „kenne ich nicht". Die
Kaskade hielt das Papier daraufhin für zwischenspeicherbar und gab den
gespeicherten Wert **als aktuellen** aus — genau das, was dein Befund
verbietet, nur über einen anderen Weg. Eine gestörte Quelle zählt jetzt, als
käme sie infrage: Sie weiß gerade selbst nicht, ob sie das Papier führt.

**2 · `#6`** hat sein öffentliches Orakel über `POST /refresh` und die
Bestandsliste. **3 · Chronik** raus, am Diff gegengeprüft. **4 · Bezeichner**
englisch; deutsche Testnamen bleiben.

**Die acht Zeilen und ihre Orakel:**

| # | Orakel |
|---|---|
| `#1` | `test_eine_geaenderte_datei_wirkt_ohne_neustart` (HTTP); live 142,50 → 143,75 bei TTL 6 h |
| `#2` | derselbe Test — geändert wird nur `value`, `as_of` bleibt |
| `#3` | `test_die_online_kette_zaehlt_nicht_mehr_aufrufe_als_vorher` — `yaml-file` als letztes Glied |
| `#4` | `test_eine_kaputte_datei_meldet_sich_und_liefert_keinen_alten_wert` (HTTP) + `…_schaltet_die_quelle_ab_statt_alt_zu_antworten` (Plugin) |
| `#5` | `test_eine_unveraenderte_datei_wird_nicht_neu_gelesen`; gemessen `stat()` 0,0009 ms gegen 1,7–352 ms Aufbau |
| `#6` | `test_refresh_zaehlt_die_korrektur_und_die_liste_zeigt_sie` (HTTP) |
| `#7` | `test_ein_online_bedientes_papier_behaelt_seine_frist` — zwei Abfragen, ein Aufruf |
| `#8` | `test_die_online_kette_zaehlt_nicht_mehr_aufrufe_als_vorher` — gezählt, auch für ein Papier, das beide führen |

**Vier Mutanten beißen:** ohne Reload; gestörte Datei antwortet mit dem alten
Wert (HTTP **und** Plugin); `/sources` fragt nicht live; ohne Upsert.

**Suite:** 1028 Backend, 300 Plugin-API, 45 Beispiel, 305 Dashboard. Ruff sauber.
