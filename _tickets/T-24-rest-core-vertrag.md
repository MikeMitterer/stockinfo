# T-24 · Den REST-Core als Vertrag festschreiben

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend) | offen | 6 h | Vertrag festschreiben + eine bewusste Verhaltenskorrektur | — |

**Löst:** Was die API zusagt, ergibt sich heute aus dem Code — nirgends steht,
welche Felder verbindlich sind, was `stale` bedeutet oder ob ein Schlusskurs
bereinigt ist. Solange das so bleibt, ist jede Änderung an der Identität ein
Blindflug.

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

**Hängt an:** nichts. **Blockiert: T-21** — erst wissen, was zugesagt ist, dann
die Identität ändern.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

**Ebene 1 — jetzt festschreiben und gegen den Bestand prüfen:**

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Vertragsdokument | Core-Pflichtfelder samt Nullability sind benannt | | |
| 2 | dasselbe | Bedeutung von `price`, `quote_time`, `fetched_at`, `cached`, `stale` steht fest | | |
| 3 | dasselbe | bereinigt gegen unbereinigt beim Tages-Schlusskurs ist entschieden | | |
| 4 | dasselbe | `listing_id` und das Verhalten bei mehrdeutigem `symbol` sind festgelegt | | |
| 5 | dasselbe | Regel, was additiv ist und was ein Bruch wäre | | |
| 6 | Core-Fixtures | liegen als Datei vor und sind von außen nutzbar | | |
| 7 | OpenAPI-Schnappschuss | ein Test schlägt an, wenn sich der Core unbemerkt ändert | | |
| 7b | **`GET /fields`** | liefert die Pflichtfelder **samt Vertragsversion** — zur Laufzeit abfragbar, nicht nur dokumentiert | | |
| 7c | Vertragsversion erhöhen | ein Konsument kann an der Nummer erkennen, dass er prüfen muss | | |

**Ebene 2 — bewusste Verhaltenskorrektur (kein „nur Dokumentation"):**

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 8 | Antwort mit Preis, aber ohne Währung von der Quelle | **Fehler** statt Antwort mit geratenem Wert | | |
| 9 | Bestandsprüfung | wo der heutige Code den Mindestvertrag verletzt, ist es benannt und behoben | | |
| 10 | `make test` | grün | | |

**Ebene 3 — hier nur benannt, umgesetzt anderswo:** `ticker`/`mic` → T-21,
`details`-Container → T-26, `generation_id` → T-25.

---

## Details

### Der Kernpunkt: eindeutige Adressierung

`(ticker, mic)` wird die Identität — aber den Unique-Index auf `symbol` einfach
zu entfernen, wäre ein stiller Bruch. Es gibt **acht** symbolbasierte
Endpunkte, und der Lookup dahinter lautet:

```sql
SELECT * FROM instruments WHERE symbol = ? ORDER BY id LIMIT 1
```

Nicht undefiniert, sondern **definiert falsch**: Bei zwei gleichnamigen Zeilen
trifft `DELETE /instruments/by-symbol/{symbol}` die ältere.

**Festzulegen ist deshalb:**

- **`listing_id`** — eindeutig, anbieterunabhängig, Schlüssel aller neuen Endpunkte
- **`symbol`** — bleibt Pflichtfeld und Anzeigename, aber **nicht** garantiert eindeutig
- Symbol-Endpunkte antworten bei Mehrdeutigkeit mit **`409 Conflict`** samt
  Kandidatenliste, statt still das Falsche zu treffen

Kollidieren kann es nur dort, wo mehrere MICs dasselbe leere Suffix teilen —
also bei US-Börsen, sobald `US` in `XNYS`/`XNAS` zerfällt (durch T-21). Vorher
ist das Symbol durch die Suffix-Regel automatisch eindeutig.

### Was sonst festzulegen ist

- Core-Pflichtfelder und ihre Nullability
- kanonische Identität `(ticker, mic)`, `listing_id` als Schlüssel, `symbol` als
  garantierter Anzeigewert
- **Pflichtwährung** für verwertbare Preise und Tagespunkte
- Bedeutung von `price`, `quote_time`, `fetched_at`, `cached`, `stale`
- bereinigt gegen unbereinigt beim Tages-Schlusskurs
- die additive `details`-Hülle: unbekannte Einträge müssen ignorierbar sein
- Fehlerverhalten bei unvollständigem Core — **kein** Raten
- was additiv ist und was ein Bruch wäre
- Profil-/Datensatz-Generation, damit Konsumenten einen Wechsel bemerken

### Der Vertrag ist abfragbar, nicht nur dokumentiert

*(Mikes Anforderung, 2026-08-20.)* Ein Dokument, das niemand zur Laufzeit lesen
kann, hilft einem Konsumenten nicht. Deshalb liefert `GET /fields` die
Pflichtfelder **samt Vertragsversion**:

```
GET /fields
{
  "core_version": "1.0",
  "core": [
    { "name": "price",    "kind": "number", "required": true },
    { "name": "currency", "kind": "string", "required": true },
    …
  ],
  "details_version": 7,          ← die offene Menge, siehe T-26
  "details": [ … ]
}
```

Dieselbe Logik für beide Ebenen: Der Core hat eine Vertragsversion, die offenen
Details haben eine eigene Nummer. Ein Konsument mit gecachter Feldliste erkennt
an der Nummer, dass er neu holen muss — ohne den Inhalt zu vergleichen.

Die Fixtures aus dem Verify-Teil sind der statische Gegenpart dazu: Sie prüfen
denselben Vertrag beim Bauen, `GET /fields` beantwortet ihn im Betrieb.

### Warum das vor T-21 gehört

StockInfo ist verteilt (GitHub, Docker Hub, Unraid-Template). Wer die API direkt
nutzt statt des mitgelieferten Dashboards, bekommt jeden Bruch ab — und man
erfährt es nicht.

Dazu kommt der Testkonsument StockPortfolio. Er gehört demselben Autor, ist aber
ein **eigenes Artefakt mit eigenem Image und eigenem Update-Zeitpunkt**: Auf
einer Unraid-Box laufen beide als getrennte Container, die niemand gleichzeitig
aktualisiert. Gemeinsame Eigentümerschaft ersetzt keinen Vertrag.

### Prüfbar, ohne Cross-Repo-CI

1. StockInfo prüft den Core gegen **Fixtures** und einen
   OpenAPI-Kompatibilitätsschnappschuss.
2. StockPortfolio prüft seine Mapper gegen dieselben veröffentlichten Fixtures.
3. Vor Releases ein kleiner Lauf: bestehende Position gegen frische Profil-DB.

Kein Repo klont das andere.

---

## Auflösung

_(offen)_
