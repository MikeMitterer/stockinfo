# T-19 · Verbleibender Punkt: Herkunft der Auflösung

**Eine Börsenzuordnung wird nicht am bestehenden Asset korrigiert.** Für eine
andere Zuordnung muss der Nutzer das Asset löschen und neu anlegen. Damit
entfällt der in T-19 vorgeschlagene Neuauflösungs- und Korrekturweg vollständig.

Die Quellenübersicht (#8) ist bereits umgesetzt. Als noch nicht erledigter
Einzelpunkt bleibt die Herkunft der Auflösung (#7). Das Ticket bleibt dafür
offen; die heutige Entscheidung beauftragt keine Implementierung dieses Rests.
Für Mike ist aktuell kein Handgriff nötig.

## Für dich

### Bisherige Antworten und Rückmeldungen

| Bezug | Rückmeldung im Originalwortlaut | Bearbeitungsstand |
|---|---|---|
| Ticketüberarbeitung | Mike, 2026-09-07: „T-19 - was gilt noch. Überarbeite das Ticket nach den neuen Regeln“ | Gegen den aktuellen Code geprüft; alte Anforderungen eingeordnet. |
| Börsenzuordnung, #1–6 einschließlich #2a/#2b | Mike, 2026-09-07: „Börsenzuordnung kann nicht korrigiert werden - der User muss das Asset löschen und neu anlegen.“ | Produktentscheidung übernommen. Korrektur-Endpunkt, Vorschau und Übernahme alter Daten entfallen. |

### Was bleibt?

| Prüfpunkt | Aktuelle Einordnung |
|---|---|
| #1–6, #2a/#2b | Entfallen durch Mikes Entscheidung; nicht als umgesetzt oder bestanden gewertet. |
| #7 · Herkunft der Auflösung | Noch offen: Die tatsächlich auflösende Quelle wird nicht als eigenes dauerhaftes Merkmal gespeichert. Kein aktueller Implementierungsauftrag. |
| #8 · Quellenübersicht | Umgesetzt; keine Nacharbeit aus T-19. |
| #9 · Projektchecks | Kein eigenständiges Feature; nur bei einer künftigen Umsetzung von #7 erneut relevant. |

## Umsetzung und technische Nachweise

### Verbindliche Produktregel

Ein Wechsel der Börsenzuordnung erfordert Löschen und Neuanlegen. Es entsteht
kein REST- oder UI-Weg, der die Zuordnung eines bestehenden Assets korrigiert.
T-19 verlangt keine Übernahme der Kurshistorie oder manuellen Angaben aus dem
gelöschten Asset in die Neuanlage. Der bisherige Vorschlag, manuelle Angaben
zu erhalten und nur Kursreihen zu verwerfen, ist damit abgelöst.

Der zuvor beschriebene Repository-Pfad für automatisch aktualisierte Identitäten
ist davon zu unterscheiden. Er wurde nur im Code betrachtet, nicht live als
Fehler reproduziert. Daraus wird hier kein neuer Korrekturauftrag abgeleitet.

### Verbleibender Umfang: #7

`ResolvedInstrument` und das Instrument-Schema speichern keinen eigenen
dauerhaften Resolver-Namen. Die Herkunft von Kursen und einzelnen Detailwerten
belegt nicht, welche Quelle die Identität aufgelöst hat. Sollte #7 umgesetzt
werden, sind Persistenz, REST-Auskunft und die gewünschte Darstellung vorher
konkret festzulegen. Die in T-56 entfernten Tooltips werden nicht automatisch
wieder eingeführt. Die alte Time-box von vier Stunden gilt für diesen Rest nicht.

### Verify

Legende: ➖ keine Live-Verifikation; kein Prüfergebnis wird aus der
Produktentscheidung abgeleitet.

| # | Prüfgegenstand | Nachweis / Stand | AI |
|---|---|---|:--:|
| 7 | Tatsächlich auflösende Quelle dauerhaft nachvollziehbar | Noch nicht implementiert; konkrete Prüfung erst mit festgelegtem REST-/UI-Vertrag | ➖ |
| 8 | Quellen je Rolle, Reihenfolge, Nutzbarkeit und Fehlergrund | Im Code von `GET /sources` vorhanden; bestehende Quellenkonfigurationstests bestanden | ➖ |

Bereits ausgeführte Prüfung vom 2026-09-07: 16 Quellenkonfigurations- und
35 Quote-Cache-Tests bestanden (zusammen 51). Kein Live-Nachweis für #7,
kein Test eines Börsenwechsels und kein neuer vollständiger Projekt-Testlauf.

```bash
# #8: vorhandene Quellenkonfiguration und REST-Auskunft
.venv/bin/pytest -q tests/test_sources_config.py
# #9: bereits geprüfte Cache-Regressionen
.venv/bin/pytest -q tests/test_quote_cache.py
```

### Side-Effects

Nur Ticketänderung. Keine Assets gelöscht oder angelegt, keine Produkt- oder
REST-Änderung. Rollen, Prioritätskette und Reviewstatus bleiben unverändert.

### Auflösung

Der Hauptumfang ist durch Mikes Produktentscheidung vom 2026-09-07 verworfen.
#8 ist umgesetzt; #7 bleibt als einziger fachlicher Rest offen. Frühere
Antworten, IDs und Belege sind unten erhalten und keine aktuellen Aufträge.

## Review-Verlauf · Historie

Die folgende Überarbeitung wurde durch Mikes anschließende Entscheidung
abgelöst. Insbesondere sind ihre Korrekturwege und offenen Prüfpunkte #1–6
keine Anforderungen mehr. Sie enthält auch die ursprüngliche August-Fassung
mit unveränderten leeren Human-Feldern.

<details>
<summary>Überarbeitung vor Mikes Entscheidung · 2026-09-07</summary>

# T-19 · Börsenzuordnung korrigieren, ohne Kursreihen zu vermischen

**Offen bleibt der sichere Korrekturweg:** Ein falsch zugeordnetes Papier soll
neu aufgelöst werden können, ohne manuelle Angaben zu verlieren oder Kurse
verschiedener Börsen und Währungen zu vermischen. Die Quellenübersicht aus
Prüfpunkt #8 ist inzwischen umgesetzt und gehört nicht mehr zum Bauumfang.

Aktuell ist kein Handgriff von Mike nötig. Dieses Ticket ist überarbeitet,
nicht umgesetzt oder zur UI-Abnahme bereit. Der Stand wurde am 2026-09-07
anhand von Code und gezielten Tests geprüft; ein Listingwechsel wurde nicht
live durchgeführt.

## Für dich

### Was gilt noch?

| Thema | Aktueller Stand |
|---|---|
| Börsenzuordnung eines bestehenden Papiers korrigieren (#1–6) | Offen. Beispiel: London/Pence war falsch, gewünscht ist Xetra/Euro. Manuelle Angaben sollen erhalten bleiben; die bisherige Kursreihe darf nicht weiterverwendet werden. |
| Herkunft der Auflösung (#7) | Noch nicht als dauerhaftes eigenes Merkmal vorhanden. Die angezeigte Kurs- oder Detailquelle beantwortet diese Frage nicht. Die konkrete UI-Darstellung ist noch festzulegen; kein Wiederaufbau der in T-56 entfernten Tooltips. |
| Quellenübersicht (#8) | Durch das Plugin-System umgesetzt: `/sources` liefert Rolle, Reihenfolge, Nutzbarkeit und Fehlergrund. Keine erneute Implementierung. |
| „Vor dem Plugin-System“ | Überholt. T-19 baut auf dem vorhandenen Identitäts- und Plugin-Vertrag auf. |

### Bisherige Antworten und Rückmeldungen

Mike, 2026-09-07: „T-19 - was gilt noch. Überarbeite das Ticket nach den neuen Regeln“.
Dies beauftragt die Bestandsprüfung und Ticketüberarbeitung, keinen Produktumbau.
Die frühere Verify-Matrix enthielt keine menschlichen Antworten. Ihre leeren
Felder bleiben unverändert in der [Historie](#review-verlauf--historie) erhalten.

## Umsetzung und technische Nachweise

| Repo | Time-box | Scope | GH-Issue |
|---|---|---|---|
| StockInfo (Backend + Dashboard) | Vor Umsetzung neu schätzen; alte 4 h nicht bestätigt | Korrekturweg für bestehende Börsenzuordnungen, Schutz der Kursreihen, Auflösungsherkunft | — |

### Aktueller Codebefund

- Das Inventar der Router enthält keinen Neuauflösungs-Endpunkt. Der alte
  Vorschlag `POST /resolve/{isin}` ist kein bestehender REST-Vertrag.
- `app/repository.py`, `_find_instrument_id`, findet ein vorhandenes Papier
  zuerst über die ISIN. `_identity_update` kann dessen Identität ändern;
  `_upsert_instrument` enthält dabei keine Invalidierung der Kursreihen.
  Das ist ein offener Schutzbedarf, kein hier live reproduzierter Fehlerlauf.
- `quotes`, `daily_closes` und `daily_meta` hängen weiterhin an `instrument_id`
  (`app/db.py`). Die opake `listing_id` trennt historische Generationen dieser
  Zeile nicht automatisch. Kurswährung und Einheit müssen im Vergleich
  berücksichtigt werden, auch wenn Ticker und MIC gleich bleiben.
- T-26 speichert manuelle Angaben in `detail_overrides`, Quellwerte in
  `detail_values` (`app/detail_store.py`). Nur die alte feste TER-/ETF-Feldliste
  zu erhalten reicht deshalb nicht mehr. Nicht mehr anwendbare Details dürfen
  auch nach einer Korrektur nicht irreführend angezeigt werden.
- `GET /sources` nutzt die laufende Kette und liefert `name`, `role`,
  `position`, `configured` und `reason` (`app/routers/dashboard.py`, `sources`).
  Die frühere Frage nach einer Diagnose zusätzlich zu einem Bool ist damit
  gelöst. `configured` steht hier für tatsächliche Nutzbarkeit der Quelle.
- `ResolvedInstrument` und das Instrument-Schema speichern keinen eigenen
  dauerhaften Resolver-Namen. Kursquelle, Detailherkunft und Auflösungsherkunft
  bleiben fachlich verschiedene Informationen.

### Korrekturweg und Grenzen

Die bestehende Zeile wird über `listing_id` eindeutig adressiert. Die konkrete
REST-Form ist vor Umsetzung mit dem vorhandenen Core-Vertrag abzugleichen;
ISIN und Provider-Symbol allein reichen nicht für alle heutigen Identitäten.
Die Umsetzung soll zunächst die Börsenzuordnung desselben Wertpapiers behandeln.
Ein Wechsel zu einem anderen Papier, die Umwandlung von `listed` in `pair` oder
`isin_only` sowie das Zusammenführen vorhandener Zeilen sind kein impliziter
Teil dieses Tickets und dürfen nicht still erfolgen.

Die Oberfläche muss **vor dem Schreiben** altes und vorgeschlagenes Listing
sowie die Zahl betroffener gespeicherter Kurspunkte zeigen. Abbrechen ändert
nichts. Erst die ausdrückliche Bestätigung darf die geprüfte Änderung anwenden;
ein Endpunkt, der erst löscht und danach die Folgen zurückmeldet, erfüllt das
nicht. Zwischen Vorschau und Bestätigung veränderte Bestände dürfen nicht
unbemerkt mit einer veralteten Bestätigung überschrieben werden.

Bei gleicher Börsenzuordnung samt Kurswährung/-einheit bleiben Kursreihen und
manuelle Angaben bestehen. Bei einem Wechsel werden die betroffenen Kursreihen
verworfen, Synchronisationsgrenzen zurückgesetzt und abgeleitete Volatilität
invalidiert. Manuelle Angaben bleiben gespeichert; berechnete und manuell
gepflegte Volatilität müssen dabei unterschieden werden. Provider-Details und
deren Anwendbarkeit sind aus dem neuen Auflösungsergebnis neu zu bestimmen.

Die alte Entscheidung „löschen statt archivieren“ bleibt als bisheriger
Designvorschlag erhalten, mit ihrer Autorenschaft Codex. Sie ist keine neue
menschliche Freigabe. Vor Umsetzung sind REST-Ablauf, Grenzen und Darstellung
von #7 konkret zu entwerfen. Diese Ticketüberarbeitung startet keine Übergabe
und verändert weder Owner noch Prioritätskette.

### Verify

Die ursprünglichen Kennungen #1–9 bleiben erhalten. Ergänzungen #2a und #2b
präzisieren die bereits geforderte Bestätigung und den Schutz beim Schreiben.
Für künftige technische Läufe eine isolierte temporäre DB und kontrollierte
Resolver-Antworten verwenden: ein Wertpapier mit zwei Listings, London/GBp
und Xetra/EUR, belegte Kursreihen und manuelle Detailwerte einschließlich `0`
und `false`. Vor einer späteren menschlichen Abnahme konkrete Instanz,
Testpapier und Bedienweg oben ergänzen; aktuell existiert dieser UI-Weg nicht.

Legende: ➖ keine Live-Verifikation; Code- und Testbefunde stehen darunter.

| # | Handgriff | Erwarteter Nachweis | woher | AI |
|---|---|---|---|:--:|
| 1 | Bestehende Börsenzuordnung unverändert neu auflösen | Kurspunkte und manuelle Details vollständig erhalten | Alter #1 | ➖ |
| 2 | London/GBp → Xetra/EUR vorschlagen und bestätigen | Keine Vermischung alter und neuer Kursreihen | Alter #2 | ➖ |
| 2a | Wechsel nur vorschlagen, dann abbrechen | Vorschau nennt beide Listings und Punktzahlen; DB unverändert | Bisherige Bestätigungspflicht | ➖ |
| 2b | Bestand zwischen Vorschau und Bestätigung ändern oder Zielkonflikt erzeugen | Kein stilles Überschreiben, keine teilweise gelöschten Daten | Atomarer Korrekturweg | ➖ |
| 3 | Nach #2 Tageskurse desselben Papiers über REST abrufen | Keine gemeinsame Pence-/Euro-Reihe | Alter #3 | ➖ |
| 4 | Nach #2 berechnete Volatilität abrufen und Tageskurse neu laden | Alter berechneter Wert verworfen; Neuberechnung erst aus passender Reihe | Alter #4 | ➖ |
| 5 | Nach #2 Synchronisationsstand lesen | `daily_meta` enthält keine alten Abdeckungsbehauptungen | Alter #5 | ➖ |
| 6 | Nach #1 und #2 manuelle Details samt Währung vergleichen | Werte einschließlich `0` und `false` erhalten; Anwendbarkeit korrekt | Alter #6, T-26 | ➖ |
| 7 | Nach erfolgreicher Auflösung Herkunft abrufen | Tatsächlich auflösende Quelle dauerhaft nachvollziehbar; UI-Form vor Umsetzung konkretisieren | Alter #7 | ➖ |
| 8 | Quellenübersicht gegen konfigurierte Kette vergleichen | Rolle, Reihenfolge, Nutzbarkeit und Gründe vorhanden; bereits implementiert | Alter #8 | ➖ |
| 9 | Nach Implementierung passende Tests und Projektchecks ausführen | Fachliche Regressionen, REST und Dashboard geprüft | Alter #9 | ➖ |

Prüfung vom 2026-09-07: **51 Tests bestanden**, davon 16 Quellenkonfigurations-
und 35 Quote-Cache-Tests. Das sind bestehende automatisierte Tests, kein
Nachweis für den noch nicht implementierten Korrekturweg und kein neuer
vollständiger `make test`-Lauf.

```bash
# #8: vorhandene Quellenkonfiguration und REST-Auskunft
.venv/bin/pytest -q tests/test_sources_config.py
# #9: bestehende Cache-Regressionen, keine Abnahme von #1–7
.venv/bin/pytest -q tests/test_quote_cache.py
```

### Side-Effects

Die aktuelle Änderung betrifft nur das Ticket. Die spätere Umsetzung kann
Kursreihen löschen und den REST-Vertrag erweitern; dafür gelten die Vorschau,
Bestätigung und Transaktionsgrenzen oben. Tests verwenden eigene Daten.
Kein Archivsystem, keine Änderung des Plugin-Installationswegs und keine
erneute Umsetzung der Quellenübersicht.

### Auflösung

Offen. Am 2026-09-07 gegen den aktuellen Code abgeglichen und nach dem neuen
Ticketformat geordnet. #8 ist umgesetzt, #1–7 bleiben offen, #9 muss zur
künftigen Implementierung erneut geprüft werden. Keine Produktänderung.

## Review-Verlauf · Historie

Die ursprüngliche Fassung folgt unverändert als Beleg der IDs, leeren
Human-Felder und damaligen Designentscheidungen. Ihre Aussagen „heute“,
„hängt an nichts“ und „vor dem Plugin-System“ gelten nur für den damaligen
Stand. Aktuelle Arbeit und Einordnung stehen ausschließlich oben.

<details>
<summary>Ursprüngliche Fassung · August 2026</summary>

# T-19 · Neu auflösen, ohne Messreihen zu vermischen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | offen | 4 h | Korrekturweg, Historien-Regel, Herkunft, Quellen-Übersicht | — |

**Löst:** Der einzige Weg, eine falsche Auflösung zu korrigieren, ist heute
`DELETE /instruments/{isin}` — und der kostet Kurshistorie, Tageskurse und alle
von Hand gepflegten Kennzahlen.

> **Ziel korrigiert (Codex-Review vom 2026-08-19).** Die erste Fassung dieses
> Tickets verlangte „nur Symbol, Börse und Gattung ändern, alles andere behalten".
> Das ist **falsch** und wäre gefährlicher als der heutige Zustand — siehe
> „Warum ‚kein Datenverlust' das falsche Ziel war".

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

**Hängt an:** nichts. Sollte **vor** dem Plugin-System stehen.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Papier neu auflösen, Listing bleibt **gleich** (Ticker, MIC, Währung) | Historie und gepflegte Kennzahlen bleiben vollständig | | |
| 2 | Papier neu auflösen, Listing **wechselt** (z.B. `.L`/GBp → `.DE`/EUR) | alte Kursreihe wird **nicht** mit der neuen vermischt | | |
| 3 | nach #2: `GET /quote/{isin}/daily` | keine Reihe, die Pence und Euro mischt | | |
| 4 | nach #2: Volatilität | wird neu aufgebaut, statt aus gemischten Werten zu stammen | | |
| 5 | nach #2: `daily_meta` | behauptet keine Zeiträume mehr als synchronisiert, die zum alten Listing gehören | | |
| 6 | nach #2: manuelle Kennzahlen (TER etc.) | bleiben — sie hängen am Papier, nicht am Listing | | |
| 7 | Detailbereich einer Zeile | zeigt „aufgelöst durch: openfigi" (o.ä.) | | |
| 8 | `GET /sources` | listet alle Quellen je Rolle, mit Reihenfolge und `configured` | | |
| 9 | `make test` | Backend, Plugin-API und Dashboard grün | | |

---

## Details

### Warum „kein Datenverlust" das falsche Ziel war

`quotes` und `daily_closes` hängen **nur** an `instrument_id`. Beide haben zwar
eine `currency`-Spalte, aber:

* `UNIQUE (instrument_id, date)` — für einen Tag kann es nur **einen**
  Schlusskurs geben, egal aus welcher Notierung
* die Volatilitätsberechnung ignoriert die Währung vollständig
  (`app/services/quote_cache.py:433`):

```python
closes = [row["close"] for row in rows if row.get("close") is not None]
return annualized_volatility(closes)
```

Wechselt ein Papier von London (GBp) nach Xetra (EUR), stünde in derselben Reihe
ein Sprung von rund **5400 auf 60**. Als Tagesrendite gelesen sind das −99 %; die
Volatilität wird unbrauchbar, und der Chart zeigt einen Absturz, den es nie gab.

**Alles zu behalten ist also schlimmer als zu löschen** — es sieht plausibel aus.

### Was stattdessen gilt

Zwei Fälle, sauber getrennt:

| Fall | Kursreihen | Manuelle Kennzahlen |
|---|---|---|
| Listing **unverändert** (Ticker, MIC, Währung gleich) | bleiben | bleiben |
| Listing **gewechselt** | werden invalidiert, `daily_meta` zurückgesetzt | bleiben |

Die manuellen Kennzahlen hängen am **Papier**, nicht an der Notierung: Ein TER
ändert sich nicht, weil dasselbe Papier an einer anderen Börse gehandelt wird.
Genau die gehen heute beim Löschen mit verloren — und genau die sind es, die
niemand nachträgt.

**Entschieden (Codex, 2026-08-20): löschen, nicht archivieren.** Die alte
Kursreihe wird verworfen, und zwar erst **nach ausdrücklicher Bestätigung** in
der Oberfläche — mit Angabe, wie viele Punkte betroffen sind. Eine
Listing-Generation an `quotes`/`daily_closes` wäre sauberer, verlangt aber eine
Generationslogik in jeder Abfrage; das ist viel Aufwand für einen seltenen
Vorgang. Archivierung bleibt ein späteres Feature und ist **keine**
Voraussetzung für das Plugin-System.

### Der Korrekturweg selbst

`POST /resolve/{isin}` löst neu auf, vergleicht das Ergebnis mit dem
gespeicherten Listing und wendet die Regel oben an. Der Endpunkt meldet zurück,
was passiert ist — unverändert oder gewechselt samt Folge —, damit die
Oberfläche vor dem Verwerfen fragen kann.

### Niemand sieht, wer aufgelöst hat

`CompositeResolver` gibt das Ergebnis zurück, nicht seine Herkunft.

**Weg:** Spalte `resolved_by` am Instrument, angezeigt im Detailbereich.

### „Ich habe das Plugin installiert und es passiert nichts"

`GET /sources` zeigt je Rolle die Kette in ihrer Reihenfolge, mit Name, Art und
Konfigurationsstand. Ohne diese Ansicht ist jede Ferndiagnose Blindflug.

**Anmerkung aus der Review:** `is_configured()` liefert nur `bool` und kann
keinen Grund nennen. Für die Anzeige braucht es entweder ein strukturiertes
Ergebnis oder eine zusätzliche Diagnosemethode — Entscheidung offen, siehe Spec.

---

## Auflösung

_(offen)_

</details>

</details>
