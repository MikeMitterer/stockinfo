---
schema_version: 1
id: SI-P-10
project: stockinfo
kind: pattern
discovery_phase: mixed
affected_work:
- implementation
- tests
- handoff
subject_author: claude
discovered_by: unknown
recorded_by: unknown
structured_by: codex
prevention_roles:
- implementer
- reviewer
provenance:
  project: stockinfo
  file: _tickets/.agents/CLAUDE-LESSONS.md
  heading: P-10 · Ein Integrationstest berührt seine Außengrenze nicht
  revision: 5fc549b84ae7d449780b856d3046230da6c5bf2d
  file_sha256: f506fd721ef98bf9c51bff326b06c22a39c24eee57f14daa4e0e93f06bd78dff
  section_sha256: 89644f6be33a9fe52e3d4b196914746cd3b83946162455aaed4edf6d02cd1599
  captured_at: '2026-09-11'
---

# SI-P-10 · Ein Integrationstest berührt seine Außengrenze nicht

**Implementer-Regel:** Für jede Integrationsaussage den tatsächlich erreichten Pfad benennen.

**Verifier-Prüfung:** Prüfen, ob die konkrete Eingabe die behauptete Außengrenze überhaupt erreicht.

## Originalbelege und Einordnung

**Erkennungsregel:** Eine Datei oder ein ganzer Test trägt den Marker
`integration` beziehungsweise wird als echter Online-Fall gezählt, obwohl der
geprüfte Pfad absichtlich vor Client, Bibliothek oder Netz abbricht. Die Suite
wirkt tiefer als sie ist und der Fall verschwindet zugleich aus dem normalen
Unit-Lauf.

**Prüffrage:** Für jeden einzelnen Integrationstest: Welcher konkrete Aufruf
verlässt den Prozess? Eine testlokal vergiftete Außengrenze muss den Test rot
machen. Bleibt er grün, ist es ein Unit-Test und wird dorthin verschoben.

**Beleg 1:** T-27b Runde 5, Commit `cd3e2f3`: Der Sammelcode-Test stand unter
dem modulweiten OpenFIGI-Integrationsmarker. Der Kern-Resolver musste bei `US`
aber gerade **vor** dem Client abbrechen; derselbe Fall existierte bereits als
Unit-Test. Runde 6 entfernte ihn aus der Integrationsdatei.

**Beleg 2:** T-23 Runde 1, Commit `e6ca003`: Der yfinance-Test für EUR→EUR
steht unter dem modulweiten Integrationsmarker und wird als einer von sieben
echten Netzfällen gezählt. `YFinancePlugin.fetch_rate` beantwortet die
Identität definitionsgemäß vor `_provider.fetch_fx_rate`; der Test berührt
Yahoo nicht und gehört in die Unit-/Contract-Suite.

**Beleg 3:** T-23 Runde 2, Commit `e35d190`: Die Übergabe meldete zehn
Integrationstests, die ausnahmslos einen Dienst berührten. Der EUR→EUR-Fall
blieb jedoch zusätzlich zu seiner neuen Unit-Kopie in der Integrationsdatei;
auch der neue justETF-Fall mit US-ISIN kehrte vor dem Provider zurück. Nur acht
der zehn gesammelten Fälle überschritten tatsächlich die Außengrenze.
