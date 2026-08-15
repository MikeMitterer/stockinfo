# T-11c · Assets-Tabelle mobil → Kartenliste

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | backlog | ~3 h | UI-only | — |

**Löst:** `InstrumentsTable.vue` (> 4 Spalten) unter `md` (768 px) je Zeile eine
**Karte** mit den 2–3 wichtigsten Werten + Status; Umschaltung via Composable
`useIsCompact` (matchMedia), nicht via verstreutem CSS. Teil-Ticket von **T-11**
(Punkt 4).

<!-- Repo: frontend (dashboard/). Status: backlog. Scope: UI-only. -->

---

## Verify

Legende: ✅ live · ⚠️ Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | `http://localhost:5173/` < 768 px | Assets als **Kartenliste**, kein waagrechtes Tabellen-Scrollen (`scrollWidth − clientWidth = 0`) | ➖ | |
| 2 | ≥ 768 px | volle Tabelle wie bisher | ➖ | |
| 3 | Code | neues Composable `useIsCompact` (matchMedia), keine verstreuten CSS-Breakpoints | ➖ | |
| 4 | Karte antippen (< 768 px) | öffnet den Kurs-Graph im Dock — wie am Desktop | ➖ | |
| 5 | Karte aufklappen | zeigt ISIN, TER, Vola, Thes., Pkt.; Aufklappen löst **kein** Auswählen aus | ➖ | |
| 6 | Kartenliste, alle Knöpfe | Trefferflächen ≥ **44 × 44 px** (messen, nicht schätzen) | ➖ | |
| 7 | Sortierleiste (< 768 px) | Auswahl + Richtungsknopf ändern die Reihenfolge — Sortieren geht mobil weiterhin | ➖ | |
| 8 | ISIN fehlt, Karte aufklappen | „+ ISIN" funktioniert auch mobil (`IsinEditor`) | ➖ | |
| 9 | Dock offen bei 375 × 812 | Karten bleiben erreichbar; Dock verdeckt sie nicht dauerhaft (Höhe messen — Richtwert: Dock ~300 px = ⅓ des Bildes) | ➖ | |

---

## Details

### Kontext / Ziel
Gap-Analyse-Punkt 4 aus **T-11**. Header ist mit T-05 bereits mobil; die Tabelle
noch nicht.

### Akzeptanzkriterien
- [ ] Kartenliste < md, Tabelle ≥ md
- [ ] `useIsCompact`-Composable steuert die Umschaltung
- [ ] Wichtigste Werte + Status je Karte sichtbar

### Side-Effects
Kein Backend-Change.

### Auflösung
_(offen)_
