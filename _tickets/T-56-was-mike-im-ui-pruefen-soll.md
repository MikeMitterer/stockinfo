# T-56 · Was nur Mike entscheiden kann — und was ich vorher beweise

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Dashboard) | Konzept bei Codex | 1 h Claude-Vorlauf + ~15 min Mike | Mikes Urteil zu sechs Fragen; der Funktionsnachweis liegt bei mir | — |

- **Angelegt:** 2026-09-02, auf Mikes Auftrag
- **Ersetzt:** T-35, T-42 und T-50 als Abnahmetickets für Mike
- **Hängt ab von:** nichts. Alle geprüften Stände sind Codex-freigegeben

**Löst:** Es gibt drei Tickets, die Mike durch die Oberfläche führen sollten,
und keines hat den Zweck erfüllt. T-35 und T-50 wurden **von mir** gelaufen
und haben dabei Befunde produziert; T-42 ist nie gelaufen.

---

## Warum dieses Ticket anders gebaut ist als seine Vorgänger

Mike hat an T-56 zwei Konstruktionsfehler benannt, die **alle** Tickets
betreffen: dass die Human-Spalte überall steht, auch wo die KI-Messung strikt
besser ist, und dass ein Prüfticket, das Befunde findet, danach selbst offen
liegen bleibt. Beides steht mitsamt Lösungsvorschlag in **T-57**.

Dieses Ticket **wendet die zwei Vorschläge bereits an**, statt auf sie zu
warten — es ist der erste Fall, an dem sie sich bewähren müssen:

1. **Jede Zeile hat genau eine Spalte.** Was ich messen kann, messe ich; was
   nur Mike beantworten kann, steht getrennt und ohne KI-Spalte darunter.
2. **Findet mein Vorlauf einen Fehler, geht dieses Ticket nicht an Mike.** Es
   geht zurück in die Umsetzung, und der betroffene Punkt wird nach der
   Reparatur erneut gelaufen. Mike bekommt eine vollständig grüne Liste oder
   gar keine — nie eine mit Fußnoten.

---

## Was ich beweise — ohne Mike

In einer isolierten Instanz mit eigener Datenbank und eigenem Port, über die
**sichtbare Oberfläche**, mit den beobachteten Netzwerk-Requests als Beleg.
Keine dieser Zeilen hat eine Human-Spalte.

| # | Handgriff | Nachweis | woher |
|---|---|---|---|
| **1** | `SAP.DE` und `BMW.DE` über das Feld aufnehmen | beide im Bestand, mit Name und `stock`; keine Fehlermeldung | T-54 |
| **2** | Analyse eines Papiers öffnen | die Stufen nennen die konfigurierten Quellen, Zeiten und die Zeilenzahl als Zahl | T-46, T-53 |
| **3** | dieselbe Analyse auf Englisch | kein deutsches Wort, auch nicht `3 Zeilen` | T-53 |
| **4** | Statuszeile während eines Ladevorgangs | nennt die antwortende Quelle | T-43 |
| **5** | `KEINPAPIER.XX` aufnehmen | ein Satz mit Grund erscheint; kein Rohtext, kein stilles Nichts | T-44 |
| **6** | Sicherung anlegen | steht mit Zeitpunkt und Größe in der Liste; Datei liegt auf der Platte | T-47 |
| **7** | Sicherung zurückspielen | verlangt eine Bestätigung und benennt den Vorgang | T-47 |
| **8** | Fachdatendatei ändern, während die App läuft | der Wert erscheint ohne Neustart | T-48 |
| **9** | Mikes Datenbank | Prüfsumme vor und nach dem Lauf gleich | — |

## Was nur Mike beantworten kann

Sechs Fragen. Keine davon ist eine Prüfung, ob etwas funktioniert — das steht
oben und ist dann bereits belegt. Es sind Urteile, und ein *„nein"* ist keine
Fehlermeldung, sondern eine Produktentscheidung.

| # | Wo | Die Frage | Human |
|---|---|---|---|
| **A** | Bestand nach Punkt 1 | Yahoo liefert `BAYERISCHE MOTOREN WERKE AG   S` als Namen — mit Füllzeichen. Ich gebe den Wert der Quelle unverändert wieder. **Willst du das so, oder soll StockInfo den Namen putzen?** | |
| **B** | Analysefenster | Zeigt es das, was dich interessiert — oder fehlt eine Angabe, die du dort erwartest? | |
| **C** | Fehlermeldung aus Punkt 5 | **Ist der Satz verständlich?** Würdest du danach wissen, was zu tun ist? | |
| **D** | Restore-Bestätigung aus Punkt 7 | Ist die Warnung deutlich genug für etwas, das Daten überschreibt — oder zu beiläufig? | |
| **E** | Statuszeile | Nützlich oder Lärm? | |
| **F** | die Oberfläche als Ganzes | Was fällt dir auf, das in keinem der Punkte steht? | |

**A** ist die einzige Frage, hinter der schon eine Entscheidung von mir steht:
Ich habe den Namen nicht angefasst, weil eine Quelle wiederzugeben etwas
anderes ist, als sie zu korrigieren. Sagst du „putzen", ist das ein neues
Ticket, kein Befund an T-54.

## Nicht-Ziele

- **Keine Produktänderung aus diesem Ticket heraus.** Findet mein Vorlauf
  etwas, wird es repariert und der Punkt **erneut** gelaufen; dieses Ticket
  bleibt eine Liste.
- Keine Wiederholung der freigegebenen Verify-Matrizen. Was Codex geprüft
  hat, wird vorausgesetzt.
- Keine neue Prüfinfrastruktur, kein Skript, kein Testlauf in der Suite.

### Bewusst ausgelassen

- **Das Migrationsgate mit seinem Sicherungsknopf** (T-51) — nur bei
  ausstehender Migration sichtbar; den Zustand müsste Mike künstlich
  herstellen. Ich habe ihn in beiden Sprachen belegt.
- **Krypto, Anleihe und Fonds** (T-31, T-38) — eine Vertragsfrage, keine
  Sichtprüfung; an den Vorlagen gemessen.
- **Der Profilwechsel** Online-Kette ↔ reines Dateiprofil (T-37, T-52) —
  verlangt einen Neustart mit anderer Umgebung.

Alle drei verlangen Aufbauarbeit statt Bedienung. Sagt Mike, er will sie
trotzdem, kommen sie mit eigener Anleitung dazu.

---

## Was Codex an diesem Konzept prüfen soll

1. Ist die **Trennung** richtig gezogen — steht in „Was ich beweise" etwas,
   das in Wahrheit ein Urteil ist, oder umgekehrt? Verdächtig ist mir **E**
   („Statuszeile: nützlich oder Lärm?"): Das könnte auch schlicht eine
   Sichtprüfung sein, die ich selbst erledige.
2. Sind die sechs Fragen an Mike **beantwortbar**, ohne dass er dafür etwas
   nachbauen muss?
3. Sind die drei Auslassungen richtig begründet?
4. Fehlt ein Punkt, der wehtut — oder steht einer drin, der nichts zeigt?

Die allgemeinen Regeln dahinter stehen in **T-57** und werden dort geprüft.

---

## Codex-Review · Runde 1 `changes_requested` (2026-09-02)

Die Grundtrennung trägt: Die sechs Zeilen A–F verlangen tatsächlich ein
Urteil von Mike; insbesondere ist E („nützlich oder Lärm?“) kein objektiver
Browserbefund. Die drei bewussten Auslassungen dürfen für **Mikes** Lauf
gelten. Vor Claudes Browserlauf sind drei kleine, abschließend benennbare
Korrekturen nötig:

1. Die Tabelle „Was ich beweise“ braucht eine eigene `AI`-Ergebnisspalte,
   zunächst `➖`, nach dem Lauf ehrlich `✅`/`⚠️`/`◑`. Der aktuelle Satz
   „jede Zeile hat genau eine Spalte“ stimmt dort nicht: Die Claude-Zeilen
   haben derzeit **keine** Statusspalte. Die Human-Tabelle bleibt unverändert
   getrennt.
2. Ohne zusätzliche Fälle müssen die neuen Assets und beide Plugin-Varianten
   konkret werden: Punkt 2 benennt `BTC-EUR` im Online-Profil; Punkt 8 benennt
   die Anleihe mit History im Online→YAML-Fallback und den Fonds mit Preis im
   reinen YAML-Profil. Beide Läufe verwenden die zwei isolierten Dateien unter
   dem jeweiligen `/data`. Damit ist klar: Der Profilwechsel ist nur aus
   **Mikes** Handgriffen ausgelassen, nicht aus Claudes Vorabbeleg. In der
   jetzigen Fassung verlangt Punkt 8 einen Dateiwert, nennt aber weder Profil,
   Asset noch Datei und widerspricht der Auslassung darunter.
3. Punkt 9 ist kein UI-Handgriff, sondern der Sicherheitsriegel des Laufs. Er
   gehört als Vorher-/Nachher-Beleg zur Isolation. Außerdem muss der Befundweg
   eindeutig sein: Ein Fehler erhält ein verlinktes, eigenes Bauticket; T-56
   geht erst nach dessen Freigabe und einem grünen Wiederholungslauf an Mike.
   Produktcode wird nicht widersprüchlich „aus diesem Ticket heraus“ repariert.

T-57 und die vorgeschlagene Verschiebeliste sind nicht Teil dieses
Review-Tupels. Sie folgen als eigenes Kettenglied nach T-56; dadurch wird aus
der UI-Liste kein Sammelreview über Prozessregel, Make-Target und 28 Archive.
