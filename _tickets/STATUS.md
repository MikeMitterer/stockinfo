# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `codex_reviewing`
- `ticket`: `T-22-quellen-konfiguration.md`
- `handoff_commit`: `20af8fa`
- `review_round`: `1`
- `owner`: `codex`
- `updated_at`: `2026-08-27`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `7a14d79`
- `last_reviewed_round`: `51`
- `workstream`: `plugin_mvp`
- `priority_chain`: `T-22-quellen-konfiguration.md > T-27a-contract-kit.md > T-27b-http-fake-real.md > T-23-plugin-registry.md`
- `priority_ticket`: `T-22-quellen-konfiguration.md`

Erlaubte Phasen: `claude_working` → `ready_for_codex` → `codex_reviewing` →
`changes_requested` oder `approved`; `portfolio_review` übergibt nach dem
letzten Kettenglied an Mike, `blocked` nur bei einem echten Hindernis.

Der Scheduler verarbeitet nur ein neues, valides Tupel aus Ticket, Commit und
Runde. Bei `ready_for_codex` muss `ticket` zusätzlich exakt
`priority_ticket` entsprechen und in `priority_chain` stehen.

## Kontext

> **Portfolio-Rebaseline Mike, 2026-08-27:** Das bisherige Vorgehen hat den
> Plugin-Host aus den Augen verloren. T-21 wird nach der freigegebenen
> Übergabe 3 eingefroren. Als Nächstes gilt ausschließlich die Kette
> **T-22 → T-27a → T-27b → T-23**. Ziel ist ein nachgewiesener Lauf eines
> Datei- und eines Entry-Point-Plugins über **Registry → Core → REST**.

> **Freigegebener T-21-Sockel:** Produktstand `2dd0dc3`, Review-Freigabe
> `d3fecb8`, anschließender Statusstand `ce55202`. Die späteren 4A-Stände
> `7a14d79` und `48fff52` sind eingefroren; Runde 52 wurde bewusst nicht mehr
> geprüft. 4A/4B werden erst nach dem Plugin-MVP wieder eingeordnet.

> **Sauberer Branch für T-22:** Nicht auf dem aktuellen 4A-Produktstand
> weiterbauen. Vom freigegebenen Sockel `ce55202` den Branch
> `t-22-quellen-konfiguration` erstellen. Danach zuerst den reinen
> Prozess-Commit `27d6195` und anschließend den Tip von
> `t-21d-offene-zuordnungen` mit dieser Rebaseline cherry-picken. Vor dem
> ersten Produktedit prüfen, dass `git log -1` die Rebaseline zeigt und
> `git diff --check` sauber ist.

> **T-28:** Nach T-23 werden T-19, T-21 4A/4B, T-25, T-26 und T-29 bis T-34
> einzeln als zwingendes Gate oder ausdrückliches Follow-up klassifiziert.
> Sie blockieren den ersten Plugin-MVP nicht automatisch. Nach Freigabe von
> T-23 gilt `phase: portfolio_review`, `owner: mike`; kein Ticket wird dann
> selbständig gestartet.

- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Review-Muster: `CLAUDE-REVIEW-PATTERNS.md`.
- Übergabe- und Scheduler-Regeln: `CODEX-REVIEW-AUTOMATION.md` und
  `CODEX-IN-CONTEXT-SCHEDULER.md`.
- T-17, T-18, T-20 und T-24 sind bereits Codex-abgenommen und bleiben bis zur
  gesammelten menschlichen Abnahme im Board-Root.

## INBOX → Claude

_Keine offene Nachricht._


## OUTBOX → Codex

### T-22 · Runde 1 · Quellen kommen aus der Datei

Erstes Glied der MVP-Kette. Stand `20af8fa`, sauberer Branch
`t-22-quellen-konfiguration` vom freigegebenen Sockel.

#### Was da ist

**Die `if`-Kaskade ist weg.** `app/sources_config.py` liest
`data/sources.yaml`, `app/sources_registry.py` macht aus einem Namen ein
Objekt, `container.py` baut nur noch aus der Kette. `GET /sources` zeigt, was
gilt — **einschließlich** der nicht einsatzbereiten Quellen; eine still
weggelassene Quelle nimmt dem Betreiber die Erklärung für ihr Fehlen.

Dazu die zwei Verträge, die nirgends standen: `DailyCloseProvider` und
`FxProvider`. `YFinanceProvider` erfüllte sie längst — man erfuhr sie beim
Scheitern, nicht beim Lesen.

#### Drei Dinge, die erst beim Ausführen auffielen

Genau der Punkt aus Leitplanke 8, deshalb nenne ich sie einzeln:

1. **Der Bauplan brauchte die Rolle.** yfinance beantwortet vier Fragen, und
   für `etf_meta` ist die Antwort ein `YFinanceEtfEnricher`, für `quotes` ein
   `YFinanceProvider`. Meine erste Fassung gab beiden dasselbe Objekt — der
   ETF-Kette hätte `is_responsible` gefehlt, und das wäre erst beim ersten
   ETF-Abruf aufgefallen.
2. **`strict_exchange` hätte still seine Wirkung verloren.** Die Einstellung
   schaltet den Yahoo-Fallback **aus der Kette**. Die Kette allein aus der
   Datei zu nehmen hätte ihn bei jedem bestehenden Betreiber mit
   `STRICT_EXCHANGE=true` wieder eingeschaltet — ohne dass er etwas geändert
   hätte, und mit genau der Überraschung in fremder Währung, die er
   ausgeschlossen hatte. Sie formt jetzt die **Vorgaben**; eine vorhandene
   Datei gewinnt weiterhin. Die zwei alten `test_container`-Tests prüften den
   **Rückgabetyp** und sind auf die Frage umgeschrieben, um die es geht: wer in
   der Kette steht.
3. **Leseweg und Verdrahtung brauchten denselben Pfad-Helfer.** Der Endpunkt
   rief `get_sources_config()` direkt auf; ein `dependency_overrides` griff
   nicht, und er hätte etwas anderes gemeldet, als die App benutzt.

#### Verifikation

* `./_tickets/T-22-smoke.sh --run`: **5/5 über echte Neustarts.** Jede
  Verify-Zeile sagt „…, Neustart" — eine Konfiguration, die erst danach gilt,
  muss auch darüber geprüft werden. Kein Netz nötig, eigener Port (8774),
  beendet nur die eigene PID.
* `make test`: Backend **633 passed, 29 skipped** (vorher 629), Plugin-API
  **36**, Dashboard **259 passed** in 47 Dateien.
* `ruff check app tests`, `git diff --check`: sauber.
* Namens-Inventar: `ast` über alle geänderten Dateien, 296 Bezeichner, keiner
  deutsch. Bash-Variablen im Script durchgehend GROSS.

#### Zwei Mutanten — und zwei Testfehler, die sie aufgedeckt haben

`is_configured` immer `True` → der Pflichtschlüssel-Test fällt. Kette umdrehen
→ **kam zuerst durch.** Zwei eigene Fehler steckten dahinter, beide jetzt
korrigiert und im Docstring benannt:

* Der Test benutzte **eine** Quelle — eine umgedrehte Einerliste ist dieselbe
  Liste.
* Und er rief `_chain()` statt `_build_resolver()`, also eine Ebene **unter**
  der Verdrahtung. Ein Fehler genau dort, wo die Kette zum Resolver wird, wäre
  durchgegangen.

Nach beiden Korrekturen schlägt der Mutant an.

#### Ein Zuschnittsbefund: Verify `#0` ist nicht gebaut

Das Profilpaket (`profile: stockinfo-profile-canada==1.0.2`) ist ein
**installiertes Paket**, aus dem Ketten gelesen werden. Es zu laden heißt,
einen Lader für Pakete zu haben — und genau der ist **T-23**, „Registry, zwei
Ladewege". In T-22 gebaut, entstünde ein zweiter Ladeweg neben dem, den T-23
danach anlegt.

Gelesen wird das Feld bereits: `SourcesConfig.profile` trägt den Wert, und
`GET /sources` gibt ihn aus. Die Zeile ist damit in der Konfiguration
**vorhanden und wirkungslos** statt unbekannt; T-23 muss sie nur noch
auflösen. Die Verify-Zeile steht auf `➖` mit dieser Begründung.

Wenn du das anders siehst, sag es jetzt — nicht nach T-27a.

#### Verify `#2b` steht auf `⚠️`

Es gibt heute **keine** eingebaute Quelle mit pflichtigem Schlüssel. Der Test
stellt eine `SourceSpec` mit `needs=("api_key",)` her und prüft alle drei Lagen
— fehlend, leer, gesetzt. Über den echten Endpunkt ist die Zeile erst belegbar,
wenn eine solche Quelle existiert; das wird mit dem ersten Plugin der Fall
sein, das einen Schlüssel verlangt. Ich habe die Zeile nicht auf `✅` gesetzt,
weil „über die echte Kette" hier nicht stimmt.

#### Angepasst, weil es sonst gebrochen wäre

`requirements.txt` deklariert jetzt `pyyaml` — es war bisher nur transitiv da,
und eine Abhängigkeit, die man nicht deklariert, verschwindet beim nächsten
Upgrade eines anderen Pakets. `docs/sources.yaml.example` liegt in `docs/` und
nicht in `data/`, weil das Laufzeit-Volume nicht versioniert wird.
