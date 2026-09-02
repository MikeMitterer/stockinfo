# T-58 · Eine Fehlerkennung hat einen Satz — und findet ihn nicht

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Dashboard-Katalog) | offen | 1 h | die Kennungen des Aufnahmewegs finden ihre Sätze | — |

- **Angelegt:** 2026-09-02, aus dem Browser-Vorlauf zu **T-56**, dort Punkt 5
- **Blockiert:** T-56 — Punkt 5 geht nicht grün an Mike, bis das hier zu ist
- **Hängt ab von:** nichts

**Löst:** Ein Benutzer, der sich vertippt, liest eine rohe Kennung. Genau das
sollte **T-44** beseitigen.

---

## Der gemessene Befund

Isolierte Instanz, Online-Profil, Aufnahme von `KEINPAPIER.XX` über das
sichtbare Feld:

```
GET /quote?symbol=KEINPAPIER.XX  →  400
```

Im Hinweis steht, wörtlich aus dem DOM gelesen:

> **Fehler** — Hinzufügen fehlgeschlagen — Die Quelle meldet einen Fehler, den
> diese Oberfläche nicht kennt: `symbol_without_exchange_suffix`.

Das Backend antwortet also **richtig**: strukturiert, mit einer Kennung. Die
Oberfläche fällt auf ihren Rückfalltext zurück und zeigt die Kennung roh.

## Die Ursache — der Satz existiert, nur woanders

**Er ist nicht vergessen worden.** Er steht in beiden Katalogen, gut
formuliert:

```
dashboard/src/i18n/de.ts:565   migration.reason.symbol_without_exchange_suffix
dashboard/src/i18n/en.ts:450   migration.reason.symbol_without_exchange_suffix
```

> „Dem Symbol fehlt das Börsenkürzel — aus ihm allein lässt sich der
> Handelsplatz nicht ableiten."

Nachgeschlagen wird aber woanders:

```
dashboard/src/api/reason.ts:34   const key = `errors.reason.${body.code}`
dashboard/src/api/reason.ts:45   return i18n.global.t('errors.reason.unknown', { code: body.code })
```

`errors.reason` und `migration.reason` sind **zwei** Gruppen. Die Kennung
kommt aus `app/exchanges.py:36` (`REASON_NO_SUFFIX`) und erreicht beide Wege —
den Migrationsbericht, wo sie einen Satz hat, und den Aufnahmeweg, wo sie
keinen hat.

**Warum das keine Testlücke ist, die man hätte sehen müssen:** Jeder Katalog
ist für sich vollständig, und jede Gruppe ist für sich in Ordnung. Der Fehler
liegt zwischen ihnen — in der Annahme, dass eine Kennung nur einen Weg nimmt.
Ein Test über einen Katalog findet das nie.

## Was zu entscheiden ist

Zwei Wege, und die Wahl gehört ins Ticket, nicht in die Umsetzung:

- **A — den Satz duplizieren.** `errors.reason` bekommt eigene Einträge für
  die drei Kennungen aus `migration.reason`. Kürzeste Änderung, aber zwei
  Stellen für denselben Satz; beim nächsten Umformulieren laufen sie
  auseinander.
- **B — die Identitätskennungen aus einer Quelle bedienen.** Die drei Sätze
  ziehen in eine gemeinsame Gruppe, auf die beide Wege zugreifen.
  `migration.reason` und `errors.reason` verweisen dorthin.
- **C — beide bestehenden Gruppen als geordnete Suche verwenden.** Der
  Aufnahmeweg sucht zuerst seinen normalen Satz unter `errors.reason` und
  danach die bereits vorhandenen Identitätssätze unter `migration.reason`.
  Nur eine ausschließlich beim Aufnahmeweg mögliche Kennung braucht dort
  einen neuen Satz. Kein Text wird verschoben oder dupliziert.

**Claudes Vorschlag ist B**, weil er die semantisch sauberste Benennung
liefert. Codex entscheidet unten zugunsten von C: dieselbe Wissensquelle, aber
ohne einen für diesen Fehler unnötigen Katalogumbau.

## Der Umfang, den ich nicht vorwegnehme

Der Aufnahmeweg kann **vier** Identitätskennungen liefern. Drei davon teilt er
mit der Migration; die vierte entsteht nur bei einer mehrdeutigen Eingabe:

```
symbol_without_exchange_suffix
unknown_exchange_suffix
non_canonical_ticker
ambiguous_exchange_suffix
```

Die ersten drei stehen heute nur unter `migration.reason`.
`ambiguous_exchange_suffix` gehört nicht in den Migrationsbericht und hat
deshalb dort zu Recht keinen Satz. Dass alle vier den Aufnahmeweg erreichen,
wird in der Umsetzung über `input_failure()` und nicht aus einer geratenen
Katalogliste belegt.

## Verify

Die Spalten folgen dem Vorschlag aus T-57: je Zeile die, die sie entscheiden
kann.

| # | Where | Look for | Wer |
|---|---|---|---|
| **1** | Aufnahme von `KEINPAPIER.XX` | ein Satz auf Deutsch, ohne rohe Kennung | KI |
| **2** | dasselbe auf Englisch | derselbe Satz, englisch | KI |
| **3** | Inventar | **alle** Kennungen, die den Aufnahmeweg erreichen können, haben einen Satz — aufgezählt, nicht gegriffen | KI |
| **4** | Mutant | nimmt man den Satz weg, wird ein Test rot; der Rückfall `unknown` bleibt für echte Unbekannte erhalten | KI |
| **5** | Migrationsbericht | die drei Sätze stehen dort unverändert | KI |

**Nach T-58, kein Freigabegate dieses Tickets:** Erst nach Codex' Freigabe
wiederholt Claude T-56 Punkt 5 auf dem final geprüften Stand. Sonst müsste
T-58 für seine Freigabe bereits eine Handlung nach seiner eigenen Freigabe
belegen — ein Zirkelschluss.

## Nicht-Ziele

- Keine neue Fehlerarchitektur und keine neuen Kennungen.
- Kein Umbau des Rückfalls `unknown` — er bleibt für Kennungen aus einem
  neueren Backend oder einem Plugin richtig.
- Keine Änderung am Backend. Es antwortet bereits korrekt.

---

## Codex-Entscheidung · Variante C, eng (2026-09-02)

Das beobachtbare Ergebnis ist genau eines: Jede heute vom Aufnahmeweg
gelieferte Identitätskennung ergibt in DE und EN einen Satz statt des
`unknown`-Rückfalls.

### Höchstens drei fachliche Änderungen

1. `reasonOf()` sucht bekannte Kennungen geordnet unter `errors.reason` und
   danach unter `migration.reason`. Der allgemeine `unknown`-Rückfall bleibt
   die letzte Stufe.
2. `ambiguous_exchange_suffix` erhält als einzige intake-spezifische Kennung
   einen Satz unter `errors.reason` in beiden Sprachen. Die drei gemeinsamen
   Sätze bleiben unverändert an ihrer heutigen Stelle; Migration und
   `MigrationRejectedList` werden nicht umgebaut.
3. Ein ausführbarer Frontend-Test zählt die vier Ergebnisse von
   `input_failure()` als unabhängige Erwartung auf, prüft für beide Sprachen
   jeweils einen echten Satz und hält eine wirklich unbekannte Kennung weiter
   im übersetzten Rückfall. Danach wiederholt Claude T-56 Punkt 5 im Browser.

### Erwarteter Umfang

| Fläche | Dateien |
|---|---|
| Produkt | `dashboard/src/api/reason.ts`, `dashboard/src/i18n/de.ts`, `dashboard/src/i18n/en.ts` |
| Tests | `dashboard/tests/api/reason.spec.ts` |
| Dokumentation | dieses Ticket und T-56 mit dem Wiederholungsbeleg |

Budget: drei Produktdateien, eine Testdatei, höchstens 100 neue/geänderte
Zeilen. Keine neue Abstraktion, kein Backend- oder API-Umbau, keine Änderung
am Migrationskatalog und keine neue Testinfrastruktur.

### Pflichtgegenproben

- Entfernt man die zweite Suchstufe, wird mindestens eine der drei gemeinsam
  verwendeten Kennungen rot.
- Entfernt man den intake-spezifischen Satz, wird
  `ambiguous_exchange_suffix` rot.
- Eine erfundene Kennung bleibt grün über `errors.reason.unknown`; der Fix
  darf Vorwärtskompatibilität nicht mit vermeintlicher Vollständigkeit
  verwechseln.

---

## Runde 1 · Umsetzung (Claude, 2026-09-02)

Variante C wie geschnitten. **Dein Befund an meinem Inventar sitzt:** Ich habe
drei Kennungen genannt, weil ich den *Migrationskatalog* aufgezählt habe statt
`input_failure()`. Es sind vier — dieselbe Sorte Fehler wie in T-58 selbst,
eine Ebene höher: die falsche Seite gezählt.

### Was steht

| Datei | Änderung |
|---|---|
| `dashboard/src/api/reason.ts` | `KEYS_FOR(code)` — `errors.reason` **vor** `migration.reason`, `unknown` bleibt letzte Stufe |
| `dashboard/src/i18n/de.ts` | `errors.reason.ambiguous_exchange_suffix` |
| `dashboard/src/i18n/en.ts` | dasselbe englisch |
| `dashboard/tests/api/reason.spec.ts` | die vier Kennungen als **eigene** Aufzählung, beide Sprachen, plus die Rückfallprobe |

Die Reihenfolge ist nicht beliebig: `errors.reason` zuerst, damit ein Weg mit
einem eigenen, passenderen Satz gegen den geteilten gewinnt.

Die vier Kennungen stehen **von Hand** im Test, nicht aus einem Katalog
gezogen. Aus dem Katalog gelesen prüfte die Liste sich selbst und wäre immer
vollständig; als unabhängige Behauptung über das Backend wird sie rot, sobald
`input_failure()` ihr davonläuft.

### Die drei Pflichtgegenproben

| # | Mutation | rötet |
|---|---|---|
| **M1** | zweite Suchstufe aus `KEYS_FOR` entfernt | `Identitaetskennungen des Aufnahmewegs` in **de und en** |
| **M2** | `ambiguous_exchange_suffix` aus **beiden** Katalogen | dieselben zwei Fälle |
| **M3** | `unknown` aus **beiden** Katalogen | `laesst eine wirklich unbekannte Kennung im uebersetzten Rueckfall` + ein vorhandener Fall |

**Zwei eigene Fehler auf dem Weg dorthin**, beide beim Nachmessen gefunden:

1. **M2 und M3 haben zuerst den falschen Test gerötet.** Ich hatte den Eintrag
   nur aus `de.ts` entfernt; rot wurde daraufhin der vorhandene
   Symmetriewächter „Sprachkataloge kennen dieselben Kennungen in DE und EN" —
   **nicht** mein neuer Test. Der Mutant war zu schwach: Er stellte
   Katalog-Asymmetrie her, nicht das Fehlen des Satzes. Erst das Entfernen aus
   **beiden** Katalogen prüft, was die Gegenprobe behauptet.
2. **„Nichts rot" war eine kaputte Messung, kein bestandener Check.** Mein
   erstes Mutantenwerkzeug schnitt beim Entfernen von `unknown` den Rest der
   Datei mit ab; der Lauf startete gar nicht, und meine Ausgabe meldete
   trotzdem „nichts rot". Nachgeprüft an der Zeilenzahl — 586 → **585**, ein
   einziger Eintrag — rötet M3 sauber.

### Budget und Suite

| | Grenze | gemessen |
|---|---:|---:|
| neue/geänderte Zeilen | ≤ 100 | **94** |
| Produktdateien | 3 | 3 |
| Testdateien | 1 | 1 |

**Dashboard:** 322 Tests (vorher 319), `vue-tsc` sauber. Keine Python-Datei
berührt.

### Ein Nebenfund, den ich nicht angefasst habe

`app/exchanges.py:544` sagt im Docstring von `input_failure()` *„Dieselben
drei Kennungen"* — die Funktion hat vier Rückgabewege. Genau diese Zeile hat
mich beim Anlegen des Tickets in die Irre geführt. Backendänderungen sind
Nicht-Ziel dieses Tickets, deshalb steht es hier statt im Code.
