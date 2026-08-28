# T-35 · Die Oberfläche am laufenden Stack prüfen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Dashboard + Backend) | offen | 3 h | Anlegen, Anzeigen, Ändern, Löschen, Cache — im Browser, gegen echte Quellen | — |

- **Angelegt:** 2026-08-28, nach der Freigabe des Plugin-MVP (`a9e49f9`)
- **Beauftragt von Mike, 2026-08-28:** „erstelle ein Ticket bei dem du dir
  zuerst überlegst welche wichtigen UI tests du machen kannst … Führe dann die
  UI tests selbständig durch."
- **Hängt ab von:** nichts. Prüft den freigegebenen Stand, ändert ihn nicht
- **Plugin-Vorgabe Mike:** es läuft die Kette, **die auf YFinance zugreift** —
  `openfigi` → `yahoo-search` für die Auflösung, `justetf` → `yfinance` für
  ETF-Kennzahlen, `yfinance` für Kurs, Tagesreihe und Devisen

**Löst:** 795 grüne Tests sagen nichts darüber, ob die Oberfläche trägt. Sie
prüfen Funktionen, nicht den Weg, den ein Mensch tatsächlich geht — und genau
dort ist bisher **kein einziges Mal** gemessen worden. Die `AI`-Spalte in T-28
steht durchgehend auf ➖: „keine Live-Verifikation".

Dieses Ticket schließt die Lücke nicht für T-28 — die Abnahme bleibt Mikes.
Es beantwortet die Vorfrage: **Hält der Stand einer Bedienung überhaupt
stand, bevor ein Mensch seine Zeit investiert?**

---

## Was geprüft wird und warum gerade das

Mike hat fünf Bereiche genannt. Sie sind hier zu einem Durchlauf verbunden,
weil sie aufeinander aufbauen: Was nicht angelegt wurde, kann man nicht
ändern, und was nicht in der Datenbank steht, kann kein Cache liefern.

**Der Prüfstand ist eine eigene Datenbank.** Nicht `data/stockinfo.db` —
darin liegen Mikes echte Papiere, 638 KB seit dem 19. August. Ein Testlauf,
der anlegt, ändert und löscht, hat dort nichts verloren; das ist genau die
Gefahr, die T-32 beschreibt. Der Lauf bekommt deshalb ein eigenes Volume,
und weil es leer startet, ist jede Zeile darin nachweislich aus diesem Lauf.

**Gemessen wird an zwei Stellen zugleich.** Was das Dashboard zeigt, ist eine
Behauptung; was in SQLite steht, ist der Zustand. Eine Prüfung, die nur auf
die Oberfläche sieht, kann einen Wert bestätigen, der nie gespeichert wurde —
und eine, die nur in die Datenbank sieht, übersieht, dass ihn niemand zu
sehen bekommt. Jede Zeile unten nennt deshalb beides.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ nicht geprüft.
`AI` = im Browser durch Claude · `Human` = Mike (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | `GET /sources` am laufenden Dienst | die von Mike vorgegebene Kette steht da und ist einsatzbereit: `openfigi`, `yahoo-search`, `justetf`, `yfinance` — jede mit `configured: true`. Keine Rolle meldet „noch nicht gebaut" | | |
| **2** | Dashboard `:5173`, Papier per ISIN anlegen (`IE00B4L5Y983`) | die Zeile erscheint **ohne Reload**, mit Name, Börse und Währung EUR | | |
| **2b** | dieselbe Aufnahme, SQLite | genau **eine** Zeile in `instruments`, ISIN und `(ticker, mic)` gesetzt — kein Platzhalter, kein `NULL` in der Identität | | |
| **3** | dasselbe Papier in der Oberfläche öffnen | Kurs mit Währung, TER und Anbieter sind gefüllt. Das belegt die **Kette**: Kurs von yfinance, TER von justETF — zwei verschiedene Quellen in einer Ansicht | | |
| **4** | ein US-Papier daneben (`US0378331005`, Apple) | kommt in **USD** an seiner Heimatbörse herein, nicht in EUR an Xetra. Die Gegenprobe zu `#2`: die Kaskade lässt europäische Papiere nicht auswandern und amerikanische nicht einwandern | | |
| **5** | eine ISIN, die nirgends auflösbar ist (`XX0000000000`) | die Oberfläche sagt es verständlich, und in `instruments` steht danach **keine** neue Zeile. Eine kaputte Zeile ist teurer als eine abgelehnte Eingabe | | |
| **6** | ein benutzerpflegbares Feld ändern (z.B. TER von Hand) | der neue Wert steht sofort in der Ansicht | | |
| **6b** | dasselbe Feld, SQLite | der Wert steht in der Override-/Detailtabelle — **nicht** in der Quellenspalte. Der Unterschied ist der Kern: Handpflege darf beim nächsten Abruf nicht überschrieben werden | | |
| **6c** | nach `#6b` erneut abrufen | die Handpflege **überlebt** den Abruf. Genau das ist der Fall, den T-28 Zeile 2 als „nichts ist über Nacht leer geworden" beschreibt | | |
| **7** | denselben Kurs zweimal hintereinander abrufen | der zweite Abruf kommt **aus dem Cache**: messbar schneller, und im Protokoll steht kein zweiter Netzaufruf | | |
| **7b** | Cache-Zeitstempel in SQLite | `fetched_at` o. ä. ist beim zweiten Abruf **unverändert** — der sichere Beleg. Antwortzeit allein kann täuschen, ein unveränderter Zeitstempel nicht | | |
| **8** | Papier löschen | verschwindet aus der Liste **und** aus `instruments`; die zugehörigen Kurszeilen bleiben nicht als Waisen zurück | | |
| **9** | Browser-Konsole über den ganzen Lauf | keine Fehler, keine fehlgeschlagenen Requests, keine Warnung über fehlende Felder | | |

_(Die `Human`-Spalte bleibt leer — sie gehört Mike.)_

---

## Was dieses Ticket ausdrücklich nicht tut

- **Es ändert keinen Produktcode.** Findet der Lauf etwas, wird es hier
  aufgeschrieben und bekommt ein eigenes Ticket. Ein Befund, der im selben
  Lauf repariert wird, ist nicht mehr unabhängig belegt.
- **Es ersetzt T-28 nicht.** Ob sich das Ergebnis richtig *anfühlt*, kann
  niemand außer Mike beantworten.
- **Es baut keine Testinfrastruktur.** Kein Playwright, kein Selenium, keine
  Fixtures — ein Browser, der laufende Stack und die echten Quellen. Der
  Testinfrastruktur-Riegel gilt.

---

## Auflösung

_(offen — wird nach dem Lauf gefüllt)_
