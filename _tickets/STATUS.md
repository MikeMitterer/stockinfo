# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-27a-contract-kit.md`
- `handoff_commit`: `6121a94`
- `review_round`: `1`
- `owner`: `codex`
- `updated_at`: `2026-08-27`
- `last_reviewed_ticket`: `T-22-quellen-konfiguration.md`
- `last_reviewed_commit`: `490314a`
- `last_reviewed_round`: `3`
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

### T-27a · Runde 1 · Contract-Kit für alle fünf Rollen

Stand `6121a94`, Branch `t-27a-contract-kit`. Elf Verify-Zeilen: zehn `✅`,
eine `⚠️` mit Begründung.

#### Was entstanden ist

| Datei | Zweck |
|---|---|
| `invariants.py` | ISIN-Prüfziffer, MIC, Währung, endliche Zahlen, Datumsfolge |
| `types.py` | `QuoteRequest`/`Quote`, `DailyRequest`/`DailyBar`/`DailySeries`, `FxRequest`/`FxRate` |
| `sources.py` | `QuoteSource`, `DailyCloseSource`, `FxSource` |
| `testing/` | aus einer Datei ein Paket: `contracts`, `scenarios`, `doubles` |
| `examples/prices_file.py` | drei Quellen — die Nutzer der drei neuen Verträge |
| `app/exchanges.py` | bezieht ISIN- und MIC-Form jetzt aus dem Vertrag |

#### Der DRY-Punkt, und diesmal habe ich in die richtige Richtung geschaut

In T-22 Runde 1 hattest du mich dafür, dass ich zwei Verträge **neu
geschrieben** habe, die es längst gab. Hier lag derselbe Fall umgekehrt vor:
Die App kannte `is_real_mic` und `ISIN_PATTERN`, das Kit hätte beides
gebraucht — und ein öffentliches Paket darf nicht von `app/` abhängen.

Aufgeteilt nach **Wissen**, nicht nach Bequemlichkeit: Die *Form* („vier
Zeichen, Großbuchstaben oder Ziffern") ist eine Aussage über ISO 10383 und
liegt im Vertrag. *Welche Sammelcodes* es gibt, hängt daran, welche Quellen
jemand einsetzt — das weiß nur die App. `app.exchanges.is_real_mic` ist die
Stelle, an der beides zusammenkommt.

**Gegenprobe gelaufen**, weil „es gibt nur eine Regel" sonst eine Behauptung
wäre. `mic_is_wellformed` im Plugin-Paket verstümmelt:

```text
Backend      10 failed, 627 passed
Plugin-API    5 failed, 183 passed
```

Beide Seiten fallen. Mutant zurückgenommen, danach alles grün.

#### Zwei Funde der neuen Regeln — im **bestehenden** Code

Beide beim ersten Lauf, beide hat kein Mensch gefunden:

1. **`CA00000000000` war keine ISIN.** Dreizehn Zeichen, falsche Prüfziffer,
   und stand als „unbekanntes Papier" in der Beispielsuite. Der Test maß damit
   die *Formprüfung* des Plugins statt seines Verhaltens bei einem echten, aber
   nicht geführten Papier. Ersetzt durch `CA0679011084` (Barrick Gold).
2. **`MetadataFileSource._COLUMNS` war ein Dict an der Klasse** — allen
   Instanzen gemeinsam. Jetzt `MappingProxyType`.

Der zweite hat mich die Regel schärfen lassen: Sie nennt jetzt den Ausweg
(`tuple`/`frozenset`/`MappingProxyType`), sonst wird sie beim ersten
Fehlalarm unterdrückt statt befolgt.

#### Die eine `⚠️`, und warum sie nicht grün ist

Verify `#9` verlangt „TTL, Half-open und Reset ohne echte Wartezeit prüfbar".

**TTL ist vorgeführt**, nicht behauptet: ein Ablauf von einer Stunde in null
Sekunden Laufzeit, mit exakter Grenze statt „ungefähr". Der Cache dort ist
Testcode und bleibt es — einen TTL zu bauen, damit die Zeile grün wird, wäre
die Umkehrung der Beweisführung.

**Half-open und Reset fehlen bewusst.** Ihre Bedeutung legt T-23 fest; sie hier
vorwegzunehmen hieße, einen Entwurf zu erfinden, um ihn dann zu prüfen — das
ist `P-07` und Leitplanke 8 in einem. Die Zeile bleibt `⚠️`, bis T-23 sie
einlöst.

#### Ein eigener Regelverstoß, den ich melde statt zu verschweigen

Beim Gegenlesen fiel mir auf, dass ich **deutsche lokale Variablen**
geschrieben hatte. CLAUDE.md lässt das ausnahmslos nicht zu, und die Altlast in
den bestehenden Beispielen zog nach derselben Regel mit.

Der Weg dorthin ist der eigentliche Bericht:

1. **Regex-Ersetzung → Prosaschaden.** Aus „niemand sonst je **gesehen** hat"
   wurde „je **seen** hat". Genau davor warnt mein eigener Merksatz.
2. **`tokenize` über `NAME`-Token → sicher, aber unvollständig.** Unter
   Python 3.11 ist ein f-String **ein** Token; die Interpolationen blieben
   stehen und wären zur Laufzeit `NameError` gewesen.
3. **`ast`-Lauf über `JoinedStr`** fand alle fünfzehn. Der positionsbasierte
   Umbau scheiterte danach an einer Zusicherung — die Spaltenangaben in
   f-Strings sind unter 3.11 nicht verlässlich. Die Zusicherung hat verhindert,
   dass etwas Falsches geschrieben wurde; korrigiert habe ich von Hand, mit der
   vollen Zeile als Anker.

**Gegenprobe:** `ast`-Inventar über alle `Name`, `arg`, `FunctionDef`,
`ClassDef` — 382 Bezeichner, keiner mehr deutsch. Docstrings und Testnamen sind
unverändert deutsch.

#### Verifikation

* `make test`: Backend **637 / 29 skipped**, Plugin-API **189 / 1 skipped**
  (vorher 36), Dashboard **259** in 47 Dateien.
* `ruff check app tests plugin_api` und `git diff --check` sauber.
* Gegenproben: geteilte MIC-Regel (oben), lügende Aufzeichnung gegen Golden
  Case (rot, wie verlangt), veränderliches Klassenattribut (rot).

**Kein Smoke-Script.** Jede Zeile der Matrix ist eine Aussage über
Bibliothekscode; nichts gilt erst nach einem Neustart. Ein Script, das nur
`pytest` aufruft, wäre eine zweite Fassade vor demselben Lauf — sag mir, wenn
du das anders siehst.

#### Was T-27b erbt

Der HTTP-Runner samt Aufzeichnung und Realbetrieb. Das Format steht,
`run_scenarios(..., only_real=True)` wählt bereits aus. Die Zusage, an der
T-27b dieses Ticket messen kann: **Es soll dort keine Zeile an einem Szenario
geändert werden müssen.**
