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
| 1 | `http://localhost:5173/` | Hauptmenü zeigt **genau 4** Punkte: Assets · Börsen · Devisen · Analyse — **linksbündig** an der Wortmarke | ✅¹ | |
| 2 | Kopfzeile rechts | **Schieberegler** statt DE/EN; Klick öffnet die Einstellungsseite (wird aktiv) | ✅² | |
| 3 | `#/settings` | Reiter in Reihenfolge **Darstellung · Sprache · API & Links · Environment**; Environment sichtbar **abgesetzt ganz rechts** | ✅³ | |
| 4 | `#/settings?tab=environment` (direkt in Adresszeile) | lädt direkt den **Environment**-Reiter; analog `?tab=appearance\|language\|links` | ✅ | |
| 5 | `#/settings` (ohne Query) eingeben | Adresszeile normalisiert auf `#/settings?tab=appearance` | ✅⁴ | |
| 6 | Sprach-Reiter | DE/EN umschalten → wirkt **app-weit**; Aktiv-Markierung bleibt auf „Sprache"; **Hauptnav-Markierung stimmt** nach Sprachwechsel (kein verrutschter Balken) | ✅⁵ | |
| 7 | DevTools → `localStorage['stockinfo-lang']` löschen, Reload | Sprache folgt der **Browser-Sprache** (kein Zwang auf EN) | ✅⁶ | |
| 8 | Fenster < 768 px | kein waagrechtes Scrollen; Hamburger-Drawer weiter funktionsfähig (T-05); Schieberegler bleibt rechts | ⚠️⁷ | |
| 9 | `cd dashboard && npm run build && npm test` | `vue-tsc -b` ohne Fehler, `vite build` ok, **102/102** Tests grün | ✅⁸ | |

> ¹ **(CC):** live gegen `http://localhost:5173/` (2026-08-15, Theme *forest*,
> 1440×900). Gemessen: 4 Tabs `[Assets, Börsen, Devisen, Analyse]`,
> `.nav-tabs` linke Kante **222 px** direkt hinter der Wortmarke (Ende 210 px),
> `.lang` nicht mehr vorhanden, `scrollWidth − clientWidth = 0`.
> ² **(CC):** `.settings-btn` bei 1388–1420 px (ganz rechts); Klick setzt die
> Adresse auf `#/settings?tab=appearance`.
> ³ **(CC):** Reihenfolge live `[Darstellung, Sprache, API & Links, Environment]`;
> Environment beginnt bei 1188 px, „API & Links" endet bei 438 px — klar abgesetzt.
> ⁴ **(CC):** echter Mount-Pfad geprüft (`location.hash='#/settings'` + voller
> `location.reload()`), Adresse danach `#/settings?tab=appearance`, aktiver
> Reiter „Darstellung".
> ⁵ **(CC):** Wechsel auf Englisch im Sprach-Reiter → Nav `[Assets, Exchanges,
> FX, Analysis]`, Seite „Settings", Reiter `[Appearance, Language, API & Links,
> Environment]`; Markierung blieb unter „Language" trotz geänderter
> Label-Breiten. Hauptnav: genau **ein** aktiver Punkt, Unterstrich als
> `::after` (2 px, Einzug 12.8 px) am Element — elementgebunden, nicht gemessen.
> ⁶ **(CC):** `stockinfo-lang` (`"en"`) gelöscht + Reload → `<html lang="de">`,
> Nav wieder deutsch, `navigator.language = "de-DE"`; `localStorage` bleibt
> danach **leer** (nur eine bewusste Wahl persistiert).
> ⁷ **(CC):** ⚠️ nur bis **606 px** geprüft — Chrome lässt das Fenster auf macOS
> nicht schmaler; **nicht** bei 375 px verifiziert. Bei 606 px: `scrollWidth −
> clientWidth = 0`, Kopfzeile einzeilig (58 px), `.nav-tabs` `display:none`,
> Hamburger links (20–57), Schieberegler rechts (554–586); Drawer öffnet, zeigt
> alle 4 Punkte, schließt bei Auswahl (`aria-expanded=false`), Navigation
> korrekt. **Offen für den Menschen:** echtes Telefon / 375 px.
> Die Assets-Tabelle rollt weiterhin in ihrem eigenen Container (`overflow-x:auto`)
> — bekannte Lücke, gehört zu **T-11c**, nicht zu T-11a.
> ⁸ **(CC):** `vue-tsc -b` exit 0, `vite build` ok, 102 Tests (28 Files) grün;
> unabhängig nachgezogen im finalen Whole-Branch-Review. Nur vorbestehende
> Sass-„legacy-JS-API"-Deprecation-Warnung (nicht neu).

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

**Beim Browser-Check gefunden (nicht T-11a-Scope, weitergereicht):**
- Kopfzeile und Inhalt enden **nicht** an derselben Kante: Wortmarke beginnt bei
  20 px, Inhalt bei 120 px (Inhalt zentriert, max 1200 px; Leisten volle Breite
  mit eigenem Padding). Der Skill verlangt denselben Streifen → **T-11e** (Zeile 1c),
  Inhaltsbreite als ein Token → **T-11b**. Vorbestehend, keine Regression aus T-11a.
- Der Reiter „Sprache" rendert ohne Karten-Rahmen, „Darstellung"/„Environment"
  bringen ihren eigenen mit → leichte Uneinheitlichkeit der Reiter-Körper.
  Kosmetik, gehört zum Feinschliff in **T-11b/d**.

### Auflösung
Branch `t-11a-nav-settings`, Commits `6ab21b8 · 3ff915a · facd0e2 · d59be94 ·
1295824 · d91848c` (Code) + `c17ef92 · 4094aee` (Icons nach Skill-Update
2026-08-15: Schieberegler statt Zahnrad, Globus für Assets, Kurstafel für
Börsen). Alle Task-Reviews + finaler Whole-Branch-Review „Ready to merge = Yes",
keine Critical/Important. KI-Browser-Vorabcheck durch (Zeilen 1–8, siehe
Fußnoten). **Offen:** finale Human-Abnahme — insbesondere Zeile 8 bei 375 px und
die Optik der neuen Icons; dann Merge nach `master` und `git mv` nach `solved/`.
