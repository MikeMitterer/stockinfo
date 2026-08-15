# T-11a · Navigation entrümpeln + Einstellungsseite

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | in-progress | ~4 h | UI-Architektur | — |

**Löst:** Hauptmenü von 7 auf 4 Arbeitsbereiche (Assets, Börsen, Devisen,
Analyse), Config/Diagnose unter eine Einstellungsseite mit adressierbaren Reitern
(`#/settings?tab=…`), Zugang über ein Zahnrad rechts. Teil-Ticket von **T-11**.

<!--
  Repo:   frontend (dashboard/)
  Status: in-progress — Code fertig & reviewt; wartet auf Human-Browser-Abnahme.
  Scope:  UI-Architektur (Nav, Settings, Routing, i18n). Kein Backend-Change.
  Branch: t-11a-nav-settings (6 Commits 6ab21b8..d91848c)
-->

---

## Verify

Legende: ✅ live bestätigt · ⚠️ bestätigt mit Einschränkung (Fußnote) ·
◑ teilweise (Fußnote) · ➖ keine Live-Verifikation (nur Unit/Review).
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

**Voraussetzung:** Stack läuft (`make dev-up`) — Backend `:8000`, Dashboard `:5173`.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | `http://localhost:5173/` | Hauptmenü zeigt **genau 4** Punkte: Assets · Börsen · Devisen · Analyse — **linksbündig** an der Wortmarke | ➖ | |
| 2 | Kopfzeile rechts | **Zahnrad** statt DE/EN; Klick öffnet die Einstellungsseite (Zahnrad wird aktiv) | ➖ | |
| 3 | `#/settings` | Reiter in Reihenfolge **Darstellung · Sprache · API & Links · Environment**; Environment sichtbar **abgesetzt ganz rechts** | ➖ | |
| 4 | `#/settings?tab=environment` (direkt in Adresszeile) | lädt direkt den **Environment**-Reiter; analog `?tab=appearance\|language\|links` | ➖ | |
| 5 | `#/settings` (ohne Query) eingeben | Adresszeile normalisiert auf `#/settings?tab=appearance` | ➖ | |
| 6 | Sprach-Reiter | DE/EN umschalten → wirkt **app-weit**; Aktiv-Markierung bleibt auf „Sprache"; **Hauptnav-Markierung stimmt** nach Sprachwechsel (kein verrutschter Balken) | ➖ | |
| 7 | DevTools → `localStorage['stockinfo-lang']` löschen, Reload | Sprache folgt der **Browser-Sprache** (kein Zwang auf EN) | ➖ | |
| 8 | Fenster < 768 px | kein waagrechtes Scrollen; Hamburger-Drawer weiter funktionsfähig (T-05); Zahnrad bleibt rechts | ➖ | |
| 9 | `cd dashboard && npm run build && npm test` | `vue-tsc -b` ohne Fehler, `vite build` ok, **102/102** Tests grün | ✅¹ | |

> ¹ **(CC):** live bestätigt — `vue-tsc -b` exit 0, `vite build` ok, 102 Tests
> (28 Files) grün; unabhängig nachgezogen im finalen Whole-Branch-Review
> (`f60887d..1295824`) und im Increment-A-Review (`1295824..d91848c`). Nur
> vorbestehende Sass-„legacy-JS-API"-Deprecation-Warnung (nicht neu).
> Zeilen 1–8 sind UI-observierbar und noch **nicht** live im Browser geprüft (➖).

---

## Details

### Kontext / Ziel
Umsetzung der Gap-Analyse-Punkte 1+2 aus **T-11** (Skill `ux-standards`).
Spec: `docs/superpowers/specs/2026-08-15-t11a-nav-settings-design.md`.
Plan: `docs/superpowers/plans/2026-08-15-t11a-nav-settings.md`.

Umsetzung subagent-getrieben (TDD je Task, Task-Review + finaler Whole-Branch-Review):

1. `useHashTab` → `{ tab, settingsTab }` + Query-Parsing `#/settings?tab=…`
2. `SettingsPanel.vue` (Reiter, Panels wiederverwendet, Sprach-Block neu) + i18n
3. `SettingsPanel` in `App.vue` verdrahtet
4. Kopfzeile: 4 Arbeitsbereiche + Zahnrad statt DE/EN
5. Subtraktive Bereinigung `TabKey`/`TABS`/tote Zweige + voller Typecheck
6. Increment: Hauptmenü linksbündig, `#/settings`-Adresse normalisiert

### Akzeptanzkriterien
- [ ] Verify-Zeilen 1–8 vom Menschen im Browser bestätigt
- [x] `vue-tsc` clean, `vite build` ok, Testsuite grün (Zeile 9)
- [x] Aktiv-Markierung messungsfrei (per-Item-CSS) — sprachwechselfest
- [x] `detectLocale()` unangetastet (Browser-Sprache beim Erst-Besuch)
- [x] Keine neuen Farb-Token-Aliase (bleibt T-11b)

### Side-Effects
Kein Backend-Change. i18n-Keys `nav.themes`/`nav.environment`/`nav.links`
bleiben ungenutzt im Katalog (bewusst, keine Löschwelle in T-11a).
Offene deferred Minors (spätere Tickets): tablist-a11y (roving tabindex /
`role=tabpanel`); redundante Mobil-CSS-Zeile `.settings-btn margin-left:auto`.

### Auflösung
Branch `t-11a-nav-settings`, Commits `6ab21b8 · 3ff915a · facd0e2 · d59be94 ·
1295824 · d91848c`. Alle Task-Reviews + finaler Whole-Branch-Review „Ready to
merge = Yes", keine Critical/Important. **Offen:** Human-Browser-Abnahme
(Zeilen 1–8), dann Merge nach `master` und `git mv` nach `solved/`.
