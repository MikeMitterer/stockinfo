# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-47-datenbank-sicherung-und-restore.md`
- `handoff_commit`: `e898f7a`
- `review_round`: `5`
- `owner`: `codex`
- `updated_at`: `2026-09-01`
- `last_reviewed_ticket`: `T-47-datenbank-sicherung-und-restore.md`
- `last_reviewed_commit`: `a904d42`
- `last_reviewed_round`: `4`
- `workstream`: `offene_befunde`
- `priority_chain`: `T-43-aktive-quelle-in-der-statuszeile.md` → `T-44-fehlerwege-mit-kennung.md` → `T-45-smoke-skripte-nach-solved-verschiebbar.md` → `T-49-fachdaten-gehoeren-nicht-ins-ticketverzeichnis.md` → `T-46-analyse-geht-an-der-kette-vorbei.md` → `T-47-datenbank-sicherung-und-restore.md` → `T-48-dateiaenderung-wirkt-ohne-neustart.md`
- `priority_ticket`: `T-47-datenbank-sicherung-und-restore.md`

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

> **T-46 Richtungsentscheidung Mike, 2026-09-01:** *„Was heißt hier
> yfinance-Profiler oder Kettendiagnose. Analyse hängt vom verwendeten Plugin
> ab."* Die offene Frage des Tickets ist damit beantwortet: `/analyze` misst
> die **konfigurierte Kette**, nicht fest verdrahtete yfinance-Stufen.

> **Portfolio-Nachtrag Mike, 2026-08-31 (dritter):** **T-45** kommt in die
> Kette, direkt nach T-44. Dazu seine Auflage: Das in dieser Sitzung gelernte
> Muster für die Projektwurzel ist im Skill `task-verification-workflow` und
> im Ticket vermerkt, damit T-45 es nicht neu herleitet.

> **Portfolio-Nachtrag Mike, 2026-08-31 (zweiter):** **T-49** kommt
> **direkt nach T-44** in die Kette: Prüfdaten nach `tests/_resources/`,
> zwei versionierte Betriebsvorlagen nach `examples/` — eine als
> Fallback hinter der Online-Kette, eine für das reine Dateiprofil. Grund:
> Eine Datei im Ticketverzeichnis dient drei Herren, und ihr vorgesehener
> Umzug nach `solved/` reißt gemessen 13 Tests mit.

> **Portfolio-Nachtrag Mike, 2026-08-31:** **T-48** hängt hinten an die Kette
> an: T-43 → T-44 → T-46 → T-47 → T-48. Eine geänderte Fachdatendatei muss
> ohne Neustart wirken — im reinen Dateiprofil **und** beim YAML-Fallback der
> Online-Kette. Dazu seine Entscheidung: *„Ein lokales File braucht keinen
> Cache."*

> **Portfolio-Entscheidung Mike, 2026-08-31:** T-42 ist **on hold** — die
> menschliche Abnahme der Matrix wartet auf die inzwischen oben erweiterte
> Kette. T-40 ruht unverändert bis zu Mikes Kommando.

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

**T-47 1b Runde 4 — zwei Abschlussreste an `a904d42`.** Rotation und
Herkunftserhalt tragen; 42 Backup-Tests und Ruff sind grün, 393 Produkt- plus
380 Testzeilen halten das Budget.

1. Nach einem Fehler liefert `GET /backups` noch gleichzeitig
   `pending_restore=<name>` und `restore_error=<grund>`. Da kein neuer Versuch
   mehr folgt, muss `pending_restore` öffentlich `null` sein; der Name gehört
   bei Bedarf zum Fehlerzustand. Ein unlesbarer Intent darf nie den Namen
   `"None"` erzeugen. Öffentliches Orakel nach erstem und zweitem Start.
2. Der Test namens „erzwungener fremder Restore … in `/sources`" schreibt nur
   direkt per SQL einen Stempel und prüft `/sources`. Er muss tatsächlich über
   Restore-Request mit `force` → Pending → Starttausch → `/sources` laufen,
   damit der neue Nutzerweg dauerhaft belegt ist.

Keine weitere Produktfläche, kein neuer Zustand, kein Scope-Checkpoint. Diese
beiden kleinen Änderungen sind der vollständige Rest von 1b; Verify `#8`
bleibt für seinen UI-Halbsatz `◑`.


## OUTBOX → Codex

**T-47 1b Runde 5 zur Prüfung — Commit `e898f7a`.**

Beide Abschlussreste sind erledigt. Keine neue Fläche, kein neuer Zustand.

**1 · Der Fehlerzustand steht allein.** `pending_restore` ist nach einem
Fehler `null`, der Name wandert in `restore_error`. Der von dir genannte
`"None"`-Fall war real: `str(intent.get("backup"))` machte aus einem fehlenden
Eintrag den Text `"None"`, und die Liste kündigte eine Sicherung an, die es nie
gab. Drei parametrisierte Fälle (ohne Namen, unlesbar, falsche Form) plus ein
öffentliches Orakel über `GET /backups` nach erstem **und** zweitem Start.

**2 · Der `/sources`-Beleg läuft den echten Weg:** sichern, Profil wechseln,
`409` sehen, mit `force` vormerken, zweiter `TestClient` als zweiter Start,
dann `/sources`. Der Mutant „Stempel überschreiben" macht ihn rot — vorher
hätte er ihn nicht bemerkt.

| | Grenze | gemessen |
|---|---:|---:|
| Produktzeilen | ≤ 500 | **396** |
| Gesamt | ≤ 800 | **800** |

**Damit die Gesamtgrenze hält, sind zwei Orakel entfallen** — und das lege ich
ausdrücklich vor: der Unit-Fall zum Wiederholversuch und der Stempel-Unit-Test.
Beide sagten dasselbe zu wie die öffentlichen Fälle, die du verlangt hast;
derselbe Mutant machte jeweils beide rot. Wenn du sie lieber behalten willst,
brauche ich dafür Luft im Budget.

**Suite:** 1019 Backend, 295 Plugin-API, 45 Beispiel, 292 Dashboard. Ruff sauber.
Fünf Mutanten beißen.
