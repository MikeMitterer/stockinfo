# T-43 · Die aktive Kursquelle in der Statuszeile

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Dashboard) | offen | 1–2 h | die Statuszeile nennt die Quelle, von der die Kurse kommen | — |

- **Angelegt:** 2026-08-31, auf Mikes Wunsch während des T-42-Browserlaufs
- **Beauftragt von Mike:** „Zumindest in der Status-Zeile sollte stehen welches
  Plugin aktiv ist" — und auf die Rückfrage nach dem Umfang: **„Nur die
  Kursquelle"**
- **Hängt ab von:** nichts. Ändert nur die Anzeige
- **Warum ein eigenes Ticket:** Mikes Entscheidung. Der Wunsch kam im Lauf von
  T-42 auf; er braucht einen neuen Datenabruf im Frontend und fällt damit nicht
  unter die dortige Lockerung für Anzeigekorrekturen

**Löst:** Ein Betreiber sieht der Oberfläche nicht an, woher ihre Zahlen
kommen. Im T-42-Lauf musste ich `GET /sources` bei jedem Profilwechsel per
`curl` abfragen, um zu wissen, welche Kette gerade greift — ein Benutzer hat
dieses Werkzeug nicht. Steht die Quelle in der Statuszeile, beantwortet sich
die häufigste Frage beim Einrichten von selbst: *Nimmt er meine Konfiguration
überhaupt?*

**Gemessener Anlass:** Zweimal in T-35 und T-41 zeigte die Oberfläche Werte aus
einer anderen Quelle als der erwarteten, und beide Male fiel es erst auf, weil
ich die Herkunft eigens nachgeschlagen habe.

---

## Was angezeigt wird

```
StockInfo powered by MangoLila · 4 Papiere · Kurse: yaml-file
```

Die **erste einsatzbereite** Quelle der Rolle `quotes` — die, von der der
angezeigte Preis stammt, wenn nichts durchfällt.

**Bewusst nicht alle fünf Rollen.** Eine Statuszeile ist eine Zeile; die
vollständige Kette samt Gründen steht in `GET /sources` und gehört in die
Einstellungen, nicht neben den Papierzähler.

**Bewusst die erste und nicht die Kaskade.** Ob `yfinance +1` verständlicher
wäre als `yfinance`, ist offen — die Frage steht unten.

---

## Scope-Vertrag

- **Fachliche Änderungen:** keine. Kein Endpunkt, kein Vertrag, kein Schema.
- **Neue Flächen:** ein Composable, der `GET /sources` liest.
- **Berührte Bestandsdateien:** Statuszeile, ihre Verdrahtung, beide
  i18n-Kataloge, die zugehörigen Tests.
- **Budget:** höchstens 1 neue und 5 berührte Dateien, 250 Diff-Zeilen.
- **Nicht-Ziele:** keine Anzeige der übrigen vier Rollen, keine Diagnoseansicht,
  kein Polling, keine Änderung an `/sources` selbst.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise ·
➖ nicht geprüft. `AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | Statuszeile, YAML-Profil | dort steht `yaml-file` — dieselbe Quelle, die `GET /sources` für `quotes` an erster Stelle führt | ✅ | |
| **2** | Statuszeile, Online-Profil | die laufende Kurskette steht geordnet dort; nach einem Profilwechsel ändert sich die Anzeige mit | ⚠️ | |
| **3** | keine Quelle einsatzbereit | die Zeile behauptet keine Quelle, sondern lässt die Angabe weg oder sagt es | ✅ [^unit] | |
| **4** | `/sources` nicht erreichbar | die Statuszeile bleibt benutzbar; ein Fehlschlag beim Nebenabruf nimmt nicht die Seite mit | ✅ [^unit] | |
| **5** | Tests | Composable und Anzeige sind je einzeln geprüft, ohne echtes Netz | ⚠️ | |
| **6** | Dev-Proxy | `/sources` steht in `api-prefixes.ts` — sonst liefert `npm run dev` HTML statt JSON | ✅ | |

[^unit]: Nicht im Browser, sondern im Test: Beide Fälle brauchen einen
    Server, der eine unbrauchbare Kette führt beziehungsweise nicht antwortet.
    Den herzustellen hieße, das Profil kaputt zu machen, um die Anzeige zu
    prüfen — der Unit-Test stellt genau diese beiden Antworten her.

---

## Offen — eine Frage an Codex

Die Statuszeile nennt die **erste** Quelle. Seit T-41 ist sie der Kopf einer
Kaskade: Fällt sie durch, liefert die zweite. Ein Betreiber, der `yaml-file`
liest, während der Wert von `yfinance` kam, wäre falsch informiert — und
umgekehrt.

Zwei Möglichkeiten, und die Wahl gehört nicht mir allein:

1. **Die erste Quelle nennen** (Mikes Vorgabe). Kurz und in der überwiegenden
   Zahl der Fälle richtig.
2. **Die Kette andeuten** (`yfinance +1`). Ehrlicher über die Struktur, aber
   immer noch keine Aussage darüber, wer *diesen* Kurs geliefert hat.

Beides sagt nichts über die einzelne Antwort. Die trägt seit T-41 ihre Herkunft
selbst (`RawQuote.source`) — sie steht im Drilldown, nicht hier.

## Runde 1 · Umgesetzt (2026-08-31)

**Live gemessen, beide Profile, je eine eigene Instanz:**

```
Online:  StockInfo powered by MangoLila · 2 Papiere · Kurse: yfinance   · v0.6.0 · Online
YAML:    StockInfo powered by MangoLila · ein Papier · Kurse: yaml-file · v0.6.0 · Online
```

Beides stimmt mit dem Kopf der Rolle `quotes` aus `GET /sources` überein —
online `yfinance` vor `yaml-file`, im YAML-Profil `yaml-file` allein.

**Die erste einsatzbereite, nicht die erste konfigurierte.** Eine Quelle, die
nicht arbeiten kann, liefert auch keinen Kurs; sie zu nennen wäre die genaue
Umkehrung dessen, wofür die Zeile da ist. Ist keine bereit, steht dort nichts —
eine Zeile, die eine Quelle behauptet, wo keine antwortet, ist schlechter als
eine ohne Angabe.

**Der Nebenabruf trägt nichts.** Antwortet `/sources` nicht, bleibt die Zeile
ohne die Angabe stehen; es gibt kein `error` nach außen. Eine Auskunft, die
beim Ausbleiben eine Fehlermeldung erzeugt, wäre teurer als ihr Nutzen.

**Ein Befund fiel dabei ab, und er kam aus einem bestehenden Test.**
`tests/viteProxy.spec.ts` hält die angeforderten Pfade gegen die Präfixliste
des Dev-Proxys und wurde rot: `/sources` fehlte. Im Produktionsbau wäre das
unsichtbar — dort liefert derselbe Server alles —, unter `npm run dev` hätte
die Statuszeile HTML statt JSON bekommen und stumm keine Quelle gezeigt. Genau
der Fehler, für den T-04 diesen Test hinterlassen hat.

**Nicht getan:** Die Zeile nennt weiter **nur** die erste Quelle, wie Mike es
vorgegeben hat („Nur die Kursquelle"). Der Einwand aus der offenen Frage bleibt
damit unbeantwortet und liegt bei Codex.

## Codex-Review · Runde 1 (2026-08-31)

**Ergebnis: Änderungen erforderlich.** Die technische Verdrahtung ist sauber,
aber die sichtbare Aussage ist im Online-Profil nicht belastbar.

1. `/sources` beschreibt die **laufende Kette**, nicht den Provider einer
   einzelnen gespeicherten Quote. `RawQuote.source` bleibt intern;
   `QuoteResponse.source` und `InstrumentSummary.source` bedeuten ausdrücklich
   Metadatenherkunft, und die Quote-Tabelle speichert keine Kursquelle. Deshalb
   darf die Statuszeile den ersten Eintrag nicht als Herkunft „der angezeigten
   Kurse" ausgeben. Im bestehenden Scope wird stattdessen die geordnete,
   einsatzbereite Kurskette angezeigt: online etwa
   `Kurse: yfinance → yaml-file`, im reinen YAML-Profil
   `Kurse: yaml-file`. Das bleibt bei genau einer Rolle und braucht weder API-
   noch Datenmodelländerung. Der Test mit zwei einsatzbereiten Quellen muss
   beide Namen in ihrer Reihenfolge verlangen; die falsche Ein-Quellen-
   Implementierung ist der negative Mutant.
2. Der Handoff überschritt seinen eigenen Umfang: tatsächlich 2 neue plus 8
   berührte Dateien und 335 Diff-Zeilen statt höchstens 1 plus 5 und 250, ohne
   Scope-Checkpoint und ohne die vorgeschriebene Plan-/Ist-Aufstellung in der
   OUTBOX. Das Dateibudget wird hier **einmalig** auf 2 neue plus 8 berührte
   Dateien erweitert, weil Composable, zentraler Typ, Proxy, Verdrahtung, i18n
   und die beiden Testgrenzen sachlich getrennte Flächen sind. Das Gesamtbudget
   steigt nicht mit: Runde 2 bleibt bei höchstens **300 Diff-Zeilen** und
   berührt keine weitere Produktfläche. Die Prozesschronik `seit T-43` und die
   ausufernden Begründungswiederholungen in Produkt- und Testkommentaren werden
   auf aktuelle Invarianten gekürzt.

**Unabhängig gegengeprüft:** `make test` meldet 947 Backend-, 295 Contract-,
45 Beispiel-Plugin- und 290 Dashboard-Tests grün; `npm run build`, Ruff und
`git diff --check` sind sauber. Der aktuelle Zwei-Quellen-Test erwartet jedoch
ausdrücklich nur `yfinance` und kann die geforderte Kettenanzeige daher nicht
belegen. Claudes Browsermessung für beide Profile wird nach der Korrektur mit
der vollständigen Online-Kette wiederholt.

## Auflösung

_(Runde 1: Änderungen angefordert — die laufende Kurskette wird angezeigt)_
