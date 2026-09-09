# T-56 · Deine Rückmeldung zur Oberfläche

Der technische Vorlauf ist **in Runde 6 freigegeben**.

A–F sind beantwortet. Die Nacharbeit zu C und zum API-Link ist umgesetzt und
im Browser geprüft. Die Nacharbeit zu F ist mit [T-26](T-26-offene-details-umsetzen.md) implementiert und
erstgetestet und durch Claude in T-26 Runde 2 auf `cb14e4b` freigegeben.
Mike hat T-56 am 2026-09-07 nach den UI-Nacharbeiten abgenommen.

## Was nur Mike beantworten kann

**Abgenommen am 2026-09-07.** Mike: „Damit sollte T-56 durch sein“.
Die früheren Urteile und die Nachweise zu den UI-Korrekturen bleiben unten
erhalten. Es ist kein weiterer Handgriff für dieses Ticket offen.

### Deine Antworten zu Analyse und Fehlermeldung

**Lauf Y** ist das reine Dateiprofil (`sources-standalone.yaml` und
`assets-standalone.yaml`).

**Lauf O** ist das Online-Profil mit YAML-Rückfall
(`sources-fallback.yaml` und `assets-fallback.yaml`).

Die Laufangabe ordnet den Handgriff der passenden vorbereiteten Instanz zu.

| Frage | Prüfpunkt # | Lauf | Handgriff | Dein Urteil | Human |
|---|---|:--:|---|---|---|
| **B** | [2](#pruefpunkt-2) | Y | Im Bestand **`BTC-EUR`** auswählen und dessen Analyse öffnen (`pair`, `BTC`/`EUR`). Die angezeigten Angaben ansehen. | Zeigt es das, was dich interessiert — oder fehlt eine Angabe, die du dort erwartest? | Passt |
| **C** | [5](#pruefpunkt-5) | O | **`KEINPAPIER.XX`** über das Feld zum Aufnehmen eingeben und das Hinzufügen auslösen. Den daraufhin angezeigten Fehlerhinweis lesen. | **Ist der Satz verständlich?** Würdest du danach wissen, was zu tun ist? | Passt so |

**Zu B:** Den Hinweis auf unpassende editierbare Felder hast du bereits
gegeben. Hier kannst du weitere fehlende Angaben ergänzen.

**Zu C:** Die Fehlermeldung enthält jetzt die getrimmte Eingabe; dein
Originalurteil bleibt oben erhalten.

### Deine bisherigen Antworten

A, D und E hast du positiv beantwortet.

F enthält deinen Änderungswunsch;
diese Rückmeldung bedeutet noch nicht, dass die Änderung umgesetzt ist.

Die ursprüngliche Frage A bleibt zur Einordnung deiner Antwort erhalten.

| # | Wo | Die Frage | Human |
|---|---|---|---|
| **A** | Bestand nach Punkt 1 | Yahoo liefert `BAYERISCHE MOTOREN WERKE AG   S` als Namen — mit Füllzeichen. Ich gebe den Wert der Quelle unverändert wieder. **Willst du das so, oder soll StockInfo den Namen putzen?** | Inzwischen wurde auf Langename umgestellt - das passt so |
| **D** | Restore-Bestätigung aus Punkt 7 | Ist die Warnung deutlich genug für etwas, das Daten überschreibt — oder zu beiläufig? | OK so |
| **E** | Statuszeile | Nützlich oder Lärm? | Passt gut so |
| **F** | die Oberfläche als Ganzes | Was fällt dir auf, das in keinem der Punkte steht? | Die Detailansicht muss die angezeigten und bearbeitbaren Angaben nach Instrumenttyp auswählen. Bei BTC-Eur kann zb die Fondswährung angepasst werden - Schmarren.|

### Deine weiteren Rückmeldungen

Jede Rückmeldung nennt die zugehörige Prüfung. Der Link führt direkt zur
Prüfzeile mit Handgriff und erwartetem Ergebnis; deine Anmerkung bleibt im
Originalwortlaut erhalten.

| Prüfpunkt | Deine Anmerkung |
|---|---|
| [1 · SAP.DE und BMW.DE aufnehmen](#pruefpunkt-1) | Name wurde nur in der Kurzform übernommen, ist inzwischen aber korrigiert |
| [2 · BTC-EUR: Analyse und angezeigte Felder](#pruefpunkt-2) | OK, die editierbaren Felder passen aber nicht |
| [4 · Statuszeile während des Ladens](#pruefpunkt-4) | OK |
| [5 · Fehlermeldung bei KEINPAPIER.XX](#pruefpunkt-5) | ok |
| [6 · Sicherung anlegen](#pruefpunkt-6) | OK, funktioniert auch über REST |
| [8a · Anleihe: geänderte YAML-History ohne Neustart](#pruefpunkt-8a) | OK |

Anmerkungen, Mike:
Gestartet ist das ganze mit der Migrationsseite. Ein Asset wurde verworfen die anderen wurden übernommen.
Backup vor der Migration hat auch funktioniert.

Bei Einstellungen / API & Links / API-Wurzel - kommt auf die aktuelle Seite - scheint mir nicht sinnvoll zu sein.

### Nachprüfung und Korrekturen · 2026-09-07

| Befund | Stand | Nachweis |
|---|---|---|
| C: Eingabe fehlt im Fehler | Behoben: getrimmte Eingabe in DE/EN, Fehlergrund bleibt erhalten | Browser auf localhost:5173: `  KEINPAPIER.XX  ` eingegeben; Toast zeigt `Hinzufügen von „KEINPAPIER.XX“ fehlgeschlagen` mit Grund. Zwei neue Sprachtests. |
| API-Wurzel führt ins Dashboard | Behoben: Link entfernt; Swagger, OpenAPI und Health bleiben | Einstellungen → API & Links im Browser: drei API-Links, keine API-Wurzel. |
| F: Fondsfelder bei BTC-EUR | **Technisch freigegeben, T-26 Runde 2** | T-26 reicht Deklaration, Anwendbarkeit und Schreibrecht bis REST/UI durch. Isolierter Browserlauf: BTC ohne Fondsfelder, ETF mit Fondsfeldern, unbekanntes Testfeld editierbar. |

Frisch geprüft: **324/324 Dashboardtests**, `vue-tsc --noEmit` und
`git diff --check` erfolgreich; TypeScript-Compiler-Inventar der neu berührten
Dateien geprüft. Die Browserprüfung betrifft die beiden lokalen Korrekturen,
keinen erneuten vollständigen Zwei-Profil-Vorlauf. Die historischen neun
AI-Ergebnisse bleiben dem damaligen Stand zugeordnet.

**Scope-Checkpoint F:** T-26 beschreibt die generische Durchleitung der
Plugin-Felder, ihre Darstellung und `overridable` einschließlich Backend.
Zusätzlich muss die Anwendbarkeit je Instrument geklärt werden: Eine globale
`FIELDS`-Liste allein genügt bei einem Plugin für mehrere Gattungen nicht.
Mike hat T-26 einschließlich REST, UI und erstem UI-Test beauftragt;
Codex hat implementiert, Claude hat den Stand `cb14e4b` unabhängig freigegeben.
T-56 ist nach Mikes abschließendem Urteil abgenommen.
T-61 ist zurückgestellt; T-62 bleibt offen; die Börsenauskunft gehört zu T-30.

### Erster UI-Durchlauf F durch Codex · 2026-09-07

Mike hat T-26 ausdrücklich abgeschlossen und den ersten UI-Durchlauf hier
beauftragt. T-26 liegt unter `solved/`; die menschliche UI-Abnahme bleibt hier.
Geprüft auf `http://127.0.0.1:5186/#/assets`, isoliertes YAML-/Demo-Profil,
eigener Backend-Port 8936. Backend mit dem freigegebenen Produktstand neu gestartet.

| # | Handgriff | Beobachtetes Ergebnis | AI |
|---|---|---|:--:|
| F1 | BTC-EUR und EUNL.DE über Symbol öffnen | BTC ohne Fondsfelder; ETF mit TER, Anbieter, Fondsdomizil; Quellenwerte ohne Editor | ✅ |
| F2 | BTC-Score 0 und ETF-Anbieter `UI-Test T-56` über UI eingeben | Beide gespeichert, REST-Herkunft `manual` | ✅ |
| F3 | Browser neu laden, Backend neu starten und Details erneut öffnen | 0 und Freitext bleiben sichtbar; REST bestätigt beide Werte | ✅ |
| F4 | Score mit Leeren, Anbieter mit Entfernen löschen | Beide manuell null; TER 0,2 % und Domizil Ireland unverändert | ✅ |
| F5 | Feldbereich und Quellenfußzeile ansehen | Keine Herkunfts-Tooltips, einzelnen Datumsangaben oder Read-only-Hinweise; Fußzeile bleibt | ✅ |
| F6 | ETF in 390-px-Kartenansicht über mehr aufklappen | Alle drei Detailfelder sichtbar, Dokumentbreite 390 px, kein horizontaler Überlauf; Emulation anschließend vollständig entfernt | ✅ |

Die Zahl-/Texteingaben wurden zunächst mit der noch laufenden Testinstanz
gespeichert, anschließend mit dem neu gestarteten freigegebenen Backend gelesen
und gelöscht. Kein neuer vollständiger Online-/YAML-Vorlauf der historischen
neun Prüfpunkte behauptet; dieser Durchlauf prüft die Nacharbeit F auf Deutsch.

**Testdaten-Befund:** Mike fragte erneut nach „Bestätigt“. Das war ein festes
`false` des Demo-Plugins ohne fachliche BTC-Bedeutung. Aus der temporären
Plugin-Deklaration und Lieferung entfernt, Test-Backend neu gestartet.
`GET /instruments` nennt bei BTC nur noch `risk-demo.score`, beim ETF
`fund_domicile`, `provider`, `ter`. Kein Produktcode geändert.

Betriebsdatenbank vor/nach dem Durchlauf SHA256 identisch:
`8a382f24ea608540acc8ad322fbc6e1037d3effb7a7e22bf9d0cbef216c69728`.
Human-Antworten unverändert. Die Eingabefelder sind für Mikes Abnahme wieder leer.

### UI-Nacharbeit: Löschknopf neben dem Textfeld

Mike meldete auf `localhost:5173/#/assets`, dass das × eine Zeile tiefer steht,
und wünschte es rot. Bei GOLD.SG reproduziert: NSelect beanspruchte die ganze
Breite, das × brach um. Textauswahl jetzt mit flexibler Restbreite und
`min-width: 0`; Löschknopf als Naive-Fehleraktion rot.
Desktop und 390 px gemessen: Anbieter, Fondswährung und Domizil samt × auf
derselben Mittellinie; kein horizontaler Überlauf. Rot im DOM bestätigt
(`rgb(224, 82, 82)`). Sechs Detail-Komponententests und vue-tsc grün.
Betriebswerte nur angesehen, keine Eingabe oder Löschung ausgeführt.

### UI-Nacharbeit: Währung neben Fondsvolumen

Mikes Befund auf GOLD.SG bestätigt: Das Währungsfeld belegte 100 Prozent
der Spalte und brach unter den Betrag um. Jetzt kompakt mit 7 rem neben dem
Betrag, Abstand 4 px. Technisches „absolute“ wird nicht als Einheit angezeigt;
beim Bearbeiten steht die Währung im eigenen Eingabefeld, bei Quellenwerten
weiterhin am Betrag. Desktop und 390 px: Betrag und Währung auf gleicher
Mittellinie, kein horizontaler Überlauf. Sechs Detail-Komponententests und
vue-tsc erfolgreich; Betriebswerte nicht geändert.

### UI-Nacharbeit: Neutrale Beschriftung des Fondsvolumens

Mikes Hinweis auf „Fondsvolumen (EUR)“ trotz eigener Währungseingabe bestätigt.
Der feste Zusatz kam aus der justETF-Deklaration. Labels heißen jetzt
„Fondsvolumen“ / „Fund size“; justETF liefert weiterhin EUR als Währung am
jeweiligen Betrag. Die separate Fondswährung beschreibt die Fondswährung,
nicht zwingend die Währung des Volumenbetrags.
Live `/fields` mit neutralen Labels bestätigt. 110 betroffene Plugin-/Detailtests,
Ruff und vollständiges Python-Bezeichnerinventar erfolgreich.

### UI-Nacharbeit: Einheitliche Währungsauswahl

Beim Fondsvolumen jetzt dieselbe filterbare Naive-Auswahl mit freier Eingabe
wie bei Fondswährung. Beide verwenden die vorhandene Vorschlagsliste
`fieldOptions.fund_currency`; keine zweite Währungsliste. Die Auswahl bleibt
kompakt neben dem Betrag. Bestehende Großschreibung und Speicherlogik bleiben
erhalten. Sechs Detail-Komponententests und vue-tsc erfolgreich.

### UI-Nacharbeit: Einheitliches rotes × rechts

Auf Mikes Rückmeldung sitzt das Löschkreuz nun bei allen manuellen
Detailwerten rechts. Das linke Löschsymbol des Zahleneditors entfällt auch
bei TER. Beim Fondsvolumen steht das gemeinsame × hinter der Währung und
entfernt den manuellen Betrag samt Währung; ein Betrag ohne Währung wird
nicht neu gespeichert. Acht Detail-Komponententests inklusive Löschen von
Zahlen mit/ohne Währung und vue-tsc erfolgreich. Position und rote Farbe im
Browser geprüft, Betriebswerte nicht gelöscht.

### UI-Nacharbeit: Veraltete Kennzahlen außerhalb des Profils

BRYN.DE lieferte `details: {}`, aber noch alte Top-Level-Werte und manuelle
Markierungen für TER/Thesaurierung. Die Tabellen-/Kartenkomponente berücksichtigt
jetzt dieselbe Feldanwendbarkeit wie die Detailansicht: Bei vorhandenem
`details` erscheinen nur darin enthaltene Kennzahlen, sonst ein Strich ohne
Markierung. Das betrifft auch eine alte Volatilität ohne aktuelle Deklaration.
Der Legacy-Pfad ohne `details` bleibt kompatibel; gespeicherte Werte und REST
unverändert. Zwei Regressionen zuerst rot, anschließend 52 betroffene
Komponententests und vue-tsc grün. Live BRYN ohne Markierungen, GOLD weiterhin
mit seinen anwendbaren manuellen TER-/Thesaurierungswerten.

### Bekannte Einschränkung

Beim Sprachwechsel kann der Inhalt einer bereits offenen Meldung in der
alten Sprache bleiben. Du hast das als **kleinen Bug, nicht als Blocker**
eingestuft.

Die Nacharbeit liegt in
[T-61](../postponed/T-61-offener-toast-behaelt-alte-inhaltssprache.md); die Abnahme von T-56
und der MVP sind dadurch nicht blockiert.

---

## Umsetzung und technische Nachweise

**Layout-Hinweis für Claude und Codex (2026-09-07):** Auf Mikes Auftrag steht
sein Arbeitsbereich jetzt am Anfang. Fragen A–F, Human-Antworten, neun
AI-Ergebnisse und Review-Belege bleiben erhalten. Mikes Anmerkungen aus der
AI-Tabelle stehen getrennt oben. Den Arbeitsbereich bei neuen Ergebnissen
aktualisieren; abgeschlossene Review-Runden bleiben Historie. Diese Umordnung
ändert weder Freigabe noch Zuständigkeit oder Abnahmekriterien.

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Dashboard) | **9/9 grün — Codex-freigegeben in Runde 6** | ~2 h Claude-Vorlauf (zwei Profile) + ~15 min Mike | Mikes Urteil zu sechs Fragen; der Funktionsnachweis liegt bei mir | — |

- **Angelegt:** 2026-09-02, auf Mikes Auftrag
- **Ersetzt:** T-35, T-42 und T-50 als Abnahmetickets für Mike
- **Hängt ab von:** nichts. Alle geprüften Stände sind Codex-freigegeben


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
| **1** | O | <a id="pruefpunkt-1"></a>`SAP.DE` und `BMW.DE` über das Feld aufnehmen | beide im Bestand, mit Name und `stock`; keine Fehlermeldung | T-54 | ✅ |
| **2** | Y | <a id="pruefpunkt-2"></a>Analyse von **`BTC-EUR`** öffnen (`pair`, `BTC`/`EUR`) | die Stufen nennen die konfigurierten Quellen, Zeiten und die Zeilenzahl als Zahl | T-46, T-53, T-31 | ✅ [^zeilen] |
| **3** | Y | <a id="pruefpunkt-3"></a>dieselbe Analyse auf Englisch | kein deutsches Wort, auch nicht `3 Zeilen` | T-53 | ✅ |
| **4** | O | <a id="pruefpunkt-4"></a>Statuszeile während eines Ladevorgangs | die laufende **Kurskette** steht geordnet dort | T-43 | ✅ [^kette] |
| **5** | O | <a id="pruefpunkt-5"></a>`KEINPAPIER.XX` aufnehmen | ein Satz mit Grund erscheint; kein Rohtext, kein stilles Nichts | T-44 | ✅ [^wdh] |
| **6** | O | <a id="pruefpunkt-6"></a>Sicherung anlegen | steht mit Zeitpunkt und Größe in der Liste; Datei liegt auf der Platte | T-47 | ✅ |
| **7** | O | <a id="pruefpunkt-7"></a>Sicherung zurückspielen | verlangt eine Bestätigung und benennt den Vorgang | T-47 | ✅ |
| **8a** | O | <a id="pruefpunkt-8a"></a>in `assets-fallback.yaml` die **History der Anleihe** `DE0001102531` ändern, während die App läuft | der Wert erscheint ohne Neustart — und zwar über den YAML-Rückfall **hinter** der Online-Kette | T-48, T-37 | ✅ |
| **8b** | Y | <a id="pruefpunkt-8b"></a>in `assets-standalone.yaml` den **Preis des Fonds** `DE0009848119` ändern, während die App läuft | derselbe Nachweis im reinen Dateiprofil | T-48, T-52 | ✅ |

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

## Review-Verlauf · Historie

Die folgenden Abschnitte dokumentieren den damaligen Stand. Frühere offene
Fragen und Sperren sind zusammen mit ihren späteren Auflösungen zu lesen.
Für Mikes aktuellen Handlungsbedarf gilt der Arbeitsbereich am Anfang;
die Produktentscheidung nach Runde 6 hält die Freigabe fest.

### Ursprünglicher Anlass und Zuschnitt

**Löst:** Es gibt drei Tickets, die Mike durch die Oberfläche führen sollten,
und keines hat den Zweck erfüllt. T-35 und T-50 wurden **von mir** gelaufen
und haben dabei Befunde produziert; T-42 ist nie gelaufen.

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

### Frühere Begründung zu Frage A · durch Mikes Antwort überholt

**A** ist die einzige Frage, hinter der schon eine Entscheidung von mir steht:
Ich habe den Namen nicht angefasst, weil eine Quelle wiederzugeben etwas
anderes ist, als sie zu korrigieren. Sagst du „putzen", ist das ein neues
Ticket, kein Befund an T-54.

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

## Runde 7 · Die Landung — halb belegt (Claude, 2026-09-04)

Mike hat `@mmit/ux-foundation` als **0.8.0** veröffentlicht und die
Aktualisierung beauftragt. Sie ist erfolgt, Commit `cb33dcb`.

### Was gelandet ist

`dashboard/package.json` verlangt `^0.8.0` statt `latest`, und
`AppDashboard.vue` gibt `title: () => t('errors.title')` herein.

Die Versionsangabe zog mit, weil sie Teil der Ursache war: `latest` ist ein
Dist-Tag, kein Bereich. Die Lockdatei hielt das Paket auf 0.6.0 fest, und aus
`package.json` war nicht abzulesen, welche Fassung das Produkt verlangt —
genau daran ist die Landung in Runde 5 zuerst hängengeblieben.

**322 Dashboardtests** und `vue-tsc` grün.

### Der Browser-Beleg

Profil **O** aus `T-56-vorlauf.sh`, frisch aufgebaute Instanz. Auf Deutsch
`KEINPAPIER.XX` aufgenommen, dann in den Einstellungen auf Englisch
umgeschaltet — ohne Neuladen, die Meldung stand durchgehend. Aus dem DOM
gelesen:

| | vor dem Wechsel | nach dem Wechsel |
|---|---|---|
| Überschrift | `Fehler` | **`Error`** ✅ |
| Fließtext | `Hinzufügen fehlgeschlagen — Dem Symbol fehlt das Börsenkürzel …` | **unverändert deutsch** ❌ |

Eine **neu** ausgelöste Meldung nach dem Wechsel ist vollständig englisch
(`Adding failed — The symbol has no exchange suffix …`).

`shasum -a 256 data/stockinfo.db` vor und nach dem Lauf identisch:
`1709aeabfc2eafc974aaa4bb0dcdbd7e0c23c80bc96000cd665ac73fe6207430`.

### Warum der Fließtext nicht mitgezogen wurde

`options.content` ist bereits eine Funktion — sie liest aber `source.value`,
und dort steht ein fertig übersetzter Satz, abgelegt zum Zeitpunkt des
Fehlschlags. Der Watcher feuert korrekt; er liest nur eine Zeichenkette, die
sich nicht mehr ändert.

Das Inventar dazu ist gemessen, nicht geschätzt —
`grep -rn 'error\.value = ' src/{composables,components,api}` ohne die
Rücksetzer auf `null`: **16 Zuweisungen in 13 Composables**, sechs davon
speist `AppDashboard.vue` in `notify` ein. Den Satz durch Schlüssel und
Parameter zu ersetzen ändert `error: Ref<string | null>` in allen 13, samt
Tests und jeder Anzeigestelle.

Das ist nach der Regel dieses Tickets kein kleiner lokaler Befund mehr,
sondern ein Vertrag — er geht als Scope-Frage an Codex und Mike, nicht in
diesen Diff. Offen bleibt dabei ausdrücklich, **ob** es überhaupt ein Fehler
ist: Die Überschrift ist ein Etikett der Oberfläche, der Fließtext die
Beschreibung eines Ereignisses, das in der alten Sprache stattfand.

## Codex-Review · Runde 6 `changes_requested` (2026-09-05)

Die eigentliche Landung in `cb33dcb` ist technisch sauber: StockInfo installiert
nachweislich `@mmit/ux-foundation` 0.8.0, die publizierten Quellen entsprechen
dem Release-Tag `0c63fba`, `^0.8.0` ist ein nachvollziehbarer statt eines
zeitabhängigen Dist-Tags, und Titel-Callback sowie Paketvertrag passen
zusammen. Frisch grün: **322/322 Dashboardtests** und `vue-tsc`.

Das genügt nicht für eine Freigabe. Vier Befunde bleiben:

1. **[S1] Die bindende Akzeptanzbedingung ist sichtbar nicht erfüllt.** Runde 5
   verlangt vor Mikes Lauf einen DOM-Beleg, bei dem Überschrift **und** Inhalt
   nach dem Sprachwechsel gemeinsam englisch sind. Der neue Browserbeleg zeigt
   das Gegenteil: `Error` steht über einem deutschen Fließtext. Das ist keine
   neue Produktfrage. Ein Toast beschreibt nach `ux-standards` einen Zustand,
   und sichtbarer Text folgt der aktiven Sprache. T-56 bleibt deshalb bei
   Claude. Vor dem nächsten Produktedit wird der Scope auf die sechs tatsächlich
   in `AppDashboard.vue:errorSources` verdrahteten Fehlerquellen und eine
   gemeinsame, reaktive Darstellung neu zugeschnitten; die sieben anderen
   Anzeigewege werden nicht ohne Verbraucherbeleg mit umgebaut. Danach läuft
   derselbe Handgriff erneut und muss am **selben offenen Toast** englischen
   Titel und englischen Inhalt zeigen.
2. **[S1] Das verlangte dauerhafte StockInfo-Orakel fehlt.** `cb33dcb` ändert
   keine Testdatei. Das SFC-/TypeScript-Inventar findet den einzigen
   `notify()`-Aufruf in `AppDashboard.vue`, aber keinen Test, der
   `AppDashboard` direkt importiert und den Sprachwechsel einer offenen Meldung
   ausführt. Deshalb bleiben alle 322 Tests auch beim jetzt dokumentierten
   Fehler grün. Die Korrektur braucht einen Test am öffentlichen UI-Weg, der
   Fehler auf Deutsch auslöst, ohne Neuaufbau auf Englisch wechselt und am
   weiter offenen Toast **beide** Texte prüft. Der minimale Mutant mit früh
   übersetztem/eingefrorenem Inhalt muss genau diesen Test röten.
3. **[S2] Das als vollständig bezeichnete Inventar ist falsch.** Ein
   TypeScript-AST-Inventar zählt dieselben 16 nichtleeren
   `error.value`-Zuweisungen in **13** Composables, nicht zwölf; die OUTBOX-Liste
   nennt mit `useMigration` selbst den dreizehnten. `grep` ist dafür nach
   `CLAUDE.md` keine Gegenprobe. Vor der Scope-Fassung werden Erzeuger und
   Verbraucher semantisch inventarisiert. Aus den 13 Speicherstellen folgt
   insbesondere nicht, dass alle denselben Toast-Vertrag brauchen — aktuell
   erreichen genau sechs `errorSources` den Notifier.
4. **[S2] Der aktuelle Übergabeteil des Tickets fragt Mike weiterhin sieben
   Fragen einschließlich G.** G ist beantwortet und als 0.8.0 gelandet; offen
   sind A–F. Vor der erneuten Übergabe muss der aktuelle Urteilsteil genau diese
   sechs Fragen zeigen. Die leeren Human-Zellen bleiben selbstverständlich
   unberührt; die Auflösung von G bleibt in Runde 6 als Historie erhalten.

**DRY-Prüfung:** Im Diff von `cb33dcb` entsteht keine zweite
Notifier-Implementierung; Auflösung und Watcher bleiben im Fundament, StockInfo
reicht nur den Katalogzugriff herein. Für die Nacharbeit gilt dieselbe Grenze:
ein gemeinsamer Fehlerträger beziehungsweise Renderer, keine sechs unabhängigen
Übersetzungsmechanismen. Neue Testinfrastruktur ist weder vorhanden noch nötig.

**Konvergenz:** Die Grundentscheidungen sind stabil. Der Rest ist mit
reaktivem Fließtext, einem vertikalen Orakel, korrigiertem Inventar und sechs
aktuellen Urteilsfragen konkret. Nach einer Scope-Neufassung innerhalb T-56 ist
eine abschließende Runde belastbar; T-57 bleibt bis dahin eingefroren.

## Produktentscheidung nach Runde 6 · Minor statt Gate (2026-09-05)

Mike stuft den sichtbaren Sonderfall ausdrücklich als **kleinen Bug und nicht
als Blocker** ein: Ein Sprachwechsel genau während der Anzeige eines Toasts
kann vorkommen, verhindert aber weder die T-56-Abnahme noch den MVP.

Damit sind die beiden S1-Befunde aus Runde 6 nicht widerlegt, sondern als
offene Nacharbeit nach
`postponed/T-61-offener-toast-behaelt-alte-inhaltssprache.md` verschoben. Die beiden
S2-Artefakte sind oben korrigiert: Das Inventar nennt 13 Composables, und der
aktuelle Urteilsteil enthält nur noch A–F; keine Human-Zelle wurde ausgefüllt.
T-56 ist in Runde 6 freigegeben.
