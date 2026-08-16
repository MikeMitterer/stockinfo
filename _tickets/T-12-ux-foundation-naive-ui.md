# T-12 · Auf ux-foundation und Naive UI umstellen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | in-progress | mehrphasig | UI-Architektur | — |

**Löst:** StockInfo bezieht Token, Themes, Schriften, Reset, Symbole, Leisten und
die wiederkehrenden Composables aus `@mikemitterer/ux-foundation` statt sie selbst
zu pflegen; Bedienelemente kommen von **Naive UI**. Löst **T-11d/e/f/g/h** ab —
alle fünf wollten nachbauen, was das Paket fertig mitbringt.

<!--
  Repo:   frontend (dashboard/). Scope: UI-Architektur, kein Backend-Change.
  Basis:  master (Branch-Stapel T-11a/b/c/i per Fast-Forward geführt).
  Pfad zum Fundament: "${DEV_LOCAL}/DevWeb/Production/ux-foundation" —
  nie absolut notieren, der Pfad unterscheidet sich je Rechner.
-->

---

## Verify

Legende: ✅ live bestätigt · ⚠️ bestätigt mit Einschränkung (Fußnote) ·
◑ teilweise (Fußnote) · ➖ keine Live-Verifikation.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

**Voraussetzung:** Stack läuft (`make dev-up`) — Backend `:8000`, Dashboard `:5173`.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | `dashboard/src/styles/` | keine eigenen Paletten mehr; Token kommen aus `tokens.css` des Pakets | | |
| 2 | Einstellungen → Themes | **alle** Paletten des Fundaments zur Wahl, Vorschau je Kachel | | |
| 3 | localStorage auf `earth`/`night`/`sunset`/`neon` setzen, neu laden | App startet auf der Vorgabe statt auf leerem `data-theme` | | |
| 4 | Kopf-/Statuszeile in einem hellen und einem dunklen Theme | Leisten holen ihre Flächen aus den Leisten-Token, Text bleibt lesbar | | |
| 5 | < 768 px | vier Symbole bleiben in der Zeile, **kein** Hamburger; Beschriftung fällt weg (T-11g) | | |
| 6 | Kopfzeile | Plakette als Inline-SVG + Wortmarke als HTML-Text, zweifarbig (T-11h) | | |
| 7 | DevTools → Computed | Fließtext in Inter, Titel in Space Grotesk (T-11f) | | |
| 8 | Konsole: `performance.getEntriesByType('resource').filter(r => !r.name.startsWith(location.origin))` | leer bis auf die eigene API — nichts vom CDN | | |
| 9 | Fehlerfall (Backend stoppen) | Meldung als **Toast**, schiebt das Layout nicht (T-11e) | | |
| 10 | Statuszeile | links Kontext + Daten-Alter, rechts Version + anklickbarer Backend-Punkt (T-11e) | | |
| 11 | Code | kein direktes `localStorage.` mehr — alles über `safeStorage`; Wächter-Test grün | | |
| 12 | Code | kein eigenes `useIsCompact`, `useTheme`, `NavIcon`, `token()` mehr | | |
| 13 | Sprache DE/EN umschalten | Naive-eigene Texte („Bestätigen"/„Abbrechen") schalten mit | | |
| 14 | `npx vitest run` + `vue-tsc -b` | Tests grün, Typecheck sauber | | |
| 15 | breiter Schirm | Kopfzeile, Inhalt und Statuszeile enden an derselben Kante | | |

```bash
cd "${DEV_LOCAL}/DevWeb/Production/StockInfo/dashboard"
npx vitest run                                    # #14
npx vue-tsc -b                                    # #14
grep -rn "localStorage\." src/ | grep -v safeStorage   # #11 → muss leer sein
```

---

## Plan

Reihenfolge nach `ux-standards` („Das Fundament einbinden", Schritt 5): erst die
Stylesheets — dort fällt sofort auf, wenn ein Token fehlt —, dann Theme und
Naive-Brücke, dann Komponenten, zuletzt die Composables. Nach jeder Phase bleibt
die App lauffähig.

### Phase 0 — Einbinden
`@mikemitterer/ux-foundation` als `file:`-Abhängigkeit, `naive-ui` dazu.
`vite.config.ts`: `additionalData` für die SCSS-Helfer, `optimizeDeps.exclude`,
`server.fs.allow`. In `main.ts` Schriften, Token, Reset in dieser Reihenfolge.

### Phase 1 — Token und Paletten
Die acht eigenen Paletten in `base.scss` entfallen; es gelten die des Pakets.
`_variables.scss` gibt `token()` und die Breakpoints ab.

**Entscheidung zu den vier eigenen Themes.** `earth`, `night`, `sunset` und
`neon` fallen **weg** statt ins Fundament zu wandern: Sie sind nie gegen die
Grenzwerte gemessen worden, hätten Leisten-Token nachzurüsten und würden die
Sammlung auf siebzehn aufblähen, ohne einen Charakter zu ergänzen, den es nicht
schon gibt. `classic`, `ocean`, `forest` und `mono` behalten ihren Namen, bekommen
aber die Farben des Fundaments — „gleicher Name, gleiche Farbe" ist die Regel,
und heute widerspricht StockInfo ihr.

Eine gespeicherte Wahl, die es nicht mehr gibt, fällt auf die Vorgabe zurück
(`isThemeId` prüft, `DEFAULT_DARK_THEME`/`DEFAULT_LIGHT_THEME` entscheiden).
Ohne das stünde ein ungültiges `data-theme` am Wurzelelement und die App wäre
farblos.

### Phase 2 — Theme-Store und Naive-Brücke
`useTheme` bezieht `THEMES`/`isThemeId`/Vorgaben aus dem Paket und speichert über
`safeStorage`. `App.vue` bekommt `NConfigProvider` mit `buildNaiveOverrides()`,
`inline-theme-disabled`, die Naive-Locale und die Provider für Meldungen.

### Phase 3 — Komponenten
`AppHeader` → `UxTopbar` (+ T-11g: Symbole statt Hamburger, Einstellungen links),
`StatusBar` → `UxStatusBar` (+ T-11e), `NavIcon` → `UxIcon`, `ThemesPanel` →
**`UxThemePicker`** (neu im Fundament, siehe unten), Marke und FavIcon nach T-11h.

### Phase 4 — Composables und Reste
`useIsCompact` aus dem Paket; `ErrorBanner` weicht Toasts (`useNotifier`);
Sprach-Erkennung über `detectLocale`/`persistLocale`; jeder `localStorage`-Zugriff
über `safeStorage`, abgesichert durch denselben Wächter-Test wie in
StockPortfolio.

### Neu im Fundament: `UxThemePicker`
Beide Apps bauen dieselbe Auswahl — ein Kachelraster, je Theme vier Farbflecken,
aktive Markierung. Das Feld `ThemeInfo.preview` im Paket existiert ausschließlich
für diese Darstellung, und die Darstellung lag zweimal vor. Beschriftungen und
Hinweise kommen als Prop herein, damit die Komponente keinen Katalog braucht.

---

## Übernommen aus T-11 (nicht verlieren)

- **T-11g** dreht Teile von T-05 und T-11a bewusst zurück: kein Hamburger, die
  Einstellungen wandern in die Menüzeile links.
- **T-11h:** `logo.svg`/`logo.png` bleiben unangetastet — Firmenmaterial, kein
  App-Asset. Kennfarbe StockInfo: Koralle nach Pflaume.
- **T-11c Zeile 8** blieb ➖: Es gibt kein Testpapier ohne ISIN.
- **T-11i Zeile 4** blieb ➖: echtes Löschen bewusst nicht ausgelöst.
- Der Stash `stash@{0}` auf `t-11d-themes` (Rohfassung der dreizehn Paletten,
  ungeprüft) ist mit dieser Umstellung **gegenstandslos** — die Paletten kommen
  aus dem Paket. Er bleibt liegen, bis jemand ihn bewusst verwirft.
