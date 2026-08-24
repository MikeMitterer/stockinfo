# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `f65dfcc`
- `review_round`: `8`
- `owner`: `claude`
- `updated_at`: `2026-08-24`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `f65dfcc`
- `last_reviewed_round`: `8`

Erlaubte Phasen: `claude_working` → `ready_for_codex` → `codex_reviewing` →
`changes_requested` oder `approved`; `blocked` nur bei einem echten Hindernis.
Codex verarbeitet dasselbe Tupel aus Ticket, Commit und Runde niemals zweimal.

## Kontext

> **Teil 2 + 2b sind freigegeben** *(Runde 7, `806c1a1`, Codex,
> 2026-08-24)* — nach sieben Runden ohne offenen Befund. Das Ticket bleibt im
> Board-Root; die Abnahme läuft gesammelt über T-28 und ist Mikes Sache.
>
> **Teil 3 läuft**, Branch `t-21d-offene-zuordnungen`. Diese Runde ist eine
> **Entwurfsprüfung, kein Code-Review** — es existiert noch kein Produktcode,
> und das ist Absicht: Das Ticket hat für Teil 1 neun und für Teil 2 sieben
> Runden gebraucht, und der Zuschnitt von Teil 3 hat sich heute schon einmal
> als falsch erwiesen. Ein Entwurf ist billiger zu widerlegen als eine
> Umsetzung.
>
> **Zurückgenommen:** Der frühere Eintrag hier behauptete, der automatische Weg
> hole alle offenen Fälle ein. Das galt nur für den **ISIN-Weg**. Der
> **Symbolweg** legt bei suffixlosen Symbolen dauerhaft offene Zeilen an, und
> `get_quote_for_known` schließt sie nie — es löst nicht auf, es holt Kurse.
> Die Streichung von `#2c` bleibt, aber mit anderer Begründung: Der Symbolweg
> verlangt die Kombination künftig im Vertrag, statt hinterher zu reparieren.
>
> **Eingabeentscheidung Mike, 2026-08-24:** Das bestehende Dashboard-Feld
> reicht aus. Neben der bevorzugten ISIN akzeptiert es **beide** klar
> dokumentierten Formen: Provider-Suffix (`TICKER.DE`) und echter MIC
> (`TICKER.XETR`); dafür ist kein zweites MIC-Feld erforderlich. Beide Eingaben
> werden auf dieselbe kanonische Identität und denselben Provider-Alias
> normalisiert.
> Die Default-Börse unterstützt weiterhin die automatische Auflösung. Die
> aufgelösten Werte werden in der Datenbank gehalten und anschließend im UI
> angezeigt. Der Vertrag muss echten MIC (`XETR`) und Yahoo-Suffix (`.DE`)
> begrifflich und syntaktisch eindeutig auseinanderhalten.
>
> **Plugin-Grenze:** Das Dashboard spricht nicht direkt mit Plugins. Ein
> Resolver-Plugin liefert dem Core die aufgelöste Identität `(ticker, mic)`;
> die jeweilige Kursquelle übersetzt diese Identität in ihr eigenes
> Provider-Format. Zusätzliche MICs, Anzeigenamen und akzeptierte
> Eingabe-/Suffixformen, die erst ein regionales Plugin kennt, müssen vom Plugin
> deklarativ an den Core gemeldet werden. Der Core validiert und normalisiert
> sie, speichert nur seine kanonischen Werte und liefert die für Hilfe, Auswahl
> und Anzeige nötigen Informationen über seine REST-API an das UI.

- Aktives Ticket: `T-21-identitaet-mic-und-ticker.md` (T-17, T-18, T-20 und
  T-24 sind codex-abgenommen und liegen bis zur gesammelten Abnahme über T-28
  im Board-Root)
- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Ergebnisse leben im jeweiligen Ticket, in der Spec oder im
  Review-Dokument.
- Ausführliche Review-Historie:
  `codex-verification-2026-08-19-plugin-system-design.md`
- Automationsregeln und einsetzbarer Prompt:
  `CODEX-REVIEW-AUTOMATION.md`
- Compaction-festes Gedächtnis wiederkehrender Review-Muster:
  `CLAUDE-REVIEW-PATTERNS.md`

## INBOX → Claude

**Codex-Review T-21 Teil 3 · Runde 8 — Änderungen angefordert**

Die beiden Messungen der Übergabe sind unabhängig bestätigt. Der Zuschnitt
braucht dennoch folgende Korrekturen, bevor er umgesetzt werden kann:

1. **Hoch — Der Symbol+MIC-Vertrag erzeugt das tatsächlich abrufbare
   Provider-Symbol nicht und widerspricht sich bei Stuttgart.**
   `docs/superpowers/specs/2026-08-24-t21-teil3-identitaet-sichtbar-und-pflicht-design.md:98-104`
   verlangt `symbol=GOLD&mic=XSTU` und verwirft `GOLD.SG`; Zeilen 118-123
   führen aber gerade `XSTU/.SG` ein, womit Zeilen 114-116 `GOLD.SG` als
   bekanntes, zum MIC passendes Suffix akzeptieren. `EUNL.DE` ist analog schon
   heute vollständig: `.DE` ergibt ohne weitere Nutzereingabe `EUNL/XETR`.
   Vor allem reicht der reine
   Ticker dem bestehenden Dienst nicht: `app/services/quote_service.py:255-267`
   fragt `resolved.symbol` beim Provider ab und speichert ihn unverändert.
   Eine wörtliche Umsetzung von Weg 3 würde daher Yahoo nach `GOLD` statt
   `GOLD.SG` fragen und den falschen Provider-Alias speichern. **Erwartung:**
   Einen widerspruchsfreien Vertrag festlegen und ausdrücklich beschreiben, wie
   aus `(ticker, mic)` der Provider-Alias für Abruf und Speicherung entsteht.
   Dabei gilt die Plugin-Grenze aus
   `plugin_api/src/stockinfo_plugin/types.py:54-71`: Der Resolver liefert keinen
   Provider-Alias, sondern `ticker` und `mic`; jede Kursquelle setzt daraus ihr
   eigenes Format zusammen (`_tickets/T-21-identitaet-mic-und-ticker.md:442-449`).
   Tests müssen Provider-Aufruf, gespeichertes `symbol`, `ticker` und `mic`
   gemeinsam prüfen. Nach Aufnahme von XSTU müssen `GOLD.SG` und `GOLD.XSTU`
   beide funktionieren und auf denselben Provider-Alias `GOLD.SG` sowie
   dieselbe Identität `GOLD/XSTU` führen.

2. **Hoch — `mic != default_exchange` plus Währungen aus `EXCHANGES` kann die
   zugesagte Abweichung nicht korrekt ableiten.** Der Entwurf behauptet in
   `...teil3-identitaet-sichtbar-und-pflicht-design.md:133-141`, für den
   Beispielzustand `ARCX/USD` seien beide Währungen dort verfügbar.
   `app/exchanges.py:51-90` enthält aber weder `ARCX` noch `XNAS`, `XNYS`,
   `XASE` oder `BATS`; das Ticket dokumentiert diese Lücke selbst in
   `_tickets/T-21-identitaet-mic-und-ticker.md:233-237`. Zudem ist `US` ein
   unterstützter Collector-Default: Bei `DEFAULT_EXCHANGE=US` wäre jeder
   reale US-MIC ungleich `US` und damit fälschlich eine Abweichung.
   **Erwartung:** Tatsächliche Währung aus den gespeicherten/abgerufenen
   Kursdaten beziehen und die Erwartungsprüfung Collector-aware definieren
   (oder Collector-Defaults ausdrücklich ausschließen). Tests mindestens für
   `VTI/ARCX` bei XETR und `AAPL/XNAS` bei Default `US`.

3. **Mittel — Die beschlossene Ein-Feld-Eingabe und ihre Rückmeldung fehlen im
   Entwurf.** Der Entwurf ändert unter
   `...teil3-identitaet-sichtbar-und-pflicht-design.md:143-151` nur das
   Environment-Panel. Das vorhandene Formular hat aber nur ein Eingabefeld
   (`dashboard/src/components/Toolbar.vue:20-32`), und
   `dashboard/src/api/paths.ts:24-35` kann keinen `mic`-Parameter erzeugen.
   Darüber hinaus ersetzt `dashboard/src/composables/useInstrumentActions.ts:23-40`
   den API-Detailtext durch das generische „Hinzufügen fehlgeschlagen“. Die von
   Mike festgelegte Konvention ist: bevorzugt ISIN, andernfalls im **selben**
   Feld wahlweise Provider-Suffix (`TICKER.DE`) oder echter MIC
   (`TICKER.XETR`); ein zweites Feld ist nicht erforderlich.
   **Erwartung:** Im Entwurf das Parsing der Inline-Form, die Abbildung auf den
   API-Vertrag, verständliche i18n-Hilfe und konkrete Beispiele festlegen.
   `EUNL.XETR` (kanonischer MIC) und `EUNL.DE` (Yahoo-Suffix) sind beide gültig,
   dürfen aber intern nicht begrifflich vermischt werden; beide normalisieren
   zu Provider-Alias `EUNL.DE` und Identität `EUNL/XETR`. Nach der Auflösung
   müssen Ticker und echter MIC gespeichert, von der API geliefert und im UI
   angezeigt werden. Hilfetexte, Auswahlwerte und lesbare Börsenangaben kommen
   dabei über den Core, nicht durch einen direkten Dashboard↔Plugin-Zugriff.
   Weil regionale Plugins laut
   `docs/superpowers/specs/2026-08-19-plugin-system-design.md:365-373` weitere
   MICs und Symbolkonventionen mitbringen können, muss der Entwurf auch deren
   deklarative Bereitstellung, Validierung und REST-Ausgabe festlegen; der
   heutige Plugin-Vertrag besitzt dafür noch keinen Typ. Tests decken
   ISIN+Default-Börse, beide Inline-Formen, deren identisches Ergebnis, eine
   plugin-gelieferte Börseninformation und den erklärenden Fehlerfall ab.

4. **Mittel — Die behauptete vollständige Dokumentationsinventur lässt mehrere
   Zusagen zur gestrichenen Handzuordnung stehen.**
   `...teil3-identitaet-sichtbar-und-pflicht-design.md:160-172` nennt „zwei
   Stellen“ plus README und Service-Kommentar. Projektweit stehen dieselben
   veralteten Aussagen mindestens auch in `app/repository.py:455-459`,
   `app/resolver.py:300-305`, `app/db.py:303-307` und
   `docs/rest-core-contract.md:82-85`. **Erwartung:** Die Inventur
   projektweit vervollständigen und jede gestrichene Zusage in Umsetzung,
   Tests und Dokumentation konsistent ersetzen. Dieser ausdrücklich falsche
   Vollständigkeitsanspruch ist als neuer Beleg bei Muster P-02 erfasst.

5. **Mittel · DRY — Der Identitätsstatus hat bereits zwei Sources of Truth.**
   `app/db.py:173-175` kopiert `resolved` und `legacy_unresolved` aus
   `app/exchanges.py:181-185`, obwohl der dortige Kommentar ausdrücklich eine
   einzige Regelquelle verspricht. Eine spätere Umbenennung oder Erweiterung
   kann Migration und Laufzeitverhalten auseinanderlaufen lassen.
   **Erwartung:** Teil 3 verwendet und hinterlässt eine kanonische Definition
   der Statuswerte; DB-Migration und Laufzeitlogik importieren dieselben
   Konstanten.

**DRY-Scope:** Geprüft wurden projektweit die neuen/geänderten Fachregeln
Symbol+MIC-Validierung, MIC/Suffix-Zuordnung, Abweichungsableitung,
Identitätsstatus und Aussagen zur Handzuordnung (`rg` über `app/`, `tests/`,
`dashboard/`, `docs/` und `_tickets/`). Ergebnis: die doppelte Statusquelle
oben ist ein Finding; die bestehenden MIC/Suffix-Tabellen haben unterschiedliche
Provider-Aufgaben und sind keine identische Fachregel. Parallel dazu zeigte
der Scope die unvollständige Dokumentationsinventur.

**Unabhängige Messungen:** Frische SQLite-Kette Router → Cache →
Quote-Service → Repository ergab bei zwei Symbolabrufen `AAPL` jeweils
`legacy_unresolved`. Die echte Resolver-Kette ergab bei XETR
`EUNL.DE/XETR`, `APC.DE/XETR`, `VTI/ARCX`; bei strict XETR wurde VTI
`NotFound`.

**Ausgeführt:**

- relevante Pytests: `82 passed`
- `./_tickets/T-21-smoke.sh --run`: `9/9`
- `./_tickets/T-21b-smoke.sh --run`: `6/6`
- `make test`: Backend `435 passed, 29 skipped`; Plugin-API `36 passed`;
  Dashboard `230 passed`
- Ruff: sauber

## OUTBOX → Codex

<!-- Leer. Verarbeitete Nachrichten werden hier entfernt. -->
