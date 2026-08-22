# Claude-Review-Muster

Versioniertes, compaction-festes Gedächtnis für wiederkehrende Fehler in
Claudes Implementierungen und Übergaben. Jeder Codex-Review liest diese Datei
vollständig. Sie ist die spätere Ausgangsbasis für einen eigenen Review-Skill.

Aufgenommen werden nur verallgemeinerbare Muster mit mindestens zwei konkreten
Belegen oder eine ausdrücklich falsche Vollständigkeitsbehauptung. Einzelne
Bugs bleiben im Ticket. Ein Eintrag enthält Erkennungsregel, Prüffrage und
Belege; neue Belege werden am bestehenden Eintrag ergänzt statt ihn zu
duplizieren.

## Übersicht

- [P-01 · Testtiefe wird überzeichnet](#p-01--testtiefe-wird-in-der-übergabe-überzeichnet)
- [P-02 · Regelumsetzung wird zu früh vollständig gemeldet](#p-02--punktuelle-korrektur-wird-als-vollständige-regelumsetzung-gemeldet)
- [P-03 · Prüfwerkzeuge räumen fremde Ressourcen auf](#p-03--prüfwerkzeuge-räumen-fremde-ressourcen-mit-auf)
- [P-04 · Negativtests prüfen nur die Fehlerbeschriftung](#p-04--negativtests-prüfen-nur-die-fehlerbeschriftung)

## P-01 · Testtiefe wird in der Übergabe überzeichnet

**Erkennungsregel:** Die Übergabe behauptet „ganze Kette", „nur externe Grenze
gemockt" oder gleichwertig, während eine eigene Kernkomponente durch Fake,
Stub oder Mock ersetzt ist.

**Prüffrage:** Welche konkrete Objektkette läuft im Test? Jeden Test-Doppel als
externe Grenze oder eigene Komponente klassifizieren und die Behauptung damit
abgleichen.

**Beleg:** T-17 Runde 1, Commit `84c9c2d`: In
`tests/test_resolver.py` ersetzte `CountingResolver` den eigenen
`YFinanceResolver`, obwohl Übergabe und Docstring behaupteten, allein
`httpx.post` sei gemockt und die ganze Kette werde geprüft.

**Beleg:** T-21 Teil 1, Commit `fce1bab`: Verify `#1` markierte die Migration
einer bestehenden Datenbank mit `✅` als live geprüft. Ticketfußnote und
Übergabe hielten zugleich fest, dass nur eine synthetisch nachgestellte
Alt-Datenbank und kein real gewachsener Bestand geprüft worden war.

[↑ Übersicht](#übersicht)

## P-02 · Punktuelle Korrektur wird als vollständige Regelumsetzung gemeldet

**Erkennungsregel:** Besprochene Beispiele sind korrigiert, aber derselbe Diff
führt neue Verstöße gegen die zugrunde liegende Regel ein oder behält alte
Referenzen darauf.

**Prüffrage:** Nicht nur die genannten Beispiele bestätigen; den vollständigen
hinzugefügten Diff automatisiert und manuell gegen die Regel prüfen.

**Beleg:** T-17 Runde 1, Commit `84c9c2d`: Die zwei besprochenen
Produktbezeichner waren englisch, gleichzeitig entstanden neue deutsche
Test-Helper, Variablen und strukturierte Log-Felder; ein Docstring verwies
weiter auf `_ist_symbolfaehig`.

**Beleg:** T-24 Teil 2, Commit `d792ce9`: Die Übergabe erklärte die
Währungspflicht als an „allen“ gefundenen Stellen umgesetzt und markierte
`#9` mit ✅. Live-, Daily- und History-Pfade waren korrigiert, aber der
meistgenutzte frische sowie der stale Cache-Pfad baute in
`CachedQuoteService._from_cache` weiterhin eine erfolgreiche `QuoteResponse`
mit `currency=None`, wenn Kurspunkt und Instrument keine Währung hatten.

**Beleg:** T-18 Runde 1, Commit `32e08ea`: Die Übergabe erklärte die neue
`fetch_etf`-Signatur an allen Stellen nachgezogen. Der Composite akzeptierte
`exchange` und `currency` und nutzte sie für `is_responsible`, verwarf beide
aber beim anschließenden `enricher.fetch_etf(...)`-Aufruf. Ein Provider, der
den neuen Kontext auch zum Abruf benötigt, wurde deshalb zuständig gewählt
und danach ohne den Kontext aufgerufen.

**Beleg:** T-20 Runde 1, Commit `5d79a6d`: Der Resolververtrag wurde von
`ResolvedInstrument | None` auf vier Ergebnisarten umgestellt und die
Quote-Kette samt Tests angepasst. Der ebenfalls am `InstrumentResolver`
hängende `QuoteAnalyzer` prüfte weiterhin nur auf `None` und griff bei
`NotFound`, `NotResponsible` und `Unavailable` auf `.symbol` zu; der
Diagnose-Endpunkt endete deshalb für unbekannte Papiere und Quellenausfälle
mit HTTP 500.

**Beleg:** T-21 Teil 1, Commit `fce1bab`: Die Identität und der eindeutige
Index wurden von `symbol` auf `(ticker, mic)` umgestellt, während
`_dedupe_symbols()` weiterhin bei jedem Start ausschließlich nach `symbol`
gruppierte. Dadurch löschte der nächste `init_db()` eines von zwei
kanonisch verschiedenen Listings mit demselben Symbol an verschiedenen MICs.

[↑ Übersicht](#übersicht)

## P-03 · Prüfwerkzeuge räumen fremde Ressourcen mit auf

**Erkennungsregel:** Cleanup bestimmt sein Ziel anhand eines globalen Merkmals
wie Port, Prozessname oder Pfadmuster statt anhand einer vom Lauf erzeugten und
gespeicherten Identität.

**Prüffrage:** Gehört jede beendete oder gelöschte Ressource nachweislich
diesem Lauf? Bei Prozess-Cleanup nur eigene PID beziehungsweise eigene
Prozessgruppe verwenden und Konflikte vor dem Start abbrechen.

**Beleg:** T-17 Runde 1, Commit `84c9c2d`: `_tickets/T-17-smoke.sh`
beendete nach dem Lauf alle Prozesse auf Port 8766; ein bereits laufender
fremder Server konnte zusätzlich den Health-Check bestehen und danach beendet
werden.

[↑ Übersicht](#übersicht)

## P-04 · Negativtests prüfen nur die Fehlerbeschriftung

**Erkennungsregel:** Eine absichtlich ungültige Fixture oder ein Negativfall gilt
als geprüft, obwohl der Test nur ein Fehlerkennzeichen wie `violates`, einen
Status oder eine Beschreibung verlangt, nicht aber die bezeichnete Verletzung
selbst reproduziert.

**Prüffrage:** Wird der Test rot, wenn man ausschließlich den eigentlichen
Fehler im Negativfall beseitigt und dessen Beschriftung unverändert lässt? Für
jede erlaubte Fehlerkennung muss eine konkrete, gegensinnige Assertion
existieren.

**Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-24 Teil 1,
Commit `403020b`: Ticketzeile `#7i` war mit `✅` als statische Konsistenz von
Artefakt und Fixtures markiert. In `tests/test_contract.py` genügte bei
nicht-konformen Fixtures jedoch ein nichtleerer `violates`-Text; selbst eine
angeblich widersprüchliche `/generation`-Fixture mit identischen UUIDs in Header
und Body passierte beide einschlägigen Prüfungen (`MUTANT_UNERKANNT`).

[↑ Übersicht](#übersicht)
