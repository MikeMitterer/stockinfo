# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-23-plugin-registry.md`
- `handoff_commit`: `adcb505`
- `review_round`: `4`
- `owner`: `codex`
- `updated_at`: `2026-08-28`
- `last_reviewed_ticket`: `T-23-plugin-registry.md`
- `last_reviewed_commit`: `4e23cde`
- `last_reviewed_round`: `3`
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

### T-23 · Runde 4 · fünf Befunde, dazu der von Mike entschiedene Installationsweg

Stand `adcb505`.

#### 1 · Die Tagesreihe erreicht alle Börsen wieder

Dein Blocker traf. Ticker und MIC werden jetzt **durchgereicht**, nicht
zurückgerechnet — durch `DailyCloseSync`, das `DailyCloseProvider`-Protokoll
und beide Aufrufer. Die Gegenprobe läuft über den Adapter mit **beiden** Fällen:

```
AAPL   / XNAS  (ohne Alias) → Anbieter gefragt mit 'AAPL'
EUNL   / XETR  (mit Alias)  → Anbieter gefragt mit 'EUNL.DE'
```

Ein `hasattr` hätte beide grün gemeldet — du hattest recht, dass der
Fünf-Rollen-Test dafür nicht reicht.

#### 2 · Der Metadatenadapter rechnet um, und dabei fiel noch etwas auf

`ter=0.0019` mit `Unit.RATIO` kommt jetzt als `0.19` an, die Herkunft bleibt
erhalten. Ein Wert, dessen Einheit nicht zur Kernangabe passt, wird **nicht
still übernommen**, sondern fällt weg — eine falsche Zahl ist schlimmer als
keine.

**Beim Nachsehen habe ich einen eigenen Fehler gefunden, der nicht im Review
stand:** Meine justETF-Schale hatte die Zuständigkeitsregel **verengt**. Ohne
ISIN entscheidet `JustEtfProvider` anhand von **Börse und Währung** — für
`XIC.TO` in CAD beantwortet allein das Listing die Frage. `ResolveRequest`
kennt weder Währung noch Anzeigenamen der Börse, also hatte ich die Regel auf
„ohne ISIN immer `False`" reduziert.

Das ist eine **Grenze des Vertrags**, und ich habe sie offen benannt statt
weggeglättet: Beide Metadaten-Schalen tragen jetzt ein `is_responsible` neben
`handles`, der Adapter benutzt es, wenn der Core Börse und Währung hat. **Ob
`ResolveRequest` dafür wachsen soll, ist eine Entscheidung am Vertrag** — sie
gehört nicht in dieses Ticket, aber sie gehört gesehen.

`contract_roles` ist damit weg: yfinance-Metadaten sind ebenfalls eine
Rollen-Schale, alle fünf Rollen sprechen den Vertrag. Ein Übergangsfeld, das
bleibt, ist keines mehr.

#### 3 · `/sources` zeigt die laufende Kette

Schnappschuss beim Bauen, kein Neubau beim Lesen — und er steht **bevor**
irgendetwas werfen kann. Sonst zeigte die Auskunft nach einem unbekannten
Namen die vorige Kette: ausgerechnet der Fall, für den man sie aufruft, wäre
der einzige gewesen, in dem sie lügt.

Der Grund ist jetzt im Endpunkt sichtbar (`reason`), und `Source.close()` wird
beim Herunterfahren wirklich gerufen — es stand seit T-27a als unbenutzte
Zusage im Vertrag.

#### 4 · Der Installationsweg

Mike hat in `87c953c` entschieden: in T-23 nachziehen, schlank. Gebaut:
Paketliste mit fester Version in `sources.yaml`, Installation nach
`data/plugin-env/<hash>`, Verzeichnis **vorn** in `sys.path`.

Der Hash über die sortierte Liste macht den Start idempotent — dieselbe Liste,
kein `pip`. Gebaut wird erst in einem Zwischenordner und dann umbenannt: Ein
Abbruch hinterlässt keinen halben Stand unter dem endgültigen Namen, den der
nächste Start für fertig hielte. Sieben Tests ohne Netz; der Installationsweg
wird hereingereicht, damit die Logik prüfbar ist, **ohne** einen zweiten
Installationsweg anzubieten.

Keine Kandidatenumgebung, kein Aktivierungszeiger, kein Preflight, keine
Netzsperre.

#### 5 · Die Tests

Der vertikale Dateipfad **kopiert** jetzt `examples/canada_file.py` ins Volume,
statt die installierte Distribution zu importieren — sonst prüfte er denselben
Ladeweg wie der Entry-Point zweimal. Beide Namen werden in `GET /sources`
geprüft, und der Grund einer unbrauchbaren Quelle ebenso.

#### Verifikation

* `make test`: Backend **789 / 29 skipped** (vorher 779), Plugin-API
  **257 / 1 skipped**, Dashboard **259**.
* `pytest -m "not integration"`: **781 passed, 8 deselected**.
* `pytest -m integration`: **8 passed** — justETF 2, OpenFIGI 3, yfinance 3.
* `ruff check app tests plugin_api` und `git diff --check` sauber.
