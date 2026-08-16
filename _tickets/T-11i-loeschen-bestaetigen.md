# T-11i · Löschen eines Assets bestätigen lassen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | ready | ~2 h | UI-only | — |

**Löst:** Ein Klick auf `✕` löscht heute sofort und unwiderruflich — samt
Kurshistorie. Künftig fragt ein Dialog nach, nennt das betroffene Papier und
was verloren geht.

<!--
  Repo:   frontend (dashboard/). Status: ready. Scope: UI-only.
  Anlass: Am 2026-08-15 ist BRYN.DE (Berkshire Hathaway) während der
  Browser-Prüfung von T-11c verschwunden — ein einzelner Fehlklick genügt.
  Symbol + ISIN konnten wiederhergestellt werden, die Historie nicht (8 → 1 Punkt).
  Entscheid Mike: Dialog mit Namen, nicht zweistufiger Knopf, kein natives confirm().
-->

---

## Verify

Legende: ✅ live bestätigt · ⚠️ bestätigt mit Einschränkung (Fußnote) ·
◑ teilweise (Fußnote) · ➖ keine Live-Verifikation (nur Unit/Review).
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

**Voraussetzung:** Stack läuft (`make dev-up`) — Backend `:8000`, Dashboard `:5173`.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Assets-Tabelle (Desktop), `✕` klicken | Dialog erscheint, **nichts** wird gelöscht, bis bestätigt wird | ✅¹ | |
| 2 | Dialog | nennt Name **und** Symbol des Papiers sowie die Zahl der Kurspunkte, die verloren gehen | ✅² | |
| 3 | „Abbrechen" / `Escape` / Klick daneben | schließt ohne zu löschen; Liste unverändert | ✅³ | |
| 4 | „Löschen" | löscht genau dieses eine Papier; Liste aktualisiert sich | ➖⁴ | |
| 5 | Kartenliste (< 768 px), `✕` antippen | derselbe Dialog, gleiche Wege | ✅⁵ | |
| 6 | Dialog auf < 768 px | passt ins Bild, kein waagrechtes Scrollen, Knöpfe ≥ 44 × 44 px | ✅⁶ | |
| 7 | DevTools → Netzwerk | vor der Bestätigung geht **kein** `DELETE` an das Backend | ✅⁷ | |
| 8 | Tastatur | Fokus landet im Dialog, `Tab` bleibt darin, `Escape` schließt | ✅⁸ | |
| 9 | Sprache umschalten | alle Dialogtexte aus dem Katalog, DE **und** EN | ✅⁹ | |

**Messweise:** 375-px-iframe auf derselben Seite (Chrome lässt das Fenster auf
macOS nicht unter ~600 px). `window.fetch` im Rahmen wurde protokolliert, um
Zeile 7 zu belegen statt zu behaupten.

> ¹ **(CC):** Klick auf `✕` bei APC.DE öffnet den Dialog; Tabelle bleibt bei
> 5 Zeilen. **Netz-Mitschnitt unmittelbar nach dem Klick: leer.**
> ² **(CC):** „Asset löschen? · Apple Inc. · APC.DE · 3 Kurspunkte gehen
> verloren. · Das lässt sich nicht rückgängig machen."
> ³ **(CC):** alle drei Wege geprüft — `Escape`, Klick auf die abdunkelnde
> Fläche und „Abbrechen" schließen jeweils; Klick **innerhalb** des Dialogs
> schließt **nicht**. Danach weiterhin 5 Zeilen.
> ⁴ **(CC):** ➖ **bewusst nicht ausgelöst.** Ein echtes Löschen hätte erneut
> Nutzerdaten samt Historie vernichtet — genau der Vorfall, der dieses Ticket
> ausgelöst hat. Der Pfad ist unit-getestet (Klick auf „Löschen" emittiert
> `confirm`) und in `App.vue` ist `remove()` nur noch aus `confirmRemoval()`
> erreichbar. **Für den Menschen:** an einem entbehrlichen Papier bestätigen.
> ⁵ **(CC):** in der Kartenliste (371 px) öffnet `✕` denselben Dialog — es gibt
> nur einen, die Rückfrage sitzt in `App.vue`, nicht in den Listen.
> ⁶ **(CC):** Dialog 323 px breit bei 371 px Viewport (24–347), Überlauf 0;
> Knöpfe „Abbrechen" 105 × 44 und „Löschen" 90 × 44.
> ⁷ **(CC):** `window.fetch` im Rahmen protokolliert. Über die gesamte Prüfung
> (Öffnen, Abbrechen, Escape, Backdrop, mobil, Sprachwechsel) **kein einziges
> `DELETE`** — nur der normale `/health`-Puls.
> ⁸ **(CC):** Fokus springt beim Öffnen auf **Abbrechen** (ein versehentliches
> Enter bricht ab, statt zu löschen); `Shift+Tab` vom ersten Element springt auf
> das letzte (Falle greift); nach `Escape` liegt der Fokus wieder auf dem
> auslösenden `✕`. `aria-modal="true"`, `aria-labelledby` gesetzt.
> ⁹ **(CC):** Englisch geprüft — und die **Einzahl** stimmt: BRYN.DE (1 Punkt)
> ergibt „1 price point will be lost", nicht „1 price points". Deutsch analog
> mit 3 Punkten in der Mehrzahl.

---

## Details

### Kontext / Ziel
Skill `ux-standards`: Zustandsmeldungen sind Toasts, aber eine **Rückfrage vor
einer unwiderruflichen Handlung** ist ein Dialog — sie verlangt eine Entscheidung,
statt einen Zustand zu melden. Kein natives `window.confirm()`: blockiert die
Seite, sieht auf jedem System anders aus, lässt sich nicht übersetzen und nicht
gestalten.

Im Projekt gibt es mit `JsonModal.vue` bereits ein Dialog-Muster — daran
anlehnen, statt ein zweites zu erfinden.

### Akzeptanzkriterien
- [x] Kein `DELETE` ohne Bestätigung (Verify #7, per Netz-Mitschnitt belegt)
- [x] Dialog nennt Name, Symbol und die Zahl der verlorenen Kurspunkte
- [x] Abbrechen, `Escape` und Klick auf die abdunkelnde Fläche brechen ab
- [x] Wirkt in Tabelle **und** Kartenliste — ein Dialog, nicht zwei
- [x] Fokus wird im Dialog gefangen und danach zurückgegeben
- [x] Alle Texte im i18n-Katalog (de = Schema-Quelle, en zieht nach), Mehrzahl korrekt
- [ ] Human-Abnahme — insbesondere Zeile 4 (echtes Löschen)

### Side-Effects
Kein Backend-Change — das Backend löscht weiterhin auf `DELETE`, nur die
Oberfläche fragt vorher. `useInstrumentActions.remove()` bleibt unverändert; die
Rückfrage sitzt davor.

**Umsetzung ohne Anfassen der Listen:** Tabelle und Karte melden `remove` ohnehin
beide an `App.vue`. Dort wird jetzt nicht mehr sofort gelöscht, sondern das Papier
gemerkt und der Dialog geöffnet. `InstrumentsTable.vue` und `InstrumentCard.vue`
sind **unverändert** — dadurch kann es die Rückfrage gar nicht zweimal geben und
kein Pfad kann sie umgehen.

**Über die Vorlage hinaus:** `JsonModal.vue` fängt den Fokus nicht ein. Der neue
Dialog tut es und gibt ihn beim Schließen zurück; der Startfokus liegt auf
*Abbrechen*, damit ein versehentliches Enter abbricht statt zu löschen. Das wäre
ein sinnvoller Nachzug für `JsonModal` (eigenes Ticket, hier bewusst nicht
mitgemacht).

### Auflösung
Branch `t-11i-loeschen-bestaetigen` (gestapelt auf `t-11c`), Commit `60aac2b`.
Neu: `ConfirmDeleteDialog.vue` + 10 Unit-Tests; `App.vue` verdrahtet;
`confirmDelete`-Block in beiden Katalogen. 147 Tests grün, Build sauber.
**Offen:** Human-Abnahme, insbesondere das tatsächliche Löschen (Zeile 4) —
das habe ich bewusst nicht ausgelöst.
