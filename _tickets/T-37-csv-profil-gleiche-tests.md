# T-37 · Dasselbe prüfen, mit einem YAML-Fallback statt mit Online-Quellen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Plugin-Beispiel + Prüfmittel) | Neuplanung · YAML entschieden | neu schätzen | ein YAML-Fallback für fünf Rollen, **dieselben** Tests, UI- und Smoke-Lauf | — |

- **Angelegt:** 2026-08-28, während Codex `405d659` prüft
- **Beauftragt von Mike, 2026-08-28:** „schalte das Plugin um auf die
  CSV-Variante. Teste die CSV-Variante auch im UI. Stelle natürlich vorher
  fest, dass die Testdaten im CSV passen. … Wenn möglich sollen sich die Tests
  auf Plugin A (Yahoo, justETF usw) und die Tests auf das Plugin das die
  CSV-Daten verwendet **nicht unterscheiden**. Selbe Schnittstelle - nur
  anderes Plugin. Implementiere die Tests nicht doppelt, wenn möglich verwende
  eine Code-Base."
- **Hängt ab von:** T-36 (die dort behobenen Befunde sind die Grundlage — ohne
  sie prüft dieser Lauf einen kaputten Stand)
- **Blockiert:** nichts

**Löst:** Der Plugin-MVP behauptet, die Quelle sei austauschbar. Bewiesen ist
das bisher nur an einer Kette. **Der Beweis ist nicht, dass beide Ketten
laufen — sondern dass sie sich mit demselben Prüfmittel prüfen lassen.**
Braucht das Fallback-Profil eigene Tests, war die Schnittstelle keine.

---

## Architekturentscheidung Mike · 2026-08-29

Der umgesetzte CSV-Entwurf mit vier fachlichen Dateien wird **verworfen**. Er
ist für einen Benutzer unnötig schwer wartbar. An seine Stelle tritt **ein
YAML-Fallback-Plugin mit genau einer Datendatei**. Es ersetzt die CSV-Variante
sowohl als vollständiges Offline-Profil als auch als letztes Kettenglied des
Online-Profils; beide Implementierungen laufen nicht parallel weiter.

Das eine Plugin darf aus derselben YAML-Datei alle fünf Rollen bedienen:

| Rolle | Daten im YAML |
|---|---|
| `resolvers` | Identität, Name und Gattung |
| `quotes` | optionaler aktueller `price` |
| `daily` | optionale manuelle `history` |
| `etf_meta` | optionale Metadaten |
| `fx` | optionale Devisenkurse |

Für die History gilt eine enge Regel: Normalerweise bilden die jeweiligen
Abfragen die History eines Assets in der Datenbank. `history` im YAML ist nur
der manuell gepflegte Fallback für ein Asset, für das keine Kursabfrage
möglich ist. Die gelesenen Punkte werden ebenfalls in der Datenbank
gespeichert. Fehlt zusätzlich `price`, darf der jüngste History-Schlusskurs
als aktueller Preis-Fallback dienen.

Es gibt **keinen Migrations- oder Kompatibilitätsweg** für die vier CSV-Dateien;
das Projekt ist in Entwicklung. Der Feldname für den aktuellen Preis lautet
`price`, nicht `quote`. Das abgestimmte Beispiel steht in
[`T-37-single-file-sample.yaml`](T-37-single-file-sample.yaml). Die daneben
liegende CSV-Datei ist nur die verworfene Vergleichsvariante, kein zu
unterstützendes Format.

Alle folgenden CSV-Abschnitte dokumentieren den bereits geprüften
Ausgangsstand. Sie sind **keine Vorgabe für die Neuimplementierung**.

Ein menschliches Verify-Ticket wird bewusst **noch nicht** daraus abgeleitet.
Mike legt es erst nach der technischen Abnahme des MVP an, wenn Online-Plugin
und YAML-Fallback beide sauber laufen. So prüft es den dann gültigen Stand
statt eine heute schon veraltende Zwischenarchitektur.

---

## Der Kern: eine Prüfstrecke, zwei Profile

`_tickets/T-35-smoke.sh` bekommt einen Schalter, **keine Kopie**:

```bash
PROFILE=online ./_tickets/T-35-smoke.sh --run   # Vorgabe: OpenFIGI, Yahoo, justETF
PROFILE=csv    ./_tickets/T-35-smoke.sh --run   # dieselben Checks, alles aus Dateien
```

Das Profil entscheidet **zwei** Dinge und sonst nichts:

1. welche `sources.yaml` geschrieben wird,
2. welche Dateien danebenliegen (nur beim CSV-Profil).

**Die Checks selbst werden nicht angefasst.** Sie fragen nach dem *Ergebnis* —
„kommt das Papier an dieser Börse in dieser Währung herein", „ist der Name
gefüllt", „überlebt die Handpflege einen Refresh" —, und das Ergebnis muss
dasselbe sein, egal wer geantwortet hat. Erwartungswerte, die vom Papier
abhängen, stehen in **einer** Tabelle je Profil; die Prüflogik darüber ist
gemeinsam.

> **Woran man merkt, dass es schiefgegangen ist:** Sobald ein Check ein `if
> [[ "${PROFILE}" == … ]]` braucht, ist die Schnittstelle an dieser Stelle
> keine gemeinsame. Das ist dann ein **Befund**, kein Grund für einen Zweig.

## Die CSV-Quelle bekommt einen zweiten Einsatzort *(Entscheidung Mike, 2026-08-28)*

Mit T-31 ist entschieden: Die hier geprüfte CSV-Quelle wird **zweifach**
verwendet — als eigenes Profil (dieses Ticket) **und** als letztes Kettenglied
des Online-Profils, damit Gattungen ohne Online-Kursquelle (Anleihen) im
laufenden Online-Profil bepreist werden. Semantik dort: **Fallback, nicht
Override** — der Online-Kurs gewinnt, die Datei greift nur, wo keine
Online-Quelle liefert; der Pfad ist konfiguriert, nicht entdeckt.

Für dieses Ticket ändert das den Scope **nicht**: Geprüft wird hier weiterhin
nur das reine CSV-Profil. Aber die Prüflogik soll die zweite Verwendung
kennen — es bleibt **eine** CSV-Implementierung, und ein Check, der sich auf
„die CSV ist die einzige Quelle" verlässt, wäre für den Kettenglied-Einsatz
schon falsch gebaut. Der Kettenglied-Fall selbst wird in T-31 umgesetzt und
geprüft.

---

## Vorher: passen die Testdaten überhaupt?

Mike ausdrücklich: *„Stelle natürlich vorher fest, dass die Testdaten im CSV
passen."* Das wird ein eigener Check **vor** allen anderen — sonst misst ein
grüner Lauf womöglich nur, dass beide Seiten denselben Tippfehler teilen.

Geprüft wird die Datei gegen das, was der Vertrag ohnehin zusagt:

* ISIN mit **gültiger Prüfziffer** (`isin_check_digit_is_valid`),
* MIC ist ein **echter** Handelsplatz, kein Sammelcode (`is_real_mic`),
* Währung ist ein gültiger ISO-4217-Code und **keine Untereinheit**
  (`currency_problem` — Pence sind der gemessene Fallstrick),
* Kurse endlich und positiv (`is_finite_price`),
* TER in Basispunkten im deklarierten Wertebereich.

Diese Funktionen stehen bereits in `stockinfo_plugin.invariants`. Sie hier zu
benutzen statt eigene Prüfungen zu schreiben ist der Punkt: **Die Testdaten
werden gegen denselben Vertrag geprüft wie die Quellen.**

**Bereits gemessen, 2026-08-28** — der Entwurf unten ist durch diese Prüfung
gelaufen, mit Gegenprobe:

```
Testdaten geprueft: ALLE SAUBER
Gegenprobe: die drei Fallen werden erkannt (XX-ISIN, Sammelcode US, GBX)
```

Die Gegenprobe ist der wichtigere Teil: Eine Prüfung, die nichts abweist,
belegt nur, dass sie durchgelaufen ist.

### Der Datenentwurf

Bewusst **dieselben drei Papiere wie im Online-Lauf** — nur so können die
Checks identisch bleiben. Die Werte entsprechen dem, was der Online-Lauf am
2026-08-28 tatsächlich geliefert hat.

```
# isins.csv — isin;ticker;mic;name;type   (`type` ist die neue Spalte)
IE00B4L5Y983;EUNL;XETR;iShares Core MSCI World UCITS ETF;etf
US0378331005;APC;XETR;Apple Inc.;stock
CA7800871021;RY;XTSE;Royal Bank of Canada;stock

# closes.csv — ticker;mic;day;close;currency
EUNL;XETR;2026-08-27;128.21;EUR
APC;XETR;2026-08-27;277.40;EUR
RY;XTSE;2026-08-27;283.40;CAD

# meta.csv — isin;ter_bps;provider;fund_domicile
IE00B4L5Y983;20;iShares;Ireland

# fx.csv — base;quote;day;rate
CAD;EUR;2026-08-27;0.6412
```

`20` Basispunkte sind `0,20 %` — genau der Wert, den justETF im Online-Lauf
geliefert hat. Die Oberfläche muss beide Male dasselbe zeigen, obwohl die eine
Quelle in Prozent und die andere in Basispunkten liefert. **Das ist der
schärfste Einzelbeweis dieses Tickets**, dass die Einheitendeklaration des
Vertrags trägt und nicht nur dokumentiert ist.

---

## Was die Beispiele schon können — und was fehlt

Alle fünf Rollen liegen als CSV-Beispiel vor; ein neues Plugin ist **nicht**
nötig:

| Rolle | Beispiel | Datei |
|---|---|---|
| `resolvers` | `CanadaFileResolver` | `isin;ticker;mic;name` |
| `etf_meta` | `MetadataFileSource` | `isin;ter_bps;provider;fund_domicile` |
| `quotes` | `PricesFileQuoteSource` | `ticker;mic;day;close;currency` |
| `daily` | `PricesFileDailySource` | dieselbe Datei |
| `fx` | `FxFileSource` | `base;quote;day;rate` |

**Eine Lücke, und sie ist die interessante:** Die Resolver-Tabelle führt keine
**Gattung**. Damit bliebe `type` leer — und der Lauf T-35 hat gezeigt, was
dann passiert: Das Dashboard hält jedes Papier für eine Aktie und fragt die
Metadatenquelle gar nicht erst. Der Check `#3b` fiele beim CSV-Profil, beim
Online-Profil nicht.

Das ist **kein** Grund für einen profilabhängigen Zweig, sondern der erste
echte Befund dieses Tickets: Die Beispieltabelle bekommt eine optionale
Spalte `type`. Additiv, alte Dateien bleiben gültig.

> **Und es ist derselbe Sachverhalt wie Mikes offene Frage aus T-35** — welche
> Felder sind Pflicht, welche optional. Wäre `name`/`type` als Pflichtfeld der
> Kette deklariert, hätte die fehlende Spalte beim Bauen des Beispiels
> auffallen müssen und nicht erst im Browser. Dieses Ticket **entscheidet die
> Frage nicht**, es liefert ihr nur einen zweiten Beleg.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ nicht geprüft.
`AI` = maschinell und im Browser durch Claude · `Human` = Mike (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | `PROFILE=csv`, Vorlauf | die Testdaten werden gegen `stockinfo_plugin.invariants` geprüft — Prüfziffer, echter MIC, Währung ohne Untereinheit, endliche Kurse. Ein Tippfehler in der CSV fällt **vor** dem ersten Check auf | ✅ | |
| **2** | `GET /sources` mit `PROFILE=csv` | in allen fünf Rollen stehen die Datei-Quellen, jede `configured: true`. Keine yfinance-, justETF- oder OpenFIGI-Quelle ist beteiligt | ✅ | |
| **3** | `./_tickets/T-35-smoke.sh --run` mit **beiden** Profilen | dieselben Checks, beide grün. **Kein Check enthält eine Fallunterscheidung nach Profil** — die Gegenprobe ist ein `grep` über das Script | ✅ | |
| **4** | die Diff des Scripts | die Prüflogik ist **einmal** da. Zwei Profil-Tabellen mit Erwartungswerten sind erlaubt, zwei Prüfstrecken nicht | ✅ | |
| **5** | Dashboard mit `PROFILE=csv` | Papier per ISIN anlegen: Zeile erscheint mit Name, Börse, Währung — genau wie beim Online-Profil, nur ohne Netz | ✅ | |
| **5b** | dasselbe Papier aufklappen | Gattung als Badge, TER und Anbieter gefüllt. **Die TER steht in der Datei in Basispunkten** und muss in Prozent ankommen — die Einheitendeklaration des Vertrags, sichtbar in der Oberfläche | ✅ | |
| **6** | eine ISIN, die **nicht** in der Tabelle steht | dieselbe verständliche Meldung wie beim Online-Profil, dieselbe Kennung `instrument_not_found`, keine neue Zeile in der Datenbank | ✅ | |
| **7** | Handpflege setzen, Refresh auslösen | überlebt — wie beim Online-Profil. Der Kurs kommt danach weiterhin aus der Datei | ✅ | |
| **8** | Papier löschen | verschwindet aus Liste und Datenbank, keine Waisen | ✅ | |
| **9** | `data/plugins/` und `sources.yaml` tauschen, Neustart | **derselbe Bestand**, andere Quelle. Die Datenbank bleibt; nur wer antwortet, ändert sich. Das ist die eigentliche Aussage des Plugin-Systems | ✅ | |
| **10** | Browser-Konsole über den ganzen CSV-Lauf | keine Fehler, keine fehlgeschlagenen Requests | ✅ | |

---

## Was dieses Ticket nicht tut

- **Keine neue Testinfrastruktur.** Kein Playwright, kein Record/Replay, kein
  Mitschnitt. Der CSV-Lauf braucht kein Netz — nicht weil er es wegmockt,
  sondern weil eine Dateiquelle keins braucht. Das ist der Unterschied, auf
  den der Testinfrastruktur-Riegel abzielt.
- **Kein neues Plugin.** Die Beispiele aus `plugin_api/examples/` decken alle
  fünf Rollen ab. Ein zweites CSV-Plugin zu schreiben wäre derselbe Fehler wie
  in einer früheren Runde: ein zweites Format und eine zweite Fachlogik für
  etwas, das existiert und vertraglich geprüft ist.
- **Es entscheidet die Pflichtfeld-Frage nicht.** Sie gehört Mike und Codex
  (T-35, „Offen: eine Frage an den Vertrag").

---

## Reihenfolge

1. **Warten auf T-36.** Bei `owner: codex` ist die Commit-Linie für
   Produktcode eingefroren; dieses Ticket ist deshalb angelegt und nicht
   begonnen.
2. Testdaten entwerfen und gegen die Invarianten prüfen (`#1`).
3. Optionale Spalte `type` im Resolver-Beispiel, mit Vertragstest.
4. `PROFILE`-Schalter im vorhandenen Script — Prüflogik unangetastet (`#3`, `#4`).
5. Beide Profile maschinell, dann der Browserlauf (`#5`–`#10`).

---

## Auflösung

**Beide Profile laufen mit derselben Prüfstrecke: 17/17 und 17/17.**
Ausgeführt am 2026-08-28, Produktstand siehe Commit.

### Was die Umsetzung gebraucht hat

1. **`type` als Spalte im Resolver-Beispiel** (`canada_file.py`), additiv.
   Tabellen ohne die Spalte bleiben gültig; eine leere Zelle wird zu `None`
   und nicht zu `""`. Zwei Vertragstests halten beides fest.
2. **`PROFILE=online|csv` im vorhandenen Script.** Das Profil schreibt die
   `sources.yaml`, legt beim CSV-Profil die Beispieldateien als *Dateien* ins
   Volume und setzt **einen** Erwartungswert: `EXPECTED_SOURCES`. Sonst kennt
   kein Check das Profil — die Gegenprobe ist ein `grep`, und `PROFILE`
   kommt in keiner Check-Funktion vor.
3. **Ein Vorlauf-Check `#0`**, der die Testdaten gegen
   `stockinfo_plugin.invariants` hält — samt Gegenprobe auf XX-ISIN,
   Sammelcode `US` und Pence. Er läuft in **beiden** Profilen.

### Der Befund, den erst das CSV-Profil sichtbar gemacht hat

**Die Herkunft war fest verdrahtet.** `app/services/quote_service.py` und
`app/services/fx_service.py` stempelten jeden Datensatz mit
`source="yfinance"` — unabhängig davon, wer geantwortet hat. Im Online-Profil
fällt das nie auf, dort *ist* yfinance die Quelle. Im CSV-Profil stand in der
Datenbank:

```
('CA7800871021', …, 'stock', 'yfinance')     ← der Kurs kam aus einer Datei
```

`source` ist das Feld, an dem ein Benutzer abliest, woher ein Wert stammt —
die Oberfläche zeigt es im Aufklappbereich als „Quelle". Es ist **derselbe
Fehlertyp** wie die Fehlermeldungen, die bis T-36 OpenFIGI und Yahoo
namentlich nannten, obwohl das Profil andere Quellen führte: eine Behauptung
über etwas, das der Dienst gar nicht geprüft hat.

Behoben: Beide Dienste fragen die Quelle nach ihrem Namen. Der Rückfall ist
bewusst **kein** Anbietername, sondern `"unbekannt"` — auf einen eingebauten
Namen zurückzufallen wäre dieselbe Behauptung, nur seltener. Gemessen
nachher:

```
('CA7800871021', …, 'prices-file-quote')
('IE00B4L5Y983', …, 'metadata-file')
fx: {'base': 'CAD', 'quote': 'EUR', 'rate': 0.6412, 'source': 'fx-file'}
```

### Der Profilwechsel auf demselben Bestand (`#9`)

Die stärkste Einzelmessung des Tickets. Dieselbe Datenbank, nur
`sources.yaml` getauscht und neu gestartet:

| | vorher (CSV) | nachher (online) |
|---|---|---|
| Kurs | aus `closes.csv` | 128,2149… von yfinance |
| `source` | `metadata-file` | `justetf` |
| Name, Gattung | erhalten | **unverändert erhalten** |
| TER | 0,20 % (aus 20 bps) | 0,20 % (von justETF) |

Dass Name und Gattung den Wechsel überleben, ist kein Zufall, sondern
`KEEP_IF_UNKNOWN` aus T-36 — ohne diesen Fix hätte der erste Refresh nach dem
Wechsel beide gelöscht.

### Offener Befund aus dem zweiten Browserlauf (2026-08-29)

**Acht UI-Texte nennen `justETF` fest** — `dashboard/src/i18n/de.ts:325,328,
331,334` und dieselben vier in `en.ts`. Es sind die Erklärungen im
Aufklappbereich, warum die Metadatenquelle nichts beigesteuert hat
(`skipReason`: `notEtf`, `noIsin`, `notEuropean`, `empty`).

Im CSV-Profil ist die Metadatenquelle **`metadata-file`**. Die Oberfläche
zeigt das eine Zeile weiter oben korrekt an (`Quelle: prices-file-quote`) und
behauptet im selben Aufklappbereich justETF. Gesehen an `RY.TO`:

> „justETF liefert nur Kennzahlen zu ETFs — dieses Papier ist eine Aktie."

**Das ist derselbe Befund, den Codex in T-36 Runde 1 als Finding 2 erhoben
hat** („Die UI-Texte dürfen keine eingebauten Provider behaupten"). Ich habe
ihn damals nur für die **Fehlermeldungen** umgesetzt; die Erklärtexte im
Drilldown standen nicht im Befund und sind mir entgangen. Die Fachlogik
dahinter stimmt — `RY` *ist* eine Aktie, und die Metadatenquelle wurde zu
Recht nicht gefragt. Falsch ist allein der Anbietername.

Nicht behoben, weil die Commit-Linie bei `codex_reviewing` eingefroren ist.
Der Umfang ist klein und rein sprachlich: acht Texte provider-neutral
formulieren, dazu ein Test wie der vorhandene
`nennt keine eingebaute Quelle beim Namen`, nur über den Drilldown-Katalog
statt über `errors.reason`.

### Was im Browser zu sehen war

Name, ETF-Badge, Kurs in EUR, **TER 0,20 % aus 20 Basispunkten**, Anbieter
iShares, Domizil Ireland — und die Oberfläche nennt `Quelle: metadata-file`.
Die unauflösbare ISIN meldet „Zu DE0007164600 hat keine der eingerichteten
Quellen ein Wertpapier gefunden" — provider-neutral und im CSV-Profil wahr.
Konsole sauber.

---

## Codex-Review · Sammelrunde zu `d313318` · Nacharbeit

Die Grundidee trägt: Ein `PROFILE`-Schalter wählt Konfiguration und Dateien,
die fachlichen Checks enthalten keinen Profilzweig, und der CSV-Lauf erreicht
17/17. Vier Aussagen sind dadurch aber noch nicht belegt beziehungsweise
werden falsch positiv:

1. `checkTestData` ignoriert den Exitstatus seines Python-Parsers. Ein nicht
   numerischer Kurs wirft vor `print`, erzeugt leeren Standardoutput und wird
   deshalb als Erfolg gezählt.
2. `/sources` belegt nur, dass `prices-file-daily` und `fx-file` konfiguriert
   sind. Keiner der 17 Checks ruft Daily oder FX auf. Ergänzt werden müssen
   gemeinsame, profilfreie Aufrufe mit konkreten Ergebniswerten und
   Quellenbelegen.
3. `source` nennt bei einem angereicherten ETF nicht die Kursquelle: Die
   Metadatenanreicherung überschreibt `prices-file-quote` mit
   `metadata-file`. Der neue Test verhindert genau diesen Pfad mit
   `type="stock"`; für die ebenfalls geänderte FX-Herkunft fehlt ein Test.
   Die Namenspflicht gehört außerdem in die Provider-Protokolle statt als
   zweimal kopierter `getattr`-Rückfall in die Dienste. Ein deutscher roher
   Rückfall darf nicht in der englischen Oberfläche erscheinen.
4. Das nach `CLAUDE.md` verlangte AST-/TS-/Bash-Inventar zeigt zahlreiche
   deutsche Bezeichner in den berührten Dateien und zwei neue
   `Record<string, any>`; die vollständige Liste steht im T-36-Review und in
   STATUS.md.
5. Der nachgereichte Browserbefund ist bestätigt: Die acht lokalisierten
   `skipReason`-Texte nennen `justETF` fest und widersprechen damit im
   CSV-Profil der sichtbaren Quelle `metadata-file`. Die Texte müssen
   provider-neutral werden; ein Katalogtest soll beide Sprachen vollständig
   gegen eingebaute Quellennamen halten.

Der Browsernachweis wird nicht angezweifelt; er ersetzt aber keine dauerhafte
Ausführung der zwei fehlenden Rollen und keine Negativprobe des Validators.
