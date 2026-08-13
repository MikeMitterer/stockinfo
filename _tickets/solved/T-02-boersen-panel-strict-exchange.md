# T-02 · Börsen-Panel datengetrieben + `strict_exchange` sichtbar

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| root (backend + frontend) | done | erledigt | UI + API | — |

**Löst:** Verifiziert, dass das Börsen-Panel (`#/exchanges`) seine Zeilen aus
`GET /exchanges` zieht (eine Quelle der Wahrheit) und `strict_exchange` im
Environment-Tab sichtbar ist (Commits `e761368`, `0745a4a`, `e64ca2b`).

<!--
  Repo:   cross (backend app/routers/dashboard.py /exchanges + /env, frontend ExchangesPanel.vue/EnvironmentPanel.vue)
  Scope:  UI + API
-->

---

## Verify

Legende: ✅ live bestätigt · ⚠️ bestätigt mit Einschränkung (Fußnote) ·
◑ teilweise (Fußnote) · ➖ keine Live-Verifikation.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human                                                                         |
|---|---|---|:--:|-------------------------------------------------------------------------------|
| 1 | `#/exchanges` im Dashboard | Tabelle „Börsen-Suffixe" mit Spalten Suffix / Börse / Region / Währung | ✅¹ | ok                                                                            |
| 2 | Börsen-Panel, Zeile Xetra (`.DE`) | Als **Standard** markiert (Badge), Zeile hervorgehoben — passt zu `default_exchange:"XETR"` | ✅² | ok, nirgends eine Info wie das Environment gesetzt wird                       |
| 3 | Börsen-Panel, Zeile London (`.L`) | Währung `GBp` **plus** Warn-Badge „oft Pence (1/100 GBP)!" | ✅³ | ok                                                                            |
| 4 | Börsen-Panel, Zeile NYSE/NASDAQ | Suffix-Spalte zeigt „(ohne)"-Platzhalter (leerer Suffix) | ✅⁴ | ok                                                                            |
| 5 | `GET /exchanges` | Liefert `default_exchange` + `exchanges[]` mit mic/suffix/name/region/currency | ✅⁵ | wahrscheinlich OK - für solche Tests brauche ich immer das kpl. curl-Command. |
| 6 | `#/environment`, Feld „Strikte Börse" | Zeigt Ja/Nein aus `strict_exchange` (Default: nein) | ✅⁶ | OK - siehe 5                                                                  |
| 7 | `GET /env` | Enthält `strict_exchange` (bool) | ✅⁷ | ??? - siehe 5                                                                 |

> ¹ **(CC):** live im Browser (2026-08-13, `#/exchanges`) — vollständige Tabelle gerendert, `/exchanges`-Request = HTTP 200 (Network).
> ² **(CC):** Zeile `.DE`/Xetra trägt Badge **„Standard"** und ist farblich hervorgehoben (read_page ref_50–54).
> ³ **(CC):** Zeile `.L`/London LSE → Währung `GBp` + Badge „oft Pence (1/100 GBP)!" (read_page ref_58–61).
> ⁴ **(CC):** Zeile NYSE/NASDAQ → Suffix-Zelle zeigt Platzhalter „(ohne)" (read_page ref_31).
> ⁵ **(CC):** `curl -s "http://localhost:8000/exchanges"` → `default_exchange:"XETR"`, u.a. `XETR/.DE/EUR`, `XLON/.L/GBp`, `US/""/USD`.
> ⁶ **(CC):** live im Browser (`#/environment`) — Feld „Strikte Börse: nein", „Default-Börse: XETR" (read_page ref_35–36, 33–34).
> ⁷ **(CC):** `curl -s "http://localhost:8000/env"` → enthält `"strict_exchange":false` und `"default_exchange":"XETR"`.
>
> **Kurz-Testblock** (kopierbar; Kommentar = Verify-Zeile):
> ```bash
> curl -s "http://localhost:8000/exchanges" | python3 -m json.tool   # #5 Börsenliste + default_exchange
> curl -s "http://localhost:8000/env"       | python3 -m json.tool   # #7 strict_exchange + default_exchange
> ```
>
> **Zu Human #2 („nirgends Info, wie das Environment gesetzt wird"):** Behoben —
> `DEFAULT_EXCHANGE` und `STRICT_EXCHANGE` sind jetzt in `.env.example`
> (Abschnitt „ISIN-Auflösung") mit Kurzkommentar dokumentiert. Werte für
> `DEFAULT_EXCHANGE` = MIC-Codes aus `/exchanges`.
>
> **⚑ Blocker gefunden & behoben (siehe [T-04](T-04-vite-proxy-fehlende-praefixe.md)):** Vor dem Fix reichte der Vite-Dev-Proxy `/exchanges` nicht ans Backend → Panel blieb **stumm leer** (kein Fehler-Banner). Das war der vom Nutzer gemeldete „Börsen werden nicht angezeigt"-Effekt.

---

## Details

### Kontext / Ziel
`GET /exchanges` ist die einzige Quelle der Börsen-Liste; das Panel rendert nur
noch, was der Endpoint liefert (keine hartkodierte Frontend-Liste mehr).
`default_exchange` steuert die Hervorhebung; `GBp`-Zeilen bekommen die
Pence-Warnung. `strict_exchange` (nur Default-Börse, sonst 404 statt Fallback)
ist im Environment-Tab als Ja/Nein sichtbar.

### Akzeptanzkriterien
- [x] Panel-Zeilen stammmen 1:1 aus `/exchanges`
- [x] Default-Börse hervorgehoben; GBp-Warnung vorhanden
- [x] `strict_exchange` im Environment-Tab lesbar
- [x] Setzen des Environments dokumentiert (`.env.example`)

### Side-Effects
Frontend-Börsenliste entfällt zugunsten des Endpoints → Panel folgt künftig
Backend-Änderungen automatisch. Additive Anzeige im Environment-Tab.

### Auflösung
UI-Tests 2026-08-13 durchgeführt (Claude in Chrome, `:5173`). #1–#7 grün —
**nach** dem Proxy-Fix aus T-04. Panel ist rein datengetrieben aus `/exchanges`.
Nebenbefund (Robustheit): Ein fehlgeschlagener `/exchanges`-Load wird nicht im
ErrorBanner angezeigt (`exchanges` fehlt in `errorSources` in `App.vue`) → das
maskierte den Bug. Siehe QUESTIONS.md.
