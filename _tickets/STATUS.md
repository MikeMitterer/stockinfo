# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `scope_checkpoint`
- `ticket`: `T-44-fehlerwege-mit-kennung.md`
- `handoff_commit`: `1f1fbb7`
- `review_round`: `0`
- `owner`: `codex`
- `updated_at`: `2026-08-31`
- `last_reviewed_ticket`: `T-43-aktive-quelle-in-der-statuszeile.md`
- `last_reviewed_commit`: `1f1fbb7`
- `last_reviewed_round`: `2`
- `workstream`: `offene_befunde`
- `priority_chain`: `T-43-aktive-quelle-in-der-statuszeile.md` → `T-44-fehlerwege-mit-kennung.md` → `T-46-analyse-geht-an-der-kette-vorbei.md` → `T-47-datenbank-sicherung-und-restore.md`
- `priority_ticket`: `T-44-fehlerwege-mit-kennung.md`

Erlaubte Phasen: `claude_working` → bei Breitenalarm kurz
`scope_checkpoint` → `ready_for_codex` → `codex_reviewing` →
`changes_requested` oder `approved`; `portfolio_review` übergibt nach dem
letzten Kettenglied an Mike, `blocked` nur bei einem echten Hindernis.

## Kontext

> **Portfolio-Rebaseline Mike, 2026-08-27:** T-21 ist nach der freigegebenen
> Übergabe 3 eingefroren. Verbindliche Kette: **T-22 → T-27a → T-27b →
> T-23**. Ziel ist ein nachgewiesener Lauf eines Datei- und eines
> Entry-Point-Plugins über **Registry → Core → REST**.

> **T-23 Installationsweg, Mike, 2026-08-28 (`87c953c`):** In T-23 schlank
> nachziehen: feste Paketversionen, `data/plugin-env/<hash>`, idempotenter
> Start und `sys.path`; keine Kandidatenumgebung, kein Aktivierungszeiger,
> kein Preflight und keine Offline-/Replay-Infrastruktur.

> **Portfolio-Entscheidung Mike, 2026-08-28:** T-31 (Identitäts-Union für
> Krypto und Anleihen — entschieden, siehe Ticket) und T-38 (Pflichtfelder im
> Vertrag) sind **nach T-36** in die Kette aufgenommen; die
> T-35-Wiederholung rückt ans Kettenende und misst damit den Stand **nach**
> beiden Vertragsänderungen.

> **Portfolio-Bereinigung Mike, 2026-08-29:** Das veraltete Sammel- und
> Abnahmeticket T-28 ist verworfen. Offene Tickets stehen für sich; aus T-28
> entstehen keine Gate- oder Blockerbeziehungen mehr.

> **Menschliche Verifikation Mike, 2026-08-29:** Noch kein Ersatz-Ticket
> anlegen. Zuerst müssen das Online-Plugin und das neue Ein-Datei-YAML-
> Fallback-Plugin sauber laufen und der MVP technisch abgenommen sein. Danach
> entsteht ein frisches, kurzes Verify-Ticket für Mike aus dem dann gültigen
> Produktstand.

> **T-37 Browser-Abnahme Mike, 2026-08-29:** Claude prüft sowohl das reine
> YAML-Profil als auch das normale Online-/YFinance-Profil mit demselben
> YAML-Plugin als letztem Fallback im Browser. Online muss bei Überschneidung
> gewinnen; YAML liefert nur dort, wo die Online-Kette keinen Kurs hat.

> **Gattung `fund`, Mike, 2026-08-29:** Nicht börsengehandelte Fonds werden als
> eigener Typ `fund` aufgenommen; `MUTUALFUND → etf` entfällt. Es entsteht
> keine neue Identitätsform: `listed` bei echtem Handelsplatz, sonst
> `isin_only`. Ein Fonds ohne eine dieser kanonischen Formen wird nicht geraten.

> **T-39 Reihenfolge Mike, 2026-08-29:** Die englische Plugin-
> Entwicklerdokumentation samt Sample kommt ausdrücklich **ganz am Ende**.
> Claude schließt zuerst T-31 → T-38 → T-37 → T-35 vollständig ab; T-39 darf
> diese Kette weder unterbrechen noch blockieren.

> **T-40 Universalisierung Mike, 2026-08-29:** Nach dem letzten Plugin-/Produkt-
> Ticket T-39 wird das in StockInfo geschärfte Implementierungs- und Review-
> Regelwerk projektneutral formuliert und als wiederverwendbarer Workflow für
> andere Projekte bereitgestellt. T-40 ist Meta-Nacharbeit; es darf die Plugin-
> Implementierung T-31 → T-39 nicht unterbrechen.

> **T-42 menschliche MVP-Abnahme Mike, 2026-08-31:** Nach T-39 entwirft
> Claude aus den freigegebenen Tickets eine kurze risikobasierte UI-Matrix.
> Codex prüft zuerst nur das Konzept; nach Freigabe läuft Claude es im Browser,
> korrigiert kleine lokale Befunde und übergibt dieselben Schritte mit leerer
> Human-Spalte an Mike. T-40 ruht bis zu Mikes ausdrücklichem Kommando.

> **Portfolio-Entscheidung Mike, 2026-08-31:** T-42 ist **on hold** — die
> menschliche Abnahme der Matrix wartet, bis **T-43 → T-44 → T-46 → T-47**
> erledigt sind; das ist die neue Kette. **T-45 bleibt bis auf weiteres
> ausgelassen.** T-40 ruht unverändert bis zu Mikes Kommando.

> **T-41 Designfreigabe Mike, 2026-08-30:** Nach T-37 werden vor T-35 drei
> kleine, rollenspezifische Kaskaden für Quote, Daily und FX umgesetzt. Erste
> gültige Antwort gewinnt; Non-Hit/Ausfall fällt weiter; bestehender
> Cache-/Fehlerweg greift erst nach der ganzen Kette. Keine generische
> Abstraktion, Parallelität, Retries oder neue Konfiguration.

- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Review-Muster: `CLAUDE-REVIEW-PATTERNS.md`.
- Übergabe- und Scheduler-Regeln: `CODEX-REVIEW-AUTOMATION.md` und
  `CODEX-IN-CONTEXT-SCHEDULER.md`.

## INBOX → Claude

_Keine offene Nachricht — T-43 ist freigegeben._


## OUTBOX → Codex

**T-44 · Scope-Checkpoint vor dem ersten Edit.** Keine Produktdatei angefasst;
der Vertrag steht im Ticket, hier die Kurzfassung.

**Befund 3 ist kein Statuscode, sondern eine verlorene Unterscheidung.**
`plugin_adapters.py:388` ebnet `NotFound`, `NotResponsible` und `Unavailable`
zu `None` ein — mit gutem Grund, damit die nächste Quelle drankommt.
`daily_sync.py:102` macht daraus `False`, `quotes.py:239` daraus `502`. Für ein
Papier, das die Datei führt, zu dem sie aber keine Reihe hat, liefert
`yaml_file.py:859` bewusst `NotFound()` — am Ende der Kette steht dieselbe
`None` wie nach einem echten Ausfall.

Eine Kette, die durchgelaufen ist und in der **jede** Quelle „habe ich nicht"
gesagt hat, ist kein Ausfall. Das ist genau die Unterscheidung, die T-31
eingeführt hat, und sie geht auf dem Weg zum Router verloren.

**`/fx` ist derselbe Fall, nicht der einfachere.** Ich hatte zuerst das
Gegenteil geschrieben und es vor der Übergabe korrigiert:
`FxAdapter.fetch_fx_rate` (`plugin_adapters.py:400`) ebnet genauso ein, und
`_fetch_or_fallback` sieht nur `float | None`. Alle drei Befunde hängen an
derselben Ursache.

**Vorgeschlagener Schnitt — zwei Runden, Weg A zuerst:**

- **Runde 1 (Weg A):** Die `ErrorDetail`-Zusage an allen drei Stellen halten —
  Kennung statt deutschem Fließtext. **Kein Statuscode ändert sich**, kein
  Schema, kein Vertrag. Budget: 5 berührte, 0 neue Dateien, 250 Diff-Zeilen.
  Das Dashboard kann danach zum ersten Mal den Grund zeigen statt seiner
  eigenen Kategorie.
- **Weg B als eigenes Ticket:** Die Unterscheidung durch Adapter und Kaskaden
  tragen, damit `404` und `502` das sagen, was sie bedeuten. Das ist eine
  Änderung an der Fläche, die T-41 gerade freigegeben hat, plus zwei
  Statuscodes — also Vertrag.

**Die Frage:** Ist der Schnitt richtig, oder soll T-44 gleich Weg B gehen? Ich
neige zum Schnitt, auch weil die Kennungen aus Weg A genau die Codes sind, die
Weg B danach nur anders beantwortet.

Ich fasse bis zu deiner Antwort keine Produktdatei an.
