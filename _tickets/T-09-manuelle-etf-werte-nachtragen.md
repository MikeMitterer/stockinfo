# T-09 · Fehlende Asset-Kennzahlen händisch nachtragen (persistent)

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| root (backend + frontend + DB) + ux-foundation | in-review | ~1 Tag | Feature (DB + API + UI) | — |

**Löst:** Nutzer-Finding — für Assets, die **nicht** über extraETF/justETF laufen,
sollen fehlende Kennzahlen (TER, Volatilität, Thesaurierend) **manuell im UI**
eingetragen werden und **persistent in der DB** bleiben.

<!--
  Repo:   cross — DB-Schema, /instruments-Overrides-Endpoint, UI-Editor.
          Dazu ux-foundation: UxInlineNumber kann jetzt „nicht gesetzt".
  Scope:  Feature, mehrschichtig. Größer als ein UI-only-Ticket.
-->

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

**Voraussetzung:** Stack läuft — Backend `:8000`, Dashboard `:5173`.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Asset ohne ETF-Quelle im UI | Felder TER/Vola/Thesaurierend sind manuell editierbar | ✅ [^1] | |
| 2 | Nach Eingabe + Reload | Werte bleiben erhalten (aus DB gelesen, nicht überschrieben) | ✅ [^2] | |
| 3 | Nach Auto-Refresh der Kurse | Manuelle Werte werden **nicht** von leeren Provider-Daten überschrieben | ✅ [^3] | |
| 4 | DB | Neue Tabelle für manuelle Overrides vorhanden (Migration) | ✅ [^4] | |
| 5 | Asset **mit** Provider-Wert, manuell etwas anderes eintragen | Angezeigt bleibt der Provider-Wert; das Merkmal daneben nennt den eigenen Wert und erklärt den Vorrang | ✅ [^5] | |
| 6 | Feld leeren | Wert verschwindet („nicht gesetzt"), nicht „0 %" | ✅ [^6] | |
| 7 | Unsinn schicken (TER 101, Vola −1, Text) | Endpoint antwortet 422, nichts wird gespeichert | ✅ [^7] | |
| 8 | Mobil (< 768 px), Karte aufklappen | dieselben drei Werte sind auch dort editierbar | ✅ [^8] | |
| 9 | Tests + Typecheck, alle drei Repos | grün | ✅ [^9] | |

```bash
# #4 — Schema
sqlite3 "${DEV_LOCAL}/DevWeb/Production/StockInfo/data/stockinfo.db" \
  "SELECT name FROM sqlite_master WHERE type='table' AND name='instrument_overrides';"

# #1/#2 — schreiben und zurücklesen
curl -s -X PUT "http://localhost:8000/instruments/by-symbol/GOLD.SG/overrides" \
  -H 'Content-Type: application/json' -d '{"ter": 0.25}'
curl -s "http://localhost:8000/instruments/by-symbol/GOLD.SG/overrides"

# #7 — Validierung (erwartet: 422)
curl -s -o /dev/null -w "%{http_code}\n" -X PUT \
  "http://localhost:8000/instruments/by-symbol/GOLD.SG/overrides" \
  -H 'Content-Type: application/json' -d '{"ter": 101}'

# #6 — leeren (alle drei auf null → Zeile verschwindet)
curl -s -X PUT "http://localhost:8000/instruments/by-symbol/GOLD.SG/overrides" \
  -H 'Content-Type: application/json' -d '{}'

# #9
cd "${DEV_LOCAL}/DevWeb/Production/StockInfo" && .venv/bin/python -m pytest -q
cd dashboard && npx vitest run && npx vue-tsc -b --force
cd "${DEV_LOCAL}/DevWeb/Production/ux-foundation" && npx vitest run && npm run typecheck
cd "${DEV_LOCAL}/DevWeb/StockPortfolio" && npx vitest run && npx vue-tsc -b --force
```

[^1]: `GOLD.SG` (EUWAX Gold, keine justETF-Quelle) hatte keine TER. Klick in die
    Zelle öffnet das Feld, `0.25` + Enter → die Zeile zeigt „0,25 %" mit dem
    Merkmal „Von Hand eingetragen — die Quelle liefert für dieses Papier nichts."
[^2]: Nach `location.reload()` stand der Wert samt Merkmal unverändert da — er
    kommt also aus der DB, nicht aus dem Zustand der Seite.
[^3]: „Alle aktualisieren" gelaufen: Kurs 124,99 → 124,69 und Kurspunkte 6 → 7,
    also ein echter Refresh. Die manuelle TER blieb. Das ist der Zweck der
    getrennten Tabelle — ein Test hält es zusätzlich fest
    (`test_ein_kurs_update_ruehrt_die_manuellen_werte_nicht_an`).
[^4]: `instrument_overrides` mit `instrument_id, ter, volatility, accumulating,
    updated_at`. Angelegt über `CREATE TABLE IF NOT EXISTS` in `_SCHEMA` — auf
    einer bestehenden DB entstand sie beim ersten Start ohne Zutun.
[^5]: An `VGWL.DE` (Provider-TER 0,14 %) 0,90 % eingetragen. Angezeigt blieb
    0,14 %; das Merkmal sagt: „Von Hand eingetragen: 0,90 %. Angezeigt wird der
    Wert der Quelle — sie hat Vorrang. Die Eingabe bleibt gespeichert und greift
    wieder, sobald die Quelle nichts liefert."
[^6]: Über `:empty-value="null"` an `UxInlineNumber`. Der Zustand musste dafür
    ins Fundament — siehe Auflösung.
[^7]: Fünf Fälle als Parametrisierung im Test (`-1`, `101`, `-0.1`, `501`,
    `"viel"`), alle 422.
[^8]: Bei 375 px: Kartenliste statt Tabelle, Karte aufgeklappt, in den Details
    steht dasselbe Feld. Kein waagrechter Überhang (`scrollWidth − clientWidth`
    = 0).
[^9]: Backend 134 · Dashboard 155 · Fundament 102 · StockPortfolio 510, alle
    Typechecks sauber, `make check-themes` ohne Verstoß.

**Testdaten wieder entfernt:** Die beiden oben eingetragenen Werte (0,25 % bzw.
0,90 %) sind erfunden und wurden nach der Prüfung gelöscht — die DB enthält
keine Overrides mehr.

---

## Details

### Kontext / Ziel
Heute stammen ETF-Extras (TER, Vola, Thesaurierung, Provider …) aus justETF/
extraETF. Für Papiere ohne diese Quelle bleiben die Felder leer. Nutzer will sie
manuell pflegen — mit klarer Vorrang-Regel gegenüber (leeren) Provider-Daten.

### Entschieden (17.08.2026)

| Frage | Entscheidung |
|---|---|
| Vorrang | **Nur Lücken füllen — aber mit Hinweis.** Was die Quelle liefert, gewinnt; ein manueller Wert greift nur, solange sie nichts hat. Verdeckt sie eine Eingabe, sagt die Oberfläche das ausdrücklich und nennt den eigenen Wert. |
| Felder | **TER, Volatilität, Thesaurierend.** Kein Name, kein Typ, keine Währung. |
| Kennzeichnung | **Ja, dezent** — ein kleines Merkmal an der Zelle, dessen Text den Zustand ausschreibt. |

Die Begründung für „mit Hinweis" ist die Schwäche der reinen Lücken-Regel: Ohne
sie verschwände eine Eingabe in dem Moment, in dem die Quelle wieder etwas
liefert — und niemand könnte sagen, ob sie noch da ist.

### Akzeptanzkriterien
- [x] DB-Migration für manuelle Overrides
- [x] API: Update-Endpoint für die Felder (Validierung)
- [x] UI: Inline-Editor an den betroffenen Assets
- [x] Persistenz über Refresh hinweg garantiert (Vorrang-Regel definiert)
- [x] i18n DE + EN

### Side-Effects
Mehrschichtig (DB/API/UI). Refresh-Merge-Logik muss manuelle Werte respektieren
— sonst gehen Eingaben beim nächsten Kurs-Update verloren.

---

## Auflösung

### Eine eigene Tabelle, keine zusätzlichen Spalten

`instrument_overrides` steht neben `instruments`, nicht darin. Der Grund ist der
Hintergrund-Refresh: Er schreibt die Instrumentenzeile bei jeder Runde neu, und
für genau die Papiere, um die es hier geht, mit **leeren** ETF-Extras. Ein
manueller Wert in derselben Zeile wäre eine Upsert-Runde vom Verschwinden
entfernt. Getrennt kann der Refresh nichts überschreiben, was er nicht kennt.

`NULL` heißt „nicht gepflegt" — nicht „0" und nicht „nein". Sind alle drei Werte
leer, verschwindet die Zeile ganz; sonst sammelten sich Karteileichen ohne
Inhalt.

### Die Vorrang-Regel steht an genau einer Stelle

`apply_overrides()` in `services/quote_cache.py`. Bewusst **nicht** in SQL: Eine
Fachregel im Join steht dort, wo niemand sie sucht.

Die Antwort trägt beides — die wirksamen Werte in `ter`/`volatility`/
`accumulating`, die rohen Eingaben in `manual_*`, dazu zwei Listen:
`manual_fields` (hier kommt der Wert gerade von Hand) und `shadowed_fields`
(hier liegt eine Eingabe, die die Quelle überstimmt). Ohne die zweite Liste
ließe sich die Kennzeichnung nicht bauen.

Ein Fallstrick, den ein Test festhält: `accumulating` ist ein Wahrheitswert, und
`False` — „ausschüttend" — ist eine **Aussage**, keine Lücke. Geprüft wird
deshalb auf `None`, nicht auf Falschheit; sonst hätte „ausschüttend" nie Bestand
gehabt.

### „Nicht gesetzt" musste ins Fundament

`UxInlineNumber` kannte nur Zahlen: `value: number`, und ein geleertes Feld
übernahm bestenfalls einen zahligen Ersatzwert. Für eine TER, die niemand kennt,
gibt es aber keinen zahligen Ersatz — 0 % ist eine Behauptung.

Statt in StockInfo eine zweite Zahl-in-der-Zeile zu bauen (was der Skill
ausdrücklich verbietet), kann die Komponente jetzt `null`: als Wert und als
Leerwert. Rückwärtskompatibel — wer eine Zahl hereingibt, merkt nichts davon.

Dabei kam ein echter Fehler ans Licht: `props.emptyValue ?? Number.NaN` behandelt
`null` wie eine fehlende Angabe, das Leeren wäre also wirkungslos geblieben. Der
Vergleich läuft jetzt gegen `undefined`.

Die vier Aufrufstellen in StockPortfolio und die zwei im Schaufenster nehmen
`number | null` entgegen und verwerfen `null` — dort gibt es den Zustand nicht,
und still auf `0` zu fallen wäre genau der Datenverlust, den die Komponente
verhindern soll.

### Die Zelle

`ManualMetric.vue` zeigt den wirksamen Wert, macht ihn an Ort und Stelle
editierbar und trägt das Merkmal. Thesaurierend hat drei Zustände und schaltet
per Klick weiter (ja → nein → nicht gesetzt); ein Auswahlfeld je Zeile hätte die
Tabelle mit Rahmen überzogen. Der Titel nennt jeweils den nächsten Zustand,
sonst wäre es Raten.

Die Komponente **bleibt in der App**: Sie kennt `InstrumentSummary` und die
Namen der drei Kennzahlen, also ein Datenmodell, das nur StockInfo hat. Was
allgemein war, liegt im Fundament.

### Zwei Dinge, die dabei nebenbei auffielen

- **Die Prozentanzeige lief über `toFixed(2)`** und schrieb damit einen Punkt,
  auch wenn die Oberfläche deutsch war. Sie läuft jetzt über `n()` — Format und
  Sprache gehören zusammen. Ein Test hielt vorher „25.80" fest und hält jetzt
  „25,80".
- **Zwei Testklassen waren an feste Julitage gebunden** (`test_daily_history`),
  während der geprüfte Dienst sein Fenster ab *heute* rechnet. Sie bestanden
  genau so lange, bis der Kalender darüber hinweggelaufen war, und meldeten
  danach einen Fehler, den es im Code nicht gab. Die Testdaten laufen jetzt mit.

### Berührte Repos

| Repo | Was |
|---|---|
| `StockInfo` (backend) | `instrument_overrides`, Repository-Methoden, `apply_overrides()`, GET/PUT-Endpoint, 19 Tests |
| `StockInfo/dashboard` | `ManualMetric`, `useOverrides`, Tabelle und Karte, Test-Fixture an einer Stelle |
| `ux-foundation` | `UxInlineNumber` kann „nicht gesetzt" (+ 4 Tests) |
| `StockPortfolio` | vier Aufrufstellen auf die erweiterte Signatur gezogen |
