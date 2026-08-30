# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-37-yaml-fallback-ein-datei.md`
- `handoff_commit`: `1c70425`
- `review_round`: `4`
- `owner`: `codex`
- `updated_at`: `2026-08-30`
- `last_reviewed_ticket`: `T-37-yaml-fallback-ein-datei.md`
- `last_reviewed_commit`: `b464471`
- `last_reviewed_round`: `3`
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

**T-37 Runde 4 zur Prüfung** — `handoff_commit: 1c70425`

Der Block ist in einem Zug geschlossen. Vorab das, was Du zu Recht beanstandet
hast: **Meine Übergabe zu Runde 3 hat zu weit behauptet.** „Der Lade-Rand
lässt keinen Benutzerwert mehr entkommen" war eine Aussage über etwas, das ich
mit vier Beispielen geprüft hatte — nicht über die Grenze.

### 1 · Die Formgrenze, als Schicht statt als Beispielsammlung

`_require_list`, `_require_mapping`, `_require_text`, `_require_currency`,
`_require_version`. Jede Meldung nennt Fundort **und** verletzte Grenze:

```
Eintrag 'a'.history.closes[1] ist int statt eines Objekts
version ist True (bool) statt einer Ganzzahl aus [1]
Eintrag 'a': metadata.ter_bps = 5000.0 liegt außerhalb des Bereichs 0.5..500.0
```

**Die drei leeren Listen hatten dieselbe Ursache, und sie ist lehrreich:**
`or {}` macht aus *jedem* falsey Wert ein „fehlt". Wer `price: []` schreibt,
meint etwas — und bekam eine Datei, die tat, als stünde dort nichts.

**Zwei Fallen der Sprache selbst** steckten in der Version: `true` und `1.0`
galten als Fassung 1, weil `True == 1` und `1.0 == 1` in einer Menge von
Ganzzahlen gefunden werden. `isinstance(..., int)` genügt nicht, weil `bool`
eine Ganzzahl *ist*.

Die Kennzahlen prüfen jetzt gegen ihren eigenen `FieldSpec` — endlich **und**
im deklarierten Bereich. Eine TER von 5000 Basispunkten durchzulassen hieße,
den eigenen `FieldSpec` für Zierde zu halten.

**24 Mutanten**, jeder verbiegt genau **eine** Grenze an einem sonst
tadellosen Rumpf: Wurzel (7), Instrument (5), Unterblöcke (7), Kennzahlen (3),
Devisen (1), plus die Gegenprobe mit gültiger Datei. Zwei Fehler in einem
Mutanten belegten nicht, welcher gefunden wurde.

### 2 · Die beiden Ergebnisregeln

**Leeres Fenster** liefert jetzt eine leere `DailySeries` mit Währung und
`adjusted`. Leer heißt „hier nichts", unbekannt heißt „dieses Papier kenne ich
nicht" — das eine schickt den Aufrufer nicht weiter, das andere schon.

Eine Grenze habe ich dabei gezogen: **ohne gepflegten Verlauf bleibt es
`NotFound`.** Eine leere Reihe trüge eine Währung und ein `adjusted`, die
niemand genannt hat; das wäre eine Zusage aus dem Nichts.

**`ZZZ/ZZZ`** ist weder zuständig noch 1.0. Der Identitätskurs gilt nur für
eine echte Währung — einem Tippfehler 1.0 zu antworten hieße, einen Code zu
bestätigen, den ISO 4217 nicht vergibt.

### Läufe

| Lauf | Ergebnis |
|---|---|
| `pytest plugin_api` | 272 passed, 1 skipped (Runde 3: 252) |
| davon `test_yaml_file.py` | 112 |
| `pytest tests` | 917 passed, 29 skipped |
| `vitest run` | 269 passed |
| `ruff check app tests plugin_api` | All checks passed |
| `PROFILE=yaml` Smoke | 20/20 |

### Zur Konvergenzansage

Du hast geschrieben: Schließt die Grenzmatrix nicht in einem Zug, folgt eine
Konsolidierung des Validators statt einer weiteren Beispielrunde. Sie ist in
einem Zug geschlossen — und die Konsolidierung ist dabei ohnehin passiert:
Die fünf `_require_*`-Funktionen **sind** der Validator, und die Prüfungen im
Katalog rufen nur noch sie.
