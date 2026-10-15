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
(„sprich sinnloser Test, kann eliminiert werden“). Aktiviert am 2026-10-15
auf Mikes Auftrag „1 und dann t-110“, Branch `t-110-json-vertragstest`,
Coder `claude`, Verifier `codex`.

## Vorläufiges Inventar (beim Anlegen)

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

Inventar beim Aktivieren: `git grep` nach `contract/fixtures`, `fixtures/`,
`test_contract.py`, `planned`, `generation_runtime` und `generation` über
`app/`, `tests/`, `contract/`, `docs/` (ohne `_tickets/` und
`docs/superpowers/`, die Historie sind).

**Fällt:**

1. `tests/test_contract.py` und `contract/fixtures/` (15 Dateien).
2. Die beiden Tests, die Fixtures gegen die laufende App halten:
   `test_http_fixture_entspricht_der_laufenden_api`
   (`tests/test_api_instrument_types.py`) und
   `test_die_fixture_zeigt_was_der_dienst_wirklich_antwortet`
   (`tests/test_symbol_ambiguity.py`). Ohne Fixture prüfen sie nichts mehr;
   Rumpfform von `409` und Typkatalog prüfen die übrigen Tests derselben
   Dateien weiter.
3. Im Artefakt der Schlüssel `planned` und im Block `generation` alles, was
   nicht gebaut ist: `endpoint: /generation`, `required_on_every_response`,
   `expose_headers_required`, die Regel zum Abgleich mit `/generation`;
   in `contract_endpoints_note` der Satz zu `/generation`. Es bleibt, was die
   App tut: Header `StockInfo-Generation` mit `Cache-Control: no-store` bei
   `GET /instrument-types`.
4. `core_version` 4.4.0 → 4.4.1 (Patch: Klarstellung ohne Änderung an einer
   Antwort; `compatibility.versioning.patch`).

**Nachgezogen:** `contract/README.md`, `docs/rest-core-contract.md`,
`docs/development.md` (falls betroffen), Docstrings/Kommentare in
`app/contract.py`, `app/main.py`, `app/models.py`,
`app/persistence/repository.py`, `tests/test_contract_openapi.py`,
`tests/test_symbol_ambiguity.py`; der Schnappschuss
`contract/openapi-core-snapshot.json` über `UPDATE_CORE_SNAPSHOT=1`, weil er
die Modellbeschreibung aus `app/models.py` enthält.

**Nicht im Umfang:** Laufzeitverhalten der App, neue Tests, Änderungen in
StockPortfolio. Dort entsteht nur ein Ticket: Die Quelle der Kopien unter
`frontend/tests/fixtures/stockinfo/` entfällt.

**Abnahme:** `make test` und `make check` grün, `make docs-check` ohne
Problem, `git grep` findet außer Historie keinen Verweis mehr auf
`contract/fixtures`, `test_contract.py`, `planned` oder `/generation`.

## Review-Verlauf (neueste Runde zuerst)

### Übergabe Runde 1 · Claude, 2026-10-15

Prüffassung `da653ce` (Umsetzung `5b3a929`, Quittung `da653ce`).

**Umgesetzt nach Scope-Vertrag:**

1. Entfernt: `tests/test_contract.py`, `contract/fixtures/` (15 Dateien),
   `test_http_fixture_entspricht_der_laufenden_api` und
   `test_die_fixture_zeigt_was_der_dienst_wirklich_antwortet`. Die
   UUID-Prüfung des Headers aus dem ersten Test steht jetzt in
   `test_typen_kommen_aus_plugins_ohne_instrumente`.
2. Artefakt: `planned` entfernt; `generation` nennt nur noch Header,
   `sent_by: ["/instrument-types"]`, `cache_control`, `id_kind` und eine Regel,
   die dem Verhalten entspricht; der Satz zu `/generation` in
   `contract_endpoints_note` ist weg; `core_version` 4.4.1.
3. Docstrings in `app/contract.py`, `app/main.py`, `app/models.py`,
   `app/persistence/repository.py`, `tests/test_contract_openapi.py`,
   `tests/test_symbol_ambiguity.py` verweisen nicht mehr auf Fixtures.
   Schnappschuss mit `UPDATE_CORE_SNAPSHOT=1` erneuert: nur `core_version`
   und die Beschreibung von `AmbiguousSymbolDetail` ändern sich.
4. Mike, 2026-10-15: „Snapshot bleibt“ — `openapi-core-snapshot.json` und
   `tests/test_contract_openapi.py` bleiben unverändert im Umfang.

**Doku-Abgleich:**

- `contract/README.md`: Verzeichnisbaum, Fixture-Absätze und
  `test_contract.py`-Aufruf entfernt; „Für dieses Repo“ beschreibt jetzt,
  was `test_contract_openapi.py` prüft; „Wenn sich etwas ändert“ verlangt
  Modell und Artefakteintrag statt Fixture.
- `docs/rest-core-contract.md`: Version 4.4.1, Stand 2026-10-15; Satz zu
  Fixtures unter dem Kopf, Auszug `core_version`, Satz unter `/fields`,
  Fixture-Links im Typkatalog und Stufen 1–2 von „Wie man den Vertrag
  prüft“. Der Abschnitt zur Generation stimmte schon mit dem Verhalten
  überein und bleibt.
- `docs/development.md`: Zeile `contract/` im Projektaufbau.
- `README.md`, `README.de.md`, `docker/README.md`, `unraid/README.md`,
  `docs/plugin-authors.md`: unverändert, sie nennen weder Fixtures noch
  `/generation`; `plugin-authors.md` beschreibt den Header schon korrekt
  nur für `/instrument-types`.

**Nachweise:**

- `git grep -n -E 'contract/fixtures|test_contract\.py|"planned"|generation_runtime|/generation\b'`
  außerhalb von `_tickets/`, `docs/superpowers/` und `CHANGELOG.md`: kein
  Treffer.
- `make test`: 1246 passed, 1 skipped; Dashboard 399 passed.
  `make check`: ruff und `vue-tsc` ohne Befund. `make docs-check`: keine
  Probleme; der Swagger-Screenshot-Hinweis kam nur aus dem Docstring in
  `app/main.py` (Oberfläche unverändert) und ist quittiert.
- StockPortfolio: Ticket
  `_tickets/10-backlog/T-97-stockinfo-vertragsfixtures-ohne-quelle.md`
  angelegt, dort nicht committet (fremdes Repo, nur Ticket).
