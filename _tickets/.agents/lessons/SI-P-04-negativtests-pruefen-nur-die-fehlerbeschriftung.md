---
schema_version: 1
id: SI-P-04
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
  heading: P-04 · Negativtests prüfen nur die Fehlerbeschriftung
  revision: 5fc549b84ae7d449780b856d3046230da6c5bf2d
  file_sha256: f506fd721ef98bf9c51bff326b06c22a39c24eee57f14daa4e0e93f06bd78dff
  section_sha256: 9ebb77b995b4cd0f8535be61984ee3a33f2c983dd1a00c9f8a861f7590a207c0
  captured_at: '2026-09-11'
---

# SI-P-04 · Negativtests prüfen nur die Fehlerbeschriftung

**Implementer-Regel:** Regelwidrige Eingaben und unabhängig bestimmte Erwartungen verwenden.

**Verifier-Prüfung:** Die konkret falsche Variante muss die Gegenprobe scheitern lassen.

## Originalbelege und Einordnung

**Erkennungsregel:** Eine absichtlich ungültige Fixture oder ein Negativfall gilt
als geprüft, obwohl der Test nur ein Fehlerkennzeichen wie `violates`, einen
Status oder eine Beschreibung verlangt, nicht aber die bezeichnete Verletzung
selbst reproduziert.

**Prüffrage:** Wird der Test rot, wenn man ausschließlich den eigentlichen
Fehler im Negativfall beseitigt und dessen Beschriftung unverändert lässt? Für
jede erlaubte Fehlerkennung muss eine konkrete, gegensinnige Assertion
existieren.

**Zweite Prüffrage — das Orakel.** Ein Großteil der Belege unten ist derselbe
Griff: Die Gegenprobe ruft die Funktion auf, die sie prüfen soll. Deshalb vor
jeder Vollständigkeitsbehauptung zusätzlich fragen: *Woher kommt der
Erwartungswert?* Zulässig sind ein **Literal** und eine **hier eigens
ausgeschriebene Regel**; unzulässig ist jeder Aufruf der geprüften Logik. Eine
Tabelle nachzuschlagen ist erlaubt — sie ist Daten. Die Regel auf sie
anzuwenden ist es nicht.

Der DRY-Reflex zeigt hier in die falsche Richtung: Im Orakel ist die Dopplung
der **Zweck**. Wo sie absichtlich steht, gehört ein Satz dazu, der das sagt —
sonst zentralisiert sie der nächste Durchgang weg.

**Beleg wegen ausdrücklich falscher Vollständigkeitsbehauptung:** T-24 Teil 1,
Commit `403020b`: Ticketzeile `#7i` war mit `✅` als statische Konsistenz von
Artefakt und Fixtures markiert. In `tests/test_contract.py` genügte bei
nicht-konformen Fixtures jedoch ein nichtleerer `violates`-Text; selbst eine
angeblich widersprüchliche `/generation`-Fixture mit identischen UUIDs in Header
und Body passierte beide einschlägigen Prüfungen (`MUTANT_UNERKANNT`).

**Beleg:** T-21 Teil 1 Runde 2, Commit `48cdaf9`: Das neue
`T-21-smoke.sh` meldete die behaupteten sechs Migrationschecks auch auf einer
vollständig leeren Datenbank als bestanden. `all(...)` auf leeren Mengen und
Vergleiche `0 == 0` ersetzten den Nachweis der konkret behaupteten
Auflösungen; selbst `#3b` prüfte nur Indexnamen statt deren Eindeutigkeit.

**Beleg:** T-21 Teil 1 Runde 3, Commit `7da4aae`: Der reparierte Smoke-Check
verwendete `split_symbol` sowohl in der Migration als auch zur Berechnung des
Erwartungswerts. Damit bestätigte die Produktionsfunktion sich selbst und
verwarf zugleich einen laut Ticket gültigen Zielzustand: Ein bereits manuell
aufgelöstes suffixloses Listing `WALONLY/XNAS` wurde von `#2` als falsch
markiert, weil sein Legacy-Symbol absichtlich nicht rückwärts zerlegbar ist.

**Beleg:** T-21 Teil 1 Runde 4, Commit `d6c4c19`: Das neue Vorwärts-Oracle
setzte `(ticker, mic)` über jeden Eintrag aus `EXCHANGES` zu `symbol` zusammen,
ohne echte MICs vom ausdrücklich verbotenen internen Sammelcode `US` zu
trennen. Eine Gegenprobe ließ die Migration `VTI` als `VTI/US` und `resolved`
erzeugen; `#2` meldete wörtlich `VTI/US→VTI` und das Script bestand mit 8/8.
Auf einem bereits migrierten Bestand bestand derselbe Check außerdem mit „0
neu zerlegt“ und prüfte damit keine einzige Zuordnung.

**Beleg:** T-21 Teil 1 Runde 5, Commit `92ee6a2`: Der ergänzte Check `#2d`
zählte alle Zeilen mit `identity_status = resolved`, prüfte aber nur, ob ihr
`mic` in der Menge bekannter Sammelcodes liegt. Eine vorbestehende Zeile
`VTI` mit Status `resolved`, aber `ticker=NULL` und `mic=NULL`, wurde als
fünfte „aufgelöste Zeile“ gezählt; das Script bestand mit 9/9. Die Migration
selbst übersprang diese unvollständige Identität anschließend dauerhaft, weil
sie jeden gesetzten Status als bereits bearbeitet behandelt.

**Beleg:** T-21 Teil 1 Runde 7, Commit `3148d09`: `#2d` versprach für
`resolved` einen echten MIC, schloss aber weiterhin nur die in `EXCHANGES`
bekannten Collector-Codes aus. Ein präparierter Bestand mit
`VTI/NOT-A-MIC/resolved` passierte `#2d` und den gesamten Smoke-Lauf mit 9/9;
die neuen Produkttests deckten ausschließlich den konkret besprochenen Wert
`US` und die positive Gegenprobe `XNAS` ab.

**Beleg:** T-21 Teil 1 Runde 8, Commit `62dcfd2`: Der Smoke ersetzte sein
eigenes MIC-Oracle durch einen Aufruf der Produktionsfunktion `is_real_mic`.
Der neue `$`-Regex akzeptierte einen finalen Zeilenumbruch; damit hielten
Produkt und Prüfung `VTI/XNAS\n/resolved` gemeinsam für gültig und der
präparierte Lauf bestand 9/9. Die neuen Grenztests enthielten Leerzeichen,
Länge, Kleinschreibung und Sonderzeichen, aber keinen Zeilenumbruch.

**Neuer Beleg:** T-21 Teil 3 Übergabe 1, Runde 25, Commit `0f79eec`:
`T-21-smoke.sh`, `T-21b-smoke.sh` und
`tests/test_identity_creation.py` ersetzten ihre bisher getrennt formulierte
Vorwärtsrechnung durch einen Aufruf der neuen Produktfunktion
`provider_alias`. Damit bestätigen Produkt und angebliche Gegenprobe wieder
dieselbe Implementierung. Zusätzlich behauptet
`test_beide_eingabeformen_treffen_dieselbe_boerse`, `EUNL.XETR` geprüft zu
haben, konstruiert dieses Ergebnis aber nur als Tupel aus der
`EXCHANGES`-Mitgliedschaft; kein MIC-Eingabeweg wird ausgeführt.

**Neuer Beleg:** T-21 Teil 3 Übergabe 2A, Runde 30, Commit `d361fbc`:
`test_jeder_erlaubte_pfad_antwortet_auch_wirklich` akzeptiert jede Antwort,
solange sie nicht exakt `503` mit `migration_pending` ist. Ein in die
Allowlist eingetragener, aber nicht existierender Pfad liefert `404` und der
Test bleibt grün. Damit prüft der angekündigte Routentabellen-Test nur die
Beschriftung „nicht vom Guard gesperrt“, nicht die Zusage, dass der erlaubte
Endpunkt tatsächlich existiert und erfolgreich antwortet.

**Neuer Beleg:** T-21 Teil 3 Übergabe 2A, Runde 31, Commit `d06a6a1`:
`test_vorschau_und_bericht_nennen_genug_zur_neuerfassung` soll die neu durch
REST geführten Felder Börse, Gattung und Währung absichern. Seine Fixture
setzt aber keines davon; der Test vergleicht anschließend nur Bericht gegen
Vorschau. Werden die Felder in beiden Mappings wieder weggelassen, bleibt
`None == None` grün. Der Erwartungswert kommt damit aus dem zweiten zu
prüfenden Pfad statt aus einem ausgeschriebenen, nichtleeren Orakel.

**Neuer Beleg:** T-21 Teil 3 Übergabe 2B, Runde 35, Commit `5b0fa31`:
`test_jede_kennung_hat_einen_satz` verspricht für jeden Ablehnungsgrund einen
Satz in beiden Sprachen, `_reason_keys()` liest aber ausschließlich die
Schlüssel. Eine In-Memory-Mutation des ersten englischen Werts auf `''` ließ
die Schlüsselmenge unverändert und alle drei Katalogtests grün. Der ergänzende
Vue-Test prüft nur einen einzigen deutschen Grund; leere Texte der übrigen
Codes oder der englischen Sprache bleiben unbeobachtet.

**Neuer Beleg:** T-36/T-37 Runde 3, Commit `cc0f028`: Smoke `#0b` speist drei
Fehler ein, verlangt danach aber nur `status != 0 || output != leer`. Der
nichtnumerische Kurs lässt `float(...)` vor der Ausgabe aller gesammelten
Befunde abbrechen; allein der Traceback genügt trotzdem für die Erfolgsmeldung
„Prüfziffer, Sammelcode und unbrauchbarer Kurs erkannt“. Keiner der drei
behaupteten Befunde wird einzeln verlangt. Ebenso fragen vier
Drilldown-Assertions gelöschte i18n-Schlüssel ab; vue-i18n liefert die Kennung
unter Warnung zurück und `not.toContain(...)` bleibt ohne existierenden
Vergleichstext grün.

**Neuer Beleg:** T-37 Runde 3, Commit `b464471`: Der neue Test
`test_die_history_wird_auf_das_fenster_beschnitten` erzeugte das richtige
leere Zeitfenster, schrieb aber `NotFound` als Erwartung fest. Der öffentliche
`DailyCloseSource`-Vertrag sagt ausdrücklich, dass ein bekanntes Papier ohne
Punkte im Fenster eine leere `DailySeries` liefert; `NotFound` bedeutet
hingegen unbekanntes Papier. Der Test unterschied die Tage, bestätigte aber
die falsche Ergebnisart.
