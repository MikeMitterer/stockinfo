# T-13 · Toasts statt Banner, Dialoge auf NModal

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | ready | ~3 h | UI-only | — |

**Löst:** Der Rest, den T-12 bewusst stehen ließ — Zustandsmeldungen als Toast
statt als Banner im Textfluss, und die beiden selbstgebauten Dialoge auf
`NModal`. Beides ändert Verhalten, das einzeln geprüft gehört, statt in der
großen Umstellung mitzulaufen. Dazu der letzte offene Punkt aus **T-11e**: die
„?"-Hinweise an erklärungsbedürftigen Begriffen.

<!--
  Repo:   frontend (dashboard/). Scope: UI-only, kein Backend-Change.
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
| 1 | Backend stoppen, „Alle aktualisieren" | Meldung als **Toast**; das Layout darunter springt **nicht** | | |
| 2 | Toast erscheint | bleibt stehen, bis er weggeklickt wird — Fehler verschwinden nicht von selbst | | |
| 3 | Backend wieder starten, erneut laden | Meldung verschwindet, sobald ihre **Ursache** entfällt | | |
| 4 | mehrere Fehler nacheinander | keine Stapel-Lawine; höchstens drei gleichzeitig | | |
| 5 | Asset löschen | Rückfrage als `NModal`, Escape schließt, Fokus liegt auf „Abbrechen" | | |
| 6 | JSON ansehen | `NModal`, Inhalt scrollt, Kopieren funktioniert weiter | | |
| 7 | Theme `sepia` (helle Fläche, dunkle Leisten) | Kopf- und Statuszeile lesbar, Wortmarke sichtbar (offen aus T-12 #4) | | |
| 8 | Fachbegriff (z.B. `strict_exchange`) | „?"-Hinweis daneben, darin bis zu zwei Verweise: „Mehr dazu" und „Zur Einstellung →" (offen aus **T-11e #3**) | | |
| 9 | Klick auf „Zur Einstellung →" | springt auf den zugehörigen Reiter, nicht nur auf die Seite | | |
| 10 | `npx vitest run` + `vue-tsc -b` | Tests grün, Typecheck sauber | | |

```bash
cd "${DEV_LOCAL}/DevWeb/Production/StockInfo/dashboard"
npx vitest run          # #8
npx vue-tsc -b          # #8
```

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
