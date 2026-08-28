# T-38 · Pflichtfelder verbindlich machen — und abfragbar

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Plugin-Vertrag + Core + REST) | offen · **Gate für T-28** | 1 Tag | Pflicht/Optional je Result-Typ, Gattungs-Vokabular, Durchsetzung, REST-Auskunft | — |

- **Angelegt:** 2026-08-28, aus T-36 Runde 1 (Codex) und Mikes Entscheidungen
- **Hängt ab von:** T-36 (die dort behobenen Befunde sind die Symptome)
- **Blockiert:** T-28 — als Plugin-Gate aufgenommen
- **Berührt:** T-31 (Papiere ohne MIC), T-34 (Wächter), T-37 (CSV-Profil)

**Löst:** Drei der fünf Befunde aus dem UI-Lauf waren **derselbe** Fehler: Ein
Wert fehlte, und nichts hat gefragt. Der Name war leer, die Gattung war leer,
und weil die Gattung leer war, wurde die Metadatenquelle nie befragt — ohne
Fehlermeldung, ohne Protokolleintrag, monatelang.

Reparieren ließ sich das an der Quelle. **Verhindern lässt es sich nur durch
eine Regel**, die sagt, welche Felder eine erfolgreiche Antwort tragen muss.

---

## Der gemessene Ausgangszustand

Nicht behauptet — am 2026-08-28 aus den Dataclasses ausgelesen:

| Typ | Pflicht (kein Vorgabewert) | optional |
|---|---|---|
| `Resolved` | `ticker`, `mic` | `isin`, **`name`**, **`instrument_type`** |
| `Quote` | `price`, `currency`, `as_of` | `volume` |
| `DailyBar` | `day`, `close` | — |
| `DailySeries` | `bars`, `currency`, `adjusted` | — |
| `FxRate` | `base`, `quote`, `rate`, `as_of` | — |
| `Reading` | `field`, `value` | `unit`, `source`, `currency` |

**Zwei Dinge fallen daran auf.**

Erstens: **Kurs und Währung sind längst Pflicht.** Mikes Vorgabe dazu ist im
Plugin-Vertrag bereits erfüllt — `Quote` hat für beide keinen Vorgabewert, und
`YFinancePlugin` weist einen Kurs ohne Währung ausdrücklich als `Unavailable`
ab. Hier ist nichts zu tun außer es **auszuweisen**.

Zweitens: Pflicht wird heute allein durch das **Fehlen eines Vorgabewerts**
ausgedrückt. Das ist knapp und wirksam, steht aber nirgends als Aussage —
weder im Contract-Kit noch in einer Auskunft, die ein Plugin-Autor lesen kann.

---

## Die Entscheidungen, die schon getroffen sind

> **Mike, 2026-08-28:** *„Wie kann es sein dass name kein Pflichtfeld ist?"*
> — `Resolved.name` wird **Pflicht**.
>
> **Mike, 2026-08-28:** *„instrument-Typ ist natürlich auch ein Pflichtfeld."*
> — `Resolved.instrument_type` wird **Pflicht**.
>
> **Mike, 2026-08-28:** *„Der Kurs ist natürlich auch ein Pflichtfeld, Währung
> auch."* — bereits erfüllt, siehe oben.
>
> **Codex, 2026-08-28:** kein pauschales `FieldSpec.required`. `FieldSpec`
> beschreibt **dynamische** Metadaten einer Quelle; die festen Felder von
> `Resolved` und `Quote` sind etwas anderes und gehören in die Typen selbst,
> ins Contract-Kit und an die Host-Grenze.

Codex hat damit recht, und der Unterschied ist wichtig genug für einen Satz:
`FieldSpec` beantwortet *„welche Kennzahlen liefert diese Quelle, und in
welcher Einheit"*. Pflichtfelder beantworten *„was muss in einer erfolgreichen
Antwort stehen, egal wer sie gibt"*. Das eine ist eine Eigenschaft der Quelle,
das andere eine des Vertrags.

---

## Die offene Frage, die zuerst beantwortet werden muss

> **Mike, 2026-08-28:** *„Bei den Typen gibt es aktuell ETF und STOCK - was
> ist mit ETC, was ist mit Kryptos?"*

**Das ist kein Nebenpunkt, sondern die Vorbedingung.** Heute kennt die App
genau zwei Gattungen (`app/providers/base.py`: `QUOTE_TYPE_MAP = {"ETF":
"etf", "MUTUALFUND": "etf", "EQUITY": "stock"}`). `instrument_type` zur
Pflicht zu machen, **bevor** das Vokabular reicht, erzwingt eine Lüge: Ein ETC
wäre dann „stock" oder „etf", und beides ist falsch.

Zu entscheiden ist also **zuerst** das Vokabular. Zur Diskussion:

| Kandidat | Warum er dazugehören könnte | Was daran hängt |
|---|---|---|
| `etc` / `etn` | Rohstoff- und Schuldverschreibungs-Tracker sind formal **keine** Fonds. justETF führt sie getrennt, OpenFIGI ebenfalls | Die ETF-Anreicherung müsste entscheiden, ob sie für ETCs greift |
| `crypto` | Mikes ausdrückliche Frage | **Hängt an T-31**: Krypto hat keinen MIC, und die Identität der App ist `(ticker, mic)`. Ohne diese Entscheidung ist die Gattung wertlos |
| `index` | Referenzwerte, die man ansehen aber nicht kaufen kann | dito T-31 |
| `bond` | Anleihen | dito T-31 |
| `fund` | Nicht börsengehandelte Fonds | heute auf `etf` abgebildet — vermutlich falsch |

**Die Empfehlung:** Das Vokabular als **offene** Aufzählung führen, wie es der
Vertrag für `source` schon tut („Ein neuer Wert in einer offenen Aufzählung"
gilt dort ausdrücklich als additiv). Dann ist `etc` ein Nachtrag und kein
Bruch. Was die App nicht kennt, zeigt sie als das, was die Quelle sagt, statt
es auf `stock` zu runden — **das Runden war der Fehler**, den dieses Ticket
verhindert.

Krypto, Index und Anleihe bleiben davon getrennt: Sie scheitern nicht am
Vokabular, sondern an der Identität. Das ist T-31.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ nicht geprüft.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | Entscheidung Mike | das Gattungs-Vokabular steht fest — welche Werte es gibt, ob es offen ist, und was mit `etc` geschieht | ➖ | |
| **2** | `stockinfo_plugin.types` | `Resolved.name` und `Resolved.instrument_type` sind Pflichtfelder. Kein Vorgabewert, und die Zusage steht im Docstring | | |
| **3** | `API_VERSION` | der Sprung ist **ehrlich** gemacht: Ein optionales Feld zur Pflicht zu erheben ist laut eigener Kompatibilitätsregel ein **Bruch**. Ein Plugin nach altem Vertrag wird abgewiesen und nicht stillschweigend geduldet | | |
| **4** | Contract-Kit | die Rollen-Suiten prüfen die Pflichtfelder. Ein Plugin-Autor merkt es **beim Bauen**, nicht ein Benutzer im Betrieb | | |
| **5** | Host-Grenze | eine Antwort ohne Pflichtfeld ist ein **Befund**: sichtbar in `/sources` oder im Protokoll, nie still. Die App leitet daraus **nichts** ab — insbesondere nicht `stock`, und sie überspringt die Metadatenkaskade nicht | | |
| **6** | `GET /fields` | die Auskunft nennt Pflicht- und Optionalfelder **auch für den Plugin-Vertrag**, nicht nur für die REST-Modelle. Heute gibt es sie nur für letztere | | |
| **6b** | dieselbe Auskunft | `name` und `type` stehen dort als **Pflicht**. Heute sagt sie `required: false` — das widerspricht der Entscheidung, sobald sie umgesetzt ist | | |
| **7** | `contract/core-contract.json` | `core_version` steigt, weil ein optionales Feld zum Pflichtfeld wird. Das ist laut eigener Regel **breaking** → Major | | |
| **8** | die vier eingebauten Plugins | jedes liefert die Pflichtfelder oder antwortet ehrlich mit `NotFound` | | |
| **9** | die CSV-Beispiele | `canada_file` bekommt die Spalte `type`; ohne sie könnte es den Vertrag nicht mehr erfüllen. Siehe T-37 | | |
| **10** | `docs/plugins.md` | ein Plugin-Autor liest, welche Felder er liefern **muss** | | |

---

## Warum das ein Gate ist und kein Follow-up

Ohne diese Regel ist die zentrale Zusage des Plugin-Systems nicht prüfbar.
„Eine fremde Quelle kann die App erweitern" heißt, dass die App weiß, was sie
von ihr erwarten darf. Heute weiß sie es nicht — sie hat es dreimal
stillschweigend nicht bekommen und drei Symptome gezeigt, die niemand
miteinander in Verbindung gebracht hätte.

T-28 fragt „ist das Ganze benutzbar geworden?". Eine Oberfläche, die bei einer
unvollständigen Quelle leere Felder zeigt statt eines Hinweises, beantwortet
diese Frage mit Nein — und zwar erst beim Benutzer.

---

## Auflösung

_(offen — wartet auf Mikes Entscheidung zu `#1`)_
