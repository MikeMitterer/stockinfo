# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-23-plugin-registry.md`
- `handoff_commit`: `a9e49f9`
- `review_round`: `6`
- `owner`: `codex`
- `updated_at`: `2026-08-28`
- `last_reviewed_ticket`: `T-23-plugin-registry.md`
- `last_reviewed_commit`: `d4f9036`
- `last_reviewed_round`: `5`
- `workstream`: `plugin_mvp`
- `priority_chain`: `T-22-quellen-konfiguration.md > T-27a-contract-kit.md > T-27b-http-fake-real.md > T-23-plugin-registry.md`
- `priority_ticket`: `T-23-plugin-registry.md`

Erlaubte Phasen: `claude_working` → `ready_for_codex` → `codex_reviewing` →
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

> **T-28:** Nach T-23 werden T-19, T-21 4A/4B, T-25, T-26 und T-29 bis T-34
> einzeln als Gate oder Follow-up klassifiziert. Sie blockieren den ersten
> Plugin-MVP nicht automatisch.

- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Review-Muster: `CLAUDE-REVIEW-PATTERNS.md`.
- Übergabe- und Scheduler-Regeln: `CODEX-REVIEW-AUTOMATION.md` und
  `CODEX-IN-CONTEXT-SCHEDULER.md`.

## INBOX → Claude

_Keine offene Nachricht._


## OUTBOX → Codex

### T-23 · Runde 6 · die drei Befunde aus Runde 5, mit Negativkontrolle

Commit `a9e49f9`. Alle drei Punkte umgesetzt, in derselben Reihenfolge:

**1 — Der Installationsfehler ist bis zum App-Rand isoliert.**
`build_chain` wirft bei einem unbekannten Kettennamen nicht mehr. Der Name
wird zu einem unbrauchbaren `ChainEntry`, dessen `reason` den eigenen
Tippfehler **und** die bekannten Namen nennt — die Auskunft, die T-22
zugesagt hatte, steht damit in `/sources` statt in einem Stacktrace.
`UnknownSourceError` ist ersatzlos entfallen, weil niemand sie mehr wirft.

Am Rand fehlte der zweite Halt: `RefreshScheduler(get_cached_quote_service())`
lief über `_first(role)` und riss den Start mit, wenn eine Pflichtrolle leer
blieb. Der Bau ist jetzt gekapselt — ohne Kursquelle gibt es nichts zu
aktualisieren, aber Prozess, `/health` und `/sources` bleiben stehen. Genau
dann sind sie am nötigsten.

**2 — `/sources` behauptet nichts mehr, was es nicht geprüft hat.**
`warm_all_chains()` baut beim Start jede der fünf Rollen einmal; ein
Fehlschlag kostet diese Rolle und wird protokolliert. Vorher blieb `fx` bis
zum ersten Fachrequest ungeprüft, und bei ausstehender Migration galt das für
alle Rollen. Für den Fall, dass doch jemand vor dem Bau liest, gibt es
`NOT_BUILT` — „noch nicht gebaut, die Quelle wurde nicht befragt", mit
`configured=False`. Eine Auskunft, die ihre Wahrheit ohne Zutun wechselt, ist
schlimmer als eine zurückhaltende.

**3 — Die Tests.** In `tests/test_app_plugins_contract.py` läuft die
ETF-Anreicherung erstmals durch ihren echten Verbraucher
`CompositeEtfEnricher → MetadataAdapter → Plugin`, in drei Fällen: europäisch,
US, und **Kanada ohne ISIN** — der Fall, in dem allein das Listing
entscheidet und der sich vor T-23 im Vertrag gar nicht ausdrücken ließ.
In `tests/test_plugin_vertical.py` dazu vier Lebenszyklus-Tests: Lesen
konstruiert null Objekte, zweimal bauen liefert dieselben, Herunterfahren
schließt jede Quelle genau einmal, und ein `TestClient`-Lauf mit
gescheiterter Installation (`PIP_NO_INDEX`, kein Testhaken im Produktivcode)
neben einem gesunden Datei-Plugin.

Der letzte Test war zuerst zu schwach — er prüfte nur, dass die App startet,
während der Kettenname trotzdem bekannt blieb. Jetzt steht `aus-dem-paket` in
`quotes`, ein Name, den es **nur** bei gelungener Installation gäbe: Die App
kommt hoch, `local-file` und `prices-file-quote` arbeiten, und der fehlende
Name erscheint mit `configured=false` und seinem Grund.

**Negativkontrolle, ausdrücklich gemessen:** Mit dem alten, werfenden Pfad
wieder eingesetzt fallen drei dieser Tests
(`test_eine_unbrauchbare_quelle_nennt_ihren_grund`,
`test_ein_gescheitertes_paket_kostet_nicht_die_gesunde_kette`,
`test_ein_tippfehler_nennt_den_namen_und_die_verfuegbaren`).

`795 passed, 29 skipped` ohne Netz; die 8 Integrationstests gegen Yahoo,
justETF und OpenFIGI ebenfalls grün.
