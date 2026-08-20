# T-24 · Den REST-Core als Vertrag festschreiben

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend) | offen | 4 h | Vertrag festlegen und prüfbar machen, keine Verhaltensänderung | — |

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

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Vertragsdokument | Core-Pflichtfelder samt Nullability sind benannt | | |
| 2 | dasselbe | Bedeutung von `price`, `quote_time`, `fetched_at`, `cached`, `stale` steht fest | | |
| 3 | dasselbe | bereinigt gegen unbereinigt beim Tages-Schlusskurs ist entschieden | | |
| 4 | Antwort ohne verwertbaren Preis | Fehler statt Antwort mit geratenen Werten | | |
| 5 | Antwort mit Preis | Währung ist **immer** gesetzt | | |
| 6 | Core-Fixtures | liegen als Datei vor und sind von außen nutzbar | | |
| 7 | OpenAPI-Schnappschuss | ein Test schlägt an, wenn sich der Core unbemerkt ändert | | |
| 8 | `make test` | grün | | |

---

## Details

### Was festzulegen ist

- Core-Pflichtfelder und ihre Nullability
- kanonische Identität `(ticker, mic)` plus garantierter Anzeigewert `symbol`
- **Pflichtwährung** für verwertbare Preise und Tagespunkte
- Bedeutung von `price`, `quote_time`, `fetched_at`, `cached`, `stale`
- bereinigt gegen unbereinigt beim Tages-Schlusskurs
- die additive `details`-Hülle: unbekannte Einträge müssen ignorierbar sein
- Fehlerverhalten bei unvollständigem Core — **kein** Raten
- was additiv ist und was ein Bruch wäre
- Profil-/Datensatz-Generation, damit Konsumenten einen Wechsel bemerken

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
