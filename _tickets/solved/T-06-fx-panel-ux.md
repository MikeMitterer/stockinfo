# T-06 · Devisen-Panel: Währungs-Dropdown + formatiertes Aktualisierungsdatum

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | ready | ~1.5 h | UI | — |

**Löst:** Vier Nutzer-Findings zum Devisen-Tab:
1. „Es braucht ein Drop-Down, um die Währung auszuwählen."
2. „Der aktuelle Wechselkurs muss angezeigt werden + Datum der letzten
   Aktualisierung."
3. „Kurszeit bricht um — Spalte zu schmal."
4. „Nachkommastellen des Wechselkurses in der Anzeige auf 3 reduzieren."

<!--
  Repo:   frontend (dashboard/src/components/FxPanel.vue)
  Scope:  UI. Backend /fx liefert bereits rate + quote_time + source + stale.
-->

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|-------|
| 1 | `#/fx`, Basis-/Zielwährung | Auswahl über **Dropdown** (bekannte Codes aus `/exchanges`-Währungen) statt Freitext | ✅¹ | ok    |
| 2 | `#/fx` nach Umrechnen | Wechselkurs klar/prominent angezeigt (ist bereits vorhanden — beibehalten) | ✅² | ok    |
| 3 | `#/fx` nach Umrechnen | „Letzte Aktualisierung" als **lesbares Datum** (nicht roher ISO-String) | ✅³ | ok    |
| 4 | `#/fx` | Freitext-Fallback bleibt möglich (exotische Codes) — oder bewusst verworfen | ✅⁴ | ok    |
| 5 | `#/fx` nach Umrechnen | Rate auf **3 Nachkommastellen** gerundet angezeigt (nicht `1.1527377367019653`) | ✅⁵ | ok    |
| 6 | `#/fx` nach Umrechnen | Kurszeit **bricht nicht um** / Spalte breit genug | ✅⁶ | ok    |

> ¹ **(CC):** live im Browser (2026-08-13, `#/fx`) — zwei `<select>` mit 21 Währungen aus `/exchanges`, sortiert, **`GBP`** (nicht `GBp`), keine Dubletten (read_page: AUD…ZAR).
> ² **(CC):** nach „Umrechnen" prominent „1 EUR = 1,155 USD"; Rohwert zusätzlich als `title`-Tooltip (Unit-Test).
> ³ **(CC):** Kurszeit lesbar formatiert — EN „Aug 13, 2026, 4:55 PM", DE „13.08.2026, 16:55" (kein roher ISO-String mehr).
> ⁴ **(CC):** Freitext **bewusst verworfen** — Design-Entscheidung „nur Dropdown" (Spec 2026-08-13). Exotische Codes wären ein separates Ticket.
> ⁵ **(CC):** Rate auf 3 Nachkommastellen — EN `1.155`, DE `1,155` (locale-abhängiges Trennzeichen).
> ⁶ **(CC):** Kurszeit einzeilig (`white-space: nowrap`), kein Umbruch bei Standard-Breite.

---

## Details

### Kontext / Ziel
Heute: zwei Freitext-Felder (3-Buchstaben-Code) + ⇄ + „Umrechnen". Rate und
`quote_time` werden nach dem Umrechnen bereits angezeigt — die Kurszeit aber als
roher ISO-String. Gewünscht: Währungswahl per Dropdown und ein lesbar
formatiertes „zuletzt aktualisiert".

### Akzeptanzkriterien
- [ ] Dropdown-Auswahl für Basis- und Zielwährung (Quelle: Währungen aus
      `/exchanges` + gängige FX-Codes; Duplikate entfernt)
- [ ] Kurszeit als lokalisiertes Datum/Uhrzeit (vue-i18n / `Intl.DateTimeFormat`),
      ohne Zeilenumbruch (Spaltenbreite/`white-space` anpassen)
- [ ] Rate in der Anzeige auf 3 Nachkommastellen gerundet (Rohwert bleibt intern)
- [ ] stale-Badge-Verhalten unverändert
- [ ] i18n: neue Labels DE + EN

### Side-Effects
Reine UI. Kein Backend-Change (Daten liegen im `/fx`-Response bereits vor).

### Auflösung
_(offen)_
