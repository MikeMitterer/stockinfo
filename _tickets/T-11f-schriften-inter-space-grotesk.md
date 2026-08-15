# T-11f · Schriften: Inter + Space Grotesk, gebündelt

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | backlog | ~2 h | UI-only | — |

**Löst:** Mitgelieferte Schriften statt Systemschrift — **Inter** (`--font-ui`:
Oberfläche, Fließtext, **alle Zahlen**) und **Space Grotesk** (`--font-display`:
Wortmarke, Seitentitel, Abschnittsüberschriften). Einbindung über `@fontsource`
(npm), **nichts vom CDN**. Teil-Ticket von **T-11** — neu aus dem Skill-Stand
2026-08-15 (Abschnitt „Schrift" + „Nichts wird nachgeladen").

<!--
  Repo:   frontend (dashboard/). Status: backlog. Scope: UI-only.
  Entscheid Mike (2026-08-15): Inter + Space Grotesk gilt.
  Die Skill-Passage "Die Marke" (Orbitron + Systemschrift) ist veraltet —
  Skill-Bereinigung an Mike gemeldet.
-->

---

## Verify

Legende: ✅ live · ⚠️ Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | App, DevTools → Computed | Fließtext/Zahlen in **Inter**; Wortmarke/Titel in **Space Grotesk** | ➖ | |
| 2 | DevTools-Konsole: `performance.getEntriesByType('resource').filter(r => !r.name.startsWith(location.origin))` | **leer** bis auf die eigene API — keine fremde Schrift-/CDN-Anfrage | ➖ | |
| 3 | Tabellen mit Zahlen | Zahlen bleiben in `--font-ui`, `tabular-nums`; Spalten springen beim Aktualisieren nicht | ➖ | |
| 4 | Bundle | nur `latin`-Teilmenge, variabel (`font-weight: 100 900`), Richtwert ~69 KB für beide Familien | ➖ | |
| 5 | Gewichte | nur 400 / 500 / 600 im Einsatz — **kein 700** (heute in 6 Dateien vorhanden) | ➖ | |

---

## Details

### Kontext / Ziel
Skill: „Eine mitgelieferte Schrift, **nicht** die des Betriebssystems" — die
Systemschrift ist keine Vorgabe, sondern deren Abwesenheit (SF Pro / Segoe UI /
Roboto = drei Metriken). Zahlen wechseln **nie** die Familie. Schriftwahl wird
nicht zur Auswahl gestellt (keine Schrift je Theme).

Größen/Gewichte laut Skill-Tabelle: Wortmarke `--font-lg`/600; Menüpunkt und
Reiter `--font-sm`/400 (bewusst zurückhaltend, keine Großbuchstaben);
Abschnittsüberschrift `--font-xs`/500 in Großbuchstaben, Laufweite +0.025em;
Tabellenzelle `--font-sm`/400; Kennzahl-Wert `--font-base`/600.

### Akzeptanzkriterien
- [ ] `@fontsource-variable/inter` + Space Grotesk als npm-Abhängigkeit, keine `<link>`-Einbindung
- [ ] `--font-ui` / `--font-display` als Token; Systemschrift nur als Rückfallkette
- [ ] Zahlen in `--font-ui` + `tabular-nums`
- [ ] Gewicht 700 aus dem Bestand entfernt (400/500/600)
- [ ] Ressourcen-Check (Verify #2) leer

### Side-Effects
Kein Backend-Change. Bundle wächst um ~69 KB (nur `latin`). Sinnvoll **nach**
T-11b (Token/Skalen stehen dann), unabhängig von T-11d.

### Auflösung
_(offen)_
