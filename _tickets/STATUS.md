# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-27b-http-fake-real.md`
- `handoff_commit`: `8698aa0`
- `review_round`: `4`
- `owner`: `codex`
- `updated_at`: `2026-08-28`
- `last_reviewed_ticket`: `T-27b-http-fake-real.md`
- `last_reviewed_commit`: `af72b5a`
- `last_reviewed_round`: `3`
- `workstream`: `plugin_mvp`
- `priority_chain`: `T-22-quellen-konfiguration.md > T-27a-contract-kit.md > T-27b-http-fake-real.md > T-23-plugin-registry.md`
- `priority_ticket`: `T-27b-http-fake-real.md`

Erlaubte Phasen: `claude_working` → `ready_for_codex` → `codex_reviewing` →
`changes_requested` oder `approved`; `portfolio_review` übergibt nach dem
letzten Kettenglied an Mike, `blocked` nur bei einem echten Hindernis.

## Kontext

> **Portfolio-Rebaseline Mike, 2026-08-27:** T-21 ist nach der freigegebenen
> Übergabe 3 eingefroren. Verbindliche Kette: **T-22 → T-27a → T-27b →
> T-23**. Ziel ist ein nachgewiesener Lauf eines Datei- und eines
> Entry-Point-Plugins über **Registry → Core → REST**.

> **Freigegebener T-21-Sockel:** Produktstand `2dd0dc3`, Review-Freigabe
> `d3fecb8`, Statusstand `ce55202`. Die späteren 4A-Stände `7a14d79` und
> `48fff52` bleiben eingefroren.

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

### T-27b · Runde 4 · **Produktentscheidung hebt den freigegebenen Entwurf auf**

Stand `8698aa0`, Produktcode in `ebf8a14`. Lies bitte zuerst diesen Abschnitt —
die drei Entwurfsrunden, die du geprüft hast, sind nicht mehr maßgeblich.

**Mike hat den Offline-Lauf gestrichen**, wörtlich: *„Wer sagt, dass der
Offline-Lauf funktionieren muss? Der Integrationstest muss laufen, der
Integrationstest verwendet das API, das Plugin, das zur Verfügung steht. Wir
brauchen keine extrem aufwändige Offline-Variante des Tests."*

Damit fällt die Grundannahme des Tickets. Record/Replay, Aufzeichnungsformat,
beide Signaturen, Bereinigung, Freshness-Tore, Socket-Sperre und der
Release-Befehl sind hinfällig — also fast alles, worüber wir drei Runden
gesprochen haben. Der Code dafür war zum Teil schon geschrieben und ist
**verworfen**, nicht auf Halde gelegt.

**Zweiter Punkt von Mike, und er trifft einen echten Fehler von mir:** Ein
Plugin schreibt seine API nicht neu, sondern benutzt die vorhandene. Mein
Beispielplugin hatte den OpenFIGI-Aufruf nachgebaut — eine zweite
Implementierung derselben Fachlogik, also genau die DRY-Verletzung, auf die du
jedes Review prüfst. Ich habe sie selbst nicht gesehen.

#### Was jetzt dasteht

`app/plugins/openfigi_resolver.py` ist eine **Rollen-Schale** um den
vorhandenen `OpenFigiClient` — kein HTTP-Aufruf, kein Anfrageformat, keine
Antwortauswertung. Übersetzt wird nur in die Sprache des Vertrags, und die
wichtigste Zeile ist `SourceUnavailableError → Unavailable`: Dieser Client hat
den Umbau hinter sich, bei dem ein Ausfall als „kenne ich nicht" zurückkam.
Diese Unterscheidung ein zweites Mal zu formulieren hieße, sie ein zweites Mal
falsch zu machen.

`tests/test_plugin_openfigi_integration.py` fragt den echten Dienst. Marker
`integration`, abwählbar mit `-m "not integration"`.

#### Der Integrationstest hat sich sofort bezahlt gemacht

Meine erste Fassung von `handles()` prüfte das Börsenmerkmal mit
`mic_is_wellformed`. Am echten Dienst gemessen:

```
US0378331005 @ XNAS (micCode=XNAS) -> None
US0378331005 @ US   (exchCode=US)  -> 'AAPL'
IE00B3RBWM25 @ XETR (micCode=XETR) -> 'VGWL'
CA78012H5675 @ XETR (micCode=XETR) -> None
```

`US` ist der Sammelcode der eigenen Tabelle und **kein MIC** — die Formprüfung
hätte ausgerechnet den Weg abgewiesen, über den OpenFIGI US-Papiere kennt.
Gegen ein Double wäre das nie aufgefallen: Das Double hätte geantwortet, was
ich ihm gesagt hätte. Das ist das beste Argument für Mikes Entscheidung, das
ich habe, und es ist nicht meins.

#### Was ich dir ausdrücklich zur Prüfung gebe

* Ob die Verify-Matrix in ihrer neuen Fassung wirklich das abdeckt, was das
  Ticket jetzt zusagt — sie ist von neun Zeilen komplett neu, und ich habe sie
  geschrieben, nachdem ich den Code hatte. Das ist die Reihenfolge, in der man
  sich Zeilen zurechtlegt.
* Ob die Rollen-Schale wirklich frei von zweiter Fachlogik ist. `handles()`
  entscheidet etwas — nämlich wann gar nicht erst gefragt wird —, und das ist
  die Stelle, an der sich Logik einschleicht.
* Ob „alte Fassung als überholt markiert stehen lassen" die richtige Wahl ist.
  Ich wollte die Historie deiner drei Runden nicht ins Leere zeigen lassen; die
  Datei ist dadurch aber sehr lang und hat zwei Verify-Matrizen.

#### Verifikation

* `make test`: Backend **642 / 29 skipped** (vorher 638), Plugin-API
  **260 / 1 skipped**, Dashboard **259**.
* `pytest -m "not integration"`: **638 passed, 29 skipped, 4 deselected**.
* `ruff check app tests plugin_api` und `git diff --check` sauber.

Time-box im Ticket von `~7 h` auf `~1 h` gesetzt — der Umfang ist ein anderer
geworden.
