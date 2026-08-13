# T-08 · Kurs-Graph: %-Veränderung anzeigen (Zeitraum + Hover)

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | backlog | ~2 h | UI | — |

**Löst:** Nutzer-Finding zum Kurs-Chart:
1. Rechts die **%-Veränderung über den gewählten Zeitraum** anzeigen.
2. Bei den Stützwerten (Datenpunkten) den **Prozentwert bei Hover** zeigen.

<!--
  Repo:   frontend (HistoryChart.vue)
  Scope:  UI — Chart-Anreicherung, keine neuen Backend-Daten nötig.
-->

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Kurs-Chart (Asset auswählen) | Rechts sichtbar: %-Veränderung über den gewählten Zeitraum (erster→letzter Wert) | ➖ | |
| 2 | Chart, Hover über Stützwert | Tooltip zeigt zusätzlich den Prozentwert (relativ zum Startwert) | ➖ | |
| 3 | Vorzeichen/Farbe | Positiv/negativ optisch unterscheidbar (grün/rot o.ä.) | ➖ | |

---

## Details

### Kontext / Ziel
Der Chart (`HistoryChart.vue`) zeigt Kurse als Serie `{x,y}`. Die
%-Veränderung ist aus der vorhandenen Serie berechenbar (Start-/Endwert bzw.
Punkt vs. Startwert) — kein neuer Endpoint nötig.

### Akzeptanzkriterien
- [ ] Zeitraum-%-Änderung rechts am Chart
- [ ] Hover-Tooltip je Stützwert mit Prozentwert
- [ ] Positiv/negativ farblich unterscheidbar
- [ ] i18n DE + EN; funktioniert für Intraday **und** EOD-Ranges

### Side-Effects
Reine UI-Berechnung aus vorhandener Serie. Kein Backend-Change.

### Auflösung
_(offen)_
