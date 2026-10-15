# T-110 · JSON-Vertragstest und Fixtures entfernen

**Warum dieses Ticket:** `tests/test_contract.py` prüft die JSON-Fixtures
unter `contract/fixtures/` gegen das JSON-Artefakt
`contract/core-contract.json`, ohne die App zu starten. Er belegt nur, dass
zwei von Hand gepflegte Dateien zueinander passen. Deshalb ist er grün,
obwohl alle 15 Fixtures einen Header `StockInfo-Generation` tragen, den die
App nur bei `/instrument-types` sendet. Der Header und `GET /generation`
stehen unter `planned` im Artefakt, einem geplanten, nie gebauten Ablauf.

**Beispiel:** `contract/fixtures/quote-200.json` zeigt eine Quote-Antwort
mit `StockInfo-Generation`. Die echte Antwort hat ihn nicht; kein Test merkt
das.

**Stand:** Auf Mikes Entscheidung vom 2026-10-15 in `20-ready/` angelegt
(„sprich sinnloser Test, kann eliminiert werden“). Folgt nach T-109.

## Vorläufiges Inventar (vor der Umsetzung genauer)

- **Bleibt:** `contract/core-contract.json` (von der App gelesen:
  `app/contract.py`, `app/routers/fields.py`), `contract/openapi-core-snapshot.json`
  und `tests/test_contract_openapi.py` (prüft die laufende App gegen den
  Schnappschuss).
- **Fällt:** `tests/test_contract.py` (13 Tests), `contract/fixtures/`
  (15 Dateien), der Schlüssel `planned` im Artefakt.
- **Nachzuziehen:** Verweise in `contract/README.md`,
  `docs/rest-core-contract.md`, `docs/development.md`; Kommentare in `app/`
  und `tests/`, die Fixtures nennen (`git grep` vor der Umsetzung); ob
  `core_version` beim Wegfall von `planned` steigt, entscheidet die
  `compatibility`-Regel im Artefakt.
- **StockPortfolio:** nutzt Kopien einzelner Fixtures
  (`frontend/tests/fixtures/stockinfo/`). Dort wird nichts geändert; der
  dortige Agent bekommt ein Ticket mit dem Hinweis, dass die Quelle entfällt.

## Scope-Vertrag

Wird beim Aktivieren nach dem Inventar festgelegt.

## Review-Verlauf (neueste Runde zuerst)

Noch keine Übergabe.
