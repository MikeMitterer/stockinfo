# T-56 · Was nur Mike entscheiden kann — und was ich vorher beweise

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Dashboard) | **9/9 gruen — Scope-Checkpoint zum Titel-Fehler** | ~2 h Claude-Vorlauf (zwei Profile) + ~15 min Mike | Mikes Urteil zu sechs Fragen; der Funktionsnachweis liegt bei mir | — |

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
| **1** | O | `SAP.DE` und `BMW.DE` über das Feld aufnehmen | beide im Bestand, mit Name und `stock`; keine Fehlermeldung | T-54 | ✅ |
| **2** | Y | Analyse von **`BTC-EUR`** öffnen (`pair`, `BTC`/`EUR`) | die Stufen nennen die konfigurierten Quellen, Zeiten und die Zeilenzahl als Zahl | T-46, T-53, T-31 | ✅ [^zeilen] |
| **3** | Y | dieselbe Analyse auf Englisch | kein deutsches Wort, auch nicht `3 Zeilen` | T-53 | ✅ |
| **4** | O | Statuszeile während eines Ladevorgangs | die laufende **Kurskette** steht geordnet dort | T-43 | ✅ [^kette] |
| **5** | O | `KEINPAPIER.XX` aufnehmen | ein Satz mit Grund erscheint; kein Rohtext, kein stilles Nichts | T-44 | ✅ [^wdh] |
| **6** | O | Sicherung anlegen | steht mit Zeitpunkt und Größe in der Liste; Datei liegt auf der Platte | T-47 | ✅ |
| **7** | O | Sicherung zurückspielen | verlangt eine Bestätigung und benennt den Vorgang | T-47 | ✅ |
| **8a** | O | in `assets-fallback.yaml` die **History der Anleihe** `DE0001102531` ändern, während die App läuft | der Wert erscheint ohne Neustart — und zwar über den YAML-Rückfall **hinter** der Online-Kette | T-48, T-37 | ✅ |
| **8b** | Y | in `assets-standalone.yaml` den **Preis des Fonds** `DE0009848119` ändern, während die App läuft | derselbe Nachweis im reinen Dateiprofil | T-48, T-52 | ✅ |

[^zeilen]: **`BTC-EUR` allein konnte die Zeilenzahl nicht zeigen** — es trägt
    im YAML einen Preis, aber keine Tagesreihe; die Stufe meldete `nichts`.
    Die Zeile hätte damit grün ausgesehen, ohne ihre zweite Hälfte je geprüft
    zu haben — genau das Muster, das in `CLAUDE-REVIEW-PATTERNS.md` steht.
    Belegt ist sie an der Anleihe `DE0001102531`, die eine History hat:
    `Tagesreihe · yaml-file · 0.00s · geliefert · 3 Zeilen`. Der `pair`-Fall
    bleibt über `BTC-EUR` belegt; **kein neuer Fall, ein zweites Papier im
    selben Handgriff.**
[^wdh]: **Wiederholt am 2026-09-02 nach T-58**, auf frisch aufgebauter Instanz.
    `GET /quote?symbol=KEINPAPIER.XX → 400`, und im Hinweis steht statt der
    rohen Kennung ein Satz — in beiden Sprachen, aus dem DOM gelesen:
    DE „Hinzufügen fehlgeschlagen — Dem Symbol fehlt das Börsenkürzel — aus
    ihm allein lässt sich der Handelsplatz nicht ableiten."; EN „Adding failed
    — The symbol has no exchange suffix — the trading venue cannot be derived
    from it alone." Im selben Handgriff fiel auf, dass der Titel nach einem
    Live-Sprachwechsel deutsch blieb. Das war als kleiner lokaler Befund
    eingeplant — **das Inventar hat ihn aus diesem Repo herausgeführt.** Die
    Ursache liegt im Vertrag von `@mmit/ux-foundation`; siehe Runde 5 und
    Frage **G**.
[^kette]: **Wortlaut geschärft.** Ich hatte „nennt die antwortende Quelle"
    geschrieben — das sagt T-43 nirgends zu. Seine Zeile `#2` verlangt „die
    laufende Kurskette steht geordnet dort", und genau das steht dort:
    `Kurse: yfinance → yaml-file` in O, `Kurse: yaml-file` in Y. Gegen meine
    ursprüngliche, schärfere Formulierung wäre die Zeile nicht belegbar
    gewesen, obwohl das Produkt seine Zusage hält.

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

Ein kleiner, eindeutig lokaler Befund wird nach der Regel in
`CODEX-REVIEW-AUTOMATION.md` direkt im laufenden Ticket korrigiert. Danach
läuft der betroffene Handgriff erneut; eine Codex-Zwischenfreigabe ist dafür
nicht nötig. Erst wenn der Befund eine neue Entscheidung, einen Vertrag, ein
Schema, Konfiguration oder eine weitere Produktschicht berührt beziehungsweise
das Kleinbudget überschreitet, entsteht ein eigenes Bauticket oder ein
Scope-Checkpoint.

**Erst wenn alle neun Zeilen und die dabei gefundenen lokalen Korrekturen
grün nachgemessen sind**, geht T-56 an Mike. Befund, Korrektur und
Wiederholungsbeleg bleiben gemeinsam in dieser Abnahme.

## Was nur Mike beantworten kann

**Sieben** Fragen — sechs aus dem Zuschnitt, die siebte aus dem Lauf. Keine
davon ist eine Prüfung, ob etwas funktioniert; das steht oben und ist dort
belegt. Es sind Urteile, und ein *„nein"* ist keine Fehlermeldung, sondern
eine Produktentscheidung.

| # | Wo | Die Frage | Human |
|---|---|---|---|
| **A** | Bestand nach Punkt 1 | Yahoo liefert `BAYERISCHE MOTOREN WERKE AG   S` als Namen — mit Füllzeichen. Ich gebe den Wert der Quelle unverändert wieder. **Willst du das so, oder soll StockInfo den Namen putzen?** | |
| **B** | Analysefenster | Zeigt es das, was dich interessiert — oder fehlt eine Angabe, die du dort erwartest? | |
| **C** | Fehlermeldung aus Punkt 5 | **Ist der Satz verständlich?** Würdest du danach wissen, was zu tun ist? | |
| **D** | Restore-Bestätigung aus Punkt 7 | Ist die Warnung deutlich genug für etwas, das Daten überschreibt — oder zu beiläufig? | |
| **E** | Statuszeile | Nützlich oder Lärm? | |
| **F** | die Oberfläche als Ganzes | Was fällt dir auf, das in keinem der Punkte steht? | |
| **G** | `ux-foundation`, `NotifyOptions` | Nach einem Sprachwechsel **ohne Neuladen** bleibt die Überschrift eines Hinweises in der alten Sprache; der Text wechselt mit. Die kleinste Korrektur ist `title: string \| (() => string)` im Fundament. **Soll es das können — oder ist der Fall selten genug, um ihn zu lassen?** Begründung in Runde 5 | |

**A** ist die einzige Frage, hinter der schon eine Entscheidung von mir steht:
Ich habe den Namen nicht angefasst, weil eine Quelle wiederzugeben etwas
anderes ist, als sie zu korrigieren. Sagst du „putzen", ist das ein neues
Ticket, kein Befund an T-54.

## Nicht-Ziele

- Keine ungeplante Produktänderung jenseits der ausdrücklich begrenzten
  Kleinbefund-Regel. Größere oder fachlich neue Änderungen folgen dem normalen
  Ticket- beziehungsweise Scope-Checkpoint-Weg.
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

---

## Runde 2 · Der Browser-Vorlauf (Claude, 2026-09-02)

**Acht von neun Zeilen grün, eine rot.** Die rote geht als **T-58** ihren
eigenen Weg; T-56 wandert damit nicht zu Mike, sondern in die Wiederholung —
genau wie oben festgelegt.

### Der Aufbau

`_tickets/T-56-vorlauf.sh` baut beide Instanzen. Jede bekommt ein eigenes
`data/` mit eigener Datenbank, eigenem Port, eigener Fachdatei und dem
Beispiel-Plugin aus `plugin_api/examples/yaml_file.py`:

```
O  API 8901 · UI 5901 · sources-fallback   → openfigi, yahoo-search, yaml-file
Y  API 8902 · UI 5902 · sources-standalone → yaml-file in allen fünf Rollen
```

Der einzige Eingriff in die Vorlagen: `/data/assets-*.yaml` zeigt auf das
isolierte Verzeichnis statt in den Container.

### Was zu sehen war

| # | gemessen |
|---|---|
| **1** | `BMW.DE` → `BAYERISCHE MOTOREN WERKE AG S`, `stock`, 60,50 EUR · `SAP.DE` → `SAP SE I`, `stock`, 182,88 EUR |
| **2** | `BTC-EUR` → `crypto`, `pair`, 94.500,00 EUR; Analyse: vier Rollen, alle `yaml-file`. Zeilenzahl an `DE0001102531`: **3 Zeilen** |
| **3** | `Daily series · yaml-file · 0.00s · answered · 3 rows` — auch `nothing`, `Total`, `Resolution` englisch |
| **4** | O: `Kurse: yfinance → yaml-file` · Y: `Kurse: yaml-file` — die Kette in Rangfolge, und sie ändert sich mit dem Profil |
| **5** | **rot** — siehe unten |
| **6** | `02.09.2026, 11:20 · 88 kB · passt zur laufenden Quellenlage`; auf der Platte `stockinfo-20260902T092052358Z-ce358593616a.db` (90.112 Bytes) plus `.json` |
| **7** | Dialog: *„…wird beim nächsten Start eingespielt. Dafür ist ein Neustart der App nötig. Bis dahin läuft der bisherige Bestand unverändert weiter."* mit **Abbrechen** / **Vormerken** |
| **8a** | Anleihe 99,42 → **88,88**, Punkte 1 → 2, ohne Neustart |
| **8b** | Fonds 142,50 → **177,77**, Punkte 1 → 2, ohne Neustart |

Die drei Identitätsformen sind dabei ohne einen zusätzlichen Fall belegt:
`listed` (SAP.DE, BMW.DE), `pair` (BTC-EUR), `isin_only` (Anleihe, Fonds).

### Der Befund — Punkt 5

```
GET /quote?symbol=KEINPAPIER.XX  →  400
Hinweis: „…einen Fehler, den diese Oberfläche nicht kennt:
          symbol_without_exchange_suffix."
```

Der Satz für diese Kennung **existiert** — unter `migration.reason`. Der
Aufnahmeweg sucht ihn unter `errors.reason` (`api/reason.ts:34`) und fällt auf
den Rückfalltext zurück. Zwei Gruppen, eine Kennung, die beide Wege nimmt.
Vollständig in **T-58**.

### Der Riegel

```
data/stockinfo.db   vorher : 1709aeabfc2eafc974aaa4bb0dcdbd7e0c23c80bc96000cd665ac73fe6207430
                    nachher: 1709aeabfc2eafc974aaa4bb0dcdbd7e0c23c80bc96000cd665ac73fe6207430
```

**Und eine Beobachtung, die nicht mir gehört:** In `data/` lagen nach dem Lauf
wieder WAL und SHM. Ihre mtime ist **10:26**; mein Lauf begann um **11:20**
(Zeitstempel der Sicherung). Sie sind also vor meinem Lauf entstanden, keiner
meiner Prozesse hatte diese Datei je offen, und die WAL ist 0 Bytes groß.
Passend dazu: **T-32 ist nicht gebaut** — `tests/conftest.py` existiert nicht,
es gibt weder die `autouse`-Umlenkung noch den Riegel auf `sqlite3.connect`.
T-55 hat eine Naht geschlossen, nicht alle. Das ist ein Argument dafür, T-32
offen zu lassen, kein Befund dieses Tickets.

### Wie es weitergeht

1. **T-58** durchläuft den normalen Weg bis zur Freigabe.
2. Danach laufe ich **Punkt 5 erneut**.
3. Erst wenn alle neun Zeilen grün sind, geht T-56 an Mike.

Die sechs Fragen an ihn sind davon unberührt und stehen bereit — **A** hat der
Lauf sogar geschärft: Beide Namen tragen Yahoos Füllzeichen sichtbar
(`SAP SE I`, `BAYERISCHE MOTOREN WERKE AG S`).

---

## Codex-Review · Runde 2, Konzept freigegeben (2026-09-02)

Alle drei Befunde aus Runde 1 sind geschlossen. Die neun objektiven Zeilen
haben eine eigene, zunächst ehrliche `AI`-Spalte; Mikes sechs Fragen bleiben
als reine Urteilszeilen getrennt. Isolation und Befundweg sind eindeutig und
ändern aus T-56 heraus keinen Produktcode.

Die Abweichung von der Formulierung aus Runde 1 ist fachlich gleichwertig und
bleibt bewusst bestehen: `BTC-EUR` läuft im reinen YAML-Profil statt online.
Damit prüft O die beiden Online-/Fallback-Grenzen über Aktie und Anleihe,
während Y `pair` über BTC und `isin_only` über den Fonds trägt. Beide
Plugin-Varianten, BTC, Anleihe, Fonds und alle drei Identitätsformen sind ohne
zusätzlichen Fall vertreten.

Freigegeben ist nur der **Browser-Vorlauf von T-56**. Claude führt beide
isolierten Profile aus, trägt die neun AI-Ergebnisse samt Messbelegen ein und
übergibt T-56 danach erneut. T-57, `make tickets` und die Verschiebeliste
bleiben bis zum Abschluss von T-56 unangetastet.

---

## Runde 4 · Punkt 5 wiederholt (Claude, 2026-09-02)

**Neun von neun Zeilen grün.** Der Funktionspunkt ist erfüllt; vor der
Übergabe an Mike bleibt nur der dabei gefundene lokale Titel-Fehler.

**Die Reihenfolge kommt von ihm, nicht von mir.** Codex hatte die
Wiederholung an seine T-58-Freigabe gebunden; Mike hat sie ausdrücklich
vorgezogen (*„Wiederhole T-56 Punkt 5"*). T-58 liegt weiterhin bei Codex zur
Prüfung — dieser Lauf misst also einen Stand, den er noch nicht freigegeben
hat. Das ist keine Umgehung, sondern Mikes Entscheidung, und sie steht hier,
damit niemand sie später aus dem Ergebnis herauslesen muss.

### Was gemessen wurde

Frisch aufgebaute Instanz O, leerer Bestand, ein Handgriff je Sprache:

```
GET /quote?symbol=KEINPAPIER.XX  →  400
```

Aus dem DOM gelesen, nicht vom Bild abgeschätzt:

| | Text im Hinweis |
|---|---|
| **DE** | Hinzufügen fehlgeschlagen — Dem Symbol fehlt das Börsenkürzel — aus ihm allein lässt sich der Handelsplatz nicht ableiten. |
| **EN** | Adding failed — The symbol has no exchange suffix — the trading venue cannot be derived from it alone. |

**Keine rohe Kennung mehr, in keiner der beiden Sprachen.** Punkt 5 ist damit
erfüllt.

### Ein Nebenbefund, der Punkt 5 nicht betrifft

Beim Sprachwechsel **ohne Neuladen** blieb die *Überschrift* des Hinweises auf
`Fehler`, während der Text englisch war. Die Gegenprobe zeigt, dass es kein
fehlender Text ist: Steht die Sprache schon **beim Seitenaufbau** auf `en`,
lautet die Überschrift `Error`.

| Sprache gesetzt | Titel | Text |
|---|---|---|
| vor dem Aufbau | `Error` | englisch |
| nach dem Aufbau | **`Fehler`** | englisch |

Ursache in `AppDashboard.vue:115`: `title: t('errors.title')` ist ein **Wert**
und wird einmal beim Aufbau ausgewertet, `content: () => …` eine **Funktion**.
Nach Mikes Klarstellung ist das kein eigenes Ticket: Claude korrigiert den
lokalen Reaktivitätsfehler direkt in T-56, ergänzt eine gezielte Gegenprobe
und wiederholt denselben Browser-Handgriff mit Live-Sprachwechsel.

### Der Riegel

```
data/stockinfo.db   vorher = nachher
  1709aeabfc2eafc974aaa4bb0dcdbd7e0c23c80bc96000cd665ac73fe6207430
```

`data/` enthält danach nur `stockinfo.db` — diesmal keine WAL-Reste.

### Was jetzt offen ist

Nur noch **Mikes sechs Fragen** — und eine siebte, die der Titel-Fehler
aufwirft. Die Fragen sind Urteile, keine Prüfungen; ein *„nein"* darauf ist
eine Produktentscheidung und kein Befund an diesem Ticket.

---

## Runde 5 · Der Titel-Fehler ist kein Kleinbefund (Claude, 2026-09-02)

Auftrag war: *erst das vollständige Inventar der `notify`-Aufrufe, dann die
kleinste Reaktivitätskorrektur.* **Das Inventar hat die Korrektur aus diesem
Repo herausgeführt.** Ich habe deshalb nichts geändert und melde einen
Scope-Checkpoint.

### Das Inventar — und warum `grep` es falsch beantwortet hätte

Drei Dateien nennen `useNotifier`, **eine** ruft es auf:

| Datei | was wirklich dasteht |
|---|---|
| `App.vue` | nur ein Kommentar — *„braucht einen `NNotificationProvider` über sich"* |
| `AppGate.vue` | ebenfalls nur ein Kommentar |
| `AppDashboard.vue:112` | **der einzige Aufruf**, in einer Schleife über sechs Fehlerquellen |

`grep -rn "notify("` hätte eine Fundstelle gemeldet und damit zufällig recht
gehabt — aber aus dem falschen Grund. Erst das Lesen aller drei Dateien zeigt,
dass es keine weiteren gibt, statt es zu hoffen.

### Warum die kleinste Korrektur nicht hier liegt

**Die Asymmetrie steht im Vertrag des Fundaments** —
`@mmit/ux-foundation/src/composables/useNotifier.ts:18`:

```ts
export interface NotifyOptions {
  title: string          // ein Wert
  content: () => string  // eine Funktion
}
```

**Ein Getter hilft nicht.** `useNotifier.notify` reicht die Optionen als
Spread weiter — `{ ...options, seconds, countdownLabel }`. Der Spread kopiert
den Wert; ein `get title()` würde genau dort einmalig ausgewertet.
`useStateNotification:164` liest `options.title` zwar erst beim Anzeigen, aber
aus dem bereits kopierten Objekt. `content` überlebt allein deshalb, weil eine
**Funktionsreferenz** kopiert wird.

**Und das Fundament ist eine installierte Abhängigkeit:**
`dashboard/.gitignore:1` schließt `node_modules/` aus, `git ls-files` liefert
nichts, `package.json:12` führt sie als `"latest"`. Eine Änderung dort wäre
beim nächsten `npm install` weg — und sie bedient weitere Apps.

### Was ich geprüft und verworfen habe

| Weg | warum nicht |
|---|---|
| Getter auf `title` | wird vom Spread bei der Registrierung ausgewertet |
| Bei Sprachwechsel neu registrieren | `useStateNotification` setzt Watcher auf; Toasts stapeln sich |
| Titel weglassen | sichtbare Produktänderung, keine Fehlerbehebung |

Jeder wäre ein Umweg um eine Ursache, die woanders liegt.

### Die siebte Frage

Der Befund steht als **Frage G** oben bei den anderen — er ist bewusst eine
Frage an Mike und keine an Codex: Es geht um ein geteiltes Deliverable, das
weitere Apps bedient, nicht um StockInfo-Fachlogik.

---

## Runde 6 · Frage G ist beantwortet — und im Fundament umgesetzt

> **Mike, 2026-09-02:** *„1 - ja"*

Damit war der Weg freigegeben, den Frage G benannt hatte. Umgesetzt ist er
**nicht hier**, sondern im Repo `ux-foundation`
(`/Volumes/DevLocal/DevWeb/Production/ux-foundation`, GitHub
`MikeMitterer/ux-foundation`), Branch `fix/notify-title-follows-locale`,
Commit `fcd088c`.

### Was dort steht

`NotifyOptions.title` und `StateNotificationOptions.title` nehmen jetzt
`string | (() => string)`. Ein gemeinsamer Helfer löst beide Formen auf; er
steht in den **Quellen des Watchers**, damit auch eine bereits offene Meldung
nachzieht.

**Additiv, kein Bruch:** Eine Zeichenkette bleibt gültig. Das ist eigens
geprüft — in einem Paket, das jede einbindende App bedient, wäre eine
Erweiterung, die zum Bruch wird, der teurere Fehler.

| | Grenze | gemessen |
|---|---|---|
| Suite | vorher 142 | **145** |
| `make typecheck`, `make lint` | sauber | sauber |

### Ein Mutant, der nicht biss — und warum das mein Fehler war

| Mutant | rötet |
|---|---|
| Überschrift aus den Watcher-Quellen | *„zieht die Überschrift einer offenen Meldung nach"* |
| Nachziehen am offenen Toast entfernt | derselbe Fall |
| Zeichenkette nicht mehr unterstützt | **neun** Fälle in beiden Gruppen |

Der erste blieb zunächst **grün**. Meine erste Testfassung ließ den *Text*
mitwechseln — dann feuert der Watcher schon wegen des Textes, und ob die
Überschrift in seinen Quellen steht, ist nicht mehr unterscheidbar. Der Test
lässt den Text jetzt bewusst unverändert; erst ein Wechsel, den **allein** die
Überschrift auslöst, prüft die Zusage.

### Was das für StockInfo bedeutet — noch nichts

```
StockInfo/dashboard/node_modules/@mmit/ux-foundation  →  title: string
ux-foundation (Quelle, fcd088c)                       →  title: string | (() => string)
```

StockInfo bezieht das Paket als **Version 0.6.0 aus der npm-Registry**
(`package-lock.json`, `resolved: registry.npmjs.org`). Der Aufrufer
`AppDashboard.vue:115` kann erst dann auf `title: () => t('errors.title')`
umgestellt werden, wenn eine neue Version veröffentlicht und hier gezogen ist —
vorher scheitert die Typprüfung an der installierten 0.6.0.

**Veröffentlichen gehört Mike.** Ich habe nichts gepusht und nichts publiziert;
der Commit liegt lokal auf seinem Branch. Bis dahin bleibt Frage G *beantwortet
und vorbereitet*, aber in der Oberfläche unverändert.

---

## Codex-Review · Runde 5, Foundation-Code frei — Landung erforderlich (2026-09-02)

Der Foundation-Commit `fcd088c` hält die getroffene Entscheidung ein:
`title` akzeptiert additiv eine Zeichenkette oder Funktion, der aktuelle Titel
wird beim Erzeugen und bei einer bereits offenen Meldung ausgewertet, und
bestehende String-Aufrufer bleiben gültig. Codex hat im Foundation-Repo frisch
**145/145 Tests**, `vue-tsc` und ESLint grün ausgeführt.

T-56 ist damit noch nicht abgeschlossen. StockInfo installiert weiterhin
Version 0.6.0; dort erlaubt der Vertrag nur `title: string`, und
`AppDashboard.vue` übergibt weiterhin einen beim Aufbau ausgewerteten Wert.
Ein Fix in einem unveröffentlichten Fremdbranch ändert das beobachtbare Produkt
nicht.

Die Landung bleibt Teil von T-56 und erzeugt kein neues Ticket: Foundation-
Branch integrieren, neues Minor-Release veröffentlichen, StockInfo-Abhängigkeit
aktualisieren, den Titel als Funktion übergeben und denselben Browser-Handgriff
mit Live-Sprachwechsel wiederholen. Erst wenn der DOM-Titel und der Inhalt
gemeinsam englisch sind, geht T-56 an Mike.
