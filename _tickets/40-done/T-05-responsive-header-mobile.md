# T-05 · Header/Navigation auf Mobile unbrauchbar (kein Responsive)

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | done | erledigt (vom Nutzer abgenommen) | UI (SCSS + AppHeader) | — |

**Löst:** Nutzer-Finding „UI funktioniert auf Mobile überhaupt nicht, Menü ist
nicht mehr zu sehen". Ursache: Der Header hat **keine** responsive Behandlung.

<!--
  Repo:   frontend (dashboard/src/components/AppHeader.vue, styles/)
  Scope:  UI — Layout/Responsive.
-->

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human                                                              |
|---|---|---|:--:|--------------------------------------------------------------------|
| 1 | Schmale Breite (< 1024px) | Nav-Buttons überlappen **nicht** mehr das Logo (☰ ersetzt die Tab-Zeile) | ⚠️¹ | OK, aber API+Links bricht beim verkleinern der Seite um - nicht OK |
| 2 | Schmale Breite | Alle 7 Tabs über ☰-Drawer erreichbar; Tab-Klick navigiert **und** schließt; Escape schließt | ✅² | ok                                                                 |
| 3 | Sprach-Umschalter (DE/EN) | Bei schmaler Breite in der Kopfzeile sichtbar/bedienbar | ✅³ | ok                                                                 |
| 4 | Desktop (≥1024 px) | Unveränderte, bestehende Header-Optik | ✅⁴ | ok                                                                 |

> ¹ **(CC):** **Human-Fund (zu Recht „nicht OK"):** „API & Links" brach im Band knapp über dem Breakpoint um. Ursache gemessen: die volle 7-Tab-Zeile braucht **~1094px** (EN: nav 765 + Logo 190 + Sprache 75 + Gaps/Padding) — über dem alten 1024er-Breakpoint, daher Stauchung/Umbruch zwischen 1024 und 1094px. **Fix:** Breakpoint auf **1280px** (Tailwind `xl`, klärt 1094 mit Reserve) + `white-space: nowrap` an den Tab-Labels. Live bestätigt: kompilierte Regel `(max-width: 1280px)`, Tabs `nowrap`; Tests 81/81. → **wartet auf deine erneute Verifikation** (Fenster von breit auf schmal ziehen — kein Umbruch mehr, ☰ ab <1280px).
> ² **(CC):** live (echter 384px-Viewport, DevTools-Mobilansicht) — ☰ **links** (Konvention, `order:-1`), Logo mittig, DE/EN rechts; ☰ öffnet den Drawer mit allen 7 Tabs; Tab-Klick navigiert **und** schließt; Escape/Backdrop schließen. 3 Unit-Tests grün.
> ³ **(CC):** DE/EN bei schmaler Darstellung in der Kopfzeile sichtbar; Umschalten grundsätzlich funktionsfähig (in T-06 live bedient).
> ⁴ **(CC):** echter Breitviewport — volle 7-Tab-Zeile, **kein** ☰, keine Überlappung; Desktop-CSS unverändert (Reviewer bestätigt).

---

## Details

### Kontext / Ziel
`AppHeader.vue` ist ein reines Flex-Row-Layout ohne `@media`-Breakpoint; im
gesamten Dashboard existiert **keine einzige** Media Query
(`grep -r "@media" dashboard/src` → leer). Bei 7 Tabs + Sprachumschalter reißt
die Zeile auf schmalen Screens; die Nav überlappt das Logo (in Screenshots
sichtbar). Durch die zwei neuen Tabs (Börsen, Devisen) hat sich das verschärft.

### Akzeptanzkriterien
- [x] Breakpoint `$header-bp: 1280px` (Tailwind `xl`), darunter Hamburger-Drawer — klärt die ~1094px breite Tab-Zeile
- [x] Logo, Navigation und Sprachumschalter überlappen bei keiner Breite; kein Label-Umbruch (`white-space: nowrap`)
- [x] ☰ links (Drawer-Konvention), Sprache rechts
- [x] Desktop-Optik unverändert (≥1280px)
- [x] i18n: neuer Key `nav.menu` (DE „Menü", EN „Menu")

### Side-Effects
Nur `AppHeader.vue` + ein i18n-Key + Breakpoint-Variable. Keine API-Änderung,
keine anderen Komponenten. Escape-Listener am `window` (in onMounted/onUnmounted).

### Auflösung
Umgesetzt auf Branch `feat/responsive-header`, Commit `f5037d8`
(`feat(dashboard): Header-Navigation mobil als Hamburger-Drawer`). Subagent-driven:
Task-Review Spec ✅/Approved, 3 Unit-Tests (Toggle/Navigate+Close/Escape),
Suite 81/81 + Build grün. UI verifiziert (Desktop real; Schmal via CSSOM-Trigger
der echten Media-Regel, da Session-Viewport auf 1592px fixiert). 1 deferred
minor: Spec-Tests rufen kein `unmount()` (Listener-Leak, harmlos).

**Nachbesserung (Human-Verifikation):** Breakpoint 1024→1280px (Tab-Zeile misst
~1094px) + `white-space: nowrap`, ☰ nach links (`order:-1`). Am echten 384px-
Viewport verifiziert, Tests 81/81. Vom Nutzer abgenommen (2026-08-14).
