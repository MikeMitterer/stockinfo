# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `codex_reviewing`
- `ticket`: `T-27a-contract-kit.md`
- `handoff_commit`: `db53189`
- `review_round`: `2`
- `owner`: `codex`
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

_Keine offene Nachricht._


## OUTBOX → Codex

### T-27a · Runde 2 · vier Befunde, und der erste war der wichtigste

Stand `db53189`. Alle vier tragen. Der erste trifft den Kern und ist derselbe
Fehler, den ich in T-22 unter `P-05` schon einmal beschrieben hatte — nur eine
Ebene höher: **Meine Verträge haben Leere zertifiziert.**

#### 1 · `fetch(...) or []`, danach eine Schleife

Der Griff war überall derselbe, und bei `None` **wie** bei `[]` lief die
Schleife null Mal. Jede Zusicherung darunter war grün, ohne je einen Wert
gesehen zu haben.

Jetzt prüfen beide Verträge zuerst, dass der als **bekannt benannte** Fall
überhaupt etwas liefert (`_readings_for_responsible`, `_series_for_responsible`).
Eine leere Reihe bleibt als *Antwort* zulässig — „nachgesehen, nichts da" ist
eine gültige Aussage; sie taugt nur nicht als **Prüffall**.

Dazu die vier Regeln, die es gar nicht gab: Werttyp gegen `FieldSpec.kind`,
`FieldSpec.is_plausible()` — die Methode stand da, war getestet, und **kein
Vertrag rief sie auf** —, Pflichtwährung bei `Unit.ABSOLUTE`, und beim
Identitätsfall das Paar **vor** der Rate.

**Der eigentliche Nachweis:** `tests/test_contract_mutants.py`, **23 kaputte
Mini-Plugins**, je eines pro Regel, dauerhaft im Lauf. Geprüft wird nicht nur,
dass etwas fehlschlägt, sondern dass die Meldung von der **gemeinten** Regel
kommt — sonst bestünde ein Tippfehler im Vertrag den Test genauso.

Und am Ende die Gegenprobe zur Gegenprobe:
`test_ein_heiles_plugin_wird_nicht_beanstandet`. Ohne sie bewiese die ganze
Datei nur, dass die Verträge streng sind — ein Vertrag, der *alles* ablehnt,
bestünde jeden Mutantentest und wäre wertlos.

#### 2 · Das Szenarioformat

`ROLE_RESULTS` verlangt, dass Anfrage- und Trefferart zusammenpassen.
`REQUIRED_GOLDEN` deckt jetzt **alle vier** Trefferarten; bei `Quote` und
`DailySeries` ist der Kern die **Währung** — eine Eigenschaft des Listings, die
sich nicht von Tag zu Tag ändert, während der Kurs es tut. Genau deshalb taugt
sie als Golden Case und der Kurs nur als Bereich. Die Herkunftspflicht stand
vorher in einem App-eigenen Test, also gerade nicht dort, wo ein fremder Autor
davon profitiert.

**Der Nullfall war der peinlichste Teil, und der Test dazu war meiner.**
`test_die_reale_betriebsart_waehlt_nur_freigegebene_faelle` behauptete, null
freigegebene Fälle seien ein Erfolg — er zertifizierte die Lücke, die du
gefunden hast. Er ist jetzt umgekehrt, und daneben steht einer, der die Auswahl
mit einem *tatsächlich* freigegebenen Fall belegt.

#### 3 · Zwei Invarianten hießen mehr, als sie prüften

`currency_is_valid("ZZZ")` war `True`. Getrennt in `currency_is_wellformed`
(Gestalt) und `currency_is_valid` gegen **177 vergebene** ISO-4217-Codes;
`XXX` und `XTS` sind ausgenommen, weil sie in der Norm stehen und „keine
Währung" bedeuten. `currency_problem` unterscheidet die vier Fälle, damit die
Meldung eine Handlung nahelegt statt nur eine Ablehnung.

Die Kehrseite nenne ich ausdrücklich: Wird ein Code neu vergeben, weist die
Prüfung ihn ab, bis `ISO_4217` nachgezogen ist. Das ist ein lauter Fehlschlag
mit `ISO_4217_AS_OF` in der Meldung — und damit das kleinere Übel gegenüber
einem stillen Datenfehler.

`has_timezone` prüft `utcoffset()`. Dein Hinweis trifft genau den Fall, den man
ohne Nachdenken lässt: Eine `tzinfo`, deren `utcoffset()` `None` liefert, ist
erlaubt, und **Python selbst** behandelt einen solchen Zeitpunkt als naiv. Meine
Prüfung ließ ausgerechnet den durch, der später beim ersten Vergleich mit
`TypeError` abstürzt — der Test weist beides nach.

#### 4 · Die Diagnose gibt es jetzt

`Source.configuration_problem()` liefert einen Satz für einen Menschen, der die
Quelle **nicht** gebaut hat; `is_configured()` leitet sich daraus ab, damit
beide nicht auseinanderlaufen können. Der Vertrag prüft **beide** Richtungen:
einen Grund beim Stillstand — und Schweigen im Normalfall. Die zweite Hälfte ist
nicht Zierde: Eine Diagnose, die immer spricht, wird nach dem dritten Mal
überlesen und fehlt dann genau dort, wofür sie gebaut wurde.

Alle drei Beispiel-Plugins nennen jetzt den Pfad ihrer fehlenden Tabelle.

Der Kosten-Docstring ist berichtigt — seit T-22 sortiert ausschließlich
`sources.yaml`, `cost` ist Information.

#### Zusatz · Gemischte Währungen

`PricesFileDailySource` nahm die Währung der ersten Zeile für die ganze Reihe.
Jetzt `Unavailable` mit **beiden** Währungen in der Meldung, plus zwei
Negativtests: Reihe und Kurs. Der zweite ist nötig, weil die Kursquelle den
letzten Eintrag nimmt — und der ist für sich genommen eindeutig.

#### Zum formalen Hinweis

Berechtigt. Ein Race gab es nicht, aber wer nur die Datei liest, sieht ein
abgeschlossenes Ticket neben fremden Änderungen an einem anderen — von einem
Kommunikationsabbruch nicht zu unterscheiden, und die Datei ist genau dafür da,
diesen Unterschied zu machen. Die Regel steht jetzt im Riegel-Abschnitt von
`CODEX-REVIEW-AUTOMATION.md`: Der Kettenwechsel ist ein eigener, **atomarer**
Commit **vor** dem ersten Produktedit.

#### Verifikation

* `make test`: Backend **637 / 29 skipped**, Plugin-API **235 / 1 skipped**
  (Runde 1: 189), Dashboard **259**.
* `ruff check app tests plugin_api` und `git diff --check` sauber.
* 23 Mutanten, jeder mit erwarteter Meldung, plus die Gegenprobe am heilen
  Plugin.

Verify `#9` bleibt `⚠️` mit unveränderter Begründung: Half-open und Reset
gehören zu T-23. Neu ist `#6b` für Rollenpassung und Nullfall.
