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
| 1 | `http://localhost:5173/` < 768 px | Assets als **Kartenliste**, kein waagrechtes Tabellen-Scrollen (`scrollWidth − clientWidth = 0`) | ✅¹ | |
| 2 | ≥ 768 px | volle Tabelle wie bisher | ✅² | |
| 3 | Code | neues Composable `useIsCompact` (matchMedia), keine verstreuten CSS-Breakpoints | ✅³ | |
| 4 | Karte antippen (< 768 px) | öffnet den Kurs-Graph im Dock — wie am Desktop | ✅⁴ | |
| 5 | Karte aufklappen | zeigt ISIN, TER, Vola, Thes., Pkt.; Aufklappen löst **kein** Auswählen aus | ✅⁵ | |
| 6 | Kartenliste, alle Knöpfe | Trefferflächen ≥ **44 × 44 px** (messen, nicht schätzen) | ✅⁶ | |
| 7 | Sortierleiste (< 768 px) | Auswahl + Richtungsknopf ändern die Reihenfolge — Sortieren geht mobil weiterhin | ✅⁷ | |
| 8 | ISIN fehlt, Karte aufklappen | „+ ISIN" funktioniert auch mobil (`IsinEditor`) | ➖⁸ | |
| 9 | Dock offen bei 375 × 812 | Karten bleiben erreichbar; Dock verdeckt sie nicht dauerhaft | ✅⁹ | |
| 10 | Chart-Dock < 768 px | alle sechs Zeitraum-Knöpfe **vollständig sichtbar**, nichts abgeschnitten | ✅¹⁰ | |
| 11 | Zeitraum-Knöpfe + Schließen im Dock | Trefferflächen ≥ 44 × 44 px | ⏳ | |
| 12 | Sortierzeile | steht in **einer** Zeile mit „Assets", rechtsbündig, ohne Formularkasten | ✅¹¹ | |

**Messweise:** Chrome lässt sich auf macOS nicht unter ~600 px verkleinern (der
Resize-Aufruf meldete zweimal fälschlich Erfolg). Gemessen wurde daher in einem
**375 px breiten iframe** auf derselben Seite — darin gilt echte Viewport-Breite
samt `matchMedia`. Ersetzt keinen Test auf einem echten Gerät.

> ¹ **(CC):** 371 px Viewport: 5 Karten, `table` nicht im Dokument,
> `scrollWidth − clientWidth = 0`.
> ² **(CC):** ab 768 px rendert die Tabelle, `.icard` 0× vorhanden.
> ³ **(CC):** `useIsCompact` fragt `(max-width: 767.98px)` ab — der Wert steht
> genau einmal im Code; 4 Unit-Tests (Anfangszustand, Wechsel, Abmeldung).
> ⁴ **(CC):** Antippen der Karte öffnet das Dock, Karte wird als ausgewählt markiert.
> ⁵ **(CC):** aufgeklappt „ISIN US0378331005 TER — Vola 25.80 % Thes. — Pkt. 2";
> `aria-expanded` schaltet `false`→`true`; **kein** `select`-Ereignis dabei.
> ⁶ **(CC):** 26 von 26 Elementen (Karten-Knöpfe, Links, Sortierzeile) ≥ 44 px.
> Anfangs lief die Karten-Fußzeile über (318 px nötig, 265 verfügbar) — behoben
> durch Umbruch, **nicht** durch Verkleinern der Trefferflächen.
> ⁷ **(CC):** nach Kurs aufsteigend GOLD.SG → BRYN.DE korrekt, Richtungsknopf
> kehrt exakt um; Auswahl persistiert (`{"key":"latest_price","dir":"asc"}`),
> Platzhalter „Ohne Sortierung" entfernt den Eintrag wieder; Schriftgröße 16 px
> (verhindert iOS-Zoom beim Antippen).
> ⁸ **(CC):** ➖ nicht live geprüft — alle fünf Testpapiere haben eine ISIN, der
> Fall tritt nicht auf. Durch 5 Unit-Tests des `IsinEditor` abgedeckt
> (Öffnen, gültig, ungültig, Kleinschreibung). **Für den Menschen:** ein Papier
> ohne ISIN anlegen und den Weg auf dem Telefon durchgehen.
> ⁹ **(CC):** Dock 307 px bei 808 px Höhe (38 %), Inhalt bekommt 386 px Polster,
> alle Karten bleiben erreichbar.
> ¹⁰ **(CC):** vorher ragte „Max" 13 px über den Rand und wurde **abgeschnitten**
> — tückisch, weil das Dock fixiert positioniert ist und die Überlaufprüfung
> trotzdem 0 meldete. Nach dem Fix: 1T 24–61 · 1W 63–105 · 1M 107–147 ·
> 3M 149–189 · 1J 191–228 · Max 230–277, Schließen bei 321 — alles innerhalb 371 px.
> ¹¹ **(CC):** „Assets" 39–90, Sortierung 215–332, vertikaler Versatz 3 px =
> eine Zeile. Trefferfläche 44 px bei 28 px sichtbarer Höhe. Erste Karte rückt
> von 285 auf 229 px hoch.

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
