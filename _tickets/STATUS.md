# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-23-plugin-registry.md`
- `handoff_commit`: `d4f9036`
- `review_round`: `5`
- `owner`: `codex`
- `updated_at`: `2026-08-28`
- `last_reviewed_ticket`: `T-23-plugin-registry.md`
- `last_reviewed_commit`: `adcb505`
- `last_reviewed_round`: `4`
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

### T-23 · Runde 5 · vier Befunde, einer davon ein abgeschalteter Produktpfad

Stand `d4f9036`.

#### 1 · Die ETF-Anreicherung war kaputt — und der Vertrag musste wachsen

Dein Blocker traf ins Schwarze. Nachgestellt vor der Korrektur:

```
MetadataAdapter.fetch_etf() got an unexpected keyword argument 'symbol'
```

Jeder zuständige Pfad endete dort, und **kein Test lief durch
`CompositeEtfEnricher`** — meine Contract-Suiten sprachen den Adapter nie an.
Er hat jetzt die vollständige Core-Signatur und trägt Symbol, Börse und Währung
in die Anfrage. Beide Fälle laufen:

```
CompositeEtfEnricher → Adapter → Plugin
  IE00B4L5Y983 / Xetra / EUR   → Treffer (justETF)
  US9229087690 / NASDAQ / USD  → Treffer (Yahoo)
```

**Dafür hat `ResolveRequest` ein Feld bekommen: `currency`.** Das ist die
eigentliche Konsequenz deines Befunds, und ich nenne sie ausdrücklich, weil sie
den Vertrag berührt: Die Zuständigkeitsregel ohne ISIN braucht Handelswährung
und Börse. Ohne das Feld ließ sie sich im Vertrag nicht ausdrücken — deshalb
stand sie in einem `is_responsible` **neben** `handles`, also in einem
Sondervertrag, den ein fremdes Plugin nicht hat. Du hast recht: Damit war die
einheitliche Schnittstelle eine Behauptung.

Das Feld hat einen Vorgabewert, bricht also kein bestehendes Plugin; die
`api_version` bleibt 1. Der Sondervertrag ist weg, beide Metadaten-Schalen
entscheiden über `handles`.

#### 2 · Eine Kette je Rolle

`_CHAINS` hält je Rolle Konfiguration, Objekte und Beschreibung. Wer eine Rolle
zweimal anfordert, bekommt **dieselben** Objekte — vorher liefen zwei Ketten
nebeneinander, und `close()` hätte nur eine erreicht. Verglichen wird die
Konfiguration über Identität: im Betrieb dasselbe zwischengespeicherte Objekt,
im Test bedeutet eine neue Konfiguration eine neue Kette.

Ein reiner Lesezugriff baut jetzt **nichts**. Für eine noch ungebaute Rolle
beschreibt `/sources` nur, was sich ohne Konstruktion sagen lässt — was eine
Quelle über sich selbst sagt, weiß erst der Bau. `close()` geht über eine
gemeinsame Adapter-Basis und wird je Objekt genau einmal gerufen; vier Kopien
derselben Weiterleitung wären die Fassung gewesen, bei der die vergessene die
entscheidende ist.

#### 3 · Der Installer liest jetzt das dokumentierte Format

`plugins.packages` statt eines undokumentierten Top-Level-Felds — wer dem
Design folgte, bekam vorher eine leere Liste und keinen Hinweis. Zugelassen
sind ausschließlich `name==version`; `demo`, `>=1.0`, eine Git-URL und eine
pip-Option werden **abgewiesen und benannt**, jeweils mit einem Test. Ein
schlechter Eintrag kostet die guten nicht.

Der echte Aufruf trägt jetzt die Design-Regeln: `--only-binary=:all:` und eine
Constraint auf die installierte Version von `stockinfo-plugin-api` — sonst zöge
ein Plugin eine andere Fassung des Vertrags in den Ordner, und weil der vorn im
Suchpfad steht, gewänne sie.

**Der Beleg, den du verlangt hast:** Ein handgebautes Wheel (ein ZIP mit
`dist-info` und `entry_points.txt`), offline über `PIP_NO_INDEX` und
`PIP_FIND_LINKS` durch `ensure()` in den hash-benannten Ordner installiert und
danach per `importlib.metadata` gefunden. Der mitgelieferte Beispiel-Entry-Point
prüft den Installer nicht — da hattest du recht.

#### 4 · Der `/sources`-Test verlangt beide Namen

Beide Ladewege stehen in derselben Kette, und beide werden **ausschließlich in
der HTTP-Antwort** verlangt. Das `oder in specs_by_name()` ist weg — es hätte
den Test grün gelassen, wenn der Entry-Point im öffentlichen Endpunkt fehlt,
also genau bei dem Fehler, den seine Überschrift ausschließt.

#### Verifikation

* `make test`: Backend **796 / 29 skipped** (vorher 789), Plugin-API
  **257 / 1 skipped**, Dashboard **259**.
* `pytest -m "not integration"`: **788 passed, 8 deselected**.
* `pytest -m integration`: **8 passed** — justETF 2, OpenFIGI 3, yfinance 3.
* `ruff check app tests plugin_api` und `git diff --check` sauber.

`docs/plugins.md` und `docs/sources.yaml.example` beschreiben jetzt
`plugins.packages` samt der drei Regeln.
