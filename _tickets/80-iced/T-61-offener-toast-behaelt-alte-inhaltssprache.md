# T-61 · Offener Toast behält die alte Inhaltssprache

**Zurückgestellt auf Mikes Wunsch vom 2026-09-07.** Der seltene Sprachwechsel-
Sonderfall bleibt dokumentiert, ist aber derzeit nicht zur Bearbeitung vorgesehen.
Für Mike gibt es aktuell nichts zu prüfen oder zu erledigen.

Eine Wiederaufnahme erfolgt erst bei ausdrücklicher neuer Einplanung.
Ein Termin ist nicht festgelegt; der Fehler ist noch nicht behoben.

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Dashboard) | **zurückgestellt · minor · nicht blockierend** | ~1–2 h | Toast-Inhalt bei Live-Sprachwechsel | — |

- **Angelegt:** 2026-09-05, nach Mikes Einordnung von T-56 Runde 6
- **Priorität:** Minor-Bug; kein Gate für T-56, den MVP oder die aktive Kette

**Löst:** Wechselt die Sprache genau während ein Fehler-Toast offen ist, folgt
der Titel bereits der neuen Sprache, während der Inhalt in der Sprache des
auslösenden Ereignisses stehen bleibt. Der Toast soll danach vollständig der
aktiven Sprache folgen.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ bestätigt mit Einschränkung ·
◑ teilweise · ➖ keine Live-Verifikation.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI |
|---|---|---|:--:|
| 1 | Dashboard, offener Fehler-Toast | Fehler auf Deutsch auslösen, ohne Neuaufbau auf Englisch wechseln: Titel und Inhalt desselben Toasts sind englisch | ➖ |
| 2 | vertikaler StockInfo-Test | Der Fall läuft über `AppDashboard.vue` und die dort verdrahteten `errorSources`; ein früh übersetzter und damit eingefrorener Inhalt macht den Test rot | ➖ |
| 3 | Regression | Ein erst nach dem Sprachwechsel ausgelöster Toast sowie unveränderte Sprache bleiben korrekt | ➖ |

Der Ausgangsbefund ist in T-56 Runde 6 per DOM beobachtet: `Error` stand über
weiter deutschem Fließtext. Das bestätigt den Bug, ersetzt aber noch nicht den
grünen Nachweis dieses Tickets.

---

## Details

### Kontext / Ziel

`@mmit/ux-foundation` 0.8.0 löst den reaktiven Titel bereits korrekt auf. In
StockInfo wird der Fehlerinhalt dagegen vor der Übergabe an den Notifier als
fertiger Text erzeugt und bleibt deshalb am offenen Toast eingefroren.

Der Zeitpunkt ist ein Randfall und die Auswirkung eine kurzzeitig gemischte
Sprache. Mike hat ihn deshalb am 2026-09-05 ausdrücklich als Minor-Bug statt
als Blocker eingeordnet.

### Akzeptanzkriterien

- [ ] Titel und Inhalt eines offenen Fehler-Toasts folgen gemeinsam der
  aktiven Sprache.
- [ ] Ein vertikaler Dashboard-Test schützt genau diesen Live-Wechsel.
- [ ] Vor einem Produktedit werden Erzeuger und Verbraucher semantisch
  inventarisiert; der Einstiegsscope sind die sechs `errorSources` aus
  `AppDashboard.vue`, nicht pauschal alle 13 Composables mit Fehlerzustand.

### Side-Effects

Keine beabsichtigte Änderung an Fehlerkennungen, API-Verträgen oder Toasts,
die erst nach dem Sprachwechsel entstehen. T-61 bleibt außerhalb der aktiven
Prioritätskette und blockiert T-56 nicht.

### Auflösung

Zurückgestellt nach `postponed/` am 2026-09-07. Kein Abschluss und keine
zusätzliche Verifikation; Akzeptanzkriterien und bisherige Befunde bleiben erhalten.
