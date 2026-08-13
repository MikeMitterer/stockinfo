# T-01 · Devisen-Tab (FxPanel) + `/fx`-Endpoint

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| root (backend + frontend) | done | erledigt | UI + API | — |

**Löst:** Verifiziert den neuen Devisen-Tab und den `/fx`-Endpoint (Commits
`1729bee`, `1850317`, `e64ca2b`): 1 base = rate quote, mit Kurszeit, Quelle und
`stale`-Kennzeichen; Validierung (422) und Nichtverfügbarkeit (502).

<!--
  Repo:   cross (backend app/routers/fx.py, frontend FxPanel.vue/useFx.ts)
  Scope:  UI + API (bewusst erweitert — Endpoint gehört zur Änderung)
-->

---

## Verify

Legende: ✅ live bestätigt · ⚠️ bestätigt mit Einschränkung (Fußnote) ·
◑ teilweise (Fußnote) · ➖ keine Live-Verifikation.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|-------|
| 1 | `#/fx` im Dashboard | Tab „Devisen" öffnet FxPanel mit zwei Code-Feldern (EUR/USD), ⇄-Button, „Umrechnen" | ✅¹ | ok    |
| 2 | FxPanel → „Umrechnen" (EUR→USD) | Zeigt „1 EUR = ~1.15 USD", Kurszeit, Quelle, Status-Badge **aktuell** | ⚠️² | ok    |
| 3 | FxPanel → ⇄-Button | Felder tauschen die Werte (EUR↔USD) | ✅³ | ok    |
| 4 | FxPanel → base=EUR quote=EUR | Rate genau `1.0`, Quelle `identity` | ✅⁴ | ok    |
| 5 | FxPanel → quote=ZZZ, „Umrechnen" | Rote Fehlerzeile „Wechselkurs konnte nicht geladen werden" (Backend 502) | ✅⁵ | ok    |
| 6 | `GET /fx?base=EU&quote=USD` | HTTP **422** (Währungscode muss 3 Buchstaben sein) | ✅⁶ | ok    |
| 7 | `GET /fx?base=usd&quote=eur` | Kleinbuchstaben werden akzeptiert, Antwort normalisiert auf `USD`/`EUR` | ✅⁷ | ok    |

> ¹ **(CC):** live im Browser (2026-08-13, `#/fx`, dark) — Panel „Devisen" mit EUR/⇄/USD/„Umrechnen" gerendert.
> ² **(CC):** live geklickt → „1 EUR = 1.1527377367019653 USD", Kurszeit + Quelle + Badge **aktuell** sichtbar. Einschränkung: Quelle zeigte `cache` (nicht `yfinance`), weil der Kurs durch einen vorherigen Aufruf bereits gecacht war — erwartetes CachedFxService-Verhalten, kein Fehler.
> ³ **(CC):** live geklickt → Felder wechselten von EUR/ZZZ zu ZZZ/EUR. Kehrwert (USD→EUR≈0.87) zusätzlich per curl bestätigt.
> ⁴ **(CC):** `curl -s "http://localhost:8000/fx?base=EUR&quote=EUR"` → `{…"rate":1.0,"source":"identity","stale":false}`.
> ⁵ **(CC):** live im Browser geklickt (EUR→ZZZ) → rote Zeile „Wechselkurs konnte nicht geladen werden"; Backend: `curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/fx?base=EUR&quote=ZZZ"` → `502`.
> ⁶ **(CC):** `curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/fx?base=EU&quote=USD"` → `422`.
> ⁷ **(CC):** `curl -s "http://localhost:8000/fx?base=usd&quote=eur"` → `{"base":"USD","quote":"EUR","rate":0.8675…}`.
>
> **Kurz-Testblock** (alle Backend-Checks dieses Tickets, kopierbar; Kommentar = Verify-Zeile):
> ```bash
> curl -s "http://localhost:8000/fx?base=EUR&quote=USD"                              # #2 Erfolgsfall
> curl -s "http://localhost:8000/fx?base=EUR&quote=EUR"                              # #4 identity → 1.0
> curl -s "http://localhost:8000/fx?base=usd&quote=eur"                              # #7 lowercase ok
> curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8000/fx?base=EU&quote=USD"   # #6 → 422
> curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8000/fx?base=EUR&quote=ZZZ"  # #5 → 502
> ```
>
> **⚑ Blocker gefunden & behoben (siehe [T-04](T-04-vite-proxy-fehlende-praefixe.md)):** Vor dem Fix reichte der Vite-Dev-Proxy `/fx` nicht ans Backend → jede Umrechnung endete in der Fehlerzeile. Erst nach dem Proxy-Fix laufen #1–#3, #5 grün.

---

## Details

### Kontext / Ziel
Neuer FastAPI-Endpoint `GET /fx?base=&quote=` liefert `FxRate`
(base, quote, rate, quote_time, source, cached, stale, fetched_at). Frontend:
Tab „Devisen" (`#/fx`) rendert `FxPanel.vue` über `useFx()`; identisches
stale/quote_time/source-Muster wie bei Kursen.

### Akzeptanzkriterien
- [x] Tab „Devisen" per Deep-Link `#/fx` erreichbar
- [x] Erfolgsfall zeigt Rate + Metadaten + korrektes Status-Badge
- [x] ⇄ tauscht Währungen; Kehrwert plausibel
- [x] Ungültiger Code → 422; unbekannte Währung → 502 → UI-Fehlerzeile

> Anzeige-Nachbesserungen (Nachkommastellen, Kurszeit-Umbruch) sind in **T-06**
> erfasst — sie ändern nichts an der hier verifizierten Funktion.

### Side-Effects
Neuer Endpoint, additiv. `FxRate` erbt bestehendes stale/quote_time-Kontrakt →
rückwärtskompatibel für Konsumenten. Keine Änderung an Kurs-Endpoints.

### Auflösung
UI-Tests 2026-08-13 durchgeführt (Claude in Chrome, `:5173`). #1–#7 grün.
**Voraussetzung war der Proxy-Fix in T-04** — ohne ihn schlug `/fx` im Dev still
fehl. Endpoint-Verhalten (422/502/identity/lowercase) unverändert korrekt.
