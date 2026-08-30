# T-38 · Pflichtfelder verbindlich machen — und abfragbar

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Plugin-Vertrag + Core + REST) | offen | 1 Tag | Pflicht/Optional je Result-Typ, Gattungs-Vokabular, Durchsetzung, REST-Auskunft | — |

- **Angelegt:** 2026-08-28, aus T-36 Runde 1 (Codex) und Mikes Entscheidungen
- **Hängt ab von:** T-36 (die dort behobenen Befunde sind die Symptome)
- **Blockiert:** nichts
- **Berührt:** T-31 (Papiere ohne MIC), T-34 (Wächter), T-37 (YAML-Fallback)

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

## Die Vorbedingung — **entschieden**, nicht mehr offen

> **Mike, 2026-08-28:** *„Bei den Typen gibt es aktuell ETF und STOCK - was
> ist mit ETC, was ist mit Kryptos?"*
>
> **Beantwortet in T-31, Entscheidung 2 (Mike, 2026-08-28):** Kanonischer
> Katalog `stock`, `etf`, `etc`, `fund`, `crypto`, `bond`. `fund` bezeichnet
> nicht börsengehandelte Fonds; ETC ist als gängiger Typ bestätigt, ETN kann
> später ergänzt werden. **Indizes bleiben draußen** und
> werden mit `unsupported_instrument_type` ehrlich abgelehnt.
>
> Damit ist dieses Ticket nicht mehr blockiert. Die Abwägung unten bleibt
> stehen, weil sie erklärt, **warum** der Katalog gebraucht wird — nicht als
> offene Frage, sondern als Begründung der getroffenen Entscheidung.

**Der Katalog war die Vorbedingung, und das gilt weiterhin.** Heute kennt die App
genau zwei Gattungen (`app/providers/base.py`: `QUOTE_TYPE_MAP = {"ETF":
"etf", "MUTUALFUND": "etf", "EQUITY": "stock"}`). `instrument_type` zur
Pflicht zu machen, **bevor** das Vokabular reicht, erzwingt eine Lüge: Ein ETC
wäre dann „stock" oder „etf", und beides ist falsch.

Der entschiedene Katalog, mit dem Grund je Eintrag:

| Gattung | Warum sie dazugehört | Was daran hängt |
|---|---|---|
| `stock` | vorhanden | — |
| `etf` | vorhanden | — |
| `etc` | Rohstoff-Tracker sind formal **keine** Fonds. justETF führt sie getrennt, OpenFIGI ebenfalls | Die ETF-Anreicherung muss entscheiden, ob sie für ETCs greift. `etn` kann später folgen |
| `fund` | nicht börsengehandelter Fonds; `MUTUALFUND → etf` ist fachlich falsch | nutzt `listed`, wenn ein echter Handelsplatz vorliegt, sonst `isin_only`; Quellen deklarieren die Gattung ausdrücklich |
| `crypto` | Mikes ausdrückliche Frage | Braucht die Paar-Identität aus T-31 — eine Coin hat keinen MIC |
| `bond` | Anleihen | Braucht die `isin_only`-Identität aus T-31 |

**Nicht aufgenommen:** `index` — ehrlich abgelehnt mit
`unsupported_instrument_type`, bis eine eigene Entscheidung ihn aufnimmt.
`fund` ist mit Mikes Entscheidung vom 2026-08-29 aufgenommen. Die bestehende
Abbildung `MUTUALFUND → etf` wird durch `MUTUALFUND → fund` ersetzt. Ein Fonds
ohne kanonische `listed`- oder `isin_only`-Identität wird nicht geraten.

**Die Aufzählung bleibt offen**, wie es der Vertrag für `source` schon hält
(„Ein neuer Wert in einer offenen Aufzählung" gilt dort ausdrücklich als
additiv). Dann ist `etn` ein Nachtrag und kein Bruch. Was die App nicht kennt,
zeigt sie als das, was die Quelle sagt, statt es auf `stock` zu runden — **das
Runden war der Fehler**, den dieses Ticket verhindert.

**Zwei Gattungen hängen an T-31, und das ist der Grund für das Paket.** Krypto
und Anleihe scheitern nicht am Vokabular, sondern an der Identität `(ticker,
mic)`. T-31 löst das mit der getaggten Union und verlangt ausdrücklich **einen
gemeinsamen `API_VERSION`-Sprung** mit diesem Ticket. Wer zuerst anfängt,
erzeugt den zweiten Sprung.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ nicht geprüft.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | Entscheidung Mike | das Gattungs-Vokabular steht fest: `stock`, `etf`, `etc`, `fund`, `crypto`, `bond`; Indizes bleiben draußen (T-31, Entscheidung 2) | ✅ | |
| **2** | `stockinfo_plugin.types` | `Resolved.name` und `Resolved.instrument_type` sind Pflichtfelder. Kein Vorgabewert, und die Zusage steht im Docstring | ✅ [^r1] | |
| **3** | `API_VERSION` | der Sprung ist **ehrlich** gemacht: Ein optionales Feld zur Pflicht zu erheben ist laut eigener Kompatibilitätsregel ein **Bruch**. Ein Plugin nach altem Vertrag wird abgewiesen und nicht stillschweigend geduldet | ✅ [^v] | |
| **4** | Contract-Kit | die Rollen-Suiten prüfen die Pflichtfelder. Ein Plugin-Autor merkt es **beim Bauen**, nicht ein Benutzer im Betrieb | ✅ [^r1] | |
| **5** | Host-Grenze | eine Antwort ohne Pflichtfeld ist ein **Befund**: sichtbar in `/sources` oder im Protokoll, nie still. Die App leitet daraus **nichts** ab — insbesondere nicht `stock`, und sie überspringt die Metadatenkaskade nicht | ✅ [^r1] | |
| **6** | `GET /fields` | die Auskunft nennt Pflicht- und Optionalfelder **auch für den Plugin-Vertrag**, nicht nur für die REST-Modelle. Heute gibt es sie nur für letztere | ✅ [^r1] | |
| **6b** | dieselbe Auskunft | `name` und `type` stehen dort als **Pflicht**. Heute sagt sie `required: false` — das widerspricht der Entscheidung, sobald sie umgesetzt ist | ✅ [^r1] | |
| **7** | `contract/core-contract.json` | `core_version` steigt, weil ein optionales Feld zum Pflichtfeld wird. Das ist laut eigener Regel **breaking** → Major | ✅ [^m] | |
| **8** | die vier eingebauten Plugins | jedes liefert die Pflichtfelder oder antwortet ehrlich mit `NotFound` | ✅ [^r1] | |
| **9** | das YAML-Beispiel | jeder `instrument`-Eintrag trägt `name` und `type`; ein nicht börsengehandelter Fonds kommt als `fund`, nicht `etf`. Siehe T-37 | ➖ [^t37] | |
| **10** | `docs/plugins.md` | ein Plugin-Autor liest, welche Felder er liefern **muss** | ✅ [^r1] | |

[^r1]: Umsetzung Runde 1 gegen `96b3184`. Die Orakel entstanden **vor** dem
    Code (`20be6d6`, zehn von dreizehn rot) und stammen aus dieser Matrix.
[^v]: **Kein zweiter Sprung.** Das Ticket verlangt einen gemeinsamen
    `API_VERSION`-Sprung mit T-31 („Wer zuerst anfängt, erzeugt den zweiten
    Sprung"). T-31 hat ihn auf `2` gemacht; veröffentlicht ist nichts,
    `plugin_api` steht auf `0.2.0`. Die Pflichtfelder fahren deshalb auf
    dieser Zahl — genau der eine Sprung, den das Paket wollte.
[^m]: Entscheidung Mike, 2026-08-30: Die REST-Zusage zieht mit.
    `core_version` 3.0.0 → 4.0.0, weil ein optionales Feld zum Pflichtfeld
    wird. Betroffen sind `quote.name`, `quote.type`, `instrument.name`,
    `instrument.type`.
[^t37]: Gehört zum YAML-Plugin und wird dort erfüllt — T-37 ist das nächste
    Kettenglied. Hier bewusst offen gelassen statt vorweggenommen.

---

## Warum das ein Gate ist und kein Follow-up

Ohne diese Regel ist die zentrale Zusage des Plugin-Systems nicht prüfbar.
„Eine fremde Quelle kann die App erweitern" heißt, dass die App weiß, was sie
von ihr erwarten darf. Heute weiß sie es nicht — sie hat es dreimal
stillschweigend nicht bekommen und drei Symptome gezeigt, die niemand
miteinander in Verbindung gebracht hätte.

Eine Oberfläche, die bei einer unvollständigen Quelle leere Felder zeigt statt
eines Hinweises, verlagert den Vertragsfehler bis zum Benutzer.

---

## Auflösung

_(umgesetzt am 2026-08-30, Runde 1 gegen `96b3184`; Verify `#9` bleibt T-37
vorbehalten.)_

`Resolved.name` und `Resolved.instrument_type` haben keinen Vorgabewert mehr.
Das ist die Hälfte, die im Ticket stand — und die kleinere.

**Die andere Hälfte hat der Bau selbst gefunden.** Ein Pflichtfeld verhindert
das *Weglassen*, nicht das *Füllen mit nichts*: `name=""` bleibt baubar, und
für jede Prüfung, die auf `None` schaut, sieht das aus wie eine Auskunft. Die
eigentliche Durchsetzung liegt deshalb in `invariants.resolution_problem` —
einer Funktion, die Contract-Kit, Host-Grenze und Plugin-Autor gemeinsam
benutzen.

Drei Fehler wurden dabei sichtbar, die vorher kein Test sah:

1. `require_core_values` kannte die neuen Pflichtfelder nicht — der Fehlfall
   wäre ein `500` ohne Auskunft gewesen, an vierzehn Stellen zugleich.
2. `get_quote_for_known` reichte die Gattung durch, den Namen nicht. Dieser Weg
   löst bewusst nicht auf; **jeder Refresh** wäre damit ein `502` geworden.
3. Das Repository schützte gegen `None`, nicht gegen `""` — ein leerer Name
   überschrieb den gespeicherten. Derselbe Befund wie im UI-Lauf, eine Schicht
   tiefer.

Befund 3 kam von einem Test, dessen alte Fassung sich nicht mehr bauen ließ.
Statt ihn zu streichen, wurde er auf den leeren String umgestellt — auf die
Lücke, die ein Pflichtfeld offen lässt.
