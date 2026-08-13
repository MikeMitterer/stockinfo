# T-09 · Fehlende Asset-Kennzahlen händisch nachtragen (persistent)

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| root (backend + frontend + DB) | backlog | ~1 Tag | Feature (DB + API + UI) | — |

**Löst:** Nutzer-Finding — für Assets, die **nicht** über extraETF/justETF laufen,
sollen fehlende Kennzahlen (TER, Volatilität, Thesaurierend, …) **manuell im UI**
eingetragen werden und **persistent in der DB** bleiben.

<!--
  Repo:   cross — DB-Schema/Migration, /instruments-Update-Endpoint, UI-Editor.
  Scope:  Feature, mehrschichtig. Größer als ein UI-only-Ticket.
-->

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Asset ohne ETF-Quelle im UI | Felder TER/Vola/Thesaurierend etc. sind manuell editierbar | ➖ | |
| 2 | Nach Eingabe + Reload | Werte bleiben erhalten (aus DB gelesen, nicht überschrieben) | ➖ | |
| 3 | Nach Auto-Refresh der Kurse | Manuelle Werte werden **nicht** von leeren Provider-Daten überschrieben | ➖ | |
| 4 | DB | Neue Spalten/Tabelle für manuelle Overrides vorhanden (Migration) | ➖ | |

---

## Details

### Kontext / Ziel
Heute stammen ETF-Extras (TER, Vola, Thesaurierung, Provider …) aus justETF/
extraETF. Für Papiere ohne diese Quelle bleiben die Felder leer. Nutzer will sie
manuell pflegen — mit klarer Vorrang-Regel gegenüber (leeren) Provider-Daten.

### Offene Design-Fragen (vor Umsetzung klären)
- Override-Modell: separate „manual"-Werte, die Provider-Werte überschreiben, vs.
  Fallback nur bei leerem Provider-Wert?
- Kennzeichnung im UI, dass ein Wert manuell ist (Badge)?
- Welche Felder genau editierbar (TER, Vola, accumulating, Provider, Name, …)?

### Akzeptanzkriterien
- [ ] DB-Migration für manuelle Overrides
- [ ] API: Update-Endpoint für die Felder (Validierung)
- [ ] UI: Inline-Editor an den betroffenen Assets
- [ ] Persistenz über Refresh hinweg garantiert (Vorrang-Regel definiert)
- [ ] i18n DE + EN

### Side-Effects
Mehrschichtig (DB/API/UI). Refresh-Merge-Logik muss manuelle Werte respektieren
— sonst gehen Eingaben beim nächsten Kurs-Update verloren.

### Auflösung
_(offen — zuerst Design-Fragen klären, ggf. brainstorming-Skill)_
