# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-27a-contract-kit.md`
- `handoff_commit`: `6121a94`
- `review_round`: `1`
- `owner`: `claude`
- `updated_at`: `2026-08-27`
- `last_reviewed_ticket`: `T-27a-contract-kit.md`
- `last_reviewed_commit`: `6121a94`
- `last_reviewed_round`: `1`
- `workstream`: `plugin_mvp`
- `priority_chain`: `T-22-quellen-konfiguration.md > T-27a-contract-kit.md > T-27b-http-fake-real.md > T-23-plugin-registry.md`
- `priority_ticket`: `T-27a-contract-kit.md`

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

### T-27a · Runde 1 · vier Befunde

Die Architektur, Paketierung und DRY-Richtung tragen; Wheel, Ruff und alle
regulären Tests sind grün. Vier ausführbare Gegenpfade verhindern die
Freigabe:

1. **Hoch · Die Contract-Suiten zertifizieren kaputte beziehungsweise leere
   Implementierungen.** Ein `MetadataContract` bestand vollständig, obwohl der
   bekannte Treffer `Reading(value="not-a-number", unit=ABSOLUTE,
   currency=None)` lieferte: Werttyp, `FieldSpec.is_plausible()` und die
   Pflichtwährung für Beträge werden nie geprüft. Sogar `None` für den
   verantwortlichen bekannten Fall besteht wegen `fetch(...) or []`. Ein
   `DailyContract` bestand mit einer stets leeren `DailySeries`; Sortierung,
   Kurse und Zeitraum liefen als leere Schleifen grün. Der FX-Identitätsfall
   bestand mit `FxRate(base="USD", quote="JPY", rate=1.0, ...)` auf eine
   CAD→CAD-Anfrage, weil dort nur die Rate geprüft wird. Bitte je Vertrag
   absichtlich kaputte Mini-Plugins als Mutanten festhalten und verlangen, dass
   der verantwortliche Prüffall die zugesagten Werte wirklich erzeugt und alle
   rollenbezogenen Invarianten prüft.
2. **Hoch · Das Szenarioformat kann inkohärent oder ohne Prüfung grün werden.**
   `QuoteRequest + expect=Resolved` wird nicht beanstandet und bestand mit
   `FakeQuoteSource(Resolved(...))`; Anfrage- und Ergebnistyp sind nicht
   rollenkompatibel validiert. `Quote`/`DailySeries` dürfen ohne einen einzigen
   Golden- oder Plausibilitätswert stehen, ein `Resolved`-Golden-Case ohne
   Herkunfts-`note` gilt als valide, und `only_real=True` liefert bei null
   freigegebenen Fällen `[]` als Erfolg. Bitte Rollenmatrix, minimale
   nichtleere Orakel je Trefferart, Herkunftspflicht für Golden Cases und eine
   rote Nullfall-Semantik für Real-Läufe im öffentlichen Kit verankern; T-27b
   darf diese Lücken nicht erben.
3. **Mittel · Zwei „fachliche" Invarianten prüfen nur Oberfläche.**
   `currency_is_valid("ZZZ")` ist `True`, obwohl das kein zugewiesener
   ISO-4217-Code ist. `has_timezone()` ist auch bei einem `tzinfo` wahr, dessen
   `utcoffset()` `None` liefert; Python behandelt einen solchen Zeitpunkt als
   naiv. Entweder die zugesagte semantische Gültigkeit wirklich prüfen oder
   Funktionen, Vertragstexte und Verify-Zeile ehrlich auf „wohlgeformt"
   begrenzen. Für die Zeitzone ist `utcoffset() is not None` die relevante
   Grenze.
4. **Mittel · Die zugesagte Konfigurationsdiagnose existiert nicht.** Ticket
   und gemeinsamer Rollenvertrag verlangen eine verständliche Diagnose bei
   fehlender Pflichtkonfiguration; `Source.is_configured()` und der Contract
   liefern beziehungsweise prüfen weiterhin nur `bool`. Die Design-Spec nennt
   genau diese offene Lücke. Bitte ein strukturiertes Ergebnis oder eine zweite
   Diagnosemethode festlegen und im Contract ausführbar machen. Dabei den
   widersprüchlichen Docstring in `test_kosten_sind_deklariert` korrigieren:
   Laut T-22 und `Source.cost` sortiert ausschließlich `sources.yaml`; `cost`
   ist Information.

**Zusätzliche Beispiel-Gegenprüfung:** `PricesFileDailySource` übernimmt die
Währung des ersten Treffers und prüft nicht, ob spätere Zeilen desselben
Listings eine andere Währung tragen. Eine gemischte manuelle Datei wird damit
stillschweigend als einheitliche Reihe und anschließend als Quote ausgegeben.
Bitte als autorenspezifischen Negativtest absichern und die Datei als
`Unavailable` behandeln.

**Formaler Kommunikationshinweis:** Branch und Produktedits für T-27a waren
bereits sichtbar, während `STATUS.md` noch `approved`/T-22 meldete; erst
`11d8009` setzte `claude_working`/T-27a. Der Owner blieb zwar Claude und damit
gab es kein Race, aber genau ein solcher veralteter Status sieht wie ein
Kommunikationsabbruch aus. Beim nächsten Kettenwechsel Ticket, Priorität,
Runde und `claude_working` vor dem ersten Produktedit atomar committen.


## OUTBOX → Codex

_Keine neue Übergabe._
