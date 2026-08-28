# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-23-plugin-registry.md`
- `handoff_commit`: `e6ca003`
- `review_round`: `1`
- `owner`: `codex`
- `updated_at`: `2026-08-28`
- `last_reviewed_ticket`: `T-27b-http-fake-real.md`
- `last_reviewed_commit`: `08814ff`
- `last_reviewed_round`: `6`
- `workstream`: `plugin_mvp`
- `priority_chain`: `T-22-quellen-konfiguration.md > T-27a-contract-kit.md > T-27b-http-fake-real.md > T-23-plugin-registry.md`
- `priority_ticket`: `T-23-plugin-registry.md`

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

### T-23 · Runde 1 · Registry mit zwei Ladewegen, zwei Plugins, Auswahl per Konfiguration

Stand `e6ca003`. **Ausdrücklicher Auftrag von Mike:** Prüf besonders das zweite
Plugin und die Auswahl zwischen beiden — das ist der Kern dieser Runde.

#### Was gebaut ist

* `app/plugin_loader.py` — Entry-Point-Gruppe `stockinfo.sources` **und**
  `data/plugins/*.py` mit `SOURCES = [...]`. Rollen werden aus den geerbten
  Protokollen **abgeleitet**, nicht deklariert. Jeder Fehlerfall (Import wirft,
  falsche `api_version`, kein Name, keine Rolle, doppelter Name) wird gemeldet
  und übersprungen; die App startet.
* `app/plugin_guard.py` — die eine Stelle, an der fremdem Code misstraut wird.
  Ausnahme → `Unavailable`, Schutzschalter nach drei Fehlschlägen in Folge,
  Half-open und Reset gegen eine **hereingereichte Uhr**.
* `app/plugins/justetf_metadata.py` und `app/plugins/yfinance_quotes.py` — die
  vorhandenen Anbindungen in ihren Rollen, ohne zweite Fachlogik.
* `tests/test_plugin_selection.py` — ein **eigenständiges CSV-Plugin** wird aus
  `data/plugins/` geladen; `sources.yaml` entscheidet zwischen ihm und dem
  echten Anbieter.

#### Das CSV-Format, damit du es gegen den Code prüfen kannst

```
closes.csv   ticker;mic;date;close;currency
fx.csv       base;quote;rate;date
```

Semikolon, Kopfzeile Pflicht. `ticker;mic` ist der Schlüssel, weil die
`QuoteRequest` genau damit kommt. Mehrere Zeilen je Papier sind erlaubt, **die
letzte gilt**; widersprechende Währungen eines Papiers ergeben `Unavailable`.

#### Drei Fehler, die erst das Messen gezeigt hat

1. **`provider_alias('RY', 'ZZZZ')` liefert den nackten Ticker `'RY'`.** Für
   die US-Plätze ohne Alias ist das richtig, für eine unbekannte Börse still
   falsch: yfinance läse `'RY'` als NYSE-Listing und lieferte einen Kurs in der
   falschen Währung, ohne dass irgendwo ein Fehler entstünde. `_symbol` prüft
   jetzt gegen `EXCHANGES`. **Das ist ein Befund über den Bestand, nicht nur
   über mein Plugin** — die Zuordnung verhält sich in der App genauso.
2. **`fetch_daily_closes` ruft `auto_adjust=True`**, meine Reihe meldete
   `adjusted=False`. Der Wert stimmte, seine Bedeutung nicht — ein Verbraucher
   hätte mit einer Rendite gerechnet, die es so nie gab. Zusätzlich kennt die
   Anbindung kein `end`; das wird jetzt im Plugin gefiltert statt still
   ignoriert.
3. **Das CSV-Plugin filterte nach `isin`**, die Anfrage trägt `ticker`/`mic`.
   Der Filter lief ins Leere. Mit nur **einer** Zeile in der Tabelle wäre das
   nie aufgefallen, weil zufällig die richtige Zeile die einzige war — deshalb
   trägt sie jetzt zwei Papiere und es gibt eine Gegenprobe darauf.

#### Was ich dir zur Prüfung besonders gebe

* Ob die Grenze bei der Kapselung richtig liegt: Geladene Quellen bekommen
  `GuardedSource`, eingebaute nicht. Meine Begründung steht an `SourceSpec.loaded`
  — eigene Ausnahmen sind Fehler **dieser** App, und sie zu `Unavailable` zu
  machen hieße, den eigenen Fehler als Anbieterausfall auszugeben. Das ist eine
  Entscheidung, keine Selbstverständlichkeit.
* Ob `specs_by_name()` an der richtigen Stelle verhindert, dass ein Plugin eine
  eingebaute Quelle verdrängt.
* Ob der Modulzustand `_LOADED` in der Registry tragbar ist. Ich halte ihn für
  richtig (einmal beim Start), aber er ist globaler Zustand, und die Tests
  brauchen dafür eine Aufräum-Fixture — das ist ein Geruch.

#### Was noch fehlt

Verify `#6b` (Harness Registry → Core → REST) und `#1`/`#2` als durchgehender
Lauf. Verify **`#6c` ist nach Mikes Entscheidung gestrichen** — die
Kandidatenumgebung beantwortet die Frage „fremdes Paket in eine laufende
Instanz installieren", die es hier nicht gibt. Ich trage die Streichung im
Ticket nach.

#### Verifikation

* `make test`: Backend **704 / 29 skipped** (vorher 691), Plugin-API
  **257 / 1 skipped**, Dashboard **259**.
* `pytest -m "not integration"`: **697 passed, 7 deselected**.
* `pytest -m integration`: **7 passed**.
* `ruff check app tests plugin_api` und `git diff --check` sauber.
