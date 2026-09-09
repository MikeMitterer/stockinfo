# T-20 · Quellen antworten differenziert statt mit `None`

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend) | codex-abgenommen | 3 h | Rückgabetypen der Quellen, Kettenlogik | — |

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
| 1 | `GET /quote/XX0000000000` (Präfix existiert nicht) | 404 — keine Quelle war zuständig oder keine kennt es | ✅ [^a] | |
| 2 | OpenFIGI und Yahoo künstlich abschalten, bekannte ISIN abrufen | **502**, nicht 404 — „konnte nicht nachsehen" | ✅ [^b] | |
| 3 | Antwortkörper bei #2 | nennt, welche Quellen ausgefallen sind | ✅ [^c] | |
| 4 | eine unzuständige Quelle in der Kette | wird übersprungen, ohne eine Anfrage zu stellen | ◑ [^d] | |
| 5 | `make test` | Backend grün; neue Tests je Antwortart | ✅ [^e] | |

```bash
./_tickets/40-done/T-20-smoke.sh --run    # #1, #2, #3, #5 — zwei Läufe, mit und ohne Netz
```

[^a]: `T-20-smoke.sh` Lauf 1 (mit Netz): `#1` HTTP **404** für
    `XX0000000000`, `#1b` HTTP 200 für `IE00B4L5Y983`. Die zweite Zeile ist
    die Gegenprobe — ohne sie stünde nicht fest, dass der 404 aus „nachgesehen
    und nichts gefunden" kommt und nicht aus einem stillen Ausfall.
[^b]: `T-20-smoke.sh` Lauf 2: **dieselbe** ISIN `IE00B4L5Y983`, jetzt HTTP
    **502**. Das Netz wird per Proxy auf einen geschlossenen Port
    abgeschnitten (Port 9, discard) — das trifft OpenFIGI wie Yahoo und
    braucht keinen Eingriff im Produktivpfad. Der Unterschied zwischen den
    beiden Läufen **ist** der Befund des Tickets.
[^c]: Beobachtet: `IE00B4L5Y983: keine Quelle konnte nachsehen — openfigi:
    [Errno 61] Connection refused; yahoo: Failed to perform, curl: (…`. Der
    Text entsteht in `CompositeResolver` und wird vom Router unverändert
    durchgereicht; vorher stand dort ein festes „Kein Kurs für ISIN …".
[^d]: **Nur als Unit-Test.** `test_unzustaendige_quelle_wird_nicht_gefragt`
    belegt, dass eine Quelle mit `handles() == False` gar nicht erst
    aufgerufen wird (Zähler bleibt auf 0), und
    `test_nur_unzustaendige_quellen_melden_das_auch_so` prüft die
    Gesamtantwort `NotResponsible`. Live ist die Zeile heute nicht
    herstellbar: Beide vorhandenen Resolver sind für jedes Papier zuständig.
    Eine unzuständige Quelle gibt es erst mit den Plugins aus **T-23** — dort
    gehört die Live-Prüfung hin.
[^e]: `make test` → Backend `345 passed, 29 skipped`, Plugin-API `36 passed`,
    Dashboard `230 passed`. Ruff sauber. Neue Tests je Antwortart:
    `test_ausfall_ist_nicht_dasselbe_wie_unbekannt`,
    `test_ein_ausfall_schlaegt_ein_kenne_ich_nicht`,
    `test_die_kette_nennt_alle_ausgefallenen_quellen`,
    `test_ein_treffer_schlaegt_einen_vorherigen_ausfall`,
    `test_nur_unzustaendige_quellen_melden_das_auch_so`, dazu die
    Service- und API-Ebene.

    Nachgetragen in Runde 1: `/analyze` prüfte weiter auf ``None`` und griff
    danach auf `.symbol` zu — für ein unbekanntes Papier **und** für einen
    Quellenausfall endete der Diagnose-Endpunkt damit in einem 500, obwohl er
    gerade dann ein Teilergebnis liefern soll. Der Analyzer bildet jetzt alle
    vier Antwortarten ab, und die Tests führen die echten Vertragstypen durch
    ihn hindurch. Ein bestehender Test lief nur deshalb grün, weil sein Fake
    ein blankes ``None`` lieferte statt `NotFound`.

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

**Stand 2026-08-22 — von Codex in Runde 2 abgenommen** (`34cf386`).

Runde 1 brachte einen Befund: Der Diagnose-Endpunkt wertete die neuen
Antwortarten nicht aus und lief in einen 500. Eingearbeitet und gegengeprüft.

| Was | Wo |
|---|---|
| Die vier Antwortarten | aus `stockinfo_plugin.types`, nicht neu erfunden |
| `Resolution` der App | `app/providers/base.py` |
| Ausfall werfen statt `None` | `SourceUnavailableError`, `OpenFigiClient.map_isin` |
| Antwortarten je Resolver | `OpenFigiResolver`, `YFinanceResolver` |
| Kettenlogik samt Zusammenfassung | `CompositeResolver.resolve_isin` |
| `handles()` vor der Anfrage | Protokoll und alle drei Resolver |
| 404 gegen 502 | `QuoteService.get_quote_by_isin`, Router |
| Diagnose wertet alle vier Arten aus | `QuoteAnalyzer._measure_resolve` (Runde 1) |

### Die App hängt jetzt am Plugin-Vertrag

`stockinfo-plugin-api` war bewusst **nicht** in der App-Umgebung installiert —
der Kommentar in `pyproject.toml` sagt das ausdrücklich. Das Ticket verlangt
aber, die Typen von dort zu übernehmen statt sie ein zweites Mal zu
definieren. Also kommt die Abhängigkeit dazu:

- `requirements.txt`: `-e ./plugin_api` — editierbar, damit eine Änderung am
  Vertrag sofort in der App sichtbar ist.
- `docker/Dockerfile`: `COPY plugin_api ./plugin_api` **vor** dem pip-Lauf.

Die Trennung der Testsuiten bleibt: `testpaths = ["tests"]` gilt weiter, und
`make test-plugin-api` läuft unverändert eigenständig.

### Was vom Plugin-Vertrag übernommen wird — und was nicht

Übernommen sind die drei Fehlfälle `NotResponsible`, `NotFound` und
`Unavailable`. Der **Erfolgsfall** bleibt vorerst `ResolvedInstrument` und
wird **nicht** durch das `Resolved` des Vertrags ersetzt: Jenes trägt `ticker`
und `mic` getrennt statt eines fertigen Anbieter-Symbols — das ist die
Identitätsfrage aus **T-21**. Beides in einem Diff hieße, zwei Umbauten zu
vermischen.

### Warum ein Ausfall ein „kenne ich nicht" schlägt

Hat eine Quelle gar nicht nachsehen können, ist „gibt es nicht" keine belegte
Aussage — auch dann nicht, wenn eine andere Quelle das Papier tatsächlich
nicht kennt. Ein 404 brächte einen Konsumenten dazu, das Papier aufzugeben.
Deshalb: ein Treffer gewinnt immer, danach zählt ein Ausfall mehr als ein
Fehlschlag.
