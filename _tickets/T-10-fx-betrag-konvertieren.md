# T-10 · Devisen: konkreten Betrag umrechnen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | backlog | ~1 h | UI (kein Backend nötig) | — |

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
|---|---|---|:--:|---|
| 1 | `#/fx` | Betragsfeld (Default 1); Ergebnis = Betrag × Rate, in Zielwährung | ➖ | |
| 2 | `#/fx` nach Umrechnen | Ergebnis lokalisiert (2 Nachkommastellen für Geldbetrag) | ➖ | |
| 3 | `#/fx` | Rate „1 base = x quote" bleibt zusätzlich sichtbar (Trennung Kurs/Betrag) | ➖ | |
| 4 | Betrag leer/ungültig | Kein Crash; sinnvoller Fallback (z.B. Betrag = 1) | ➖ | |

---

## Details

### Kontext / Ziel
`/fx` liefert bereits `rate` (+ quote_time/source/stale). Ein Betragsfeld im
Panel genügt: `Ergebnis = Betrag × rate`, in Zielwährung formatiert. **Kein
Backend-Change** — der Nutzer vermutete API-Bedarf, aber die Multiplikation
gehört ins Frontend (sonst steckte ein Devisen- **und** ein Betrags-Wert in
einem Feld, und man könnte veraltete Kurse nicht mehr auseinanderhalten — vgl.
Stufe-3-Skepsis in `docs/stockinfo-currency-request.md`).

### Offene Design-Fragen
- Betrag als eigenes Feld links neben Basiswährung, oder unter der Rate?
- Nachkommastellen für Geldbeträge: 2 (Standard) — Rate bleibt bei 3 (T-06).
- Soll der Betrag die Rate-Zeile ersetzen oder ergänzen? (Vorschlag: ergänzen.)

### Akzeptanzkriterien
- [ ] Betragsfeld (numerisch, Default 1)
- [ ] Ergebnis = Betrag × rate, in Zielwährung, lokalisiert (2 Nachkommastellen)
- [ ] Rate-Zeile bleibt sichtbar (Kurs ≠ Betrag)
- [ ] Defensiver Umgang mit leerem/ungültigem Betrag
- [ ] i18n DE + EN; kein Backend-Change

### Side-Effects
Reine UI-Erweiterung von `FxPanel.vue`. `useFx`/`/fx` unverändert.

### Auflösung
_(offen)_
