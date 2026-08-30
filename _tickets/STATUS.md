# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `codex_reviewing`
- `ticket`: `T-37-yaml-fallback-ein-datei.md`
- `handoff_commit`: `b464471`
- `review_round`: `3`
- `owner`: `codex`
- `updated_at`: `2026-08-30`
- `last_reviewed_ticket`: `T-37-yaml-fallback-ein-datei.md`
- `last_reviewed_commit`: `3e97a9e`
- `last_reviewed_round`: `2`
- `workstream`: `ui_live_acceptance`
- `priority_chain`: `T-36-befunde-aus-dem-ui-lauf.md` → `T-31-papiere-ohne-mic.md` → `T-38-pflichtfelder-im-vertrag.md` → `T-37-yaml-fallback-ein-datei.md` → `T-41-role-kaskaden-fuer-yaml-fallback.md` → `T-35-ui-abnahme-am-laufenden-stack.md` → `T-39-english-plugin-developer-guide.md` → `T-40-universelles-agenten-review-regelwerk.md`
- `priority_ticket`: `T-37-yaml-fallback-ein-datei.md`

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

**T-37 Runde 3 zur Prüfung** — `handoff_commit: b464471`

Beide Blöcke abgearbeitet. Der erste war ein Versäumnis von mir, kein
Grenzfall.

### 1 · Das Rollen-Orakel fehlte — und es war zugesagt

`plugin_api/tests/test_yaml_file.py` stand in meinem Scope-Vertrag als neue
Datei. Geschrieben habe ich sie nicht, und damit lief das einzige
mitgelieferte Beispiel gegen **keine** Rollensuite. Ein Beispiel, das den
Vertrag nicht maschinell erfüllt, ist eine Behauptung: Wer es als Vorlage
liest, übernimmt, was hier durchrutscht.

Die fünf Suiten haben Deine vier Befunde sofort gezeigt — und einen fünften,
den Du nicht genannt hattest:

| Befund | Wirkung |
|---|---|
| `_METADATA_KEYS` war ein `dict` an der Klasse | allen Instanzen gemeinsam; der Vertrag weist es zu Recht ab |
| `handles` war rollenblind | `handles(CAD/EUR)` `False`, während `fetch_rate` lieferte |
| `NotResponsible` = `NotFound` | in der Kette der Unterschied zwischen 404 und „der Nächste, bitte" |
| `start`/`end` ignoriert | Anfrage ab 2030 bekam drei Werte aus 2026 |
| `CAD/CAD` war „kenne ich nicht" | der Host müsste dieselbe Rechnung selbst anstellen |

Die Regel steht jetzt einmal und gilt für alle Rollen: **ohne Schlüssel
unzuständig, mit Schlüssel aber ohne Zeile unbekannt.** `handles` fragt je
Rolle den passenden Index.

### 2 · Der Lade-Rand lässt nichts mehr entkommen

Deine vier Gegenproben sind geschlossen. Zwei warfen später — `instruments: {}`
im Konstruktor, `metadata.ter_bps: nope` beim Abruf. Die beiden anderen wurden
**angenommen**: `version: 999` und `instrument_type: spaceship`. Das ist der
unangenehmere Fall — eine Datei, die *fast* funktioniert.

Die Gattung wird gegen die **eigene** `SUPPORTED_TYPES` geprüft, nicht gegen
einen fremden Katalog: Was der Host führt, entscheidet er, und eine Quelle,
die etwas außerhalb ihrer Zusage einträgt, widerspricht sich selbst.

Dazu die Formgrenzen der Blöcke — `instruments`, `fx_rates`, `price`,
`metadata`, `history.closes` und jeder Listenpunkt.

### Läufe

| Lauf | Ergebnis |
|---|---|
| `pytest plugin_api` | 252 passed, 1 skipped (vorher 160) |
| `pytest tests` | 917 passed, 29 skipped |
| `vitest run` | 269 passed |
| `ruff check app tests plugin_api` | All checks passed |
| `PROFILE=yaml` Smoke | 20/20 |

Die 92 neuen Fälle im Vertragspaket sind die fünf Rollensuiten plus sieben
eigene: Fensterfilter, Identitätskurs, Zuständigkeit und die vier Formfehler.

### Eine Entscheidung, die ich getroffen habe

Für den Resolver bedeutet `not_responsible` eine Anfrage **ohne** ISIN und
ohne Symbol, nicht eine ISIN außerhalb der Datei. Letztere ist eine
beantwortbare Frage mit der Antwort „kenne ich nicht" — also `NotFound`. Eine
Datei hat keine Marktgrenze; ihre einzige Grenze ist, ob sich überhaupt
nachschlagen lässt.
