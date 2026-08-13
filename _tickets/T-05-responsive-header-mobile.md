# T-05 · Header/Navigation auf Mobile unbrauchbar (kein Responsive)

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | ready | ~2 h | UI (SCSS + evtl. Menü-Komponente) | — |

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

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Dashboard bei ~384 px Breite | Nav-Buttons überlappen **nicht** mehr das Logo | ➖ | |
| 2 | Mobile-Breite | Alle Tabs erreichbar (Hamburger/Menü oder Umbruch/Scroll) | ➖ | |
| 3 | Sprach-Umschalter (DE/EN) | Auf Mobile sichtbar und bedienbar | ➖ | |
| 4 | Desktop (≥1024 px) | Unveränderte, bestehende Header-Optik | ➖ | |

---

## Details

### Kontext / Ziel
`AppHeader.vue` ist ein reines Flex-Row-Layout ohne `@media`-Breakpoint; im
gesamten Dashboard existiert **keine einzige** Media Query
(`grep -r "@media" dashboard/src` → leer). Bei 7 Tabs + Sprachumschalter reißt
die Zeile auf schmalen Screens; die Nav überlappt das Logo (in Screenshots
sichtbar). Durch die zwei neuen Tabs (Börsen, Devisen) hat sich das verschärft.

### Akzeptanzkriterien
- [ ] Definierter Breakpoint, unterhalb dessen die Nav kollabiert
      (Hamburger-Menü oder horizontal scrollbare/umbrechende Tab-Leiste)
- [ ] Logo, Navigation und Sprachumschalter überlappen bei keiner Breite
- [ ] Desktop-Optik unverändert

### Side-Effects
Neuer responsiver Zustand; ggf. kleine Menü-Komponente. Keine API-Änderung.
i18n beachten (neue Labels wie „Menü" via vue-i18n, DE + EN).

### Auflösung
_(offen)_
