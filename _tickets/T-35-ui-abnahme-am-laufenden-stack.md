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
dort ist bisher **kein einziges Mal** gemessen worden.

Dieses Ticket ersetzt keine menschliche Abnahme durch Mike. Es beantwortet
die Vorfrage: **Hält der Stand einer Bedienung überhaupt
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
| **1** | `GET /sources` am laufenden Dienst | die von Mike vorgegebene Kette steht da und ist einsatzbereit: `openfigi`, `yahoo-search`, `justetf`, `yfinance` — jede mit `configured: true`. Keine Rolle meldet „noch nicht gebaut" | ✅ | |
| **2** | Dashboard `:5173`, Papier per ISIN anlegen (`IE00B4L5Y983`) | die Zeile erscheint **ohne Reload**, mit Name, Börse und Währung EUR | ✅ | |
| **2b** | dieselbe Aufnahme, SQLite | genau **eine** Zeile in `instruments`, ISIN und `(ticker, mic)` gesetzt — kein Platzhalter, kein `NULL` in der Identität | ✅ | |
| **3** | dasselbe Papier in der Oberfläche öffnen | Kurs mit Währung, TER und Anbieter sind gefüllt. Das belegt die **Kette**: Kurs von yfinance, TER von justETF — zwei verschiedene Quellen in einer Ansicht | ✅ | |
| **4** | ein Papier, das die Vorzugsbörse **nicht** führt (`CA7800871021`, Royal Bank) | kommt an seiner **Heimatbörse** in CAD herein. Das ist die Kaskade aus T-18: erst die Vorzugsbörse, dann die Heimat aus dem ISIN-Präfix | ✅ | |
| **4b** | ein US-Papier daneben (`US0378331005`, Apple) | kommt an **Xetra in EUR** herein — und das ist **richtig**, nicht falsch. Die Vorzugsbörse gewinnt, wenn sie das Papier führt. Diese Zeile stand zuerst falsch herum im Ticket; gemessen wurde `APC.DE / Xetra / XETR`, und genau das sagt T-18 zu | ✅ | |
| **5** | eine ISIN, die nirgends auflösbar ist (`XX0000000000`) | die Oberfläche sagt es verständlich, und in `instruments` steht danach **keine** neue Zeile. Eine kaputte Zeile ist teurer als eine abgelehnte Eingabe | ✅ | |
| **6** | ein benutzerpflegbares Feld ändern (z.B. TER von Hand) | der neue Wert steht sofort in der Ansicht | ✅ | |
| **6b** | dasselbe Feld, SQLite | der Wert steht in der Override-/Detailtabelle — **nicht** in der Quellenspalte. Der Unterschied ist der Kern: Handpflege darf beim nächsten Abruf nicht überschrieben werden | ✅ | |
| **6c** | nach `#6b` erneut abrufen | die Handpflege **überlebt** den Abruf — nichts ist nach einer erneuten Quellenabfrage leer geworden | ✅ | |
| **7** | denselben Kurs zweimal hintereinander abrufen | der zweite Abruf kommt **aus dem Cache**: messbar schneller, und im Protokoll steht kein zweiter Netzaufruf | ✅ | |
| **7b** | Cache-Zeitstempel in SQLite | `fetched_at` o. ä. ist beim zweiten Abruf **unverändert** — der sichere Beleg. Antwortzeit allein kann täuschen, ein unveränderter Zeitstempel nicht | ✅ | |
| **8** | Papier löschen | verschwindet aus der Liste **und** aus `instruments`; die zugehörigen Kurszeilen bleiben nicht als Waisen zurück | ✅ | |
| **9** | Browser-Konsole über den ganzen Lauf | keine Fehler, keine fehlgeschlagenen Requests, keine Warnung über fehlende Felder | ✅ | |

_(Die `Human`-Spalte bleibt leer — sie gehört Mike.)_

---

## Mitgebrachter Befund aus T-37 (2026-08-30)

**Der Drilldown nennt jede Nicht-ETF-Gattung „Aktie".**

`dashboard/src/i18n/de.ts:350`:

> „Kennzahlen werden nur für ETFs geholt — dieses Papier ist **eine Aktie**.
> Die Quelle wird deshalb gar nicht erst abgefragt, alle Felder lassen sich von
> Hand nachtragen."

Gemessen im Browserlauf zu T-37, YAML-Profil: Der Satz stand unter einer
**Bundesanleihe** (`instrument_type: bond`). Er stimmte, solange es zwei
Gattungen gab; seit T-31 und T-38 sind es sechs, und für `bond`, `crypto` und
`fund` ist er schlicht falsch.

Die Aussage dahinter bleibt richtig — die Metadatenquelle wird für diese
Papiere nicht gefragt. Falsch ist nur die Begründung, und sie ist die einzige
Stelle, an der ein Benutzer die Gattung seines Papiers erklärt bekommt.

Nicht in T-37 behoben: Es wäre eine weitere Produktfläche gewesen, und das
Ticket stand bereits unter einem Scope-Checkpoint. Hier ist der Ort, weil T-35
die Oberfläche am laufenden Stack abnimmt.

---

## Was dieses Ticket ausdrücklich nicht tut

- ~~**Es ändert keinen Produktcode.**~~ **Diese Zeile hat nicht gehalten, und
  zwar auf Mikes ausdrückliche Ansage.** Der erste Befund („Name — leer, ist
  schon mal falsch") kam von ihm, während der Lauf noch lief; danach war
  Reparieren beauftragt, nicht Notieren. Die Änderungen stehen unten
  vollständig, damit Codex sie **als Änderungen** prüft und nicht als Befunde.
- **Es ersetzt keine menschliche Abnahme.** Ob sich das Ergebnis richtig
  *anfühlt*, kann niemand außer Mike beantworten.
- **Es baut keine Testinfrastruktur.** Kein Playwright, kein Selenium, keine
  Fixtures — ein Browser, der laufende Stack und die echten Quellen. Der
  Testinfrastruktur-Riegel gilt.

---

## Auflösung

**Der Lauf hat stattgefunden am 2026-08-28**, im Browser gegen den laufenden
Stack (Backend `:8000`, Dashboard `:5173`) mit der vorgegebenen Kette und einer
eigenen Datenbank. `data/stockinfo.db` wurde nicht angefasst — Zeitstempel
unverändert 19. August.

**Alle vierzehn Zeilen sind bestätigt** — aber erst, nachdem fünf Befunde
behoben waren. Vier davon waren im Betrieb sichtbar und von keinem der 796
Unit-Tests gesehen.

### Befund 1 · `yahoo-search` war in der Kette kaputt

Gefunden **vor** dem Lauf, beim Prüfen von Mikes Aussage „alles läuft nur noch
über das Plugin". Sie stimmte fast: `_yahoo_search` baute weiter
`app.resolver.YFinanceResolver` — eine Klasse mit den **Core**-Signaturen
`handles(isin: str)` / `resolve_isin(...)`. Weil `_build_one` seit Runde 3
**jede** Quelle adaptiert, bekam sie den `ResolverAdapter` übergestülpt, der
`handles(ResolveRequest)` und `resolve(...)` ruft. Gemessen:

    handles("US0378331005")        -> True   ← falsch, nahm die Anfrage an
    resolve_isin("XX0000000000")   -> AttributeError: 'YFinanceResolver'
                                      object has no attribute 'resolve'

`CompositeResolver` fängt in seiner Kaskade nichts ab. **Jede ISIN, die
OpenFIGI nicht kennt, endete damit in einem `500`** — ausgerechnet im Fallback
für US-Titel, für den die Quelle existiert.

*Behoben:* `app/plugins/yahoo_search_resolver.py`, dieselbe dünne Rollenhülle
wie bei OpenFIGI und justETF. **Der Adapter blieb unangetastet** — ihn beide
Formen erraten zu lassen hätte den Übergangszustand verewigt, genau das
`contract_roles`-Feld, das Runde 3 entfernt hat.

*Wächter:* `test_jede_eingebaute_quelle_spricht_in_jeder_rolle_den_vertrag` —
strukturell, nicht über einen Aufruf: Jede eingebaute Quelle muss in **jeder**
Rolle von der Vertragsklasse dieser Rolle abstammen. Gegenprobe gemessen
(`isinstance(YFinanceResolver(...), Resolver)` → `False`).

### Befund 2 · Kein Name, keine Gattung — und deshalb nie justETF

Der Lauf zeigte für `IE00B4L5Y983` eine Zeile ohne Namen, ohne TER, ohne
Anbieter, mit der Erklärung „dieses Papier ist eine Aktie". Es ist der iShares
Core MSCI World.

Ursache: `OpenFigiClient.map_isin` gab **nur den Ticker** zurück. In derselben
Antwort steht:

    {"ticker": "EUNL", "name": "ISHARES CORE MSCI WORLD",
     "securityType": "ETP", "securityType2": "Mutual Fund", …}

Beides wurde verworfen. Ohne `type` greift im Dashboard `skipReason ===
'notEtf'` — **justETF wurde gar nicht erst gefragt**. TER, Anbieter, Domizil,
Fondsvolumen und Replikationsart blieben für jedes Papier dauerhaft leer, ohne
Fehlermeldung und ohne Protokolleintrag.

*Behoben:* `FigiMatch(ticker, name, instrument_type)` statt einer nackten
Zeichenkette; `_FIGI_TYPES` bildet OpenFIGIs Gattungen auf das Vokabular der
App ab und lässt Unbekanntes **auf `None` stehen** statt zu raten — ein
geratenes `"stock"` schaltete die ETF-Anreicherung wieder still ab.

*Gemessen nachher:* `name='ISHARES CORE MSCI WORLD', type='etf'`, TER 0,2 %,
Anbieter iShares, Domizil Irland. Apple: `name='APPLE INC', type='stock'`.

### Befund 3 · Ein Refresh löschte den Namen

Unmittelbar danach sichtbar: Nach `POST /refresh/{isin}` stand `name` auf
`NULL` — bei **jedem** Papier, nach genau einem Klick.

Das ist die Kehrseite eines **richtigen** Vertrags: `Quote` trägt Preis,
Währung, Zeitpunkt und Volumen und **kein** Namensfeld. Das ist korrekt — ein
Kurs ist ein Preis zu einer Zeit und weiß nichts über die Gattung seines
Papiers; Name und Gattung stehen in `Resolved`. Nur schrieb der Kurs-Weg diese
Spalten trotzdem mit, aus der Zeit vor T-23.

*Behoben:* `KEEP_IF_UNKNOWN = {"name", "type"}` in `app/repository.py` —
**nur beim Aktualisieren**. Die Regel stand dort längst, nur für andere
Felder: *„Ihr gespeicherter Stand ist mehr wert als ein `NULL`, das nur ‚ich
habe gerade nicht nachgesehen' bedeutet."*

Der erste Anlauf hat sie fälschlich auch auf das **Anlegen** gelegt; die
beiden Plugin-Durchstiche in `test_plugin_vertical.py` sind darüber sofort
gefallen (`assert None == 'Royal Bank of Canada'`).

### Befund 4 · „Hinzufügen fehlgeschlagen" — und sonst nichts

Von Mike im Lauf bestätigt. Zwei Ursachen, beide behoben:

1. `app/routers/quotes.py` antwortete mit `detail="Keine Auflösung für ISIN …"`
   — deutschem Fließtext. Das verletzt die eigene Zusage aus `ErrorDetail`:
   *„Der Text gehört ins UI und muss in DE und EN vorliegen."* Jetzt
   `{"code": "instrument_not_found", "params": {...}}`, dieselbe Kennung wie
   der Aufnahmeweg.
2. Das Dashboard verwarf jede Antwort und zeigte eine feste Kategorie.
   `dashboard/src/api/reason.ts` übersetzt jetzt die **Kennung** über einen
   Katalog in DE und EN; ein mitgelieferter Fließtext ist nur der Rückfall.

*Nebenbefund:* Der Anlegeweg des Dashboards läuft über `GET /quote/…`, **nicht**
über `POST /instruments/intake`. Die typisierte Auskunft, die dort längst
existiert, kam beim Benutzer deshalb nie an. Das ist behoben, aber die Frage,
welcher Weg der richtige ist, gehört Codex und Mike — sie steht unten.

*Gemessen nachher, im Browser:* „Hinzufügen fehlgeschlagen — Zu XX0000000000
ließ sich kein Wertpapier finden — weder über OpenFIGI noch über die
Yahoo-Suche."

### Befund 5 · Zwei Schönheitsfehler, beide von Mike gesehen

- **Der Trennstrich brach vor den Aktionsknöpfen ab.** `.actions` war ein
  `<td>` mit `display: flex`. Damit verlässt die Zelle das Tabellenlayout:
  Sie zählt nicht zur Tabellenbreite, und ihr `border-bottom` wird um eine
  eigene Box gezeichnet. Der Löschen-Knopf war dadurch bei schmalem Fenster
  gleich mit abgeschnitten. Jetzt `text-align: right; white-space: nowrap`.
- **Der Caret stand über dem Ticker.** `.row-toggle` ist `display: inline`,
  die Zeile brach zwischen Dreieck und Symbol. `white-space: nowrap` — dieselbe
  Entscheidung wie bei den Zahlenspalten in derselben Datei.

---

## Offen: eine Frage an den Vertrag, kein Fix

**Mike, 2026-08-28:** *„das Plugin muss ganz klar eine Feldliste von
Pflichtfeldern und von optionalen Feldern liefern — Pflichtfelder müssen
logischerweise gefüllt sein. Wie kann es sein dass name kein Pflichtfeld ist?"*

**Die Antwort auf die Frage lautet: weil es nie entschieden wurde.** Geprüft:

- `FieldSpec` deklariert `name`, `kind`, `unit`, `plausible`, `label_en`,
  `label_de`, `overridable` — **kein `required`**.
- Die Resolver-Rolle deklariert überhaupt keine Feldliste.
- `Resolved.name` und `Resolved.instrument_type` sind `= None`. Optional
  durch Auslassung, nicht durch Entscheidung.

Die drei Befunde oben sind Ausprägungen desselben Lochs: Ein Wert fehlte, und
**nichts hat gefragt**. Meine Fixes füllen die Werte; sie machen sie nicht zur
Regel. Ohne Regel kommt das nächste Plugin und lässt sie wieder weg.

**Vorschlag — bewusst als Vorschlag, nicht als Umsetzung.** Der Vertrag ist
Codex' und Mikes Sache, und die Frage ist zu grundsätzlich für einen
Nebeneffekt dieses Tickets:

1. `FieldSpec` bekommt `required: bool = False`.
2. Jede Rolle deklariert ihre Pflichtfelder. Für `Resolver` wären das heute
   `ticker` und `mic` (die werden bereits erzwungen — ein `Resolved` ohne sie
   wird zu `NotFound`); die Frage ist, ob `name` dazugehört.
3. **Pflicht heißt „die Kette muss es liefern", nicht „jede Quelle".** Ein
   CSV-Plugin mit ISIN→Ticker-Tabelle kennt legitim keinen Namen; das
   `canada-file`-Beispiel wäre sonst sofort vertragswidrig. Die Prüfung gehört
   an den Rand des Core: Was am Ende der Kette ohne Pflichtfeld herauskommt,
   ist ein Befund — sichtbar in `/sources` oder im Protokoll, nicht still.
4. Das Contract-Kit prüft es, damit ein Plugin-Autor es beim Bauen merkt und
   nicht ein Benutzer im Betrieb.

Wer das zuschneidet, sollte T-27a und T-34 danebenlegen: T-34s Wächter `#3`
(„jede Kennung hat DE und EN") ist dieselbe Sorte Lücke, eine Schicht weiter.

---

## Was der Lauf über die Prüfmittel selbst sagt

`_tickets/T-35-smoke.sh` stellt dieselben Fragen über REST — **15 Checks, alle
grün**, mit Netz gegen die echten Quellen. Er hat sich beim ersten Lauf selbst
erwischt: `report` gab bei leerem Zusatztext `1` zurück, wodurch im
`bedingung && report … || report …` **beides** feuerte. 17 Meldungen bei 12
erwarteten Checks — gefunden allein durch die Vollständigkeitsprüfung am Ende,
die genau dafür da ist (P-05).

**Stand am Ende:** 802 Unit-Tests, 8 Integrationstests gegen Yahoo/justETF/
OpenFIGI, 257 Vertragstests, 259 Dashboard-Tests, `vue-tsc` sauber, 15/15
Smoke-Checks.
