# T-31 · Papiere ohne echten MIC — Krypto, Index, Anleihe

- **Status:** offen (entschieden 2026-08-28)
- **Angelegt:** 2026-08-25, beim Bau von T-21 Teil 3, Übergabe 2A
- **Entschieden:** 2026-08-28, Mike im Gespräch mit Claude — Details unten
- **Repo:** StockInfo
- **Abhängt von:** T-21 Teil 3 (Entscheidung 2)
- **Verzahnt mit:** T-38 (Pflichtfelder/`instrument_type` — **ein** gemeinsamer
  `API_VERSION`-Sprung statt zwei) und T-37 (die CSV-Quelle bekommt einen
  zweiten Einsatzort, siehe dort)

## Verify-Matrix

| # | Where | Look for | AI | Human |
|---|---|---|---|---|
| 1 | Entscheidung | Mike hat entschieden: Krypto und Anleihen kommen in den MVP, mit eigener Identitätsform und eigenem Typ; Indizes bleiben draußen | ✅ [^a] | |
| 2 | `app/db.py` | die Identität ist eine getaggte Union: `kind` ∈ `listed`/`pair`/`isin_only`, ein `CHECK` je `kind` erzwingt genau die passende Feldbelegung — halbe Identitäten bleiben unmöglich | | |
| 3 | `app/exchanges.py`, Contract-Kit | `canonical_identity` wird zur Weiche über die Union; `is_real_mic` und `is_canonical_ticker` bleiben unverändert die `listed`-Hälfte. Im Vertrag: discriminated union über `kind` | | |
| 4 | Typ-Katalog | `stock`/`etf`/`etc`/`crypto`/`bond` kanonisch (Ort: T-38); `QUOTE_TYPE_MAP` erweitert um `CRYPTOCURRENCY → crypto`, `BOND → bond` — Erkennen, nicht Raten | | |
| 5 | Aufnahmeweg | die Paar-Identität entsteht aus dem **Gattungs-Befund der Quelle**, nie aus der Symbolform; Eintritt per Symbol (`isin = NULL`), die By-Symbol-Routen tragen ihn | | |
| 6 | Aufnahmeweg | eine **nicht** aufgenommene Gattung (Index) wird mit eigener Kennung `unsupported_instrument_type` abgelehnt — nicht mit dem Zufallsbefund der Symbolform; i18n DE/EN | | |
| 7 | Kursweg | für ein Paar muss die Währung des gelieferten Kurses `quote_currency` entsprechen; eine Abweichung ist ein Datenfehler und wird abgelehnt, nicht still konvertiert | | |
| 8 | Metadatenkaskade | sie läuft nur für Typen, deren Metadaten es geben kann — kein justETF-Abruf für eine Coin, keine TER-Frage an eine Anleihe | | |
| 9 | Tests | `BTC-EUR` prüft das **entschiedene** Verhalten (Annahme als `pair`), ein Index den Ablehnungsgrund, eine Anleihe die `isin_only`-Form samt `quote_unavailable` ohne liefernde Quelle | | |

[^a]: Entschieden am 2026-08-28; die einzelnen Punkte stehen unter
    **Die Entscheidung**. Die Human-Spalte bleibt für Mikes Bestätigung des
    fortgeschriebenen Tickets.

## Die Entscheidung (Mike, 2026-08-28)

1. **Option 3 aus der Fundliste** — eine eigene Identitätsform für Gattungen
   ohne Handelsplatz. Krypto und Anleihen sollen **schon im MVP** erfassbar
   sein.
2. **Jede Gattung bekommt einen eigenen Typ.** Kanonischer Katalog:
   `stock`, `etf`, `etc`, `crypto`, `bond`. ETC ist als gängiger Typ bestätigt;
   ETN kann später ergänzt werden, wenn gebraucht.
3. **Kein Migrationspfad.** Kryptos waren nie unterstützt, es gibt keine
   Altzeile. Bestandszeilen bekommen lediglich `kind = 'listed'` backfilled.
4. **Indizes bleiben draußen** — sie waren Teil des Fundes, sind aber nicht
   Teil der Entscheidung. Sie werden ehrlich abgelehnt
   (`unsupported_instrument_type`), bis eine eigene Entscheidung sie aufnimmt.
5. **Anleihen werden ausschließlich über Quellen bepreist.** Die Handpflege
   (`instrument_overrides`) bleibt Metadaten — ein Preis ist ein Messpunkt mit
   Herkunft (`price NOT NULL`, `quote_time`, `fetched_at`), kein pflegbares
   Attribut. Kein Preis heißt kein Quote-Datensatz, nicht ein Quote mit Lücke.
6. **Die CSV-Quelle wird zum Kettenglied des Online-Profils** (Mikes
   Vorschlag): Das Online-Profil hängt die ohnehin in T-37 gebaute CSV-Quelle
   ans **Ende** seiner Kette. Eine Anleihe fällt durch die Online-Quellen
   durch und landet bei der Datei — im laufenden Online-Profil, ohne
   Profilwechsel. Die Profil-Exklusivität (genau ein Plugin aktiv) bleibt
   unangetastet.

**Offen als eigene Entscheidungszeile:** eine *manuelle Quelle* — ein
Eingabeweg im Dashboard, der einen vollwertigen Quote schreibt (`price`,
`quote_time`, `provider: manual`). Wenn gewollt, ist das ein eigenes kleines
Feature und **keine** Override-Spalte. Für den MVP zurückgestellt; die
CSV-Quelle deckt den Bedarf.

## Der Entwurf: Identität als getaggte Union

Die T-21-Lehre bleibt: kein Wert, der etwas anderes vorgibt zu sein. Statt
eines Sentinel-MIC bekommt die Identität einen expliziten Diskriminator:

```
kind = 'listed'     → ticker + mic          (Aktie, ETF, ETC, börsengehandelte Anleihe)
kind = 'pair'       → base + quote_currency (natives Krypto: BTC/EUR)
kind = 'isin_only'  → isin                  (OTC-Anleihe: die ISIN ist die Identität)
```

- **SQLite:** `ticker`/`mic` werden wieder nullable; ein `CHECK` je `kind`
  erzwingt genau die passende Belegung (`pair` → `base` und `quote_currency`
  gesetzt, `mic IS NULL`; `isin_only` → `isin IS NOT NULL`). „Vollständig"
  ist damit je Gattung definiert, halbe Identitäten bleiben unmöglich.
- **Pydantic/Contract-Kit:** discriminated union über `kind`. Ein Plugin sagt
  ausdrücklich, welche Identitätsform es liefert, statt dass der Host aus
  Feldkombinationen rät.
- **Fähigkeitsdeklaration:** ein Plugin deklariert, welche `kind`s und
  Typen es bedient. Der Host überspringt Quellen, die eine Gattung nicht
  bedienen, und antwortet für den Rest ehrlich mit `quote_unavailable` —
  statt dass ein CSV-Plugin OpenFIGI-Fragen bekommt oder Yahoo eine
  `isin_only`-Anleihe. **Ort:** T-38, wo Pflichtfelder und `instrument_type`
  ohnehin kanonisiert werden; zusammen ergibt das einen einzigen
  `API_VERSION`-Sprung.
- **Symbolformat:** `{base}-{quote}` ist das Paar-Symbol (`BTC-EUR`). Der
  Bindestrich, den `is_canonical_ticker` bei `listed`-Tickers zu Recht
  verbietet, ist hier das Trennzeichen der *anderen* Form. Die Zerlegung
  läuft über `kind`, nie über die Symbolform allein.

## Krypto: der Weg durch die App

Zwei Arten, „Krypto zu halten" — nur eine braucht die neue Form:

| | Krypto-**ETP** (21Shares & Co.) | **natives** Krypto (die Coin) |
|---|---|---|
| ISIN / MIC | vorhanden | gibt es nicht |
| Identität | `listed` — braucht nur den Typ | `pair` — der Gegenstand dieses Tickets |

Der Kern des Paars: `BTC` allein hat keinen Preis. Einen Preis gibt es nur
relativ zu einer Währung, und `BTC-EUR` ≠ `BTC-USD`. Die Rolle, die bei der
Aktie der Handelsplatz spielt („wo gilt dieser Preis?"), spielt beim Paar die
Quote-Währung. `BTC-EUR` neben `BTC-USD` sind zwei Instrumente — so legitim
wie zwei Listings derselben Aktie.

1. **Erfassen** per Symbol (`BTC-EUR`), nicht per ISIN — die gibt es nicht.
   `isin` ist im Schema bereits nullable, die By-Symbol-Routen existieren.
2. **Auflösen:** Quellen ohne `pair`-Fähigkeit werden übersprungen; yfinance
   kennt `BTC-EUR` nativ und meldet `quoteType: CRYPTOCURRENCY`. Aus dem
   Gattungs-Befund — nicht aus dem Bindestrich — entsteht die Paar-Identität.
3. **Speichern:** normale Instrumenten-Zeile mit `kind='pair'`, `base`,
   `quote_currency`, `type='crypto'`, `isin=NULL`.
4. **Kurse:** ab hier nichts Besonderes — `quotes`-Zeilen, Cache, Refresh wie
   bei jedem Papier. Zusatzregel: Kurswährung muss `quote_currency`
   entsprechen (Matrix `#7`).
5. **Metadaten:** TER, Fondsvolumen, Domizil sind Fonds-Begriffe; für
   `type='crypto'` läuft die Kaskade gar nicht erst los (Matrix `#8`).

Krypto ist damit in **beiden** Profilen zu Hause: online über yfinance, im
CSV-Profil über eine Dateizeile. Anders als die Anleihe braucht es keinen
Fallback — es ist die Gattung mit der besten Quellenlage.

## Anleihe: erfassbar sofort, bepreist über Quellen

1. **Erfassen** funktioniert mit `isin_only` sofort — Instrument, Name, Typ,
   Metadaten (inkl. Handpflege) sind da. OpenFIGI kennt Anleihen-ISINs und
   kann Metadaten liefern; einen Preis liefern die Online-Quellen nicht.
2. **Ohne liefernde Quelle** zeigt `/quote/{isin}` den strukturierten
   `quote_unavailable`-Zustand — die wahre Aussage „keine Quelle konnte einen
   Preis feststellen". Die provider-neutralen Fehlertexte aus T-36 Finding 2
   tragen genau diesen Fall.
3. **Der Weg zum Preis ist die CSV-Quelle** — als Kettenende des
   Online-Profils (Entscheidung 6) oder im reinen CSV-Profil. Sie *ist* die
   Handpflege für Preise, nur in ehrlicher Form: jede Zeile mit Zeitpunkt und
   Herkunft, wiederholbarer Refresh, keine zweite Preis-Wahrheit neben
   `quotes`.

## Die CSV-Quelle als Kettenglied — drei Bedingungen

Damit Entscheidung 6 sauber bleibt:

1. **Eigene Quelle, kein Seitenblick im Adapter.** Die Yahoo-Hülle bleibt
   schlank; die CSV-Quelle steht als eigenes Kettenglied in der
   Profilkonfiguration.
2. **Konfiguriert, nicht entdeckt.** Das Profil nennt den Dateipfad; fehlt
   die Datei, meldet die Quelle das dreiwertige „konnte nicht feststellen"
   (T-20) und die Kette läuft weiter. Kein Verzeichnis-Scannen.
3. **Fallback, nicht Override.** CSV steht **zuletzt**: Ein Papier, das
   online und in der Datei steht, bekommt den Online-Kurs; die CSV greift
   nur, wo keine Online-Quelle liefert. Die umgekehrte Semantik wäre ein
   eigenes Feature — nicht im MVP.

Eine Implementierung, zwei Verwendungen — siehe die Notiz in T-37.

## Worum es geht *(Fundlage, 2026-08-25)*

T-21 Teil 3 verlangt seit Entscheidung 2 eine **vollständige kanonische
Identität**: kanonischer Ticker **und** echter MIC nach ISO 10383. Seit
Übergabe 2A steht das im Schema (`ticker`/`mic` als `NOT NULL`), und
`canonical_identity` lehnt alles andere ab.

Damit lässt sich **`BTC-USD` nicht mehr speichern**. Eine Kryptowährung wird
an keinem Handelsplatz im Sinne von ISO 10383 gehandelt; es gibt schlicht
keinen MIC, der wahr wäre. Dasselbe gilt für Indizes und einen Teil der
Anleihen.

**Das ist keine Nachlässigkeit im Entwurf, sondern eine Folge, die niemand
ausgesprochen hat.** Die gemessene Auswirkungstabelle in der Spec führt nur
Aktien und ETFs auf; die Gattungen ohne Handelsplatz kamen darin nicht vor.

Im realen Bestand gab es am 2026-08-25 **keine** solche Zeile — sechs
Instrumente, fünf mit Börsensuffix, dazu `VTI`. `QUOTE_TYPE_MAP` kannte nur
`ETF`, `MUTUALFUND` und `EQUITY`.

## Die Auswege, wie sie beim Fund aussahen

1. **Streng bleiben.** Was keinen echten MIC hat, gehört nicht in den
   Bestand.
2. **Ein Katalogeintrag für „kein Handelsplatz".** Ein MIC-Wert, der keine
   Börse bezeichnet — dieselbe Sorte magischer Wert, die T-21 gerade
   austreibt.
3. **Eine eigene Identitätsform für Gattungen ohne Handelsplatz.**

**Gewählt: Nr. 3** — mit dem Zuschnitt und den Grenzen unter
**Die Entscheidung**.
