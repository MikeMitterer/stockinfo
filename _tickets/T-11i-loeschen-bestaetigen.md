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
| 1 | Assets-Tabelle (Desktop), `✕` klicken | Dialog erscheint, **nichts** wird gelöscht, bis bestätigt wird | ➖ | |
| 2 | Dialog | nennt Name **und** Symbol des Papiers sowie die Zahl der Kurspunkte, die verloren gehen | ➖ | |
| 3 | „Abbrechen" / `Escape` / Klick daneben | schließt ohne zu löschen; Liste unverändert | ➖ | |
| 4 | „Löschen" | löscht genau dieses eine Papier; Liste aktualisiert sich | ➖ | |
| 5 | Kartenliste (< 768 px), `✕` antippen | derselbe Dialog, gleiche Wege | ➖ | |
| 6 | Dialog auf < 768 px | passt ins Bild, kein waagrechtes Scrollen, Knöpfe ≥ 44 × 44 px | ➖ | |
| 7 | DevTools → Netzwerk | vor der Bestätigung geht **kein** `DELETE` an das Backend | ➖ | |
| 8 | Tastatur | Fokus landet im Dialog, `Tab` bleibt darin, `Escape` schließt | ➖ | |
| 9 | Sprache umschalten | alle Dialogtexte aus dem Katalog, DE **und** EN | ➖ | |

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
- [ ] Kein `DELETE` ohne Bestätigung (Verify #7)
- [ ] Dialog nennt Name, Symbol und die Zahl der verlorenen Kurspunkte
- [ ] Abbrechen, `Escape` und Klick auf die abdunkelnde Fläche brechen ab
- [ ] Wirkt in Tabelle **und** Kartenliste — ein Dialog, nicht zwei
- [ ] Fokus wird im Dialog gefangen und danach zurückgegeben
- [ ] Alle Texte im i18n-Katalog (de = Schema-Quelle, en zieht nach)

### Side-Effects
Kein Backend-Change — das Backend löscht weiterhin auf `DELETE`, nur die
Oberfläche fragt vorher. `useInstrumentActions.remove()` bleibt unverändert; die
Rückfrage sitzt davor.

### Auflösung
_(offen)_
