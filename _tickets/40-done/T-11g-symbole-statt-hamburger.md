# T-11g · Symbole statt Hamburger, Einstellungen nach links

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | ready | ~3 h | UI-only | — |

**Löst:** Der Hamburger-Drawer entfällt — unter dem Umschaltpunkt bleiben die
vier Symbole in der Zeile stehen, nur die Beschriftung fällt weg. Der
Einstellungen-Knopf wandert von rechts in die Menüzeile links. Teil-Ticket von
**T-11**, neu aus dem Skill-Stand 2026-08-15 (Abschnitt „Auf schmalen Schirmen
bleiben die Symbole stehen").

<!--
  Repo:   frontend (dashboard/). Status: ready. Scope: UI-only.
  Entscheid Mike (2026-08-15): Symbole-statt-Hamburger ist die Vorgabe,
  der Hamburger die begründungspflichtige Ausnahme. Bezug ist StockPortfolio.
  Dreht bewusst einen Teil von T-05 (Hamburger-Drawer) und von T-11a
  (Einstellungen rechts) zurück — beides war Stand des damaligen Skills.
-->

---

## Verify

Legende: ✅ live bestätigt · ⚠️ bestätigt mit Einschränkung (Fußnote) ·
◑ teilweise (Fußnote) · ➖ keine Live-Verifikation (nur Unit/Review).
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

**Voraussetzung:** Stack läuft (`make dev-up`) — Backend `:8000`, Dashboard `:5173`.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | `http://localhost:5173/`, Fenster 375 px | **kein** `☰` im Dokument; fünf Symbole (Assets, Börsen, Devisen, Analyse, Einstellungen) nebeneinander sichtbar | ➖ | |
| 2 | ebenda | `document.documentElement.scrollWidth − clientWidth === 0`; Kopfzeile einzeilig, Höhe 58 px | ➖ | |
| 3 | Fenster 375 px | Beschriftungen sichtbar **weg**, aber je Knopf ein `.visually-hidden` mit dem Text — Screenreader liest weiter „Assets" usw. | ➖ | |
| 4 | Fenster 1024 px | ebenfalls **keine** Schublade (heute greift der Drawer schon unter 1280 px) | ➖ | |
| 5 | Fenster ≥ 768 px | Beschriftungen wieder da, alle fünf Punkte **linksbündig** an der Wortmarke | ➖ | |
| 6 | Kopfzeile rechts | Einstellungen steht **nicht** mehr rechts; rechts bleibt nur, was keine Navigation ist | ➖ | |
| 7 | Einstellungen-Punkt | trägt dasselbe Aktiv-Merkmal wie die vier anderen (volle Textfarbe + 2 px Unterstrich), kein Sonderstil | ➖ | |
| 8 | Fenster 375 px | Plakette statt voller Wortmarke — das Logo darf keine 190 px belegen (siehe „Kontext") | ➖ | |
| 9 | Tastatur: Tab durch die Kopfzeile | Reihenfolge Wortmarke → fünf Menüpunkte; kein Fokus auf einem unsichtbaren Drawer-Rest | ➖ | |
| 10 | `grep -rn "isOpen\|backdrop\|hamburger\|nav.menu" dashboard/src` | keine Treffer mehr — auch der i18n-Schlüssel `nav.menu` ist weg | ➖ | |
| 11 | `cd dashboard && npm run build && npm test` | `vue-tsc -b` ohne Fehler, `vite build` ok, Testsuite grün | ➖ | |

Messblock — Zeile für Zeile in der DevTools-Konsole:

```js
// #1 + #10: kein Hamburger, keine Reste
document.querySelectorAll('.hamburger, .backdrop').length                    // → 0

// #2: kein waagrechter Überhang
document.documentElement.scrollWidth - document.documentElement.clientWidth  // → 0

// #1 + #5: Symbole zählen und Beschriftungen prüfen
[...document.querySelectorAll('.appheader .tab')].map(t => t.innerText.trim())

// #3: zugängliche Beschriftung trotz versteckten Texts
[...document.querySelectorAll('.appheader .tab')].map(t => t.textContent.trim())

// #6: rechte Kante — was steht rechts von der Navigation?
const n = document.querySelector('.nav-tabs').getBoundingClientRect()
;[...document.querySelectorAll('.appheader > *')]
  .filter(e => e.getBoundingClientRect().left > n.right)
  .map(e => e.className)                                                     // → []

// #8: Breite des Zeichens auf schmalem Schirm
document.querySelector('.appheader .brand').getBoundingClientRect().width
```

---

## Details

### Kontext / Ziel

Der Skill sagt seit 2026-08-15 ausdrücklich: Unter dem Umschaltpunkt fällt die
**Beschriftung** weg, nicht der Menüpunkt. Der Hamburger ist die Ausnahme und
wird erst nötig, wenn die Punkte **auch als Symbole** nicht mehr in eine Zeile
passen. Bezug ist StockPortfolio, `AppTopbar.vue`:

```vue
<span class="topbar__label">{{ item.label }}</span>
<span class="visually-hidden">{{ item.label }}</span>
```

```scss
&__label {
  display: none;

  @include up(md) { display: inline; }
}
```

**Gemessen am Ist-Zustand** (2026-08-15, `http://localhost:5173/`, 1746 px,
Deutsch):

| Bestandteil | Breite |
|---|---|
| Logo (`stockinfo-logo.svg` als ein Bild) | 190,4 px |
| vier Punkte **mit** Beschriftung inkl. Abstände | 403,0 px |
| vier Punkte **ohne** Beschriftung inkl. Abstände | 178,4 px |
| Einstellungen-Knopf | 32,0 px |
| Kopfzeilen-Padding | 2 × 20 px |

Daraus: mit Beschriftung braucht die Kopfzeile rund **690 px**, ohne rund
**465 px**. Der Umschaltpunkt steht aber auf `$header-bp: 1280px`
(`src/styles/_variables.scss:36`). Es gibt also gut **590 px Breite, auf denen
die Schublade ohne Anlass erscheint** — auf jedem Laptop und jedem Tablet quer.

**Die Kopplung an das Logo ist der unbequeme Teil:** 465 px passen auf ein
375-px-Telefon immer noch nicht. Der Grund ist das Logo — es ist *ein* Bild von
190 px, das die Wortmarke enthält, und aus einem Bild lässt sich die Wortmarke
nicht abwerfen. Der Skill verlangt aber, dass unterhalb `sm` die Wortmarke
entfällt und die Plakette bleibt. Zwei Wege:

- **Sauber:** Plakette als Inline-SVG + Wortmarke als HTML-Text, wie in
  StockPortfolio. Löst zugleich das Schrift- und Theme-Problem der Datei (die
  Wortmarke steht dort als `<text>` in `system-ui`, Gewicht 700, Füllung fest
  `#ece8f2`). Gehört in das noch nicht angelegte Logo-Ticket.
- **Übergangsweise in diesem Ticket:** unterhalb `sm` auf
  `stockinfo-icon.svg` umschalten, damit Zeile 8 erfüllt ist.

Der zweite Weg ist hier eingeplant, damit T-11g für sich abschließbar bleibt.
Kommt das Logo-Ticket, ersetzt es die Umschaltung durch die saubere Trennung.

**Einstellungen gehört nach links.** Der Skill führt „Einstellungen" in der
Tabelle der wiederkehrenden **Menüpunkte** (Symbol: Schieberegler) und sagt zur
Ausrichtung: alles, was zur Navigation gehört, steht links und schließt an die
Wortmarke an — rechts steht nur, was *nicht* Navigation ist (Aktualisieren,
Zustand der Daten, Sitzung, notfalls Sprache). Eine Seite ist ein Ort, kein
Werkzeug. In StockPortfolio ist Einstellungen der vierte von vier
gleichrangigen Punkten; StockInfo bekommt damit fünf. Das liegt im Richtwert
von drei bis fünf.

Dass der Knopf heute rechts steht, ist kein Fehler von T-11a — es war der
damalige Stand. Mit dem Umzug fällt auch `margin-left: auto` an ihm weg und
damit die in T-11a notierte redundante Mobil-CSS-Zeile.

### Akzeptanzkriterien

- [ ] `.hamburger`, `.backdrop`, `isOpen`, `selectTab`-Schließlogik und der
      `keydown`/Escape-Listener sind aus `AppHeader.vue` entfernt
- [ ] i18n-Schlüssel `nav.menu` in `de.ts` **und** `en.ts` gelöscht
- [ ] `.visually-hidden` als Hilfsklasse angelegt (StockInfo hat noch keine) und
      je Menüpunkt gesetzt
- [ ] Beschriftungen fallen unter **`md` (768 px)** weg, nicht unter 1280 px;
      `$header-bp` entsprechend angepasst oder aufgelöst, mit Kommentar samt
      gemessener Zahl daneben
- [ ] Einstellungen ist ein Menüpunkt in `tabs`, links, mit gleichem Aktivstil;
      `margin-left: auto` entfällt
- [ ] Unterhalb `sm` zeigt die Kopfzeile die Plakette statt der vollen Wortmarke
- [ ] Verify-Zeilen 1–10 vom Menschen im Browser bestätigt

### Side-Effects

Kein Backend-Change. Dreht Teile von **T-05** (Hamburger-Drawer) und **T-11a**
(Einstellungen rechts) bewusst zurück — beide bleiben in `solved/` bzw. auf
ihrem Stand, das „Warum" steht hier.

Berührt `AppHeader.vue`, `src/styles/_variables.scss` und beide i18n-Kataloge.
Unabhängig von T-11b/c/d/e. Die Logo-Umschaltung unter `sm` ist ausdrücklich
eine Zwischenlösung und wird vom Logo-Ticket abgelöst.

Die in T-11a offen notierte tablist-a11y (roving tabindex, `role=tabpanel`)
bleibt offen — sie betrifft die Reiter der Einstellungsseite, nicht die
Kopfzeile.

### Auflösung

_(offen)_

---

## Abschluss (2026-08-16)

**Nicht einzeln umgesetzt — abgelöst durch T-12.** Was dieses Ticket
nachbauen wollte, liefert `@mikemitterer/ux-foundation` seit dem 16.08.2026
fertig. Ein zweiter Nachbau wäre genau die Doppelung, die das Paket beenden
soll. Die Anforderungen sind in T-12 als Abnahmekriterien übernommen.
