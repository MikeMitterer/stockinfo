# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-37-yaml-fallback-ein-datei.md`
- `handoff_commit`: `3e97a9e`
- `review_round`: `2`
- `owner`: `codex`
- `updated_at`: `2026-08-30`
- `last_reviewed_ticket`: `T-37-yaml-fallback-ein-datei.md`
- `last_reviewed_commit`: `472a5e9`
- `last_reviewed_round`: `1`
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

**T-37 Runde 2 zur Prüfung** — `handoff_commit: 3e97a9e`

Alle drei Befunde abgearbeitet. Sie waren berechtigt, und zwei davon hätte
keine Suite gefunden.

### 1 · Beim Laden wirklich validieren

`_Catalogue` prüft jetzt mit `stockinfo_plugin.invariants` — denselben
Funktionen, an denen der Host jede Antwort misst: Identitätsform, ISIN, MIC,
Währungen, Zeitpunkte mit Zone, positive endliche Beträge, doppelte
History-Tage und doppelte Wechselkurspaare. Jede Meldung nennt **Fundort und
verletzte Regel**; „ungültig" allein ist in einer Datei mit hundert Zeilen
keine Auskunft.

**Der stillste Fehler war der, den Du zuerst genannt hast.** Zwei Einträge mit
derselben ISIN widersprechen sich — bis hier gewann der zweite, weil die
Index-Zuweisung den ersten überschrieb. Die Datei sah gültig aus, und welcher
Eintrag galt, hing an der Zeilenreihenfolge.

| Riegel | Fälle |
|---|---:|
| Mutanten, je **eine** verletzte Regel, sonst tadellos | 8 |
| Gegenprobe mit gültiger Datei | 1 |
| Reload nach simuliertem Neustart, gemessen | 1 |

### 2 · Die Zusage war über den Host, nicht über die Quelle

Deine Messung — `reads 5` — trifft zu, und der Fehler war meine Formulierung.
„Einmal gelesen" ist nichts, was diese Datei zusagen kann: Der Host baut je
Rolle eine Instanz. Zugesagt ist jetzt **eine Datei, ein Parser, ein Schema**,
und das hält sie selbst.

Der Modul-Docstring sagt außerdem ausdrücklich, was *nicht* zugesagt wird und
warum eine rollenübergreifende Zwischenspeicherung hier keinem Problem
abhilft. Ticket und Orakel sind mitgezogen. Keine Cache-Architektur.

### 3 · Nur unterstützte Betriebswege dokumentieren

`sources.yaml.example` und `plugins.md` zeigten `yaml-file` am Ende jeder
Kette — genau die abgespaltene Kaskade. Beide zeigen jetzt das eigenständige
Profil und sagen den Satz, der fehlte: Ein Eintrag wie
`quotes: [yfinance, yaml-file]` **sieht aus wie ein Rückfall und ist keiner**.
`T-37-sources-online-with-yaml-fallback.yaml` trägt einen Banner und bleibt
als Entwurf liegen.

Entfernt oder umgestellt: `T-37-single-file-sample.csv`, der
Contract-Kit-Docstring, die tote `prices-file-quote`-Konfiguration im
vertikalen Test, und zwei aktive Verweise auf `canada_file`
(`examples/__init__.py`, Plugin-Spec).

Matrix nachgezogen: `#6` ist **⚠️ statt ✅** — solange der Drilldown eine
Anleihe „Aktie" nennt, stimmt „Drilldown … stimmen" nicht vollständig.

### Was ich bewusst nicht angefasst habe

Zwei Test-Doubles in `test_quote_service.py` heißen `prices-file-quote`. Das
ist ein frei gewählter Name für eine Quelle **ohne Metadaten**, nicht ein
Verweis auf das gelöschte Plugin; Deine Aufzählung nannte ihn nicht, und ein
Umbenennen wäre Diff ohne Aussage. Sag Bescheid, wenn Du es anders siehst.

### Läufe

| Lauf | Ergebnis |
|---|---|
| `pytest tests` | 917 passed, 29 skipped |
| `pytest plugin_api` | 160 passed, 1 skipped |
| `vue-tsc` / `vitest run` | ohne Befund / 269 passed |
| `ruff check app tests plugin_api` | All checks passed |
| `PROFILE=yaml` Smoke | 20/20 |

`PROFILE=online` steht **nicht** in dieser Liste: Ohne `yaml-file` in der
Kette ist er kein T-37-Beleg, wie Du geschrieben hast.

### Soll/Ist gegen Runde 1

| Wert | Runde 1 | jetzt |
|---|---:|---:|
| Diff-Zeilen gegen `472a5e9` | — | 997 |
| davon Tests/Doku | — | ~640 |

Der Zuwachs ist fast vollständig Prüfung: acht Mutanten, Gegenprobe,
Reload-Messung und die Doku-Korrekturen.
