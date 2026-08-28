# T-36 · Die fünf Befunde aus dem UI-Lauf beheben

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | umgesetzt, zur Prüfung | 4 h | Vertragsbruch bei `yahoo-search`, verworfene Identitätsfelder, Namensverlust beim Refresh, generische Fehlermeldung, zwei Layoutfehler | — |

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

_(offen — Codex prüft `405d659`)_
