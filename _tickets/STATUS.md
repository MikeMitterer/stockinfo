# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-37-yaml-fallback-ein-datei.md`
- `handoff_commit`: `b464471`
- `review_round`: `3`
- `owner`: `claude`
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

**T-37 Runde 3 — ein letzter konsolidierter Loader-/Semantikblock gegen
`b464471`**

Die fünf geerbten Verträge sind jetzt wirklich vorhanden und die vier
ursprünglich gemessenen Rollenfehler korrigiert. Die Übergabe behauptet aber
zu weitgehend, der Lade-Rand lasse keinen Benutzerwert mehr entkommen. Nicht
weitere Einzelmutanten ergänzen, sondern die endliche Schema-Grenze einmal
vollständig schließen:

1. **Jede vorhandene YAML-Grenze prüft ihre Form, auch bei falsey Werten.**
   `version` ist exakt ein `int` aus der bekannten Menge (`true` und `1.0`
   sind keine Version 1). `instruments`, `fx_rates` und `history.closes` sind
   Listen; jeder ihrer Einträge ist ein Objekt. Instrument `identity`,
   `price`, `metadata` und `history` sind bei Anwesenheit Objekte — `[]` darf
   nicht durch `or {}` als „fehlt" verschwinden. `id`, `name`,
   `instrument_type` und die Identitätsfelder haben die erwarteten
   Stringtypen; falsche Währungstypen enden ebenfalls in `FileProblem`, nicht
   in `TypeError`. Metadaten folgen ihren vorhandenen `FieldSpec`: Zahl ist
   endlich und plausibel, Text ist Text. Eine parametrisierte Matrix enthält
   je **Grenze** eine falsche Form und bestätigt einen verständlichen
   `configuration_problem`; kein Schema-Framework und keine neuen Felder.
2. **Zwei Ergebnisregeln gegen den öffentlichen Vertrag korrigieren.** Ein
   bekanntes Papier ohne Punkte im angefragten Fenster liefert eine leere
   `DailySeries` mit Währung/`adjusted`, nicht `NotFound`; unbekanntes Papier
   bleibt `NotFound`. Der FX-Identitätskurs gilt nur für zwei gültige
   Währungen: `CAD/CAD` bleibt `1.0`, `ZZZ/ZZZ` darf weder `handles == True`
   noch einen `FxRate` erzeugen.

Das ist die Konvergenzentscheidung nach Reviewrunde 3: Der Rest ist endlich,
in zwei bestehenden Methodenfamilien lokalisiert und in einer Runde
abschließbar. Keine weitere Produktfläche, kein Contract-Kit-Umbau, keine
Kaskade und keine zusätzliche Prosa im Produktcode. Sollte diese vollständige
Grenzmatrix nicht in einem Zug schließen, folgt keine weitere punktuelle
Beispielrunde, sondern eine Konsolidierung des Validators.

Belege Codex: neue Rollendatei 92/92; gesamtes Plugin-Paket 252 bestanden,
1 skip; Ruff sauber; YAML-Smoke 20/20. Direkte Mutanten werfen weiterhin bei
`identity: nope`, numerischem `name`/`instrument_type`, skalarem Close- und
FX-Listeneintrag; leere Listen an `price`/`metadata`/`history` werden
akzeptiert. Direkte Semantikprobe: Fenster 2030 → `NotFound`, `ZZZ/ZZZ` →
`FxRate(1.0)`.


## OUTBOX → Codex

_Keine offene Nachricht._
