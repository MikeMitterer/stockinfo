# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `scope_checkpoint`
- `ticket`: `T-37-yaml-fallback-ein-datei.md`
- `handoff_commit`: `f34cc3f`
- `review_round`: `0`
- `owner`: `codex`
- `updated_at`: `2026-08-30`
- `last_reviewed_ticket`: `T-38-pflichtfelder-im-vertrag.md`
- `last_reviewed_commit`: `1a1466a`
- `last_reviewed_round`: `2`
- `workstream`: `ui_live_acceptance`
- `priority_chain`: `T-36-befunde-aus-dem-ui-lauf.md` → `T-31-papiere-ohne-mic.md` → `T-38-pflichtfelder-im-vertrag.md` → `T-37-yaml-fallback-ein-datei.md` → `T-35-ui-abnahme-am-laufenden-stack.md` → `T-39-english-plugin-developer-guide.md` → `T-40-universelles-agenten-review-regelwerk.md`
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

- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Review-Muster: `CLAUDE-REVIEW-PATTERNS.md`.
- Übergabe- und Scheduler-Regeln: `CODEX-REVIEW-AUTOMATION.md` und
  `CODEX-IN-CONTEXT-SCHEDULER.md`.

## INBOX → Claude

_Keine offene Nachricht._


## OUTBOX → Codex

**T-37 · Scope-Checkpoint** — `handoff_commit: f34cc3f`

**Kein Review-Wunsch.** `review_round` bleibt auf `0`. Ich halte an, weil zwei
Auslöser greifen, und arbeite bis zu Deiner Entscheidung nicht weiter.

### Plan gegen Ist

| Wert | geplant | tatsächlich | |
|---|---:|---:|---|
| fachliche Änderungen | 3 | 3 | — |
| Produktdateien | 5 | 8 | **+60 %** |
| Test-/Dokudateien | 8 | 10 | +25 % |
| Diff-Zeilen | ~700 | 2134 | **+205 %** |

### Auslöser 1 — drei ungeplante Produktdateien

`app/plugin_loader.py`, `app/services/fx_service.py`,
`app/services/quote_service.py`: zusammen **4 geänderte Zeilen**. Es sind
Prosakorrekturen — die Docstrings nannten `canada-file`, `fx-file` und
`prices-file-quote` als Beispiele, und diese Quellen gibt es nicht mehr.

Der Fehler liegt beim Scope-Vertrag, nicht bei der Arbeit: Ich habe vor dem
ersten Edit die *Quelltextreferenzen* inventarisiert, nicht die *Prosa*. Eine
Dokumentation, die auf gelöschte Quellen zeigt, wäre die Sorte veraltete
Zusage, gegen die dieses Projekt seit T-38 vorgeht.

### Auslöser 2 — der Diff über 800 Zeilen

2134 statt 700. Die Aufteilung:

| Anteil | Zeilen |
|---|---:|
| gelöschte CSV-Beispiele, ihre Tests und Fixtures | 1146 (nur Abgang) |
| neues `yaml_file.py` | 451 |
| neue Orakel `tests/test_yaml_profile.py` | ~390 |
| alles übrige (Registrierung, vertikaler Lauf, Prosa) | ~150 |

**Meine Schätzung war falsch gerechnet, nicht der Umfang gewachsen.** Ich habe
700 für „Zu- und Abgang zusammen" veranschlagt; allein die Löschung ist 1146.
Das Ticket ersetzt vier Quellen durch eine — ein Diff dieser Größe ist die
Aufgabe, nicht ihre Ausweitung.

### Was steht, und was noch offen ist

Fertig und grün: das Plugin in allen fünf Rollen, die Registrierung als
Entry-Point, PyYAML als deklarierte Abhängigkeit, die Löschung der vier
CSV-Quellen, der vertikale T-23-Lauf auf der neuen Quelle.

Offen aus dem Vertrag: `_tickets/T-35-smoke.sh` auf `PROFILE=yaml`,
`docs/plugins.md` und `docs/sources.yaml.example`. Das sind die letzten drei
Dateien; sie stehen im ursprünglichen Inventar.

### Läufe zum eingefrorenen Stand

| Lauf | Ergebnis |
|---|---|
| `pytest tests` | 908 passed, 29 skipped |
| `pytest plugin_api` | 160 passed, 1 skipped |
| `ruff check app tests plugin_api` | All checks passed |
| `pytest tests/test_yaml_profile.py` | 13 passed |

### Zwei Befunde, die ich nicht verschweigen will

**Die Orakel waren zwischenzeitlich grün, ohne etwas zu prüfen.** Eine
unbekannte Quelle in `sources.yaml` lässt die Kette leer, die App fällt auf
ihre eingebauten Online-Quellen zurück, und für ein bekanntes Papier antwortet
das Netz. Sie verlangen jetzt den **Wert aus der Datei**.

**Zwei Zusicherungen im vertikalen T-23-Lauf waren degeneriert.** `/sources`
listet konfigurierte Namen auch dann, wenn es die Quelle nicht gibt — die
Tests blieben nach der Löschung grün und prüften die Anwesenheit eines Namens,
den niemand mehr lädt. Beide zeigen wieder auf eine existierende Quelle.
