# T-11h · Zeichen, Wortmarke und FavIcon trennen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | ready | ~3 h | UI-only | — |

**Löst:** Das Logo wird auseinandergenommen — Plakette als Inline-SVG, Wortmarke
als HTML-Text. Damit verschwindet der letzte `<text>` aus einer geladenen
SVG-Datei und mit ihm die falsche Schrift, das verbotene Gewicht 700 und die
fest eingetragene Füllung `#ece8f2`. Dazu ein FavIcon, das bei 16 px trägt.
Teil-Ticket von **T-11**, neu aus dem Skill-Stand 2026-08-15 (Abschnitt „Die
Marke").

<!--
  Repo:   frontend (dashboard/). Status: ready. Scope: UI-only.
  Entscheid Mike (2026-08-15): logo.svg und logo.png bleiben unangetastet —
  Firmenmaterial, kein App-Asset. Kennfarbe je App: StockInfo behält
  Koralle nach Pflaume, StockPortfolio hat Azur nach Indigo bekommen.
  Löst die Zwischenlösung aus T-11g ab (Logo-Umschaltung unter sm).
-->

---

## Verify

Legende: ✅ live bestätigt · ⚠️ bestätigt mit Einschränkung (Fußnote) ·
◑ teilweise (Fußnote) · ➖ keine Live-Verifikation (nur Unit/Review).
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

**Voraussetzung:** Stack läuft (`make dev-up`) — Backend `:8000`, Dashboard `:5173`.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | `http://localhost:5173/stockinfo-icon.svg` direkt aufrufen | Zeichen wird **gerendert**, keine Parser-Fehlerseite; kein `<text>` in der Datei | ➖ | |
| 2 | Kopfzeile, alle 8 Themes durchschalten | Plakette trägt **immer denselben** Verlauf Koralle → Pflaume, unabhängig vom Theme | ➖ | |
| 3 | Kopfzeile, alle 8 Themes | Zeichen auf der Plakette bleibt sichtbar (weiß), kippt nirgends ins Dunkle | ➖ | |
| 4 | Wortmarke | „Stock" in Leisten-Textfarbe, „Info" in der Kennfarbe; Gewicht **600**, nicht 700 | ➖ | |
| 5 | DevTools → Computed an der Wortmarke | `font-family` ist `--font-display`, nicht `system-ui` — bzw. dessen Rückfallkette, solange **T-11f** offen ist | ➖ | |
| 6 | Browser-Reiter, echtes Fenster | FavIcon bei 16 px erkennbar: Kachel + Trendlinie, keine Matschfläche | ➖ | |
| 7 | Fenster < 640 px | Wortmarke entfällt, **Plakette bleibt** — ohne die Bild-Umschaltung aus T-11g | ➖ | |
| 8 | `grep -rn "stockinfo-logo\|ece8f2\|<text" dashboard/src dashboard/public dashboard/index.html` | keine Treffer mehr (außer in `logo.svg`/`logo.png`, die bleiben) | ➖ | |
| 9 | `ls dashboard/public` | `stockinfo-logo.svg` und `stockinfo-icon.png` sind weg; `logo.svg`, `logo.png`, `favicon.png` **unangetastet** | ➖ | |
| 10 | Kontrast, gegen die **gerenderte** Leiste gemessen | Kennfarbe der Wortmarke ≥ 4,5:1 in jedem Theme; Zeichen auf der Plakette ≥ 3:1 | ➖ | |
| 11 | `cd dashboard && npm run build && npm test` | `vue-tsc -b` ohne Fehler, `vite build` ok, Testsuite grün | ➖ | |

Messblock — in der DevTools-Konsole:

```js
// #10: Kontrast der Wortmarke gegen die TATSÄCHLICH gerenderte Leiste.
// Nicht gegen --c-bg rechnen: die Kopfzeile ist mit 0.85 durchscheinend
// plus backdrop-filter, der Token ist also nicht die sichtbare Farbe.
const lin = c => (c/=255) <= 0.03928 ? c/12.92 : Math.pow((c+0.055)/1.055, 2.4)
const lum = ([r,g,b]) => 0.2126*lin(r) + 0.7152*lin(g) + 0.0722*lin(b)
const px  = s => s.match(/\d+/g).slice(0,3).map(Number)
const k   = (a,b) => { const [h,l] = [lum(a),lum(b)].sort((x,y)=>y-x); return ((h+0.05)/(l+0.05)).toFixed(2) }

const wort = document.querySelector('.brand__accent')   // Klassenname anpassen
const bar  = document.querySelector('.appheader')
k(px(getComputedStyle(wort).color), px(getComputedStyle(bar).backgroundColor))

// #2: Verlauf der Plakette über alle Themes — muss 8-mal derselbe String sein
;['classic','ocean','earth','night','mono','sunset','forest','neon'].map(t => {
  document.documentElement.dataset.theme = t
  return t + ': ' + getComputedStyle(document.querySelector('.brand__badge')).backgroundImage
})

// #8: kein Text in einer geladenen SVG-Datei
fetch('/stockinfo-icon.svg').then(r => r.text()).then(s => s.includes('<text'))  // → false
```

---

## Details

### Kontext / Ziel

Der Skill sagt: **In einer geladenen Logodatei steht kein `<text>`.** Ein SVG,
das über `<img src>` oder `<link rel="icon">` hereinkommt, ist ein eigenes
Dokument — es sieht weder die Schriften der Seite noch ihre CSS-Variablen und
erbt keine Textfarbe. Die Aufteilung ist deshalb immer dieselbe:

| Teil | Wo er lebt |
|---|---|
| Plakette / FavIcon | SVG, nur Formen |
| Wortmarke | HTML-Text daneben, `--font-display`, Gewicht 600 |

**Der Ist-Zustand verletzt das dreifach.** `public/stockinfo-logo.svg` enthält:

```xml
<text x="66" y="37" font-family="system-ui,-apple-system,'Segoe UI',Arial,sans-serif"
      font-size="30" font-weight="700" letter-spacing="0.3">
  <tspan fill="#ece8f2">Stock</tspan><tspan fill="url(#ml)">Info</tspan>
</text>
```

Systemschrift statt der gebündelten, Gewicht **700** (der Skill kennt nur
400/500/600), und eine feste Füllung `#ece8f2` — die verschwindet, sobald mit
**T-11d** ein helles Theme dazukommt. Genau dieselbe Sorte Fehler steht in
`logo.svg` mit `font-family="Orbitron"`; die Datei bleibt aber unangetastet, sie
ist Firmenmaterial und wird nicht geladen.

Immerhin ist die **Leserichtung schon richtig**: „Stock" neutral, „Info" farbig.
Der Skill hat das inzwischen als Regel — farbig ist der Teil, der die App
unterscheidet, „Stock" teilen sich beide. Das bleibt, es zieht nur von SVG nach
HTML um.

**Der Verlauf ist heute keine Marke.** `--c-grad` ist in `base.scss` **je Theme
ein anderer** — acht Stück von `#f2673f → #9a3593` bis `#2fe0ff → #ff45d6`. Der
Skill: *„eine Marke, die je nach Anstrich anders aussieht, ist keine"*. Die
Plakette bekommt deshalb feste Token; `--c-grad` bleibt, wo es hingehört — am
Unterstrich des aktiven Menüpunkts, denn das **ist** die Akzentfarbe und die
darf mit dem Theme wechseln.

```scss
// Marke — themeunabhängig, StockInfo behält Koralle nach Pflaume
--brand-from:     223  84  48;   // #df5430
--brand-to:       129  44 124;   // #812c7c
--brand-contrast: 255 255 255;   // das Zeichen auf dem Verlauf
```

`--brand-contrast` ist eine eigene Variable und nicht `--accent-contrast`:
Letzteres wechselt mit dem Theme, die Plakette nicht. Rechnerisch trägt Weiß auf
diesem Verlauf 3,83:1 an der hellsten Ecke und 4,67:1 dort, wo das Zeichen
liegt — über den 3:1 für nicht-textliche Grafik. **Nachmessen statt übernehmen**,
sobald T-11d die Paletten bringt.

**Die Kennfarbe der Wortmarke braucht zwei Stufen.** Koralle `#df5430` erreicht
gegen die heutigen acht (durchweg dunklen) Leisten rund 5:1 und trägt damit. Auf
einer hellen Leiste — `paper` kommt mit **T-11d** — fällt sie auf rund 3,1:1 und
reicht nicht mehr. Also dasselbe Vorgehen wie bei Status- und Kategoriefarben:
eine helle und eine dunkle Stufe desselben Tons. Richtwert für die dunkle
Variante `#b03d1f` (rund 4,9:1 auf `paper`) — verbindlich ist die Messung, nicht
die Zahl.

Umgeschaltet wird nach der **Leiste**, nicht nach dem Inhalt: Ein Theme mit
hellem Inhalt und dunkler Kopfzeile bleibt bei der hellen Stufe.

**Das FavIcon lebt bei 16 px.** `stockinfo-icon.svg` trägt heute Candlestick-
Balken mit Deckkraft 0.22, eine Trendlinie, eine Pfeilspitze **und** drei
Datenpunkte. Bei 64 px ist das Detail, bei 16 px Matsch — die Deckkraft 0.22
verschwindet dort ganz. Übrig bleiben Kachel, Trendlinie, Pfeilspitze.

**Fallstrick beim Bearbeiten der SVG-Datei:** In einem XML-Kommentar ist kein
doppelter Bindestrich erlaubt. Ein Token-Name wie `--brand-from` darin macht die
Datei ungültig, und der Browser zeigt statt des Zeichens einen Parser-Fehler
(genau so passiert, deshalb steht Verify-Zeile 1 an erster Stelle). Token-Namen
im Kommentar ohne ihr Präfix nennen.

### Akzeptanzkriterien

- [ ] `AppHeader.vue`: `<img class="logo">` ersetzt durch Plakette (Inline-SVG,
      Verlauf aus den Token) + Wortmarke als HTML-Text aus dem i18n-Katalog
- [ ] Wortmarke zweiteilig, „Info" trägt `--brand-word`; Gewicht 600
- [ ] `base.scss`: `--brand-from`, `--brand-to`, `--brand-contrast`,
      `--brand-word` (zwei Stufen) — fest, **nicht** aus `--c-grad` abgeleitet
- [ ] `--c-grad` bleibt am Aktiv-Unterstrich, wird nicht mit der Marke vermischt
- [ ] `public/stockinfo-icon.svg` neu gezeichnet, auf 16 px ausgelegt
- [ ] `public/stockinfo-logo.svg` und `public/stockinfo-icon.png` gelöscht
- [ ] `logo.svg`, `logo.png`, `favicon.png` **nicht** angefasst
- [ ] Die Logo-Umschaltung unter `sm` aus **T-11g** ist wieder entfernt — die
      Wortmarke fällt jetzt als HTML weg, die Plakette bleibt
- [ ] Verify-Zeilen 1–10 vom Menschen im Browser bestätigt

### Side-Effects

Kein Backend-Change.

**Reihenfolge:** Sinnvoll **nach T-11g** (dort wird die Kopfzeile ohnehin
angefasst) und **vor oder nach T-11d** — bei „nach" fällt die zweite Stufe von
`--brand-word` sofort an, bei „vor" wird sie vorbereitet und mit T-11d
nachgemessen. Unabhängig von T-11b/c/e.

**Hängt an T-11f:** Die Wortmarke soll `--font-display` (Space Grotesk) tragen.
Solange T-11f offen ist, greift die Rückfallkette und die Wortmarke sieht aus
wie heute. Das ist kein Fehler dieses Tickets — es macht sie nur *fähig* dazu.
Verify-Zeile 5 ist entsprechend formuliert.

`favicon.png` bleibt liegen, obwohl unreferenziert: Ob eine PNG-Fassung für
`apple-touch-icon` gebraucht wird, ist eine eigene Frage und gehört nicht hier
hinein.

### Auflösung

_(offen)_

---

## Abschluss (2026-08-16)

**Nicht einzeln umgesetzt — abgelöst durch T-12.** Was dieses Ticket
nachbauen wollte, liefert `@mikemitterer/ux-foundation` seit dem 16.08.2026
fertig. Ein zweiter Nachbau wäre genau die Doppelung, die das Paket beenden
soll. Die Anforderungen sind in T-12 als Abnahmekriterien übernommen.
