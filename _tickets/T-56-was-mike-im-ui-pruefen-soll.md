# T-56 · Was nur Mike entscheiden kann — und was ich vorher beweise

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Dashboard) | Konzept freigegeben nach Runde 1, Vorlauf offen | ~2 h Claude-Vorlauf (zwei Profile) + ~15 min Mike | Mikes Urteil zu sechs Fragen; der Funktionsnachweis liegt bei mir | — |

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

1. **Jede Zeile trägt genau eine entscheidende Spalte** — `AI` **oder**
   `Human`, nie beide. Was ich messen kann, messe ich; was nur Mike
   beantworten kann, steht getrennt darunter.
2. **Findet mein Vorlauf einen Fehler, geht dieses Ticket nicht an Mike.**
   Der Weg dafür ist unten unter *Was passiert, wenn mein Vorlauf etwas
   findet* festgelegt. Mike bekommt eine vollständig grüne Liste oder gar
   keine — nie eine mit Fußnoten.

---

## Was ich beweise — ohne Mike

Über die **sichtbare Oberfläche**, mit den beobachteten Netzwerk-Requests als
Beleg. Keine dieser Zeilen hat eine Human-Spalte; die `AI`-Spalte steht bis
zum Lauf auf `➖` und danach auf dem, was herausgekommen ist — nicht auf dem,
was herauskommen sollte.

**Zwei Läufe, zwei isolierte Instanzen**, jede mit eigener Datenbank, eigenem
Port und eigener Fachdatei unter ihrem `/data`:

- **O** — das Online-Profil mit YAML als letztem Rückfall
  (`examples/sources-fallback.yaml` + `examples/assets-fallback.yaml`)
- **Y** — das reine Dateiprofil
  (`examples/sources-standalone.yaml` + `examples/assets-standalone.yaml`)

| # | Lauf | Handgriff | Nachweis | woher | AI |
|---|:--:|---|---|---|:--:|
| **1** | O | `SAP.DE` und `BMW.DE` über das Feld aufnehmen | beide im Bestand, mit Name und `stock`; keine Fehlermeldung | T-54 | ➖ |
| **2** | Y | Analyse von **`BTC-EUR`** öffnen (`pair`, `BTC`/`EUR`) | die Stufen nennen die konfigurierten Quellen, Zeiten und die Zeilenzahl als Zahl | T-46, T-53, T-31 | ➖ |
| **3** | Y | dieselbe Analyse auf Englisch | kein deutsches Wort, auch nicht `3 Zeilen` | T-53 | ➖ |
| **4** | O | Statuszeile während eines Ladevorgangs | nennt die antwortende Quelle | T-43 | ➖ |
| **5** | O | `KEINPAPIER.XX` aufnehmen | ein Satz mit Grund erscheint; kein Rohtext, kein stilles Nichts | T-44 | ➖ |
| **6** | O | Sicherung anlegen | steht mit Zeitpunkt und Größe in der Liste; Datei liegt auf der Platte | T-47 | ➖ |
| **7** | O | Sicherung zurückspielen | verlangt eine Bestätigung und benennt den Vorgang | T-47 | ➖ |
| **8a** | O | in `assets-fallback.yaml` die **History der Anleihe** `DE0001102531` ändern, während die App läuft | der Wert erscheint ohne Neustart — und zwar über den YAML-Rückfall **hinter** der Online-Kette | T-48, T-37 | ➖ |
| **8b** | Y | in `assets-standalone.yaml` den **Preis des Fonds** `DE0009848119` ändern, während die App läuft | derselbe Nachweis im reinen Dateiprofil | T-48, T-52 | ➖ |

**Damit ist der Profilwechsel nur aus Mikes Handgriffen ausgelassen, nicht
aus meinem Vorabbeleg.** Codex hat den Widerspruch in der ersten Fassung
benannt: Punkt 8 verlangte einen Dateiwert, nannte aber weder Profil noch
Papier noch Datei — und stand damit gegen die Auslassung weiter unten. Die
drei Identitätsformen fallen dabei ohne einen einzigen zusätzlichen Fall mit
ab: `pair` in Punkt 2, `isin_only` in 8a und 8b, `listed` in Punkt 1.

### Der Riegel, der kein Handgriff ist

Mikes Betriebsdatenbank wird nicht angefasst. Das ist keine Verify-Zeile,
sondern die Bedingung, unter der der Lauf überhaupt stattfindet:
`shasum -a 256 data/stockinfo.db` **vor** und **nach** beiden Läufen, beide
Werte im Bericht. Weichen sie ab, ist der Lauf ungültig — unabhängig davon,
wie die neun Zeilen ausgegangen sind.

Der Grund, das ausdrücklich hinzuschreiben: Bei T-50 hatte ich eine
Abweichung, und sie stammte aus einer veralteten Vergleichsbasis. Ein Riegel,
den man im Zweifel wegdiskutiert, ist keiner.

### Was passiert, wenn mein Vorlauf etwas findet

Kein Punkt bekommt eine Fußnote, und nichts wird „aus diesem Ticket heraus"
repariert:

1. Der Befund wird ein **eigenes Bauticket**, hier verlinkt.
2. Dieses Bauticket durchläuft den normalen Weg bis zu Codex' Freigabe.
3. Danach laufe ich den betroffenen Punkt **erneut**.
4. **Erst wenn alle neun Zeilen grün sind**, geht T-56 an Mike.

T-56 bleibt dabei durchgehend eine Liste. Es baut nichts, und es wartet nicht
als offenes Ticket auf die Reparatur — es geht in die Wiederholung.

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

- **Keine Produktänderung aus diesem Ticket heraus** — auch nicht als kleine
  Korrektur nebenbei. Ein Befund wird ein eigenes Bauticket; der Weg steht
  oben.
- Keine Wiederholung der freigegebenen Verify-Matrizen. Was Codex geprüft
  hat, wird vorausgesetzt.
- Keine neue Prüfinfrastruktur, kein Skript, kein Testlauf in der Suite.

### Aus **Mikes** Handgriffen ausgelassen

Die Überschrift ist der Punkt: Ausgelassen heißt hier *nicht ungeprüft*,
sondern *nicht von Mike auszuführen*.

| Bereich | warum nicht bei Mike | wo es trotzdem belegt ist |
|---|---|---|
| **Das Migrationsgate mit seinem Sicherungsknopf** (T-51) | nur bei ausstehender Migration sichtbar; den Zustand müsste er künstlich herstellen | im T-51-Browserlauf, beide Sprachen |
| **Krypto, Anleihe und Fonds** (T-31, T-38) | drei Identitätsformen sind eine Vertragsfrage, keine Sichtprüfung | an den Vorlagen gemessen — und in meinem Vorlauf: `pair` in Punkt 2, `isin_only` in 8a/8b |
| **Der Profilwechsel** Online ↔ reines Dateiprofil (T-37, T-52) | verlangt einen Neustart mit anderer Umgebung | **beide Profile laufen in meinem Vorlauf** (O und Y) |

Alle drei verlangen von Mike Aufbauarbeit statt Bedienung. Sagt er, er will
sie trotzdem selbst sehen, kommen sie mit eigener Anleitung dazu.

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

---

## Runde 1 · Die drei Korrekturen (Claude, 2026-09-02)

Alle drei angenommen; keine davon war Geschmack.

**1 · Die Claude-Zeilen hatten gar keine Spalte.** Mein Satz „jede Zeile hat
genau eine Spalte" beschrieb einen Zustand, den das Ticket nicht hatte: Die
Human-Tabelle trug eine Spalte, meine Tabelle **keine**. Ein Ergebnis ohne
Feld, in das es geschrieben wird, ist eine Absicht, keine Prüfung. Die neun
Zeilen tragen jetzt eine `AI`-Spalte auf `➖`, und der Satz sagt, was er
meint: *eine entscheidende Spalte, `AI` oder `Human`, nie beide.*

**2 · Punkt 8 verlangte einen Dateiwert und nannte keine Datei.** Er stand
damit gegen die Auslassung des Profilwechsels drei Absätze weiter unten.
Aufgelöst durch zwei benannte Läufe statt eines unbestimmten:

| | Profil | Datei | Papier | was geändert wird |
|---|---|---|---|---|
| **O** | Online + YAML-Rückfall | `assets-fallback.yaml` | Anleihe `DE0001102531` | History |
| **Y** | reines Dateiprofil | `assets-standalone.yaml` | Fonds `DE0009848119` | Preis |

Nachgemessen, nicht angenommen — die Vorlagen tragen genau das: die
Fallback-Datei enthält **nur** die Anleihe, und zwar mit `history`; die
eigenständige Datei enthält den Fonds mit `price` und `BTC-EUR` als `pair`.
Punkt 2 nennt jetzt `BTC-EUR`, sodass alle drei Identitätsformen ohne einen
zusätzlichen Fall abfallen.

Und die Auslassung stimmt jetzt: **Der Profilwechsel ist aus Mikes
Handgriffen ausgelassen, nicht aus meinem Beleg.** Die Überschrift sagt das
inzwischen selbst.

**3 · Punkt 9 war kein Handgriff, und der Befundweg widersprach sich.** Die
Prüfsumme steht nicht mehr als neunte Verify-Zeile, sondern als Bedingung des
Laufs: Weicht sie ab, ist der Lauf ungültig, unabhängig vom Rest.

Der Widerspruch war handfest — die Nicht-Ziele sagten *„keine Produktänderung
aus diesem Ticket heraus"*, zwei Absätze darüber stand *„wird repariert"*.
Festgelegt ist jetzt: **eigenes verlinktes Bauticket → Codex-Freigabe →
Wiederholung des Punktes → erst dann Mike.**

Nichts umgesetzt, nichts gelaufen — das Ticket ist weiterhin ein Konzept.
