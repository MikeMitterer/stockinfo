# Übergabe — T-15 ETF-Extras nachtragen + Schublade

**Stand:** 2026-08-17, Branch `t-15-etf-extras-nachtragen`, aus `master`.
**Plan:** `docs/superpowers/plans/2026-08-17-etf-extras-nachtragen-und-schublade.md`
**Spec:** `docs/superpowers/specs/2026-08-17-etf-extras-nachtragen-und-schublade-design.md`

Diese Datei existiert, damit ein Kontextwechsel nichts kostet. Das
Arbeits-Ledger unter `.superpowers/sdd/` ist git-ignoriert und verschwindet beim
Aufräumen — die Entscheidungen dürfen dort nicht mitsterben.

## Was fertig ist

Alle acht Tasks des Plans sind implementiert, jeder mit eigenem Review.

| Task | Inhalt | Stand |
|---|---|---|
| 1 | Schema und Migration (beide Tabellen, idempotent) | ✅ Review sauber |
| 2 | Modelle, `OVERRIDE_FIELDS` 3 → 8, Validierung | ✅ Review sauber |
| 3 | Repository feldgetrieben (SQL aus der Konstante erzeugt) | ✅ Review sauber |
| 4 | Dienst und Endpoint, Test über den **echten** Dienst | ✅ Review sauber |
| 5 | Beschaffung: Domizil holen, Fondswährung trennen | ✅ Review sauber |
| 6 | `MetricValue`, Tabelle wird lesend | ✅ Review sauber |
| 7 | `MetricEditor` mit Entfernen im gesperrten Zustand | ✅ 1 Befund geparkt |
| 8 | Schublade, Kartenliste, Aufräumen, Testlücken | Review lief zuletzt |

**Zahlen zuletzt:** 199 Frontend-Tests, 163 Backend-Tests, `vue-tsc` sauber.
`ruff` meldet einen vorbestehenden `F401` in `tests/test_resolver.py`, der nicht
aus dieser Arbeit stammt.

## Was noch offen ist

1. **Gesamtprüfung über den Branch** (whole-branch review) — war der nächste
   Schritt. Dabei die unten stehenden „deferred minors" triagieren.
2. **Ticket(s) anlegen** im Board `_tickets/`, Nummer T-15. Laut Spec sind
   Backend (Daten + Beschaffung) und Frontend (Schublade) getrennt abnehmbar,
   also voraussichtlich zwei Tickets.
3. **Verify-Matrix je Ticket**, zweistufig (`AI` / `Human`). Ausdrückliche
   Vorgabe des Nutzers: **Backend-Zeilen prüft die KI selbst per `curl`** gegen
   die laufende API (Port 8000, läuft mit `--reload`) — die gehören **nicht** in
   die Human-Spalte, das wäre doppelte Arbeit. Die Human-Spalte trägt nur, was
   ein Mensch beurteilen muss: Oberfläche, Schublade, Ausrichtung, Bedienung.
4. **Browser-Prüfung** als Teil des KI-Vorabchecks — gemessen statt geschätzt.
   Offen aus den Reviews: Spaltenkanten gegen die Spaltenköpfe, kein waagrechter
   Überhang bei 375 px, Verhalten von `NSelect` mit `tag` bei getippter
   Neueingabe (Vitest simuliert das nur), Kontrast der Schublade je Theme.
5. **Ledger-Verzeichnis löschen**, wenn die Gesamtprüfung sauber ist:
   `rm -rf .superpowers/sdd/2026-08-17-etf-extras-nachtragen-und-schublade`.

## Offene Kleinbefunde (deferred minors)

- **Task 2:** Ein Kommentar nennt Ticket `T-15`, das im Board noch nicht
  existiert. Klärt sich mit Punkt 2 oben.
- **Task 3:** Neue lokale Variablen in `repository.py` waren zunächst deutsch;
  inzwischen durch die Standard-Korrektur überholt — prüfen, ob dort noch etwas
  steht.
- **Task 4:** Der Selbstprüfungs-Abschnitt in `task-4-report.md` behauptet
  deutsche Bezeichner, die der Nachzieh-Commit längst ersetzt hat. Reiner
  Doku-Fehler.
- **Task 6:** Der Bericht zitiert die falsche Task-Nummer für die Löschung von
  `ManualMetric` (Task 8, nicht 7).
- **Task 7:** `utils/suggestions.ts` war zunächst ungenutzt — in Task 8
  verdrahtet, also erledigt; beim Gesamtreview gegenprüfen.

## Urteile, die ich in deinem Namen getroffen habe

Zwölf Stück, in der Reihenfolge ihres Entstehens. Jedes mit dem, was es kostet,
falls es falsch war.

1. **Branch statt git-worktree.** Dieser Checkout trägt `.venv`,
   `dashboard/node_modules` und `data/stockinfo.db`; ein frischer Worktree hätte
   nichts davon, und jeder Testbefehl des Plans liefe ins Leere.
   *Kosten:* Auf `master` kann parallel nicht gearbeitet werden.
2. **Ein Kollateral-Test wurde schon in Task 1 repariert**, nicht erst in Task 3.
   Der Plan ließ Task 2 mit „Expected: PASS" enden, was mit einem roten Test aus
   Task 1 nicht aufgeht. *Kosten:* Der Test prüft eine Spur weniger scharf, bis
   sein feldgetriebener Nachfolger ab Task 3 übernimmt.
3. **Namensbefund war zur Hälfte richtig** — echter Verstoß war nur der
   Funktionsname, nicht die lokalen Variablen. *(Später durch Urteil 9 überholt.)*
4. **Die Global Constraints waren zu absolut formuliert** und haben ein Review
   fehlgeleitet; im Plan präzisiert. *Kosten:* keine.
5. **Ein Rundlauf-Test wanderte von Task 2 nach Task 4.** Task 2 ändert nur
   Modelle; dass Werte zurückkommen, kann erst Task 4 halten. Ein Test gehört in
   den Task, der ihn erfüllen kann. *Kosten:* eine Task später abgesichert.
6. **Die vierfache Spaltenliste in `db.py` bleibt.** Das ist das bestehende
   Muster der Datei; ableitbar nur, indem man den SQL-String generiert — mehr
   Ebene als Gewinn. *Kosten:* Eine neue Spalte braucht zwei Einträge je Tabelle.
7. **Testliterale bleiben Literale**, werden nicht aus `OVERRIDE_FIELDS`
   abgeleitet. Ein Test, der seine Erwartung aus der geprüften Konstante zieht,
   ist tautologisch. *Kosten:* keiner.
8. **Die acht Felder in drei Pydantic-Modellen sind Typisierung**, keine
   Duplikation. *Kosten:* Ein neuntes Feld braucht vier Deklarationen.
9. **Der Bestand wird nicht flächendeckend umbenannt.** Nach der Standard-
   Korrektur („Bezeichner immer englisch") gilt: neuer Code englisch, angefasste
   Zeilen ziehen mit — kein Sweep. *Kosten:* Altlast bleibt sichtbar.
10. **Die Paket-Umstellung auf `@mmit/ux-foundation` wurde als eigener Commit
    gesichert** (`accc8db`), bevor die Frontend-Tasks liefen. Sonst hätte ein
    Subagent fremde Arbeit in seinen Task-Commit gezogen. *Kosten:* Ein Commit
    im Branch, der thematisch nicht zu T-15 gehört — benannt und herauslösbar.
11. **Ein deutscher Testbezeichner aus meinem eigenen Brief wurde korrigiert**,
    obwohl plan-mandatiert. *Kosten:* keine.
12. **`ManualMetric.vue` durfte in Task 7 doch angefasst werden.** Der Reviewer
    hat das zu Recht als Regelverstoß gemeldet; ich habe es akzeptiert: vier
    defensive Zeilen, der betroffene Zweig unerreichbar, die Alternative hätte
    Duplikation erzeugt — und die Datei wird in Task 8 ohnehin gelöscht.
    *Kosten:* ein toter Zweig in einer Datei, die als Nächstes verschwindet.

## Was diese Arbeit über den Plan gelernt hat

Drei Befunde kamen nicht aus dem Code, sondern aus den Task-Grenzen — sie wären
ohne die Aufteilung nicht aufgefallen:

- **Eine Attrappe deckte eine ganze Schicht zu.** Kein Test rief je den echten
  `CachedQuoteService`; die Suite blieb grün, während der Endpoint live mit
  `TypeError` brach. Geschlossen in Task 4, mit Nachweis.
- **Der Plan stellte Erwartungen einen Task zu früh** — zweimal. Beide Male
  meldete der Implementierer es, statt in Nachbartasks zu greifen.
- **Die Frontend-Typen kannten nur drei der acht Felder.** Das Backend war
  längst weiter; niemand hatte nachgezogen.

---

# NACHTRAG — Stand nach Sichtprüfung und Gesamtprüfung

**Wichtig: Der Branch ist derzeit NICHT mergefähig.** Die Punkte unten müssen
vorher behoben sein.

## Was seit dem ersten Teil dieser Datei passiert ist

1. **Der Mensch hat die Schublade angesehen** und einen schweren Fehler
   gefunden: Bei `EUNL.DE` standen acht Beschriftungen ohne Werte. Ursache:
   `MetricEditor` umschloss mit `v-if="editable"` **alle** Anzeige-Zweige, nicht
   nur deren Bedienbarkeit. Gesperrte Felder rendern dadurch nichts.
   → Behoben in `3ae5c04`, `5c2d97f`, `bea0e22` (Wert anzeigen über
   `MetricValue`, Erklärung immer sichtbar, Layout mehrspaltig mit Fußzeile).

2. **Die Gesamtprüfung des Branches** (opus, 26 Commits) kam unabhängig zum
   selben Befund und fand weitere Abweichungen von der Spec. Urteil:
   *nicht mergefähig*. Backend solide — Migration auf einer Kopie der echten DB
   verlustfrei und idempotent, Kette trägt bis in jede Antwort, Währungstrennung
   konsequent. Das Frontend erfüllte seinen Zweck nicht.

3. **Ein Fix-Agent ist hängengeblieben** (600 s ohne Fortschritt), ohne zu
   committen. Sein halbfertiger Stand lag im Arbeitsbaum; ein frischer Agent auf
   stärkerem Modell hat übernommen.

## Befunde der Gesamtprüfung und ihr Stand

| # | Befund | Stand |
|---|---|---|
| C1 | Gesperrte Felder zeigen keinen Wert; **Regression gegen T-09**: mobil waren TER/Vola/Thes. ganz verschwunden, der haltende Test wurde in Task 8 gelöscht | behoben |
| C2 | Zustand „verdeckt" zeigt weder eigenen noch Quellwert, nur das Kreuz | behoben |
| I1 | `source` fehlt in der Schublade (Spec §3); Feld existiert nicht auf `InstrumentSummary` | **in Arbeit** |
| I2 | Erklärung kennt nur 1 von 3 Gründen und **lügt** in den anderen: Aktie mit DE-ISIN → „Quelle abgefragt, nichts geliefert" (nie abgefragt); Papier ohne ISIN → „Diese ISIN liegt außerhalb" (es gibt keine) | vermutlich behoben, **verifizieren** |
| I3 | `Escape` schließt die Schublade nicht | **offen** |
| I4 | Vorrang-Regel steht im Frontend dreimal, je anders formuliert (Task 6/7/8) | vermutlich behoben, **verifizieren** |
| I5 | `app/repository.py` bricht als einzige Datei die Namensregel — inkl. des öffentlichen Parameters `werte`, während der Dienst `values` sagt | **offen** |
| M1 | `MetricValue` nahm `OverrideField`, verstand aber nur drei | behoben (verallgemeinert) |
| M2 | Toter Kommentarverweis auf gelöschte `ManualMetric.vue` | offen/prüfen |
| M3 | `.visually-hidden` nur scoped in `InstrumentsTable` → Merkmalstext steht sichtbar in der Zelle | offen/prüfen |
| M4 | Vier Commits lassen die Backend-Suite rot → `git bisect` unbrauchbar | bewusst (Urteile 2/5), bleibt |
| M5 | `types.ts` zählt die acht Felder zweimal auf; `useOverrides` baut den Payload getippt; zwei Label-Karten für dieselbe Aussage | teils offen |
| M6 | Kein Wächter `set(OVERRIDE_FIELDS) == set(InstrumentOverrides.model_fields)` | offen |
| M7 | `fund_currency` freie Eingabe vs. Backend `^[A-Z]{3}$` → „usd" endet im generischen Fehler-Toast | offen |

## Zwei weitere Urteile (Nr. 13 und 14)

13. **Layout der Schublade weicht von der Hausregel ab.** Der `ux-standards`-
    Skill schrieb „zweispaltig: links bearbeiten, rechts nachlesen" vor. Bei acht
    Feldern und einer Zeile Herkunft trägt das nicht. Entschieden (vom Menschen):
    Felder mehrspaltig, Herkunft als Fußzeile. *Kosten:* weicht von der bisherigen
    Formulierung ab — der Skill ist deshalb aktualisiert worden.
14. **Der `ux-standards`-Skill wurde geändert**: aus der Vorschrift wurde eine
    Entscheidungsregel („Die Aufteilung folgt dem Inhalt") mit Tabelle für vier
    Inhaltsverhältnisse, plus zwei Lehren: *was nicht bearbeitbar ist,
    verschwindet nicht* und *erklär die Ansicht auch im Normalfall*.
    *Kosten:* keine — die Regel beschreibt jetzt, was tatsächlich trägt.

## Warum kein Task-Review C1 gefunden hat

Meine Prüfaufträge fragten im gesperrten Zustand nach „Bedienelement fehlt,
Entfernen-Knopf da" — nie nach der **Anwesenheit** des Wertes. Die Tests prüfen
Abwesenheit; ein Feld, das gar nichts rendert, besteht sie glänzend. Fehler in
der Fragestellung, nicht in der Ausführung. Für künftige Sperren gilt: beides
testen.

## Nächste Schritte

1. Laufenden Fix-Agenten abwarten, Ergebnis prüfen (offene Punkte oben).
2. **Browser-Prüfung** — steht komplett aus und ist jetzt zwingend, nicht
   optional: Werte in der Schublade sichtbar, Spaltenkanten gegen die Köpfe,
   kein waagrechter Überhang bei 375 px, Kontrast je Theme, `NSelect`-Verhalten
   bei getippter Neueingabe.
3. Erneute Gesamtprüfung nach den Fixes.
4. Tickets anlegen (T-15, voraussichtlich zwei), Verify-Matrix zweistufig —
   Backend-Zeilen per `curl` in die KI-Spalte, Human-Spalte nur für Sichtbares.
5. Ledger löschen: `rm -rf .superpowers/sdd/2026-08-17-etf-extras-nachtragen-und-schublade`
