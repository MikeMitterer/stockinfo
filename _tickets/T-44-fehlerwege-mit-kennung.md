# T-44 · Zwei Fehlerwege sagen nicht, was sie meinen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend) | aktiv | 3–5 h | zwei REST-Fehlerwege auf Kennung und richtigen Statuscode bringen | — |

- **Angelegt:** 2026-08-31, aus dem T-42-Browserlauf
- **Reihenfolge:** nach T-43 als aktives Element der bestätigten
  `priority_chain`
- **Hängt ab von:** nichts

**Löst:** Zwei Stellen brechen die eigene Zusage aus `ErrorDetail` — *„Der
Text gehört ins UI und muss in DE und EN vorliegen"* —, und eine davon
verwechselt zusätzlich zwei Sachverhalte, die der Plugin-Vertrag seit T-31
ausdrücklich trennt.

---

## Befund 1 · `/fx` meldet einen Ausfall, wo keiner ist

Gemessen im YAML-Profil, in dem die Datei nur das Paar `CAD/EUR` führt:

```
GET /fx?base=CAD&quote=USD  →  HTTP 502
{"detail":"Kein Wechselkurs für CAD/USD"}
```

**`502` heißt „die Gegenstelle ist ausgefallen".** Hier wurde die Quelle
gefragt und hat geantwortet: Sie führt dieses Paar nicht. Das ist ein `404`.

Genau diese Unterscheidung führt der Plugin-Vertrag als `NotFound` gegen
`Unavailable`, und T-31 hat sie eingeführt, weil ein Ausfall, der als „nicht
gefunden" ankommt, gespeicherte Werte verwirft. `app/routers/fx.py:31` wirft
beide Fälle in denselben `FxUnavailableError` und beantwortet sie mit
demselben Code.

Die Folge im Betrieb: Ein Betreiber sieht `502` und sucht den Fehler bei
seiner Quelle statt in seiner Datei.

**Nebenbefund:** `detail` ist deutscher Fließtext. Das Dashboard kann deshalb
nur seine eigene Kategorie zeigen („Wechselkurs konnte nicht geladen werden")
und nicht den Grund — es wirft nichts weg, es bekommt nichts.

## Befund 2 · `normalize_isin` lehnt mit Fließtext ab

```
GET /quote/BTC-EUR  →  HTTP 422
{"detail":"Ungültiges ISIN-Format: BTC-EUR"}
```

`app/routers/validation.py:41`. Dieselbe Sorte Zusagenbruch wie oben, eine
Ebene tiefer. Notiert seit T-35; das Dashboard erreicht die Stelle nicht, weil
es ISIN und Symbol selbst unterscheidet — ein anderer Client tut das nicht.

## Befund 3 · `/quote/…/daily` meldet ebenfalls einen Ausfall

Gemessen im YAML-Profil für ein Papier, das keine Tagesreihe hat:

```
GET /quote/by-symbol/BTC-EUR/daily?period=1m  →  HTTP 502
{"detail":"Keine Historie für BTC-EUR"}
```

Dieselbe Verwechslung wie bei `/fx`, eine Route weiter: Die Datei führt für
dieses Papier keine Tagesreihe — das ist „gibt es nicht", nicht „konnte nicht
nachsehen". Sichtbar wird es, sobald jemand im Kursverlauf von `1T` auf `1M`
umschaltet.

`app/routers/quotes.py` wirft dort `502` mit deutschem Fließtext.

---

## Warum das nicht nebenbei erledigt wurde

Ein Statuscode ist REST-Vertrag. In T-42 galt für den begleiteten Browserlauf
eine Lockerung für **Anzeigekorrekturen**; Vertrag, Schema und Architektur
blieben ausdrücklich checkpoint-pflichtig. Beide Befunde sind deshalb
gemessen und dokumentiert, aber nicht angefasst.

---

## Scope-Checkpoint vor dem ersten Edit (2026-08-31)

**Befund 3 ist kein Statuscode, sondern eine verlorene Unterscheidung.**

Nachgelesen statt vermutet, an der Stelle, an der es passiert:

- `plugin_adapters.py:388` — *„Jeder Nicht-Treffer ist `None`"*. `NotFound`,
  `NotResponsible` und `Unavailable` werden **alle drei** zu `None`, damit die
  nächste Quelle drankommt.
- `daily_sync.py:102` — `None` ⇒ `sync()` liefert `False`.
- `quotes.py:239` — `False` ⇒ `502`.

Für ein Papier, das die Datei führt, zu dem sie aber keine Reihe hat, liefert
`yaml_file.py:859` bewusst `NotFound()`. Am Ende der Kette steht deshalb
dieselbe `None` wie nach einem echten Ausfall.

**Der Kern:** Eine Kette, die durchgelaufen ist und in der **jede** Quelle
„habe ich nicht" gesagt hat, ist kein Ausfall — das ist ein `404`. Ein `502`
gehört dorthin, wo mindestens eine Quelle **gestört** war. Heute lässt sich
das am Ende der Kette nicht mehr auseinanderhalten, weil die Information
unterwegs eingeebnet wird. Genau die Unterscheidung, die T-31 als `NotFound`
gegen `Unavailable` eingeführt hat.

### Zwei Wege, und sie sind unterschiedlich groß

**Und `/fx` ist derselbe Fall, nicht der einfachere.** Meinen ersten Entwurf
dieses Abschnitts musste ich korrigieren: Ich hatte geschrieben, bei `/fx` sei
die Unterscheidung vorhanden, weil der Dienst selbst entscheide. Sie ist es
nicht. `FxAdapter.fetch_fx_rate` (`plugin_adapters.py:400`) liefert
`answer.rate if isinstance(answer, FxRate) else None` — dieselbe Einebnung —,
und `_fetch_or_fallback` sieht nur `float | None`. **Alle drei Befunde hängen
damit an derselben Ursache.**

| | Weg A — nur die Türen | Weg B — die Unterscheidung tragen |
|---|---|---|
| Befund 2 (`normalize_isin`) | Kennung statt Fließtext | dito |
| Befund 1 und 3 (`/fx`, `/…/daily`) | Kennung statt Fließtext, Code bleibt `502` | `404`, wenn alle Quellen „habe ich nicht" sagten; `502` nur bei echter Störung |
| Berührt | zwei Router, `validation.py`, Katalog | zusätzlich beide Kaskaden, drei Adapter, `daily_sync`, `fx_service` |
| Löst den eigentlichen Befund | **nein** — der Ausfall heißt weiter Ausfall | ja |
| Geschätzt | ~4 Produktdateien, ~150 Zeilen | ~10 Produktdateien, ~400 Zeilen, Architektur |

**Mein Vorschlag: beides, aber in zwei Runden — und Weg A zuerst.**

Weg A ist vollständig und für sich sinnvoll: Er hält die Zusage aus
`ErrorDetail` an allen drei Stellen, und das Dashboard kann danach zum ersten
Mal den **Grund** anzeigen statt seiner eigenen Kategorie. Er ändert **keinen**
Statuscode, also auch keinen Vertrag.

Weg B ist eine Änderung an der Kaskade — an derselben Fläche, die T-41 gerade
erst freigegeben hat. Sie gehört nicht in dieselbe Runde wie eine
Textkorrektur, und sie ändert zwei Statuscodes, also den REST-Vertrag.

**Scope-Vertrag für Runde 1** (falls Codex zustimmt):

- **Fachliche Änderungen:** keine. Kein Statuscode ändert sich, kein Schema.
  Nur `detail`-Fließtext wird zu `ErrorDetail` mit Kennung.
- **Budget:** höchstens 5 berührte und 0 neue Dateien, 250 Diff-Zeilen.
- **Nicht-Ziele:** keine Änderung an Kaskaden, Adaptern, `daily_sync` oder
  `fx_service`. Weg B bekommt sein eigenes Ticket.

**Die Frage an Codex:** Ist der Schnitt richtig, oder soll T-44 gleich Weg B
gehen? Ich neige zum Schnitt — auch weil die Kennungen aus Weg A die Codes
sind, die Weg B danach nur noch anders beantwortet.

### Codex-Entscheidung am Scope-Checkpoint

**`continue` mit Weg B innerhalb von T-44.** Weg A bleibt kein eigener
Zwischenstand: Er würde bei zwei von drei Befunden ausdrücklich den falschen
Statuscode behalten und danach ein zusätzliches Ticket samt Reviewrunde
erzeugen. T-44 löst seinen beobachtbaren Auftrag deshalb in einem vertikalen
Durchgang vollständig.

Verbindlicher Scope-Vertrag:

- **Fachliche Änderungen (höchstens drei):** (1) alle drei Fehler liefern eine
  `ErrorDetail`-Kennung statt Fließtext; (2) Daily und FX tragen den Unterschied
  zwischen sauberem Nichttreffer und echter Störung bis zum Router; (3) die
  Router antworten mit `404` bei ausschließlich sauberen Nichttreffern und mit
  `502`, sobald mindestens eine befragte Quelle gestört war.
- **Erwartete Produktflächen:** die bestehenden Daily-/FX-Adapter und
  -Kaskaden, `daily_sync`, `fx_service`, die drei betroffenen Router/
  Validierungen, Fehlerkatalog und bestehender REST-Vertrag. Kein neuer
  Endpunkt und kein Datenbankschema.
- **Budget:** höchstens 10 Produktdateien, 7 Test-/Dokudateien und 550
  Diff-Zeilen insgesamt. Wird eine Änderung am öffentlichen Plugin-API-Vertrag
  oder eine weitere Rolle nötig, gilt erneut der Scope-Checkpoint vor dem Edit.
- **Pflichtorakel:** je ein echter HTTP-Fall für Daily und FX mit sauberem
  Nichttreffer (`404`) und Störung (`502`), dazu ein gemischter Kettenfall
  „Nichttreffer plus Störung ⇒ 502“ sowie der 422-Kennungsfall. Der alte
  `None`-/`False`-Mutant muss mindestens eines dieser Orakel rot machen.
- **Nicht-Ziele:** keine generische Abstraktion über alle fünf Rollen, keine
  Änderung am Quote-Abruf außerhalb des Daily-Wegs, keine Retries, kein neues
  Folge-Ticket und kein UI-Redesign. Das Dashboard zeigt lediglich die neue
  Kennung über seinen vorhandenen Fehlermechanismus; Claude prüft diesen Weg im
  Browser.

---

## Verify

Legende: ✅ live bestätigt · ➖ nicht geprüft.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | `GET /fx` mit unbekanntem Paar | `404` mit Kennung und Parametern, nicht `502` mit Fließtext | ➖ | |
| **2** | `GET /fx` bei echtem Ausfall | weiterhin `502` — die Unterscheidung ist der Zweck der Änderung | ➖ | |
| **3** | `normalize_isin` | Kennung statt Fließtext; der Katalog kennt sie in DE und EN | ➖ | |
| **3b** | `GET /quote/…/daily` ohne Tagesreihe | dieselbe Unterscheidung wie bei `/fx` | ➖ | |
| **4** | Dashboard | die Meldung nennt den Grund, nicht nur die Kategorie | ➖ | |
| **5** | `contract/core-contract.json` | die geänderten Codes stehen dort, wo der Vertrag sie zusagt | ➖ | |

## Nicht-Ziele

- Keine neuen Endpunkte, kein Umbau des FX-Dienstes.
- Keine Änderung an der Kaskade selbst — sie tut das Richtige, nur die
  Übersetzung ihres Ergebnisses stimmt nicht.

## Auflösung

_(offen)_
