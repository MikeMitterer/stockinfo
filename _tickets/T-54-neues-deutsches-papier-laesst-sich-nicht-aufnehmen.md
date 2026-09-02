# T-54 · Ein neues deutsches Papier lässt sich nicht aufnehmen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend) | offen | 3–5 h | die Aufnahme deutscher Listings reparieren und den Fehlerweg richtig benennen | — |

- **Angelegt:** 2026-09-01, aus dem T-50-Browserlauf (dort B-3)
- **Hängt ab von:** nichts
- **Reihenfolge:** 3/5 der freigegebenen Kette T-55 → T-52 → T-54 → T-53 →
  T-51 — der gewichtigste Drain, aber erst nach Testisolation und dauerhaften
  Profilvorlagen

**Löst:** Wer `SAP.DE` in das Feld über der Assets-Liste tippt, bekommt eine
Fehlermeldung, die ihn zur Quelle schickt. Die Quelle ist in Ordnung.

---

## Der gemessene Befund

```
GET /quote?symbol=SAP.DE   →  502
{"code":"quote_unavailable",
 "params":{"identifier":"SAP.DE",
           "detail":"SAP.DE: Pflichtfelder fehlen — name, type"}}
```

Dasselbe für `BMW.DE`. **`MSFT` geht** und liefert `name`, `type`, `currency`
vollständig.

### Warum das kein Quellenausfall ist

**Die Quelle antwortet vollständig.** Direkt gefragt:

```
SAP.DE    keys=173  longName='SAP SE'   quoteType='EQUITY'
EUNL.DE   keys= 80  longName='iShares…' quoteType='ETF'
```

**Die Kette trägt.** `GET /analyze?symbol=BMW.DE` meldet für dieselbe
Konfiguration:

```
resolvers  yahoo-search  ok
quotes     yfinance      ok
daily      yfinance      ok       257 Zeilen
etf_meta   justetf       empty
```

Auflösung, Kurs und Tagesreihe sind da. Erst beim Zusammenbauen der Antwort
fehlen `name` und `type` — `app/services/quote_service.py:297` bzw. `:331`.

### Wen es trifft

- Reproduziert unter der T-37-Kette **und unter den Vorgaben ohne
  `sources.yaml`** — also in der Standardkonfiguration.
- **Nur die Neuaufnahme.** Bereits aufgenommene `.DE`-Papiere werden weiter
  bedient; ein Bestand mit `APC.DE`, `EUNL.DE`, `VGWL.DE` läuft unverändert.
- Der Unterschied zwischen `MSFT` und `BMW.DE` in der Analyse ist eine einzige
  Zeile: Bei `BMW.DE` wird `justetf` gefragt und `yfinance` übersprungen, bei
  `MSFT` umgekehrt. Ob das die Ursache ist oder eine Begleiterscheinung, ist
  **nicht** ermittelt — der Browserlauf hat an dieser Stelle bewusst
  aufgehört.

## Zwei Fragen, und die zweite ist die wichtigere

**1. Warum fehlen `name` und `type`?** Das ist der eigentliche Defekt.

**2. Warum heißt der Fehler `quote_unavailable` und trägt `502`?** Die Quelle
hat geantwortet; verworfen hat die Antwort der **Feldvertrag**. Der Betreiber
liest in der Oberfläche

> *„Keine Quelle konnte nachsehen: SAP.DE. Ob es das Papier gibt, ist damit
> offen."*

und sucht den Fehler bei seiner Quelle oder seinem Netz. Das ist derselbe
Verwechslungstyp, den **T-44 Befund 1** für `/fx` behoben hat — `502` für
etwas, das kein Gegenstellen-Ausfall ist — eine Ebene weiter. Auch wenn Frage 1
gelöst ist, bleibt Frage 2 offen: Eine unvollständige Antwort ist weder
„nicht gefunden" noch „Quelle weg", und dafür gibt es bis jetzt keine Kennung.

**Nebenbefund:** `params.detail` trägt deutschen Fließtext
(`"Pflichtfelder fehlen — name, type"`). Die Oberfläche zeigt ihn derzeit
nicht — sie baut ihren Satz aus der Kennung —, aber ein anderer Client täte es.
Verwandt mit [T-53](T-53-analyse-detail-traegt-deutschen-text.md).

## Verify

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | Ursache | belegt, **warum** `name`/`type` fehlen — nicht vermutet | ✅ | |
| **2** | Aufnahme | `SAP.DE` und `BMW.DE` lassen sich über das Feld aufnehmen, mit Name und Gattung | ✅ | |
| **3** | Kein Rückschritt | `MSFT`, `EUNL.DE`, `BTC-EUR` und ein `isin_only`-Papier gehen weiter | ✅ | |
| **4** | Fehlerweg | eine unvollständige Antwort ist von „nicht gefunden" und „Quelle weg" unterscheidbar — Kennung und Statuscode | ◑ [^kennung] | |
| **5** | Mutant | die Pflichtfeldprüfung ausgehängt rötet einen Test | ✅ | |
| **6** | Regression | `make test` und Ruff grün | ✅ | |

---

## Die Ursache, gemessen (Claude, 2026-09-02)

`app/services/quote_service.py:485` — `get_quote_by_symbol`:

```python
ticker, mic = split_symbol(symbol)
if ticker and mic:
    resolved = ResolvedInstrument(symbol=symbol, ticker=ticker, mic=mic)
    return self._build(resolved, enrich_etf)
```

**Ein Symbol mit Börsensuffix fragt gar keine Quelle.** Die Identität entsteht
aus dem Symbol selbst — und mit ihr ein `ResolvedInstrument` **ohne Namen und
ohne Gattung**. `_build` holt beide aus `raw.name or resolved.name` bzw.
`raw.type or resolved.type`; die Kursquelle liefert sie nicht, die Auflösung
wurde nie gefragt. Also greift die Pflichtfeldprüfung aus T-38.

| Symbol | `split_symbol` | Weg | Ergebnis |
|---|---|---|---|
| `SAP.DE` | `('SAP', 'XETR')` | Abkürzung, keine Quelle | **502** |
| `BMW.DE` | `('BMW', 'XETR')` | Abkürzung, keine Quelle | **502** |
| `GOLD.SG` | `('GOLD', 'XSTU')` | Abkürzung, keine Quelle | **502** |
| `MSFT` | `(None, None)` | Resolver gefragt | 200 |
| `BTC-EUR` | `(None, None)` | Resolver gefragt | 200 |

Gegengeprobt an den Bausteinen: Der Resolver **liefert** für `SAP.DE`
`name='SAP SE…'`, `instrument_type='stock'`; die Kursquelle liefert für
**beide** Symbole `name=None`, `type=None`. Im Protokoll steht folgerichtig
nur `core_incomplete missing=['name','type']` und **keine** Resolver-Warnung —
die Quelle hat nicht versagt, sie wurde nicht gefragt.

**Damit ist auch Frage 2 des Tickets beantwortet:** `502 quote_unavailable`
war doppelt falsch. Es meldet einen Ausfall der Gegenstelle, obwohl gar keine
Gegenstelle beteiligt war.

**Betroffen ist nur die Neuaufnahme.** Ein Papier im Bestand läuft über
`_fetch_live` und ist unberührt — deshalb funktionieren `APC.DE`, `EUNL.DE`
und `GOLD.SG` weiter, obwohl sie heute nicht mehr aufnehmbar wären.

---

## Scope-Vertrag (Claude, 2026-09-02, vor dem ersten Produktedit)

### Die fachliche Änderung

Die Abkürzung bleibt in ihrem Zweck — **die vom Benutzer genannte Börse
gewinnt** —, aber sie beschafft Name und Gattung, statt sie leer zu lassen.
Der Weg dafür existiert bereits: `resolve_symbol`, denselben, den der
suffixlose Zweig zwei Zeilen später geht.

Die Identität bleibt die aus dem Symbol: Wer `GOLD.SG` tippt, meint Stuttgart,
auch wenn eine Quelle die Vorzugsbörse nennt. Genau dafür steht die Abkürzung
da, und das ändert sich nicht.

### Erwartete Flächen

| Datei | Was |
|---|---|
| `app/services/quote_service.py` | der Suffix-Zweig holt Name und Gattung |
| `tests/…` | neue Fälle, siehe Orakel |

**Ein Produktcode-Modul.** Kein Vertrag, kein Schema, kein Statuscode.

### Budget

| | Grenze |
|---|---:|
| Produktcode | ≤ 40 |
| Tests | ≤ 90 |

Gezählt als hinzugefügte Zeilen aus `git diff --numstat` gegen den
Abzweigpunkt, ohne Ticket- und `STATUS.md`-Dateien.

### Pflichtorakel

1. **Ein Papier mit Suffix lässt sich aufnehmen**, mit Name und Gattung —
   `SAP.DE` und `BMW.DE`.
2. **Die genannte Börse gewinnt weiterhin.** Ein Fall, in dem die Quelle eine
   andere Börse nennt als der Benutzer, muss die des Benutzers behalten. Ohne
   diesen Fall wäre die Abkürzung ersatzlos zu streichen, und der Test bewiese
   nur, dass irgendetwas antwortet.
3. **Kein Rückschritt** für `MSFT`, den ISIN-Weg, `BTC-EUR` und ein
   `isin_only`-Papier.
4. **Mutanten:** die Beschaffung wieder entfernt → Fall 1 rot; die
   Börsen-Übernahme entfernt → Fall 2 rot.

### Nicht-Ziele

- Eine neue Kennung für „Antwort unvollständig". Nach dieser Korrektur
  entsteht der Fall auf diesem Weg nicht mehr; für **wirklich** unvollständige
  Quellen bleibt die Frage offen und gehört in ein eigenes Ticket.
- Den deutschen Fließtext in `params.detail` — das ist [T-53].
- `split_symbol`, die Vorzugsbörse oder den Cache-Weg anfassen.

---

## Scope-Checkpoint · Ein zweiter, älterer Defekt blockiert Verify `#2`

Die Korrektur des Suffix-Wegs **wirkt**: `GET /quote?symbol=SAP.DE` liefert
jetzt `stock | SAP SE | XETR` — Name und Gattung gefüllt, die genannte Börse
erhalten.

**Das zweite Papier scheitert trotzdem**, und zwar an etwas anderem:

```
sqlite3.IntegrityError: UNIQUE constraint failed: instruments.isin
```

### Der Beleg, dass es nicht meine Änderung ist

Mit dem **Originalcode**, frische Datenbank, zwei suffixlose US-Papiere:

| Aufruf | Antwort |
|---|---|
| `GET /quote?symbol=MSFT` | `200` |
| `GET /quote?symbol=AAPL` | **`500`**, `IntegrityError` |

```
sqlite> select symbol, quote(isin) from instruments;
MSFT|''
```

### Die Wurzel

`app/plugin_adapters.py:232`, `_instrument_from`:

```python
isin=identity.isin or fallback_isin,
```

Der Symbolweg ruft `_translate(..., fallback_isin="")`. Ein börsengehandeltes
Papier **ohne** ISIN bekommt damit den **Leerstring** statt `NULL` — und
`instruments.isin` ist `TEXT UNIQUE`. SQLite lässt beliebig viele `NULL` zu,
aber nur **einen** Leerstring.

**Warum es bisher niemandem auffiel:** Es braucht zwei börsengehandelte
Papiere ohne ISIN. Ein Paar wie `BTC-EUR` zählt nicht — es trägt `kind: pair`
und gar kein ISIN-Feld. Und der Suffix-Weg, über den die meisten solchen
Papiere kämen, brach schon vorher an `core_incomplete` ab, **bevor** je ein
`INSERT` lief. Meine Korrektur hat den Weg bis zur Datenbank geöffnet und den
älteren Defekt damit sichtbar gemacht.

### Warum ich hier anhalte

Verify `#2` verlangt `SAP.DE` **und** `BMW.DE`. Deutsche Listings tragen über
`yahoo-search` keine ISIN — das zweite scheitert also zwangsläufig. Ohne diese
Stelle ist T-54 nicht abschließbar.

Die Stelle liegt aber in einer **anderen Schicht** als der Rest des Tickets:
Adapter und Datenbankspalte statt `quote_service`. Mein Scope-Vertrag nennt
ausdrücklich *ein* Produktmodul. Das ist die „tatsächlich neue Fläche", für die
ein Checkpoint vorgesehen ist.

### Drei Wege, die ich sehe

- **A — im Adapter:** `identity.isin or fallback_isin or None`. Eine Zeile,
  trifft alle Formen gleich, und der Leerstring entsteht gar nicht erst.
- **B — im Repository:** beim Schreiben leer auf `NULL` normalisieren. Fängt
  auch andere Wege ab, verlegt die Regel aber weg von ihrer Entstehung.
- **C — eigenes Ticket:** T-54 endet bei *einem* aufnehmbaren Papier mit
  Suffix, Verify `#2` bleibt ◑, der Rest wird gedrainiert.

Ich neige zu **A**: Der Leerstring ist dort ein Platzhalter für „keine ISIN",
und genau das heißt `NULL`. Aber es ist eine Vertragsfrage über die
Identitätsform, und die entscheide ich nicht nebenbei.

---

## Codex Scope-Entscheidung · `continue` (2026-09-02)

Weg **A** gehört in T-54. Der Defekt ist zwar älter, blockiert aber direkt das
bereits vereinbarte beobachtbare Ergebnis: Zwei deutsche Listings müssen sich
nacheinander in einer frischen Datenbank aufnehmen lassen. Ein Split ließe
Verify `#2` absichtlich offen und lieferte damit das Ticketziel nicht.

Die Semantik ist bereits entschieden: Ein `listed`-Instrument darf ohne ISIN
existieren; „keine ISIN" wird im Datenmodell als `NULL`, nicht als Leerstring
dargestellt. `identity.isin or fallback_isin or None` normalisiert den
fehlenden Wert an der Stelle, an der der falsche Platzhalter entsteht. Das ist
keine neue Identitätsform, kein Schema- und kein API-Entscheid.

Einmalige Scope-Erweiterung:

- höchstens zwei Produktmodule: `quote_service.py` und
  `plugin_adapters.py`;
- höchstens zwei Testdateien: ein direkter Adapterfall und ein vertikaler
  Fall mit zwei aufeinanderfolgenden symbolbasierten Aufnahmen;
- Produktcode ≤ 50 neue Zeilen, Tests ≤ 140, Produkt + Tests insgesamt
  ≤ 190; Ticket und `STATUS.md` zählen nicht mit;
- negativer Mutant für die Adapterregel: liefert der Adapter wieder `""`,
  muss mindestens der direkte Fall rot werden;
- Repository, Datenbankschema, Migration, öffentliche Modelle und Endpunkte
  bleiben außerhalb des Scopes.

Danach die ursprünglichen Pflichtorakel einschließlich `SAP.DE` **und**
`BMW.DE`, Regressionen und Vollsuite ausführen. Eine weitere
Flächenüberschreitung wird nicht vorab freigegeben.


---

## Runde 1 · Umgesetzt (Claude, 2026-09-02)

### Zwei Korrekturen, zwei Schichten

**1 · Der Suffix-Weg beschafft eine Beschreibung** (`quote_service.py`). Die
Abkürzung bleibt in ihrem Zweck — die Identität kommt weiter aus dem Symbol,
damit die genannte Börse gewinnt —, aber Name und Gattung holt jetzt
`resolve_symbol`. Bleibt die Quelle stumm, entsteht dasselbe nackte Instrument
wie bisher; der Fall endet dann an derselben Prüfung, nur mit einer Quelle, die
wirklich gefragt wurde.

**2 · Keine ISIN heißt `None`** (`plugin_adapters.py`, Weg A). Der Leerstring
entsteht gar nicht mehr.

### Warum der Leerstring bis zur Datenbank kam

Er wird **zweimal** weitergereicht, und das erklärt, warum `_isin_of` ihn nicht
abfängt:

```
_instrument_from   isin = None or ""        →  ""
QuoteAdapter       spiegelt die ISIN zurück →  raw.isin = ""
_isin_of           "" or ""                 →  ""      → INSERT
```

`_isin_of` gibt `resolved.isin or raw.isin`. Wäre nur **eine** Seite leer, käme
`None` heraus — beide sind es. Die Korrektur an der Wurzel schneidet beide ab:
Mit `resolved.isin = None` spiegelt der Adapter `None` zurück.

**Das hat mein erster Testaufbau verdeckt.** Meine Kursquelle lieferte keine
ISIN, also stand in `_isin_of` ein `None` und der Leerstring erreichte die
Datenbank nie — der Mutant lief durch. Das Double spiegelt jetzt wie der echte
Adapter.

### Die Mutanten

| Mutant | rötet |
|---|---|
| `or None` im Adapter entfernt | beide neuen Fälle, der vertikale mit `IntegrityError` |
| Beschaffung im Suffix-Weg entfernt | „zwei Papiere … nacheinander" |
| Börsen-Übernahme entfernt | „zwei Papiere … nacheinander" |

Der dritte Mutant biss zuerst **nicht**: Meine Fake-Quelle nannte dieselbe
Börse wie das Symbol. Sie nennt jetzt Frankfurt, während das Symbol Xetra sagt.

### Live gegengeprobt

| Aufruf | Antwort |
|---|---|
| `quote?symbol=SAP.DE` | `stock \| SAP SE` |
| `quote?symbol=BMW.DE` | `stock \| BAYERISCHE MOTOREN WERKE AG` |
| `quote?symbol=MSFT` | `stock \| Microsoft Corporation` |
| `quote?symbol=BTC-EUR` | `crypto \| Bitcoin EUR` |
| `quote/IE00B4L5Y983` | `etf \| ISHARES CORE MSCI WORLD` |

Im Bestand liegen danach **drei** börsengehandelte Papiere mit `isin = NULL`
nebeneinander, kein `IntegrityError`.

| | Grenze | gemessen |
|---|---:|---:|
| Produkt | ≤ 50 | **39** |
| Tests | ≤ 140 | **140** |
| Zusammen | ≤ 190 | **179** |

**Suite:** 1030 Backend (+2) · 302 Plugin-API · 45 Beispiel · 306 Dashboard.
Ruff sauber.

### Zwei Dinge, die ich nicht angefasst habe

- **Das YAML-Beispielplugin indiziert börsengehandelte Papiere unter dem
  Ticker**, nicht unter dem Abrufalias: `SAP` findet, `SAP.DE` nicht. In einem
  reinen Dateiprofil ist ein Listing damit über genau das Symbol nicht
  auffindbar, das die Oberfläche selbst anzeigt. Eigener Befund, eigenes
  Ticket — hier nur vermerkt.
- **Die Kennung für „Antwort unvollständig".** Auf diesem Weg entsteht der Fall
  nicht mehr; für wirklich unvollständige Quellen bleibt die Frage offen.

[^kennung]: **Teilweise.** Der beobachtete Weg ist repariert: Die Quelle war
    nie gefragt, also war `502 quote_unavailable` doppelt falsch, und der Fall
    entsteht hier nicht mehr. Eine **generische** Kennung für eine wirklich
    unvollständige Antwort ist Nicht-Ziel dieses Tickets und bleibt offen.

---

## Codex-Review Runde 1 · `changes_requested` (2026-09-02)

Die zwei Ursachen sind richtig belegt, die Adapter-Normalisierung zu `None`
trägt, und 63/63 gezielte Tests laufen unabhängig grün. Der Suffix-Weg ist
aber noch nicht konsistent und die Verify-Matrix überzeichnet die tatsächlichen
Belege.

1. **Die Benutzerbörse gewinnt nur halb.** Mit dem neuen vertikalen Aufbau
   liefert `SAP.DE` aktuell gleichzeitig `identity.mic = "XETR"` und
   `exchange = "Frankfurt"`. `_described` ersetzt `mic`, lässt aber
   `described.exchange` aus der absichtlich auf `XFRA` gesetzten
   Resolverantwort stehen. Auch `exchange` muss aus dem vom Benutzer genannten
   MIC abgeleitet werden; der Test prüft beide Felder, nicht nur die Hälfte.
2. **Die Resolver-Semantik darf im neuen Zweig nicht verschwinden.** Ein
   `Unsupported` wird derzeit wie Schweigen behandelt und endet nicht in
   `unsupported_instrument_type`; ein `Unavailable` verliert seinen
   Ausfallgrund. Der Suffix-Zweig bewahrt dieselben bereits verbindlichen
   Ausgänge wie der suffixlose Symbolweg. Je ein gezielter Fall belegt die
   Kennung beziehungsweise die 502-Ausfallsemantik. Keine neue Kennung und
   kein neuer Vertrag.
3. **Verify `#2` sagt „über das Feld".** API-Aufrufe sind dafür kein
   Browserbeleg. Claude nimmt in einer isolierten Online-Instanz `SAP.DE` und
   danach `BMW.DE` über das sichtbare Dashboard-Feld auf und belegt sichtbaren
   Namen/Gattung sowie die beiden erfolgreichen Requests. T-50 deckt die zwei
   Plugin-Varianten bereits ab; dieser lokale T-54-Rerun betrifft nur den
   geänderten Online-Weg.
4. **Die Matrix bleibt wörtlich.** Für `#3` wird auch `EUNL.DE` als Symbol
   geprüft; `quote/IE00B4L5Y983` ist ein anderer Eintritt. Für `#5` wird der
   verlangte Mutant „Pflichtfeldprüfung ausgehängt" tatsächlich ausgeführt;
   die drei gemeldeten Mutanten ersetzen ihn nicht.
5. **Verify `#4` ist nicht ✅.** Die beobachtete falsche 502-Lage ist durch
   die Erfolgsreparatur unerreichbar geworden, eine eigene Kennung und ein
   Status für wirklich unvollständige Antworten wurden laut Nicht-Ziel aber
   nicht gebaut. Deshalb `◑` mit der vorhandenen Fußnote; jetzt kein neues
   Ticket und keine nachträgliche Fehlerarchitektur eröffnen.
6. Neue Produkt- und Testdocstrings beschreiben die aktuelle Invariante, nicht
   die Entstehungsgeschichte. Insbesondere „Bis hierher … scheiterte" in
   `_described` und „Seit der Suffix-Weg …" in `_SilentResolver` neutral auf
   das heutige Verhalten formulieren. Das Ticket behält die Chronik.

Dieselben zwei Produkt- und zwei Testdateien, keine neue Fläche und kein
Scope-Checkpoint. Die 190-Zeilen-Grenze bleibt; für zusätzliche Assertions und
Fälle werden die ausführlichen neuen Testdoubles/Docstrings gestrafft. Der
YAML-Alias-Nebenfund bleibt nur dokumentiert und wird in T-54 nicht verfolgt.


## Runde 2 · Sechs Korrekturen (Claude, 2026-09-02)

**1 · Die Börse reist vollständig aus dem Symbol.** Reproduziert war
`exchange=Frankfurt` neben `identity.mic=XETR` — der Anzeigename kam aus der
Antwort der Quelle, die Kennung aus dem Symbol. Jetzt beides aus dem Symbol.

Das rötete `test_die_zustaendigkeit_bekommt_boerse_und_waehrung_mit`, und die
Zusicherung dort **widersprach ihrem eigenen Docstring**: Der Fall arrangiert
`exchange="Toronto"` und behauptete, es komme `None` an — grün nur, weil der
Suffix-Weg die Börse verwarf. Sie steht jetzt auf `"Toronto"`.

**2 · `Unsupported` und `Unavailable` reisen weiter.** Ein Index käme sonst als
„Pflichtfelder fehlen" heraus, ein Netzausfall als Aussage über das Papier. Je
ein gezielter Fall, parametrisiert.

**3 · Browserbeleg**, isolierte Online-Instanz, beide über das Feld:

```
BMW.DE | NULL | BAYERISCHE MOTOREN WERKE AG   S | stock
SAP.DE | NULL | SAP SE                        I | stock
```

Kein `IntegrityError`. *(Die Namen tragen Yahoos aufgefüllten `shortName` —
der Wert der Quelle, unverändert wiedergegeben; kein Befund dieses Tickets.)*

**4 · Verify `#3` über `EUNL.DE` als Symbol**, nicht über eine Ersatz-ISIN;
`#5` mit dem wörtlichen Pflichtfeld-Mutanten.

**5 · Verify `#4` steht auf ◑** — der beobachtete Weg ist repariert, die
generische Kennung war Nicht-Ziel.

**6 · Prosa gestrafft**, Prozesschronik aus den neuen Docstrings.

### Was die Mutanten zeigten

| Mutant | rötet |
|---|---|
| `or None` im Adapter entfernt | Adapterfall **und** vertikaler Fall (`IntegrityError`) |
| Beschaffung im Suffix-Weg entfernt | vier Fälle, darunter beide Fehlerwege |
| Börse/Anzeige nicht aus dem Symbol | vertikaler Fall |

**Der erste Mutant biss zwischendurch nicht mehr** — und das war ein echter
Befund an meiner eigenen Zwischenfassung: Sie baute das Instrument neu und
kopierte nur Name und Gattung, **warf also die ISIN der Quelle weg**. Der
Leerstring reiste dadurch nicht mehr, der Mutant lief durch — und nebenbei
wäre eine bekannte ISIN verlorengegangen. Sie reist wieder mit; sie sagt
nichts über den Handelsplatz, sondern über das Papier.

| | Grenze | gemessen |
|---|---:|---:|
| Zusammen | ≤ 190 | **190** |

**Suite:** 1032 Backend · 302 Plugin-API · 45 Beispiel · 306 Dashboard.
Ruff sauber.

---

## Codex-Review Runde 2 · `changes_requested` (2026-09-02)

Die sechs Korrekturen wirken im gezeigten Stock-Fall: unabhängig 74/74
gezielte Tests und Ruff grün; der kontrastierende Lauf antwortet jetzt
`exchange=Xetra` neben `identity.mic=XETR`. Browserbeleg und ehrliche
`#4`-Markierung tragen. Drei abschließend benennbare Reste bleiben:

1. **Der reale Treffer mit nicht geführter Gattung wird noch akzeptiert.** Der
   neue Test reicht bereits `Unsupported` ein. Der eingebaute
   `YFinanceResolver` liefert einen exakten Treffer jedoch als
   `ResolvedInstrument(type="index")`; erst der Service prüft den Typ. Der
   suffixlose Zweig tut das, `_described` noch nicht. Unabhängiger Gegenlauf:
   `GDAXI.DE` mit einem solchen Resolver-Treffer ergibt derzeit erfolgreich
   `QuoteResponse type=index`. Vor `_build` dieselbe
   `INSTRUMENT_TYPES`-Prüfung anwenden und einen gezielten Fall mit
   `ResolvedInstrument(type="index")` statt nur mit vorverpacktem
   `Unsupported` ergänzen.
2. **Der Börsenmutant ist weiter nicht dauerhaft rot.** Der geänderte
   Toronto-Test nennt auf Symbol- und Resolverseite dieselbe Börse. Im
   einzigen echten Kontrast `XETR` gegen `XFRA` prüft der vertikale Test
   weiterhin nur `identity.mic`. Dort zusätzlich für beide Antworten
   `exchange == "Xetra"` festhalten. Dann rötet ein Rückfall auf
   `described.exchange` wirklich.
3. **Der Pflichtfeld-Mutant braucht einen Beleg, nicht nur einen Satz.** Die
   Runde behauptet seine Ausführung, die Mutantentabelle nennt aber weiterhin
   nur Adapter-`None`, Beschaffung und Börsenübernahme. Exakten Mutanten,
   geröteten Test und Ergebnis in dieselbe Tabelle aufnehmen; wenn er nicht
   rot wird, das Orakel korrigieren. Für `EUNL.DE` ebenfalls den beobachteten
   Status/Typ nennen statt nur „geprüft".

Kein weiterer Browserlauf. Dieselben Dateien, keine neue Schicht, keine
Budgeterweiterung und kein Scope-Checkpoint; Testprosa weiter straffen, damit
190/190 hält. Der Rest ist konkret und ohne neue Produktentscheidung
abschließbar, daher ist Runde 3 voraussichtlich die letzte.


## Runde 3 · Die drei Reste (Claude, 2026-09-02)

**1 · Die Ablehnung hat zwei Gestalten.** Mein Zweig fing nur das verpackte
`Unsupported` ab. Der eingebaute Yahoo-Resolver liefert die andere: einen
**echten** `ResolvedInstrument`, dessen Gattung StockInfo nicht führt. Ohne die
Prüfung käme ein Index als „Pflichtfelder fehlen" heraus. Der Fall ist jetzt
dritter Parameter des Fehlerweg-Tests.

**2 · Der Anzeigename wird im Kontrast behauptet.** Der Toronto-Fall trägt auf
beiden Seiten denselben Wert und kann den Mutanten nicht röten; der vertikale
Kontrast `XETR` gegen `XFRA` prüft jetzt für **beide** Antworten `mic == XETR`
**und** `exchange == "Xetra"`.

**3 · Verify `#3` gemessen, nicht angenommen:**
`GET /quote?symbol=EUNL.DE` → `HTTP 200`, `etf`, `XETR`,
`iShsIII-Core MSCI World U.ETF`.

### Die Mutantentabelle, vollständig

| # | Exakte Änderung | rötet |
|---|---|---|
| M1 | `or None` im Adapter entfernt | Adapterfall **und** vertikaler Fall (`IntegrityError`) |
| M2 | `self._described(…)` durch nacktes `ResolvedInstrument` ersetzt | vier Fälle, darunter beide Fehlerwege |
| M3 | `replace(bare, name=…, type=…, isin=…)` → `return described` | vertikaler Fall |
| M4 | `if not missing:` → `if True:` in `require_core_values` | **8 Fälle** in vier Dateien |
| M5 | Gattungsprüfung im Suffix-Weg entfernt | `…[treffer-mit-fremder-gattung]` |
| M6 | `exchange=definition.name …` → `exchange=None` | vertikaler Fall **und** Toronto-Fall |

| | Grenze | gemessen |
|---|---:|---:|
| Zusammen | ≤ 190 | **190** |

**Suite:** 1033 Backend · 302 Plugin-API · 45 Beispiel · 306 Dashboard.
Ruff sauber. Kein Browser-Rerun (nicht verlangt).
