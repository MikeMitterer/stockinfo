# T-14 · Kontrast auf umgekehrten Leisten — und ein Prüfskript, das ihn sieht

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| ux-foundation (Deliverable) + alle Apps | ready | ~4 h | Token + Komponente + Prüfskript | — |

**Löst:** Verify #7 aus **T-13**. In den Themes, die hellen Inhalt zwischen
dunkle Leisten setzen (`sepia`, `meadow`), liegen Wortmarke, Akzent-Verweis und
die leise Stufe der Statuszeile unter 4.5:1 — und `make check-themes` meldet
sie trotzdem als „in Ordnung".

<!--
  Repo:   Deliverable liegt in ux-foundation (Token, UxStatusBar, theme-tokens.py).
          Die Apps erben die Korrektur, ohne selbst etwas zu ändern.
-->

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | `make check-themes` | misst gegen die **gerenderte** Leiste (Deckkraft über der Inhaltsfläche), nicht gegen `--surface-header` | | |
| 2 | `make check-themes` | meldet `sepia` und `meadow` als Verstoß, solange sie nicht korrigiert sind — der Lauf muss also erst rot werden | | |
| 3 | Theme `sepia`, Statuszeile | „powered by"-Verweis ≥ 4.5:1 gegen die gerenderte Leiste | | |
| 4 | Theme `sepia`, Kopfzeile | Wortmarken-Hälfte „Info" ≥ 4.5:1 | | |
| 5 | Theme `sepia`, Statuszeile | Trennpunkte, Version, Ampel-Beschriftung ≥ 4.5:1 | | |
| 6 | Theme `meadow`, beide Leisten | dieselben fünf Messungen halten | | |
| 7 | alle übrigen Themes | keine Verschlechterung — der Lauf bleibt sonst grün | | |
| 8 | StockInfo und StockPortfolio | beide erben die Korrektur, ohne eigene Werte zu setzen | | |

```bash
cd "${DEV_LOCAL}/DevWeb/Production/ux-foundation"
make check-themes                          # #1, #2, #7
npx vitest run                             # Token-Wächter
python3 scripts/theme-tokens.py --help     # die selteneren Unterbefehle
```

Messung im Browser (gegen die **gerenderte** Fläche, nicht gegen den Token) —
die Leisten laufen mit Deckkraft, darunter schimmert der Inhalt durch:

```js
// #3 bis #6 — in der laufenden App, je Theme
const lin = c => { c/=255; return c <= 0.03928 ? c/12.92 : Math.pow((c+0.055)/1.055, 2.4) }
const lum = ([r,g,b]) => 0.2126*lin(r) + 0.7152*lin(g) + 0.0722*lin(b)
const nums = s => s.match(/[\d.]+/g).map(Number)
const k = (a,b) => { const [h,l] = [lum(a),lum(b)].sort((x,y)=>y-x); return +(((h+0.05)/(l+0.05)).toFixed(2)) }
const seite = nums(getComputedStyle(document.body).backgroundColor).slice(0,3)
const flaeche = el => { const v = nums(getComputedStyle(el).backgroundColor), a = v[3] ?? 1
  return [0,1,2].map(i => Math.round(v[i]*a + seite[i]*(1-a))) }
const bar = document.querySelector('.ux-statusbar')
k(nums(getComputedStyle(bar.querySelector('a')).color).slice(0,3), flaeche(bar))
```

---

## Details

### Was gemessen wurde (T-13, Theme `sepia`)

Die Leiste läuft mit `token(--surface-header, .85)` über hellem Inhalt. Der
Token ist `rgb(43 37 30)`, gerendert wird daraus `rgb(73 67 59)` — sichtbar
heller, und damit trägt helle Schrift darauf **weniger**, nicht mehr.

| Element | Token | gemessen | verlangt |
|---|---|--:|--:|
| Wortmarke „Info" | `--brand-word` (dunkle Stufe) | **4.15** | 4.5 |
| „powered by"-Verweis | `--accent` | **2.27** | 4.5 |
| Trennpunkte, Version, Ampel | `--text-bar-muted` | **3.93** | 4.5 |
| Menüpunkte | `--text-bar-secondary` | 6.09 | 4.5 |
| Statuszeilen-Text | `--text-bar` | 7.11 | 4.5 |

`make check-themes` meldete `sepia` dabei als „in Ordnung" — es rechnet gegen
den **Token**. Genau die Falle, die der Skill unter „Kontrast gegen die
gerenderte Fläche, nicht gegen das Token" beschreibt.

### Die eigentliche Ursache

Die Leisten haben eigene Flächen- und Textfarben (`--surface-header`,
`--text-bar…`) — genau deshalb darf ein Theme sie umkehren. **Der Akzent hat
keine solche Entsprechung.** `.ux-statusbar__origin` greift auf `--accent`, und
der ist für die Inhaltsfläche gewählt.

Dasselbe Muster war in T-13 schon zweimal zu sehen: Ein `NButton` in der
Kopfzeile stand bei 1.38:1, weil Naive global die Farben des Inhalts bekommt —
gelöst mit `buildBarNaiveOverrides()`. Und der Verweis in der Statuszeile stand
im neuen `macos`-Theme bei 2.88:1 — gelöst mit `--text-bar-accent`. Beide
Vorlagen sind also vorhanden; dieses Ticket wendet sie auf `sepia` und `meadow`
an und bringt das Prüfskript so weit, dass es solche Fälle selbst findet.

### Vorschlag

- **`--text-bar-accent` gibt es bereits.** Es kam mit dem `macos`-Theme dazu,
  weil ein neu angelegtes Theme nicht mit einer bekannten Lücke ausgeliefert
  werden sollte: Der Verweis lag dort bei 2.88:1, mit eigenem Ton bei 5.48:1.
  Der Rückfall ist `--accent`, `UxStatusBar` liest es. Für dieses Ticket bleibt
  also nur, **`sepia` und `meadow` einen Wert zu geben** — der Mechanismus
  steht.
- **`--brand-word`** und **`--text-bar-muted`** für `sepia` und `meadow` gegen
  die *gerenderte* Leiste lösen, nicht gegen den Token. Vorsicht bei
  `--text-bar-muted`: Der Abstand zu `--text-bar-secondary` darf dabei nicht
  unter rund 10 % Helligkeit fallen, sonst liest sich die leise Stufe nicht
  mehr als leise (siehe „Die leise Stufe muss leise bleiben" im Skill).
- **`theme-tokens.py`** rechnet die Deckkraft der Leisten mit. Der Wert steht
  heute in den Komponenten (`UxTopbar`, `UxStatusBar`); damit er nicht an zwei
  Orten lebt, gehört er als Token in `tokens.css` — dann kann das Skript ihn
  lesen.

### Side-Effects

Ändert Werte, die alle Apps teilen. Die Korrektur an `--brand-word` betrifft
jedes Theme mit dunklen Leisten, nicht nur die beiden — vor dem Commit
`make check-themes` über die ganze Sammlung.

### Auflösung

_(offen)_
