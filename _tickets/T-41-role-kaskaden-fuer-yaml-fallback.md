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
- **Budget:** nach Scope-Checkpoint 1 höchstens 4 Produktdateien, 8
  Test-/Dokudateien und 1.200 gesamte Diff-Zeilen. Browserbeleg steht im
  Ticket; kein neues Browser-Script.
- **Nicht-Ziele:** keine generische Kettenabstraktion, keine neue
  Konfiguration, keine Parallelität, Retries, Timeouts, Health-Scores,
  Cachetabellen oder Änderungen an Resolver-/Metadatenkaskaden und YAML-Schema.

Bei Überschreitung greift der bestehende Scope-Checkpoint-Riegel.

### Scope-Checkpoint 1 · `continue`

Codex-Entscheidung am 2026-08-30 gegen `115ac6c`: Das Produktinventar hält
mit vier Dateien exakt den bestätigten Entwurf. Die acht tatsächlichen
Test-/Dokudateien waren im freigegebenen Implementierungsplan bereits einzeln
genannt; der Scope-Vertrag hatte sie mit fünf lediglich falsch
zusammengezählt. Der Aufwuchs auf 1.131 gesamte Diff-Zeilen steckt überwiegend
in den vorab verlangten Rollen-, Container- und REST-Orakeln. Es ist keine
neue Schicht, Konfiguration oder unabhängig lieferbare Fachänderung
entstanden.

Das Budget wird deshalb einmalig auf **4 Produktdateien, 8
Test-/Dokudateien und 1.200 gesamte Diff-Zeilen** korrigiert. Der Produktstand
ist eingefroren; erlaubt ist nur noch die formale Neuübergabe desselben
Commits. Eine weitere Überschreitung führt zu `reduce` oder `split`.

### Review Runde 1 · Gewinner und Metadatenherkunft müssen dieselbe Quelle sein

Codex-Review gegen `115ac6c`, mit rein textueller Selbstheilung in `f742c9c`:
Reihenfolge, Fallthrough, Daily-Leerwert, FX-Herkunft und die REST-Kette sind
grün. Ein bestehender Quote-Vertrag bleibt jedoch offen. Liefert die erste
Kursquelle nichts und die zweite eine `RawQuote` mit Name, Gattung und Börse,
übernimmt der Core diese Metadaten, meldet in `quote.source` aber den Namen der
ersten Quelle. Die direkte Gegenprobe ergab Inhalt von `second` bei
`source="first"`.

Der Abschluss bleibt in den vorhandenen Quote-Composite-Dateien: Die Herkunft
des Gewinners muss für genau die verarbeitete Antwort kontextlokal und damit
nebenläufigkeitssicher sichtbar sein; eine gemeinsame veränderliche
„letzte Quelle" ist weiterhin verboten. Das bestehende Orakel „Composite-Name
ist immer die erste Quelle" wird durch einen öffentlichen `QuoteService`-Fall
ersetzt: erste Quelle `None`, zweite Quelle liefert Metadaten, Antwort nennt
die zweite. Keine neue Produktdatei, kein neuer öffentlicher Vertrag und keine
weitere Doku- oder Browserarbeit.

Codex hat außerdem die neu eingeführte Prozesschronik aus Codekommentaren,
Test-Docstrings und aktiver Versionsprosa mechanisch entfernt. 79 fokussierte
Tests, Ruff und Diff-Check blieben danach grün.

## Verify

Legende: ✅ live bestätigt · ⚠️ bestätigt mit Einschränkung · ◑ teilweise ·
➖ keine Live-Verifikation · `AI` nur KI · `Human` nur Mensch.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | Quote-Composite | erster gültiger Kurs gewinnt; Miss/Ausfall fällt weiter; nach Treffer kein weiterer Aufruf | ◑ [^review-r1] | |
| **2** | Daily-Composite + Adapter | Non-Hit fällt weiter; gültige leere `DailySeries` stoppt als `[]`; nach Gesamtausfall kein Wasserzeichen | ✅ | |
| **3** | FX-Service | erster Kurs gewinnt; tatsächlicher Lieferant wird gespeichert und bleibt im Cache; stale erst nach Gesamtausfall | ✅ | |
| **4** | Container/REST | alle konfigurierten Quellen bleiben in Reihenfolge erhalten; Online-Überlappung gewinnt, YAML-Bond schließt die Lücke | ◑ [^review-r1] | |
| **5** | Regression | gezielte Tests, vollständiges `make test`, Ruff, Diff-Check und YAML-Smoke 20/20 | ✅ | |
| **6** | Browser durch Claude | `BTC-EUR` online, Anleihe über YAML-History, `fund` nutzbar; Liste/Drilldown/Quelle korrekt; Konsole und Requests sauber | ✅ | |

[^review-r1]: Reihenfolge und Werte sind belegt. Offen ist die Herkunft einer
    zweiten Kursquelle, wenn gerade ihre `RawQuote` Metadaten zum Ergebnis
    beiträgt; Details stehen im Review-Abschnitt oberhalb der Matrix.

### Was gelaufen ist

**Zeilen 1–3** — `tests/test_composite_market.py` (11 Orakel, Aufrufzähler an
jedem Double) und `tests/test_fx_service.py` (6 neue Kaskadenfälle, darunter
`test_die_herkunft_der_zweiten_quelle_ueberlebt_den_cache`).

**Zeile 4** — `tests/test_container.py` misst die Kette an der Wurzel
(`_market_chain("quotes")` gibt beide Namen in Reihenfolge), und
`tests/test_yaml_profile.py` prüft dieselbe Zusage durch den REST-Eintritt:
Überlappung an die vordere Quelle (999,0 statt 128,21), Lücke an die Datei
(99,42), Tagesreihe an die Datei (99,18 / 99,31 / 99,42), `/fx` nennt
`yaml-file` als Lieferanten.

**Gegenprobe statt grünem Lauf.** Mit `return sources[:1]` — also der alten
`_first`-Verdrahtung — fallen genau diese vier Orakel um und sonst keines.
Ohne diese Probe wäre nicht belegt, dass sie die Kaskade prüfen und nicht
bloß den Normalfall.

**Zeile 5** —

```
.venv/bin/ruff check app tests plugin_api/src plugin_api/tests plugin_api/examples   → All checks passed
make test        → 944 Backend + 295 plugin_api + 269 Frontend, alle grün
PROFILE=yaml ./_tickets/T-35-smoke.sh --run                                          → 20/20
git diff --check → sauber
```

**Zeile 6 — der Browserlauf**, Online-Profil mit `yaml-file` als letztem Glied
in `resolvers`, `quotes`, `daily` und `fx`:

| Papier | Kurs | Wer hat geliefert |
|---|---|---|
| `BTC-EUR` | 68.095,81 EUR | yfinance — die Datei nennt 94.500,00 und hat verloren |
| `DE0001102531` | 99,42 EUR | die Datei (jüngster Schlusskurs), online kennt kein Papier mit Kurs |
| `DE0009848119` → `HJUA.F` | 175,61 EUR | yfinance — die Datei nennt 142,50 und hat verloren |
| `/fx` CAD→EUR | 0,6204 | yfinance — die Datei nennt 0,6412 und hat verloren |

Die Tagesreihe der Anleihe kam mit allen drei gepflegten Punkten. Konsole
leer, alle 21 Requests 200.

**Ein Befund aus dem Lauf, der in die Doku gewandert ist.** Mit `yaml-file`
nur in den Marktrollen scheitert die Anleihe schon an der **Aufnahme**: „Zu
DE0001102531 hat keine der eingerichteten Quellen ein Wertpapier gefunden."
Die Kaskade hilft beim Kurs erst, wenn das Papier überhaupt aufgelöst wird —
die Datei gehört also auch in `resolvers`. `docs/plugins.md` und
`docs/sources.yaml.example` sagen das jetzt.

**Nicht in T-41 geändert:** Der Drilldown nennt die Anleihe weiterhin „eine
Aktie" (`dashboard/src/i18n/de.ts`). Der Befund steht seit T-35 dort und
gehört nicht in dieses Ticket.

## Übergaberegel

T-41 beginnt erst nach der Freigabe von T-37. Danach wird es vor T-35
implementiert und unabhängig von Codex geprüft. T-39 bleibt gemäß Mikes
Reihenfolge am Ende der Produktkette; T-40 bleibt die anschließende
Universalisierung des Regelwerks.
