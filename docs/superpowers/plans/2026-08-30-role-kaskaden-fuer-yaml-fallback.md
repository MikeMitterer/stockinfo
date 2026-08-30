# Role Cascades for the YAML Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the configured quote, daily, and FX provider order execute as a real fallback chain so online data wins and `yaml-file` fills only genuine gaps.

**Architecture:** Add focused Core composites for quote and daily providers, and iterate FX providers inside `CachedFxService` so the exact winning source is persisted without mutable shared state. Keep registry construction, adapters, circuit breakers, resolver composition, and metadata composition unchanged.

**Tech Stack:** Python 3.11, pytest, FastAPI `TestClient`, existing `stockinfo_plugin` result types and StockInfo provider protocols.

**Spec:** `docs/superpowers/specs/2026-08-30-role-kaskaden-fuer-yaml-fallback-design.md`

## Global Constraints

- The order in `sources.yaml` is authoritative; do not reorder or parallelize providers.
- Fall through only on a non-hit or unavailable result; the first valid result wins.
- A valid empty `DailySeries` is success and stops the chain.
- Existing stale-cache and typed-error behavior runs only after the whole role chain fails.
- Do not add configuration keys, a generic chain framework, retries, timeouts, cache tables, or browser infrastructure.
- Reuse existing plugin adapters and contract result types.

---

### Task 1: Quote and daily composites

**Files:**
- Create: `app/providers/composite_market.py`
- Modify: `app/plugin_adapters.py`
- Create: `tests/test_composite_market.py`
- Modify: `tests/test_plugin_vertical.py`

**Interfaces:**
- Consumes: `QuoteProvider.fetch_quote(...) -> RawQuote | None` and `DailyCloseProvider.fetch_daily_closes(...) -> list[dict] | None` from `app.providers.base`.
- Produces: `CompositeQuoteProvider(*providers)` and `CompositeDailyCloseProvider(*providers)`, both implementing the existing Core protocols.

- [ ] **Step 1: Write failing order and fallthrough tests**

  Add doubles that record calls, then assert: the first valid quote wins; a
  `None` quote reaches the second provider; no provider after a hit is called;
  all misses return `None`. Repeat for daily data, with the additional oracle
  that `[]` stops the chain while `None` falls through.

- [ ] **Step 2: Run the new tests and confirm the missing composites fail**

  Run: `.venv/bin/pytest -q tests/test_composite_market.py`

  Expected: collection/import failure because the two composite classes do
  not exist.

- [ ] **Step 3: Implement the two minimal composites**

  Each class stores the ordered tuple and loops once. Quote returns the first
  `RawQuote`; daily returns the first value that is not `None`, including
  `[]`. Both return `None` only after every provider misses.

- [ ] **Step 4: Preserve the daily contract distinction in the adapter**

  Change `DailyAdapter.fetch_daily_closes`: translate `DailySeries` to a list
  exactly as today, including an empty tuple becoming `[]`; translate
  `NotResponsible`, `NotFound`, and `Unavailable` to `None`. Add a direct
  adapter test proving `NotFound -> None` and empty `DailySeries -> []`.

- [ ] **Step 5: Run focused tests**

  Run: `.venv/bin/pytest -q tests/test_composite_market.py tests/test_plugin_vertical.py`

  Expected: all pass.

- [ ] **Step 6: Commit the independently testable composites**

  Commit message: `feat(sources): Kurs- und History-Kaskaden ausfuehren`

### Task 2: FX chain with exact provenance

**Files:**
- Modify: `app/services/fx_service.py`
- Modify: `tests/test_fx_service.py`

**Interfaces:**
- Consumes: an ordered `FxRateProvider` sequence plus the existing single-provider form used by tests and callers.
- Produces: unchanged public `CachedFxService.get_rate(base, quote) -> FxRate` behavior, with the actual winning provider in `source`.

- [ ] **Step 1: Write failing FX chain tests**

  Prove: first rate wins; `None` reaches the next provider; later providers are
  not called after a hit; all misses use stale cache or raise the existing
  `FxUnavailableError`; a YAML-named second provider is saved as `source` and
  that source survives the cache read.

- [ ] **Step 2: Run the focused tests and confirm failure**

  Run: `.venv/bin/pytest -q tests/test_fx_service.py`

  Expected: the new sequence cases fail because `CachedFxService` calls only
  one provider.

- [ ] **Step 3: Implement local ordered iteration**

  Normalize the constructor input to an ordered tuple. In
  `_fetch_or_fallback`, loop through it and retain `declared_name(provider)`
  in a local variable beside the winning rate. Save and return that local
  source. Invoke stale-cache/error behavior only when no provider returned a
  rate. Do not add mutable "last source" state.

- [ ] **Step 4: Run focused tests**

  Run: `.venv/bin/pytest -q tests/test_fx_service.py`

  Expected: all pass, including existing single-provider tests.

- [ ] **Step 5: Commit the independently testable FX chain**

  Commit message: `feat(fx): konfigurierte Quellen als Kaskade abfragen`

### Task 3: Composition root, vertical oracles, and live acceptance

**Files:**
- Modify: `app/container.py`
- Modify: `tests/test_container.py`
- Modify: `tests/test_yaml_profile.py`
- Modify: `_tickets/T-41-role-kaskaden-fuer-yaml-fallback.md`
- Modify: `docs/sources.yaml.example`
- Modify: `docs/plugins.md`

**Interfaces:**
- Consumes: `CompositeQuoteProvider`, `CompositeDailyCloseProvider`, and the ordered FX provider input from Tasks 1–2.
- Produces: all configured usable providers reaching the existing quote, daily, and FX consumers.

- [ ] **Step 1: Write failing composition tests**

  Configure two providers in each role and assert the composition root retains
  both in order. Keep the existing empty-chain `RuntimeError`, but make it
  describe a required non-empty chain rather than a first provider.

- [ ] **Step 2: Write failing vertical YAML fallback oracles**

  Reuse `tests/test_yaml_profile.py` and the existing `TestClient`/registry
  path. Prove through the public REST entry path that an online-like first
  provider wins on overlap, while its non-hit reaches the YAML bond price;
  prove daily valid-empty versus non-hit behavior and `/fx` reporting
  `yaml-file` when the first provider misses. Assert distinguishing values and
  provider call counts so an empty/default chain cannot pass.

- [ ] **Step 3: Run the focused tests and confirm they fail for the old `_first` wiring**

  Run: `.venv/bin/pytest -q tests/test_container.py tests/test_yaml_profile.py`

  Expected: the second provider is not reached before the composition change.

- [ ] **Step 4: Replace `_first` with required full-chain wiring**

  Keep `_chain(role)` as the registry boundary. Add one bounded non-empty
  check returning the complete list, wrap quote and daily lists in their
  composites, and pass the complete FX list to `CachedFxService`. Use the same
  daily composite in both `get_cached_quote_service` and
  `get_daily_history_service`. Do not touch resolver or ETF metadata builders.

- [ ] **Step 5: Update active documentation only**

  Restore the approved online-plus-YAML example in `docs/sources.yaml.example`
  and `docs/plugins.md` only after the vertical tests pass. Historical review
  findings remain unchanged. Update the T-41 AI matrix with exact commands
  and results; never write the Human column.

- [ ] **Step 6: Run automated verification**

  Run:

  ```bash
  .venv/bin/pytest -q tests/test_composite_market.py tests/test_container.py tests/test_fx_service.py tests/test_yaml_profile.py tests/test_plugin_vertical.py
  .venv/bin/ruff check app tests plugin_api/src plugin_api/tests plugin_api/examples
  PROFILE=yaml ./_tickets/T-35-smoke.sh --run
  make test
  git diff --check
  ```

  Expected: all tests and checks pass; YAML smoke reports 20/20.

- [ ] **Step 7: Perform Claude's browser acceptance**

  Run the normal Online profile with `yaml-file` last. Add and inspect
  `BTC-EUR`, `DE0001102531`, and `DE0009848119`; record the actual winner and
  value for each, verify overlap favors online, the bond falls through to the
  newest YAML close, console is clean, and no unexpected request fails. Use
  the existing browser workflow and leave no new launcher script.

- [ ] **Step 8: Commit and hand off to Codex**

  Commit message: `feat(sources): YAML als echten Online-Fallback verdrahten`

  Handoff only after the worktree is clean and the ticket contains the
  automated and browser evidence.
