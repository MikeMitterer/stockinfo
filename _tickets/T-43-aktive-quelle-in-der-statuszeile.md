# T-43 · Die aktive Kursquelle in der Statuszeile

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Dashboard) | offen | 1–2 h | die Statuszeile nennt die Quelle, von der die Kurse kommen | — |

- **Angelegt:** 2026-08-31, auf Mikes Wunsch während des T-42-Browserlaufs
- **Beauftragt von Mike:** „Zumindest in der Status-Zeile sollte stehen welches
  Plugin aktiv ist" — und auf die Rückfrage nach dem Umfang: **„Nur die
  Kursquelle"**
- **Hängt ab von:** nichts. Ändert nur die Anzeige
- **Warum ein eigenes Ticket:** Mikes Entscheidung. Der Wunsch kam im Lauf von
  T-42 auf; er braucht einen neuen Datenabruf im Frontend und fällt damit nicht
  unter die dortige Lockerung für Anzeigekorrekturen

**Löst:** Ein Betreiber sieht der Oberfläche nicht an, woher ihre Zahlen
kommen. Im T-42-Lauf musste ich `GET /sources` bei jedem Profilwechsel per
`curl` abfragen, um zu wissen, welche Kette gerade greift — ein Benutzer hat
dieses Werkzeug nicht. Steht die Quelle in der Statuszeile, beantwortet sich
die häufigste Frage beim Einrichten von selbst: *Nimmt er meine Konfiguration
überhaupt?*

**Gemessener Anlass:** Zweimal in T-35 und T-41 zeigte die Oberfläche Werte aus
einer anderen Quelle als der erwarteten, und beide Male fiel es erst auf, weil
ich die Herkunft eigens nachgeschlagen habe.

---

## Was angezeigt wird

```
StockInfo powered by MangoLila · 4 Papiere · Kurse: yaml-file
```

Die **erste einsatzbereite** Quelle der Rolle `quotes` — die, von der der
angezeigte Preis stammt, wenn nichts durchfällt.

**Bewusst nicht alle fünf Rollen.** Eine Statuszeile ist eine Zeile; die
vollständige Kette samt Gründen steht in `GET /sources` und gehört in die
Einstellungen, nicht neben den Papierzähler.

**Bewusst die erste und nicht die Kaskade.** Ob `yfinance +1` verständlicher
wäre als `yfinance`, ist offen — die Frage steht unten.

---

## Scope-Vertrag

- **Fachliche Änderungen:** keine. Kein Endpunkt, kein Vertrag, kein Schema.
- **Neue Flächen:** ein Composable, der `GET /sources` liest.
- **Berührte Bestandsdateien:** Statuszeile, ihre Verdrahtung, beide
  i18n-Kataloge, die zugehörigen Tests.
- **Budget:** höchstens 1 neue und 5 berührte Dateien, 250 Diff-Zeilen.
- **Nicht-Ziele:** keine Anzeige der übrigen vier Rollen, keine Diagnoseansicht,
  kein Polling, keine Änderung an `/sources` selbst.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise ·
➖ nicht geprüft. `AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | Statuszeile, YAML-Profil | dort steht `yaml-file` — dieselbe Quelle, die `GET /sources` für `quotes` an erster Stelle führt | ➖ | |
| **2** | Statuszeile, Online-Profil | dort steht `yfinance`; nach einem Profilwechsel ändert sich die Anzeige mit | ➖ | |
| **3** | keine Quelle einsatzbereit | die Zeile behauptet keine Quelle, sondern lässt die Angabe weg oder sagt es | ➖ | |
| **4** | `/sources` nicht erreichbar | die Statuszeile bleibt benutzbar; ein Fehlschlag beim Nebenabruf nimmt nicht die Seite mit | ➖ | |
| **5** | Tests | Composable und Anzeige sind je einzeln geprüft, ohne echtes Netz | ➖ | |

---

## Offen — eine Frage an Codex

Die Statuszeile nennt die **erste** Quelle. Seit T-41 ist sie der Kopf einer
Kaskade: Fällt sie durch, liefert die zweite. Ein Betreiber, der `yaml-file`
liest, während der Wert von `yfinance` kam, wäre falsch informiert — und
umgekehrt.

Zwei Möglichkeiten, und die Wahl gehört nicht mir allein:

1. **Die erste Quelle nennen** (Mikes Vorgabe). Kurz und in der überwiegenden
   Zahl der Fälle richtig.
2. **Die Kette andeuten** (`yfinance +1`). Ehrlicher über die Struktur, aber
   immer noch keine Aussage darüber, wer *diesen* Kurs geliefert hat.

Beides sagt nichts über die einzelne Antwort. Die trägt seit T-41 ihre Herkunft
selbst (`RawQuote.source`) — sie steht im Drilldown, nicht hier.

## Auflösung

_(offen)_
