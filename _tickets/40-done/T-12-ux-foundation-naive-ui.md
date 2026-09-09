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
| 1 | `dashboard/src/styles/` | keine eigenen Paletten mehr; Token kommen aus `tokens.css` des Pakets | ✅¹ | |
| 2 | Einstellungen → Darstellung | **alle** Paletten des Fundaments zur Wahl, Vorschau je Kachel | ✅² | |
| 3 | localStorage auf `earth`/`night`/`sunset`/`neon` setzen, neu laden | App startet auf der Vorgabe statt auf leerem `data-theme` | ✅³ | |
| 4 | Kopf-/Statuszeile in einem hellen und einem dunklen Theme | Leisten holen ihre Flächen aus den Leisten-Token, Text bleibt lesbar | ◑⁴ | |
| 5 | < 768 px | Symbole bleiben in der Zeile, **kein** Hamburger; Beschriftung fällt weg (T-11g) | ✅⁵ | |
| 6 | Kopfzeile | Plakette als Inline-SVG + Wortmarke als HTML-Text, zweifarbig (T-11h) | ✅⁶ | |
| 7 | DevTools → Computed | Fließtext in Inter, Titel in Space Grotesk (T-11f) | ✅⁷ | |
| 8 | Konsole: `performance.getEntriesByType('resource')…` | leer bis auf die eigene API — nichts vom CDN | ✅⁸ | |
| 9 | Fehlerfall (Backend stoppen) | Meldung als **Toast**, schiebt das Layout nicht (T-11e) | ➖⁹ | |
| 10 | Statuszeile | links Kontext, rechts Version + anklickbarer Backend-Punkt (T-11e) | ✅¹⁰ | |
| 11 | Code | kein direktes `localStorage.` mehr — alles über `safeStorage`; Wächter-Test grün | ✅¹¹ | |
| 12 | Code | kein eigenes `useIsCompact`, `NavIcon`, `token()`, keine eigene Sprach-Erkennung mehr | ✅¹² | |
| 13 | Sprache DE/EN umschalten | Wahl greift, `lang` zieht mit, Naive-Locale hängt an derselben Quelle | ✅¹³ | |
| 14 | `npx vitest run` + `vue-tsc -b` | Tests grün, Typecheck sauber | ✅¹⁴ | |
| 15 | breiter Schirm | Kopfzeile, Inhalt und Statuszeile enden an derselben Kante | ✅¹⁵ | |
| 16 | Assets, Devisen, Einstellungen | keine nativen `input`/`select`/`button` mehr — alles Naive UI | ✅¹⁶ | |

¹ `base.scss` enthält nur noch Marke, Globales und geteilte Bausteine; die acht Paletten sind entfallen.
² Gemessen: 13 Kacheln, Namen aus dem Katalog („MangoLila", „Bernstein", „Petrol", „Klassisch"…).
³ `sunset` gesetzt → nach dem Neuladen `data-theme="mangolila"`, Speicher auf `mangolila` korrigiert, Grundfläche `rgb(24 23 22)`.
⁴ Nur in `mangolila` und `classic` live gesehen. Ein helles Theme mit umgekehrten Leisten (`sepia`) steht noch aus.
⁵ Bei 375 px: fünf Menüpunkte, **null** sichtbare Beschriftungen, kein Hamburger, waagrechter Überhang 0.
⁶ Plakette trägt das Kurstafel-Motiv im Markenverlauf, Wortmarke „Stock" + „Info" als Text.
⁷ `Inter Variable` für den Fließtext, `Space Grotesk Variable` für Überschriften.
⁸ Liste der fremden Ressourcen: leer.
⁹ **Nicht umgesetzt.** `ErrorBanner` steht weiterhin im Textfluss; die Provider für Toasts sind verdrahtet, die Umstellung der fünf Fehlerquellen fehlt. Siehe „Offen".
¹⁰ Punkt sichtbar und grün (`--status-ok`), Klick führt auf die Einstellungen; Kontext zeigt „5 Papiere".
¹¹ `grep` nach direktem Zugriff liefert nur einen Kommentar; `tests/storageAccess.spec.ts` grün.
¹² Alle vier Dateien gelöscht bzw. umgebogen; `NavIconName` kommt aus dem Paket.
¹³ Umschalten auf Englisch: `lang` wechselt auf `en`, Speicher auf `en`; die Naive-Locale hängt am selben `locale`.
¹⁴ 149 Tests in 34 Dateien, `vue-tsc -b` ohne Ausgabe, `vite build` erfolgreich.
¹⁵ Linke und rechte Kante von Kopf- und Statuszeile stimmen überein.
¹⁶ `grep` über alle Komponenten: kein `<button>`, `<input>`, `<select>`, `<textarea>` mehr.

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
  App-Asset. Kennfarbe StockInfo: **Koralle nach Pflaume**. Das ist die eine
  Ausnahme von „alles kommt aus dem Fundament" — Themes sind über alle Apps
  dieselben, die Marke unterscheidet sie. Die App überschreibt `--brand-from`,
  `--brand-to` und `--brand-word` auf `:root`; die beiden Stufen der Wortmarke
  sind gegen alle Leisten-Flächen gemessen (4,8:1 dunkel, 5,2:1 hell).
- **T-11c Zeile 8** blieb ➖: Es gibt kein Testpapier ohne ISIN.
- **T-11i Zeile 4** blieb ➖: echtes Löschen bewusst nicht ausgelöst.
- Der Stash `stash@{0}` auf `t-11d-themes` (Rohfassung der dreizehn Paletten,
  ungeprüft) ist mit dieser Umstellung **gegenstandslos** — die Paletten kommen
  aus dem Paket. Er bleibt liegen, bis jemand ihn bewusst verwirft.

---

## Auflösung

Umgesetzt in `master`, Commits `67af83a` (Fundament und Naive-Brücke),
`f4e2539` (native Bedienelemente ersetzt), `9292aae` (eine Sorte Knopf) und
`97a1063` (Verify-Matrix). 151 Tests in 35 Dateien, `vue-tsc -b` sauber,
`vite build` erfolgreich.

Fünfzehn der sechzehn Verify-Zeilen sind live geprüft (siehe Fußnoten oben);
Zeile 9 blieb ➖. Die Human-Abnahme entfiel auf Entscheid des Auftraggebers —
die Befunde aus seinem parallelen Testlauf sind eingeflossen: klebende
Statuszeile, sichtbarer Zustandspunkt, Wortmarke in der eigenen Kennfarbe,
erkennbare Verweise, Knopfgrößen.

**Was dabei ins Fundament ging** — die Umstellung hat mehr geliefert als
genommen: `UxNavItem` und `UxThemePicker` (beide lagen dreimal vor), die
Symbole `exchanges`/`fx`/`analysis`, ein Zeichen samt FavIcon fürs
Schaufenster, und zwei Korrekturen, bei denen **StockInfos** Fassung die
bessere war: der Umschaltpunkt bei `767.98` statt `767` und die Fensterbreite
sofort statt erst beim Einhängen gemessen.

**Ein Fund erklärte drei Symptome auf einmal:** `additionalData` erreicht nur
Dateien, die Vite selbst verarbeitet — was Sass über `@use` nachlädt, sieht es
nicht. `_variables.scss` kannte `token()` deshalb nicht, ließ den Aufruf als
unbekannte CSS-Funktion stehen (**ohne Fehler**), und der Browser verwarf jede
Deklaration damit. Sichtbar als nackte Eingabefelder, Verweise ohne Rahmen und
fehlende Flächen.

**Offen, weiter in [T-13](T-13-toasts-und-dialoge.md):** Toasts statt
`ErrorBanner`, die beiden Dialoge auf `NModal`, und ein helles Theme mit
umgekehrten Leisten ansehen (Verify #4).
