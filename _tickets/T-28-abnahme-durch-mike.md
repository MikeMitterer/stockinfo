# T-28 · Abnahme durch Mike — grobe Tests am Ende

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo | sammelt | zu schätzen | Abnahme aus Nutzersicht, keine Detailprüfung | — |

**Löst:** Die Frage „ist das Ganze benutzbar geworden?" — einmal, am Ende, statt
Ticket für Ticket. Die `Human`-Spalte der Einzeltickets bleibt bis dahin leer.

**Hängt zunächst an:** dem nachweisbaren Plugin-MVP aus den bereits
freigegebenen Sockeln T-17, T-18, T-20, T-24 und T-21 bis Übergabe 3 sowie der
verbindlichen Kette **T-22 → T-27a → T-27b → T-23**.

T-28 bleibt das **letzte menschliche Abnahme-Gate**, aber seine Abhängigkeiten
wachsen nicht mehr automatisch. Nach T-23 werden T-19, die eingefrorenen
T-21-Übergaben 4A/4B, T-25, T-26 und T-29 bis T-34 einzeln eingeordnet:
**vor T-28 erforderlich** oder **ausdrückliches Follow-up**. Erst diese
dokumentierte Entscheidung bestimmt den endgültigen Abnahmeumfang.

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
| 15 | Datei-Plugin nach `data/plugins/` legen und neu starten | die Quelle erscheint in `/sources` und kann über den normalen REST-Weg ein Papier liefern | ➖ [^plugin_mvp] | |
| 16 | dasselbe Plugin als installiertes Entry-Point-Paket verwenden | es erscheint und arbeitet gleichwertig, ohne Datei im Daten-Volume | ➖ [^plugin_mvp] | |
| 17 | ein Papier über das Datei-Plugin aufnehmen | die Antwort durchläuft sichtbar Registry → Core → REST; kein separater Plugin-Endpunkt umgeht den Core | ➖ [^plugin_mvp] | |
| 18 | `/sources` ansehen | Reihenfolge und Konfigurationszustand stimmen; yfinance und justETF erscheinen als normale Registry-Quellen | ➖ [^plugin_mvp] | |
| 19 | Quellenreihenfolge in `sources.yaml` ändern und neu starten | `/sources` und der tatsächlich verwendete Provider folgen der neuen Reihenfolge | ➖ [^plugin_mvp] | |

_(wächst nur nach einer ausdrücklichen Scope-Entscheidung — je aufgenommenem
Ticket ein bis drei Zeilen, nicht mehr)_

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
[^plugin_mvp]: T-22, T-27a, T-27b und T-23 — Konfiguration, vollständiges
    Contract-Kit, strikt offline prüfbarer HTTP-Referenzweg und Registry mit
    Datei- sowie Entry-Point-Lader. Der Host-Harness von T-23 muss denselben
    Weg in-process vollständig durchlaufen.

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

T-28 wird in zwei Schritten erreicht:

1. Der Plugin-MVP T-22 → T-27a → T-27b → T-23 ist implementiert, von Codex
   freigegeben und beweist einen realen Weg Registry → Core → REST.
2. Danach werden alle offenen Plugin-Tickets inventarisiert. Für jedes wird
   festgehalten, ob es vor der Abnahme zwingend ist oder als Follow-up nach
   T-28 bleibt. Diese Einordnung entscheidet Mike auf Basis von Codex'
   Empfehlung; weder Ticketnummer noch bloße Zugehörigkeit zum Subprojekt
   reichen als automatischer Blocker.

Codex fordert Mike erst zur Abnahme auf, wenn diese Einordnung vollständig ist,
alle als zwingend eingestuften Tickets freigegeben sind und der gemeinsame
Stand auf `master` liegt. Neue Tickets erweitern T-28 nur durch eine ebenso
ausdrückliche Entscheidung.

---

## Inventar der offenen Tickets — Stand nach dem Plugin-MVP

*Angelegt Claude, 2026-08-28, nach der Freigabe von T-23 (`a9e49f9`). Schritt 1
oben ist damit erfüllt: Die Kette T-22 → T-27a → T-27b → T-23 ist freigegeben
und belegt den Lauf Registry → Core → REST über beide Ladewege.*

**Was das hier ist und was nicht.** Die Einordnung entscheidet Mike auf Basis
von **Codex'** Empfehlung — so steht es oben, und daran ändert dieser Abschnitt
nichts. Er liefert das **Inventar** darunter: welche Tickets es wirklich gibt,
woran jedes hängt und was es für die Abnahme bedeutet. Mikes Spalte bleibt
leer, bis er sie füllt.

**Der Bereich stimmt nicht.** Oben steht „T-29 bis T-34". Ein Ticket **T-34
existiert nicht** — weder im Board-Root noch unter `solved/`; die Zahl kommt
nur in dieser Aufzählung und in `STATUS.md` vor. Real offen sind T-29, T-30,
T-31, T-32 und T-33. Entweder ist die Obergrenze ein Vertipper, oder ein
geplantes Ticket wurde nie angelegt — das zu klären ist Teil der Einordnung,
weil ein Gate auf ein nicht existierendes Ticket nie erfüllbar wäre.

| Ticket | Hängt an | Was die Abnahme davon merkt | Vorschlag |
|---|---|---|:--:|
| **T-26** Detailfelder durchreichen | — | Ein Plugin darf neue Felder deklarieren; sie gehen in Persistenz, API, Override-Modell und Dashboard **verloren**. Der Vertrag sagt Erweiterbarkeit zu, die eine Schicht später endet — genau das, was T-28 aus Nutzersicht prüfen soll. | **Gate** |
| **T-32** Testdatenbank abschotten | — | Ein Dienst, der sich sein Repository selbst aus den Settings baut, landet im Test an der **Arbeitsdatenbank**. Bei einer Abnahme am laufenden Stack ist das ein Risiko für Mikes echte Daten, und es ist unabhängig und klein. | **Gate** |
| **T-33** Profil wechselt den Handelsplatz | T-21 Teil 3 | Das Ticket weist sich selbst T-28 zu („Gehört in: T-28, das finale Plugin-Gate"). Der `409` ist gebaut, die **Auflösung** nicht — und ein Profilwechsel ist der Normalfall, sobald es zwei Plugins gibt. Braucht **zuerst eine Entscheidung von Mike**, dann Arbeit. | **Gate**, nach Entscheidung |
| **T-19** Neu auflösen ohne Datenverlust | — | Eine falsche Auflösung ist heute nur per `DELETE` zu korrigieren, das Historie und Handpflege kostet. Schmerzhaft, aber ein Weg existiert; das Plugin-Versprechen hängt nicht daran. | Follow-up |
| **T-21 4A/4B** | eingefroren | Von Mike am 2026-08-27 ausdrücklich bis nach dem MVP zurückgestellt. Diese Zeile hält das nur fest. | Follow-up |
| **T-25** Quellenprofil wechseln | Design | Sicherung, Rotation und Wiederherstellung beim Profiltausch. Ein zweites Profil zu **haben** ist MVP, es sicher zu **tauschen** ist der Schritt danach — überschneidet sich fachlich mit T-33. | Follow-up |
| **T-29** Alias-Lebenszyklus | — | `symbol` ist abrufrelevant, steht aber in einer providerlosen Spalte. Mit **einer** aktiven Kursquelle trägt das; mit wechselnden Quellen wird es falsch. Erster Kandidat, falls Mike doch ein Gate ergänzen will. | Follow-up |
| **T-30** Plugin-deklarierte Börsenauskunft | — | Ein regionales Plugin kann seine MICs nicht mitbringen; der Katalog bleibt Core-Wissen. Begrenzt, was ein Plugin kann — nicht, ob der MVP läuft. | Follow-up |
| **T-31** Papiere ohne MIC | T-21 Teil 3 | Krypto, Index, Anleihe. Steht auf „Entscheidung ausstehend" und ist ohne Mikes Antwort nicht umsetzbar. | Follow-up, Entscheidung offen |

**Die eine Einschränkung aus Codex' Runde 6** gehört in dieselbe Abwägung: Der
Installationsweg nach `data/plugin-env/<hash>` ist maschinell belegt, aber es
gab **keinen echten Container-Image-Update-Lauf auf demselben Volume**. Genau
das ist der Grund, warum der Ordner unter `/data` liegt — die Zusage ist
begründet und getestet, aber nicht am echten `docker pull` gemessen. Eine Zeile
dafür in der Verify-Matrix unten wäre in zwei Minuten zu prüfen.

---

## Auflösung

_(offen)_
