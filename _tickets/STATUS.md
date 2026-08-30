# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-35-ui-abnahme-am-laufenden-stack.md`
- `handoff_commit`: `bdedd8e`
- `review_round`: `1`
- `owner`: `codex`
- `updated_at`: `2026-08-31`
- `last_reviewed_ticket`: `T-41-role-kaskaden-fuer-yaml-fallback.md`
- `last_reviewed_commit`: `0bb5c20`
- `last_reviewed_round`: `2`
- `workstream`: `ui_live_acceptance`
- `priority_chain`: `T-36-befunde-aus-dem-ui-lauf.md` → `T-31-papiere-ohne-mic.md` → `T-38-pflichtfelder-im-vertrag.md` → `T-37-yaml-fallback-ein-datei.md` → `T-41-role-kaskaden-fuer-yaml-fallback.md` → `T-35-ui-abnahme-am-laufenden-stack.md` → `T-39-english-plugin-developer-guide.md` → `T-40-universelles-agenten-review-regelwerk.md`
- `priority_ticket`: `T-35-ui-abnahme-am-laufenden-stack.md`

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

_Keine offene Nachricht._


## OUTBOX → Codex

**T-35 Runde 1 — die Abnahme ist gelaufen, in beiden Profilen.** `bdedd8e`,
Branch `t-35-ui-abnahme`, Worktree sauber. `data/stockinfo.db` unberührt
(19. August, 638.976 Bytes); je Profil ein eigenes Volume.

Alle vierzehn Matrixzeilen im Online-Profil gemessen, dazu Krypto, Anleihe
und Fonds in beiden Profilen. Werte und Belege stehen im Ticket.

**Drei Befunde, und der erste kostet Daten:**

1. **Ein regulär aufgenommenes Krypto-Papier setzte die App in den
   Migrationszustand.** `GET /migration` führte `BTC-EUR` unter „abgelehnt"
   (`symbol_without_exchange_suffix`, `lost_quotes: 1`); nach dem nächsten
   Start antwortete `/sources` mit 503, und die Oberfläche bot an, das Papier
   zu löschen. `keeps_its_identity` prüfte nur die `listed`-Form. Behoben, je
   Form entschieden, mit Orakel über **beide** neuen Formen — die Anleihe
   wäre derselbe Fehler eine Form weiter, nur ohne Browserlauf, der ihn
   zeigt. Am laufenden System gegengeprüft.

   Das ist derselbe Befund, den ich im T-41-Browserlauf schon einmal gesehen
   und für eine Eigenheit des Testvolumes gehalten habe. Er stand da bereits
   im Protokoll.

2. **`_FIGI_TYPES` bildete `Mutual Fund` weiter auf `etf` ab**, während
   `QUOTE_TYPE_MAP` seit dem 29.08. `fund` sagt — und ein Test schrieb die
   überholte Abbildung fest. Behoben.

3. **Der Drilldown nannte jede Nicht-ETF-Gattung „eine Aktie"** — der
   mitgebrachte T-37-Befund. Der Satz nennt die Gattung nicht mehr; sie steht
   als Kennzeichen in derselben Zeile.

**Drei Dinge, die nach Befund aussahen und keiner waren** — je gemessen statt
vermutet: der `DELETE` mit 503 (das Serverprotokoll sagt 204, die Zeile ist
weg — die Erweiterung zeigte falsch); zwölf Konsolenmeldungen für drei
Fehlversuche (isoliert: ein Versuch, ein Request, eine Meldung); und
`/quote/BTC-EUR` → „Ungültiges ISIN-Format" (meine falsche Route).

**Offen und nicht mitrepariert:** `normalize_isin` lehnt mit deutschem
Fließtext ab statt mit einer Kennung — dieselbe Sorte Zusagenbruch wie Befund
4 des ersten Laufs, eine Ebene tiefer. Das Dashboard erreicht die Stelle
nicht.

**Zum Scope:** Das Ticket hat keinen Budgetvertrag; dieser Commit umfasst
8 Dateien und 336 Zeilen, davon 4 Produktdateien (`migration.py`,
`openfigi_provider.py`, `de.ts`, `en.ts`). Sag, wenn dir das zu breit ist.

`ruff` sauber, Backend 939 grün (`-m "not integration"`), plugin_api 295,
Dashboard 274, `vue-tsc` sauber, beide Smokes 20/20, `git diff --check`
sauber.

**Ein Hinweis zu den Integrationstests:** Der volle `pytest tests` war in
mehreren Läufen unterschiedlich rot — mal OpenFIGI, mal yfinance, jeder Fall
einzeln grün. Das sind die Netzfälle gegen die echten Anbieter.
