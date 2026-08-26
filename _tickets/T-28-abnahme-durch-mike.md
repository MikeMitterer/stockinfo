# T-28 · Abnahme durch Mike — grobe Tests am Ende

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo | sammelt | zu schätzen | Abnahme aus Nutzersicht, keine Detailprüfung | — |

**Löst:** Die Frage „ist das Ganze benutzbar geworden?" — einmal, am Ende, statt
Ticket für Ticket. Die `Human`-Spalte der Einzeltickets bleibt bis dahin leer.

**Hängt an:** allen Tickets des Plugin-Subprojekts. Derzeit sind das T-17 bis
T-27b sowie T-29 bis T-32. T-28 ist bewusst das **letzte Abnahme-Gate**,
auch wenn seine Nummer kleiner ist: Jedes später entstehende Ticket, das zum
Plugin-Subprojekt gehört, erweitert diese Abhängigkeit vor der Abnahme.

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

---

## Wie dieses Ticket zu lesen ist

Die Zeilen sind **grob**. Sie fragen nach dem, was jemand an der Oberfläche
sieht — nicht nach einzelnen Feldern, Zeitstempeln oder Codepfaden. Jede Zeile
soll sich in ein bis zwei Minuten am laufenden Stack beantworten lassen
(`make dev-up`, Backend `:8000`, Dashboard `:5173`), ohne dass jemand ein
Ticket nachlesen muss.

Die feine Prüfung ist an anderer Stelle schon passiert: Unit-Tests, die
Prüf-Scripts `T-NN-smoke.sh` und Codex' Review. Hier geht es um die Frage, ob
das Ergebnis im Alltag trägt.

Die `AI`-Spalte steht bewusst auf ➖ — diese Zeilen gehören dem Menschen. Wo
das Verhalten maschinell belegt ist, nennt die Fußnote das Ticket.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Ein europäisches Papier per ISIN aufnehmen (z.B. `IE00B4L5Y983`) | kommt an der erwarteten Börse in EUR herein, Kennzahlen sind gefüllt | ➖ [^t17] | |
| 2 | Dasselbe Papier später erneut ansehen | TER, Anbieter und Domizil stehen noch da — nichts ist über Nacht leer geworden | ➖ [^t17] | |
| 3 | Ein Papier aufnehmen, dessen ISIN nirgends auflösbar ist | die App sagt das verständlich, statt eine kaputte Zeile anzulegen | ➖ [^t17] | |
| 4 | Die Liste durchsehen, nachdem länger nichts angefasst wurde | keine Zeile trägt ein Symbol oder eine ISIN, die nicht zum Papier gehört | ➖ [^t17] | |
| 5 | `curl http://localhost:8000/fields` | nennt eine Vertragsversion und je Antworttyp die Felder — lesbar, ohne ins Repo zu schauen | ➖ [^t24] | |
| 6 | Ein Papier ansehen, dessen Kurs die Quelle ohne Währung meldet | die App sagt, dass sie keinen verwertbaren Kurs hat — statt eine Zahl ohne Währung anzuzeigen | ➖ [^t24] | |
| 7 | Kurs, Tagesreihe und Historie desselben Papiers nebeneinander | überall dieselbe Währung, nirgends eine leere Angabe | ➖ [^t24] | |
| 8 | Ein kanadisches oder japanisches Papier per ISIN aufnehmen (`CA7800871021`, `JP3633400001`) | kommt herein — an seiner Heimatbörse, in der dortigen Währung | ➖ [^t18] | |
| 9 | Ein außereuropäischer ETF in der Liste (z.B. `XIC.TO` per Symbol) | Anbieter ist gefüllt, nicht leer | ➖ [^t18] | |
| 10 | Ein europäisches Papier daneben (`IE00B4L5Y983`) | unverändert an der eingestellten Börse, in EUR — nichts ist ausgewandert | ➖ [^t18] | |
| 11 | Netzstecker ziehen (oder WLAN aus), ein bekanntes Papier abrufen | die App sagt „konnte nicht nachsehen" und nennt die Quellen — sie behauptet nicht, das Papier gäbe es nicht | ➖ [^t20] | |
| 12 | Netz wieder an, dasselbe Papier | kommt normal herein; nichts ist in der Zwischenzeit gelöscht oder überschrieben worden | ➖ [^t20] | |
| 13 | Nach dem Update einmal die Instrumentenliste durchsehen | alle Papiere sind noch da, mit ihrer Historie — die Umstellung auf die neue Identität hat nichts gekostet | ➖ [^t21] | |
| 14 | Umzugsbericht nach dem Update öffnen | jede nicht eindeutig zuordenbare Altzeile ist mit altem Symbol und Grund genannt; keine kaputte Zeile lebt im aktiven Bestand weiter | ➖ [^t21] | |

_(wächst mit jedem abgeschlossenen Ticket — je Ticket ein bis drei Zeilen,
nicht mehr)_

[^t17]: T-17 — Fehler im Antwortpfad. Maschineller Nachweis:
    `./_tickets/T-17-smoke.sh --run` (acht Checks) und
    `./_tickets/T-16-smoke.sh --run` (`#5c`), dazu zwölf Unit-Tests.
[^t24]: T-24 — REST-Core als Vertrag. Maschineller Nachweis: `tests/
    test_contract.py`, `tests/test_contract_openapi.py`,
    `tests/test_api_fields.py`, dazu die Währungstests in
    `test_quote_service.py`, `test_quote_cache.py` und
    `test_daily_history.py`. Zeile 6 ist im Alltag schwer herbeizuführen —
    sie tritt nur ein, wenn eine Quelle wirklich keine Währung nennt.
[^t18]: T-18 — Auflösung erreicht mehr Märkte. Maschineller Nachweis:
    `./_tickets/T-18-smoke.sh --run` (acht Checks, darunter genau diese drei
    Fälle), dazu die Resolver- und Provider-Tests. Zeile 10 ist die
    Gegenprobe: Die Kaskade darf europäische Papiere nicht auswandern lassen.
[^t20]: T-20 — Quellen antworten differenziert. Maschineller Nachweis:
    `./_tickets/T-20-smoke.sh --run` (zwei Läufe, Netz einmal offen und einmal
    abgeschnitten). Zeile 11 ist der Fall, der vorher als „gibt es nicht"
    ankam; Zeile 12 die Gegenprobe, dass der Ausfall nichts zerstört hat.
[^t21]: T-21 — Identität auf `(ticker, mic)` und migrieren-oder-ablehnen.
    Maschineller Nachweis: `./_tickets/T-21-smoke.sh --run`,
    `./_tickets/T-21b-smoke.sh --run` sowie die Migrations- und
    Endpunkttests. Zeile 14 prüft die bewusste Grenze: Eine nicht zuordenbare
    Altzeile bleibt im Bericht nachvollziehbar, aber nicht als ungültiger
    Instrumentdatensatz aktiv.

---

## Details

### Warum gesammelt statt einzeln

Eine Abnahme je Ticket würde denselben Handgriff zehnmal verlangen — ein Papier
aufnehmen, ansehen, aktualisieren — und jedes Mal in einer Zwischenversion, die
niemand behält. Am Ende zählt der Zustand, der bleibt.

Der Preis ist, dass ein Fehler länger unentdeckt bleiben kann. Dagegen stehen
die Prüf-Scripts und Codex' unabhängige Prüfung je Commit; sie fangen das ab,
was maschinell zu sehen ist. Was sie nicht beantworten, ist die Frage, ob sich
das Ergebnis richtig anfühlt — und die stellt sich sinnvoll nur einmal, am
fertigen Stand.

### Wann dieses Ticket dran ist

T-28 ist das letzte Ticket des Plugin-Subprojekts. Codex fordert Mike erst dann
zur Abnahme auf, wenn

* alle zum Subprojekt gehörenden Tickets — derzeit T-17 bis T-27b sowie T-29
  bis T-32 — abgeschlossen und von Codex freigegeben sind,
* später entdeckte Plugin-Folgetickets ebenfalls abgeschlossen oder
  ausdrücklich aus dem Subprojekt herausentschieden wurden und
* der gemeinsame Stand auf `master` liegt.

Vorher wächst hier nur die grobe Prüfliste. Die Ticketnummer bestimmt keine
Reihenfolge; die vollständige Abhängigkeitsmenge bestimmt den Zeitpunkt.

---

## Auflösung

_(offen)_
