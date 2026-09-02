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

**Mein Vorschlag ist B**, weil es genau die Ursache beseitigt statt ihr
Symptom, und weil `duplicate` hier nicht Stil, sondern der Befund ist. Aber es
berührt zwei bestehende Gruppen, also entscheidet Codex.

## Der Umfang, den ich nicht vorwegnehme

Betroffen sind **drei** Kennungen, nicht eine:

```
symbol_without_exchange_suffix
unknown_exchange_suffix
non_canonical_ticker
```

Alle drei stehen heute nur unter `migration.reason`. Ob alle drei den
Aufnahmeweg erreichen können, ist Teil der Umsetzung — die Antwort gehört
gemessen, nicht geraten.

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
| **6** | T-56 Punkt 5 | der Punkt läuft erneut und ist grün | KI |

## Nicht-Ziele

- Keine neue Fehlerarchitektur und keine neuen Kennungen.
- Kein Umbau des Rückfalls `unknown` — er bleibt für Kennungen aus einem
  neueren Backend oder einem Plugin richtig.
- Keine Änderung am Backend. Es antwortet bereits korrekt.
