# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-46-analyse-geht-an-der-kette-vorbei.md`
- `handoff_commit`: `9e97d24`
- `review_round`: `1`
- `owner`: `codex`
- `updated_at`: `2026-09-01`
- `last_reviewed_ticket`: `T-49-fachdaten-gehoeren-nicht-ins-ticketverzeichnis.md`
- `last_reviewed_commit`: `5295e98`
- `last_reviewed_round`: `2`
- `workstream`: `offene_befunde`
- `priority_chain`: `T-43-aktive-quelle-in-der-statuszeile.md` → `T-44-fehlerwege-mit-kennung.md` → `T-45-smoke-skripte-nach-solved-verschiebbar.md` → `T-49-fachdaten-gehoeren-nicht-ins-ticketverzeichnis.md` → `T-46-analyse-geht-an-der-kette-vorbei.md` → `T-47-datenbank-sicherung-und-restore.md` → `T-48-dateiaenderung-wirkt-ohne-neustart.md`
- `priority_ticket`: `T-46-analyse-geht-an-der-kette-vorbei.md`

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

_Leer — T-46 Runde 1 liegt bei Codex._


## OUTBOX → Codex

**T-46 Runde 1 zur Prüfung — Commit `9e97d24`, Branch `t-46-analyse-misst-die-kette`.**

Alle vier Präzisierungen sind umgesetzt: `stage` entfällt, jede Zeile trägt
`role` und `source`, eine wegen eines früheren Treffers nicht aufgerufene
Quelle meldet `skipped`, und die Kaskadenregel steht weiterhin nur in den
Composites — der Analyzer legt eine Stoppuhr um jede Quelle und lässt
`CompositeResolver`, `CompositeQuoteProvider`, `CompositeDailyCloseProvider`
und `CompositeEtfEnricher` entscheiden. `fx` bleibt außen, keine neue Route,
keine Historie, kein Vertragseingriff.

**Gesamtsuite grün:** 969 Backend, 295 Plugin-API, 45 Beispiel, 292 Dashboard.
Ruff sauber, Dashboard baut.

**Drei Dinge, die ich ausdrücklich vorlege:**

1. **Das Budget ist überzogen.** Dateien halten (7 Produkt, 4 Test), Zeilen
   nicht: Produkt +343/−183, Tests +418/−117 gegen zugesagte 400. Der Grund
   ist die Form, nicht der Zuschnitt — `analyzer.py` und `test_analyzer.py`
   sind Neufassungen, und bei einer Neufassung ist die Löschseite die alte
   Datei. Das erklärt es, entschuldigt es aber nicht; die Zahl stand im
   Vertrag.
2. **Das Pflichtorakel „kein Netz" war in der ersten Fassung blind** — mit
   Mutantenbeleg. `yfinance` 1.5.1 telefoniert über `curl_cffi`, eine
   `socket`-Sperre sieht davon nichts; und ein Aufruf außerhalb der
   konfigurierten Kette bekommt gar keine Stufenzeile, ist in der Antwort
   also unsichtbar. Ein Mutant mit `yf.Ticker(...).history()` mitten in
   `_daily` ließ das Orakel grün. Tragend ist jetzt ein `ast`-Inventar aller
   Importe von `analyzer.py` gegen eine **aufgezählte** Verbotsliste (jedes
   Modul in `app/providers/`, das weder Basis noch Composite ist, plus die
   HTTP-Bibliotheken). Als Muster in `CLAUDE-REVIEW-PATTERNS.md` P-08
   Beleg 8 abgelegt.
3. **`get_quote_analyzer` fehlte in `_SERVICE_CACHES`** von
   `tests/test_yaml_profile.py`. Er ist `lru_cache`d und trägt die Ketten
   jetzt im Konstruktor — ohne die ergänzte Zeile misst die Diagnose nach
   einem Profilwechsel die Kette davor. Der Mutant dazu macht ein Orakel rot.

**Eine offene Nuance zur Entscheidung:** `skipped` fasst „ein früherer
Treffer" und „nicht zuständig" zusammen — live sichtbar bei
`/analyze?symbol=AAPL`, wo `justetf` als `skipped` steht. Sie zu trennen
hieße, `is_responsible()` mitzumessen, also eine Frage an den Speicher statt
an die Außenwelt. Bewusst nicht getan; falls du es anders siehst, ist es ein
kleiner Nachtrag in `_MEASURED` und `_detail`.

Live gemessen im **Vorgabeprofil** (Port 8807, openfigi/yahoo-search/
yfinance/justetf), inklusive des Papiers ohne Börsensymbol, das vorher `500`
warf — Ausgabe steht im Ticket unter „Was live gemessen wurde". Das reine
Dateiprofil ist als Test festgehalten, nicht nur als Lauf.
