# T-04 · Vite-Dev-Proxy: `/exchanges`, `/fx`, `/analyze` fehlten

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | done | erledigt | Config | — |

**Löst:** Bug beim Testen gefunden — die neuen Endpoints wurden im Dev-Proxy
nicht ans Backend weitergereicht, dadurch waren **Börsen-, Devisen- und
Analyse-Tab** im Dev funktionslos. (Nutzer-Meldung: „Börsen werden nicht
angezeigt", „Analyse funktioniert nicht", „Devisenumrechnung funktioniert nicht".)

<!--
  Repo:   frontend (dashboard/vite.config.ts)
  Scope:  Config — Dev-only, betrifft NICHT das Docker-Image (dort ein Server).
-->

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human                                                |
|---|---|---|:--:|------------------------------------------------------|
| 1 | `curl :5173/exchanges` | Liefert **JSON** (nicht `<!doctype html>`) | ✅¹ | curl-Commands!                                       |
| 2 | `curl :5173/fx?base=EUR&quote=USD` | Liefert JSON mit `rate` | ✅² |                                                      |
| 3 | `curl :5173/analyze?symbol=EUNL.DE` | Liefert JSON mit `stages` | ✅³ |                                                      |
| 4 | Browser `#/exchanges` | Börsen-Tabelle rendert; Network `/exchanges` = 200 | ✅⁴ | Dieser Test war schon bei einem anderen Ticket dabei |
| 5 | Browser-Konsole nach Reload | **Kein** `SyntaxError: Unexpected token '<'` mehr | ✅⁵ | ok                                                   |

> ¹ **(CC):** `curl -s "http://localhost:5173/exchanges"` (2026-08-13) → `{"default_exchange":"XETR",…}` (JSON, nicht HTML).
> ² **(CC):** `curl -s "http://localhost:5173/fx?base=EUR&quote=USD"` → `{…"rate":1.1527…}`.
> ³ **(CC):** `curl -s "http://localhost:5173/analyze?symbol=EUNL.DE"` → `{…"stages":[…]}`.
> ⁴ **(CC):** Börsen-Panel im Browser gerendert, Network-Eintrag `/exchanges` 200. **Human-Hinweis:** deckt sich mit T-02 #1 — hier bewusst redundant als direkter Proxy-Beleg; für die Abnahme genügt der T-02-Test.
> ⁵ **(CC):** vor Fix Konsole-Error bei jedem Load; nach Proxy-Restart kein neuer Error.
>
> **Kern-Test — Proxy liefert JSON statt HTML** (kopierbar; Kommentar = Verify-Zeile):
> ```bash
> # Vor dem Fix: '<!doctype html>' — nach dem Fix: JSON mit den erwarteten Feldern
> curl -s "http://localhost:5173/exchanges"             | head -c 80; echo   # #1 JSON statt HTML
> curl -s "http://localhost:5173/fx?base=EUR&quote=USD" | head -c 80; echo   # #2 JSON mit rate
> curl -s "http://localhost:5173/analyze?symbol=EUNL.DE" | head -c 80; echo  # #3 JSON mit stages
> ```
> Gegenprobe direkt am Backend (`:8000`) zeigt dieselben Daten — der Unterschied lag allein am Proxy auf `:5173`.

---

## Details

### Kontext / Ziel
`dashboard/vite.config.ts` proxyt nur eine feste Präfix-Liste ans Backend
(`:8000`). Die in den letzten Commits ergänzten Endpoints `/exchanges`, `/fx`,
`/analyze` fehlten dort → Vite lieferte für diese Pfade das SPA-`index.html`,
der Client scheiterte am JSON-Parse und ließ die Panels leer/fehlerhaft.

### Fix
`apiPrefixes` um `/exchanges`, `/fx`, `/analyze` erweitert; Dashboard-Prozess
neu gestartet (`overmind restart dashboard`), damit Vite die Proxy-Config lädt.

### Side-Effects
Keine. Reiner Dev-Proxy; Produktion (Docker, ein Server) war nie betroffen.

### Nachgelagerte Robustheit (siehe QUESTIONS/GitHub)
Ein fehlgeschlagener `/exchanges`-Load erscheint **nicht** im ErrorBanner
(`exchanges` fehlt in `errorSources` in `App.vue`) — dadurch war der Ausfall
stumm. Kandidat für einen separaten Fix.

### Auflösung
`dashboard/vite.config.ts` — `apiPrefixes` erweitert (noch nicht committet).
UI-Tests der abhängigen Tickets T-01/T-02 laufen seither grün.
