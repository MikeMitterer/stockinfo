# T-03 · justETF nur europäische UCITS-ISINs scrapen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| backend | done | erledigt | Backend-Verhalten (nicht UI-sichtbar) | — |

**Löst:** Verifiziert, dass `JustEtfProvider` für nicht-europäische ISINs
(US/CA/JP …) gar nicht erst scrapet, sondern sofort `None` liefert — spart pro
Refresh einen langsamen, sicher fehlschlagenden Netz-Aufruf (Commit `aee2c84`).

<!--
  Repo:   backend (app/providers/justetf_provider.py)
  Scope:  Backend-Verhalten — bewusst NICHT UI-only. Observabel via Add-Instrument
          + Logs, nicht durch ein sichtbares Panel. Deshalb eigenes Ticket.
-->

---

## Verify

Legende: ✅ live bestätigt · ⚠️ bestätigt mit Einschränkung (Fußnote) ·
◑ teilweise (Fußnote) · ➖ keine Live-Verifikation.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|-------|
| 1 | `is_european_isin()` (Unit) | `IE00B4L5Y983`→True, `US0378331005`→False, `CA…`→False | ✅¹ |       |
| 2 | Dashboard „Assets" → Add `US0378331005` (Apple) | Instrument wird angelegt, aber **ohne** ETF-Extras (TER/Provider) — kein justETF-Hang | ➖ | ok    |
| 3 | Guard-Test (Repro-Command unten) | Log `justetf_skipped_non_european isin=US…`, **kein** Scrape-Aufruf für US-ISIN; EU-ISIN erreicht den Scrape-Pfad | ✅² |       | nehme 
| 4 | Dashboard „Assets" → europäische ETF-ISIN (z.B. `IE00B4L5Y983`) | ETF-Extras werden (best-effort) angereichert — Scrape läuft weiterhin | ➖ | ok    |

> ¹ **(CC):** live `python -c "is_european_isin(...)"` (2026-08-13) → IE=True, US=False, CA=False.
> ² **(CC):** live verifiziert (2026-08-13) — `justetf_scraping.get_etf_overview` durch Raise-Guard ersetzt; `fetch_etf("US0378331005")` → `None` in **0.06 ms**, Log `justetf_skipped_non_european isin=US0378331005`, Guard **nicht** ausgelöst (kein Scrape). Gegenprobe: `fetch_etf("IE00B4L5Y983")` löst den Guard aus (`get_etf_overview` wird aufgerufen) → Scrape-Pfad für EU-ISINs unverändert aktiv.

**Repro-Command** (kopierbar):
```bash
.venv/bin/python - <<'PY'
import justetf_scraping
from app.providers.justetf_provider import JustEtfProvider
justetf_scraping.get_etf_overview = lambda isin: (_ for _ in ()).throw(
    AssertionError(f"Scrape fuer {isin} — Skip hat versagt"))
print("US:", JustEtfProvider().fetch_etf("US0378331005"))   # -> None, kein Scrape
try:
    JustEtfProvider().fetch_etf("IE00B4L5Y983")             # -> Scrape-Pfad erreicht
except Exception as e:
    print("IE Scrape-Pfad erreicht:", e)
PY
```

---

## Details

### Kontext / Ziel
justETF listet ausschließlich europäische UCITS-ETFs; das Domizil ist am
ISIN-Länderpräfix (EU + EEA + CH/UK) erkennbar. `fetch_etf()` prüft vorab per
`is_european_isin()` und überspringt nicht-europäische ISINs, statt einen
langsamen Scrape zu starten, der garantiert leer zurückkommt.

### Akzeptanzkriterien
- [x] Nicht-europäische ISIN → sofort `None`, kein Netz-Call (0.06 ms, Guard-Test)
- [x] Europäische ISIN → Scrape läuft unverändert (best-effort)
- [x] Allow-List großzügig (kein echter EU-ETF verloren)

### Side-Effects
Reine Performance-/Robustheits-Optimierung; keine API-Formänderung. Grenzfall:
in Nicht-EU-Domizil aufgelegte, aber europäisch gehandelte Papiere würden
übersprungen — bewusst akzeptiert (justETF hätte dort ohnehin nichts).

### Auflösung
2026-08-13 verifiziert (Guard-Test, kein echter Netz-Call nötig). Skip für
nicht-europäische ISINs bestätigt (Log + 0.06 ms), Scrape-Pfad für EU-ISINs
unverändert. Kein Code-Change nötig — Verhalten aus Commit `aee2c84` korrekt.
