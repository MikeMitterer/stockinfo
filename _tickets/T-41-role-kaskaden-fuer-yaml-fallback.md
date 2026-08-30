# T-41 · Echte Rollen-Kaskaden für den YAML-Fallback

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo | wartet auf T-37 | 0,5–1 Tag | Quote, Daily und FX fragen ihre konfigurierte Reihenfolge wirklich ab | — |

- **Angelegt:** 2026-08-30
- **Hängt ab von:** T-37
- **Danach:** T-35 wiederholen
- **Design bestätigt:** Mike, 2026-08-30
- **Design:** `docs/superpowers/specs/2026-08-30-role-kaskaden-fuer-yaml-fallback-design.md`
- **Plan:** `docs/superpowers/plans/2026-08-30-role-kaskaden-fuer-yaml-fallback.md`

**Löst:** `sources.yaml` erlaubt für `quotes`, `daily` und `fx` bereits mehrere
Quellen, der Host verwendet dort aber nur die erste einsatzbereite Instanz.
Darum erreicht eine Anleihe ohne Online-Kurs das konfigurierte `yaml-file`
nicht. T-41 macht genau diese drei Reihenfolgen ausführbar.

## Scope-Vertrag

- **Fachliche Änderungen:** drei kleine, rollenspezifische Kaskadenregeln:
  Quote, Daily und FX.
- **Produktflächen:** `app/providers/composite_market.py`,
  `app/plugin_adapters.py`, `app/services/fx_service.py`, `app/container.py`.
- **Tests/Doku:** fokussierte Composite-/FX-/Container-Tests, Erweiterung der
  bestehenden YAML-Vertikale, aktive Plugin-/Quellen-Doku und dieses Ticket.
- **Budget:** höchstens 4 Produktdateien, 5 Test-/Dokudateien und 650 gesamte
  Diff-Zeilen. Browserbeleg steht im Ticket; kein neues Browser-Script.
- **Nicht-Ziele:** keine generische Kettenabstraktion, keine neue
  Konfiguration, keine Parallelität, Retries, Timeouts, Health-Scores,
  Cachetabellen oder Änderungen an Resolver-/Metadatenkaskaden und YAML-Schema.

Bei Überschreitung greift der bestehende Scope-Checkpoint-Riegel.

## Verify

Legende: ✅ live bestätigt · ⚠️ bestätigt mit Einschränkung · ◑ teilweise ·
➖ keine Live-Verifikation · `AI` nur KI · `Human` nur Mensch.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | Quote-Composite | erster gültiger Kurs gewinnt; Miss/Ausfall fällt weiter; nach Treffer kein weiterer Aufruf | | |
| **2** | Daily-Composite + Adapter | Non-Hit fällt weiter; gültige leere `DailySeries` stoppt als `[]`; nach Gesamtausfall kein Wasserzeichen | | |
| **3** | FX-Service | erster Kurs gewinnt; tatsächlicher Lieferant wird gespeichert und bleibt im Cache; stale erst nach Gesamtausfall | | |
| **4** | Container/REST | alle konfigurierten Quellen bleiben in Reihenfolge erhalten; Online-Überlappung gewinnt, YAML-Bond schließt die Lücke | | |
| **5** | Regression | gezielte Tests, vollständiges `make test`, Ruff, Diff-Check und YAML-Smoke 20/20 | | |
| **6** | Browser durch Claude | `BTC-EUR` online, Anleihe über YAML-History, `fund` nutzbar; Liste/Drilldown/Quelle korrekt; Konsole und Requests sauber | | |

## Übergaberegel

T-41 beginnt erst nach der Freigabe von T-37. Danach wird es vor T-35
implementiert und unabhängig von Codex geprüft. T-39 bleibt gemäß Mikes
Reihenfolge am Ende der Produktkette; T-40 bleibt die anschließende
Universalisierung des Regelwerks.

