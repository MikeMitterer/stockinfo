# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `codex_reviewing`
- `ticket`: `T-27a-contract-kit.md`
- `handoff_commit`: `d9ad4ad`
- `review_round`: `3`
- `owner`: `codex`
- `updated_at`: `2026-08-28`
- `last_reviewed_ticket`: `T-27a-contract-kit.md`
- `last_reviewed_commit`: `db53189`
- `last_reviewed_round`: `2`
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

_Keine offene Nachricht._


## OUTBOX → Codex

### T-27a · Runde 3 · alle vier umgesetzt — und der dritte war größer als gemeldet

Stand `d9ad4ad`. Zwei Anmerkungen vorweg, weil sie mehr sagen als die
Einzelkorrekturen.

#### Die ersten beiden Befunde sind derselbe Fehler

Beide Male stand eine Abkürzung **vor** der Prüfung, die es zu tun gab: Die
Rollenprüfung stieg bei Fehlfällen aus, bevor sie den Anfragetyp ansah; die
Bereichsprüfung sah die Anzahl der Grenzen an, aber nicht ihre Art. Danach lief
jeweils etwas grün, das nie gefragt worden war — `P-08` in der Prüfschicht
selbst.

Beim ersten kommt eine Bosheit dazu, die ich festhalten möchte: `DirectRunner`
**erfindet** für einen unbekannten Anfragetyp ein `Unavailable`. Ein Fall, der
`Unavailable` erwartet, bekommt damit vom Prüfstand genau die Antwort, die er
hören will. Der Runner tut nichts Falsches — sicher macht es erst die
Validierung davor. Beides steht jetzt in
`test_ein_unbekannter_anfragetyp_faellt_auch_bei_einem_fehlfall_auf`, samt der
Zusicherung, dass der Runner weiterhin so antwortet.

Die Grenzen prüft `is_finite_number` — die mit `is_finite_price` geteilte
Hälfte. Getrennt geblieben sind sie, weil ein Kurs zusätzlich positiv sein muss
und eine Grenze nicht: `(-10, 10)` ist ein richtiger Bereich. Fünf
parametrisierte Gegenproben belegen beide Zusagen: Die Beschreibung wird
beanstandet, **und** `run_scenarios` kommt bis zum Ende.

#### Beim dritten war der genannte Code nicht der einzige

`BGN` stimmte. Statt ihn zu streichen, habe ich die Liste als Ganzes gegen die
offizielle List One gestellt — der Unterschied zwischen Symptom und Inventar:

```
list-one.xml → Pblshd="2026-01-01", 178 vergebene Codes
bei uns, offiziell nicht mehr:  ANG, BGN
offiziell, bei uns nicht:       XAD
```

`ANG` war seit dem 30. Juni 2025 zurückgezogen (abgelöst durch `XCG`), `XAD`
(Arab Accounting Dinar) ist vergeben und wurde von uns abgewiesen — laut
Docstring der Liste „der schlimmere Fehler". Eine Punktkorrektur an `BGN` hätte
beide stehen lassen; das wäre `P-02` gewesen.

Jetzt deckungsgleich: **176** = 178 minus `XXX`/`XTS`. `ISO_4217_AS_OF` trägt
das `Pblshd`-Datum der Quelle statt eines selbstgesetzten Monats — ein Datum,
das von der Quelle stammt, lässt sich gegen sie prüfen.
`test_der_gemeldete_stand_und_die_liste_gehoeren_zusammen` bindet Anzahl und
Stand aneinander, damit sie nicht wieder getrennt altern. Ein Netzabruf im Test
wäre der falsche Weg: rot, sobald jemand im Zug sitzt, und ohne Bezug zur Sache.

#### Vierter Befund

`review_round: 0` bei Arbeitsbeginn, Hochzählen auf `1` bei der ersten
Übergabe — an beiden Stellen. Der Riegel-Abschnitt nennt jetzt auch den Grund:
Zwei verschiedene Runden mit derselben Nummer nähmen dem Schlüssel
`(ticket, handoff_commit, review_round)` genau dort die Eindeutigkeit, wo die
Duplikatsperre auf ihn baut. `227` ist auf die belegten `235` berichtigt.

#### Gegenprobe

Weil die neuen Tests sonst nur behaupten, dass sie prüfen: `src` auf `db53189`
zurückgesetzt, dieselben Tests laufen lassen.

```
6 failed, 20 deselected
  test_ein_unbekannter_anfragetyp_faellt_auch_bei_einem_fehlfall_auf
  test_unbrauchbare_grenzen_sind_ein_beschreibungsfehler [5 Parameter]
    → TypeError: object of type 'float' has no len()
```

Der letzte Fehlschlag ist wörtlich das gemeldete Symptom.

#### Verifikation

* `make test`: Backend **637 / 29 skipped**, Plugin-API **257 / 1 skipped**
  (Runde 2: 235), Dashboard **259**.
* `ruff check app tests plugin_api` und `git diff --check` sauber.
* 23 Mutanten unverändert grün, samt Gegenprobe am heilen Plugin.

Verify `#9` bleibt `⚠️` mit unveränderter Begründung: Half-open und Reset
gehören zu T-23. Neu ist `#6c` — eine kaputte Fallbeschreibung kommt als Befund
zurück, statt die übrigen Fälle mitzureißen.

**Eine Frage an dich für `CLAUDE-REVIEW-PATTERNS.md`:** Ich habe die ersten
beiden Befunde unter `P-08` eingeordnet. Der Fall „das Prüfwerkzeug liefert
selbst die erwartete Antwort" könnte aber ein eigenes Muster verdienen — er
unterscheidet sich davon, dass hier nicht der Test zu schwach ist, sondern die
Gegenseite zu willig. Deine Einschätzung, dein Kapitel.
