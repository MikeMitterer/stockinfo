# T-13 · Toasts statt Banner, Dialoge auf NModal

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend + ux-foundation | in-review | ~3 h | UI-only | — |

**Löst:** Der Rest, den T-12 bewusst stehen ließ — Zustandsmeldungen als Toast
statt als Banner im Textfluss, und die beiden selbstgebauten Dialoge auf
`NModal`. Beides ändert Verhalten, das einzeln geprüft gehört, statt in der
großen Umstellung mitzulaufen. Dazu der letzte offene Punkt aus **T-11e**: die
„?"-Hinweise an erklärungsbedürftigen Begriffen.

<!--
  Repo:   frontend (dashboard/) + ux-foundation (UxInfoHint, Bar-Brücke, Schatten).
  Scope:  UI-only, kein Backend-Change.
  Basis:  master nach T-12.
-->

---

## Verify

Legende: ✅ live bestätigt · ⚠️ bestätigt mit Einschränkung (Fußnote) ·
◑ teilweise (Fußnote) · ➖ keine Live-Verifikation.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

**Voraussetzung:** Stack läuft (`make dev-up`) — Backend `:8000`, Dashboard `:5173`.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Backend stoppen, „Alle aktualisieren" | Meldung als **Toast**; das Layout darunter springt **nicht** | ✅ [^1] | |
| 2 | Toast erscheint | bleibt stehen, bis er weggeklickt wird — Fehler verschwinden nicht von selbst | ✅ [^2] | |
| 3 | Backend wieder starten, erneut laden | Meldung verschwindet, sobald ihre **Ursache** entfällt | ✅ [^3] | |
| 4 | mehrere Fehler nacheinander | keine Stapel-Lawine; höchstens drei gleichzeitig | ✅ [^4] | |
| 5 | Asset löschen | Rückfrage als `NModal`, Escape schließt, Fokus liegt auf „Abbrechen" | ✅ [^5] | |
| 6 | JSON ansehen | `NModal`, Inhalt scrollt, Kopieren funktioniert weiter | ✅ [^6] | |
| 7 | Theme `sepia` (helle Fläche, dunkle Leisten) | Kopf- und Statuszeile lesbar, Wortmarke sichtbar (offen aus T-12 #4) | ⚠️ [^7] | |
| 8 | Fachbegriff (z.B. `strict_exchange`) | „?"-Hinweis daneben, darin bis zu zwei Verweise: „Mehr dazu" und „Zur Einstellung →" (offen aus **T-11e #3**) | ✅ [^8] | |
| 9 | Klick auf „Zur Einstellung →" | springt auf den zugehörigen Reiter, nicht nur auf die Seite | ✅ [^9] | |
| 10 | `npx vitest run` + `vue-tsc -b` | Tests grün, Typecheck sauber | ✅ [^10] | |
| 11 | Toast steht, Maus auf „Alle aktualisieren" | der Knopf ist anklickbar, nicht von der Meldung verdeckt | ✅ [^11] | |
| 12 | Dialog, Toast und „?"-Hinweis, hell **und** dunkel | jedes trägt einen sichtbaren Schatten, der Dialog den kräftigeren | ✅ [^12] | |

```bash
cd "${DEV_LOCAL}/DevWeb/Production/StockInfo/dashboard"
npx vitest run          # #10
npx vue-tsc -b --force  # #10

cd "${DEV_LOCAL}/DevWeb/Production/ux-foundation"
npx vitest run          # #10 — UxInfoHint, Schatten-Stufen
npm run typecheck       # #10
make check-themes       # #7 — meldet sepia als „in Ordnung", siehe Fußnote
```

[^1]: Gemessen statt geschaut: Oberkante der Assets-Karte vor dem Fehler
    `top: 128`, danach `top: 128`; waagrechter Überhang 0. Der Toast liegt
    `position: fixed` über allem.
[^2]: Drei Toasts standen rund **20 Minuten** unverändert. Wegklicken wirkt und
    hält: Nach dem ✕ kamen sie nicht wieder (`dismissed` im Composable).
[^3]: Backend gestoppt → Toast; Backend gestartet → „Alle aktualisieren" →
    der Toast ging **ohne Klick** in `notification-transition-leave-active`,
    und die Tabelle hatte wieder 5 Zeilen. Das Verschwinden selbst war nicht zu
    sehen: Der Automat läuft mit `document.visibilityState === 'hidden'`, dort
    feuert `requestAnimationFrame` nicht, und Vue-Übergänge bleiben bei
    `leave-from` stehen. Im echten Reiter ist das nicht so.
[^4]: Fünf Fehlerquellen gleichzeitig aktiv, im DOM standen **drei**
    (`NNotificationProvider :max="3"`).
[^5]: `.n-modal` vorhanden, `document.activeElement` war der Knopf mit
    `.confirm-delete__cancel` („Cancel"), Escape schloss den Dialog. Die zehn
    Unit-Tests sind erhalten — nur die Selektoren ziehen jetzt aufs `body`,
    weil Naive teleportiert. Nebenbei behoben: Der alte Fokus-Code rief
    `.focus()` auf einer **Komponenten-Instanz** auf und warf; der Fokus landete
    also nie auf „Abbrechen".
[^6]: Inhalt rollt in seinem eigenen Bereich (283 von 432 px sichtbar,
    `scrollTop > 0`), Adresszeile bleibt stehen, kein waagrechter Überhang.
    „URL kopieren" schaltete auf „kopiert ✓".
[^7]: **Reißt.** Gegen die *gerenderte* Leiste gemessen (0.85 Deckkraft über
    hellem Inhalt ⇒ `rgb(73 67 59)`), nicht gegen das Token:
    Wortmarke „Info" **4.15:1**, „powered by"-Verweis **2.27:1**,
    Trennpunkte/Version/Ampel **3.93:1** — verlangt sind 4.5:1.
    Menüpunkte (6.09) und Statuszeilen-Text (7.11) sind in Ordnung.
    `make check-themes` meldet `sepia` als „in Ordnung", weil es gegen den
    **Token** rechnet — genau die Falle, die der Skill beschreibt.
    → eigenes Ticket **T-14**.
    Der Knopf „Alle aktualisieren" stand nach dem Umzug in die Kopfzeile
    zunächst bei **1.38:1**; das ist in diesem Ticket behoben (siehe Auflösung),
    er liegt jetzt bei **9.06:1**.
[^8]: Zwei Hinweise gesetzt: `strict_exchange` (Environment) mit „Mehr dazu →"
    auf die Börsentabelle, „Pkt." (Assets-Tabelle) mit „Zur Einstellung →".
    **Kein einzelner Hinweis trägt beide** — an keiner der beiden Stellen hätte
    der zweite Verweis ein sinnvolles Ziel. Die Komponente kann beide, der
    Schaufenster-Block im Fundament zeigt das.
[^9]: Klick auf „Zur Einstellung →" landete auf `#/settings?tab=environment` —
    Seite **und** Reiter, nicht nur die Seite.
[^10]: Dashboard 155 Tests grün, `vue-tsc` sauber. Fundament 98 Tests grün,
    `typecheck` sauber. StockPortfolio (wegen `InfoHint`) 510 Tests grün.
[^11]: `elementFromPoint` auf der Knopfmitte traf vorher `n-notification-main`,
    jetzt den Knopf selbst.
[^12]: Dunkel (`mangolila`): Dialog `0.6 / 0.4`, Toast `0.45`, Hinweis `0.45`.
    Hell (`sepia`): Dialog `0.18 / 0.1`, Toast und Hinweis `0.12`.

---

## Ausgangslage

Aus T-12 übernommen, damit nichts verloren geht:

- **`NMessageProvider` und `NNotificationProvider` hängen bereits** in
  `App.vue`. Umzustellen sind die fünf Quellen in `errorSources` —
  Instrumente, Aktionen, Historie, Tagesdaten, Aktualisieren.
- Der Skill verlangt: Eine Meldung beschreibt einen **Zustand**, kein Ereignis
  — sie verschwindet, sobald ihre Ursache entfällt, und Weggeklicktes bleibt
  weg. Dafür gibt es `useStateNotification` im Fundament; StockPortfolio
  benutzt es bereits.
- **`ConfirmDeleteDialog`** trägt zehn Unit-Tests und eine eigene
  Fokus-Führung. Beim Umbau auf `NModal` müssen beide erhalten bleiben — der
  Dialog schützt vor unwiderruflichem Löschen samt Kurshistorie.
- **`JsonModal`** ist der einfachere Fall: Anzeige plus zwei Kopieren-Knöpfe.
- Verify #4 aus T-12 blieb ◑: Ein helles Theme mit umgekehrten Leisten wurde
  nicht live angesehen.

### Zu den „?"-Hinweisen (aus T-11e)

Der Skill verlangt: Erklärung dort, wo die Frage entsteht — zwei, drei Sätze am
Begriff, nicht eine Hilfeseite. Im Hinweis stehen bis zu zwei Verweise in einer
Zeile: **links** die Vertiefung, **rechts** die Stellschraube („Zur Einstellung
→"). Letzteres setzt voraus, dass die Reiter über die Adresse ansteuerbar sind
— das sind sie seit T-11a (`#/settings?tab=…`).

StockPortfolio hat das als `InfoHint.vue` gelöst; sobald StockInfo eine zweite
Fassung bräuchte, gehört die Komponente ins Fundament statt zweimal gebaut.
Kandidaten hier: `strict_exchange`, die Datenlage-Angaben und die
Environment-Herkunft.

---

## Auflösung

### Toasts statt Banner

`ErrorBanner.vue` und der Typ `ErrorEntry` sind entfallen; die fünf Quellen aus
`errorSources` hängen an `useNotifier` aus dem Fundament. Anzeigedauer `0` —
Fehler bleiben stehen, bis man sie wegklickt. Eine Einstellung dafür gibt es in
dieser App nicht, und eine Zahl im Code wäre eine geratene.

**`App.vue` ist dafür geteilt worden.** `useNotifier()` braucht einen
`NNotificationProvider` **über** sich; in derselben Komponente, die ihn erst im
Template aufspannt, findet `useNotification()` ihn nicht. `App.vue` ist jetzt
der Rahmen (Theme-Brücke, Locale, Provider), `AppDashboard.vue` der Inhalt —
dieselbe Aufteilung wie in StockPortfolio.

### Die Meldung verdeckte den Knopf, der sie behebt

Naive setzt Toasts 12 px unter den oberen Rand. Dort saß „Alle aktualisieren" —
gemessen von 76 bis 110 Pixel, also mitten unter der Meldung. Da Fehler stehen
bleiben, war ausgerechnet die Handlung unerreichbar, mit der man den Fehler
behebt. Weiter nach unten zu schieben half nicht: Dann liegt der Toast auf dem
Tabellenkopf.

Gelöst nach dem Skill statt gegen ihn: **„Alle aktualisieren" ist in die
Kopfzeile gezogen**, in die rechte Gruppe — dorthin gehört „die eine Handlung,
die überall gilt". Die Leiste über der Tabelle trägt jetzt nur noch das
Eingabefeld samt „Hinzufügen", links und auf 34 rem begrenzt. Die Toasts stehen
weiter rechts oben, beginnen aber bei `4 rem` (Kopfzeile 3.5 rem plus Naives
eigener Abstand).

Der Knopf brachte dabei ein neues Problem mit: Auf einer umgekehrten Leiste
(`sepia`) stand er mit **1.38:1** — unsichtbar. Naive bekommt global die Farben
des **Inhalts**, die Leisten haben aber eigene Token. Dafür gibt es jetzt
`buildBarNaiveOverrides()` im Fundament, eingehängt über einen zweiten
`NConfigProvider` um die `#actions`-Gruppe. Ergebnis: **9.06:1**.

Die Wiederholung „Overrides bauen, beim Theme-Wechsel neu lesen" steht seither
einmal in `useNaiveOverrides.ts` statt zweimal.

### Dialoge auf NModal

`ConfirmDeleteDialog` und `JsonModal` sitzen auf `NModal` mit `preset="card"`.
Rund achtzig Zeilen Nachbau sind entfallen — abdunkelnde Fläche, Escape, Klick
daneben, Fokus-Falle und Fokus-Rückgabe bringt Naive mit. Geblieben ist die
eine Entscheidung, die es nicht treffen kann: Der Fokus landet auf
**Abbrechen**.

Zwei Dinge, die erst im Browser auffielen:

- Beim Ausblenden leerte sich der Kasten, bevor er verschwand — der Inhalt hing
  direkt an `item`, und der Aufrufer setzt seine Auswahl sofort zurück. Beide
  Dialoge halten den Wert jetzt in einer eigenen Kopie bis `@after-leave`.
- Naive prüft bei Escape `e.code`, nicht `e.key`. Im Browser stehen beide, im
  Test nur das, was man setzt.

### „?"-Hinweise — die Komponente ist ins Fundament gezogen

`InfoHint.vue` lag in StockPortfolio; StockInfo brauchte dieselbe Sache, also
zieht sie um, statt ein zweites Mal zu entstehen. Im Fundament heißt sie
`UxInfoHint` und kennt weder Katalog noch Router: Wörter und Adressen kommen als
Props, und weil es Adressen sind, entstehen echte `a`-Elemente.

Beide Apps behalten eine dünne eigene Fassung, die Tabs bzw. Routen in Adressen
übersetzt und die Beschriftungen aus ihrem Katalog holt — dieselbe Aufteilung
wie bei `AppStatusBar`. Die Aufrufstellen in StockPortfolio sind unverändert.

Gesetzt in StockInfo: `strict_exchange` (der lange Beitext unter dem Wert ist
damit weg) und die Spalte „Pkt.". Letztere sitzt in einem sortierbaren
Spaltenkopf, deshalb `@click.stop` — sonst sortiert das Antippen des
Fragezeichens die Tabelle. Weil der Kopf dadurch breiter wurde, brach der Kurs
zweizeilig um; die Zahlenspalten tragen jetzt `white-space: nowrap` und die
Tabelle rollt lieber, als Zahlen zu zerlegen.

### Schatten (nachträglich, auf Zuruf)

Dialoge, Toasts und Hinweise trugen keinen Schatten und klebten damit auf der
Seite. Im Fundament stehen jetzt zwei Stufen als Token — `--shadow-sm` für
alles, was knapp schwebt, `--shadow-lg` für Dialoge —, gestaffelt nach der
**Helligkeit des Inhalts**: Schwarz auf Anthrazit ist fast nicht zu sehen,
derselbe Wert wirkt auf Papier zu kräftig. Vier Themes bekommen die schwache
Stufe (`paper`, `mono`, `sepia`, `meadow`), ein Test hält das an `THEMES`
fest.

Ein Fallstrick dabei: `Modal.boxShadow` allein bleibt wirkungslos, weil ein
Dialog mit `preset="card"` seinen Schatten aus dem **Card**-Theme holt. Gesetzt
wird er darum am Peer — so trägt die Karte *im Dialog* die starke Stufe,
während Karten im Inhalt bei der leisen bleiben.

### Was offen bleibt

Verify #7 reißt und ist damit **nicht** erledigt: In den Themes mit umgekehrten
Leisten (`sepia`, `meadow`) liegen Wortmarke, Akzent-Verweis und die leise Stufe
der Statuszeile unter 4.5:1. Die Ursache ist strukturell — die Leisten haben
eigene Token, der Akzent nicht —, und das Prüfskript im Fundament misst gegen
den Token statt gegen die gerenderte Fläche. Beides steht in **T-14**.

### Berührte Repos

| Repo | Was |
|---|---|
| `StockInfo/dashboard` | Toasts, beide Dialoge, Kopfzeile, Hinweise, `useNaiveOverrides` |
| `ux-foundation` | `UxInfoHint`, `buildBarNaiveOverrides()`, Schatten-Token, Schaufenster |
| `StockPortfolio` | `InfoHint.vue` auf die Fundament-Fassung umgestellt |
