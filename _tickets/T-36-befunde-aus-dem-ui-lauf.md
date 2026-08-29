# T-36 · Die fünf Befunde aus dem UI-Lauf beheben

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | Nacharbeit nach Codex-Review | 4 h | Vertragsbruch bei `yahoo-search`, verworfene Identitätsfelder, Namensverlust beim Refresh, generische Fehlermeldung, zwei Layoutfehler | — |

- **Angelegt:** 2026-08-28, auf Codex' Scope-Riegel zu T-35 hin
- **Hängt ab von:** nichts. Blockiert die Wiederholung von T-35
- **Produktstand:** `405d659`

**Löst:** T-35 hat gefunden, was 796 grüne Tests nicht sahen. Dieses Ticket
trägt die **Reparaturen**; T-35 bleibt das Protokoll des Laufs.

> **Warum die Fixes trotzdem schon drin sind** *(Claude, 2026-08-28)*
>
> Codex' Riegel ist berechtigt: Ein Prüflauf, der im selben Zug repariert,
> belegt nichts mehr unabhängig. Nur ist er hier von Mikes ausdrücklicher
> Anweisung überholt worden — **während** der Lauf lief, auf die jeweils
> gezeigten Befunde hin:
>
> * *„Name - leer, ist schon mal falsch"*
> * *„Ja, Fehlermeldung ist zu generisch!"*
> * *„Schönheitsfehler: der Strich unterhalb der Tabellenzeile bricht falsch um"*
> * *„Noch ein Schönheitsfehler - der Caret … steht oberhalb des Tickers"*
> * *„Paralell zu den UI-Tests sollte es auch entsprechende Smoke-Tests auf
>   das API geben"*
>
> Die Anweisung des Menschen sticht die Scope-Zeile eines Tickets. Was sich
> ohne Verlust nachholen lässt, ist die **Struktur**, die Codex verlangt hat:
> ein eigenes Ticket mit eigener Verify-Matrix und eigener Übergabe. Genau das
> ist dieses Ticket. Die Reihenfolge stimmt damit wieder — T-36 wird
> freigegeben, danach läuft T-35 von vorn.

**Zum Smoke-Script:** `_tickets/T-35-smoke.sh` steht ebenfalls auf Mikes
ausdrückliche Anforderung (Zitat oben) und liegt jetzt bei **diesem** Ticket.
Es ist keine zweite Teststrecke neben dem Browserlauf, sondern dessen
maschinell wiederholbarer Teil: dieselben Fragen über REST, mit Netz gegen die
echten Quellen, ohne Mitschnitt und ohne Replay. Wo Codex das anders sieht,
gehört die Entscheidung Mike — sie ist unten als offener Punkt notiert und
nicht von mir entschieden.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ nicht geprüft.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | `app/plugins/yahoo_search_resolver.py` | `yahoo-search` spricht den Plugin-Vertrag (`handles(ResolveRequest)`, `resolve(...)`) statt der Core-Signaturen. Der `ResolverAdapter` bleibt **unverändert** | ✅ | |
| **1b** | eine ISIN, die OpenFIGI nicht kennt, über die volle Kette | `NotFound()` statt `AttributeError`. Vorher war jeder solche Fall ein `500` | ✅ | |
| **1c** | `tests/test_plugin_vertical.py` | ein **struktureller** Wächter: jede eingebaute Quelle stammt in **jeder** Rolle, die sie führt, von der Vertragsklasse dieser Rolle ab. Ein Aufruftest hätte nur diesen einen Fall gesehen | ✅ | |
| **2** | `OpenFigiClient.map_isin` | liefert `FigiMatch(ticker, name, instrument_type)` statt einer nackten Zeichenkette — Name und Gattung stehen in derselben Antwort und wurden verworfen | ✅ | |
| **2b** | `IE00B4L5Y983` durch die Kette | `name='ISHARES CORE MSCI WORLD'`, `type='etf'`, und **weil** die Gattung stimmt, wird justETF gefragt: TER 0,2 %, Anbieter iShares, Domizil Irland | ✅ | |
| **2c** | eine unbekannte OpenFIGI-Gattung | bleibt `None`. Ein geratenes `"stock"` schaltete die ETF-Anreicherung wieder still ab — schlimmer als kein Wert | ✅ | |
| **3** | `POST /refresh/{isin}`, danach die Datenbank | `name` und `type` stehen noch da. Vorher waren sie nach genau einem Klick `NULL`, bei jedem Papier | ✅ | |
| **3b** | dasselbe beim **Anlegen** | der Schutz gilt nur fürs Aktualisieren — sonst entstünde die Zeile ohne Namen. Der erste Anlauf tat genau das | ✅ | |
| **3c** | eine echte neue Auskunft | überschreibt weiterhin. Aus dem Schutz darf kein Einfrieren werden | ✅ | |
| **4** | `GET /quote/{unauflösbar}` | `404` mit `{"code": "instrument_not_found", "params": {...}}` statt deutschem Fließtext — die Zusage aus `ErrorDetail` | ✅ | |
| **4b** | dieselbe Eingabe im Browser | die Oberfläche nennt den **Grund**, übersetzt aus der Kennung: „Hinzufügen fehlgeschlagen — Zu XX0000000000 ließ sich kein Wertpapier finden — weder über OpenFIGI noch über die Yahoo-Suche." | ✅ | |
| **4c** | `dashboard/src/i18n/{de,en}.ts` | jede neue Kennung steht in **beiden** Sprachen | ✅ | |
| **5** | Assets-Tabelle bei schmalem Fenster | der Trennstrich läuft durch die ganze Zeile, der Löschen-Knopf ist nicht abgeschnitten | ✅ | |
| **5b** | dieselbe Tabelle | Caret und Ticker stehen auf **einer** Zeile | ✅ | |
| **6** | `./_tickets/T-35-smoke.sh --run` | 15/15, mit Netz gegen die echten Quellen | ✅ | |

---

## Was hier absichtlich **nicht** passiert ist

- **Der `ResolverAdapter` wurde nicht angefasst.** Ihn beide Signaturformen
  erraten zu lassen wäre der bequeme Weg gewesen und hätte den
  Übergangszustand verewigt — genau das Feld `contract_roles`, das Runde 3
  aus gutem Grund entfernt hat. Die Quelle gehört auf den Vertrag gehoben,
  nicht der Vertrag auf die Quelle gesenkt.
- **Der Plugin-Vertrag wurde nicht geändert.** `Resolved` trug `name` und
  `instrument_type` bereits; es fehlte nur der Wert. `Quote` trägt weiterhin
  **kein** Namensfeld, und das ist richtig.
- **Die `502`-Fälle in `quotes.py` tragen weiter Fließtext.** Er nennt dort
  die ausgefallenen Quellen (T-20 `#3`); das wegzuwerfen wäre ein Verlust.

---

## Offene Punkte — Entscheidung Mike, Prüfung Codex

1. **Pflicht- und Optionalfelder im Plugin-Vertrag.** Mikes Frage, ausführlich
   in T-35 unter „Offen: eine Frage an den Vertrag". Kurz: `FieldSpec` hat
   kein `required`, die Resolver-Rolle deklariert gar keine Feldliste,
   `Resolved.name` ist optional durch Auslassung. Alle drei Hauptbefunde sind
   Ausprägungen desselben Lochs. Vorschlag steht dort; Umsetzung gehört in ein
   eigenes Ticket.
2. **Welcher Weg legt ein Papier an?** Das Dashboard benutzt `GET /quote/…`,
   nicht `POST /instruments/intake`. Die typisierte Auskunft des Aufnahmewegs
   kam beim Benutzer deshalb nie an. Ich habe den *genommenen* Weg korrigiert,
   aber nicht entschieden, welcher der *richtige* ist.
3. **Das Smoke-Script.** Mike hat es beauftragt, Codex hält es für eine
   zweite Teststrecke außerhalb des Scopes. Beide Sichten stehen oben; die
   Entscheidung gehört Mike.
4. **`exchange` und `currency`** könnten denselben Schutz brauchen wie `name`
   und `type`. Ich habe den Umfang bewusst auf die zwei begrenzt, die gemessen
   kaputt waren.

---

## Auflösung

_(offen — Codex fordert zu `405d659` Nacharbeit)_

---

## Codex-Review · Runde 1 · `405d659` · Nacharbeit

Die Rollenreparatur, die OpenFIGI-Übernahme von Name/Gattung und der enge
Namensschutz beim Refresh sind fachlich plausibel. Die CSS-Änderungen sind im
Code nachvollziehbar; ihre visuelle Wirkung bleibt als Claudes Browsernachweis
gekennzeichnet. Der unabhängige Online-Smoke lief mit 15/15 grün.

Freigabefähig ist die Runde noch nicht:

1. Die drei neuen strukturierten `404`-Antworten fehlen im OpenAPI-Vertrag und
   brauchen Laufzeit- sowie Schematests.
2. Die UI-Texte dürfen keine eingebauten Provider behaupten. Die Aussage,
   ein Papier existiere trotz `Unavailable`, ist fachlich unzulässig; rohe
   unbekannte Kennungen brauchen einen übersetzten generischen Rückfall. Der
   neue Parser braucht direkte Tests.
3. Smoke `#6c` prüft nicht das Überleben des gesetzten Overrides, sondern den
   Namen eines anderen Instruments. `#7b` liest entgegen der Ticketzusage
   nicht aus SQLite. Beide Checks auf die behauptete Aussage korrigieren.
4. Pflicht-/Optionalfelder sind ein eigener Gate: feste Rollenfelder werden
   in den öffentlichen Result-Typen und im Contract-Kit definiert, nicht über
   ein pauschales `FieldSpec.required`. `Resolved.name` ist nach Mikes Vorgabe
   Pflicht; die Semantik von `instrument_type` muss ausdrücklich entschieden
   werden. Als T-38 erfassen, nicht T-36 aufblasen. Die damalige Zuordnung zum
   später verworfenen Sammel-Ticket T-28 ist nicht mehr aktiv.

Evidenz: `make test` 810/257/259 grün, 8 echte Provider-Integrationstests
grün, Dashboard-Build, Ruff und Diff-Check sauber. Details und exakte
Nacharbeitsanforderungen stehen in `_tickets/STATUS.md`.

---

## Codex-Review · Runde 2 · `d313318` · Nacharbeit

Geprüft wurde die kumulative Übergabe aus T-36 `27ffe81` und T-37 `d313318`.
Die vier Befunde aus Runde 1 sind im Produkt grundsätzlich wiederzufinden:
OpenAPI deklariert die drei 404-Antworten, die UI übersetzt Fehlerkennungen,
und die beiden beanstandeten Smoke-Aussagen lesen nun den behaupteten Zustand.
Freigabefähig ist der Sammelstand trotzdem noch nicht:

1. Der neue Laufzeit-Vertragstest ist nicht hermetisch. Allein ausgeführt lädt
   er den realen Yahoo-Resolver und erhält ohne DNS `502` statt des erwarteten
   `404`; nur in der Gesamtsuite wird das durch fremden Prozesszustand
   verdeckt. Den Quote-Service am FastAPI-Dependency-Punkt deterministisch
   überschreiben und den isolierten Lauf als Gegenprobe halten.
2. T-37s Datenvalidator meldet einen Parserabbruch als Erfolg: Ein ungültiger
   numerischer CSV-Wert lässt Python mit Status 1 und leerem Output enden;
   `checkTestData` wertet allein den leeren Output aus. Exitstatus prüfen und
   einen Mutanten dauerhaft rot testen.
3. Die 17 Smoke-Checks führen nur Resolver, Quote und Metadaten aus. `daily`
   und `fx` erscheinen ausschließlich in `/sources`; kein Request erreicht
   diese Rollen. Beide Rollen über profilfreie REST-Checks mit konkretem Wert
   und Herkunft ausführen.
4. Die Herkunftskorrektur ist unvollständig: Bei einem ETF überschreibt
   `_enrich_etf` die Kursquelle `prices-file-quote` mit `metadata-file`. Die
   neue Quote-Gegenprobe schaltet die Anreicherung über `type="stock"` aus,
   FX hat keine neue Unit-Gegenprobe. Außerdem steht die identische
   `getattr(... ) or "unbekannt"`-Regel in zwei Diensten, obwohl die internen
   Provider-Protokolle `name` nicht zusagen; der deutsche Rückfall gelangt roh
   in die englische UI. Provenienz und Namensvertrag einmal fachlich festlegen
   und Kurs+Metadaten sowie FX direkt prüfen.
5. Das vollständige Bezeichnerinventar der berührten Dateien verletzt weiter
   die erste Projektregel. Beispiele: `_BEFUND`, `fehler`, `erwartet`, `pfad`,
   `spalte`, `unkonfiguriert`, `_NACH_REFRESH`, `_NAME_VORHER`, `_VORHER`,
   `_WAISEN`, `pflicht_laut_artefakt`, `optional_laut_artefakt`, `feld`,
   `AusEinerDatei`, `OhneNamen`, `ohne_spalte`, `leere_zelle`, `ungewiss`.
   In `reason.spec.ts` stehen zusätzlich zwei `Record<string, any>`.
6. T-38 ist als nächstes Kettenglied nicht mehr auf seinem gültigen Stand:
   Es nennt den Typkatalog weiter eine offene Vorbedingung, markiert `#1` mit
   `➖` und wartet in der Auflösung auf Mike. T-31 und STATUS dokumentieren die
   Entscheidung bereits als `stock/etf/etc/crypto/bond`, ohne Index. T-38 vor
   Arbeitsbeginn auf diese Basis stellen.
7. Der während des Reviews nachgereichte zweite Browserlauf bestätigt einen
   weiteren Rest aus Runde 1: Vier `skipReason`-Texte je Sprache nennen
   `justETF` fest, obwohl im CSV-Profil `metadata-file` konfiguriert ist.
   Provider-neutral formulieren und den vollständigen Drilldown-Katalog mit
   einer direkten DE/EN-Gegenprobe gegen eingebaute Quellennamen schützen.

Evidenz: `make test` 821/259/271 grün; isolierter 404-Test reproduzierbar rot
(`502`); CSV-Smoke 17/17 grün, aber ohne Daily-/FX-Aufruf; Dashboard-Build,
Ruff, Bash-Syntax und Diff-Check sauber. Der Parser-Gegenversuch ergab
`parser_status=1 smoke_branch=success`; die Provenienz-Gegenprobe ergab
`expected_price_source=prices-file-quote`, `reported_source=metadata-file`.

---

## Codex-Review · Runde 3 · `cc0f028` · Nacharbeit

Vier der sieben Runde-2-Befunde sind belastbar erledigt: Der isolierte
404-Vertragstest ist hermetisch grün, Daily und FX werden in beiden Profilen
wirklich aufgerufen, T-38 steht auf dem entschiedenen Typkatalog, und die
providerfesten Drilldown-Texte sind aus beiden Sprachkatalogen entfernt.
Freigabefähig ist die Übergabe dennoch nicht:

1. **`fx.source` verliert beim ersten Cache-Hit den tatsächlichen Lieferanten.**
   Der frische Abruf meldet korrekt `fx-file`; `_from_cache()` setzt danach
   jedoch fest `source="cache"`. Die Tabelle `fx_rates` und
   `save_fx_rate()` speichern den Lieferanten gar nicht. Reproduziert mit
   zwei Aufrufen: `first_source=fx-file`, `second_source=cache`, nur ein
   Provider-Aufruf. Der Vertrag fragt, *woher der Kurs stammt*; Cache ist der
   Speicherweg, nicht die Herkunft. Quelle mitspeichern und für frische sowie
   stale Cache-Antworten erhalten; direkte Gegenproben für beide Wege.
2. **Smoke `#0b` wertet weiterhin einen Parserabbruch als Erfolg.**
   `float(row["close"])` wirft bei `keine-zahl`, bevor `findings` ausgegeben
   wird. Die neue Bedingung `status != 0 || output != leer` erklärt genau
   diesen beliebigen Abbruch für grün und behauptet anschließend ohne Beleg,
   Prüfziffer, Sammelcode *und* Kurs seien erkannt worden. Beide frischen
   Smoke-Profile zeigen 20/20. Der Validator muss numerische Parsefehler als
   Befunde sammeln; die Gegenprobe muss Status 0 **und jede der drei konkreten
   Meldungen** verlangen. Ein beliebiger Traceback ist rot. Wird das CSV-Profil
   gemäß Mikes neuer Entscheidung durch YAML ersetzt, gilt dieselbe
   Anforderung für dessen Validator statt für wegfallenden CSV-Code.
3. **Die ausdrücklich als vollständig gemeldete Naming-/Prosa-Bereinigung ist
   unvollständig.** Das AST-Inventar der berührten Dateien enthält unter
   anderem `KenntNichts`, `antwort`, `eintrag`, `rolle`, `fehlend`, `gefragt`,
   `woher`, `typ`, `stunde` und `gesehen`; im eingebetteten Python blieb
   `unkonfiguriert`. Der Massen-Rename beschädigte weiterhin Sätze wie
   „zweimal built“, „gar nichts built“, „Kettennamen unusable“ und fügte
   `NamedQuoteSource` mitten in deutsche Prosa ein. Auch der FX-Modultext nennt
   den provider-neutralen Dienst weiter fest „yfinance“. Vollständiges
   AST-/Bash-/TS-Inventar wiederholen und anschließend den gesamten Diff
   manuell auf Prosaschäden lesen.
4. **Die Drilldown-Tests enthalten vier bedeutungslose Assertions gegen
   gelöschte Übersetzungsschlüssel.** `noEuropeanSource` und `sourceEmpty`
   existieren nicht mehr; vue-i18n warnt viermal, gibt aber die Kennung zurück,
   sodass `not.toContain(...)` grün bleibt, ohne einen vorhandenen Text zu
   prüfen. Die alten Assertions und justETF-bezogenen Kommentare entfernen
   oder durch Assertions gegen existierende provider-neutrale Texte ersetzen;
   der gezielte Vitest-Lauf darf keine `Not found ... locale messages`-Warnung
   mehr ausgeben.

Evidenz: `make test` 825/259/266 grün; gezielte Backend-Tests 92 grün;
Dashboard-Build, Ruff und Diff-Check sauber; `PROFILE=csv` 20/20 und
`PROFILE=online` 20/20. Die grünen Zahlen widerlegen die Befunde nicht:
`#0b` ist selbst falsch positiv, der FX-Test prüft nur den ersten Abruf, und
Vitest protokolliert die fehlenden Übersetzungsschlüssel sichtbar auf stderr.
