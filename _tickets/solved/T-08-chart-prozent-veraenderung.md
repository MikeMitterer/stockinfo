# T-08 · Kurs-Graph: %-Veränderung anzeigen (Zeitraum + Hover)

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | done | erledigt (vom Nutzer abgenommen) | UI | — |

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

| # | Where | Look for | AI | Human                                                        |
|---|---|---|:--:|--------------------------------------------------------------|
| 1 | Kurs-Chart (Asset auswählen) | Rechts sichtbar: %-Veränderung über den gewählten Zeitraum (erster→letzter Wert) | ✅¹ | ok, die rechte Achse mit Prozentwerten möchte ich auch sehen |
| 2 | Chart, Hover/Tap über Stützwert | Tooltip zeigt zusätzlich den Prozentwert (relativ zum Startwert) | ✅² | ok                                                           |
| 3 | Vorzeichen/Farbe | Positiv/negativ optisch unterscheidbar (Pfeil + Vorzeichen + Farbe) | ✅³ | ok                                                           |

> ¹ **(CC):** Zwei Anzeigen: (a) Header-Badge mit der Gesamtveränderung („▲ +0,66 %" / „▼ −7,24 %"), Pure-Funktion `periodChangePct`. (b) **Rechte Y-Achse** mit der %-Skala relativ zum Startwert (Human-Wunsch) — live (APC.DE, 1M): rechts „+5,9 % … 0 % … −9,3 %", die 0%-Linie liegt beim Startkurs; via `pctAxisBounds` an die Kursachse gekoppelt (gleiche Spanne). i18n-Titel `chart.periodChange`. utils-Tests 6, Suite 91/91.
> ² **(CC):** live Hover auf Endpunkt → Tooltip-Zeile „ggü. Start: +0,66 %" (relativ zum ersten Punkt, via `relChangePct`). i18n `chart.vsStart`. Funktioniert per Hover **und** Tap (Chart.js).
> ³ **(CC):** Pfeil (▲/▼/→) **plus** Vorzeichen (`signDisplay:'exceptZero'`) **plus** Farbe — Farbe nicht alleiniger Träger (ux-standards). Grün `$health-ok` / Rot `$health-down`, fix/semantisch (themeunabhängig). tabular-nums.

---

## Details

### Kontext / Ziel
Der Chart (`HistoryChart.vue`) zeigt Kurse als Serie `{x,y}`. Die
%-Veränderung ist aus der vorhandenen Serie berechenbar (Start-/Endwert bzw.
Punkt vs. Startwert) — kein neuer Endpoint nötig.

### Akzeptanzkriterien
- [x] Zeitraum-%-Änderung rechts am Chart (Badge im Header)
- [x] Hover/Tap-Tooltip je Stützwert mit Prozentwert (ggü. Start)
- [x] Positiv/negativ unterscheidbar (Pfeil + Vorzeichen + Farbe)
- [x] i18n DE + EN; Serie-basiert → gilt für Intraday **und** EOD-Ranges

### Side-Effects
Reine UI-Berechnung aus vorhandener Serie. Kein Backend-Change.

### Auflösung
`utils/changePct.ts` (`relChangePct`, `periodChangePct`, `pctAxisBounds`) + Test
(6 Fälle); `HistoryChart.vue`: %-Badge im Header (grün/rot, Pfeil+Vorzeichen),
Tooltip-Zeile „ggü. Start" **und rechte %-Achse** (an die Kursachse gekoppelt).
i18n `chart.periodChange`, `chart.vsStart` (de/en). Suite 91/91, Build grün.
Commit `1260294`, vom Nutzer abgenommen (2026-08-15).
