# Role Cascades for the YAML Fallback — Design

**Approved by Mike:** 2026-08-30

## Goal

The configured order for `quotes`, `daily`, and `fx` becomes real: the first
provider with a valid result wins, while a miss or temporary failure continues
to the next provider. This lets `yaml-file` sit behind the online providers as
the manually maintained fallback without overriding fresh online data.

Resolvers and ETF metadata already have composites and remain unchanged.

## Chosen architecture

Use three small, role-specific ordered chains at the Core boundary:

- quote: first non-`None` `RawQuote` wins;
- daily: first non-`None` result wins, including a valid empty list;
- FX: first non-`None` rate wins, and the winning provider is retained locally
  so the persisted `source` remains correct.

The existing plugin adapters remain the contract boundary. For daily data,
only a `DailySeries` becomes a Core list; `NotResponsible`, `NotFound`, and
`Unavailable` all become `None` so the next provider can be asked. A genuine
empty `DailySeries` becomes `[]` and stops the chain. This preserves the
contract distinction between a valid empty answer and a non-hit.

Quote and daily use focused composite providers. FX iterates the ordered
providers inside `CachedFxService`, because that service must save the name of
the exact provider that returned the rate. A mutable "last provider" property
on a shared composite is rejected: concurrent requests could attribute a rate
to the wrong source.

## End-to-end behavior

1. `sources.yaml` keeps the existing ordered lists.
2. The registry builds and guards every usable configured provider exactly as
   today; capability filtering and each provider's circuit breaker stay in
   place.
3. The composition root requires a non-empty chain for each of the three
   roles and passes the whole chain to its role-specific consumer.
4. Providers are called sequentially. There is no parallelism, retry, timeout,
   reordering, or cost-based selection.
5. Once every configured provider has failed or missed, existing behavior
   resumes: quote and FX may serve stale cache; daily does not advance its
   watermark after failure; without cache the current typed error remains.

## Configuration example

```yaml
resolvers: [openfigi, yahoo-search, yaml-file]
etf_meta:  [justetf, yfinance, yaml-file]
quotes:    [yfinance, yaml-file]
daily:     [yfinance, yaml-file]
fx:        [yfinance, yaml-file]

providers:
  openfigi:
    api_key: ${OPENFIGI_API_KEY}
  yaml-file:
    path: /data/assets.yaml
```

The order is authoritative. If YFinance returns a valid Bitcoin price, YAML
is not asked. If no online source can quote the configured bond, YAML may
return its explicit `price` or newest manual history close.

## Scope boundaries

- No new configuration keys or profile format.
- No generic chain framework and no changes to resolver/metadata composition.
- No retry policy, concurrency, timeout system, health scoring, or dynamic
  provider order.
- No new cache tables or persisted result types.
- No changes to the YAML data model.
- Browser acceptance reuses the existing application/browser workflow; no new
  browser runner or second smoke script.

## Verification

Automated tests must prove order, fallthrough, all-failed behavior, valid empty
daily behavior, FX provenance, cache behavior after total failure, and a real
container/REST entry path with YAML behind an online-like provider.

Claude's browser acceptance must cover at least:

- `BTC-EUR`: online result wins over an overlapping YAML entry;
- `DE0001102531`: online miss falls through to YAML and uses the newest manual
  history close;
- `DE0009848119`: the `fund` identity and price remain usable;
- list and drilldown source/identity/price display, clean console, and no
  failed requests other than deliberately exercised non-hits.
