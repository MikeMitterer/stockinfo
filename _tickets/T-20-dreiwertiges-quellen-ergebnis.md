# T-20 · Quellen antworten differenziert statt mit `None`

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend) | offen | 3 h | Rückgabetypen der Quellen, Kettenlogik | — |

**Löst:** `resolve_isin` gibt `None` zurück, und das bedeutet drei verschiedene
Dinge: *nicht mein Bereich*, *kenne ich nicht*, *gerade kaputt*. Die Kette kann sie
nicht unterscheiden, der Router auch nicht — deshalb wird jeder Fehlschlag zu 404,
auch wenn beide Quellen nur ausgefallen waren.

Der Vertrag dafür steht bereits: `stockinfo_plugin.types` liefert `Resolved`,
`NotResponsible`, `NotFound` und `Unavailable` (Commit `840121c`). Dieses Ticket
zieht die App nach.

**Hängt an:** nichts. **Blockiert:** T-23 (ohne die Unterscheidung kann eine
Plugin-Kette nicht sinnvoll weiterschalten).

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | `GET /quote/XX0000000000` (Präfix existiert nicht) | 404 — keine Quelle war zuständig oder keine kennt es | | |
| 2 | OpenFIGI und Yahoo künstlich abschalten, bekannte ISIN abrufen | **502**, nicht 404 — „konnte nicht nachsehen" | | |
| 3 | Antwortkörper bei #2 | nennt, welche Quellen ausgefallen sind | | |
| 4 | eine unzuständige Quelle in der Kette | wird übersprungen, ohne eine Anfrage zu stellen | | |
| 5 | `make test` | Backend grün; neue Tests je Antwortart | | |

```bash
curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:8000/quote/XX0000000000"   # #1 → 404
```

---

## Details

### Warum das mehr ist als Kosmetik

Aus dem Unterschied folgen drei Dinge:

| Antwort | Kette | HTTP | Gespeicherter Stand |
|---|---|---|---|
| `NotResponsible` | nächste Quelle, **ohne Kosten** | — | unberührt |
| `NotFound` | nächste Quelle | 404 wenn alle | darf ersetzt werden |
| `Unavailable` | nächste Quelle | **502** wenn alle | **geschützt** |

Die letzte Spalte ist der Grund, warum dasselbe Muster bei den ETF-Metadaten schon
gebaut wurde (`metadata_complete`, Commit `809c48a`): Ein einzelner Ausfall hatte
einen gepflegten Datenbestand mit `NULL` überschrieben.

### Umfang

* `InstrumentResolver` gibt `Resolution` zurück statt `ResolvedInstrument | None`
* `CompositeResolver` wertet die Arten aus und merkt sich, was unterwegs ausfiel
* `handles()` an den Resolvern — unzuständige Quellen kosten dann nichts mehr
* Die Router übersetzen die Gesamtantwort in 404 bzw. 502
* `QuoteService` reicht die Unterscheidung durch

Die Typen werden aus `stockinfo-plugin-api` übernommen, nicht neu erfunden — sonst
gibt es zwei Wahrheiten über denselben Vertrag.

---

## Auflösung

_(offen)_
