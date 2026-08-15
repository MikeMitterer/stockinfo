# T-10 · Devisen: konkreten Betrag umrechnen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | done | erledigt (vom Nutzer abgenommen) | UI (kein Backend nötig) | — |

**Löst:** Nutzer-Idee — statt nur der Rate „1 base = x quote" soll man einen
**konkreten Betrag** eingeben und das Ergebnis sehen (z.B. 250 EUR → 288,25 USD).

<!--
  Repo:   frontend (FxPanel.vue)
  Scope:  UI. Backend NICHT nötig — /fx liefert die Rate, Ergebnis = Betrag × Rate.
-->

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|-------|
| 1 | `#/fx` | Betragsfeld (Default 1); Ergebnis = Betrag × Rate, in Zielwährung | ✅¹ | ok    |
| 2 | `#/fx` nach Umrechnen | Ergebnis lokalisiert (2 Nachkommastellen für Geldbetrag) | ✅¹ | ok    |
| 3 | `#/fx` | Rate „1 base = x quote" bleibt zusätzlich sichtbar (Trennung Kurs/Betrag) | ✅² | ok    |
| 4 | Betrag leer/ungültig | Kein Crash; sinnvoller Fallback (Betrag = 1) | ✅³ | ok    |

> ¹ **(CC):** live (`#/fx`, DE) — Betrag 250 → prominent „250 EUR = 289,32 USD" (Betrag × **präziser** `result.rate`, 2 Nachkommastellen). Betragsfeld Default 1. Reaktiv: Betrag ändern rechnet ohne erneuten Abruf neu.
> ² **(CC):** Darunter sekundär (muted) „1 EUR = 1,157 USD" — die 3-stellige Rate bleibt getrennt vom Betrag sichtbar.
> ³ **(CC):** Unit-Test — leerer Betrag → Fallback 1 (`Number('')` ist 0, daher leerer String separat abgefangen; `String()`-Wrap gegen number-Input). Suite 89/89.

---

## Details

### Kontext / Ziel
`/fx` liefert bereits `rate` (+ quote_time/source/stale). Ein Betragsfeld im
Panel genügt: `Ergebnis = Betrag × rate`, in Zielwährung formatiert. **Kein
Backend-Change** — der Nutzer vermutete API-Bedarf, aber die Multiplikation
gehört ins Frontend (sonst steckte ein Devisen- **und** ein Betrags-Wert in
einem Feld, und man könnte veraltete Kurse nicht mehr auseinanderhalten — vgl.
Stufe-3-Skepsis in `docs/stockinfo-currency-request.md`).

### Design-Entscheidungen (umgesetzt)
- Betragsfeld **links neben** der Basiswährung (in der Controls-Zeile).
- Geldbetrag mit **2** Nachkommastellen; Rate-Zeile bleibt bei 3 (T-06).
- Betrag **ergänzt** die Rate-Zeile (ersetzt sie nicht): oben prominent der
  umgerechnete Betrag, darunter sekundär die Einheiten-Rate.

### Akzeptanzkriterien
- [x] Betragsfeld (numerisch, Default 1)
- [x] Ergebnis = Betrag × rate, in Zielwährung, lokalisiert (2 Nachkommastellen)
- [x] Rate-Zeile bleibt sichtbar (Kurs ≠ Betrag)
- [x] Defensiver Umgang mit leerem/ungültigem Betrag (Fallback 1)
- [x] i18n DE + EN (`fx.amount`); kein Backend-Change

### Side-Effects
Reine UI-Erweiterung von `FxPanel.vue`. `useFx`/`/fx` unverändert.

### Auflösung
`FxPanel.vue`: Betragsfeld + `amountNum`/`convertedText`-Computeds (reaktiv,
ohne Re-Fetch); prominente Betrags-Zeile + sekundäre Rate-Zeile; i18n
`fx.amount` (de/en). 2 neue FxPanel-Tests (Umrechnung + Fallback). Suite
91/91, Build grün. Commit `781b699`, vom Nutzer abgenommen (2026-08-15).
