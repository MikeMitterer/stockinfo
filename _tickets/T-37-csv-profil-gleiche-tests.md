# T-37 · Dasselbe prüfen, mit dem CSV-Plugin statt mit Yahoo

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Plugin-Beispiele + Prüfmittel) | offen | 4 h | zweites Quellenprofil aus CSV, **dieselben** Tests, UI- und Smoke-Lauf | — |

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
Braucht das CSV-Profil eigene Tests, war die Schnittstelle keine.

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
| **1** | `PROFILE=csv`, Vorlauf | die Testdaten werden gegen `stockinfo_plugin.invariants` geprüft — Prüfziffer, echter MIC, Währung ohne Untereinheit, endliche Kurse. Ein Tippfehler in der CSV fällt **vor** dem ersten Check auf | | |
| **2** | `GET /sources` mit `PROFILE=csv` | in allen fünf Rollen stehen die Datei-Quellen, jede `configured: true`. Keine yfinance-, justETF- oder OpenFIGI-Quelle ist beteiligt | | |
| **3** | `./_tickets/T-35-smoke.sh --run` mit **beiden** Profilen | dieselben Checks, beide grün. **Kein Check enthält eine Fallunterscheidung nach Profil** — die Gegenprobe ist ein `grep` über das Script | | |
| **4** | die Diff des Scripts | die Prüflogik ist **einmal** da. Zwei Profil-Tabellen mit Erwartungswerten sind erlaubt, zwei Prüfstrecken nicht | | |
| **5** | Dashboard mit `PROFILE=csv` | Papier per ISIN anlegen: Zeile erscheint mit Name, Börse, Währung — genau wie beim Online-Profil, nur ohne Netz | | |
| **5b** | dasselbe Papier aufklappen | Gattung als Badge, TER und Anbieter gefüllt. **Die TER steht in der Datei in Basispunkten** und muss in Prozent ankommen — die Einheitendeklaration des Vertrags, sichtbar in der Oberfläche | | |
| **6** | eine ISIN, die **nicht** in der Tabelle steht | dieselbe verständliche Meldung wie beim Online-Profil, dieselbe Kennung `instrument_not_found`, keine neue Zeile in der Datenbank | | |
| **7** | Handpflege setzen, Refresh auslösen | überlebt — wie beim Online-Profil. Der Kurs kommt danach weiterhin aus der Datei | | |
| **8** | Papier löschen | verschwindet aus Liste und Datenbank, keine Waisen | | |
| **9** | `data/plugins/` und `sources.yaml` tauschen, Neustart | **derselbe Bestand**, andere Quelle. Die Datenbank bleibt; nur wer antwortet, ändert sich. Das ist die eigentliche Aussage des Plugin-Systems | | |
| **10** | Browser-Konsole über den ganzen CSV-Lauf | keine Fehler, keine fehlgeschlagenen Requests | | |

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

_(offen)_
